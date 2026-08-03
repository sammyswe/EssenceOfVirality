#!/usr/bin/env python3
"""Lint project-authored skills in .cursor/skills/ (ADR 0005).

Checks structural quality only (deterministic). Instruction quality beyond banned
patterns is the skill critic's job, not CI's.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    BANNED_SKILL_PATTERNS,
    CONFIDENCE_VALUES,
    EVIDENCE_BASIS_VALUES,
    EVIDENCE_REQUIRED_BANKS,
    MATURITY_VALUES,
    SEMVER_RE,
    SKILL_BANKS,
    SKILLS_DIR,
    parse_frontmatter,
    rel,
)

MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)#\s]+)[^)]*\)")


def lint_skill(skill_dir: Path, seen_names: dict) -> list[str]:
    errors: list[str] = []
    skill_md = skill_dir / "SKILL.md"
    where = rel(skill_md)
    if not skill_md.is_file():
        return [f"{rel(skill_dir)}: missing SKILL.md"]

    fm, body = parse_frontmatter(skill_md)
    if fm is None:
        return [f"{where}: missing or unparsable YAML frontmatter"]

    name = fm.get("name")
    if not name:
        errors.append(f"{where}: frontmatter missing 'name'")
    elif name != skill_dir.name:
        errors.append(f"{where}: name '{name}' != folder '{skill_dir.name}'")
    if name:
        if name in seen_names:
            errors.append(f"{where}: duplicate skill name (also {seen_names[name]})")
        else:
            seen_names[name] = where

    if not fm.get("description"):
        errors.append(f"{where}: frontmatter missing 'description'")

    bank = skill_dir.parent.name
    if bank not in SKILL_BANKS:
        errors.append(f"{where}: bank '{bank}' not one of {SKILL_BANKS}")

    meta = fm.get("metadata") or {}
    if not isinstance(meta, dict):
        errors.append(f"{where}: metadata must be a map")
        meta = {}

    version = str(meta.get("version", ""))
    if not SEMVER_RE.match(version):
        errors.append(f"{where}: metadata.version '{version}' is not semver")

    maturity = meta.get("maturity")
    if maturity not in MATURITY_VALUES:
        errors.append(f"{where}: metadata.maturity '{maturity}' invalid")

    confidence = meta.get("confidence")
    if confidence not in CONFIDENCE_VALUES:
        errors.append(f"{where}: metadata.confidence '{confidence}' invalid")

    basis = meta.get("evidence_basis")
    if not isinstance(basis, list) or not set(basis) <= EVIDENCE_BASIS_VALUES:
        errors.append(f"{where}: metadata.evidence_basis must be a list drawn from {sorted(EVIDENCE_BASIS_VALUES)}")

    if "requires_human_approval" not in meta or not isinstance(meta["requires_human_approval"], bool):
        errors.append(f"{where}: metadata.requires_human_approval (bool) required")

    if bank in EVIDENCE_REQUIRED_BANKS and maturity != "deprecated":
        refs = meta.get("evidence_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{where}: domain-bank skills need non-empty metadata.evidence_refs")
        if not basis:
            errors.append(f"{where}: domain-bank skills need non-empty metadata.evidence_basis")

    for pattern in BANNED_SKILL_PATTERNS:
        m = pattern.search(body)
        if m:
            errors.append(f"{where}: banned phrase '{m.group(0)}' (overclaiming/vague language)")

    for match in MD_LINK_RE.finditer(body):
        target = match.group(1)
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        if not (skill_dir / target).exists() and not (skill_md.parent / target).exists():
            errors.append(f"{where}: referenced file '{target}' does not exist")

    return errors


def lint_all(skills_dir: Path = SKILLS_DIR) -> list[str]:
    errors: list[str] = []
    seen_names: dict = {}
    count = 0
    if not skills_dir.is_dir():
        return [f"{rel(skills_dir)}: missing skills directory"]
    for skill_md in sorted(skills_dir.rglob("SKILL.md")):
        count += 1
        errors.extend(lint_skill(skill_md.parent, seen_names))
    print(f"lint_skills: {count} skills checked")
    return errors


def main() -> int:
    errors = lint_all()
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print(f"lint_skills: FAILED ({len(errors)} errors)", file=sys.stderr)
        return 1
    print("lint_skills: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
