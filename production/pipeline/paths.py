"""Repository paths and configuration loading."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

PRODUCTION_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = PRODUCTION_DIR.parent

CONFIG_DIR = PRODUCTION_DIR / "config"
TEMPLATES_DIR = PRODUCTION_DIR / "templates"

JOBS_DIR = REPO_ROOT / "jobs"
JOBS_INCOMING = JOBS_DIR / "incoming"
JOBS_PROCESSING = JOBS_DIR / "processing"
JOBS_REVIEW = JOBS_DIR / "review"
JOBS_APPROVED = JOBS_DIR / "approved"
JOBS_FAILED = JOBS_DIR / "failed"

OUTPUTS_DIR = REPO_ROOT / "outputs"
OUTPUTS_PREVIEWS = OUTPUTS_DIR / "previews"
OUTPUTS_FINAL = OUTPUTS_DIR / "final"
OUTPUTS_PACKAGES = OUTPUTS_DIR / "posting-packages"
OUTPUTS_QUALITY = OUTPUTS_DIR / "quality-reports"
OUTPUTS_PLANS = OUTPUTS_DIR / "edit-plans"

FEEDBACK_RAW = REPO_ROOT / "feedback" / "raw"
FEEDBACK_STRUCTURED = REPO_ROOT / "feedback" / "structured"

PREFERENCES_APPROVED = REPO_ROOT / "preferences" / "approved"
PREFERENCES_PROPOSED = REPO_ROOT / "preferences" / "proposed"

EXPERIMENTS_DIR = REPO_ROOT / "experiments"
ANALYTICS_DIR = REPO_ROOT / "analytics" / "posts"
RESEARCH_DIR = REPO_ROOT / "research" / "tracks"

OPENMONTAGE_DIR = REPO_ROOT / "integrations" / "openmontage"


def openmontage_clone() -> Path:
    """Path to the pinned OpenMontage clone (env override supported)."""
    override = os.environ.get("OPENMONTAGE_CLONE_PATH")
    return Path(override) if override else OPENMONTAGE_DIR / "clone"


ALL_WRITABLE_DIRS = [
    JOBS_INCOMING, JOBS_PROCESSING, JOBS_REVIEW, JOBS_APPROVED, JOBS_FAILED,
    OUTPUTS_PREVIEWS, OUTPUTS_FINAL, OUTPUTS_PACKAGES, OUTPUTS_QUALITY, OUTPUTS_PLANS,
    FEEDBACK_RAW, FEEDBACK_STRUCTURED,
    PREFERENCES_APPROVED, PREFERENCES_PROPOSED,
    EXPERIMENTS_DIR, ANALYTICS_DIR, RESEARCH_DIR,
]


def ensure_dirs() -> None:
    for directory in ALL_WRITABLE_DIRS:
        directory.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=None)
def load_config(name: str) -> dict[str, Any]:
    """Load a YAML file from production/config/ by stem name."""
    path = CONFIG_DIR / f"{name}.yaml"
    if not path.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache(maxsize=None)
def load_templates() -> dict[str, dict[str, Any]]:
    """Load every format-family template keyed by its ``name``."""
    templates: dict[str, dict[str, Any]] = {}
    for path in sorted(TEMPLATES_DIR.glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        name = data.get("name") or path.stem
        data["_source"] = str(path.relative_to(REPO_ROOT))
        templates[name] = data
    return templates


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``override`` into a copy of ``base``."""
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def rel(path: Path | str) -> str:
    """Repository-relative string for reporting, falling back to absolute."""
    try:
        return str(Path(path).resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)
