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
