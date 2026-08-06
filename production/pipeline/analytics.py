"""Performance learning from manually entered TikTok results.

The creator posts by hand and types the numbers back in. This module stores those
records and generates *hypotheses* — never conclusions. Every generated statement
carries the sample size, a confidence label, the confounders that could explain it
and a suggested next experiment.

The guard that matters: no recommendation is emitted from a single video, and
nothing here edits a skill or a preference.
"""

from __future__ import annotations

import statistics
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from .paths import ANALYTICS_DIR, rel

# Below this many posts in a group, no comparison is offered at all.
MINIMUM_GROUP_SIZE = 3
# Below this many posts per side, a comparison is labelled low confidence.
CONFIDENT_GROUP_SIZE = 6

NUMERIC_FIELDS = (
    "views", "likes", "comments", "shares", "saves", "followers_gained",
    "average_watch_time_seconds", "completion_rate", "rewatch_rate",
)


@dataclass
class PostRecord:
    """One posted video and its measured outcome."""

    video_id: str
    posted_date: str
    job_id: str = ""
    revision: int = 1
    format_family: str = ""
    duration_seconds: float = 0.0
    hook: str = ""
    caption: str = ""
    hashtags: list[str] = field(default_factory=list)
    hashtag_strategy: list[str] = field(default_factory=list)
    first_artist: str = ""
    second_artist: str = ""
    first_track: str = ""
    second_track: str = ""
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    saves: int | None = None
    followers_gained: int | None = None
    average_watch_time_seconds: float | None = None
    completion_rate: float | None = None
    rewatch_rate: float | None = None
    experiment_id: str | None = None
    notes: str = ""
    recorded_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def engagement_rate(self) -> float | None:
        if not self.views:
            return None
        interactions = sum(
            value or 0 for value in (self.likes, self.comments, self.shares, self.saves)
        )
        return interactions / self.views


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _path(video_id: str) -> Path:
    return ANALYTICS_DIR / f"post-{video_id}.yaml"


