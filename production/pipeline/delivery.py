"""Getting a finished render onto the creator's phone.

The pipeline runs in a container the creator never sees. A path under
``outputs/`` is not a delivery, so this module stages renders where the cloud
agent can turn them into links.

The mechanism that has actually been verified in this environment is the cloud
agent's artifact directory: a file placed there and referenced from a pull
request body is uploaded, and the path is rewritten to a link into the agent's
artifact viewer, which opens on a phone for anyone signed in to Cursor. It is a
link rather than an inline player, so the creator taps through to download.
When that directory does not exist — a local checkout, a different runner — the
staging step reports that plainly instead of pretending it worked.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from .paths import OUTPUTS_FINAL, OUTPUTS_PACKAGES, OUTPUTS_PREVIEWS, rel

# Where the Cursor cloud agent looks for files to publish alongside a PR.
CLOUD_ARTIFACT_DIR = Path("/opt/cursor/artifacts")

# Renders are a few megabytes; anything much larger is a sign something is wrong
# with the encode rather than with the video.
SIZE_WARNING_BYTES = 50 * 1024 * 1024


@dataclass
class Delivery:
    """What was staged for the creator, and where it can be reached."""

    video_id: str
    destination: Path | None
    staged: list[dict[str, str]] = field(default_factory=list)
    available: bool = False
    reason: str = ""
    warnings: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "video_id": self.video_id,
            "destination": str(self.destination) if self.destination else None,
            "staged": self.staged,
            "available": self.available,
            "reason": self.reason,
            "warnings": self.warnings,
        }


def artifact_dir() -> Path | None:
    """The cloud agent's artifact directory, or None when not running in one."""
    override = os.environ.get("CURSOR_ARTIFACT_DIR")
    candidate = Path(override) if override else CLOUD_ARTIFACT_DIR
    if not candidate.is_dir():
        return None
    if not os.access(candidate, os.W_OK):
        return None
    return candidate


def _render_paths(video_id: str) -> list[tuple[str, Path]]:
    """The files worth putting in front of the creator, largest value first."""
    candidates = [
        ("preview", OUTPUTS_PREVIEWS / f"{video_id}-preview.mp4"),
        ("final", OUTPUTS_FINAL / f"{video_id}.mp4"),
        ("thumbnail", OUTPUTS_PACKAGES / f"{video_id}-thumbnail.jpg"),
    ]
    return [(label, path) for label, path in candidates if path.is_file()]


def stage(video_id: str) -> Delivery:
    """Copy a render's viewable files into the cloud agent's artifact directory.

    The preview comes first deliberately: it is a fraction of the size and is
    what a creator reviewing on a phone connection actually wants.
    """
    delivery = Delivery(video_id=video_id, destination=None)

    files = _render_paths(video_id)
    if not files:
        delivery.reason = (
            f"no render found for {video_id}. Expected "
            f"{rel(OUTPUTS_FINAL / f'{video_id}.mp4')} — run the job first."
        )
        return delivery

    destination = artifact_dir()
    if destination is None:
        delivery.reason = (
            f"{CLOUD_ARTIFACT_DIR} is not present or not writable, so there is no "
            "cloud artifact channel here. The files exist and can be fetched with "
            "git, scp or the editor's own download."
        )
        delivery.staged = [
            {"label": label, "source": rel(path), "published_path": ""}
            for label, path in files
        ]
        return delivery

    target_dir = destination / "assets"
    target_dir.mkdir(parents=True, exist_ok=True)

    for label, path in files:
        published = target_dir / path.name
        shutil.copy2(path, published)
        size = published.stat().st_size
        if size > SIZE_WARNING_BYTES:
            delivery.warnings.append(
                f"{path.name} is {size / 1_048_576:.0f} MB, which is large for a "
                f"{label} — check the render preset before sending it to a phone"
            )
        delivery.staged.append({
            "label": label,
            "source": rel(path),
            "published_path": str(published),
        })

    delivery.destination = target_dir
    delivery.available = True
    return delivery


def markdown_embed(delivery: Delivery) -> str:
    """Markdown referencing the staged files, for a pull request body.

    The tag form is what triggers the upload. When the pull request is written,
    the cloud agent replaces each tag with a link into its artifact viewer, so
    what the creator sees is a tappable download rather than an inline player.
    """
    if not delivery.available:
        return ""
    lines: list[str] = []
    for entry in delivery.staged:
        path = entry["published_path"]
        if path.endswith((".mp4", ".mov")):
            lines.append(f'<video src="{path}"></video>')
        else:
            lines.append(f'<img alt="{entry["label"]}" src="{path}" />')
    return "\n".join(lines)
