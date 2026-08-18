"""Scroll-stop technique bank for the production pipeline.

Techniques live in the experimental skill reference
``.cursor/skills/experimental/produce-scroll-stop-hook/references/techniques.md``
and are applied when building a ``hook-overlay`` edit plan. This module only
loads rows with ``status: active``; rejected craft stays documented but is not
applied.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from .paths import REPO_ROOT

TECHNIQUES_PATH = (
    REPO_ROOT
    / ".cursor"
    / "skills"
    / "experimental"
    / "produce-scroll-stop-hook"
    / "references"
    / "techniques.md"
)

_FENCE = re.compile(r"```ya?ml\s*\n(.*?)```", re.DOTALL | re.IGNORECASE)


@dataclass
class Technique:
    id: str
    name: str
    scroll_stop_move: str
    intended_viewer_effect: str = ""
    requirements: list[str] = field(default_factory=list)
    contraindications: list[str] = field(default_factory=list)
    channel_fit: str = "pass"
    status: str = "active"
    evidence: list[str] = field(default_factory=list)

    @property
    def active(self) -> bool:
        return self.status == "active" and self.channel_fit != "reject"

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "scroll_stop_move": self.scroll_stop_move,
            "intended_viewer_effect": self.intended_viewer_effect,
            "requirements": self.requirements,
            "contraindications": self.contraindications,
            "channel_fit": self.channel_fit,
            "status": self.status,
            "evidence": self.evidence,
        }


def _coerce(entry: dict[str, Any]) -> Technique | None:
    tech_id = str(entry.get("id", "")).strip()
    name = str(entry.get("name", "")).strip()
    move = str(entry.get("scroll_stop_move", "")).strip()
    if not tech_id or not name or not move:
        return None
    req = entry.get("requirements") or []
    contra = entry.get("contraindications") or []
    evidence = entry.get("evidence") or []
    if isinstance(req, str):
        req = [req]
    if isinstance(contra, str):
        contra = [contra]
    if isinstance(evidence, str):
        evidence = [evidence]
    return Technique(
        id=tech_id,
        name=name,
        scroll_stop_move=" ".join(move.split()),
        intended_viewer_effect=" ".join(
            str(entry.get("intended_viewer_effect", "")).split()
        ),
        requirements=[str(item).strip() for item in req if str(item).strip()],
        contraindications=[str(item).strip() for item in contra if str(item).strip()],
        channel_fit=str(entry.get("channel_fit", "pass")).strip() or "pass",
        status=str(entry.get("status", "active")).strip() or "active",
        evidence=[str(item).strip() for item in evidence if str(item).strip()],
    )


def load_techniques(path: Path | None = None) -> list[Technique]:
    """Parse the techniques.md YAML fence into Technique rows."""
    target = path or TECHNIQUES_PATH
    if not target.is_file():
        return []
    text = target.read_text(encoding="utf-8")
    match = _FENCE.search(text)
    if match is None:
        return []
    loaded = yaml.safe_load(match.group(1))
    if not isinstance(loaded, list):
        return []
    techniques: list[Technique] = []
    for entry in loaded:
        if not isinstance(entry, dict):
            continue
        technique = _coerce(entry)
        if technique is not None:
            techniques.append(technique)
    return techniques


def active_techniques(path: Path | None = None) -> list[Technique]:
    return [technique for technique in load_techniques(path) if technique.active]


@dataclass
class TechniqueApplication:
    id: str
    name: str
    applied: bool
    reason: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "applied": self.applied,
            "reason": self.reason,
        }


def apply_to_hook_overlay(
    *,
    has_hook_clip: bool,
    hook_text: str,
    profile_id: str,
    fiction_signal: str,
) -> list[TechniqueApplication]:
    """Decide which active techniques fire for this hook-overlay plan.

    The renderer already enforces mix-audio-from-frame-zero, muted overlay,
    beat-snapped handover, and Spotify visibility. This function records which
    retained craft those choices satisfy, and which rows are skipped with a
    reason — matching the produce-scroll-stop-hook output contract.
    """
    applications: list[TechniqueApplication] = []
    for technique in active_techniques():
        tech_id = technique.id
        if not has_hook_clip:
            applications.append(TechniqueApplication(
                id=tech_id,
                name=technique.name,
                applied=False,
                reason="no hook clip on this job — cannot apply scroll-stop craft",
            ))
            continue

        if tech_id.endswith("pattern-interrupt-open") or tech_id.endswith(
            "depth-motion-entry"
        ):
            applications.append(TechniqueApplication(
                id=tech_id,
                name=technique.name,
                applied=True,
                reason=(
                    "hook-overlay opens on a full-frame AI clip (fiction motion / "
                    "pattern break) while mix audio already plays"
                ),
            ))
            continue

        if tech_id.endswith("visual-confirm-fast"):
            applications.append(TechniqueApplication(
                id=tech_id,
                name=technique.name,
                applied=True,
                reason=(
                    "handover dissolves to the Spotify capture within the recipe "
                    "visibility ceiling so the open promise is confirmed on-screen"
                ),
            ))
            continue

        if tech_id.endswith("payoff-rehook"):
            applications.append(TechniqueApplication(
                id=tech_id,
                name=technique.name,
                applied=True,
                reason=(
                    "overlay / anticipation copy points at the untouched mix "
                    "switch as the later payoff"
                ),
            ))
            continue

        if tech_id.endswith("subjective-stakes-line"):
            if hook_text.strip():
                applications.append(TechniqueApplication(
                    id=tech_id,
                    name=technique.name,
                    applied=True,
                    reason=(
                        f"on-screen hook {hook_text!r}"
                        + (f" from profile {profile_id}" if profile_id else " from bank")
                    ),
                ))
            else:
                applications.append(TechniqueApplication(
                    id=tech_id,
                    name=technique.name,
                    applied=False,
                    reason="no hook overlay text selected",
                ))
            continue

        if tech_id.endswith("prop-incongruity"):
            if fiction_signal or profile_id:
                applications.append(TechniqueApplication(
                    id=tech_id,
                    name=technique.name,
                    applied=True,
                    reason=(
                        "Higgsfield hook is fiction-signalled; surprising props stay "
                        "inside the AI scene rather than as fabricated reality"
                        + (f" ({fiction_signal})" if fiction_signal else "")
                    ),
                ))
            else:
                applications.append(TechniqueApplication(
                    id=tech_id,
                    name=technique.name,
                    applied=False,
                    reason="no fiction signal recorded for this hook clip",
                ))
            continue

        applications.append(TechniqueApplication(
            id=tech_id,
            name=technique.name,
            applied=True,
            reason="active technique retained for hook-overlay plans",
        ))
    return applications
