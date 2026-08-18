"""Per-hook copy profiles.

Each Higgsfield hook clip can carry a profile that describes what is on screen
and binds that clip to overlay wording, allowed CTAs, and exactly three
captions to rotate across posts that reuse the clip. Profiles live as YAML
files under ``production/config/hook-profiles/`` (one file per hook). Only
profiles with status ``testing`` or ``proven`` can drive a render; drafts are
written after analysing a new clip and wait for creator approval — same
lifecycle as the copy bank.

Matching: a job's hook asset (role ``hook``, else the first usable supporting
clip) matches a profile when the asset's filename stem or label equals one of
the profile's ``asset_stems`` (case-insensitive).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from . import copybank
from .paths import CONFIG_DIR

PROFILES_DIR = CONFIG_DIR / "hook-profiles"
ACTIVE_STATUSES = frozenset({"testing", "proven"})
REQUIRED_CAPTION_COUNT = 3


class HookProfileError(ValueError):
    """Raised when a profile file is malformed."""


@dataclass
class HookCaption:
    id: str
    template: str
    status: str = "testing"
    notes: str = ""


@dataclass
class HookProfile:
    id: str
    path: Path
    status: str
    asset_stems: list[str]
    description: str
    overlay_hook_ids: list[str] = field(default_factory=list)
    overlay_texts: list[str] = field(default_factory=list)
    cta_ids: list[str] = field(default_factory=list)
    captions: list[HookCaption] = field(default_factory=list)
    fiction_signal: str = ""
    notes: str = ""

    @property
    def active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    def active_captions(self) -> list[HookCaption]:
        return [
            caption for caption in self.captions
            if caption.status in ACTIVE_STATUSES
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "path": str(self.path),
            "status": self.status,
            "asset_stems": self.asset_stems,
            "description": self.description,
            "overlay_hook_ids": self.overlay_hook_ids,
            "overlay_texts": self.overlay_texts,
            "cta_ids": self.cta_ids,
            "captions": [
                {
                    "id": caption.id,
                    "template": caption.template,
                    "status": caption.status,
                    "notes": caption.notes,
                }
                for caption in self.captions
            ],
            "fiction_signal": self.fiction_signal,
            "notes": self.notes,
        }


def _normalise_stem(value: str) -> str:
    return Path(str(value)).stem.strip().lower()


def load_profile(path: Path) -> HookProfile:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise HookProfileError(f"{path} must contain a YAML mapping")

    profile_id = str(loaded.get("id") or path.stem).strip()
    status = str(loaded.get("status", "draft")).strip()
    if status not in copybank.STATUSES:
        raise HookProfileError(
            f"{path} status {status!r} invalid; expected one of {copybank.STATUSES}"
        )

    stems = loaded.get("asset_stems") or []
    if isinstance(stems, str):
        stems = [stems]
    stems = [_normalise_stem(stem) for stem in stems if str(stem).strip()]
    if not stems:
        raise HookProfileError(f"{path} needs at least one asset_stem")

    description = str(loaded.get("description", "") or "").strip()
    if not description:
        raise HookProfileError(
            f"{path} needs a description of what happens on screen — "
            "captions are written from it"
        )

    captions_raw = loaded.get("captions") or []
    if not isinstance(captions_raw, list):
        raise HookProfileError(f"{path} captions must be a list")
    captions: list[HookCaption] = []
    for index, entry in enumerate(captions_raw):
        if not isinstance(entry, dict):
            raise HookProfileError(f"{path} captions[{index}] must be a mapping")
        template = str(entry.get("template", "")).strip()
        if not template:
            raise HookProfileError(f"{path} captions[{index}] has empty template")
        captions.append(HookCaption(
            id=str(entry.get("id") or f"{profile_id}-cap-{index + 1}"),
            template=template,
            status=str(entry.get("status", "testing")).strip() or "testing",
            notes=str(entry.get("notes", "") or ""),
        ))

    if len(captions) != REQUIRED_CAPTION_COUNT:
        raise HookProfileError(
            f"{path} must declare exactly {REQUIRED_CAPTION_COUNT} captions "
            f"(found {len(captions)}) — each hook rotates a fixed trio"
        )

    hook_ids = loaded.get("overlay_hook_ids") or loaded.get("hook_ids") or []
    texts = loaded.get("overlay_texts") or []
    cta_ids = loaded.get("cta_ids") or []
    if isinstance(hook_ids, str):
        hook_ids = [hook_ids]
    if isinstance(texts, str):
        texts = [texts]
    if isinstance(cta_ids, str):
        cta_ids = [cta_ids]

    return HookProfile(
        id=profile_id,
        path=path,
        status=status,
        asset_stems=stems,
        description=description,
        overlay_hook_ids=[str(value).strip() for value in hook_ids if str(value).strip()],
        overlay_texts=[str(value).strip() for value in texts if str(value).strip()],
        cta_ids=[str(value).strip() for value in cta_ids if str(value).strip()],
        captions=captions,
        fiction_signal=str(loaded.get("fiction_signal", "") or ""),
        notes=str(loaded.get("notes", "") or ""),
    )


def load_all(directory: Path | None = None) -> list[HookProfile]:
    root = directory or PROFILES_DIR
    if not root.is_dir():
        return []
    profiles: list[HookProfile] = []
    for path in sorted(root.glob("*.yaml")):
        if path.name.startswith("_"):
            continue  # templates / notes, not live profiles
        profiles.append(load_profile(path))
    return profiles


def active_profiles(directory: Path | None = None) -> list[HookProfile]:
    return [profile for profile in load_all(directory) if profile.active]


def match_for_asset(
    *,
    filename: str = "",
    label: str = "",
    directory: Path | None = None,
) -> HookProfile | None:
    """Return the active profile whose stems match this hook asset, if any."""
    candidates = {
        _normalise_stem(filename),
        _normalise_stem(label),
    }
    candidates.discard("")
    if not candidates:
        return None
    for profile in active_profiles(directory):
        if candidates & set(profile.asset_stems):
            return profile
    return None


def match_from_assets(
    assets: list[Any], directory: Path | None = None
) -> HookProfile | None:
    """Prefer a role=hook asset; otherwise try every usable supporting clip."""
    ordered = [
        asset for asset in assets
        if getattr(asset, "usable", True) and getattr(asset, "role", "") == "hook"
    ]
    if not ordered:
        ordered = [asset for asset in assets if getattr(asset, "usable", True)]
    for asset in ordered:
        matched = match_for_asset(
            filename=getattr(asset, "filename", "") or getattr(asset, "path", Path()).name,
            label=getattr(asset, "label", "") or "",
            directory=directory,
        )
        if matched is not None:
            return matched
    return None


def summary(directory: Path | None = None) -> dict[str, Any]:
    profiles = load_all(directory)
    by_status: dict[str, int] = {}
    for profile in profiles:
        by_status[profile.status] = by_status.get(profile.status, 0) + 1
    return {
        "directory": str(directory or PROFILES_DIR),
        "total": len(profiles),
        "by_status": by_status,
        "profiles": [
            {"id": profile.id, "status": profile.status, "stems": profile.asset_stems}
            for profile in profiles
        ],
    }
