"""Skill 6 — copywriting and the posting package.

Produces everything needed to post by hand: caption, hashtags, thumbnail choice,
pinned comment and prepared replies, alongside the decisions and hypothesis behind
the edit.

Copy never asserts an external fact unless a dated research note supports it.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from . import artifacts, copybank, hookprofiles, rules
from .creative import _stable_choice
from .editplan import EditPlan
from .inspector import InputReport
from .om import write_export_bundle
from .paths import rel
from .probe import extract_frame
from .quality import QualityReport

# Hashtag pools by strategy. Which pool performs best is an open question the
# analytics subsystem is meant to answer, so all four are tracked separately.
HASHTAG_POOLS: dict[str, list[str]] = {
    "spotify_specific": ["#spotify", "#spotifymix", "#spotifyplaylist", "#spotifytransition"],
    "niche": ["#mixing", "#transition", "#djtok", "#songmashup", "#backtoback"],
    "broad": ["#fyp", "#foryou", "#music", "#viral"],
    "artist_specific": [],
}

DEFAULT_STRATEGY = ["spotify_specific", "niche", "broad"]

_TAG_CLEAN = re.compile(r"[^a-z0-9]+")


@dataclass
class PostingPackage:
    job_id: str
    revision: int
    created_at: str
    final_hook: str
    onscreen_text: list[dict[str, Any]]
    caption: str
    hashtags: list[str]
    hashtag_strategy: list[str]
    thumbnail_frame_seconds: float
    thumbnail_path: str | None
    thumbnail_text: str
    call_to_action: str
    pinned_comment: str
    prepared_replies: list[str]
    creative_format: str
    editing_decisions: list[dict[str, str]]
    retention_hypothesis: str
    research_used: list[dict[str, Any]]
    output_file: str
    preview_file: str | None
    render_metadata: dict[str, Any]
    quality_status: str
    experiment: dict[str, Any] | None
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _artist_tags(job_tracks: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for slot in ("first", "second"):
        track = job_tracks.get(slot) or {}
        artist = str(track.get("artist", "") or "").strip()
        if artist:
            cleaned = _TAG_CLEAN.sub("", artist.lower())
            if cleaned:
                tags.append(f"#{cleaned}")
    return tags


def build_hashtags(
    job_tracks: dict[str, Any],
    strategy: list[str] | None = None,
    *,
    limit: int = 8,
) -> tuple[list[str], list[str]]:
    """Assemble hashtags from the configured strategy pools.

    Returns (hashtags, strategy_used) so analytics can compare pools later.
    """
    strategy = list(strategy or DEFAULT_STRATEGY)
    pools = dict(HASHTAG_POOLS)
    pools["artist_specific"] = _artist_tags(job_tracks)
    if pools["artist_specific"] and "artist_specific" not in strategy:
        strategy.insert(0, "artist_specific")

    tags: list[str] = []
    for pool_name in strategy:
        for tag in pools.get(pool_name, []):
            if tag not in tags:
                tags.append(tag)
            if len(tags) >= limit:
                return tags, strategy
    return tags, strategy


def _track_phrase(job_tracks: dict[str, Any]) -> str:
    first = job_tracks.get("first") or {}
    second = job_tracks.get("second") or {}
    first_title = str(first.get("title", "") or "").strip()
    second_title = str(second.get("title", "") or "").strip()
    if first_title and second_title:
        return f"{first_title} into {second_title}"
    return ""


def _render_copy_template(template: str, phrase: str) -> str | None:
    """Fill a bank caption/pinned template, or None when it cannot be filled.

    The only placeholder the package can always resolve is ``{pairing}``; an
    entry with any other unfilled placeholder (``{day_number}`` needs a value
    only the creator knows) is skipped for this job rather than posted broken.
    """
    rendered = template
    if "{pairing}" in rendered:
        if not phrase:
            return None
        rendered = rendered.replace("{pairing}", phrase)
    if "{" in rendered and "}" in rendered:
        return None
    return rendered.strip() or None


def build_caption(
    plan: EditPlan,
    job_tracks: dict[str, Any],
    research: list[dict[str, Any]] | None = None,
) -> str:
    """Write the caption. Facts appear only when a dated source backs them."""
    phrase = _track_phrase(job_tracks)
    lines: list[str] = []

    # Hook profiles carry a fixed trio of captions for that clip; when the plan
    # matched one, rotate among those three before falling back to the global bank.
    profile_candidates: list[str] = []
    if plan.hook_profile_id:
        for profile in hookprofiles.active_profiles():
            if profile.id != plan.hook_profile_id:
                continue
            for caption in profile.active_captions():
                rendered = _render_copy_template(caption.template, phrase)
                if rendered:
                    profile_candidates.append(rendered)
            break

    bank_candidates = [
        rendered
        for entry in copybank.active("captions")
        if (rendered := _render_copy_template(str(entry.get("template", "")), phrase))
    ]
    candidates = profile_candidates or bank_candidates
    if candidates:
        seed = f"{plan.job_id}:r{plan.revision}:caption"
        lines.append(_stable_choice(candidates, seed))
    elif phrase:
        lines.append(f"{phrase} — made in Spotify.")
    else:
        lines.append("Made in Spotify, one transition, no edits to the audio.")

    supported = [
        note for note in (research or [])
        if note.get("source_url") and note.get("published_date")
    ]
    if supported:
        lines.append(str(supported[0].get("caption_angle") or "").strip())

    if plan.cta_text:
        lines.append(plan.cta_text.rstrip("?.!") + "?")

    return "\n".join(line for line in lines if line)


def choose_thumbnail(plan: EditPlan) -> tuple[float, str]:
    """Pick a cover frame and its text.

    The frame sits just before the blend, where the Spotify surface shows both
    tracks and the hook text is still on screen.
    """
    candidate = max(plan.transition_output_seconds - 0.6, 0.2)
    candidate = min(candidate, max(plan.duration_seconds - 0.2, 0.2))
    text = plan.hook_text or "spotify transition"
    return candidate, text


def build_pinned_comment(plan: EditPlan, job_tracks: dict[str, Any]) -> str:
    phrase = _track_phrase(job_tracks)
    candidates = [
        rendered
        for entry in copybank.active("pinned_comments")
        if (rendered := _render_copy_template(str(entry.get("template", "")), phrase))
    ]
    if candidates:
        return _stable_choice(candidates, f"{plan.job_id}:r{plan.revision}:pinned")
    if phrase:
        return f"{phrase}. Made with Spotify's own mix feature — {plan.cta_text or 'thoughts?'}"
    return plan.cta_text or "Which pairing should I try next?"


def build_replies(plan: EditPlan, job_tracks: dict[str, Any]) -> list[str]:
    """Prepared, honest replies for likely comments."""
    second = (job_tracks.get("second") or {}).get("title", "")
    replies = [
        "Spotify's own mix feature did the blend — I picked the pairing and the timing.",
        "Drop a pairing and I'll try it in the next one.",
    ]
    if second:
        replies.append(f"Track two is {second}.")
    else:
        replies.append("Track two is in the caption.")
    return replies[:3]


def build_package(
    plan: EditPlan,
    input_report: InputReport,
    quality: QualityReport,
    *,
    job_tracks: dict[str, Any],
    final_path: Path,
    preview_path: Path | None,
    render_metadata: dict[str, Any],
    research: list[dict[str, Any]] | None = None,
    hashtag_strategy: list[str] | None = None,
    thumbnail_dir: Path | None = None,
) -> PostingPackage:
    """Assemble the posting package for one render."""
    warnings: list[str] = []
    research = list(research or [])

    unsupported = rules.check_claims_sourced(research)
    if unsupported:
        warnings.extend(str(violation) for violation in unsupported)
        research = [
            note for note in research
            if note.get("source_url") and note.get("published_date")
        ]

    hashtags, strategy_used = build_hashtags(job_tracks, hashtag_strategy)
    caption = build_caption(plan, job_tracks, research)
    thumbnail_seconds, thumbnail_text = choose_thumbnail(plan)

    thumbnail_path: str | None = None
    if thumbnail_dir is not None and final_path.is_file():
        destination = thumbnail_dir / f"{plan.job_id}-r{plan.revision}-thumbnail.jpg"
        try:
            extract_frame(final_path, thumbnail_seconds, destination)
            thumbnail_path = rel(destination)
        except Exception as exc:  # noqa: BLE001 - thumbnail is non-essential
            warnings.append(f"could not extract thumbnail frame: {exc}")

    onscreen = [
        {
            "text": cue.text,
            "role": cue.role,
            "start_seconds": cue.start_seconds,
            "end_seconds": cue.end_seconds,
        }
        for cue in plan.text_cues
    ]

    return PostingPackage(
        job_id=plan.job_id,
        revision=plan.revision,
        created_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        final_hook=plan.hook_text,
        onscreen_text=onscreen,
        caption=caption,
        hashtags=hashtags,
        hashtag_strategy=strategy_used,
        thumbnail_frame_seconds=round(thumbnail_seconds, 3),
        thumbnail_path=thumbnail_path,
        thumbnail_text=thumbnail_text,
        call_to_action=plan.cta_text,
        pinned_comment=build_pinned_comment(plan, job_tracks),
        prepared_replies=build_replies(plan, job_tracks),
        creative_format=plan.template_name,
        editing_decisions=plan.decisions,
        retention_hypothesis=plan.retention_hypothesis
        or "No explicit hypothesis recorded for this format.",
        research_used=research,
        output_file=rel(final_path),
        preview_file=rel(preview_path) if preview_path else None,
        render_metadata={
            **render_metadata,
            "transition_detection": input_report.transition,
            "crop_profile": input_report.crop_profile.name,
        },
        quality_status=quality.status,
        experiment=plan.experiment.as_dict() if plan.experiment else None,
        warnings=warnings,
    )


def write_package(package: PostingPackage, directory: Path) -> Path:
    """Write the package as YAML plus a copy-paste friendly Markdown sheet."""
    directory.mkdir(parents=True, exist_ok=True)
    stem = artifacts.stamp(package.job_id, package.revision)

    yaml_path = artifacts.write(
        directory / f"{stem}-posting-package.yaml",
        "posting_package",
        artifacts.artifact_id("pkg", stem),
        package.as_dict(),
        created_at=package.created_at,
    )

    markdown_path = directory / f"{stem}-posting-package.md"
    markdown_path.write_text(_markdown(package), encoding="utf-8")
    return yaml_path


def _markdown(package: PostingPackage) -> str:
    lines = [
        f"# Posting package — {package.job_id} (revision {package.revision})",
        "",
        f"Format: **{package.creative_format}** · Quality: **{package.quality_status}** · "
        f"Built {package.created_at}",
        "",
        "## Post this",
        "",
        f"- **Video**: `{package.output_file}`",
    ]
    if package.preview_file:
        lines.append(f"- **Preview**: `{package.preview_file}`")
    if package.thumbnail_path:
        lines.append(
            f"- **Cover frame**: `{package.thumbnail_path}` "
            f"(at {package.thumbnail_frame_seconds:.2f}s)"
        )
    lines += [
        "",
        "### Caption",
        "",
        "```",
        package.caption,
        " ".join(package.hashtags),
        "```",
        "",
        "### Pinned comment",
        "",
        "```",
        package.pinned_comment,
        "```",
        "",
        "### Prepared replies",
        "",
    ]
    lines += [f"{index}. {reply}" for index, reply in enumerate(package.prepared_replies, 1)]
    lines += [
        "",
        "## On-screen text",
        "",
        "| Time | Role | Text |",
        "|---|---|---|",
    ]
    for cue in package.onscreen_text:
        lines.append(
            f"| {cue['start_seconds']:.2f}–{cue['end_seconds']:.2f}s | {cue['role']} "
            f"| {cue['text']} |"
        )

    lines += [
        "",
        "## Why this edit",
        "",
        f"Retention hypothesis: {package.retention_hypothesis}",
        "",
        "| Decision | Rationale |",
        "|---|---|",
    ]
    for decision in package.editing_decisions:
        lines.append(f"| {decision.get('decision', '')} | {decision.get('rationale', '')} |")

    if package.experiment:
        lines += [
            "",
            "## Experiment",
            "",
            f"- Hypothesis: {package.experiment.get('hypothesis', '')}",
            f"- Variable: `{package.experiment.get('variable', '')}`",
            f"- Control: `{package.experiment.get('control_reference', '')}`",
            f"- Expected effect: `{package.experiment.get('expected_effect', '')}`",
            f"- Status: `{package.experiment.get('status', '')}`",
        ]

    if package.research_used:
        lines += ["", "## Research used", ""]
        for note in package.research_used:
            lines.append(
                f"- {note.get('summary', '')} — {note.get('source_url', '')} "
                f"({note.get('published_date', '')})"
            )

    if package.warnings:
        lines += ["", "## Warnings", ""]
        lines += [f"- {warning}" for warning in package.warnings]

    lines += [
        "",
        "---",
        "",
        "Posting is manual. This package describes a retention hypothesis, not a "
        "prediction of reach.",
        "",
    ]
    return "\n".join(lines)


def write_export_bundle_if_available(
    package: PostingPackage, final_path: Path, export_dir: Path
) -> dict[str, Any]:
    """Ask OpenMontage to lay out an export bundle alongside our own package."""
    outcome = write_export_bundle(
        final_path,
        title=f"{package.job_id} r{package.revision}",
        export_dir=export_dir,
        description=package.caption,
        hashtags=package.hashtags,
    )
    return {"backend": outcome.backend, "success": outcome.success, "error": outcome.error}
