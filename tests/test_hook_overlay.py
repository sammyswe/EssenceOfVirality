"""Tests for the hook-overlay recipe pieces: lyric sheets, grouping, timing."""

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from production.pipeline import lyrics  # noqa: E402
from production.pipeline.creative import plan_timing  # noqa: E402
from production.pipeline.inspector import CropProfile, InputReport  # noqa: E402
from production.pipeline.jobspec import JobSpec  # noqa: E402
from production.pipeline.paths import load_config, load_templates  # noqa: E402


# ---------------------------------------------------------------- lyric sheets

def _write_sheet(tmp_path: Path, body: str) -> Path:
    (tmp_path / "lyrics.yaml").write_text(textwrap.dedent(body), encoding="utf-8")
    return tmp_path


def test_missing_sheet_returns_none(tmp_path):
    assert lyrics.load_sheet(tmp_path) is None


def test_sheet_loads_and_reports_verification(tmp_path):
    _write_sheet(tmp_path, """
        verified: false
        source_urls: ["https://example.com/lyrics"]
        words:
          - {text: "GOTTA", start: 1.0, end: 1.4}
          - {text: "LET", start: 1.4, end: 1.7}
    """)
    sheet = lyrics.load_sheet(tmp_path)
    assert sheet is not None
    assert sheet.verified is False
    assert len(sheet.words) == 2
    assert sheet.source_urls == ["https://example.com/lyrics"]


def test_sheet_rejects_unordered_words(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        words:
          - {text: "LATER", start: 5.0, end: 5.5}
          - {text: "EARLIER", start: 1.0, end: 1.5}
    """)
    with pytest.raises(lyrics.LyricsError):
        lyrics.load_sheet(tmp_path)


def test_sheet_rejects_backwards_window(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        words:
          - {text: "BAD", start: 2.0, end: 1.0}
    """)
    with pytest.raises(lyrics.LyricsError):
        lyrics.load_sheet(tmp_path)


def test_grouping_respects_max_words_and_gaps(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        group_max_words: 2
        words:
          - {text: "WHEN", start: 1.0, end: 1.2}
          - {text: "YOUR", start: 1.2, end: 1.4}
          - {text: "LIFE", start: 1.4, end: 1.6}
          - {text: "GETS", start: 1.6, end: 1.8}
          - {text: "COMPLICATED", start: 4.0, end: 4.8}
    """)
    sheet = lyrics.load_sheet(tmp_path)
    groups, warnings = lyrics.build_groups(
        sheet, source_in=0.0, output_duration=30.0
    )
    assert [group.text for group in groups] == [
        "WHEN YOUR", "LIFE GETS", "COMPLICATED",
    ]
    # Colour rotation advances per group.
    assert [group.style_index for group in groups] == [0, 1, 2]
    assert warnings == []


def test_groups_map_to_output_time_and_drop_outside_window(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        words:
          - {text: "BEFORE", start: 2.0, end: 2.4}
          - {text: "INSIDE", start: 12.0, end: 12.5}
          - {text: "AFTER", start: 55.0, end: 55.5}
    """)
    sheet = lyrics.load_sheet(tmp_path)
    groups, _ = lyrics.build_groups(sheet, source_in=10.0, output_duration=30.0)
    assert len(groups) == 1
    assert groups[0].text == "INSIDE"
    assert groups[0].start_seconds == pytest.approx(2.0)


def test_emoji_is_stripped_with_warning(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        words:
          - {text: "MUSIC 🎧", start: 1.0, end: 1.5}
    """)
    sheet = lyrics.load_sheet(tmp_path)
    groups, warnings = lyrics.build_groups(sheet, source_in=0.0, output_duration=10.0)
    assert groups[0].text == "MUSIC"
    assert any("emoji" in warning for warning in warnings)


def test_captions_held_for_readability_but_not_into_successor(tmp_path):
    _write_sheet(tmp_path, """
        verified: true
        group_max_words: 1
        words:
          - {text: "FAST", start: 1.0, end: 1.1}
          - {text: "NEXT", start: 1.2, end: 1.4}
    """)
    sheet = lyrics.load_sheet(tmp_path)
    groups, _ = lyrics.build_groups(sheet, source_in=0.0, output_duration=10.0)
    # First caption may not overlap the second's start.
    assert groups[0].end_seconds <= groups[1].start_seconds
    # Last caption gets its readability hold.
    assert groups[1].end_seconds - groups[1].start_seconds >= lyrics.MIN_DISPLAY_SECONDS


# --------------------------------------------------------- full-recording mode

def _fake_job(tmp_path: Path) -> JobSpec:
    return JobSpec(
        job_id="test-job",
        job_dir=tmp_path,
        spotify_recording=tmp_path / "spotify.mp4",
        config=load_config("defaults"),
    )


def _fake_report(duration: float, transition_at: float) -> InputReport:
    return InputReport(
        job_id="test-job",
        spotify={"path": "spotify.mp4", "duration_seconds": duration,
                 "width": 1080, "height": 1920},
        crop_profile=CropProfile(
            name="test", description="test profile",
            crop={"x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0},
            must_remain_visible={}, fit="cover",
        ),
        protected_regions=[],
        transition={"seconds": transition_at,
                    "start_seconds": transition_at - 1.2,
                    "end_seconds": transition_at + 2.0},
        beats=None,
        loudness=None,
        assets=[],
        blocking_problems=[],
        warnings=[],
        backends={},
    )


def test_use_full_recording_keeps_everything(tmp_path):
    job = _fake_job(tmp_path)
    report = _fake_report(duration=52.0, transition_at=20.0)
    template = load_templates()["hook-overlay"]
    timing = plan_timing(job, report, template)
    assert timing.source_in == 0.0
    assert timing.source_out == pytest.approx(52.0)
    assert timing.duration == pytest.approx(52.0)
    assert timing.transition_output == pytest.approx(20.0)


def test_trimming_templates_unchanged(tmp_path):
    job = _fake_job(tmp_path)
    report = _fake_report(duration=90.0, transition_at=45.0)
    template = load_templates()["clean-showcase"]
    timing = plan_timing(job, report, template)
    assert timing.duration <= float(job.config["duration"]["maximum_seconds"]) + 1.0


def test_hook_overlay_template_shape():
    template = load_templates()["hook-overlay"]
    assert template["family"] == "hook_overlay"
    assert (template["pacing"] or {}).get("use_full_recording") is True
    assert (template["constraints"] or {}).get("karaoke_lyrics") is True
    assert set(template["cta_slots"]) == {"build", "post_payoff", "closing"}
    rotation = template["text_styles"]["lyric_rotation"]
    styles = load_config("text-styles")["styles"]
    for name in [*rotation, template["text_styles"]["cta"],
                 template["text_styles"]["hook"]]:
        assert name in styles, f"template references undefined style {name!r}"
