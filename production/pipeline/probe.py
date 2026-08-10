"""FFmpeg/FFprobe helpers.

Every subprocess call in the pipeline funnels through here so that failures carry
the command that produced them.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class MediaError(RuntimeError):
    """Raised when ffmpeg/ffprobe fails or a file is unusable."""


def require_binaries() -> None:
    missing = [name for name in ("ffmpeg", "ffprobe") if shutil.which(name) is None]
    if missing:
        raise MediaError(
            f"Missing required binaries: {', '.join(missing)}. "
            "Install FFmpeg (apt install ffmpeg / brew install ffmpeg)."
        )


def run(cmd: list[str], *, timeout: int = 3600) -> subprocess.CompletedProcess:
    """Run a command, raising MediaError with stderr context on failure."""
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise MediaError(f"Command timed out after {timeout}s: {' '.join(cmd[:6])} …") from exc
    if proc.returncode != 0:
        tail = (proc.stderr or "").strip().splitlines()[-12:]
        raise MediaError(
            "Command failed (exit {code}):\n  {cmd}\n  {err}".format(
                code=proc.returncode,
                cmd=" ".join(cmd),
                err="\n  ".join(tail) or "(no stderr)",
            )
        )
    return proc


@dataclass
class MediaInfo:
    """Normalised probe result for one media file."""

    path: str
    exists: bool
    duration_seconds: float = 0.0
    width: int = 0
    height: int = 0
    fps: float = 0.0
    video_codec: str = ""
    audio_codec: str = ""
    sample_rate: int = 0
    channels: int = 0
    file_size_bytes: int = 0
    bitrate_kbps: float = 0.0
    rotation: int = 0
    has_video: bool = False
    has_audio: bool = False
    audio_stream_count: int = 0
    warnings: list[str] = field(default_factory=list)

    @property
    def aspect_ratio(self) -> float:
        return (self.width / self.height) if self.height else 0.0

    @property
    def is_vertical(self) -> bool:
        return self.height > self.width

    def as_dict(self) -> dict[str, Any]:
        data = {
            key: getattr(self, key)
            for key in (
                "path", "exists", "duration_seconds", "width", "height", "fps",
                "video_codec", "audio_codec", "sample_rate", "channels",
                "file_size_bytes", "bitrate_kbps", "rotation", "has_video",
                "has_audio", "audio_stream_count", "warnings",
            )
        }
        data["aspect_ratio"] = round(self.aspect_ratio, 4)
        return data


def _parse_rate(raw: str) -> float:
    if not raw:
        return 0.0
    if "/" in raw:
        num, _, den = raw.partition("/")
        try:
            denominator = float(den)
            return float(num) / denominator if denominator else 0.0
        except ValueError:
            return 0.0
    try:
        return float(raw)
    except ValueError:
        return 0.0


def _rotation_of(stream: dict[str, Any]) -> int:
    tags = stream.get("tags") or {}
    if "rotate" in tags:
        try:
            return int(float(tags["rotate"])) % 360
        except (TypeError, ValueError):
            pass
    for side in stream.get("side_data_list") or []:
        if "rotation" in side:
            try:
                return int(float(side["rotation"])) % 360
            except (TypeError, ValueError):
                continue
    return 0


def probe(path: Path | str) -> MediaInfo:
    """Probe a media file. Never raises for a missing file — check ``.exists``."""
    path = Path(path)
    if not path.is_file():
        return MediaInfo(path=str(path), exists=False, warnings=["file does not exist"])

    proc = run([
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ], timeout=120)
    data = json.loads(proc.stdout or "{}")
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    audio = audio_streams[0] if audio_streams else {}

    info = MediaInfo(
        path=str(path),
        exists=True,
        duration_seconds=float(fmt.get("duration") or 0.0),
        width=int(video.get("width") or 0),
        height=int(video.get("height") or 0),
        fps=round(_parse_rate(video.get("avg_frame_rate") or video.get("r_frame_rate") or ""), 3),
        video_codec=video.get("codec_name", ""),
        audio_codec=audio.get("codec_name", ""),
        sample_rate=int(audio.get("sample_rate") or 0),
        channels=int(audio.get("channels") or 0),
        file_size_bytes=int(fmt.get("size") or 0),
        bitrate_kbps=round(float(fmt.get("bit_rate") or 0) / 1000, 1),
        rotation=_rotation_of(video),
        has_video=bool(video_streams),
        has_audio=bool(audio_streams),
        audio_stream_count=len(audio_streams),
    )

    # A rotation tag swaps the effective display dimensions.
    if info.rotation in (90, 270):
        info.width, info.height = info.height, info.width
        info.warnings.append(f"rotation tag {info.rotation}deg applied to reported dimensions")
    if info.duration_seconds <= 0:
        info.warnings.append("container reports no duration")
    if not info.has_video:
        info.warnings.append("no video stream")
    if info.audio_stream_count > 1:
        info.warnings.append(f"{info.audio_stream_count} audio streams; only the first is used")

    return info


def measure_loudness(path: Path | str, *, stream: str = "a:0") -> dict[str, float]:
    """EBU R128 loudness measurement via the ``loudnorm`` filter's analysis pass."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
            "-map", stream, "-af", "loudnorm=print_format=json", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    stderr = proc.stderr or ""
    start = stderr.rfind("{")
    end = stderr.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise MediaError("loudnorm analysis produced no JSON block")
    payload = json.loads(stderr[start:end + 1])
    return {
        "input_i": float(payload.get("input_i", 0.0)),
        "input_tp": float(payload.get("input_tp", 0.0)),
        "input_lra": float(payload.get("input_lra", 0.0)),
        "input_thresh": float(payload.get("input_thresh", 0.0)),
        "target_offset": float(payload.get("target_offset", 0.0)),
    }