def record_post(**fields: Any) -> PostRecord:
    """Store one post's results."""
    if not fields.get("video_id"):
        raise ValueError("video_id is required")
    if not fields.get("posted_date"):
        fields["posted_date"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    known = {key: value for key, value in fields.items() if key in PostRecord.__annotations__}
    record = PostRecord(**known)
    record.recorded_at = _now()

    ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
    payload = record.as_dict()
    payload["artifact_kind"] = "tiktok_post_result"
    _path(record.video_id).write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return record


def load_all() -> list[PostRecord]:
    if not ANALYTICS_DIR.is_dir():
        return []
    records: list[PostRecord] = []
    for path in sorted(ANALYTICS_DIR.glob("post-*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        data.pop("artifact_kind", None)
        for key, value in list(data.items()):
            if hasattr(value, "isoformat"):
                data[key] = value.isoformat()
        known = {k: v for k, v in data.items() if k in PostRecord.__annotations__}
        try:
            records.append(PostRecord(**known))
        except TypeError:
            continue
    return records


@dataclass
class Hypothesis:
    """A pattern worth testing — explicitly not a finding."""

    statement: str
    metric: str
    evidence: str
    sample_size: int
    confidence: str
    confounders: list[str]
    suggested_experiment: str
    should_affect_future_edits: bool

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _values(records: Iterable[PostRecord], metric: str) -> list[float]:
    values: list[float] = []
    for record in records:
        value = getattr(record, metric, None)
        if isinstance(value, (int, float)):
            values.append(float(value))
    return values


def _confidence(group_a: int, group_b: int) -> str:
    smaller = min(group_a, group_b)
    if smaller >= CONFIDENT_GROUP_SIZE:
        return "medium"
    return "low"


def _standard_confounders() -> list[str]:
    return [
        "posting time and day differ between groups",
        "track popularity differs between videos and is not controlled",
        "the account's follower base changed over the period",
        "TikTok distribution varies between posts for reasons not visible here",
    ]


def _compare_groups(
    records: list[PostRecord],
    key: str,
    metric: str,
    metric_label: str,
) -> list[Hypothesis]:
    """Compare a metric across the values of one grouping field."""
    groups: dict[str, list[PostRecord]] = {}
    for record in records:
        value = getattr(record, key, "") or ""
        if not value:
            continue
        groups.setdefault(str(value), []).append(record)

    usable = {
        name: items for name, items in groups.items()
        if len(_values(items, metric)) >= MINIMUM_GROUP_SIZE
    }
    if len(usable) < 2:
        return []

    medians = {
        name: statistics.median(_values(items, metric))
        for name, items in usable.items()
    }
    ordered = sorted(medians.items(), key=lambda entry: entry[1], reverse=True)
    best_name, best_value = ordered[0]
    worst_name, worst_value = ordered[-1]
    if worst_value <= 0:
        return []

    ratio = best_value / worst_value
    if ratio < 1.25:
        return []

    best_count = len(usable[best_name])
    worst_count = len(usable[worst_name])
    return [Hypothesis(
        statement=(
            f"{key.replace('_', ' ')} {best_name!r} may reach a higher {metric_label} "
            f"than {worst_name!r} (median {best_value:,.0f} vs {worst_value:,.0f})."
        ),
        metric=metric,
        evidence=(
            f"{best_count} post(s) as {best_name!r}, {worst_count} as {worst_name!r}; "
            f"medians {best_value:,.1f} and {worst_value:,.1f}"
        ),
        sample_size=best_count + worst_count,
        confidence=_confidence(best_count, worst_count),
        confounders=_standard_confounders(),
        suggested_experiment=(
            f"Post alternating videos in {best_name!r} and {worst_name!r} with comparable "
            "track pairings until each side has at least "
            f"{CONFIDENT_GROUP_SIZE} posts, then compare {metric_label} again."
        ),
        should_affect_future_edits=False,
    )]


def _duration_bands(records: list[PostRecord]) -> list[Hypothesis]:
    bands: dict[str, list[PostRecord]] = {"15-22s": [], "22-30s": [], "30-45s": []}
    for record in records:
        duration = record.duration_seconds or 0
        if 15 <= duration < 22:
            bands["15-22s"].append(record)
        elif 22 <= duration < 30:
            bands["22-30s"].append(record)
        elif 30 <= duration <= 45:
            bands["30-45s"].append(record)

    usable = {
        name: items for name, items in bands.items()
        if len(_values(items, "completion_rate")) >= MINIMUM_GROUP_SIZE
    }
    if len(usable) < 2:
        return []

    medians = {
        name: statistics.median(_values(items, "completion_rate"))
        for name, items in usable.items()
    }
    best_name, best_value = max(medians.items(), key=lambda entry: entry[1])
    worst_name, worst_value = min(medians.items(), key=lambda entry: entry[1])
    if worst_value <= 0 or best_value / worst_value < 1.15:
        return []

    return [Hypothesis(
        statement=(
            f"Videos of {best_name} may hold viewers to the end more often than "
            f"{worst_name} ones (median completion {best_value:.1%} vs {worst_value:.1%})."
        ),
        metric="completion_rate",
        evidence=f"{len(usable[best_name])} vs {len(usable[worst_name])} posts",
        sample_size=len(usable[best_name]) + len(usable[worst_name]),
        confidence=_confidence(len(usable[best_name]), len(usable[worst_name])),
        confounders=[
            *_standard_confounders(),
            "shorter videos mechanically reach higher completion rates, so this may "
            "measure duration rather than editing quality",
        ],
        suggested_experiment=(
            f"Cut the same transition to both {best_name} and {worst_name} and compare "
            "average watch time in seconds, which is not mechanically tied to length."
        ),
        should_affect_future_edits=False,
    )]


def _hook_patterns(records: list[PostRecord]) -> list[Hypothesis]:
    groups: dict[str, list[PostRecord]] = {}
    for record in records:
        hook = (record.hook or "").strip().lower()
        if hook:
            groups.setdefault(hook, []).append(record)
    usable = {
        name: items for name, items in groups.items()
        if len(_values(items, "comments")) >= MINIMUM_GROUP_SIZE
    }
    if len(usable) < 2:
        return []
    medians = {
        name: statistics.median(_values(items, "comments")) for name, items in usable.items()
    }
    best_name, best_value = max(medians.items(), key=lambda entry: entry[1])
    worst_name, worst_value = min(medians.items(), key=lambda entry: entry[1])
    if worst_value <= 0 or best_value / worst_value < 1.3:
        return []
    return [Hypothesis(
        statement=(
            f"The hook {best_name!r} may draw more comments than {worst_name!r} "
            f"(median {best_value:,.0f} vs {worst_value:,.0f})."
        ),
        metric="comments",
        evidence=f"{len(usable[best_name])} vs {len(usable[worst_name])} posts",
        sample_size=len(usable[best_name]) + len(usable[worst_name]),
        confidence=_confidence(len(usable[best_name]), len(usable[worst_name])),
        confounders=[
            *_standard_confounders(),
            "hook wording travels with format and track choice, so the effect may "
            "belong to either",
        ],
        suggested_experiment=(
            f"Use {best_name!r} and {worst_name!r} on the same format family with "
            "similar tracks, alternating between posts."
        ),
        should_affect_future_edits=False,
    )]


def generate_hypotheses(records: list[PostRecord] | None = None) -> list[Hypothesis]:
    """Derive testable hypotheses from the recorded post results."""
    records = records if records is not None else load_all()
    if len(records) < MINIMUM_GROUP_SIZE * 2:
        return []

    hypotheses: list[Hypothesis] = []
    hypotheses += _compare_groups(records, "format_family", "views", "view count")
    hypotheses += _compare_groups(records, "format_family", "comments", "comment count")
    hypotheses += _duration_bands(records)
    hypotheses += _hook_patterns(records)
    return hypotheses


def report() -> dict[str, Any]:
    """Summary of recorded performance plus any hypotheses it supports."""
    records = load_all()
    hypotheses = generate_hypotheses(records)

    totals: dict[str, Any] = {"posts": len(records)}
    for metric in NUMERIC_FIELDS:
        values = _values(records, metric)
        if values:
            totals[metric] = {
                "count": len(values),
                "median": round(statistics.median(values), 3),
                "mean": round(statistics.fmean(values), 3),
            }

    blocked_reason = ""
    if not hypotheses:
        blocked_reason = (
            f"{len(records)} post(s) recorded. At least {MINIMUM_GROUP_SIZE} posts per "
            "compared group are needed before any pattern is offered, and a pattern "
            "remains a hypothesis until an experiment tests it."
        )

    return {
        "generated_at": _now(),
        "totals": totals,
        "hypotheses": [hypothesis.as_dict() for hypothesis in hypotheses],
        "note": blocked_reason or (
            "These are hypotheses derived from small samples. None of them is a "
            "measured effect, and none has changed any skill or preference."
        ),
        "records": [rel(_path(record.video_id)) for record in records],
    }
