"""Skill 10 — job orchestration.

Runs a job folder end to end and leaves behind everything needed to post, review or
revise: the render, a preview, the edit plan, the posting package, the quality
report and a production manifest linking them.

Job folders move between ``jobs/`` states; original media is never modified and
never moved out from under the creator.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .. import __version__
from . import (
    artifacts,
    creative,
    creative_gate,
    experiments,
    feedback as feedback_module,
    inspector,
    posting,
    quality,
    render as render_module,
    research as research_module,
    revision as revision_module,
)
from .editplan import EditPlan
from .jobspec import JobError, JobSpec, load_job
from .om import capability_report
from .paths import (
    JOBS_APPROVED,
    JOBS_FAILED,
    JOBS_INCOMING,
    JOBS_REVIEW,
    OUTPUTS_FINAL,
    OUTPUTS_PACKAGES,
    OUTPUTS_PLANS,
    OUTPUTS_PREVIEWS,
    OUTPUTS_QUALITY,
    deep_merge,
    ensure_dirs,
    rel,
)
from .probe import MediaError, require_binaries


PIPELINE_VERSION = __version__


class PipelineError(RuntimeError):
    """Raised when a job cannot be completed."""


@dataclass
class JobResult:
    job_id: str
    revision: int
    status: str
    final_path: Path | None = None
    preview_path: Path | None = None
    plan_path: Path | None = None
    package_path: Path | None = None
    quality_path: Path | None = None
    creative_minimum_path: Path | None = None
    manifest_path: Path | None = None
    plan: EditPlan | None = None
    quality_report: quality.QualityReport | None = None
    creative_minimum: creative_gate.CreativeMinimumReport | None = None
    package: posting.PostingPackage | None = None
    experiment_id: str | None = None
    messages: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "revision": self.revision,
            "status": self.status,
            "final": rel(self.final_path) if self.final_path else None,
            "preview": rel(self.preview_path) if self.preview_path else None,
            "edit_plan": rel(self.plan_path) if self.plan_path else None,
            "posting_package": rel(self.package_path) if self.package_path else None,
            "quality_report": rel(self.quality_path) if self.quality_path else None,
            "creative_minimum_report": (
                rel(self.creative_minimum_path) if self.creative_minimum_path else None
            ),
            "manifest": rel(self.manifest_path) if self.manifest_path else None,
            "experiment": self.experiment_id,
            "messages": self.messages,
            "warnings": self.warnings,
            "post_ready": (
                self.quality_report.post_ready if self.quality_report is not None else False
            ),
        }


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def find_job(reference: str) -> Path:
    """Resolve a job reference: a path, or a job id searched across job states."""
    candidate = Path(reference)
    if candidate.is_dir():
        return candidate.resolve()
    for directory in (JOBS_INCOMING, JOBS_REVIEW, JOBS_APPROVED, JOBS_FAILED):
        guess = directory / reference
        if guess.is_dir():
            return guess.resolve()
    raise JobError(
        f"No job folder for {reference!r}. Looked for a directory at that path and "
        f"under {rel(JOBS_INCOMING)}/, {rel(JOBS_REVIEW)}/, {rel(JOBS_APPROVED)}/."
    )


def newest_job() -> Path:
    """Most recently modified job folder in jobs/incoming."""
    if not JOBS_INCOMING.is_dir():
        raise JobError(f"{rel(JOBS_INCOMING)} does not exist")
    candidates = [path for path in JOBS_INCOMING.iterdir() if path.is_dir()]
    if not candidates:
        raise JobError(
            f"No job folders in {rel(JOBS_INCOMING)}. Create one with "
            "`./process-job new <job-id>`."
        )
    return max(candidates, key=lambda path: path.stat().st_mtime).resolve()


def next_revision(job_id: str) -> int:
    """One past the highest revision already rendered for this job."""
    existing = sorted(OUTPUTS_FINAL.glob(f"{job_id}-r*.mp4")) if OUTPUTS_FINAL.is_dir() else []
    highest = 0
    for path in existing:
        suffix = path.stem.rsplit("-r", 1)[-1]
        if suffix.isdigit():
            highest = max(highest, int(suffix))
    return highest + 1


def _write_plan(plan: EditPlan) -> Path:
    stamp = artifacts.stamp(plan.job_id, plan.revision)
    return artifacts.write(
        OUTPUTS_PLANS / f"{stamp}-edit-plan.yaml",
        "edit_plan", artifacts.artifact_id("plan", stamp), plan.as_dict(),
    )


def _write_quality(report: quality.QualityReport) -> Path:
    stamp = artifacts.stamp(report.job_id, report.revision)
    return artifacts.write(
        OUTPUTS_QUALITY / f"{stamp}-quality-report.yaml",
        "quality_report", artifacts.artifact_id("qr", stamp), report.as_dict(),
        created_at=report.created_at,
    )


def _write_creative_minimum(report: creative_gate.CreativeMinimumReport) -> Path:
    stamp = artifacts.stamp(report.job_id, report.revision)
    return artifacts.write(
        OUTPUTS_QUALITY / f"{stamp}-creative-minimum.yaml",
        "creative_minimum_report",
        artifacts.artifact_id("cm", stamp),
        report.as_dict(),
        created_at=report.created_at,
    )


def _write_manifest(
    job: JobSpec,
    plan: EditPlan,
    input_report: inspector.InputReport,
    render_result: render_module.RenderResult,
    quality_report: quality.QualityReport,
    package_path: Path,
    experiment_id: str | None,
) -> Path:
    """Production manifest: the lineage record linking a render to its decisions.

    Conforms to ``schemas/video-production-manifest.schema.json`` so analytics can
    later trace a post's outcome back to the decisions that produced it.
    """
    stamp = artifacts.stamp(plan.job_id, plan.revision)
    capabilities = capability_report()
    openmontage = capabilities["openmontage"]

    body = {
        "schema_maturity": "scaffold",
        "video_id": stamp,
        "job_id": plan.job_id,
        "revision": plan.revision,
        "source_assets": [
            rel(job.spotify_recording),
            *(rel(asset.path) for asset in job.assets),
        ],
        "pipeline_version": PIPELINE_VERSION,
        "openmontage_version": openmontage.get("actual_ref") or None,
        "openmontage": openmontage,
        "backends": {**input_report.backends, **render_result.backends},
        "format": "9:16",
        "resolution": f"{render_result.width}x{render_result.height}",
        "duration_seconds": round(render_result.duration_seconds, 3),
        "format_family": plan.format_family,
        "template": plan.template_name,
        "transition": input_report.transition,
        "crop_profile": input_report.crop_profile.name,
        "editing_decisions": plan.decisions,
        "hook": {"type": "onscreen_text", "text": plan.hook_text},
        "cta": {"type": "onscreen_text", "text": plan.cta_text},
        "audio": plan.audio.as_dict() if plan.audio else None,
        "quality_status": quality_report.status,
        "technically_valid": quality_report.technically_valid,
        "post_ready": quality_report.post_ready,
        "creative_minimum_status": (
            (quality_report.creative_minimum or {}).get("status")
        ),
        "artifacts": {
            "final": rel(render_result.output_path),
            "preview": rel(render_result.preview_path) if render_result.preview_path else None,
            "posting_package": rel(package_path),
            "quality_report": rel(OUTPUTS_QUALITY / f"{stamp}-quality-report.yaml"),
            "creative_minimum_report": rel(
                OUTPUTS_QUALITY / f"{stamp}-creative-minimum.yaml"
            ),
            "edit_plan": rel(OUTPUTS_PLANS / f"{stamp}-edit-plan.yaml"),
        },
        "experiment": experiment_id,
        "retention_hypothesis": plan.retention_hypothesis,
        "preference_refs": plan.preference_refs,
        "research_refs": plan.research_refs,
    }
    return artifacts.write(
        OUTPUTS_FINAL / f"{stamp}-manifest.yaml",
        "video_production_manifest", artifacts.artifact_id("vpm", stamp), body,
        inputs=[reference for reference in (experiment_id,) if reference],
    )


def move_job(job_dir: Path, destination_root: Path) -> Path:
    """Move a job folder between lifecycle states, preserving its contents."""
    destination_root.mkdir(parents=True, exist_ok=True)
    destination = destination_root / job_dir.name
    if destination.resolve() == job_dir.resolve():
        return job_dir
    if destination.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        destination = destination_root / f"{job_dir.name}-{stamp}"
    shutil.move(str(job_dir), str(destination))
    return destination


def process(
    job_reference: str | Path,
    *,
    revision: int | None = None,
    format_override: str | None = None,
    apply_feedback: bool = True,
    move_on_success: bool = True,
    make_preview: bool = True,
    dry_run: bool = False,
) -> JobResult:
    """Run one job from inputs to post-ready outputs."""
    ensure_dirs()
    require_binaries()

    job_dir = find_job(str(job_reference))
    job = load_job(job_dir)
    revision_number = revision if revision is not None else next_revision(job.job_id)

    result = JobResult(job_id=job.job_id, revision=revision_number, status="running")
    result.warnings.extend(job.warnings)

    # Feedback history reshapes the configuration before anything is planned.
    adjustments: revision_module.RevisionAdjustments | None = None
    if apply_feedback:
        history = feedback_module.load_for_job(job.job_id)
        if history:
            directives = feedback_module.merge_directives(history)
            previous = _previous_plan(job.job_id)
            adjustments = revision_module.build_adjustments(
                directives,
                current_config=job.config,
                previous_hook=previous.get("hook_text", "") if previous else "",
                previous_cta=previous.get("cta_text", "") if previous else "",
            )
            job.config = deep_merge(job.config, adjustments.config_overrides)
            if adjustments.format_override and not format_override:
                format_override = adjustments.format_override
            result.messages.append(
                f"applied {len(adjustments.applied)} directive(s) from "
                f"{len(history)} feedback record(s)"
            )

    input_report = inspector.inspect(job)
    result.warnings.extend(input_report.warnings)
    if not input_report.ok:
        result.status = "failed"
        result.messages.extend(input_report.blocking_problems)
        if move_on_success:
            move_job(job_dir, JOBS_FAILED)
        return result

    subjects = [
        str((job.tracks.get(slot) or {}).get(field_name, ""))
        for slot in ("first", "second")
        for field_name in ("artist", "title")
    ]
    research_notes = research_module.notes_for(subjects) if job.research_enabled else []
    if job.research_enabled and not research_notes:
        result.warnings.append(
            "research is enabled but no sourced notes match these tracks; copy will "
            "avoid any factual claim"
        )

    plan = creative.build_plan(
        job,
        input_report,
        revision=revision_number,
        format_override=format_override,
        research_refs=[note["id"] for note in research_notes],
    )
    if adjustments is not None:
        revision_module.apply_to_plan(plan, adjustments)
    result.plan = plan
    result.warnings.extend(plan.warnings)

    if dry_run:
        result.status = "planned"
        result.plan_path = _write_plan(plan)
        result.messages.append("dry run: plan written, nothing rendered")
        return result

    fingerprints = quality.fingerprint_sources(
        [job.spotify_recording, *(asset.path for asset in job.assets)]
    )

    final_path = OUTPUTS_FINAL / f"{job.job_id}-r{revision_number}.mp4"
    preview_path = (
        OUTPUTS_PREVIEWS / f"{job.job_id}-r{revision_number}-preview.mp4"
        if make_preview and job.outputs.get("preview", True)
        else None
    )

    try:
        render_result = render_module.render(
            plan, input_report, final_path, preview_path=preview_path
        )
    except (render_module.RenderError, MediaError) as exc:
        result.status = "failed"
        result.messages.append(f"render failed: {exc}")
        if move_on_success:
            move_job(job_dir, JOBS_FAILED)
        return result

    result.final_path = render_result.output_path
    result.preview_path = render_result.preview_path
    result.messages.extend(render_result.notes)

    quality_report = quality.run_checks(
        plan, input_report, render_result,
        config=job.config, source_fingerprints=fingerprints,
    )
    creative_report = creative_gate.evaluate(job, plan)
    quality_report.creative_minimum = creative_report.as_dict()
    result.quality_report = quality_report
    result.creative_minimum = creative_report
    result.quality_path = _write_quality(quality_report)
    result.creative_minimum_path = _write_creative_minimum(creative_report)

    experiment_id: str | None = None
    if plan.experiment is not None:
        experiment = experiments.create(
            job_id=job.job_id,
            revision=revision_number,
            hypothesis=plan.experiment.hypothesis,
            variable=plan.experiment.variable,
            control_reference=plan.experiment.control_reference,
            expected_effect=plan.experiment.expected_effect,
            what_changed=f"format {plan.template_name}, hook {plan.hook_text!r}",
            why="; ".join(plan.creative_rationale),
            format_family=plan.format_family,
        )
        experiment_id = experiment.id
        result.experiment_id = experiment_id

    package = posting.build_package(
        plan, input_report, quality_report,
        job_tracks=job.tracks,
        final_path=render_result.output_path,
        preview_path=render_result.preview_path,
        render_metadata=render_result.as_dict(),
        research=research_notes,
        thumbnail_dir=OUTPUTS_PACKAGES,
    )
    result.package = package
    result.package_path = posting.write_package(package, OUTPUTS_PACKAGES)
    result.plan_path = _write_plan(plan)
    result.manifest_path = _write_manifest(
        job, plan, input_report, render_result, quality_report,
        result.package_path, experiment_id,
    )

    if not quality_report.technically_valid:
        result.status = "quality_failed"
        result.messages.append(
            "technical quality checks failed; the render is not uploadable. See "
            f"{rel(result.quality_path)}"
        )
        return result

    if not creative_report.passed:
        result.status = "needs_creative_input"
        result.messages.append(
            "technical checks passed, but creative minimum failed — this is a "
            "valid draft file, not a review-ready / feed candidate. See "
            f"{rel(result.creative_minimum_path)}"
        )
        for action in creative_report.creator_actions:
            result.messages.append(f"add: {action}")
        result.messages.append(
            "job left in place (not moved to jobs/review/). Fill tracks, add a "
            "supporting clip, force preferred_format, or set an explicit waiver "
            "in creative_direction, then re-run."
        )
        return result

    result.status = "review"
    if move_on_success and job_dir.parent.resolve() == JOBS_INCOMING.resolve():
        moved = move_job(job_dir, JOBS_REVIEW)
        result.messages.append(f"job moved to {rel(moved)} for review")
    return result


def _previous_plan(job_id: str) -> dict[str, Any] | None:
    if not OUTPUTS_PLANS.is_dir():
        return None
    plans = sorted(OUTPUTS_PLANS.glob(f"{job_id}-r*-edit-plan.yaml"))
    if not plans:
        return None
    return yaml.safe_load(plans[-1].read_text(encoding="utf-8")) or None


def revise(job_reference: str | Path, feedback_text: str) -> tuple[Any, JobResult]:
    """Record feedback and render the next revision from it."""
    ensure_dirs()
    job_dir = find_job(str(job_reference))
    job = load_job(job_dir)

    previous = _previous_plan(job.job_id)
    if previous is None:
        raise PipelineError(
            f"No earlier render for {job.job_id}. Run `./process-job {job.job_id}` first."
        )

    record = feedback_module.interpret(
        feedback_text,
        job_id=job.job_id,
        revision=int(previous.get("revision", 1)),
        current_format=previous.get("template_name"),
        current_text_style=(
            previous.get("text_cues", [{}])[0].get("style")
            if previous.get("text_cues") else None
        ),
    )
    feedback_module.save(record, feedback_text)

    result = process(job_dir, apply_feedback=True, move_on_success=False)
    result.messages.insert(
        0,
        f"feedback {record.id} recorded: {len(record.directives)} directive(s), "
        f"{len(record.proposed_preferences)} preference proposal(s)",
    )
    if record.unmatched_phrases:
        result.warnings.append(
            "not understood as concrete changes: "
            + "; ".join(repr(phrase) for phrase in record.unmatched_phrases)
        )
    return record, result


def approve(job_reference: str | Path) -> Path:
    """Mark a job approved and move it out of review."""
    job_dir = find_job(str(job_reference))
    return move_job(job_dir, JOBS_APPROVED)