def extract_frame(video: Path | str, timestamp: float, destination: Path) -> Path:
    """Write a single JPEG frame at ``timestamp``."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    run([
        "ffmpeg", "-y", "-v", "error",
        "-ss", f"{max(timestamp, 0):.3f}", "-i", str(video),
        "-frames:v", "1", "-q:v", "2", str(destination),
    ], timeout=180)
    return destination


def frame_statistics(video: Path | str, timestamp: float) -> dict[str, float]:
    """Mean luma and its spread for one frame — used for black/frozen detection."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-ss", f"{max(timestamp, 0):.3f}", "-i", str(video),
            "-frames:v", "1", "-vf", "signalstats,metadata=mode=print", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    stats: dict[str, float] = {}
    for line in (proc.stderr or "").splitlines():
        # Lines arrive as "[Parsed_metadata_1 @ 0x..] lavfi.signalstats.YAVG=16.5".
        marker = line.find("lavfi.signalstats.")
        if marker == -1:
            continue
        key, _, value = line[marker + len("lavfi.signalstats."):].strip().partition("=")
        try:
            stats[key.strip().lower()] = float(value)
        except ValueError:
            continue
    return stats


def detect_freeze(
    video: Path | str, *, noise_db: float = -55.0, min_duration: float = 1.5
) -> list[dict[str, float]]:
    """Frozen intervals reported by the ``freezedetect`` filter.

    A Spotify capture is mostly a still interface, so this looks for genuinely
    identical frames rather than for low visual variety.
    """
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
            "-vf", f"freezedetect=n={noise_db}dB:d={min_duration}",
            "-an", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    intervals: list[dict[str, float]] = []
    current: dict[str, float] = {}
    for line in (proc.stderr or "").splitlines():
        for key in ("freeze_start", "freeze_duration", "freeze_end"):
            marker = line.find(f"lavfi.freezedetect.{key}")
            if marker == -1:
                continue
            _, _, value = line[marker:].partition(":")
            if not value:
                _, _, value = line[marker:].partition("=")
            try:
                current[key] = float(value.strip())
            except ValueError:
                continue
            if key == "freeze_end" and current:
                intervals.append(dict(current))
                current = {}
    if current.get("freeze_start") is not None and "freeze_end" not in current:
        intervals.append(dict(current))
    return intervals


def detect_black_frames(
    video: Path | str, *, min_duration: float = 0.15, threshold: float = 0.06
) -> list[dict[str, float]]:
    """Return black intervals reported by the ``blackdetect`` filter."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats", "-i", str(video),
            "-vf", f"blackdetect=d={min_duration}:pix_th={threshold}",
            "-an", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    intervals: list[dict[str, float]] = []
    for line in (proc.stderr or "").splitlines():
        if "black_start" not in line:
            continue
        entry: dict[str, float] = {}
        for token in line.split():
            if ":" in token and token.split(":")[0] in {
                "black_start", "black_end", "black_duration"
            }:
                key, _, value = token.partition(":")
                try:
                    entry[key] = float(value)
                except ValueError:
                    continue
        if entry:
            intervals.append(entry)
    return intervals


def detect_letterbox(video: Path | str, *, sample_seconds: float = 3.0) -> dict[str, int] | None:
    """Detect black bars with ``cropdetect``. Returns crop geometry or None."""
    proc = subprocess.run(
        [
            "ffmpeg", "-hide_banner", "-nostats",
            "-t", f"{sample_seconds}", "-i", str(video),
            "-vf", "cropdetect=limit=24:round=2:reset=0", "-an", "-f", "null", "-",
        ],
        capture_output=True, text=True, check=False,
    )
    last: str | None = None
    for line in (proc.stderr or "").splitlines():
        marker = line.rfind("crop=")
        if marker != -1:
            last = line[marker + len("crop="):].strip()
    if not last:
        return None
    try:
        width, height, x, y = (int(part) for part in last.split(":"))
    except ValueError:
        return None
    return {"width": width, "height": height, "x": x, "y": y}


def decode_mono_pcm(video: Path | str, *, sample_rate: int = 22050) -> "list[float]":
    """Decode the first audio stream to mono float samples via numpy."""
    import numpy as np

    proc = subprocess.run(
        [
            "ffmpeg", "-v", "error", "-i", str(video),
            "-map", "a:0", "-ac", "1", "-ar", str(sample_rate),
            "-f", "s16le", "-acodec", "pcm_s16le", "-",
        ],
        capture_output=True, check=False,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise MediaError("could not decode audio stream for analysis")
    samples = np.frombuffer(proc.stdout, dtype="<i2").astype("float32") / 32768.0
    return samples
