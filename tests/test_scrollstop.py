"""Tests for scroll-stop technique loading and application."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from production.pipeline import scrollstop  # noqa: E402


def test_load_active_techniques_from_skill_bank():
    techniques = scrollstop.active_techniques()
    ids = {technique.id for technique in techniques}
    assert "tech-20260818-pattern-interrupt-open" in ids
    assert "tech-20260818-visual-confirm-fast" in ids
    # Rejected craft must not be active.
    assert "tech-20260818-fake-metric-banner" not in ids
    assert "tech-20260818-pain-dream-stack" not in ids


def test_apply_marks_hook_overlay_craft():
    apps = scrollstop.apply_to_hook_overlay(
        has_hook_clip=True,
        hook_text="bassquake. stay for the switch",
        profile_id="hook-06-earthquake-bassquake",
        fiction_signal="visibly_stylised_or_impossible_scene",
    )
    by_id = {item.id: item for item in apps}
    assert by_id["tech-20260818-pattern-interrupt-open"].applied is True
    assert by_id["tech-20260818-subjective-stakes-line"].applied is True
    assert by_id["tech-20260818-prop-incongruity"].applied is True


def test_apply_skips_without_hook_clip():
    apps = scrollstop.apply_to_hook_overlay(
        has_hook_clip=False,
        hook_text="",
        profile_id="",
        fiction_signal="",
    )
    assert apps
    assert all(not item.applied for item in apps)
