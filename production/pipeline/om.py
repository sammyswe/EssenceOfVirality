"""Adapter around the pinned OpenMontage clone.

OpenMontage is AGPL-3.0 and lives outside this repository (ADR 0001). This module
is the only place that imports from the clone, so the rest of the pipeline never
depends on upstream module paths.

Every helper degrades to a local FFmpeg implementation when the clone is absent,
and records which path it took in ``ToolOutcome.backend`` so reports state
honestly what actually ran.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .paths import OPENMONTAGE_DIR, openmontage_clone
from .probe import MediaError, probe, run

# Tools verified present at pin 4eab34c5 and runnable without any API key.
KEY_FREE_TOOLS = {
    "audio_probe": "tools.analysis.audio_probe:AudioProbe",
    "scene_detect": "tools.analysis.scene_detect:SceneDetect",
    "frame_sampler": "tools.analysis.frame_sampler:FrameSampler",
    "audio_energy": "tools.analysis.audio_energy:AudioEnergy",
    "video_trimmer": "tools.video.video_trimmer:VideoTrimmer",
    "auto_reframe": "tools.video.auto_reframe:AutoReframe",
    "video_compose": "tools.video.video_compose:VideoCompose",
    "video_stitch": "tools.video.video_stitch:VideoStitch",
    "audio_mixer": "tools.audio.audio_mixer:AudioMixer",
    "subtitle_gen": "tools.subtitle.subtitle_gen:SubtitleGen",
    "export_bundle": "tools.publishers.export_bundle:ExportBundle",
}


@dataclass
class ToolOutcome:
    """Result of an adapter call, naming the backend that produced it."""

    success: bool
    backend: str
    data: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def pinned_ref() -> str:
    ref_file = OPENMONTAGE_DIR / "PINNED_REF"
    if not ref_file.is_file():
        return ""
    for line in ref_file.read_text(encoding="utf-8").splitlines():
        candidate = line.strip()
        if len(candidate) == 40 and all(c in "0123456789abcdef" for c in candidate):
            return candidate
    return ""


def clone_available() -> bool:
    clone = openmontage_clone()
    return (clone / "tools" / "base_tool.py").is_file()


def clone_head() -> str:
    clone = openmontage_clone()
    if not (clone / ".git").exists():
        return ""
    try:
        proc = run(["git", "-C", str(clone), "rev-parse", "HEAD"], timeout=30)
    except MediaError:
        return ""
    return proc.stdout.strip()


def pin_status() -> dict[str, Any]:
    """Report whether the clone is present and matches PINNED_REF."""
    expected = pinned_ref()
    if not clone_available():
        return {
            "available": False,
            "expected_ref": expected,
            "actual_ref": "",
            "matches_pin": False,
            "note": (
                "OpenMontage clone not found; the pipeline runs its FFmpeg fallbacks. "
                "See docs/guides/setup.md to install it."
            ),
        }
    actual = clone_head()
    return {
        "available": True,
        "expected_ref": expected,
        "actual_ref": actual,
        "matches_pin": bool(expected) and actual == expected,
        "note": "" if actual == expected else "clone HEAD differs from PINNED_REF",
    }


_PATH_READY = False


def _ensure_import_path() -> bool:
    global _PATH_READY
    if not clone_available():
        return False
    if not _PATH_READY:
        clone = str(openmontage_clone().resolve())
        if clone not in sys.path:
            sys.path.insert(0, clone)
        _PATH_READY = True
    return True


def load_tool(name: str):
    """Instantiate an OpenMontage tool by adapter name, or return None."""
    target = KEY_FREE_TOOLS.get(name)
    if not target or not _ensure_import_path():
        return None
    module_path, _, class_name = target.partition(":")
    try:
        module = __import__(module_path, fromlist=[class_name])
        return getattr(module, class_name)()
    except Exception:  # noqa: BLE001 - upstream import problems must not break the run
        return None


def _call(name: str, payload: dict[str, Any]) -> ToolOutcome | None:
    tool = load_tool(name)
    if tool is None:
        return None
    try:
        result = tool.execute(payload)
    except Exception as exc:  # noqa: BLE001 - upstream tools raise varied exceptions
        return ToolOutcome(False, f"openmontage:{name}", error=str(exc))
    return ToolOutcome(
        success=bool(result.success),
        backend=f"openmontage:{name}",
        data=dict(result.data or {}),
        error=result.error,
    )


# --- Capabilities used by the pipeline -------------------------------------------------


def probe_media(path: Path | str) -> ToolOutcome:
    """Technical probe. Prefers OpenMontage ``audio_probe``, falls back to ffprobe."""
    outcome = _call("audio_probe", {"input_path": str(path)})
    if outcome and outcome.success:
        return outcome
    info = probe(path)
    return ToolOutcome(info.exists, "ffprobe", data=info.as_dict())


def detect_scenes(path: Path | str, *, min_scene_seconds: float = 0.6) -> ToolOutcome:
    """Scene boundaries for supporting clips."""
    outcome = _call("scene_detect", {
        "input_path": str(path),
        "method": "content",
        "min_scene_length_seconds": min_scene_seconds,
    })
    if outcome and outcome.success:
        return outcome
    return ToolOutcome(False, "unavailable", error="scene_detect requires the OpenMontage clone")


def sample_frames(
    path: Path | str, timestamps: list[float], output_dir: Path
) -> ToolOutcome:
    """Extract frames at given timestamps for review and thumbnails."""
    output_dir.mkdir(parents=True, exist_ok=True)
    outcome = _call("frame_sampler", {
        "input_path": str(path),
        "strategy": "timestamps",
        "timestamps": timestamps,
        "output_dir": str(output_dir),
        "format": "jpg",
        "quality": 2,
    })
    if outcome and outcome.success:
        return outcome

    from .probe import extract_frame

    frames = []
    for index, timestamp in enumerate(timestamps):
        destination = output_dir / f"frame_{index:02d}.jpg"
        extract_frame(path, timestamp, destination)
        frames.append({
            "path": str(destination), "timestamp_seconds": timestamp, "index": index,
        })
    return ToolOutcome(True, "ffmpeg", data={"frames": frames, "frame_count": len(frames)})


def reframe_to_portrait(source: Path, destination: Path) -> ToolOutcome:
    """Convert a supporting clip to 1080x1920. OpenMontage ``auto_reframe`` first."""
    outcome = _call("auto_reframe", {
        "input_path": str(source),
        "output_path": str(destination),
        "target_aspect": "portrait",
        "target_width": 1080,
        "target_height": 1920,
    })
    if outcome and outcome.success:
        return outcome
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source),
        "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
        "-an", "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", str(destination),
    ])
    return ToolOutcome(True, "ffmpeg", data={"output": str(destination)})


def trim(source: Path, destination: Path, start: float, end: float) -> ToolOutcome:
    """Cut a segment. OpenMontage ``video_trimmer`` first."""
    outcome = _call("video_trimmer", {
        "operation": "cut",
        "input_path": str(source),
        "output_path": str(destination),
        "start_seconds": start,
        "end_seconds": end,
        "codec": "libx264",
    })
    if outcome and outcome.success:
        return outcome
    run([
        "ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-to", f"{end:.3f}",
        "-i", str(source), "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", str(destination),
    ])
    return ToolOutcome(True, "ffmpeg", data={"output": str(destination)})


def encode_tiktok(source: Path, destination: Path) -> ToolOutcome:
    """Final encode through the OpenMontage ``tiktok`` media profile."""
    outcome = _call("video_compose", {
        "operation": "encode",
        "input_path": str(source),
        "output_path": str(destination),
        "profile": "tiktok",
        "codec": "libx264",
        "crf": 20,
    })
    if outcome and outcome.success:
        return outcome
    run([
        "ffmpeg", "-y", "-v", "error", "-i", str(source),
        "-s", "1080x1920", "-r", "30",
        "-c:v", "libx264", "-crf", "20", "-preset", "medium", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(destination),
    ])
    return ToolOutcome(True, "ffmpeg", data={"output": str(destination)})


def write_export_bundle(
    video_path: Path,
    title: str,
    export_dir: Path,
    *,
    description: str = "",
    hashtags: list[str] | None = None,
    thumbnail_path: Path | None = None,
) -> ToolOutcome:
    """Package the render for manual posting. OpenMontage ``export_bundle`` first."""
    payload: dict[str, Any] = {
        "video_path": str(video_path),
        "title": title,
        "export_dir": str(export_dir),
        "description": description,
        "hashtags": hashtags or [],
        "platform": "tiktok",
        "visibility": "private",
    }
    if thumbnail_path is not None:
        payload["thumbnail_path"] = str(thumbnail_path)
    outcome = _call("export_bundle", payload)
    if outcome and outcome.success:
        return outcome
    export_dir.mkdir(parents=True, exist_ok=True)
    return ToolOutcome(
        False, "unavailable",
        error="export_bundle requires the OpenMontage clone; the posting package is "
              "still written by the pipeline itself",
    )


def capability_report() -> dict[str, Any]:
    """Which backend each pipeline capability will use on this machine."""
    available = clone_available()
    return {
        "openmontage": pin_status(),
        "capabilities": {
            "probe": "openmontage:audio_probe" if available else "ffprobe",
            "scene_detection": "openmontage:scene_detect" if available else "unavailable",
            "frame_sampling": "openmontage:frame_sampler" if available else "ffmpeg",
            "reframe": "openmontage:auto_reframe" if available else "ffmpeg",
            "trim": "openmontage:video_trimmer" if available else "ffmpeg",
            "final_encode": "openmontage:video_compose(tiktok)" if available else "ffmpeg",
            "export_bundle": "openmontage:export_bundle" if available else "pipeline-native",
            # Always ours: OpenMontage has no text-overlay operation without Node/Remotion.
            "composite_and_text": "ffmpeg:filter_complex (pipeline-native)",
            "transition_detection": "pipeline-native (spectral flux)",
            "loudness": "ffmpeg:loudnorm",
        },
    }
