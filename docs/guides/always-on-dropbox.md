# Keeping the Dropbox pipeline "online"

Dropbox is the always-available **mailbox**. A Cursor **cloud agent** is the
worker that checks it. Agents do not stay running forever — something must
**wake** one when you upload.

You do **not** need to sit in the agent chat. Create a Cursor Automation once;
after that, Dropbox (or a timer) is enough.

Full wake setup: [`dropbox-wake-agent.md`](dropbox-wake-agent.md).

## What you want (unattended)

```
Phone → Dropbox /spotify-mix-videos/incoming/
              │
              ▼
     Cursor Automation wakes a cloud agent
              │
              ▼
     ./process-job dropbox pull --run
              │
              ▼
     Dropbox /spotify-mix-videos/renders/<video-id>/
```

Two ways to wake the agent:

| Path | Delay | Extra infra |
|------|--------|-------------|
| **A — Scheduled automation** | Up to the schedule interval (e.g. 15 min) | None |
| **B — Dropbox webhook → relay → Cursor** | ~1 minute after upload | Cloudflare Worker |

Start with **A**. Move to **B** only if the wait bothers you.

Secrets (`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`) must
already be in Cloud Agent Secrets so every automation-spawned run can talk to
Dropbox.

## Near-online (manual wake)

If you skip Automations for now: drop files in Dropbox, then start any cloud
agent with `Process Dropbox uploads`. Same mailbox; you are the wake button.

## What this still will not do

- Post to TikTok (stays manual).
- Run 24/7 inside one chat session — Automations start **new** runs when needed.
