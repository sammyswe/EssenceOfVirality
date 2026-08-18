"""Tests for the copy testing bank and the Dropbox channel's offline logic."""

import sys
import textwrap
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from production.pipeline import copybank, dropbox_sync  # noqa: E402
from production.pipeline.posting import _render_copy_template  # noqa: E402


# ---------------------------------------------------------------- the real bank

def test_shipped_bank_is_valid():
    bank = copybank.load_bank()
    for section in copybank.SECTIONS:
        for entry in bank.get(section) or []:
            assert entry.get("id"), f"entry without id in {section}"
            assert entry.get("text") or entry.get("template"), entry["id"]


def test_shipped_bank_ids_are_unique():
    bank = copybank.load_bank()
    ids = [
        str(entry["id"])
        for section in copybank.SECTIONS
        for entry in bank.get(section) or []
    ]
    assert len(ids) == len(set(ids))


def test_drafts_are_not_active():
    for section in copybank.SECTIONS:
        for entry in copybank.active(section):
            assert entry["status"] in {"testing", "proven"}


def test_onscreen_sections_carry_no_emoji():
    """Hooks and CTAs render through drawtext, which cannot draw colour emoji."""
    for section in ("hooks", "ctas"):
        for entry in copybank.entries(section):
            text = str(entry.get("text", ""))
            assert all(ord(char) < 0x2600 for char in text), (
                f"{entry['id']} contains a character drawtext cannot render: {text!r}"
            )


# ---------------------------------------------------------------- lifecycle

def _tiny_bank(tmp_path: Path) -> Path:
    path = tmp_path / "copy-bank.yaml"
    path.write_text(textwrap.dedent("""
        hooks:
          - {id: hook-x, text: "wait for it", kind: anticipation, status: draft}
        ctas:
          - {id: cta-x, text: "rate it", intent: comment_rate, status: testing}
        captions: []
        pinned_comments: []
    """), encoding="utf-8")
    return path


def test_set_status_roundtrip(tmp_path):
    path = _tiny_bank(tmp_path)
    assert copybank.active("hooks", path) == []

    entry = copybank.set_status("hook-x", "testing", note="approved in grilling", path=path)
    assert entry["status"] == "testing"
    assert "approved in grilling" in entry["notes"]

    reloaded = copybank.active("hooks", path)
    assert [e["id"] for e in reloaded] == ["hook-x"]


def test_set_status_rejects_unknown_entry_and_status(tmp_path):
    path = _tiny_bank(tmp_path)
    with pytest.raises(copybank.CopyBankError):
        copybank.set_status("hook-missing", "testing", path=path)
    with pytest.raises(copybank.CopyBankError):
        copybank.set_status("hook-x", "published", path=path)


def test_find_by_text(tmp_path):
    path = _tiny_bank(tmp_path)
    section, entry = copybank.find_by_text("rate it", path)
    assert (section, entry["id"]) == ("ctas", "cta-x")
    assert copybank.find_by_text("never in the bank", path) is None


# ---------------------------------------------------------------- caption fill

def test_caption_template_fills_pairing():
    assert (
        _render_copy_template("{pairing} — made in Spotify.", "A into B")
        == "A into B — made in Spotify."
    )


def test_caption_template_without_pairing_is_skipped():
    assert _render_copy_template("{pairing} — made in Spotify.", "") is None


def test_caption_template_with_unknown_placeholder_is_skipped():
    assert _render_copy_template("day {day_number} of blends", "A into B") is None


# ---------------------------------------------------------------- dropbox logic

def test_slug_job_id():
    assert dropbox_sync.slug_job_id("Stuss 2.MOV") == "job-stuss-2"
    assert dropbox_sync.slug_job_id("job-already-good") == "job-already-good"
    assert dropbox_sync.slug_job_id("___") == "job-upload"


def test_choose_recording_prefers_filename_hint():
    files = [
        {".tag": "file", "name": "hook-clip.mp4", "size": 900},
        {".tag": "file", "name": "spotify-capture.mov", "size": 100},
    ]
    chosen = dropbox_sync.choose_recording(files)
    assert chosen["name"] == "spotify-capture.mov"


def test_choose_recording_falls_back_to_largest():
    files = [
        {".tag": "file", "name": "a.mp4", "size": 100},
        {".tag": "file", "name": "b.mp4", "size": 900},
        {".tag": "file", "name": "notes.txt", "size": 5000},
    ]
    assert dropbox_sync.choose_recording(files)["name"] == "b.mp4"
    assert dropbox_sync.choose_recording([{".tag": "file", "name": "x.txt"}]) is None


def test_config_from_env():
    assert dropbox_sync.DropboxConfig.from_env({}) is None
    config = dropbox_sync.DropboxConfig.from_env({
        "DROPBOX_REFRESH_TOKEN": "r", "DROPBOX_APP_KEY": "k",
        "DROPBOX_BASE_FOLDER": "mixes/",
    })
    assert config is not None
    assert config.base_folder == "/mixes"
    # A refresh token without an app key cannot authenticate.
    assert dropbox_sync.DropboxConfig.from_env({"DROPBOX_REFRESH_TOKEN": "r"}) is None
    # An access token alone is enough for one session.
    assert dropbox_sync.DropboxConfig.from_env({"DROPBOX_ACCESS_TOKEN": "t"}) is not None


