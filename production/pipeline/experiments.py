"""Experiment records: what changed, why, and what happened.

An experiment links one render's deliberate variation to the metrics it was meant
to move. Results are entered after posting; nothing is concluded automatically.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import artifacts
from .paths import EXPERIMENTS_DIR, rel

STATUS_VALUES = {"awaiting_results", "results_recorded", "inconclusive", "abandoned"}

METRIC_TARGETS = {
    "views", "average_watch_time", "completion_rate", "three_second_retention",
    "early_skip_rate", "likes", "comments", "shares", "saves", "followers",
}


@dataclass
class Experiment:
    id: str
    job_id: str
    revision: int
    created_at: str
    hypothesis: str
    variable: str
    control_reference: str
    expected_effect: str
    status: str
    what_changed: str = ""
    why: str = ""
    format_family: str = ""
    video_id: str | None = None
    results: dict[str, Any] = field(default_factory=dict)
    interpretation: str = ""
    repeat_recommended: str = "unknown"
    more_evidence_required: bool = True
    confounders: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _path(experiment_id: str) -> Path:
    return EXPERIMENTS_DIR / f"{experiment_id}.yaml"


def create(
    *,
    job_id: str,
    revision: int,
    hypothesis: str,
    variable: str,
    control_reference: str,
    expected_effect: str,
    what_changed: str = "",
    why: str = "",
    format_family: str = "",
) -> Experiment:
    experiment = Experiment(
        id=artifacts.artifact_id(
            "exp", artifacts.today(), artifacts.stamp(job_id, revision)
        ),
        job_id=job_id,
        revision=revision,
        created_at=_now(),
        hypothesis=hypothesis,
        variable=variable,
        control_reference=control_reference,
        expected_effect=expected_effect,
        status="awaiting_results",
        what_changed=what_changed,
        why=why,
        format_family=format_family,
    )
    save(experiment)
    return experiment


def save(experiment: Experiment) -> Path:
    return artifacts.write(
        _path(experiment.id),
        "production_experiment", experiment.id, experiment.as_dict(),
        created_at=experiment.created_at,
    )


def load(experiment_id: str) -> Experiment | None:
    path = _path(experiment_id)
    if not path.is_file():
        return None
    data = artifacts.strip_envelope(yaml.safe_load(path.read_text(encoding="utf-8")) or {})
    try:
        return Experiment(**data)
    except TypeError:
        return None


def load_all() -> list[Experiment]:
    if not EXPERIMENTS_DIR.is_dir():
        return []
    experiments: list[Experiment] = []
    for path in sorted(EXPERIMENTS_DIR.glob("*.yaml")):
        data = artifacts.strip_envelope(
            yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        )
        try:
            experiments.append(Experiment(**data))
        except TypeError:
            continue
    return experiments


def record_results(
    experiment_id: str,
    results: dict[str, Any],
    *,
    interpretation: str = "",
    confounders: list[str] | None = None,
) -> Experiment:
    experiment = load(experiment_id)
    if experiment is None:
        raise FileNotFoundError(f"No experiment {experiment_id!r}")
    experiment.results = dict(results)
    experiment.status = "results_recorded"
    experiment.interpretation = interpretation
    experiment.confounders = list(confounders or experiment.confounders)
    # A single posted video cannot establish an effect; that stays true regardless
    # of how large the numbers look.
    experiment.more_evidence_required = True
    experiment.repeat_recommended = "repeat_to_gather_evidence"
    save(experiment)
    return experiment


def summary() -> dict[str, Any]:
    experiments = load_all()
    by_status: dict[str, int] = {}
    for experiment in experiments:
        by_status[experiment.status] = by_status.get(experiment.status, 0) + 1
    return {
        "total": len(experiments),
        "by_status": by_status,
        "awaiting_results": [
            {"id": e.id, "hypothesis": e.hypothesis, "path": rel(_path(e.id))}
            for e in experiments if e.status == "awaiting_results"
        ],
    }
