"""Skill 8 — feedback interpretation.

Turns natural-language creator feedback into structured records and concrete
revision directives. Two things it deliberately will not do: guess at a directive
it cannot justify, and promote a lasting preference without approval.

Interpretation is rule-based and auditable: every directive names the phrase that
triggered it, so a wrong reading can be corrected rather than argued with.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

from . import preferences as prefs
from .paths import FEEDBACK_RAW, FEEDBACK_STRUCTURED, rel

# Scope of a piece of feedback.
SCOPE_ONE_OFF = "one_off"
SCOPE_FORMAT = "format_specific"
SCOPE_ARTIST = "artist_specific"
SCOPE_ASSET = "asset_specific"
SCOPE_PREFERENCE = "potential_permanent_preference"

# Phrases that mark feedback as a lasting rule rather than a note on this render.
_LASTING_MARKERS = re.compile(
    r"\b(always|never|from now on|going forward|every time|as a rule|by default|"
    r"keep (?:this|that)|stop using|use (?:this|that) more)\b",
    re.IGNORECASE,
)

# Phrases that keep feedback scoped to this render only.
_ONE_OFF_MARKERS = re.compile(
    r"\b(this time|just here|on this one|for this video|in this edit)\b", re.IGNORECASE
)

_FORMAT_QUALIFIER = re.compile(
    r"\b(?:but )?only for ([a-z -]+?)(?: videos| edits| ones)?\b", re.IGNORECASE
)


@dataclass
class Directive:
    """One concrete change to apply on the next render."""

    action: str
    parameters: dict[str, Any] = field(default_factory=dict)
    stage: str = "creative"
    trigger_phrase: str = ""
    confidence: str = "medium"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackRecord:
    """Structured form of one feedback submission."""

    id: str
    job_id: str
    revision: int
    created_at: str
    raw_feedback: str
    interpreted_issues: list[str]
    directives: list[Directive]
    scope: str
    scope_value: str
    confidence: str
    approval_required: bool
    proposed_preferences: list[str] = field(default_factory=list)
    unmatched_phrases: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["directives"] = [directive.as_dict() for directive in self.directives]
        return data


# Each rule: (pattern, issue, action, parameters, stage, preference key/value or None)
_RULES: list[tuple[re.Pattern[str], str, str, dict[str, Any], str, tuple[str, Any] | None]] = [
    (
        re.compile(r"spotify.{0,24}(too small|bigger|larger|hard to see)|"
                   r"(make|want).{0,16}(waveform|spotify).{0,16}(bigger|larger)",
                   re.IGNORECASE),
        "The Spotify surface is not prominent enough.",
        "increase_spotify_area", {"step": 0.08}, "layout",
        ("spotify_fraction", "+0.08"),
    ),
    (
        re.compile(r"spotify.{0,24}(too big|too large|smaller)", re.IGNORECASE),
        "The Spotify surface dominates too much.",
        "decrease_spotify_area", {"step": 0.06}, "layout",
        ("spotify_fraction", "-0.06"),
    ),
    (
        re.compile(r"\b(hook|opening line|first line).{0,30}"
                   r"(too generic|generic|boring|weak|bland)", re.IGNORECASE),
        "The hook is too generic.",
        "regenerate_hook", {"avoid_previous": True}, "creative", None,
    ),
    (
        re.compile(r"\b(opening|intro|start|beginning).{0,24}(too slow|slow|drags|dragging)",
                   re.IGNORECASE),
        "The opening takes too long to reach the payoff.",
        "shorten_lead_in", {"seconds": 2.0}, "retention", None,
    ),
    (
        re.compile(r"\b(ai clip|ai footage|hook clip|the clip).{0,30}"
                   r"(distract|distracting|too much|competes|overpowers)", re.IGNORECASE),
        "The supporting clip competes with the transition.",
        "shorten_secondary", {"factor": 0.6}, "layout", None,
    ),
    (
        re.compile(r"(remove|drop|lose|get rid of|no more).{0,20}"
                   r"(ai clip|hook clip|secondary|extra clip|the clip)", re.IGNORECASE),
        "The supporting clip should not be used.",
        "remove_secondary", {}, "layout", None,
    ),
    (
        re.compile(r"(remove|no|drop|never use|stop).{0,24}zoom", re.IGNORECASE),
        "The zoom emphasis is unwanted.",
        "disable_zoom", {}, "retention", ("zoom_emphasis", False),
    ),
    (
        re.compile(r"(more|stronger|bigger).{0,20}(zoom|emphasis|punch)", re.IGNORECASE),
        "The transition needs stronger visual emphasis.",
        "increase_emphasis", {"amount_step": 0.05}, "retention", None,
    ),
    (
        re.compile(r"transition.{0,30}(needs|more).{0,20}(emphasis|visual|punch|impact)",
                   re.IGNORECASE),
        "The transition needs stronger visual emphasis.",
        "increase_emphasis", {"amount_step": 0.05}, "retention", None,
    ),
    (
        re.compile(r"(remove|no|drop).{0,20}(progress bar|progress)", re.IGNORECASE),
        "The progress bar is unwanted.",
        "disable_progress_bar", {}, "retention", ("progress_bar", False),
    ),
    (
        re.compile(r"caption.{0,30}(artificial|robotic|ai|fake|generic|cringe)", re.IGNORECASE),
        "The caption does not sound like the creator.",
        "rewrite_caption", {"register": "plain"}, "copy", None,
    ),
    (
        re.compile(r"(keep|like|love).{0,24}(this|that).{0,16}(text style|font|styling)",
                   re.IGNORECASE),
        "The current text style is approved.",
        "keep_text_style", {}, "copy", ("text_style", "current"),
    ),
    (
        re.compile(r"(use|do).{0,20}(this|that).{0,20}(layout|format).{0,16}more",
                   re.IGNORECASE),
        "This layout should be used more often.",
        "keep_format", {}, "creative", ("preferred_format", "current"),
    ),
    (
        re.compile(r"\b(too long|shorten it|make it shorter|cut it down)\b", re.IGNORECASE),
        "The edit runs longer than wanted.",
        "shorten_output", {"seconds": 4.0}, "retention", None,
    ),
    (
        re.compile(r"\b(too short|make it longer|extend it)\b", re.IGNORECASE),
        "The edit is shorter than wanted.",
        "lengthen_output", {"seconds": 4.0}, "retention", None,
    ),
    (
        re.compile(r"(no|remove|drop).{0,16}(text|captions?|overlay)s?\b", re.IGNORECASE),
        "On-screen text is unwanted in this edit.",
        "remove_text", {}, "copy", None,
    ),
    (
        re.compile(r"(cta|call to action).{0,30}(weak|change|different|generic)",
                   re.IGNORECASE),
        "The call to action needs changing.",
        "regenerate_cta", {"avoid_previous": True}, "copy", None,
    ),
    (
        re.compile(r"\b(switch|change|use).{0,20}(split[- ]?screen|picture[- ]?in[- ]?picture|"
                   r"pip|clean showcase|comedy hook|curiosity|reaction)\b", re.IGNORECASE),
        "A different format family was requested.",
        "change_format", {}, "creative", None,
    ),
]

_FORMAT_ALIASES = {
    "split-screen": "split-screen",
    "split screen": "split-screen",
    "splitscreen": "split-screen",
    "picture-in-picture": "picture-in-picture",
    "picture in picture": "picture-in-picture",
    "pip": "picture-in-picture",
    "clean showcase": "clean-showcase",
    "comedy hook": "comedy-hook",
    "curiosity": "curiosity",
    "reaction": "reaction",
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _split_statements(text: str) -> list[str]:
    parts = re.split(r"[.;\n]+|,\s*(?=and\b|but\b)|\band\b(?=\s+(?:make|remove|the|use|keep))",
                     text)
    return [part.strip() for part in parts if part and part.strip()]


def classify_scope(text: str) -> tuple[str, str, str]:
    """Return (scope, scope_value, confidence) for a feedback string."""
    format_match = _FORMAT_QUALIFIER.search(text)
    if format_match:
        qualifier = format_match.group(1).strip().lower()
        alias = _FORMAT_ALIASES.get(qualifier, qualifier)
        return SCOPE_FORMAT, alias, "medium"
    if _ONE_OFF_MARKERS.search(text):
        return SCOPE_ONE_OFF, "", "high"
    if _LASTING_MARKERS.search(text):
        return SCOPE_PREFERENCE, "", "high"
    return SCOPE_ONE_OFF, "", "low"


def interpret(
    raw_feedback: str,
    *,
    job_id: str,
    revision: int,
    current_format: str | None = None,
    current_text_style: str | None = None,
) -> FeedbackRecord:
    """Convert free-text feedback into a structured record with directives."""
    text = (raw_feedback or "").strip()
    if not text:
        raise ValueError("feedback is empty")

    directives: list[Directive] = []
    issues: list[str] = []
    proposed_keys: list[tuple[str, Any, str]] = []
    matched_spans: list[str] = []

    statements = _split_statements(text)
    for statement in statements:
        statement_matched = False
        for pattern, issue, action, parameters, stage, preference in _RULES:
            match = pattern.search(statement)
            if not match:
                continue
            statement_matched = True
            matched_spans.append(match.group(0))
            params = dict(parameters)

            if action == "change_format":
                requested = None
                for alias, canonical in _FORMAT_ALIASES.items():
                    if alias in statement.lower():
                        requested = canonical
                        break
                if requested is None:
                    continue
                params["format"] = requested

            if issue not in issues:
                issues.append(issue)
            directives.append(Directive(
                action=action,
                parameters=params,
                stage=stage,
                trigger_phrase=match.group(0),
                confidence="medium",
            ))
            if preference is not None:
                key, value = preference
                if value == "current":
                    resolved = (
                        current_format if key == "preferred_format" else current_text_style
                    )
                    if resolved:
                        proposed_keys.append((key, resolved, statement))
                else:
                    proposed_keys.append((key, value, statement))

        if not statement_matched and len(statement.split()) >= 3:
            matched_spans.append("")

    unmatched = [
        statement for statement in statements
        if len(statement.split()) >= 3
        and not any(pattern.search(statement) for pattern, *_ in _RULES)
    ]

    scope, scope_value, scope_confidence = classify_scope(text)
    if not directives:
        confidence = "low"
    elif len(unmatched) > len(directives):
        confidence = "low"
    else:
        confidence = scope_confidence if scope_confidence != "low" else "medium"

    record_id = (
        f"fb-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}-{job_id}-r{revision}"
    )

    notes: list[str] = []
    if unmatched:
        notes.append(
            "Some feedback was not understood as a concrete change; it is recorded "
            "verbatim and needs either a rephrase or a manual edit."
        )
    if scope == SCOPE_PREFERENCE:
        notes.append(
            "Wording suggests a lasting rule. A preference proposal has been written; "
            "it takes effect only after approval."
        )

    record = FeedbackRecord(
        id=record_id,
        job_id=job_id,
        revision=revision,
        created_at=_now(),
        raw_feedback=text,
        interpreted_issues=issues,
        directives=directives,
        scope=scope,
        scope_value=scope_value,
        confidence=confidence,
        approval_required=scope == SCOPE_PREFERENCE or confidence == "low",
        unmatched_phrases=unmatched,
        notes=notes,
    )

    # Preference proposals: recorded, never applied automatically.
    for key, value, statement in proposed_keys:
        preference_scope = "format" if scope == SCOPE_FORMAT else "global"
        preference = prefs.propose(
            key=key,
            value=value,
            statement=statement.strip(),
            scope=preference_scope,
            scope_value=scope_value if preference_scope == "format" else "",
            confidence="low" if scope != SCOPE_PREFERENCE else "medium",
            evidence=[{
                "ref": record_id,
                "job_id": job_id,
                "revision": revision,
                "quote": statement.strip(),
                "recorded_at": record.created_at,
            }],
        )
        record.proposed_preferences.append(preference.id)

    return record


def save(record: FeedbackRecord, raw_text: str) -> tuple[Path, Path]:
    """Persist the raw text and the structured record."""
    FEEDBACK_RAW.mkdir(parents=True, exist_ok=True)
    FEEDBACK_STRUCTURED.mkdir(parents=True, exist_ok=True)

    raw_path = FEEDBACK_RAW / f"{record.id}.txt"
    raw_path.write_text(raw_text.strip() + "\n", encoding="utf-8")

    structured_path = FEEDBACK_STRUCTURED / f"{record.id}.yaml"
    payload = record.as_dict()
    payload["artifact_kind"] = "creator_feedback"
    payload["raw_file"] = rel(raw_path)
    structured_path.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return raw_path, structured_path


def load_for_job(job_id: str) -> list[FeedbackRecord]:
    """Every structured feedback record for a job, oldest first."""
    if not FEEDBACK_STRUCTURED.is_dir():
        return []
    records: list[FeedbackRecord] = []
    for path in sorted(FEEDBACK_STRUCTURED.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if data.get("job_id") != job_id:
            continue
        data.pop("artifact_kind", None)
        data.pop("raw_file", None)
        data["directives"] = [Directive(**item) for item in data.get("directives", [])]
        try:
            records.append(FeedbackRecord(**data))
        except TypeError:
            continue
    return records


def merge_directives(records: Iterable[FeedbackRecord]) -> list[Directive]:
    """Collapse a history of feedback into the directives to apply now.

    Later feedback wins for the same action; contradictory pairs cancel so a
    creator can undo an earlier instruction by stating the opposite.
    """
    opposites = {
        "increase_spotify_area": "decrease_spotify_area",
        "decrease_spotify_area": "increase_spotify_area",
        "disable_zoom": "increase_emphasis",
        "increase_emphasis": "disable_zoom",
        "shorten_output": "lengthen_output",
        "lengthen_output": "shorten_output",
    }
    merged: dict[str, Directive] = {}
    for record in records:
        for directive in record.directives:
            merged.pop(opposites.get(directive.action, ""), None)
            merged[directive.action] = directive
    return list(merged.values())