# ---------------------------------------------------------------- grilling rulings

def test_grilling_retirements_are_enforced():
    retired = {
        entry["id"]
        for section in copybank.SECTIONS
        for entry in copybank.entries(section)
        if entry["status"] == "retired"
    }
    assert {
        "hook-003", "hook-013", "cta-010", "cta-011", "cap-005",
    } <= retired


def test_grilling_approvals_are_active():
    active_ids = {
        entry["id"]
        for section in copybank.SECTIONS
        for entry in copybank.active(section)
    }
    for entry_id in (
        "hook-006", "hook-009", "hook-012",
        "cta-006", "cta-007", "cta-008", "cta-009", "cta-012", "cta-013",
        "cap-003", "cap-007", "pin-003",
    ):
        assert entry_id in active_ids, entry_id
    assert copybank.find("cta-012")[1]["text"] == "follow for the next mix"


def test_false_mixes_itself_wording_is_gone_from_active_pool():
    for section in ("hooks", "captions"):
        for entry in copybank.active(section):
            blob = str(entry.get("text") or entry.get("template") or "").lower()
            assert "mixes itself" not in blob
            assert "blends itself" not in blob


def test_intent_weights_prefer_comment_over_follow():
    weights = copybank.intent_weights()
    assert weights["comment_rate"] > weights["follow"]
    assert weights["save"] > weights["follow_milestone"]


# ---------------------------------------------------------------- hook profiles

def test_template_profile_is_ignored():
    from production.pipeline import hookprofiles
    assert all(not p.id.startswith("_") for p in hookprofiles.load_all())


def test_hook_profile_requires_three_captions_and_description(tmp_path):
    from production.pipeline import hookprofiles

    path = tmp_path / "hook-01.yaml"
    path.write_text(textwrap.dedent("""
        id: hook-01
        status: testing
        asset_stems: [hook-01]
        description: ""
        captions:
          - {id: a, template: "one {pairing}"}
    """), encoding="utf-8")
    with pytest.raises(hookprofiles.HookProfileError):
        hookprofiles.load_profile(path)

    path.write_text(textwrap.dedent("""
        id: hook-01
        status: testing
        asset_stems: [hook-01]
        description: "DJ on decks in a Spotify-green room."
        captions:
          - {id: a, template: "one {pairing}"}
          - {id: b, template: "two {pairing}"}
          - {id: c, template: "three {pairing}"}
    """), encoding="utf-8")
    profile = hookprofiles.load_profile(path)
    assert len(profile.captions) == 3
    assert profile.active


def test_hook_profile_matches_stem(tmp_path):
    from production.pipeline import hookprofiles

    path = tmp_path / "hook-01-decks.yaml"
    path.write_text(textwrap.dedent("""
        id: hook-01-decks
        status: testing
        asset_stems: [hook-01-decks-spotify-green]
        description: "Recognisable DJ on decks."
        overlay_hook_ids: [hook-006]
        cta_ids: [cta-006]
        captions:
          - {id: a, template: "cap a {pairing}", status: testing}
          - {id: b, template: "cap b {pairing}", status: testing}
          - {id: c, template: "cap c {pairing}", status: testing}
    """), encoding="utf-8")
    matched = hookprofiles.match_for_asset(
        filename="hook-01-decks-spotify-green.mp4",
        directory=tmp_path,
    )
    assert matched is not None
    assert matched.id == "hook-01-decks"
    assert hookprofiles.match_for_asset(
        filename="other-clip.mp4", directory=tmp_path
    ) is None


def test_hook_profile_inline_ctas_and_overlay_texts(tmp_path):
    from production.pipeline import hookprofiles

    path = tmp_path / "hook-06-earthquake-bassquake.yaml"
    path.write_text(textwrap.dedent("""
        id: hook-06-earthquake-bassquake
        status: testing
        asset_stems: [hook-06-earthquake-bassquake]
        description: "Glasses vibrate from the bassquake."
        overlay_texts:
          - "this bass just caused an earthquake"
          - "watch the glasses — the room is shaking"
          - "bassquake. stay for the switch"
        ctas:
          - {id: a, text: "rate the shake out of 10", intent: comment_rate}
          - {id: b, text: "send this to whoever needs their speaker to move", intent: share}
          - {id: c, text: "save this for when the room needs a bassquake", intent: save}
        captions:
          - {id: a, template: "one {pairing}"}
          - {id: b, template: "two {pairing}"}
          - {id: c, template: "three {pairing}"}
    """), encoding="utf-8")
    profile = hookprofiles.load_profile(path)
    assert len(profile.overlay_texts) == 3
    assert len(profile.cta_texts) == 3
    assert profile.cta_texts[0].intent == "comment_rate"
