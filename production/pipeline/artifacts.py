"""The envelope every structured file the pipeline writes must carry.

The repository validates YAML artifacts against JSON Schema and checks reference
integrity across them (ADR 0004). Both tools key off the same four fields:
``artifact_type`` maps a file to its schema, ``id`` makes it referenceable,
``created_at`` orders it, and ``produced_by`` records which stage wrote it.

Production artifacts join that scheme rather than inventing a parallel one, so a
render's edit plan is checked by the same CI step as a claim record.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

# Stage names double as the `produced_by` value, which is how a reader tells a
# quality report written by the checker from one hand-edited by the creator.
PIPELINE = "workflow:production-pipeline"
CREATOR = "creator"

ID_RE = re.compile(r"^(plan|qr|cm|pkg|vpm|fb|pref|exp|post|res)-[a-z0-9][a-z0-9-]*$")


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def today() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def stamp(job_id: str, revision: int) -> str:
    """The id suffix shared by every artifact belonging to one render."""
    return f"{job_id}-r{revision}"


def artifact_id(prefix: str, *parts: str) -> str:
    """Build an id the repository's reference checker will accept.

    Uppercase and punctuation are folded out rather than rejected: ids are built
    from job names and timestamps that the creator controls, and a job called
    ``Job_001`` should not fail a render.
    """
    slug = "-".join(str(part) for part in parts if str(part))
    slug = re.sub(r"[^a-z0-9-]+", "-", slug.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    identifier = f"{prefix}-{slug}"
    if not ID_RE.match(identifier):
        raise ValueError(f"cannot build a valid artifact id from {prefix!r} and {parts!r}")
    return identifier


def envelope(
    artifact_type: str,
    identifier: str,
    *,
    produced_by: str = PIPELINE,
    created_at: str | None = None,
    inputs: list[str] | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "artifact_type": artifact_type,
        "id": identifier,
        "created_at": created_at or now(),
        "produced_by": produced_by,
    }
    if inputs:
        payload["inputs"] = list(inputs)
    return payload


def write(
    path: Path,
    artifact_type: str,
    identifier: str,
    body: dict[str, Any],
    *,
    produced_by: str = PIPELINE,
    created_at: str | None = None,
    inputs: list[str] | None = None,
) -> Path:
    """Write ``body`` as YAML with the envelope fields first."""
    payload = envelope(
        artifact_type, identifier,
        produced_by=produced_by, created_at=created_at, inputs=inputs,
    )
    for key, value in body.items():
        if key not in payload:
            payload[key] = value
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return path


def strip_envelope(data: dict[str, Any]) -> dict[str, Any]:
    """Drop the envelope so a record can be rebuilt from its own fields."""
    stripped = dict(data)
    for key in ("artifact_type", "artifact_kind", "produced_by", "inputs"):
        stripped.pop(key, None)
    return stripped
