"""Skill 9 (storage half) — approved and proposed preferences.

A preference is a lasting creative rule inferred from creator feedback. Proposals
are written freely; promotion to ``preferences/approved/`` requires explicit
creator approval or a repeated, consistent signal. Nothing here silently rewrites
a skill file.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from . import artifacts
from .paths import PREFERENCES_APPROVED, PREFERENCES_PROPOSED, rel

# Number of independent, consistent feedback events required to auto-promote
# a proposal when the creator has not stated it as a lasting rule.
PROMOTION_THRESHOLD = 3

SCOPES = {"global", "format", "artist", "asset", "one_off"}

VALID_KEYS = {
    "preferred_format",
    "avoid_format",
    "text_style",
    "hook_style",
    "cta_style",
    "layout",
    "spotify_fraction",
    "pip_scale",
    "pip_corner",
    "zoom_emphasis",
    "progress_bar",
    "hook_duration",
    "lead_in_seconds",
    "caption_voice",
    "hashtag_strategy",
    "banned_device",
}

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(value: str, limit: int = 48) -> str:
    return _SLUG_RE.sub("-", value.lower()).strip("-")[:limit] or "preference"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass
class Preference:
    """One lasting creative rule."""

    id: str
    key: str
    value: Any
    scope: str
    scope_value: str
    statement: str
    status: str                      # proposed | approved | retired
    confidence: str                  # low | medium | high
    created_at: str
    updated_at: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    supersedes: str | None = None
    approved_by: str | None = None
    approved_at: str | None = None
    retired_reason: str = ""

    @property
    def support_count(self) -> int:
        return len(self.evidence)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _path_for(preference: Preference) -> Path:
    directory = (
        PREFERENCES_APPROVED if preference.status == "approved" else PREFERENCES_PROPOSED
    )
    return directory / f"{preference.id}.yaml"


def _write(preference: Preference) -> Path:
    return artifacts.write(
        _path_for(preference),
        "creator_preference", preference.id, preference.as_dict(),
        produced_by=artifacts.CREATOR,
        created_at=preference.created_at,
    )


def _load_dir(directory: Path) -> list[Preference]:
    if not directory.is_dir():
        return []
    preferences: list[Preference] = []
    for path in sorted(directory.glob("*.yaml")):
        data = artifacts.strip_envelope(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
        for key, value in list(data.items()):
            if isinstance(value, (date, datetime)):
                data[key] = value.isoformat()
        try:
            preferences.append(Preference(**data))
        except TypeError:
            continue
    return preferences


def load_all(*, include_proposed: bool = False) -> list[Preference]:
    preferences = _load_dir(PREFERENCES_APPROVED)
    if include_proposed:
        preferences.extend(_load_dir(PREFERENCES_PROPOSED))
    return preferences


def make_id(key: str, scope: str, scope_value: str, statement: str) -> str:
    scope_part = _slug(scope_value) if scope_value else scope
    return artifacts.artifact_id(
        "pref", artifacts.today(),
        _slug(key, 24), _slug(scope_part, 16), _slug(statement, 20),
    )


def propose(
    *,
    key: str,
    value: Any,
    statement: str,
    scope: str = "global",
    scope_value: str = "",
    confidence: str = "low",
    evidence: Iterable[dict[str, Any]] = (),
) -> Preference:
    """Record a proposed preference. Never auto-applies."""
    if key not in VALID_KEYS:
        raise ValueError(f"preference key {key!r} not in {sorted(VALID_KEYS)}")
    if scope not in SCOPES:
        raise ValueError(f"preference scope {scope!r} not in {sorted(SCOPES)}")

    evidence_list = list(evidence)
    existing = find(key=key, scope=scope, scope_value=scope_value, include_proposed=True)
    if existing is not None and existing.status != "retired":
        # Same rule proposed again: accumulate support rather than duplicating.
        known = {entry.get("ref") for entry in existing.evidence}
        for entry in evidence_list:
            if entry.get("ref") not in known:
                existing.evidence.append(entry)
        existing.value = value
        existing.updated_at = _now()
        if existing.support_count >= PROMOTION_THRESHOLD:
            existing.confidence = "medium"
        _write(existing)
        return existing

    now = _now()
    preference = Preference(
        id=make_id(key, scope, scope_value, statement),
        key=key,
        value=value,
        scope=scope,
        scope_value=scope_value,
        statement=statement,
        status="proposed",
        confidence=confidence,
        created_at=now,
        updated_at=now,
        evidence=evidence_list,
    )
    _write(preference)
    return preference


def find(
    *, key: str, scope: str, scope_value: str, include_proposed: bool = False
) -> Preference | None:
    for preference in load_all(include_proposed=include_proposed):
        if (
            preference.key == key
            and preference.scope == scope
            and preference.scope_value == scope_value
            and preference.status != "retired"
        ):
            return preference
    return None


def approve(preference_id: str, *, approved_by: str = "creator") -> Preference:
    """Promote a proposal to an approved preference."""
    source = PREFERENCES_PROPOSED / f"{preference_id}.yaml"
    if not source.is_file():
        if (PREFERENCES_APPROVED / f"{preference_id}.yaml").is_file():
            raise ValueError(f"{preference_id} is already approved")
        raise FileNotFoundError(f"No proposed preference {preference_id!r}")

    data = artifacts.strip_envelope(yaml.safe_load(source.read_text(encoding="utf-8")) or {})
    preference = Preference(**data)

    superseded = find(
        key=preference.key, scope=preference.scope, scope_value=preference.scope_value
    )
    if superseded is not None:
        preference.supersedes = superseded.id
        superseded.status = "retired"
        superseded.retired_reason = f"superseded by {preference.id}"
        superseded.updated_at = _now()
        # Retired rules stay recoverable in the proposed directory.
        (PREFERENCES_APPROVED / f"{superseded.id}.yaml").unlink(missing_ok=True)
        superseded.status = "retired"
        artifacts.write(
            PREFERENCES_PROPOSED / f"{superseded.id}.yaml",
            "creator_preference", superseded.id, superseded.as_dict(),
            produced_by=artifacts.CREATOR,
            created_at=superseded.created_at,
        )

    preference.status = "approved"
    preference.approved_by = approved_by
    preference.approved_at = _now()
    preference.updated_at = preference.approved_at
    if preference.confidence == "low":
        preference.confidence = "medium"
    _write(preference)
    source.unlink(missing_ok=True)
    return preference


def promotable() -> list[Preference]:
    """Proposals with enough repeated, consistent support to offer for approval."""
    return [
        preference for preference in _load_dir(PREFERENCES_PROPOSED)
        if preference.status == "proposed"
        and preference.support_count >= PROMOTION_THRESHOLD
    ]


@dataclass
class ResolvedPreferences:
    """Approved preferences narrowed to one job's context."""

    values: dict[str, Any] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    banned_devices: list[str] = field(default_factory=list)
    avoided_formats: list[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def refs(self) -> list[str]:
        return sorted(set(self.sources.values()))


def resolve(
    *, format_family: str | None = None, artists: Iterable[str] = ()
) -> ResolvedPreferences:
    """Collapse approved preferences into the values that apply to this job.

    Precedence: artist scope beats format scope beats global scope.
    """
    artist_set = {artist.strip().lower() for artist in artists if artist}
    resolved = ResolvedPreferences()
    ranking = {"global": 0, "format": 1, "artist": 2}
    best_rank: dict[str, int] = {}

    for preference in load_all():
        if preference.status != "approved":
            continue
        if preference.scope == "format":
            if not format_family or preference.scope_value != format_family:
                continue
        elif preference.scope == "artist":
            if preference.scope_value.strip().lower() not in artist_set:
                continue
        elif preference.scope not in {"global"}:
            continue

        if preference.key == "banned_device":
            resolved.banned_devices.append(str(preference.value))
            resolved.sources[f"banned_device:{preference.value}"] = preference.id
            continue
        if preference.key == "avoid_format":
            resolved.avoided_formats.append(str(preference.value))
            resolved.sources[f"avoid_format:{preference.value}"] = preference.id
            continue

        rank = ranking.get(preference.scope, 0)
        if rank >= best_rank.get(preference.key, -1):
            best_rank[preference.key] = rank
            resolved.values[preference.key] = preference.value
            resolved.sources[preference.key] = preference.id

    return resolved


def summary() -> dict[str, Any]:
    approved = _load_dir(PREFERENCES_APPROVED)
    proposed = _load_dir(PREFERENCES_PROPOSED)
    return {
        "approved_count": len(approved),
        "proposed_count": len([p for p in proposed if p.status == "proposed"]),
        "retired_count": len([p for p in proposed if p.status == "retired"]),
        "promotable": [
            {
                "id": p.id,
                "statement": p.statement,
                "support_count": p.support_count,
            }
            for p in promotable()
        ],
        "approved": [
            {"id": p.id, "key": p.key, "value": p.value, "scope": p.scope,
             "statement": p.statement, "path": rel(_path_for(p))}
            for p in approved
        ],
    }
