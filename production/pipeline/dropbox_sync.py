"""Dropbox as the phone's file channel.

The verified delivery path (cloud artifact links in the pull request) works,
but it lives inside a Cursor session. Dropbox gives the creator a channel that
outlives the agent: drop a recording into a folder from the phone, and collect
the finished render from another folder — both inside the Dropbox app.

Folder contract, rooted at ``DROPBOX_BASE_FOLDER`` (default
``/spotify-mix-videos``):

- ``incoming/`` — the creator drops recordings here. A loose video file
  becomes one job; a subfolder becomes one job containing all of its files
  (the Spotify recording is picked by filename hint, then by size).
- ``imported/`` — where pulled uploads are moved, so nothing imports twice.
- ``renders/<video-id>/`` — where ``push`` uploads the preview, final and
  thumbnail, each with a shared link the creator can open on the phone.
- ``education/hooks-incoming/`` — TikTok / tutorial videos the creator
  supplies about scroll-stop hooks and retention. Pulled for analysis only
  (never committed to git); findings feed the produce-scroll-stop-hook skill.
- ``education/hooks-imported/`` — education videos after pull, so nothing
  is analysed twice.

Credentials come from the environment only (never git — ``SECURITY.md``):

- ``DROPBOX_REFRESH_TOKEN`` + ``DROPBOX_APP_KEY`` (+ optional
  ``DROPBOX_APP_SECRET``) — the long-lived setup; the module exchanges the
  refresh token for a short-lived access token per run; or
- ``DROPBOX_ACCESS_TOKEN`` — a short-lived token, fine for one session.

In a Cursor cloud agent these belong in Dashboard → Cloud Agents → Secrets.
Implemented over ``urllib`` deliberately: no new dependency for four HTTP
endpoints.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .jobspec import SPOTIFY_HINTS, VIDEO_SUFFIXES, write_job_template
from .paths import JOBS_APPROVED, JOBS_FAILED, JOBS_INCOMING, JOBS_PROCESSING, JOBS_REVIEW, REPO_ROOT, rel

API_BASE = "https://api.dropboxapi.com"
CONTENT_BASE = "https://content.dropboxapi.com"
DEFAULT_BASE_FOLDER = "/spotify-mix-videos"

# files/upload takes one call up to ~150 MB; recordings are tens of MB.
UPLOAD_LIMIT_BYTES = 140 * 1024 * 1024

_SLUG = re.compile(r"[^a-z0-9]+")


class DropboxError(RuntimeError):
    """Raised when the Dropbox API refuses or the channel is misconfigured."""


@dataclass
class DropboxConfig:
    access_token: str = ""
    refresh_token: str = ""
    app_key: str = ""
    app_secret: str = ""
    base_folder: str = DEFAULT_BASE_FOLDER

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "DropboxConfig | None":
        env = dict(os.environ if env is None else env)
        config = cls(
            access_token=env.get("DROPBOX_ACCESS_TOKEN", "").strip(),
            refresh_token=env.get("DROPBOX_REFRESH_TOKEN", "").strip(),
            app_key=env.get("DROPBOX_APP_KEY", "").strip(),
            app_secret=env.get("DROPBOX_APP_SECRET", "").strip(),
            base_folder=env.get("DROPBOX_BASE_FOLDER", DEFAULT_BASE_FOLDER).strip()
            or DEFAULT_BASE_FOLDER,
        )
        if not config.base_folder.startswith("/"):
            config.base_folder = "/" + config.base_folder
        config.base_folder = config.base_folder.rstrip("/")
        if config.access_token or (config.refresh_token and config.app_key):
            return config
        return None

    @property
    def missing(self) -> str:
        if self.refresh_token and not self.app_key:
            return "DROPBOX_REFRESH_TOKEN is set but DROPBOX_APP_KEY is missing"
        return (
            "set DROPBOX_REFRESH_TOKEN + DROPBOX_APP_KEY (durable) or "
            "DROPBOX_ACCESS_TOKEN (one session)"
        )


@dataclass
class PulledJob:
    job_id: str
    job_dir: str
    recording: str
    assets: list[str] = field(default_factory=list)
    dropbox_source: str = ""


@dataclass
class PullResult:
    created: list[PulledJob] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "created": [vars(job) for job in self.created],
            "skipped": self.skipped,
            "messages": self.messages,
        }


@dataclass
class PushResult:
    video_id: str
    uploaded: list[dict[str, str]] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "video_id": self.video_id,
            "uploaded": self.uploaded,
            "messages": self.messages,
        }


def slug_job_id(name: str) -> str:
    """A Dropbox filename or folder name, as a valid job id."""
    stem = Path(name).stem.lower()
    slug = _SLUG.sub("-", stem).strip("-") or "upload"
    if not slug.startswith("job-"):
        slug = f"job-{slug}"
    return slug[:64].rstrip("-.")


def job_exists(job_id: str) -> bool:
    """Whether a job id is already present in any lifecycle directory."""
    lifecycle = (JOBS_INCOMING, JOBS_PROCESSING, JOBS_REVIEW, JOBS_APPROVED, JOBS_FAILED)
    return any((directory / job_id).is_dir() for directory in lifecycle)


def choose_recording(files: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Pick the Spotify recording: filename hint first, then largest file."""
    videos = [
        entry for entry in files
        if Path(str(entry.get("name", ""))).suffix.lower() in VIDEO_SUFFIXES
    ]
    if not videos:
        return None
    for entry in videos:
        lowered = str(entry["name"]).lower()
        if any(hint in lowered for hint in SPOTIFY_HINTS):
            return entry
    return max(videos, key=lambda entry: int(entry.get("size", 0)))


