"""Word-timed lyric captions ("karaoke" cues).

Reads a creator-supplied ``lyrics.yaml`` from the job folder and turns it into
word-group caption windows for the retention editor. The pipeline never invents
lyrics: the sheet must carry ``verified: true`` — set by the creator after
checking the words and their timing against the actual recording — before any
lyric reaches the screen. An unverified sheet is reported and skipped, because a
wrong lyric on screen is worse than none.

Times in the sheet are expressed against the **source recording** timeline; the
caller maps them onto the output timeline via the plan's source window.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

LYRICS_FILENAME = "lyrics.yaml"

# Display shorter than this reads as flicker on a phone.
MIN_DISPLAY_SECONDS = 0.35


class LyricsError(ValueError):
    """Raised when a lyrics sheet is present but structurally unusable."""


@dataclass
class LyricWord:
    text: str
    start: float
    end: float


@dataclass
class LyricSheet:
    """A validated word-timed lyric sheet for one job."""

    path: Path
    verified: bool
    source_urls: list[str]
    words: list[LyricWord]
    group_max_words: int = 3
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": str(self.path),
            "verified": self.verified,
            "source_urls": self.source_urls,
            "word_count": len(self.words),
            "group_max_words": self.group_max_words,
        }


@dataclass
class LyricGroup:
    """One on-screen caption: a few consecutive words and their window."""

    text: str
    start_seconds: float           # output timeline
    end_seconds: float
    style_index: int = 0
    stripped_characters: list[str] = field(default_factory=list)


def _is_renderable(char: str) -> bool:
    """True when the character survives an FFmpeg drawtext pass legibly.

    Colour emoji do not render through drawtext with the fonts this pipeline
    ships; they come out as tofu boxes. They are stripped with a warning rather
    than burned in broken. (Emoji-capable caption rendering is an upgrade path,
    not a silent degradation — see docs/guides/hook-overlay-recipe.md.)
    """
    if char in {"\n", " "}:
        return True
    category = unicodedata.category(char)
    if category.startswith(("L", "N", "P")):
        # Letters, numbers, punctuation — but emoji live in So/Sk mostly.
        return ord(char) < 0x2600
    if category in {"Zs"}:
        return True
    if category in {"Sm", "Sc"}:  # maths / currency symbols render fine
        return True
    return False


def _clean_word(raw: str) -> tuple[str, list[str]]:
    kept: list[str] = []
    stripped: list[str] = []
    for char in raw:
        if _is_renderable(char):
            kept.append(char)
        else:
            stripped.append(char)
    return "".join(kept).strip(), stripped


def load_sheet(job_dir: Path) -> LyricSheet | None:
    """Load ``lyrics.yaml`` from the job folder, or None when absent."""
    path = Path(job_dir) / LYRICS_FILENAME
    if not path.is_file():
        return None

    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise LyricsError(f"{path} must contain a YAML mapping")

    raw_words = loaded.get("words")
    if not isinstance(raw_words, list) or not raw_words:
        raise LyricsError(f"{path} has no 'words' list")

    words: list[LyricWord] = []
    previous_start = -1.0
    for index, entry in enumerate(raw_words):
        if not isinstance(entry, dict):
            raise LyricsError(f"{path} words[{index}] must be a mapping")
        text = str(entry.get("text", "")).strip()
        if not text:
            raise LyricsError(f"{path} words[{index}] has empty text")
        try:
            start = float(entry["start"])
            end = float(entry["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise LyricsError(
                f"{path} words[{index}] needs numeric 'start' and 'end' seconds"
            ) from exc
        if end <= start:
            raise LyricsError(
                f"{path} words[{index}] ({text!r}) ends at {end}s, "
                f"before it starts at {start}s"
            )
        if start < previous_start:
            raise LyricsError(
                f"{path} words[{index}] ({text!r}) starts at {start}s, earlier than "
                "the previous word — the sheet must be in singing order"
            )
        previous_start = start
        words.append(LyricWord(text=text, start=start, end=end))

    sources = loaded.get("source_urls") or loaded.get("sources") or []
    if isinstance(sources, str):
        sources = [sources]

    return LyricSheet(
        path=path,
        verified=bool(loaded.get("verified", False)),
        source_urls=[str(url) for url in sources],
        words=words,
        group_max_words=max(1, int(loaded.get("group_max_words", 3))),
        notes=str(loaded.get("notes", "") or ""),
    )


def build_groups(
    sheet: LyricSheet,
    *,
    source_in: float,
    output_duration: float,
    gap_break_seconds: float = 0.6,
    hold_seconds: float = 0.25,
    style_count: int = 3,
) -> tuple[list[LyricGroup], list[str]]:
    """Group consecutive words into caption windows on the output timeline.

    A group closes when it reaches ``group_max_words`` or the singer pauses for
    longer than ``gap_break_seconds``. Groups outside the output window are
    dropped; groups too brief to read are extended to ``MIN_DISPLAY_SECONDS``
    but never into their successor.
    """
    warnings: list[str] = []
    stripped_all: list[str] = []

    # Map to output time and drop words outside the rendered window.
    mapped: list[LyricWord] = []
    for word in sheet.words:
        start = word.start - source_in
        end = word.end - source_in
        if end <= 0 or start >= output_duration:
            continue
        text, stripped = _clean_word(word.text)
        stripped_all.extend(stripped)
        if not text:
            continue
        mapped.append(LyricWord(
            text=text,
            start=max(0.0, start),
            end=min(end, output_duration),
        ))

    if stripped_all:
        unique = sorted(set(stripped_all))
        warnings.append(
            "stripped characters drawtext cannot render legibly (colour emoji): "
            + " ".join(unique)
        )

    groups: list[LyricGroup] = []
    bucket: list[LyricWord] = []

    def flush() -> None:
        if not bucket:
            return
        text = " ".join(word.text for word in bucket)
        groups.append(LyricGroup(
            text=text,
            start_seconds=round(bucket[0].start, 3),
            end_seconds=round(bucket[-1].end, 3),
            style_index=len(groups) % max(1, style_count),
        ))
        bucket.clear()

    for word in mapped:
        if bucket:
            gap = word.start - bucket[-1].end
            if len(bucket) >= sheet.group_max_words or gap > gap_break_seconds:
                flush()
        bucket.append(word)
    flush()

    # Readability: hold each caption briefly, but never into the next one.
    for index, group in enumerate(groups):
        limit = (
            groups[index + 1].start_seconds if index + 1 < len(groups)
            else output_duration
        )
        desired = max(
            group.end_seconds + hold_seconds,
            group.start_seconds + MIN_DISPLAY_SECONDS,
        )
        group.end_seconds = round(min(desired, max(limit - 0.05, group.end_seconds)), 3)

    too_quick = sum(
        1 for group in groups
        if group.end_seconds - group.start_seconds < MIN_DISPLAY_SECONDS
    )
    if too_quick:
        warnings.append(
            f"{too_quick} lyric caption(s) display for under {MIN_DISPLAY_SECONDS}s "
            "because the next word arrives immediately; check the timing sheet"
        )

    return groups, warnings
