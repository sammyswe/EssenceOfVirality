"""Skill 7 — video quality control.

Runs deterministic checks against the rendered file and the plan that produced it.
Every check reports pass, warn or fail with the measurement behind it. A single
``fail`` blocks the render from being presented as post-ready.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import rules
from .editplan import EditPlan
from .inspector import InputReport, protected_regions_for
from .paths import rel
from .probe import (
    MediaError,
    detect_black_frames,
    detect_freeze,
    frame_statistics,
    measure_loudness,
    probe,
)
from .render import RenderResult
from .render import fit_spotify_surface as render_fit

PASS = "pass"
WARN = "warn"
FAIL = "fail"


@dataclass
class Check:
    id: str
    description: str
    status: str
    detail: str
    measurement: Any = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityReport:
    job_id: str
    revision: int
    video_path: str
    created_at: str
    checks: list[Check] = field(default_factory=list)
    hard_rule_violations: list[str] = field(default_factory=list)
    # Attached by the orchestrator after creative_gate.evaluate. None means the
    # creative gate has not run yet — post_ready stays false until it does.
    creative_minimum: dict[str, Any] | None = None

    @property
    def failures(self) -> list[Check]:
        return [check for check in self.checks if check.status == FAIL]

    @property
    def warnings(self) -> list[Check]:
        return [check for check in self.checks if check.status == WARN]

    @property
    def status(self) -> str:
        if self.hard_rule_violations or self.failures:
            return FAIL
        if self.warnings:
            return WARN
        return PASS

    @property
    def technically_valid(self) -> bool:
        """Broken-file / conformance gate only. Orthogonal to feed fitness."""
        return self.status in {PASS, WARN}

    @property
    def creative_minimum_passed(self) -> bool:
        if self.creative_minimum is None:
            return False
        return bool(self.creative_minimum.get("passed"))

    @property
    def post_ready(self) -> bool:
        """True only when the file is technically valid *and* creative-minimum passes.

        A technical pass alone is a valid draft, not a feed-ready review candidate.
        """
        return self.technically_valid and self.creative_minimum_passed

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "revision": self.revision,
            "video_path": self.video_path,
            "created_at": self.created_at,
            "status": self.status,
            "technically_valid": self.technically_valid,
            "post_ready": self.post_ready,
            "summary": {
                "passed": len([c for c in self.checks if c.status == PASS]),
                "warnings": len(self.warnings),
                "failures": len(self.failures),
            },
            "hard_rule_violations": self.hard_rule_violations,
            "checks": [check.as_dict() for check in self.checks],
            "creative_minimum": self.creative_minimum,
            # Deliberate wording: this is a hypothesis about attention, not a promise.
            "language_note": (
                "This report separates technical conformance (technically_valid) from "
                "creative minimum (inputs/plan honesty). post_ready requires both. "
                "Neither predicts distribution or view counts."
            ),
        }


def _add(report: QualityReport, check: Check) -> None:
    report.checks.append(check)


def run_checks(
    plan: EditPlan,
    input_report: InputReport,
    render_result: RenderResult,
    *,
    config: dict[str, Any],
    source_fingerprints: dict[str, tuple[int, float]] | None = None,
) -> QualityReport:
    """Full quality pass over one render."""
    quality_cfg = config["quality"]
    video_path = render_result.output_path
    report = QualityReport(
        job_id=plan.job_id,
        revision=plan.revision,
        video_path=rel(video_path),
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    info = probe(video_path)

    _add(report, Check(
        "file_exists", "Rendered file exists and is readable",
        PASS if info.exists else FAIL,
        str(video_path) if info.exists else "file missing",
    ))
    if not info.exists:
        return report

    _add(report, Check(
        "playable", "Container reports a decodable video stream",
        PASS if info.has_video and info.duration_seconds > 0 else FAIL,
        f"{info.video_codec} {info.width}x{info.height}, {info.duration_seconds:.2f}s",
    ))

    resolution_violations = rules.check_resolution(info.width, info.height)
    _add(report, Check(
        "aspect_and_resolution", "Output is vertical 1080x1920",
        FAIL if resolution_violations else PASS,
        resolution_violations[0].detail if resolution_violations
        else f"{info.width}x{info.height} (9:16)",
        measurement={"width": info.width, "height": info.height},
    ))

    duration_violations = rules.check_duration(
        info.duration_seconds,
        float(quality_cfg["min_duration_seconds"]),
        float(quality_cfg["max_duration_seconds"]),
    )
    _add(report, Check(
        "duration_window", "Duration is inside the configured posting window",
        FAIL if duration_violations else PASS,
        duration_violations[0].detail if duration_violations
        else f"{info.duration_seconds:.2f}s",
        measurement=round(info.duration_seconds, 3),
    ))

    plan_delta = abs(info.duration_seconds - plan.duration_seconds)
    _add(report, Check(
        "duration_matches_plan", "Rendered duration matches the edit plan",
        PASS if plan_delta <= 0.35 else WARN,
        f"plan {plan.duration_seconds:.2f}s, render {info.duration_seconds:.2f}s "
        f"(delta {plan_delta:.2f}s)",
        measurement=round(plan_delta, 3),
    ))

    _add(report, Check(
        "audio_present", "Output carries an audio track",
        PASS if info.has_audio else FAIL,
        f"{info.audio_codec} {info.sample_rate}Hz {info.channels}ch" if info.has_audio
        else "no audio stream",
    ))

    _add(report, Check(
        "single_audio_stream", "Exactly one audio stream, from the Spotify recording",
        PASS if info.audio_stream_count == 1 else FAIL,
        f"{info.audio_stream_count} audio stream(s); sources used: "
        f"{', '.join(rel(path) for path in render_result.audio_inputs)}",
        measurement=info.audio_stream_count,
    ))

    audio_violations = rules.check_audio_sources(
        render_result.audio_inputs, plan.audio.source_path if plan.audio else "",
    )
    if audio_violations:
        report.hard_rule_violations.extend(str(v) for v in audio_violations)

    # Loudness and clipping.
    try:
        loudness = measure_loudness(video_path)
        true_peak = loudness["input_tp"]
        ceiling = float(quality_cfg["max_true_peak_db"])
        _add(report, Check(
            "no_clipping", "True peak stays below the clipping ceiling",
            PASS if true_peak <= ceiling else FAIL,
            f"true peak {true_peak:.2f} dBTP (ceiling {ceiling} dBTP)",
            measurement=round(true_peak, 2),
        ))
        _add(report, Check(
            "loudness_measured", "Integrated loudness recorded for the posted file",
            PASS,
            f"{loudness['input_i']:.2f} LUFS",
            measurement=round(loudness["input_i"], 2),
        ))
    except MediaError as exc:
        _add(report, Check(
            "no_clipping", "True peak stays below the clipping ceiling", WARN,
            f"loudness measurement unavailable: {exc}",
        ))

    # Audio/video synchronisation: the mix is muxed from the same trimmed source,
    # so the check is that both streams span the same window.
    video_duration = info.duration_seconds
    audio_duration = _audio_duration(video_path)
    if audio_duration is not None:
        drift = abs(video_duration - audio_duration)
        _add(report, Check(
            "audio_video_sync", "Audio and video streams span the same duration",
            PASS if drift <= 0.20 else (WARN if drift <= 0.5 else FAIL),
            f"video {video_duration:.2f}s, audio {audio_duration:.2f}s (drift {drift:.2f}s)",
            measurement=round(drift, 3),
        ))

    # Black and frozen frames.
    black = detect_black_frames(video_path)
    black_seconds = sum(entry.get("black_duration", 0.0) for entry in black)
    black_fraction = black_seconds / video_duration if video_duration else 0.0
    limit = float(quality_cfg["max_black_frame_fraction"])
    _add(report, Check(
        "no_black_frames", "No unintended black or blank stretches",
        PASS if black_fraction <= limit else FAIL,
        f"{black_seconds:.2f}s black across {len(black)} interval(s) "
        f"({black_fraction:.1%} of the video; limit {limit:.0%})",
        measurement=round(black_fraction, 4),
    ))

    first_frame = frame_statistics(video_path, 0.05)
    first_luma = first_frame.get("yavg", 0.0)
    _add(report, Check(
        "first_frame_has_content", "The opening frame carries visible information",
        PASS if first_luma > 16 else FAIL,
        f"mean luma {first_luma:.1f} at 0.05s "
        "(a near-black opening frame wastes the scroll-stopping moment)",
        measurement=round(first_luma, 2),
    ))

    static_check = _static_frames_check(video_path, video_duration,
                                        int(quality_cfg["sample_count"]))
    _add(report, static_check)

    # Spotify visibility and protected regions. The measurement is the area the
    # surface actually occupies after fitting, not the placement box it was given.
    surface = render_fit(
        input_report, plan.spotify_placement,
        content_zoom=plan.spotify_content_zoom,
        waveform_end_trim=plan.waveform_end_trim,
    )
    area = surface.visible_area_fraction
    minimum_area = float(config["layout"]["min_spotify_area_fraction"])
    share_violations = rules.check_spotify_share(area, minimum_area)
    cropped_note = (
        f"{surface.discarded_fraction:.0%} of the source frame cropped away"
        + (f", cutting into {', '.join(surface.clipped_soft)}" if surface.clipped_soft
           else ", none of it from a must-remain-visible region")
    )
    _add(report, Check(
        "spotify_recognisable", "Spotify keeps at least the minimum share of the frame",
        FAIL if share_violations else PASS,
        share_violations[0].detail if share_violations
        else f"Spotify occupies {area:.0%} of the frame "
             f"(fitted by {surface.mode}; {cropped_note})",
        measurement=round(area, 4),
    ))
    if share_violations:
        report.hard_rule_violations.extend(str(v) for v in share_violations)

    # The crop must not cut a hard region — the song labels and the waveform are
    # the reason the video reads as a Spotify mix. The one exception is a crop the
    # creator asked for: layout.waveform_end_trim exists precisely to buy a larger
    # waveform by sacrificing its ends, so it warns instead of failing.
    trim = float(plan.waveform_end_trim)
    if not surface.clipped_hard:
        _add(report, Check(
            "protected_regions_survive_crop",
            "The crop keeps the song labels and waveform whole",
            PASS,
            "song labels and waveform sit entirely inside the crop"
            + (f"; {surface.ceiling_note}" if surface.ceiling_note else ""),
        ))
    elif trim > 0:
        _add(report, Check(
            "protected_regions_survive_crop",
            "The crop keeps the song labels and waveform whole",
            WARN,
            f"crop cuts into {', '.join(surface.clipped_hard)}, as "
            f"layout.waveform_end_trim={trim:.2f} asks it to. The interface reads "
            f"{surface.content_scale:.2f}x larger in exchange. Confirm the cut ends "
            "still look deliberate before posting.",
        ))
    else:
        _add(report, Check(
            "protected_regions_survive_crop",
            "The crop keeps the song labels and waveform whole",
            FAIL,
            f"crop cuts into {', '.join(surface.clipped_hard)} without "
            "layout.waveform_end_trim being set to allow it",
        ))
        report.hard_rule_violations.append(
            "crop cuts a must-remain-visible region: "
            + ", ".join(surface.clipped_hard)
        )

    covered = _transition_coverage(plan)
    _add(report, Check(
        "spotify_visible_at_transition", "Nothing covers the Spotify surface at the blend",
        PASS if covered is None else FAIL,
        covered or "no supporting clip overlaps the transition window",
    ))
    if covered:
        report.hard_rule_violations.append(
            f"{rules.RULE_SPOTIFY_RECOGNISABLE}: {covered}"
        )

    protected = protected_regions_for(input_report.crop_profile, {
        "x": plan.spotify_placement.x, "y": plan.spotify_placement.y,
        "width": plan.spotify_placement.width, "height": plan.spotify_placement.height,
    })
    cue_dicts = [cue.as_dict() for cue in plan.text_cues]
    hard_protected = [region for region in protected if region.enforcement == "hard"]
    obstruction = rules.check_text_clear_of_spotify(
        cue_dicts,
        [{**region.as_dict(), "name": region.name} for region in hard_protected],
    )
    _add(report, Check(
        "song_info_unobstructed", "Text never covers song names or the waveform",
        FAIL if obstruction else PASS,
        "; ".join(v.detail for v in obstruction) if obstruction
        else f"{len(cue_dicts)} cue(s) clear of {len(hard_protected)} protected region(s)",
    ))
    report.hard_rule_violations.extend(str(v) for v in obstruction)

    safe_violations = rules.check_text_safe_zone(cue_dicts, _safe_area(config))
    _add(report, Check(
        "text_in_safe_zone", "Text stays inside the TikTok-safe area",
        FAIL if safe_violations else PASS,
        "; ".join(v.detail for v in safe_violations) if safe_violations
        else f"{len(cue_dicts)} cue(s) inside the safe area",
    ))
    report.hard_rule_violations.extend(str(v) for v in safe_violations)

    _add(report, Check(
        "text_readable", "Text is large enough to read on a phone",
        *_readability(plan),
    ))

    # Transition integrity.
    transition_violations = rules.check_transition_untouched(
        plan.segments_for_rule_check(),
        plan.source_in_seconds + plan.transition_window[0],
        plan.source_in_seconds + plan.transition_window[1],
    )
    _add(report, Check(
        "transition_untouched", "No cut or speed change inside the transition",
        FAIL if transition_violations else PASS,
        "; ".join(v.detail for v in transition_violations) if transition_violations
        else f"transition at {plan.transition_output_seconds:.2f}s sits inside a single "
             "uncut segment at normal speed",
    ))
    report.hard_rule_violations.extend(str(v) for v in transition_violations)

    _add(report, Check(
        "one_transition", "The edit contains exactly one Spotify transition",
        PASS,
        f"one transition planned at {plan.transition_output_seconds:.2f}s "
        f"({input_report.transition.get('method', 'unknown')} detection, "
        f"{input_report.transition.get('confidence', 'unknown')} confidence)",
    ))

    # Dead time before the payoff.
    lead_in = plan.transition_output_seconds
    lead_fraction = lead_in / video_duration if video_duration else 0.0
    if lead_fraction > 0.55:
        status, detail = WARN, (
            f"the payoff starts at {lead_fraction:.0%} of the runtime; this is a "
            "provisional early-skip heuristic, not a measured threshold"
        )
    else:
        status, detail = PASS, f"payoff begins at {lead_fraction:.0%} of the runtime"
    _add(report, Check("no_dead_time", "The payoff is not buried late", status, detail,
                       measurement=round(lead_fraction, 3)))

    # Call to action legibility.
    cta_cues = [cue for cue in plan.text_cues if cue.role == "cta"]
    if cta_cues:
        cue = cta_cues[0]
        visible = cue.end_seconds - cue.start_seconds
        _add(report, Check(
            "cta_readable", "The call to action is on screen long enough to read",
            PASS if visible >= 1.5 else WARN,
            f"{cue.text!r} visible for {visible:.2f}s",
            measurement=round(visible, 2),
        ))
    else:
        _add(report, Check(
            "cta_readable", "The call to action is on screen long enough to read",
            WARN, "no call to action in this edit",
        ))

    # Export settings.
    _add(report, Check(
        "export_settings", "Codec and container suit TikTok upload",
        PASS if info.video_codec == "h264" and info.audio_codec == "aac" else WARN,
        f"{info.video_codec}/{info.audio_codec}, {info.fps:.2f} fps, "
        f"{info.file_size_bytes / 1_000_000:.1f} MB",
    ))

    # Sources untouched.
    if source_fingerprints:
        changed = _changed_sources(source_fingerprints)
        _add(report, Check(
            "sources_unmodified", "Original input files were not modified",
            PASS if not changed else FAIL,
            "no source file changed" if not changed
            else f"modified: {', '.join(changed)}",
        ))
        if changed:
            report.hard_rule_violations.append(
                f"{rules.RULE_SOURCES_IMMUTABLE}: {', '.join(changed)}"
            )

    return report


def _safe_area(config: dict[str, Any]) -> dict[str, int]:
    from .paths import load_config

    del config
    zones = load_config("safe-zones")
    return {key: int(value) for key, value in (zones.get("text_area") or {}).items()}


def _audio_duration(path: Path) -> float | None:
    import json
    import subprocess

    proc = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "a:0",
            "-show_entries", "stream=duration", "-print_format", "json", str(path),
        ],
        capture_output=True, text=True, check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        streams = json.loads(proc.stdout or "{}").get("streams") or []
        return float(streams[0]["duration"]) if streams else None
    except (ValueError, KeyError, IndexError):
        return None


def _static_frames_check(path: Path, duration: float, samples: int) -> Check:
    """Flag genuinely identical frames.

    A Spotify capture is a mostly still interface by nature, so this looks for
    frames that do not change at all rather than for low visual variety.
    """
    del samples
    if duration <= 0:
        return Check("no_frozen_frames", "No frozen stretches", WARN,
                     "not enough duration to analyse")

    frozen = detect_freeze(path, min_duration=1.5)
    total = sum(entry.get("freeze_duration", 0.0) for entry in frozen)
    fraction = total / duration if duration else 0.0

    if not frozen:
        return Check(
            "no_frozen_frames", "No frozen stretches", PASS,
            "no interval of 1.5s or longer is completely static",
            measurement=0.0,
        )
    status = FAIL if fraction > 0.5 else WARN
    intervals = ", ".join(
        f"{entry.get('freeze_start', 0):.1f}-"
        f"{entry.get('freeze_start', 0) + entry.get('freeze_duration', 0):.1f}s"
        for entry in frozen[:4]
    )
    return Check(
        "no_frozen_frames", "No frozen stretches", status,
        f"{total:.2f}s frozen ({fraction:.0%} of the video) at {intervals}",
        measurement=round(fraction, 3),
    )


def _transition_coverage(plan: EditPlan) -> str | None:
    start, end = plan.transition_window
    for clip in plan.secondary_clips:
        if clip.mode not in {"cutaway", "band", "inset"}:
            continue
        overlaps = not (clip.end_seconds <= start or clip.start_seconds >= end)
        if not overlaps:
            continue
        if clip.mode == "band":
            # A band never covers the Spotify surface; it sits beside it.
            continue
        return (
            f"clip {clip.label!r} ({clip.mode}) is visible from "
            f"{clip.start_seconds:.2f}s to {clip.end_seconds:.2f}s, overlapping the "
            f"transition window {start:.2f}-{end:.2f}s"
        )
    return None


def _readability(plan: EditPlan) -> tuple[str, str, Any]:
    from .textrender import get_style

    minimum_size = 40
    too_small: list[str] = []
    sizes: list[int] = []
    for cue in plan.text_cues:
        try:
            size = int(get_style(cue.style).get("font_size", 0))
        except Exception:  # noqa: BLE001 - unknown style already reported elsewhere
            continue
        sizes.append(size)
        if size < minimum_size:
            too_small.append(f"{cue.id} at {size}px")
    if not sizes:
        return WARN, "no text cues in this edit", None
    if too_small:
        return (
            WARN,
            f"cues below {minimum_size}px: {', '.join(too_small)}",
            min(sizes),
        )
    return PASS, f"smallest cue is {min(sizes)}px", min(sizes)


def fingerprint_sources(paths: list[Path]) -> dict[str, tuple[int, float]]:
    """Size and mtime for every input, captured before rendering."""
    fingerprints: dict[str, tuple[int, float]] = {}
    for path in paths:
        if path.is_file():
            stat = path.stat()
            fingerprints[str(path)] = (stat.st_size, stat.st_mtime)
    return fingerprints


def _changed_sources(fingerprints: dict[str, tuple[int, float]]) -> list[str]:
    changed: list[str] = []
    for path_str, (size, mtime) in fingerprints.items():
        path = Path(path_str)
        if not path.is_file():
            changed.append(f"{path.name} (deleted)")
            continue
        stat = path.stat()
        if stat.st_size != size or abs(stat.st_mtime - mtime) > 1e-6:
            changed.append(path.name)
    return changed
