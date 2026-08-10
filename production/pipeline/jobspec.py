"""Job definition loading and validation.

A job is a folder containing media plus a ``job.yaml``. Everything the pipeline
needs comes from the job; nothing is inferred from filenames alone unless the job
omits an explicit assignment.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import deep_merge, load_config

VIDEO_SUFFIXES = {".mp4", ".mov", ".mkv", ".webm", ".m4v", ".avi"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}

JOB_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

# Filenames that identify the Spotify recording when job.yaml does not name it.
SPOTIFY_HINTS = ("spotify", "mix", "screen-recording", "screenrecording", "screen_recording")

ASSET_ROLES = {
    "hook",          # plays first, before the Spotify surface takes over
    "overlay",       # picture-in-picture or split partner
    "cutaway",       # brief interruption mid-video
    "payoff",        # appears at or after the transition
    "unassigned",    # role decided by the creative director
}


class JobError(ValueError):
    """Raised when a job folder cannot be turned into a valid JobSpec."""


@dataclass
class AssetSpec:
    """One supporting visual asset."""

    path: Path
    role: str = "unassigned"
    label: str = ""
    start_seconds: float | None = None
    end_seconds: float | None = None
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "filename": self.path.name,
            "role": self.role,
            "label": self.label,
            "start_seconds": self.start_seconds,
            "end_seconds": self.end_seconds,
            "notes": self.notes,
        }


@dataclass
class JobSpec:
    """Validated job definition."""

    job_id: str
    job_dir: Path
    spotify_recording: Path
    assets: list[AssetSpec] = field(default_factory=list)
    creative_direction: dict[str, Any] = field(default_factory=dict)
    render: dict[str, Any] = field(default_factory=dict)
    research: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    tracks: dict[str, Any] = field(default_factory=dict)
    transition: dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def preferred_format(self) -> str:
        return str(self.creative_direction.get("preferred_format", "auto"))

    @property
    def mood(self) -> str:
        return str(self.creative_direction.get("mood", "") or "")

    @property
    def research_enabled(self) -> bool:
        return bool(self.research.get("enabled", False))

    def assets_by_role(self, role: str) -> list[AssetSpec]:
        return [asset for asset in self.assets if asset.role == role]

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "job_dir": str(self.job_dir),
            "spotify_recording": str(self.spotify_recording),
            "assets": [asset.as_dict() for asset in self.assets],
            "creative_direction": self.creative_direction,
            "render": self.render,
            "research": self.research,
            "outputs": self.outputs,
            "tracks": self.tracks,
            "transition": self.transition,
            "notes": self.notes,
            "warnings": self.warnings,
        }


DEFAULT_JOB: dict[str, Any] = {
    "creative_direction": {
        "preferred_format": "auto",
        "mood": "",
        "must_include": [],
        "avoid": [],
        "notes": "",
        # Creative-minimum waivers (explicit opt-outs). Default false.
        "waive_track_metadata": False,
        "waive_empty_asset_fallback": False,
        "waive_generic_hook": False,
    },
    "render": {
        "target_platform": "tiktok",
        "aspect_ratio": "9:16",
        "minimum_duration_seconds": None,
        "maximum_duration_seconds": None,
    },
    "research": {"enabled": False},
    "outputs": {
        "preview": True,
        "final": True,
        "posting_package": True,
        "quality_report": True,
    },
    "tracks": {"first": {}, "second": {}},
    "transition": {},
}


def _is_nine_sixteen(value: Any) -> bool:
    """Accept ``9:16`` however YAML rendered it.

    Unquoted ``9:16`` is a sexagesimal integer under YAML 1.1, which PyYAML still
    implements, so a hand-written job file yields 556 rather than a string.
    """
    if isinstance(value, str):
        return value.strip().replace(" ", "") == "9:16"
    return value == 9 * 60 + 16


def _resolve_media(job_dir: Path, value: str) -> Path:
    candidate = Path(value)
    if not candidate.is_absolute():
        candidate = job_dir / candidate
    return candidate


def _guess_spotify_recording(videos: list[Path]) -> Path | None:
    """Pick the Spotify recording by filename hint, then by longest duration."""
    for video in videos:
        lowered = video.name.lower()
        if any(hint in lowered for hint in SPOTIFY_HINTS):
            return video
    return videos[0] if len(videos) == 1 else None


def load_job(job_dir: Path | str) -> JobSpec:
    """Load and validate a job folder into a JobSpec."""
    job_dir = Path(job_dir).resolve()
    if not job_dir.is_dir():
        raise JobError(f"Job folder does not exist: {job_dir}")

    job_file = job_dir / "job.yaml"
    raw: dict[str, Any] = {}
    if job_file.is_file():
        loaded = yaml.safe_load(job_file.read_text(encoding="utf-8"))
        if loaded is not None and not isinstance(loaded, dict):
            raise JobError(f"{job_file} must contain a YAML mapping")
        raw = loaded or {}
    merged = deep_merge(DEFAULT_JOB, raw)

    warnings: list[str] = []

    # A pipeline setting written at the top level of job.yaml is silently ignored
    # otherwise, which reads as the pipeline disobeying the job file.
    config_sections = set(load_config("defaults"))
    misplaced = sorted(config_sections & set(raw) - set(DEFAULT_JOB))
    for section in misplaced:
        warnings.append(
            f"job.yaml sets {section!r} at the top level, where it does nothing; "
            f"pipeline settings belong under config_overrides.{section}"
        )

    job_id = str(merged.get("job_id") or job_dir.name).strip().lower()
    if not JOB_ID_RE.match(job_id):
        raise JobError(
            f"job_id {job_id!r} must be lowercase alphanumeric with . _ - (max 64 chars)"
        )

    videos = sorted(
        path for path in job_dir.iterdir()
        if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
    )
    if not videos:
        raise JobError(
            f"No video files in {job_dir}. Add the Spotify screen recording "
            f"(one of: {', '.join(sorted(VIDEO_SUFFIXES))})."
        )

    declared = merged.get("spotify_recording")
    if declared:
        spotify = _resolve_media(job_dir, str(declared))
        if not spotify.is_file():
            raise JobError(f"spotify_recording {declared!r} not found at {spotify}")
    else:
        guessed = _guess_spotify_recording(videos)
        if guessed is None:
            raise JobError(
                f"{len(videos)} videos present but job.yaml does not name "
                "spotify_recording. Set it explicitly, or include 'spotify' in the "
                "recording's filename."
            )
        spotify = guessed
        warnings.append(
            f"spotify_recording inferred as {spotify.name}; declare it in job.yaml to be certain"
        )

    declared_assets = merged.get("additional_assets") or []
    assets: list[AssetSpec] = []
    claimed = {spotify.resolve()}

    for entry in declared_assets:
        if isinstance(entry, str):
            entry = {"path": entry}
        if not isinstance(entry, dict) or not entry.get("path"):
            raise JobError(f"additional_assets entry must have a 'path': {entry!r}")
        path = _resolve_media(job_dir, str(entry["path"]))
        if not path.is_file():
            raise JobError(f"additional asset not found: {path}")
        role = str(entry.get("role", "unassigned"))
        if role not in ASSET_ROLES:
            raise JobError(
                f"asset role {role!r} invalid; use one of {sorted(ASSET_ROLES)}"
            )
        assets.append(AssetSpec(
            path=path,
            role=role,
            label=str(entry.get("label", "") or path.stem),
            start_seconds=entry.get("start_seconds"),
            end_seconds=entry.get("end_seconds"),
            notes=str(entry.get("notes", "") or ""),
        ))
        claimed.add(path.resolve())

    # Any remaining video in the folder becomes an unassigned asset.
    if not declared_assets:
        for video in videos:
            if video.resolve() in claimed:
                continue
            assets.append(AssetSpec(path=video, label=video.stem))
            claimed.add(video.resolve())

    notes_file = job_dir / "notes.txt"
    notes = merged["creative_direction"].get("notes", "") or ""
    if notes_file.is_file():
        file_notes = notes_file.read_text(encoding="utf-8").strip()
        notes = f"{notes}\n{file_notes}".strip() if notes else file_notes

    defaults = load_config("defaults")
    render_overrides: dict[str, Any] = {}
    minimum = merged["render"].get("minimum_duration_seconds")
    maximum = merged["render"].get("maximum_duration_seconds")
    if minimum is not None:
        render_overrides.setdefault("duration", {})["minimum_seconds"] = float(minimum)
    if maximum is not None:
        render_overrides.setdefault("duration", {})["maximum_seconds"] = float(maximum)
    config = deep_merge(defaults, render_overrides)
    config = deep_merge(config, merged.get("config_overrides") or {})

    if not _is_nine_sixteen(merged["render"].get("aspect_ratio", "9:16")):
        raise JobError(
            "render.aspect_ratio must be '9:16' — TikTok output is vertical only "
            f"(got {merged['render'].get('aspect_ratio')!r})"
        )

    research = dict(merged.get("research") or {})
    if research.get("enabled") is None:
        research["enabled"] = bool(config.get("research", {}).get("enabled", False))

    return JobSpec(
        job_id=job_id,
        job_dir=job_dir,
        spotify_recording=spotify,
        assets=assets,
        creative_direction=dict(merged.get("creative_direction") or {}),
        render=dict(merged.get("render") or {}),
        research=research,
        outputs=dict(merged.get("outputs") or {}),
        tracks=dict(merged.get("tracks") or {}),
        transition=dict(merged.get("transition") or {}),
        notes=notes,
        config=config,
        warnings=warnings,
        raw=raw,
    )


def write_job_template(job_dir: Path, job_id: str, spotify_filename: str) -> Path:
    """Write a starter job.yaml into an existing job folder."""
    job_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "job_id": job_id,
        "spotify_recording": spotify_filename,
        "additional_assets": [],
        "tracks": {
            "first": {"title": "", "artist": ""},
            "second": {"title": "", "artist": ""},
        },
        "transition": {"seconds": None},
        "creative_direction": {
            "preferred_format": "auto",
            "mood": "",
            "must_include": [],
            "avoid": [],
            "notes": "",
            # Creative-minimum waivers — leave false unless you intentionally ship
            # without tracks / with the recording-only fallback format.
            "waive_track_metadata": False,
            "waive_empty_asset_fallback": False,
            "waive_generic_hook": False,
        },
        "render": {
            "target_platform": "tiktok",
            "aspect_ratio": "9:16",
            "minimum_duration_seconds": 15,
            "maximum_duration_seconds": 45,
        },
        "research": {"enabled": False},
        "outputs": {
            "preview": True,
            "final": True,
            "posting_package": True,
            "quality_report": True,
        },
    }
    destination = job_dir / "job.yaml"
    destination.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return destination
