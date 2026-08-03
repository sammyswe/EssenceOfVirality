#!/usr/bin/env python3
"""Check artifact ID uniqueness and reference integrity across the repository.

JSON Schema cannot express cross-record referential integrity; this tool does
(ADR 0004). Any full-string value matching the artifact ID pattern must refer to
an artifact that exists.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import ARTIFACT_ID_RE, REPO_ROOT, iter_artifact_files, rel


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _walk_strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _walk_strings(v)


def check_repo(root: Path = REPO_ROOT) -> list[str]:
    errors: list[str] = []
    ids: dict[str, str] = {}
    artifacts = list(iter_artifact_files(root))

    for path, data in artifacts:
        aid = data.get("id")
        if not isinstance(aid, str) or not ARTIFACT_ID_RE.match(aid):
            errors.append(f"{rel(path)}: missing or malformed id '{aid}'")
            continue
        if aid in ids:
            errors.append(f"{rel(path)}: duplicate id '{aid}' (also {ids[aid]})")
        else:
            ids[aid] = rel(path)

    # Fixture IDs (fix-...) live in evaluation/fixtures, outside artifact dirs.
    fixtures_dir = root / "evaluation" / "fixtures"
    known_fixture_ids = set()
    if fixtures_dir.is_dir():
        import yaml

        for fpath in fixtures_dir.glob("*.yaml"):
            data = yaml.safe_load(fpath.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("fixture_id"), str):
                known_fixture_ids.add(data["fixture_id"])

    known = set(ids) | known_fixture_ids
    for path, data in artifacts:
        for value in _walk_strings(data):
            if ARTIFACT_ID_RE.match(value) and value not in known:
                errors.append(f"{rel(path)}: dangling reference '{value}'")

    print(f"check_ids: {len(ids)} ids, {len(artifacts)} artifacts checked")
    return errors


def main() -> int:
    errors = check_repo()
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print(f"check_ids: FAILED ({len(errors)} errors)", file=sys.stderr)
        return 1
    print("check_ids: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
