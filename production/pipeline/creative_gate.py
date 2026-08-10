"""Creative-minimum gate — separate from technical quality.

Technical checks ask whether the file is uploadable. This gate asks whether the
job has the minimum creative inputs to be treated as a review candidate for a
house / Spotify-mix feed. It does not predict views, ranking, or virality.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

from .editplan import EditPlan
from .jobspec import JobSpec

PASS = "pass"
FAIL = "fail"

GENERIC_HOOKS = {
    "wait for the switch",
    "spotify did this on its own",
}


@dataclass
class CreativeCheck:
    id: str
    description: str
    status: str
    detail: str
    creator_action: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CreativeMinimumReport:
    """Outcome of the creative-minimum gate for one plan."""

    job_id: str
    revision: int
    created_at: str
    checks: list[CreativeCheck] = field(default_factory=list)

    @property
    def failures(self) -> list[CreativeCheck]:
        return [check for check in self.checks if check.status == FAIL]

    @property
    def passed(self) -> bool:
        return not self.failures

    @property
    def status(self) -> str:
        return PASS if self.passed else FAIL

    @property
    def creator_actions(self) -> list[str]:
        actions: list[str] = []
        for check in self.failures:
            if check.creator_action and check.creator_action not in actions:
                actions.append(check.creator_action)
        return actions

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "revision": self.revision,
            "created_at": self.created_at,
            "status": self.status,
            "passed": self.passed,
            "summary": {
                "passed": len([c for c in self.checks if c.status == PASS]),
                "failures": len(self.failures),
            },
            "checks": [check.as_dict() for check in self.checks],
            "creator_actions": self.creator_actions,
            "language_note": (
                "Creative minimum is a product gate on inputs and plan honesty, "
                "not a prediction of For You distribution or engagement."
            ),
        }


def tracks_complete(tracks: dict[str, Any]) -> bool:
    """True when both mix slots name a title and artist."""
    for slot in ("first", "second"):
        track = tracks.get(slot) or {}
        title = str(track.get("title", "") or "").strip()
        artist = str(track.get("artist", "") or "").strip()
        if not title or not artist:
            return False
    return True


def waive_track_metadata(job: JobSpec) -> bool:
    direction = job.creative_direction or {}
    return bool(direction.get("waive_track_metadata"))


def waive_empty_asset_fallback(job: JobSpec) -> bool:
    direction = job.creative_direction or {}
    return bool(direction.get("waive_empty_asset_fallback"))


def waive_generic_hook(job: JobSpec) -> bool:
    direction = job.creative_direction or {}
    return bool(direction.get("waive_generic_hook"))


def format_was_forced(job: JobSpec, plan: EditPlan) -> bool:
    """True when the job explicitly requested the format that shipped."""
    requested = str(job.preferred_format or "auto").strip()
    if not requested or requested == "auto":
        return False
    return requested == plan.template_name


def hook_references_tracks(hook: str, tracks: dict[str, Any]) -> bool:
    text = (hook or "").strip().lower()
    if not text:
        return False
    for slot in ("first", "second"):
        track = tracks.get(slot) or {}
        for field_name in ("title", "artist"):
            value = str(track.get(field_name, "") or "").strip().lower()
            if value and value in text:
                return True
    return False


def evaluate(
    job: JobSpec,
    plan: EditPlan,
) -> CreativeMinimumReport:
    """Run the creative-minimum checks against a finished plan."""
    report = CreativeMinimumReport(
        job_id=plan.job_id,
        revision=plan.revision,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    # 1. Track metadata (or explicit waiver).
    if waive_track_metadata(job):
        report.checks.append(CreativeCheck(
            id="track_metadata",
            description="Both tracks name title and artist, or the job waives that requirement",
            status=PASS,
            detail="creative_direction.waive_track_metadata is set; blank tracks are intentional",
        ))
    elif tracks_complete(job.tracks):
        report.checks.append(CreativeCheck(
            id="track_metadata",
            description="Both tracks name title and artist, or the job waives that requirement",
            status=PASS,
            detail="tracks.first and tracks.second each have title and artist",
        ))
    else:
        report.checks.append(CreativeCheck(
            id="track_metadata",
            description="Both tracks name title and artist, or the job waives that requirement",
            status=FAIL,
            detail=(
                "tracks.first/second are missing title or artist; hooks, CTAs and "
                "captions cannot name the pairing"
            ),
            creator_action=(
                "Fill tracks.first and tracks.second (title + artist) in job.yaml, "
                "or set creative_direction.waive_track_metadata: true if blank "
                "metadata is intentional"
            ),
        ))

    # 2. Empty-asset fallback (recording-only collapse into a weak default).
    empty_fallback = bool(getattr(plan, "empty_asset_fallback", False))
    if not empty_fallback:
        report.checks.append(CreativeCheck(
            id="format_not_empty_default",
            description="Format is not the recording-only empty-asset fallback unless forced or waived",
            status=PASS,
            detail=(
                f"format {plan.template_name!r} was not selected solely because "
                "supporting clips / metadata were missing"
            ),
        ))
    elif format_was_forced(job, plan) or waive_empty_asset_fallback(job):
        reason = (
            f"job.yaml forces preferred_format: {plan.template_name}"
            if format_was_forced(job, plan)
            else "creative_direction.waive_empty_asset_fallback is set"
        )
        report.checks.append(CreativeCheck(
            id="format_not_empty_default",
            description="Format is not the recording-only empty-asset fallback unless forced or waived",
            status=PASS,
            detail=f"empty-asset fallback accepted because {reason}",
        ))
    else:
        report.checks.append(CreativeCheck(
            id="format_not_empty_default",
            description="Format is not the recording-only empty-asset fallback unless forced or waived",
            status=FAIL,
            detail=(
                f"format {plan.template_name!r} was chosen only because higher-value "
                "families needed supporting clips or track metadata that this job "
                "does not have"
            ),
            creator_action=(
                "Add a supporting hook/overlay clip, fill track metadata for "
                "unexpected-combination, set creative_direction.preferred_format "
                f"to {plan.template_name!r} to force it, or set "
                "creative_direction.waive_empty_asset_fallback: true"
            ),
        ))

    # 3. Hook specificity.
    explicit_hook = bool((job.creative_direction.get("hook") or "").strip())
    hook = (plan.hook_text or "").strip()
    hook_lower = hook.lower()
    if explicit_hook:
        report.checks.append(CreativeCheck(
            id="hook_specificity",
            description="Hook makes a specific promise (not a blank-input generic)",
            status=PASS,
            detail="hook supplied explicitly in job.yaml",
        ))
    elif waive_generic_hook(job):
        report.checks.append(CreativeCheck(
            id="hook_specificity",
            description="Hook makes a specific promise (not a blank-input generic)",
            status=PASS,
            detail="creative_direction.waive_generic_hook is set",
        ))
    elif hook_references_tracks(hook, job.tracks):
        report.checks.append(CreativeCheck(
            id="hook_specificity",
            description="Hook makes a specific promise (not a blank-input generic)",
            status=PASS,
            detail=f"hook names a track or artist from job metadata: {hook!r}",
        ))
    elif hook_lower in GENERIC_HOOKS or not hook:
        report.checks.append(CreativeCheck(
            id="hook_specificity",
            description="Hook makes a specific promise (not a blank-input generic)",
            status=FAIL,
            detail=(
                f"hook {hook!r} is a generic anticipation line with no track/artist "
                "promise — weak scroll-stop for house / Spotify-mix content"
            ),
            creator_action=(
                "Set creative_direction.hook to a specific line, fill track "
                "metadata so artist/track hooks can be selected, or set "
                "creative_direction.waive_generic_hook: true"
            ),
        ))
    else:
        report.checks.append(CreativeCheck(
            id="hook_specificity",
            description="Hook makes a specific promise (not a blank-input generic)",
            status=PASS,
            detail=f"hook is non-generic: {hook!r}",
        ))

    return report


def compose_retention_hypothesis(
    template_hypothesis: str,
    *,
    emphasis_enabled: bool,
) -> str:
    """Retention hypothesis must describe the plan that will actually render.

    Template copy often assumes zoom emphasis. When emphasis is disabled by
    preference or config, citing a zoom-marked payoff is plan/hypothesis drift.
    """
    base = (template_hypothesis or "").strip()
    if emphasis_enabled:
        return base
    return (
        "Keeping the Spotify surface unobstructed is expected to protect "
        "completion_rate by making the payoff legible, with no competing visual "
        "to explain. Zoom emphasis is disabled on this render, so the hypothesis "
        "does not rely on a zoom-marked payoff."
    )
