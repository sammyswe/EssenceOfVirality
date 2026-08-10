"""Skill 1 — Spotify input inspection.

Validates the supplied media, measures the Spotify recording's geometry, selects a
crop profile, locates the regions that must stay visible, and finds the transition.
Produces the structured report every later stage reads.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import audio_analysis
from .jobspec import AssetSpec, JobSpec
from .om import detect_scenes, probe_media
from .paths import load_config
from .probe import MediaError, detect_letterbox, probe


@dataclass
class Region:
    """A rectangle in output-canvas pixels.

    ``enforcement`` is ``hard`` when text may never cover the region (song
    information, waveform) and ``soft`` when overlapping is allowed but recorded.
    """

    name: str
    x1: int
    y1: int
    x2: int
    y2: int
    enforcement: str = "hard"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CropProfile:
    name: str
    description: str
    crop: dict[str, float]
    must_remain_visible: dict[str, dict[str, float]]
    fit: str = "cover"
    warning: str = ""
    match_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AssetReport:
    """Inspection result for one supporting clip."""

    filename: str
    path: str
    role: str
    label: str
    usable: bool
    duration_seconds: float
    width: int
    height: int
    is_vertical: bool
    has_audio: bool
    scene_count: int | None
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InputReport:
    """Everything the creative and render stages need to know about the inputs."""

    job_id: str
    spotify: dict[str, Any]
    crop_profile: CropProfile
    protected_regions: list[Region]
    transition: dict[str, Any]
    beats: dict[str, Any] | None
    loudness: dict[str, Any] | None
    assets: list[AssetReport]
    blocking_problems: list[str]
    warnings: list[str]
    backends: dict[str, str]

    @property
    def ok(self) -> bool:
        return not self.blocking_problems

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "spotify": self.spotify,
            "crop_profile": self.crop_profile.as_dict(),
            "protected_regions": [region.as_dict() for region in self.protected_regions],
            "transition": self.transition,
            "beats": self.beats,
            "loudness": self.loudness,
            "assets": [asset.as_dict() for asset in self.assets],
            "blocking_problems": self.blocking_problems,
            "warnings": self.warnings,
            "backends": self.backends,
        }


def select_crop_profile(width: int, height: int) -> CropProfile:
    """Choose the crop profile whose aspect-ratio window contains the source."""
    config = load_config("crop-profiles")
    profiles: dict[str, Any] = config.get("profiles", {})
    ratio = (width / height) if height else 0.0

    chosen_name = config.get("default_profile", "vertical_full")
    reason = f"default profile; source ratio {ratio:.3f} matched no window"
    for name, profile in profiles.items():
        match = profile.get("match") or {}
        low = float(match.get("aspect_ratio_min", -1))
        high = float(match.get("aspect_ratio_max", -1))
        if low <= ratio <= high:
            chosen_name = name
            reason = f"source ratio {ratio:.3f} within [{low}, {high}]"
            break

    profile = profiles.get(chosen_name, {})
    return CropProfile(
        name=chosen_name,
        description=str(profile.get("description", "")).strip(),
        crop=dict(profile.get("crop") or {"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0}),
        must_remain_visible=dict(profile.get("must_remain_visible") or {}),
        fit=str(profile.get("fit", "cover")),
        warning=str(profile.get("warning", "")).strip(),
        match_reason=reason,
    )


def enforcement_names() -> tuple[set[str], set[str]]:
    """Region names text may never cover, and names it should merely avoid.

    A region named by neither list is treated as hard: an unclassified part of the
    Spotify interface is more likely to matter than not.
    """
    enforcement_cfg = load_config("crop-profiles").get("region_enforcement") or {}
    return set(enforcement_cfg.get("hard") or []), set(enforcement_cfg.get("soft") or [])


def protected_regions_for(
    profile: CropProfile, placement: dict[str, int]
) -> list[Region]:
    """Map the profile's must-stay-visible fractions onto the output canvas.

    ``placement`` is where the Spotify surface sits in the 1080x1920 frame:
    ``{"x": .., "y": .., "width": .., "height": ..}``.
    """
    hard_names, soft_names = enforcement_names()

    regions: list[Region] = []
    for name, box in profile.must_remain_visible.items():
        x1 = placement["x"] + int(placement["width"] * float(box.get("x", 0.0)))
        y1 = placement["y"] + int(placement["height"] * float(box.get("y", 0.0)))
        x2 = x1 + int(placement["width"] * float(box.get("width", 0.0)))
        y2 = y1 + int(placement["height"] * float(box.get("height", 0.0)))
        if name in hard_names:
            enforcement = "hard"
        elif name in soft_names:
            enforcement = "soft"
        else:
            enforcement = "hard"
        regions.append(
            Region(name=name, x1=x1, y1=y1, x2=x2, y2=y2, enforcement=enforcement)
        )
    return regions


def hard_regions(regions: list[Region]) -> list[Region]:
    return [region for region in regions if region.enforcement == "hard"]


def _inspect_asset(asset: AssetSpec, *, want_scenes: bool) -> AssetReport:
    info = probe(asset.path)
    notes: list[str] = list(info.warnings)
    usable = info.exists and info.has_video and info.duration_seconds > 0

    if not info.exists:
        notes.append("file missing")
    elif not info.has_video:
        notes.append("no video stream; supporting assets must contain picture")
    if info.has_audio:
        notes.append("audio present but will be discarded — the mix is the only audio source")
    if usable and info.duration_seconds < 0.5:
        notes.append("shorter than 0.5s; too brief to read on screen")
        usable = False

    scene_count: int | None = None
    if usable and want_scenes:
        outcome = detect_scenes(asset.path)
        if outcome.success:
            scene_count = int(outcome.data.get("scene_count") or 0)

    return AssetReport(
        filename=asset.path.name,
        path=str(asset.path),
        role=asset.role,
        label=asset.label,
        usable=usable,
        duration_seconds=round(info.duration_seconds, 3),
        width=info.width,
        height=info.height,
        is_vertical=info.is_vertical,
        has_audio=info.has_audio,
        scene_count=scene_count,
        notes=notes,
    )


def inspect(job: JobSpec, *, analyse_beats: bool = True) -> InputReport:
    """Run the full input inspection for a job."""
    config = job.config
    blocking: list[str] = []
    warnings: list[str] = list(job.warnings)
    backends: dict[str, str] = {}

    probe_outcome = probe_media(job.spotify_recording)
    backends["probe"] = probe_outcome.backend
    info = probe(job.spotify_recording)

    if not info.exists:
        blocking.append(f"Spotify recording not found: {job.spotify_recording}")
    if info.exists and not info.has_video:
        blocking.append("Spotify recording has no video stream")
    if info.exists and not info.has_audio:
        blocking.append(
            "Spotify recording has no audio stream. The mix audio is the product — "
            "re-record with system audio capture enabled."
        )
    if info.exists and info.duration_seconds <= 0:
        blocking.append("Spotify recording reports zero duration; the file may be truncated")

    minimum = float(config["duration"]["minimum_seconds"])
    if info.exists and 0 < info.duration_seconds < minimum:
        warnings.append(
            f"recording is {info.duration_seconds:.1f}s, shorter than the {minimum:.0f}s "
            "minimum output duration; the edit cannot be padded because the audio "
            "cannot be extended"
        )

    profile = select_crop_profile(info.width, info.height)
    if profile.warning:
        warnings.append(profile.warning)
    if info.exists and not info.is_vertical:
        warnings.append(
            f"source is {info.width}x{info.height} (landscape); cropping to 9:16 will "
            "discard horizontal information — record in portrait where possible"
        )

    letterbox = detect_letterbox(job.spotify_recording) if info.exists else None
    if letterbox and info.width and info.height:
        trimmed_fraction = 1.0 - (letterbox["width"] * letterbox["height"]) / (
            info.width * info.height
        )
        if trimmed_fraction > 0.02:
            warnings.append(
                f"black bars detected: usable picture is "
                f"{letterbox['width']}x{letterbox['height']} at "
                f"({letterbox['x']},{letterbox['y']}); {trimmed_fraction:.0%} of the frame "
                "is padding"
            )

    transition_dict: dict[str, Any] = {}
    beats_dict: dict[str, Any] | None = None
    loudness_dict: dict[str, Any] | None = None

    if info.exists and info.has_audio:
        declared = job.transition.get("seconds")
        try:
            estimate = audio_analysis.detect_transition(
                job.spotify_recording,
                hop_seconds=float(config["transition"]["hop_seconds"]),
                search_start_fraction=float(config["transition"]["search_start_fraction"]),
                search_end_fraction=float(config["transition"]["search_end_fraction"]),
                declared_seconds=float(declared) if declared is not None else None,
                duration_seconds=info.duration_seconds,
            )
            transition_dict = estimate.as_dict()
            backends["transition"] = estimate.method
            if estimate.confidence == "low":
                warnings.append(
                    "transition detection confidence is low — set transition.seconds in "
                    "job.yaml if the emphasis lands in the wrong place"
                )
        except MediaError as exc:
            blocking.append(f"transition analysis failed: {exc}")

        if analyse_beats:
            grid = audio_analysis.estimate_beats(job.spotify_recording)
            if grid is not None:
                beats_dict = grid.as_dict()
                backends["beats"] = grid.method
            else:
                warnings.append(
                    "no stable tempo detected; visual changes will align to the "
                    "transition rather than to a beat grid"
                )

        report = audio_analysis.analyse_loudness(
            job.spotify_recording,
            target_lufs=float(config["audio"]["loudness_target_lufs"]),
            tolerance=float(config["audio"]["normalise_skip_tolerance_lufs"]),
            true_peak_ceiling=float(config["audio"]["loudness_true_peak_db"]),
        )
        if report is not None:
            loudness_dict = report.as_dict()
            backends["loudness"] = "ffmpeg:loudnorm"

    assets = [
        _inspect_asset(asset, want_scenes=True)
        for asset in job.assets
    ]
    unusable = [asset.filename for asset in assets if not asset.usable]
    if unusable:
        warnings.append(f"ignoring unusable supporting assets: {', '.join(unusable)}")

    spotify_payload = info.as_dict()
    spotify_payload["letterbox"] = letterbox
    spotify_payload["probe_backend"] = probe_outcome.backend

    return InputReport(
        job_id=job.job_id,
        spotify=spotify_payload,
        crop_profile=profile,
        protected_regions=[],  # filled once the layout places the Spotify surface
        transition=transition_dict,
        beats=beats_dict,
        loudness=loudness_dict,
        assets=assets,
        blocking_problems=blocking,
        warnings=warnings,
        backends=backends,
    )
