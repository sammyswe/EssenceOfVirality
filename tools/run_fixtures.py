#!/usr/bin/env python3
"""Structural checks for behavioural fixtures in evaluation/fixtures/.

Behavioural evaluation (running skills against fixtures) is agent-driven and out of
CI scope; this tool only guarantees fixtures are well-formed and reference real skills.
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, SKILLS_DIR, rel

REQUIRED_FIELDS = ["fixture_id", "title", "description", "video", "known_problems", "expected_diagnoses", "must_preserve"]
REQUIRED_VIDEO_FIELDS = ["duration_seconds", "format", "content"]


def existing_skill_names() -> set[str]:
    return {p.parent.name for p in SKILLS_DIR.rglob("SKILL.md")}


def check_fixtures(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    fixtures_dir = root / "evaluation" / "fixtures"
    if not fixtures_dir.is_dir():
        return ["evaluation/fixtures: directory missing"]
    skills = existing_skill_names()
    seen_ids: dict[str, str] = {}
    files = sorted(fixtures_dir.glob("*.yaml"))
    if not files:
        return ["evaluation/fixtures: no fixtures found"]

    for path in files:
        where = rel(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            errors.append(f"{where}: not a YAML mapping")
            continue
        for field in REQUIRED_FIELDS:
            if field not in data:
                errors.append(f"{where}: missing '{field}'")
        fid = data.get("fixture_id", "")
        if not str(fid).startswith("fix-"):
            errors.append(f"{where}: fixture_id must start with 'fix-'")
        if fid in seen_ids:
            errors.append(f"{where}: duplicate fixture_id (also {seen_ids[fid]})")
        else:
            seen_ids[fid] = where
        video = data.get("video") or {}
        for field in REQUIRED_VIDEO_FIELDS:
            if field not in video:
                errors.append(f"{where}: video missing '{field}'")
        if not data.get("known_problems") and not data.get("known_strengths"):
            errors.append(f"{where}: needs known_problems or known_strengths")
        for diag in data.get("expected_diagnoses") or []:
            skill = (diag or {}).get("skill")
            if not skill:
                errors.append(f"{where}: expected_diagnoses entry missing 'skill'")
            elif skill not in skills:
                errors.append(f"{where}: expected_diagnoses references unknown skill '{skill}'")
            if not (diag or {}).get("expectation"):
                errors.append(f"{where}: expected_diagnoses entry missing 'expectation'")

    print(f"run_fixtures: {len(files)} fixtures checked")
    return errors


def main() -> int:
    errors = check_fixtures()
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print(f"run_fixtures: FAILED ({len(errors)} errors)", file=sys.stderr)
        return 1
    print("run_fixtures: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
