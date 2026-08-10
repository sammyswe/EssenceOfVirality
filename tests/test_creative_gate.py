"""Unit tests for the creative-minimum gate and retention-hypothesis honesty."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from production.pipeline import creative_gate
from production.pipeline.editplan import EditPlan, Emphasis, Placement
from production.pipeline.jobspec import JobSpec
from production.pipeline.quality import Check, PASS, QualityReport


def _job(**overrides: Any) -> JobSpec:
    base = dict(
        job_id="job-gate-test",
        job_dir=Path("/tmp/job-gate-test"),
        spotify_recording=Path("/tmp/job-gate-test/spotify.mp4"),
        assets=[],
        creative_direction={
            "preferred_format": "auto",
            "waive_track_metadata": False,
            "waive_empty_asset_fallback": False,
            "waive_generic_hook": False,
        },
        tracks={"first": {}, "second": {}},
    )
    base.update(overrides)
    return JobSpec(**base)


def _plan(**overrides: Any) -> EditPlan:
    base = dict(
        job_id="job-gate-test",
        revision=1,
        format_family="clean_showcase",
        template_name="clean-showcase",
        source_in_seconds=0.0,
        source_out_seconds=21.0,
        duration_seconds=21.0,
        transition_output_seconds=7.0,
        transition_window=(5.8, 9.0),
        layout_mode="full",
        spotify_placement=Placement(0, 0, 1080, 1920),
        background="blurred_spotify",
        hook_text="wait for the switch",
        empty_asset_fallback=True,
        emphasis=Emphasis(
            enabled=False, at_seconds=7.0, amount=0.08,
            attack_seconds=0.35, release_seconds=0.55,
        ),
    )
    base.update(overrides)
    return EditPlan(**base)


def test_recording_only_blank_metadata_fails_creative_minimum():
    report = creative_gate.evaluate(_job(), _plan())
    assert not report.passed
    failed_ids = {check.id for check in report.failures}
    assert "track_metadata" in failed_ids
    assert "format_not_empty_default" in failed_ids
    assert "hook_specificity" in failed_ids
    assert any("Fill tracks" in action for action in report.creator_actions)
    assert any("supporting" in action.lower() or "preferred_format" in action
               for action in report.creator_actions)


def test_tracks_force_format_and_specific_hook_pass():
    job = _job(
        tracks={
            "first": {"title": "Night Drive", "artist": "Lowbeam"},
            "second": {"title": "Paper Lanterns", "artist": "Ashra Kite"},
        },
        creative_direction={
            "preferred_format": "clean-showcase",
            "hook": "Lowbeam into Ashra Kite",
            "waive_track_metadata": False,
            "waive_empty_asset_fallback": False,
            "waive_generic_hook": False,
        },
    )
    plan = _plan(
        empty_asset_fallback=True,  # would fail unless forced
        hook_text="Lowbeam into Ashra Kite",
        template_name="clean-showcase",
    )
    report = creative_gate.evaluate(job, plan)
    assert report.passed, [c.as_dict() for c in report.failures]


def test_waivers_allow_blank_recording_only_job():
    job = _job(
        creative_direction={
            "preferred_format": "auto",
            "waive_track_metadata": True,
            "waive_empty_asset_fallback": True,
            "waive_generic_hook": True,
        },
    )
    report = creative_gate.evaluate(job, _plan())
    assert report.passed


def test_quality_report_post_ready_requires_creative_minimum():
    report = QualityReport(
        job_id="job-gate-test",
        revision=1,
        video_path="outputs/final/x.mp4",
        created_at="2026-08-10T00:00:00Z",
        checks=[Check("file_exists", "exists", PASS, "ok")],
    )
    assert report.technically_valid
    assert not report.post_ready  # creative gate not attached yet

    report.creative_minimum = {"passed": False, "status": "fail"}
    assert report.technically_valid
    assert not report.post_ready

    report.creative_minimum = {"passed": True, "status": "pass"}
    assert report.post_ready


def test_retention_hypothesis_omits_zoom_when_emphasis_disabled():
    template = (
        "Keeping the Spotify surface unobstructed and marking the transition "
        "with a single zoom is expected to protect completion_rate by making "
        "the payoff legible, with no competing visual to explain."
    )
    enabled = creative_gate.compose_retention_hypothesis(
        template, emphasis_enabled=True,
    )
    disabled = creative_gate.compose_retention_hypothesis(
        template, emphasis_enabled=False,
    )
    assert "zoom" in enabled.lower()
    assert "zoom-marked payoff" in disabled.lower()
    assert "disabled" in disabled.lower()
    # Must not claim the render uses zoom as the payoff marker.
    assert "marking the transition with a single zoom" not in disabled


def test_hook_references_tracks():
    tracks = {
        "first": {"title": "Night Drive", "artist": "Lowbeam"},
        "second": {"title": "Paper Lanterns", "artist": "Ashra Kite"},
    }
    assert creative_gate.hook_references_tracks("Lowbeam into Ashra Kite", tracks)
    assert not creative_gate.hook_references_tracks("wait for the switch", tracks)


def test_tracks_complete():
    assert not creative_gate.tracks_complete({"first": {}, "second": {}})
    assert creative_gate.tracks_complete({
        "first": {"title": "A", "artist": "B"},
        "second": {"title": "C", "artist": "D"},
    })
