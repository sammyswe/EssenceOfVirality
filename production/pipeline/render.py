"""Skill 4 — rendering.

Builds one FFmpeg ``filter_complex`` from the edit plan and executes it. A single
graph keeps the render deterministic and avoids intermediate generation loss.

Audio handling is deliberately narrow: the Spotify recording's stream is the only
audio input, every other input is mapped video-only, and the sole permitted
processing is loudness normalisation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import textrender
from .editplan import EditPlan, Placement
from .inspector import InputReport, enforcement_names
from .om import encode_tiktok, pin_status
from .paths import load_config
from .probe import MediaError, probe, run

CANVAS_WIDTH = 1080
CANVAS_HEIGHT = 1920


class RenderError(RuntimeError):
    """Raised when the render cannot be produced."""


@dataclass
class RenderResult:
    output_path: Path
    preview_path: Path | None
    duration_seconds: float
    width: int
    height: int
    audio_inputs: list[str]
    filter_graph: str
    command: list[str]
    backends: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "output_path": str(self.output_path),
            "preview_path": str(self.preview_path) if self.preview_path else None,
            "duration_seconds": round(self.duration_seconds, 3),
            "width": self.width,
            "height": self.height,
            "audio_inputs": self.audio_inputs,
            "backends": self.backends,
            "notes": self.notes,
        }


def _even(value: float) -> int:
    return max(2, int(value) // 2 * 2)


def _cover(label_in: str, label_out: str, width: int, height: int) -> str:
    return (
        f"[{label_in}]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},setsar=1[{label_out}]"
    )


def _pad_fit(label_in: str, label_out: str, width: int, height: int) -> str:
    return (
        f"[{label_in}]scale={width}:{height}:force_original_aspect_ratio=decrease,"
        f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1[{label_out}]"
    )


def _source_aspect(report: InputReport) -> float:
    """Aspect ratio of the Spotify source after its crop profile is applied."""
    width = float(report.spotify.get("width") or 0)
    height = float(report.spotify.get("height") or 0)
    if not width or not height:
        return 0.0
    crop = report.crop_profile.crop
    width *= float(crop.get("width", 1.0))
    height *= float(crop.get("height", 1.0))
    return width / height if height else 0.0


@dataclass
class SurfaceFit:
    """How the Spotify surface is fitted into its placement."""

    crop_filter: str | None
    mode: str                      # cover | contain
    visible_area_fraction: float
    discarded_fraction: float
    note: str
    content_scale: float = 1.0     # how much larger the interface reads than uncropped
    ceiling_note: str = ""         # why a requested enlargement could not go further
    clipped_hard: list[str] = field(default_factory=list)
    clipped_soft: list[str] = field(default_factory=list)


def _envelope(
    boxes: dict[str, dict[str, float]],
    frame_width: float,
    frame_height: float,
    *,
    margin: float = 0.02,
    side_trim: float = 0.0,
) -> tuple[float, float, float, float]:
    """Pixel box (width, height, centre_x, centre_y) enclosing the given regions."""
    x1 = max(0.0, min(float(box.get("x", 0.0)) for box in boxes.values()) - margin + side_trim)
    y1 = max(0.0, min(float(box.get("y", 0.0)) for box in boxes.values()) - margin)
    x2 = min(1.0, max(
        float(box.get("x", 0.0)) + float(box.get("width", 0.0)) for box in boxes.values()
    ) + margin - side_trim)
    y2 = min(1.0, max(
        float(box.get("y", 0.0)) + float(box.get("height", 0.0)) for box in boxes.values()
    ) + margin)
    x2 = max(x2, x1 + 0.05)
    return (
        (x2 - x1) * frame_width,
        (y2 - y1) * frame_height,
        (x1 + x2) / 2 * frame_width,
        (y1 + y2) / 2 * frame_height,
    )


def _clipped_regions(
    report: InputReport,
    frame_width: float,
    frame_height: float,
    crop: tuple[float, float, float, float],
) -> tuple[list[str], list[str]]:
    """Names of must-remain-visible regions the crop cuts into, split hard/soft."""
    left, top, width, height = crop
    soft_names = enforcement_names()[1]
    hard: list[str] = []
    soft: list[str] = []
    for name, box in report.crop_profile.must_remain_visible.items():
        x1 = float(box.get("x", 0.0)) * frame_width
        y1 = float(box.get("y", 0.0)) * frame_height
        x2 = x1 + float(box.get("width", 0.0)) * frame_width
        y2 = y1 + float(box.get("height", 0.0)) * frame_height
        # A one-pixel tolerance absorbs the rounding done when the crop is emitted.
        inside = (
            x1 >= left - 1 and y1 >= top - 1
            and x2 <= left + width + 1 and y2 <= top + height + 1
        )
        if inside:
            continue
        (soft if name in soft_names else hard).append(name)
    return sorted(hard), sorted(soft)


def _focus_boxes(report: InputReport) -> dict[str, dict[str, float]]:
    """The regions a zoom should enlarge: the hard ones, or everything if none."""
    hard_names = enforcement_names()[0]
    boxes = report.crop_profile.must_remain_visible
    focus = {name: box for name, box in boxes.items() if name in hard_names}
    return focus or boxes


def fit_spotify_surface(
    report: InputReport,
    placement: Placement,
    *,
    content_zoom: float = 0.0,
    waveform_end_trim: float = 0.0,
) -> SurfaceFit:
    """Decide how to place the Spotify surface without losing what must stay visible.

    Two different problems share this crop. When the placement is a different shape
    from the source, cropping the whole frame would cut song labels or the waveform,
    so the crop is taken around the envelope of everything that must remain visible.
    When the shapes already agree, the crop exists only to make the interface read
    larger, so it moves towards the *hard* regions alone — the song labels and
    waveform — and lets the artwork be trimmed first.

    Enlargement has a hard ceiling: the waveform already spans most of the frame
    width, so it cannot grow much without its ends being cut. ``waveform_end_trim``
    is the opt-in lever that accepts that cut; the fit reports the ceiling either way.
    """
    source_width = float(report.spotify.get("width") or 0)
    source_height = float(report.spotify.get("height") or 0)
    profile_crop = report.crop_profile.crop
    frame_width = source_width * float(profile_crop.get("width", 1.0))
    frame_height = source_height * float(profile_crop.get("height", 1.0))

    canvas_area = float(CANVAS_WIDTH * CANVAS_HEIGHT)
    placement_fraction = (placement.width * placement.height) / canvas_area

    if not frame_width or not frame_height:
        return SurfaceFit(None, "cover", placement_fraction, 0.0, "")

    target_aspect = placement.width / placement.height
    source_aspect = frame_width / frame_height
    mismatch = abs(source_aspect - target_aspect) / target_aspect

    if report.crop_profile.fit == "pad":
        scale = min(placement.width / frame_width, placement.height / frame_height)
        visible = (frame_width * scale) * (frame_height * scale) / canvas_area
        return SurfaceFit(
            None, "contain", visible, 0.0,
            "crop profile requests padding rather than cropping",
        )

    content_zoom = max(0.0, min(float(content_zoom), 1.0))
    if mismatch <= 0.08 and content_zoom <= 0.0:
        return SurfaceFit(None, "cover", placement_fraction, 0.0, "")

    boxes = report.crop_profile.must_remain_visible
    if not boxes:
        if mismatch <= 0.08:
            return SurfaceFit(
                None, "cover", placement_fraction, 0.0,
                "content zoom requested but the crop profile defines no "
                "must-remain-visible regions to zoom towards",
            )
        scale = min(placement.width / frame_width, placement.height / frame_height)
        visible = (frame_width * scale) * (frame_height * scale) / canvas_area
        return SurfaceFit(
            None, "contain", visible, 0.0,
            "no must-remain-visible regions defined, so the surface is fitted whole",
        )

    ceiling_note = ""

    if mismatch <= 0.08:
        # Pure enlargement. The tightest crop that still holds the hard regions and
        # keeps the placement's shape sets the ceiling; content_zoom interpolates
        # from the whole frame towards it.
        focus = _focus_boxes(report)
        trim = max(0.0, min(float(waveform_end_trim), 0.25))
        focus_w, focus_h, centre_x, centre_y = _envelope(
            focus, frame_width, frame_height, side_trim=trim
        )
        tightest_w = min(frame_width, max(focus_w, focus_h * target_aspect))
        tightest_h = min(frame_height, tightest_w / target_aspect)
        tightest_w = tightest_h * target_aspect

        crop_w = frame_width + (tightest_w - frame_width) * content_zoom
        crop_h = crop_w / target_aspect
        if crop_h > frame_height:
            crop_h = frame_height
            crop_w = crop_h * target_aspect
        centre_x = frame_width / 2 + (centre_x - frame_width / 2) * content_zoom
        centre_y = frame_height / 2 + (centre_y - frame_height / 2) * content_zoom

        content_scale = frame_width / crop_w
        ceiling_scale = frame_width / tightest_w if tightest_w else 1.0
        if content_scale < 1.02:
            widest = max(
                float(box.get("width", 0.0)) for box in focus.values()
            )
            ceiling_note = (
                f"enlargement is capped at {ceiling_scale:.2f}x: the widest protected "
                f"region spans {widest:.0%} of the frame width, so cropping further "
                "would cut its ends. Set layout.waveform_end_trim to accept that cut."
                if trim <= 0 else
                f"enlargement is capped at {ceiling_scale:.2f}x even with "
                f"layout.waveform_end_trim={trim:.2f}"
            )
    else:
        # Shape change. Protect everything, then grow towards the placement's shape.
        crop_w, crop_h, centre_x, centre_y = _envelope(boxes, frame_width, frame_height)
        if crop_w / crop_h < target_aspect:
            crop_w = min(frame_width, crop_h * target_aspect)
        else:
            crop_h = min(frame_height, crop_w / target_aspect)
        content_scale = 1.0

    left = min(max(centre_x - crop_w / 2, 0.0), max(frame_width - crop_w, 0.0))
    top = min(max(centre_y - crop_h / 2, 0.0), max(frame_height - crop_h, 0.0))

    achieved_aspect = crop_w / crop_h
    achieved_mismatch = abs(achieved_aspect - target_aspect) / target_aspect
    crop_filter = f"crop=w={_even(crop_w)}:h={_even(crop_h)}:x={int(left)}:y={int(top)}"
    discarded = 1.0 - (crop_w * crop_h) / (frame_width * frame_height)
    clipped_hard, clipped_soft = _clipped_regions(
        report, frame_width, frame_height, (left, top, crop_w, crop_h)
    )
    if clipped_soft:
        ceiling_note = "; ".join(filter(None, [
            ceiling_note,
            f"{', '.join(clipped_soft)} partly cropped to make room for the zoom",
        ]))

    if achieved_mismatch <= 0.08:
        reason = (
            f"content zoom {content_zoom:.0%} makes the song labels and waveform read "
            f"{content_scale:.2f}x larger"
            if mismatch <= 0.08 else
            "cropped to the must-remain-visible envelope"
        )
        return SurfaceFit(
            crop_filter, "cover", placement_fraction, discarded,
            f"{reason} ({_even(crop_w)}x{_even(crop_h)}) so the "
            f"{placement.width}x{placement.height} placement is filled",
            content_scale=content_scale,
            ceiling_note=ceiling_note,
            clipped_hard=clipped_hard,
            clipped_soft=clipped_soft,
        )

    scale = min(placement.width / crop_w, placement.height / crop_h)
    visible = (crop_w * scale) * (crop_h * scale) / canvas_area
    return SurfaceFit(
        crop_filter, "contain", visible, discarded,
        f"cropped to the must-remain-visible envelope, then fitted whole: the envelope "
        f"aspect {achieved_aspect:.3f} still differs from the placement aspect "
        f"{target_aspect:.3f}, so the surface is letterboxed rather than cut",
        content_scale=content_scale,
        ceiling_note=ceiling_note,
        clipped_hard=clipped_hard,
        clipped_soft=clipped_soft,
    )


def _crop_expression(crop: dict[str, float]) -> str | None:
    """FFmpeg crop filter for a fractional crop profile, or None when full-frame."""
    x = float(crop.get("x", 0.0))
    y = float(crop.get("y", 0.0))
    width = float(crop.get("width", 1.0))
    height = float(crop.get("height", 1.0))
    if (x, y, width, height) == (0.0, 0.0, 1.0, 1.0):
        return None
    return (
        f"crop=w=iw*{width:.5f}:h=ih*{height:.5f}:"
        f"x=iw*{x:.5f}:y=ih*{y:.5f}"
    )


def build_filter_graph(
    plan: EditPlan, report: InputReport
) -> tuple[str, list[list[str]], list[str]]:
    """Return (filter_complex, extra_input_args, notes).

    ``extra_input_args`` holds the ffmpeg arguments for each secondary clip, in the
    order they become inputs 1..n.
    """
    notes: list[str] = []
    chains: list[str] = []
    inputs: list[list[str]] = []

    placement = plan.spotify_placement
    profile_crop = _crop_expression(report.crop_profile.crop)
    fit = report.crop_profile.fit

    # Input 0 feeds both the background and the Spotify surface.
    source_chain = "[0:v]"
    if profile_crop:
        source_chain += profile_crop + ","
    chains.append(f"{source_chain}split=2[src_bg][src_main]")

    # Background: a blurred, darkened copy so letterboxed sources never show bars.
    chains.append(
        f"[src_bg]scale={CANVAS_WIDTH}:{CANVAS_HEIGHT}:force_original_aspect_ratio=increase,"
        f"crop={CANVAS_WIDTH}:{CANVAS_HEIGHT},gblur=sigma=42,eq=brightness=-0.12,"
        f"setsar=1[bg]"
    )

    # The Spotify surface itself.
    surface = fit_spotify_surface(
        report, placement,
        content_zoom=plan.spotify_content_zoom,
        waveform_end_trim=plan.waveform_end_trim,
    )
    surface_label = "src_main"
    if surface.crop_filter:
        chains.append(f"[src_main]{surface.crop_filter}[src_cropped]")
        surface_label = "src_cropped"
    if surface.mode == "contain":
        chains.append(_pad_fit(surface_label, "spot", placement.width, placement.height))
    else:
        chains.append(_cover(surface_label, "spot", placement.width, placement.height))
    if surface.note:
        notes.append(surface.note)
    if surface.ceiling_note:
        notes.append(surface.ceiling_note)
    del fit

    chains.append(
        f"[bg][spot]overlay=x={placement.x}:y={placement.y}:"
        f"shortest=0:eof_action=pass[stage0]"
    )

    stage = "stage0"
    for index, clip in enumerate(plan.secondary_clips, start=1):
        clip_placement: Placement = clip.placement or Placement(
            0, 0, CANVAS_WIDTH, CANVAS_HEIGHT
        )
        width = _even(clip_placement.width)
        height = _even(clip_placement.height)

        input_args = ["-i", clip.path]
        if clip.loop:
            input_args = ["-stream_loop", "-1", *input_args]
        if clip.source_in:
            input_args = ["-ss", f"{clip.source_in:.3f}", *input_args]
        inputs.append(input_args)

        label = f"sec{index}"
        clip_chain = (
            f"[{index}:v]scale={width}:{height}:force_original_aspect_ratio=increase,"
            f"crop={width}:{height},setsar=1,fps=30,"
            f"setpts=PTS-STARTPTS+{clip.start_seconds:.3f}/TB"
        )
        fade_out = max(0.0, float(clip.fade_out_seconds or 0.0))
        if fade_out > 0:
            visible = clip.end_seconds - clip.start_seconds
            fade_out = min(fade_out, max(visible / 3.0, 0.0))
        if fade_out > 0:
            fade_start = clip.end_seconds - fade_out
            clip_chain += (
                f",format=yuva420p,fade=t=out:st={fade_start:.3f}:"
                f"d={fade_out:.3f}:alpha=1"
            )
            notes.append(
                f"{clip.label!r} dissolves out over {fade_out:.2f}s ending at "
                f"{clip.end_seconds:.2f}s"
            )
        chains.append(f"{clip_chain}[{label}]")
        next_stage = f"stage{index}"
        chains.append(
            f"[{stage}][{label}]overlay=x={clip_placement.x}:y={clip_placement.y}:"
            f"enable='between(t,{clip.start_seconds:.3f},{clip.end_seconds:.3f})':"
            f"eof_action=pass:repeatlast=0[{next_stage}]"
        )
        stage = next_stage

    # Zoom emphasis at the transition. zoompan is the only filter in this build
    # whose geometry can follow input time, so the pulse is applied to the
    # composited frame rather than to a single layer.
    emphasis = plan.emphasis
    if emphasis and emphasis.enabled and emphasis.amount > 0:
        attack = max(emphasis.attack_seconds, 0.05)
        release = max(emphasis.release_seconds, 0.05)
        at = emphasis.at_seconds
        ramp = (
            f"if(lt(it,{at:.3f}),"
            f"max(0,1-({at:.3f}-it)/{attack:.3f}),"
            f"max(0,1-(it-{at:.3f})/{release:.3f}))"
        )
        zoom_expr = f"1+{emphasis.amount:.4f}*({ramp})"
        chains.append(
            f"[{stage}]zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d=1:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:fps=30[zoomed]"
        )
        stage = "zoomed"
        notes.append(
            f"zoom pulse of {emphasis.amount:.0%} centred on {at:.2f}s marks the transition"
        )

    # Progress bar: an animated overlay, because drawbox geometry is fixed at
    # filter-graph initialisation in this FFmpeg build.
    bar = plan.progress_bar or {}
    if bar.get("enabled"):
        bar_height = int(bar.get("height", 10))
        colour = str(bar.get("colour", "#1DB954"))
        opacity = float(bar.get("opacity", 0.85))
        bar_index = len(inputs) + 1
        inputs.append([
            "-f", "lavfi", "-i",
            f"color=c={colour}@{opacity:.3f}:s={CANVAS_WIDTH}x{bar_height}:r=30",
        ])
        y_position = (
            CANVAS_HEIGHT - bar_height if bar.get("position", "bottom") == "bottom" else 0
        )
        chains.append(
            f"[{stage}][{bar_index}:v]overlay="
            f"x='-w+(w*t/{plan.duration_seconds:.3f})':y={y_position}:"
            f"format=auto:eof_action=pass[bar]"
        )
        stage = "bar"

    # Text cues.
    text_filters: list[str] = []
    for cue in plan.text_cues:
        style, _ = textrender.fit_to_safe_area(
            cue.text, cue.style, cue.y, textrender.safe_area()
        )
        text_filters.append(textrender.build_drawtext(
            cue.text, style,
            y=cue.y,
            start=cue.start_seconds,
            end=cue.end_seconds,
            animation=cue.animation,
        ))
    if text_filters:
        chains.append(f"[{stage}]" + ",".join(text_filters) + "[texted]")
        stage = "texted"

    chains.append(f"[{stage}]format=yuv420p[vout]")

    # Audio: input 0 only.
    audio = plan.audio
    if audio and audio.normalise:
        chains.append(
            f"[0:a]loudnorm=I={audio.target_lufs}:TP={audio.true_peak_db}:LRA=11,"
            f"aresample=48000[aout]"
        )
        notes.append(f"loudness normalised: {audio.reason}")
    else:
        chains.append("[0:a]aresample=48000[aout]")
        if audio:
            notes.append(f"audio left unprocessed: {audio.reason}")

    return ";".join(chains), inputs, notes


def render(
    plan: EditPlan,
    report: InputReport,
    output_path: Path,
    *,
    preset: str = "tiktok_final",
    preview_path: Path | None = None,
) -> RenderResult:
    """Execute the plan and write the final MP4."""
    presets = load_config("render-presets")["presets"]
    if preset not in presets:
        raise RenderError(f"unknown render preset {preset!r}; available: {sorted(presets)}")
    settings = presets[preset]

    source = Path(plan.audio.source_path if plan.audio else report.spotify["path"])
    if not source.is_file():
        raise RenderError(f"Spotify recording not found: {source}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    graph, extra_inputs, notes = build_filter_graph(plan, report)

    command: list[str] = [
        "ffmpeg", "-y", "-hide_banner", "-v", "error",
        "-ss", f"{plan.source_in_seconds:.3f}",
        "-t", f"{plan.duration_seconds:.3f}",
        "-i", str(source),
    ]
    for args in extra_inputs:
        command.extend(args)

    command.extend([
        "-filter_complex", graph,
        "-map", "[vout]", "-map", "[aout]",
        "-t", f"{plan.duration_seconds:.3f}",
        "-c:v", str(settings["codec"]),
        "-crf", str(settings["crf"]),
        "-preset", str(settings["preset"]),
        "-pix_fmt", str(settings["pixel_format"]),
        "-r", str(settings["fps"]),
        "-c:a", str(settings["audio_codec"]),
        "-b:a", str(settings["audio_bitrate"]),
        "-ar", "48000",
    ])
    if settings.get("faststart"):
        command.extend(["-movflags", "+faststart"])
    command.append(str(output_path))

    try:
        run(command, timeout=3600)
    except MediaError as exc:
        raise RenderError(
            f"{exc}\n\nFilter graph was:\n{graph}"
        ) from exc

    info = probe(output_path)
    if not info.exists:
        raise RenderError(f"render reported success but produced no file: {output_path}")

    backends = {
        "composite": "ffmpeg:filter_complex",
        "text": "ffmpeg:drawtext",
        "audio": "ffmpeg:loudnorm" if (plan.audio and plan.audio.normalise) else "passthrough",
        "openmontage": "available" if pin_status()["available"] else "absent",
    }

    preview_written: Path | None = None
    if preview_path is not None:
        preview_written = render_preview(output_path, preview_path)

    return RenderResult(
        output_path=output_path,
        preview_path=preview_written,
        duration_seconds=info.duration_seconds,
        width=info.width,
        height=info.height,
        audio_inputs=[str(source)],
        filter_graph=graph,
        command=command,
        backends=backends,
        notes=notes,
    )


def render_preview(final_path: Path, preview_path: Path) -> Path:
    """Downscaled proxy for quick review on a phone."""
    presets = load_config("render-presets")["presets"]["preview_fast"]
    preview_path.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-hide_banner", "-v", "error", "-i", str(final_path),
        "-vf", f"scale={presets['width']}:{presets['height']}",
        "-c:v", str(presets["codec"]), "-crf", str(presets["crf"]),
        "-preset", str(presets["preset"]), "-pix_fmt", str(presets["pixel_format"]),
        "-c:a", str(presets["audio_codec"]), "-b:a", str(presets["audio_bitrate"]),
        "-movflags", "+faststart", str(preview_path),
    ], timeout=900)
    return preview_path


def conform_with_openmontage(source: Path, destination: Path) -> dict[str, Any]:
    """Final pass through the OpenMontage ``tiktok`` media profile.

    Used as a conformance check: the profile owns the export geometry, so a render
    that survives it unchanged is known to match the platform target.
    """
    outcome = encode_tiktok(source, destination)
    return {
        "backend": outcome.backend,
        "success": outcome.success,
        "error": outcome.error,
        "output": str(destination),
    }
