#!/usr/bin/env python3
"""Validate every YAML artifact against its canonical JSON Schema (ADR 0004)."""

from __future__ import annotations

import sys
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, SCHEMA_REGISTRY, iter_artifact_files, load_schemas, rel

SCHEMA_BASE = "https://essenceofvirality.local/schemas/"


def build_validators():
    schemas = load_schemas()
    registry = Registry().with_resources(
        (uri, Resource.from_contents(schema)) for uri, schema in schemas.items()
    )
    validators = {}
    for artifact_type, filename in SCHEMA_REGISTRY.items():
        uri = SCHEMA_BASE + filename
        if uri not in schemas:
            raise SystemExit(f"schema registry points at missing schema: {filename}")
        validators[artifact_type] = Draft202012Validator(schemas[uri], registry=registry)
    return validators


def validate_repo(root: Path = REPO_ROOT) -> list[str]:
    validators = build_validators()
    errors: list[str] = []
    count = 0
    for path, data in iter_artifact_files(root):
        count += 1
        artifact_type = data.get("artifact_type")
        validator = validators.get(artifact_type)
        if validator is None:
            errors.append(f"{rel(path)}: unknown artifact_type '{artifact_type}'")
            continue
        for err in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path)):
            where = "/".join(str(p) for p in err.absolute_path) or "<root>"
            errors.append(f"{rel(path)}: {where}: {err.message}")
    print(f"validate_artifacts: {count} artifacts checked")
    return errors


def main() -> int:
    errors = validate_repo()
    for e in errors:
        print(f"ERROR {e}", file=sys.stderr)
    if errors:
        print(f"validate_artifacts: FAILED ({len(errors)} errors)", file=sys.stderr)
        return 1
    print("validate_artifacts: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
