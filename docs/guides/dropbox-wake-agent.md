# Wake a cloud agent from Dropbox

You want: paste a mix into Dropbox → a Cursor **cloud agent** starts → render
lands back in Dropbox — without opening Cursor yourself.

Cursor can wake agents via [Automations](https://cursor.com/docs/cloud-agent/automations)
(webhook or schedule). Dropbox can notify on file changes. Those two do **not**
plug together directly: Cursor’s webhook requires an
`Authorization: Bearer …` header, and Dropbox webhooks cannot set custom
headers. You need a one-line **relay** in the middle (or skip Dropbox wakeups
and use a schedule).

```
Dropbox upload
    │
    ▼
Dropbox webhook  ──POST (no auth header)──►  tiny relay
                                               │
                                               ▼
                                    Cursor Automation webhook
                                    (Bearer token added here)
                                               │
                                               ▼
                                    Cloud agent: dropbox pull --run
                                               │
                                               ▼
                                    /spotify-mix-videos/renders/…
```

## Branch (required until PR merges)

`./process-job dropbox …` lives on
`cursor/copy-bank-dropbox-cf50` (PR #15), **not** on `main` yet.

Point every Dropbox-worker Automation at branch **`cursor/copy-bank-dropbox-cf50`**.
After that PR merges, switch the Automation to `main`.

## Option A — Scheduled automation (simplest, no relay)

Good enough for two posts a day. The agent polls Dropbox on a timer.

1. Open [cursor.com/automations](https://cursor.com/automations) → New.
2. Trigger: **Schedule** (e.g. every 15 minutes).
3. Repository: this repo (`EssenceOfVirality`), branch
   **`cursor/copy-bank-dropbox-cf50`** (see above).
4. Prompt (paste exactly):

```text
You are the Dropbox mix worker. Run:

./process-job dropbox pull --run

If nothing was imported, reply with one line that incoming was empty and stop.
If jobs ran, list each video id and its Dropbox render links.
Do not merge PRs. Do not post to TikTok.
```

5. Ensure Cloud Agent Secrets include `DROPBOX_APP_KEY`,
   `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`.
6. Save and enable.

You never open the agent; you only use Dropbox. Worst case: up to one schedule
interval of delay after upload.

## Option B — Dropbox wake → relay → Cursor (true “on drop”)

### 1. Create the Cursor automation (webhook)

Same as Option A, but trigger = **Webhook** (you can also keep a slow schedule
as backup). Save once so Cursor shows:

- Webhook URL (looks like `https://api2.cursor.sh/automations/webhook/…`)
- API key (`crsr_…`) — use **Generate auth header**

Store the API key as a secret on the relay, never in git.

Automation prompt: same as Option A.

### 2. Deploy the relay

A ready Cloudflare Worker lives in
[`tools/dropbox-cursor-relay/`](../../tools/dropbox-cursor-relay/). It:

1. Answers Dropbox’s one-time `?challenge=` verification.
2. On Dropbox `POST`, verifies `X-Dropbox-Signature`.
3. Forwards a POST to your Cursor webhook with the Bearer header.

Deploy (Cloudflare account free tier is enough):

```bash
cd tools/dropbox-cursor-relay
npx wrangler secret put CURSOR_WEBHOOK_URL    # paste the automation URL
npx wrangler secret put CURSOR_API_KEY        # paste crsr_…
npx wrangler secret put DROPBOX_APP_SECRET    # your Dropbox app secret
npx wrangler deploy
```

Note the worker HTTPS URL, e.g. `https://dropbox-cursor-relay.….workers.dev`.

### 3. Point Dropbox at the relay

In the [Dropbox App Console](https://www.dropbox.com/developers/apps) for the
same app you already use:

1. Webhooks → add the worker URL.
2. Dropbox sends a GET with `challenge` — the worker echoes it; status becomes
   enabled.

### 4. Test

Drop a small video into `/spotify-mix-videos/incoming/`. Within about a minute
you should see a new cloud agent run on
[cursor.com/agents](https://cursor.com/agents) and, if the job succeeds, a
folder under `/spotify-mix-videos/renders/`.

## What this still will not do

- It will not post to TikTok (posting stays manual).
- It will not skip quality gates or invent lyrics.
- Dropbox’s webhook only says “something changed”; the agent still runs
  `dropbox pull`, which is what finds the new files.

## Recommendation

Start with **Option A** (15‑minute schedule) — zero extra infra. Move to
**Option B** when the delay bothers you.

## Cloud-agent verification (2026-08-18)

Checked from a cloud agent with your secrets loaded:

| Check | Result |
|-------|--------|
| `DROPBOX_APP_KEY` / `SECRET` / `REFRESH_TOKEN` | Present |
| `./process-job dropbox status` | Connected as Samuel Elliott’s |
| `./process-job dropbox ensure` | Folder tree OK |
| `./process-job status` | ffmpeg available; formats include `hook-overlay` |
| `/spotify-mix-videos/incoming` | Empty (ready for a test drop) |
| Automations branch | Creator set to `cursor/copy-bank-dropbox-cf50` |

**Smoke test (optional):** drop any short video into
`/spotify-mix-videos/incoming/`, then watch
[cursor.com/agents](https://cursor.com/agents) for a new run (schedule: within
one interval; webhook: ~1 minute). Renders land under
`/spotify-mix-videos/renders/`. If the agent says incoming was empty, the
wake worked but Dropbox had not synced yet — wait and re-check.

Wake environment setup is complete without that smoke test: secrets, mailbox,
pipeline, Automations + PR branch are in place. Run the drop whenever you want
to confirm end-to-end.
