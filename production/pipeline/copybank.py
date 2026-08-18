"""The copy testing bank — hooks, CTAs, captions and pinned comments.

``production/config/copy-bank.yaml`` holds every piece of wording the pipeline
may put on screen or in a posting package, each with a lifecycle status:

- ``draft`` — proposed, never rendered, awaiting the creator's review;
- ``testing`` — approved for rotation, performance unknown;
- ``proven`` — repeatedly associated with strong posts;
- ``retired`` — pulled, kept for the record with the reason.

The pipeline draws only from ``testing`` and ``proven`` entries, so a freshly
drafted idea cannot reach a render until the creator has ruled on it. Status
changes go through :func:`set_status` (surfaced as ``./process-job copy ...``),
which rewrites the YAML — commentary therefore lives in ``notes`` fields the
rewrite preserves, never in YAML comments.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .paths import CONFIG_DIR

BANK_PATH = CONFIG_DIR / "copy-bank.yaml"

SECTIONS = ("hooks", "ctas", "captions", "pinned_comments")
STATUSES = ("draft", "testing", "proven", "retired")
ACTIVE_STATUSES = frozenset({"testing", "proven"})


class CopyBankError(ValueError):
    """Raised for unknown entries, bad statuses, or a malformed bank file."""


def load_bank(path: Path | None = None) -> dict[str, Any]:
    """Load the bank. Deliberately uncached: the CLI mutates statuses."""
    bank_path = path or BANK_PATH
    if not bank_path.is_file():
        raise CopyBankError(f"Copy bank not found: {bank_path}")
    loaded = yaml.safe_load(bank_path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise CopyBankError(f"{bank_path} must contain a YAML mapping")
    for section in SECTIONS:
        entries = loaded.get(section) or []
        if not isinstance(entries, list):
            raise CopyBankError(f"{bank_path} section {section!r} must be a list")
        for entry in entries:
            status = str(entry.get("status", "")).strip()
            if status not in STATUSES:
                raise CopyBankError(
                    f"{bank_path} entry {entry.get('id')!r} has status {status!r}; "
                    f"expected one of {STATUSES}"
                )
    return loaded


def entries(section: str, path: Path | None = None) -> list[dict[str, Any]]:
    if section not in SECTIONS:
        raise CopyBankError(f"Unknown section {section!r}; expected one of {SECTIONS}")
    return list(load_bank(path).get(section) or [])


def active(section: str, path: Path | None = None) -> list[dict[str, Any]]:
    """Entries the pipeline is allowed to render or post."""
    return [
        entry for entry in entries(section, path)
        if str(entry.get("status")) in ACTIVE_STATUSES
    ]


def find(entry_id: str, path: Path | None = None) -> tuple[str, dict[str, Any]]:
    """Locate an entry by id. Returns (section, entry)."""
    bank = load_bank(path)
    for section in SECTIONS:
        for entry in bank.get(section) or []:
            if str(entry.get("id")) == entry_id:
                return section, entry
    raise CopyBankError(f"No copy-bank entry with id {entry_id!r}")


def find_by_text(text: str, path: Path | None = None) -> tuple[str, dict[str, Any]] | None:
    """Match rendered wording back to its bank entry, for attribution."""
    needle = text.strip()
    bank = load_bank(path)
    for section in SECTIONS:
        for entry in bank.get(section) or []:
            candidate = str(entry.get("text") or entry.get("template") or "").strip()
            if candidate and candidate == needle:
                return section, entry
    return None


def set_status(
    entry_id: str, status: str, *, note: str = "", path: Path | None = None
) -> dict[str, Any]:
    """Move an entry through its lifecycle and rewrite the bank file."""
    if status not in STATUSES:
        raise CopyBankError(f"Status {status!r} invalid; expected one of {STATUSES}")
    bank_path = path or BANK_PATH
    bank = load_bank(bank_path)
    target: dict[str, Any] | None = None
    for section in SECTIONS:
        for entry in bank.get(section) or []:
            if str(entry.get("id")) == entry_id:
                target = entry
                break
        if target:
            break
    if target is None:
        raise CopyBankError(f"No copy-bank entry with id {entry_id!r}")

    previous = str(target.get("status"))
    target["status"] = status
    if note:
        existing = str(target.get("notes", "") or "").strip()
        target["notes"] = f"{existing} [{previous}->{status}: {note}]".strip()

    bank_path.write_text(
        yaml.safe_dump(bank, sort_keys=False, allow_unicode=True, width=88),
        encoding="utf-8",
    )
    return target


def intent_weights(path: Path | None = None) -> dict[str, int]:
    """CTA intent → relative weight for growth-phase rotation."""
    bank = load_bank(path)
    raw = bank.get("cta_intent_weights") or {}
    return {str(key): max(0, int(value)) for key, value in raw.items()}


def summary(path: Path | None = None) -> dict[str, Any]:
    bank = load_bank(path)
    result: dict[str, Any] = {"path": str(path or BANK_PATH), "sections": {}}
    for section in SECTIONS:
        section_entries = bank.get(section) or []
        counts: dict[str, int] = {}
        for entry in section_entries:
            counts[str(entry["status"])] = counts.get(str(entry["status"]), 0) + 1
        result["sections"][section] = {
            "total": len(section_entries),
            "by_status": counts,
        }
    return result