class DropboxClient:
    def __init__(self, config: DropboxConfig):
        self.config = config
        self._token = config.access_token

    # -- transport ---------------------------------------------------------

    def _refresh_access_token(self) -> str:
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.config.refresh_token,
            "client_id": self.config.app_key,
        }
        if self.config.app_secret:
            payload["client_secret"] = self.config.app_secret
        request = urllib.request.Request(
            f"{API_BASE}/oauth2/token",
            data=urllib.parse.urlencode(payload).encode("ascii"),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")
            raise DropboxError(
                f"token refresh failed ({exc.code}): {detail}. Check "
                "DROPBOX_REFRESH_TOKEN / DROPBOX_APP_KEY / DROPBOX_APP_SECRET."
            ) from exc
        token = str(body.get("access_token", ""))
        if not token:
            raise DropboxError(f"token refresh returned no access_token: {body}")
        return token

    def token(self) -> str:
        if not self._token:
            if not self.config.refresh_token:
                raise DropboxError(self.config.missing)
            self._token = self._refresh_access_token()
        return self._token

    def _request(
        self,
        url: str,
        *,
        headers: dict[str, str],
        data: bytes | None,
        timeout: int,
    ) -> tuple[int, bytes, dict[str, str]]:
        request = urllib.request.Request(url, data=data, method="POST")
        for key, value in headers.items():
            request.add_header(key, value)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read(), dict(exc.headers or {})

    def api(self, endpoint: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call an RPC endpoint under api.dropboxapi.com/2/."""
        status, body, _ = self._request(
            f"{API_BASE}/2/{endpoint}",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload if payload is not None else None).encode("utf-8"),
            timeout=60,
        )
        if status >= 400:
            raise DropboxError(
                f"{endpoint} failed ({status}): {body.decode('utf-8', 'replace')}"
            )
        return json.loads(body.decode("utf-8")) if body.strip() else {}

    def api_allow(self, endpoint: str, payload: dict[str, Any],
                  tolerated: str) -> dict[str, Any] | None:
        """Like :meth:`api`, but a specific error tag returns None."""
        status, body, _ = self._request(
            f"{API_BASE}/2/{endpoint}",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload).encode("utf-8"),
            timeout=60,
        )
        text = body.decode("utf-8", "replace")
        if status >= 400:
            if tolerated in text:
                return None
            raise DropboxError(f"{endpoint} failed ({status}): {text}")
        return json.loads(text) if text.strip() else {}

    def download(self, dropbox_path: str, destination: Path) -> None:
        status, body, _ = self._request(
            f"{CONTENT_BASE}/2/files/download",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Dropbox-API-Arg": json.dumps({"path": dropbox_path}),
            },
            data=b"",
            timeout=600,
        )
        if status >= 400:
            raise DropboxError(
                f"download of {dropbox_path} failed ({status}): "
                f"{body.decode('utf-8', 'replace')}"
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(body)

    def upload(self, local: Path, dropbox_path: str) -> dict[str, Any]:
        size = local.stat().st_size
        if size > UPLOAD_LIMIT_BYTES:
            raise DropboxError(
                f"{local.name} is {size / 1_048_576:.0f} MB, above the single-call "
                "upload limit — a render this large is a sign the encode is wrong"
            )
        status, body, _ = self._request(
            f"{CONTENT_BASE}/2/files/upload",
            headers={
                "Authorization": f"Bearer {self.token()}",
                "Content-Type": "application/octet-stream",
                "Dropbox-API-Arg": json.dumps({
                    "path": dropbox_path, "mode": "overwrite", "mute": True,
                }),
            },
            data=local.read_bytes(),
            timeout=600,
        )
        if status >= 400:
            raise DropboxError(
                f"upload to {dropbox_path} failed ({status}): "
                f"{body.decode('utf-8', 'replace')}"
            )
        return json.loads(body.decode("utf-8"))

    # -- folder operations ---------------------------------------------------

    def list_folder(self, path: str) -> list[dict[str, Any]] | None:
        """Entries in a folder, or None when the folder does not exist."""
        result = self.api_allow(
            "files/list_folder", {"path": path}, tolerated="path/not_found"
        )
        if result is None:
            return None
        entries = list(result.get("entries") or [])
        while result.get("has_more"):
            result = self.api("files/list_folder/continue", {"cursor": result["cursor"]})
            entries.extend(result.get("entries") or [])
        return entries

    def ensure_folder(self, path: str) -> None:
        self.api_allow(
            "files/create_folder_v2", {"path": path, "autorename": False},
            tolerated="path/conflict",
        )

    def move(self, from_path: str, to_path: str) -> None:
        self.api("files/move_v2", {
            "from_path": from_path, "to_path": to_path, "autorename": True,
        })

    def shared_link(self, path: str) -> str:
        created = self.api_allow(
            "sharing/create_shared_link_with_settings", {"path": path},
            tolerated="shared_link_already_exists",
        )
        if created is not None:
            return str(created.get("url", ""))
        existing = self.api(
            "sharing/list_shared_links", {"path": path, "direct_only": True}
        )
        links = existing.get("links") or []
        return str(links[0]["url"]) if links else ""

    def account_display_name(self) -> str:
        account = self.api("users/get_current_account")
        return str((account.get("name") or {}).get("display_name", ""))


@dataclass
class EducationPull:
    downloaded: list[dict[str, str]] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    local_dir: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "downloaded": self.downloaded,
            "skipped": self.skipped,
            "messages": self.messages,
            "local_dir": self.local_dir,
        }


def status() -> dict[str, Any]:
    """Whether the Dropbox channel is configured and reachable."""
    config = DropboxConfig.from_env()
    if config is None:
        return {
            "configured": False,
            "reason": DropboxConfig().missing,
        }
    client = DropboxClient(config)
    try:
        name = client.account_display_name()
    except DropboxError as exc:
        return {"configured": True, "reachable": False, "reason": str(exc)}
    return {
        "configured": True,
        "reachable": True,
        "account": name,
        "base_folder": config.base_folder,
        "incoming": f"{config.base_folder}/incoming",
        "renders": f"{config.base_folder}/renders",
        "hooks_library": f"{config.base_folder}/hooks/library",
        "education_incoming": f"{config.base_folder}/education/hooks-incoming",
    }


def _connect() -> DropboxClient:
    config = DropboxConfig.from_env()
    if config is None:
        raise DropboxError(
            "Dropbox is not configured: " + DropboxConfig().missing
            + ". In a Cursor cloud agent, add these under Dashboard -> Cloud "
            "Agents -> Secrets."
        )
    return DropboxClient(config)


def pull() -> PullResult:
    """Import new recordings from ``<base>/incoming`` into job folders.

    The creator's originals are moved to ``<base>/imported/`` afterwards —
    within Dropbox, never deleted — so a second pull cannot double-import.
    """
    client = _connect()
    base = client.config.base_folder
    incoming = f"{base}/incoming"
    result = PullResult()

    entries = client.list_folder(incoming)
    if entries is None:
        for folder in (incoming, f"{base}/imported", f"{base}/renders"):
            client.ensure_folder(folder)
        result.messages.append(
            f"created the folder structure under {base} — drop a recording "
            f"into {incoming} from the Dropbox app and pull again"
        )
        return result

    client.ensure_folder(f"{base}/imported")

    for entry in entries:
        tag = str(entry.get(".tag", ""))
        name = str(entry.get("name", ""))
        source_path = str(entry.get("path_display") or entry.get("path_lower") or "")

        if tag == "file":
            if Path(name).suffix.lower() not in VIDEO_SUFFIXES:
                result.skipped.append(f"{name}: not a video file")
                continue
            files = [entry]
        elif tag == "folder":
            listed = client.list_folder(source_path) or []
            files = [item for item in listed if str(item.get(".tag")) == "file"]
            if not files:
                result.skipped.append(f"{name}/: empty folder")
                continue
        else:
            result.skipped.append(f"{name}: unsupported entry type {tag!r}")
            continue

        job_id = slug_job_id(name)
        if job_exists(job_id):
            result.skipped.append(
                f"{name}: job {job_id!r} already exists — rename the upload "
                "if this is a different mix"
            )
            continue

        recording = choose_recording(files)
        if recording is None:
            result.skipped.append(f"{name}: no video file among {len(files)} file(s)")
            continue

        job_dir = JOBS_INCOMING / job_id
        job_dir.mkdir(parents=True, exist_ok=True)
        assets: list[str] = []
        try:
            for item in files:
                item_name = str(item["name"])
                item_path = str(item.get("path_display") or item.get("path_lower"))
                client.download(item_path, job_dir / item_name)
                if item is not recording:
                    assets.append(item_name)
        except DropboxError:
            # A half-downloaded job folder would be picked up by `newest`;
            # remove it so the failed pull leaves no trace.
            shutil.rmtree(job_dir, ignore_errors=True)
            raise

        write_job_template(job_dir, job_id, str(recording["name"]))
        client.move(source_path, f"{base}/imported/{name}")

        result.created.append(PulledJob(
            job_id=job_id,
            job_dir=rel(job_dir),
            recording=str(recording["name"]),
            assets=assets,
            dropbox_source=source_path,
        ))

    if not entries:
        result.messages.append(
            f"{incoming} is empty — drop a recording there from the Dropbox app"
        )
    return result


def push(video_id: str, files: list[tuple[str, Path]]) -> PushResult:
    """Upload a render's files to ``<base>/renders/<video-id>/`` with links."""
    client = _connect()
    base = client.config.base_folder
    result = PushResult(video_id=video_id)

    if not files:
        raise DropboxError(f"no files to push for {video_id} — run the job first")

    client.ensure_folder(f"{base}/renders")
    target_folder = f"{base}/renders/{video_id}"
    client.ensure_folder(target_folder)

    for label, path in files:
        remote = f"{target_folder}/{path.name}"
        client.upload(path, remote)
        link = client.shared_link(remote)
        result.uploaded.append({
            "label": label,
            "source": rel(path),
            "dropbox_path": remote,
            "link": link,
        })

    result.messages.append(
        "links open in the Dropbox app or browser; the preview is the small "
        "one to check first"
    )
    return result


def ensure_tree() -> list[str]:
    """Create the full Dropbox folder contract if missing. Returns paths touched."""
    client = _connect()
    base = client.config.base_folder
    folders = [
        f"{base}/incoming",
        f"{base}/imported",
        f"{base}/renders",
        f"{base}/hooks",
        f"{base}/hooks/incoming",
        f"{base}/hooks/imported",
        f"{base}/hooks/library",
        f"{base}/education",
        f"{base}/education/hooks-incoming",
        f"{base}/education/hooks-imported",
    ]
    for folder in folders:
        client.ensure_folder(folder)
    return folders


def pull_education() -> EducationPull:
    """Download creator-supplied hook/retention education videos for analysis.

    Videos land in ``tmp/education/hooks/<slug>/`` locally (gitignored). Dropbox
    originals move to ``education/hooks-imported/``. Nothing is committed — only
    the later extraction notes and skill updates enter git.
    """
    client = _connect()
    base = client.config.base_folder
    incoming = f"{base}/education/hooks-incoming"
    result = EducationPull()
    local_root = REPO_ROOT / "tmp" / "education" / "hooks"
    local_root.mkdir(parents=True, exist_ok=True)
    result.local_dir = rel(local_root)

    entries = client.list_folder(incoming)
    if entries is None:
        ensure_tree()
        result.messages.append(
            f"created education folders — drop tutorial/hook videos into "
            f"{incoming} and pull-education again"
        )
        return result

    client.ensure_folder(f"{base}/education/hooks-imported")
    video_entries = [
        entry for entry in entries
        if str(entry.get(".tag")) == "file"
        and Path(str(entry.get("name", ""))).suffix.lower() in VIDEO_SUFFIXES
    ]
    for entry in entries:
        if entry not in video_entries and str(entry.get(".tag")) == "file":
            result.skipped.append(f"{entry.get('name')}: not a video file")

    if not video_entries:
        result.messages.append(
            f"{incoming} has no video files yet — paste TikTok screen recordings "
            "or exports of hook/retention tutorials there"
        )
        return result

    for entry in video_entries:
        name = str(entry["name"])
        source_path = str(entry.get("path_display") or entry.get("path_lower"))
        slug = slug_job_id(name).removeprefix("job-") or "edu"
        dest_dir = local_root / slug
        if dest_dir.exists() and any(dest_dir.iterdir()):
            result.skipped.append(f"{name}: already pulled to {rel(dest_dir)}")
            client.move(source_path, f"{base}/education/hooks-imported/{name}")
            continue
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / name
        client.download(source_path, dest)
        client.move(source_path, f"{base}/education/hooks-imported/{name}")
        result.downloaded.append({
            "name": name,
            "local_path": rel(dest),
            "slug": slug,
        })

    result.messages.append(
        f"downloaded {len(result.downloaded)} education video(s) under "
        f"{result.local_dir} — analyse next; do not commit the mp4s"
    )
    return result
