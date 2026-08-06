"""Skill 5 — artist and track research notes.

Version one stores and validates notes rather than fetching them: automated
retrieval is deferred (creator instruction, section 22), and the pipeline must run
with no network at all.

The rule this module enforces is the one that matters: a note without a URL and a
publication date cannot be used in copy. Unsourced context is dropped rather than
paraphrased into a caption.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .paths import RESEARCH_DIR, rel

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_SLUG_RE = re.compile(r"[^a-z0-9]+")

# How stale a note may be before it stops being described as current.
STALE_AFTER_DAYS = 90

RELEVANCE_KINDS = {
    "recent_release",
    "tour_announcement",
    "viral_clip",
    "meme",
    "fan_discussion",
    "lyric_or_theme",
    "artist_connection",
    "track_contrast",
    "tiktok_trend",
    "upcoming_event",
    "cultural_context",
}


class ResearchError(ValueError):
    """Raised when a note cannot be accepted."""


@dataclass
class ResearchNote:
    """One sourced piece of context about an artist or track."""

    id: str
    subject: str
    kind: str
    summary: str
    source_url: str
    source_name: str
    published_date: str
    recorded_at: str
    event_date: str | None = None
    caption_angle: str = ""
    hook_angle: str = ""
    usable_in_copy: bool = True
    staleness_note: str = ""
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _slug(value: str, limit: int = 40) -> str:
    return _SLUG_RE.sub("-", value.lower()).strip("-")[:limit] or "note"


def _days_old(published: str) -> int | None:
    try:
        parsed = datetime.strptime(published, "%Y-%m-%d").date()
    except ValueError:
        return None
    return (date.today() - parsed).days


def add_note(
    *,
    subject: str,
    kind: str,
    summary: str,
    source_url: str,
    source_name: str,
    published_date: str,
    event_date: str | None = None,
    caption_angle: str = "",
    hook_angle: str = "",
) -> ResearchNote:
    """Validate and store a research note."""
    if kind not in RELEVANCE_KINDS:
        raise ResearchError(f"kind {kind!r} not in {sorted(RELEVANCE_KINDS)}")
    if not source_url.startswith(("http://", "https://")):
        raise ResearchError("source_url must be a full http(s) URL")
    if not _DATE_RE.match(published_date):
        raise ResearchError("published_date must be YYYY-MM-DD")
    if event_date and not _DATE_RE.match(event_date):
        raise ResearchError("event_date must be YYYY-MM-DD")
    if not summary.strip():
        raise ResearchError("summary is required")

    warnings: list[str] = []
    staleness = ""
    usable = True
    age = _days_old(published_date)
    if age is None:
        warnings.append("published_date could not be parsed; treating the note as stale")
        usable = False
    elif age > STALE_AFTER_DAYS:
        staleness = (
            f"published {age} days ago; too old to describe as current. Use it for "
            "background only, not as a trend claim."
        )
        warnings.append(staleness)
    elif age < 0:
        warnings.append("published_date is in the future; check the source")
        usable = False

    note = ResearchNote(
        id=f"res-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{_slug(subject, 24)}-{_slug(kind, 16)}",
        subject=subject.strip(),
        kind=kind,
        summary=summary.strip(),
        source_url=source_url.strip(),
        source_name=source_name.strip() or source_url,
        published_date=published_date,
        recorded_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        event_date=event_date,
        caption_angle=caption_angle.strip(),
        hook_angle=hook_angle.strip(),
        usable_in_copy=usable,
        staleness_note=staleness,
        warnings=warnings,
    )
    save(note)
    return note


def save(note: ResearchNote) -> Path:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    path = RESEARCH_DIR / f"{note.id}.yaml"
    payload = note.as_dict()
    payload["artifact_kind"] = "track_research_note"
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def load_all() -> list[ResearchNote]:
    if not RESEARCH_DIR.is_dir():
        return []
    notes: list[ResearchNote] = []
    for path in sorted(RESEARCH_DIR.glob("res-*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.pop("artifact_kind", None)
        for key, value in list(data.items()):
            if isinstance(value, (date, datetime)):
                data[key] = value.isoformat()
        try:
            notes.append(ResearchNote(**data))
        except TypeError:
            continue
    return notes


def notes_for(subjects: list[str]) -> list[dict[str, Any]]:
    """Usable notes matching any of the given artists or track titles."""
    wanted = {subject.strip().lower() for subject in subjects if subject and subject.strip()}
    if not wanted:
        return []
    matched: list[dict[str, Any]] = []
    for note in load_all():
        if not note.usable_in_copy:
            continue
        subject = note.subject.lower()
        if any(term in subject or subject in term for term in wanted):
            matched.append({
                "id": note.id,
                "subject": note.subject,
                "kind": note.kind,
                "summary": note.summary,
                "source_url": note.source_url,
                "source_name": note.source_name,
                "published_date": note.published_date,
                "event_date": note.event_date,
                "caption_angle": note.caption_angle,
                "hook_angle": note.hook_angle,
                "path": rel(RESEARCH_DIR / f"{note.id}.yaml"),
            })
    return matched


def research_brief(subjects: list[str]) -> dict[str, Any]:
    """What is known, and what an agent would still need to look up."""
    found = notes_for(subjects)
    covered = {note["subject"].lower() for note in found}
    missing = [
        subject for subject in subjects
        if subject and subject.strip()
        and not any(subject.strip().lower() in name for name in covered)
    ]
    return {
        "subjects": subjects,
        "notes": found,
        "missing_subjects": missing,
        "instruction": (
            "Add notes with `./process-job research add` before rendering if current "
            "context should shape the hook. Copy will not assert anything that has no "
            "note with a URL and a publication date."
        ),
    }
