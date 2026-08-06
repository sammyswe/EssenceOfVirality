"""Shared helpers for the deterministic validators.

These tools are the CI integrity layer (ADR 0006): schema validation, skill lint,
ID/reference integrity and fixture structure. They must stay deterministic — no
network, no model calls.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"
SKILLS_DIR = REPO_ROOT / ".cursor" / "skills"

# Directories scanned for YAML artifacts (files bearing an `artifact_type` key).
# The production directories hold the pipeline's durable memory — feedback,
# preferences, experiments, post results — and the committed worked examples.
# Live run output under outputs/ is regenerated per run and is not in git.
ARTIFACT_DIRS = [
    "research",
    "evidence",
    "evaluation/reports",
    "evaluation/regression",
    "analytics",
    "tests/fixtures/artifacts",
    "feedback/structured",
    "preferences",
    "experiments",
    "examples/approved-outputs",
]

# artifact_type -> schema file (mirrors schemas/README.md).
SCHEMA_REGISTRY = {
    "source_manifest": "source-manifest.schema.json",
    "extraction_report": "extraction-report.schema.json",
    "claim_record": "claim-record.schema.json",
    "evidence_assessment": "evidence-assessment.schema.json",
    "technique_record": "technique-record.schema.json",
    "contradiction_record": "contradiction-record.schema.json",
    "knowledge_change_proposal": "knowledge-change-proposal.schema.json",
    "skill_change_proposal": "skill-change-proposal.schema.json",
    "evaluation_report": "evaluation-report.schema.json",
    "experiment_proposal": "experiment-proposal.schema.json",
    "pull_request_summary": "pull-request-summary.schema.json",
    "analytics_observation": "analytics-observation.schema.json",
    "video_production_manifest": "video-production-manifest.schema.json",
    # Production pipeline artifacts.
    "edit_plan": "edit-plan.schema.json",
    "quality_report": "quality-report.schema.json",
    "posting_package": "posting-package.schema.json",
    "creator_feedback": "creator-feedback.schema.json",
    "creator_preference": "creator-preference.schema.json",
    "production_experiment": "production-experiment.schema.json",
    "tiktok_post_result": "tiktok-post-result.schema.json",
    "track_research_note": "track-research-note.schema.json",
}

ARTIFACT_ID_RE = re.compile(
    r"^(src|ext|claim|assess|tech|contra|kcp|scp|eval|obs|exp|prs|vpm|fix"
    r"|plan|qr|pkg|fb|pref|post|res)-[a-z0-9][a-z0-9-]*$"
)

SKILL_BANKS = [
    "general-virality",
    "spotify-mix-content",
    "research-workflows",
    "meta",
    "experimental",
    # Operating instructions for the production pipeline's stages. These skills
    # describe how to run and reason about `production/`; the creative claims
    # they act on belong to the domain banks, so they carry no evidence refs.
    "production",
]

# Banks whose skills encode domain knowledge and therefore need evidence references.
EVIDENCE_REQUIRED_BANKS = {"general-virality", "spotify-mix-content"}

MATURITY_VALUES = {"experimental", "provisional", "validated", "stable", "deprecated"}
CONFIDENCE_VALUES = {"low", "medium", "high"}
EVIDENCE_BASIS_VALUES = {
    "official",
    "academic",
    "observational",
    "creator_experiment",
    "first_party_analytics",
    "expert_opinion",
    "creator_statement",
}
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

# Overclaiming language that must never appear in an operational skill.
BANNED_SKILL_PATTERNS = [
    re.compile(r"guaranteed?\s+(to\s+go\s+)?viral", re.IGNORECASE),
    re.compile(r"guarantees?\s+virality", re.IGNORECASE),
    re.compile(r"will\s+go\s+viral", re.IGNORECASE),
    re.compile(r"make\s+it\s+engaging(?![a-z])", re.IGNORECASE),
]


def _normalise_dates(value):
    """PyYAML parses unquoted ISO dates into date objects; schemas expect strings."""
    import datetime

    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {k: _normalise_dates(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise_dates(v) for v in value]
    return value


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        return _normalise_dates(yaml.safe_load(fh))


def iter_artifact_files(root: Path = REPO_ROOT):
    """Yield (path, data) for every YAML artifact in the scanned directories."""
    for rel in ARTIFACT_DIRS:
        base = root / rel
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*.yaml")) + sorted(base.rglob("*.yml")):
            data = load_yaml(path)
            if isinstance(data, dict) and "artifact_type" in data:
                yield path, data


def load_schemas():
    """Load all schemas keyed by their $id for $ref resolution."""
    schemas = {}
    for path in SCHEMAS_DIR.glob("*.schema.json"):
        with path.open("r", encoding="utf-8") as fh:
            schema = json.load(fh)
        schemas[schema["$id"]] = schema
    return schemas


def parse_frontmatter(path: Path):
    """Return (frontmatter_dict, body) for a markdown file, or (None, text)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    try:
        fm = yaml.safe_load(parts[1])
    except yaml.YAMLError:
        return None, text
    return (fm if isinstance(fm, dict) else None), parts[2]


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
