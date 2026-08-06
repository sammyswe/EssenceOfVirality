"""Hard rules that no configuration, template, preference or feedback may override.

Every rule here maps to a creator instruction. ``check_*`` functions return a list
of violation strings; an empty list means the rule holds. The orchestrator refuses
to publish a render whose hard-rule check fails.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable

# Rule identifiers used in reports and quality checks.
RULE_SINGLE_AUDIO_SOURCE = "hard.audio.single_source"
RULE_NO_MUSIC_REPLACEMENT = "hard.audio.no_replacement"
RULE_NO_TRANSITION_EDIT = "hard.audio.no_transition_edit"
RULE_SPOTIFY_RECOGNISABLE = "hard.visual.spotify_recognisable"
RULE_SPOTIFY_UNOBSTRUCTED = "hard.visual.song_info_unobstructed"
RULE_VERTICAL_OUTPUT = "hard.render.vertical_1080x1920"
RULE_DURATION_WINDOW = "hard.render.duration_window"
RULE_ONE_TRANSITION = "hard.content.one_transition"
RULE_NO_INVENTED_FACTS = "hard.content.no_invented_facts"
RULE_SOURCES_IMMUTABLE = "hard.io.sources_never_modified"
RULE_TEXT_IN_SAFE_ZONE = "hard.visual.text_in_safe_zone"
RULE_PREFERENCE_APPROVAL = "hard.learning.explicit_approval_required"

HARD_RULES: dict[str, str] = {
    RULE_SINGLE_AUDIO_SOURCE: (
        "The Spotify recording supplies the only audio stream in the render."
    ),
    RULE_NO_MUSIC_REPLACEMENT: (
        "The music is never replaced, remixed, layered or supplemented with other audio."
    ),
    RULE_NO_TRANSITION_EDIT: (
        "The transition region is never cut, time-stretched or speed-changed."
    ),
    RULE_SPOTIFY_RECOGNISABLE: (
        "The Spotify surface keeps at least the configured minimum share of frame area "
        "and is visible during the transition."
    ),
    RULE_SPOTIFY_UNOBSTRUCTED: (
        "Overlay text never covers the song information or waveform region."
    ),
    RULE_VERTICAL_OUTPUT: "Output is 1080x1920, H.264, with an AAC audio track.",
    RULE_DURATION_WINDOW: (
        "Output duration stays within the configured window unless the job overrides it."
    ),
    RULE_ONE_TRANSITION: "One Spotify transition per video.",
    RULE_NO_INVENTED_FACTS: (
        "Copy never asserts artist news, trends, quotations or statistics without a "
        "recorded, dated source."
    ),
    RULE_SOURCES_IMMUTABLE: "Original input files are read-only; renders go to outputs/.",
    RULE_TEXT_IN_SAFE_ZONE: "Text stays inside the TikTok-safe text area.",
    RULE_PREFERENCE_APPROVAL: (
        "A lasting preference is only stored after explicit creator approval or repeated "
        "consistent feedback."
    ),
}


@dataclass(frozen=True)
class Violation:
    rule: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover - formatting only
        return f"{self.rule}: {self.detail}"


def check_audio_sources(audio_inputs: Iterable[str], spotify_path: str) -> list[Violation]:
    """Exactly one audio input, and it must be the Spotify recording."""
    inputs = list(audio_inputs)
    if len(inputs) != 1:
        return [Violation(
            RULE_SINGLE_AUDIO_SOURCE,
            f"expected exactly 1 audio input, found {len(inputs)}: {inputs}",
        )]
    if inputs[0] != spotify_path:
        return [Violation(
            RULE_SINGLE_AUDIO_SOURCE,
            f"audio input {inputs[0]!r} is not the Spotify recording {spotify_path!r}",
        )]
    return []


def check_transition_untouched(
    segments: Iterable[dict[str, Any]],
    transition_start: float,
    transition_end: float,
) -> list[Violation]:
    """No cut boundary or speed change may fall inside the transition region."""
    violations: list[Violation] = []
    for segment in segments:
        speed = float(segment.get("speed", 1.0) or 1.0)
        if speed != 1.0:
            violations.append(Violation(
                RULE_NO_TRANSITION_EDIT,
                f"segment {segment.get('id', '?')} applies speed {speed}",
            ))
        start = float(segment.get("source_in", 0.0))
        end = float(segment.get("source_out", 0.0))
        # A boundary strictly inside the protected region means the blend was cut.
        for boundary in (start, end):
            if transition_start < boundary < transition_end:
                violations.append(Violation(
                    RULE_NO_TRANSITION_EDIT,
                    f"cut at {boundary:.2f}s falls inside the transition region "
                    f"({transition_start:.2f}-{transition_end:.2f}s)",
                ))
    return violations


def check_spotify_share(area_fraction: float, minimum: float) -> list[Violation]:
    if area_fraction < minimum:
        return [Violation(
            RULE_SPOTIFY_RECOGNISABLE,
            f"Spotify occupies {area_fraction:.0%} of the frame, below the {minimum:.0%} floor",
        )]
    return []


def check_text_safe_zone(
    cues: Iterable[dict[str, Any]],
    text_area: dict[str, Any],
) -> list[Violation]:
    violations: list[Violation] = []
    for cue in cues:
        box = cue.get("box")
        if not box:
            continue
        x1, y1, x2, y2 = box["x1"], box["y1"], box["x2"], box["y2"]
        if (
            x1 < text_area["x_min"]
            or x2 > text_area["x_max"]
            or y1 < text_area["y_min"]
            or y2 > text_area["y_max"]
        ):
            violations.append(Violation(
                RULE_TEXT_IN_SAFE_ZONE,
                f"cue {cue.get('id', '?')!r} box ({x1},{y1})-({x2},{y2}) leaves the text area",
            ))
    return violations


def check_text_clear_of_spotify(
    cues: Iterable[dict[str, Any]],
    protected_boxes: Iterable[dict[str, Any]],
) -> list[Violation]:
    """Text must not intersect the song-information or waveform regions."""
    violations: list[Violation] = []
    boxes = list(protected_boxes)
    for cue in cues:
        box = cue.get("box")
        if not box:
            continue
        for protected in boxes:
            overlaps = not (
                box["x2"] <= protected["x1"]
                or box["x1"] >= protected["x2"]
                or box["y2"] <= protected["y1"]
                or box["y1"] >= protected["y2"]
            )
            if overlaps:
                violations.append(Violation(
                    RULE_SPOTIFY_UNOBSTRUCTED,
                    f"cue {cue.get('id', '?')!r} overlaps protected region "
                    f"{protected.get('name', 'spotify')}",
                ))
    return violations


def check_duration(duration: float, minimum: float, maximum: float) -> list[Violation]:
    if duration < minimum or duration > maximum:
        return [Violation(
            RULE_DURATION_WINDOW,
            f"duration {duration:.2f}s outside [{minimum:.1f}, {maximum:.1f}]s",
        )]
    return []


def check_resolution(width: int, height: int) -> list[Violation]:
    if (width, height) != (1080, 1920):
        return [Violation(
            RULE_VERTICAL_OUTPUT, f"output is {width}x{height}, expected 1080x1920",
        )]
    return []


def check_claims_sourced(claims: Iterable[dict[str, Any]]) -> list[Violation]:
    """Any factual assertion in copy needs a source with a date."""
    violations: list[Violation] = []
    for claim in claims:
        if not claim.get("source_url") or not claim.get("published_date"):
            violations.append(Violation(
                RULE_NO_INVENTED_FACTS,
                f"claim {claim.get('text', '?')!r} lacks a dated source",
            ))
    return violations
