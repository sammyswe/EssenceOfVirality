# Keeping the Dropbox pipeline "online"

This repository does **not** run a 24/7 daemon inside Cursor. A cloud agent is a
session: it starts when you (or an automation) start it, does work, and stops.
Dropbox is the always-available **mailbox**; the agent is the worker that checks
the mailbox.

## What you already have (near-online)

1. Drop mixes (and optional hook clips) into `/spotify-mix-videos/incoming/`.
2. Open Cursor (phone is fine) and start a cloud agent on this repo with one
   line: `Process Dropbox uploads` (runs `./process-job dropbox pull --run`).
3. Collect the finished video from `/spotify-mix-videos/renders/<video-id>/`
   or the printed share links.

Secrets (`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, `DROPBOX_REFRESH_TOKEN`) must
be saved in Cloud Agent Secrets so every new run can authenticate. You do not
need `DROPBOX_BASE_FOLDER` unless you want a non-default root.

This is the lowest-friction path and matches how the tools are built today.

## Truly unattended options

Pick one when quality is good enough that you want zero chat:

### A — Scheduled Cursor automation (if your plan supports it)

Create a Cursor Automation that starts this repo's cloud agent on a schedule
(e.g. every hour) with a fixed prompt:

> Run `./process-job dropbox pull --run`. If nothing was imported, say so and
> stop. If jobs ran, list the Dropbox render links.

Then you only use Dropbox; the automation is the worker. Confirm scheduling in
the Cursor dashboard for your account — capabilities vary by plan.

### B — Small always-on machine + cron

On a VPS or always-on Mac mini you control:

1. Clone the repo, install dependencies, put the same Dropbox env vars in a
   local `.env` (never commit it).
2. Cron every N minutes:

```bash
cd /path/to/EssenceOfVirality && set -a && source .env && set +a \
  && ./process-job dropbox pull --run >> /var/log/mix-pipeline.log 2>&1
```

Same mailbox, worker always polling. You still review/post manually unless you
add a later posting integration (out of scope here).

### C — Stay on-demand

Keep using the phone agent. Two posts a day do not need a daemon; they need a
reliable `pull --run` and Dropbox renders.

## Recommendation

Stay on **near-online (A/C)** until the render quality and hook profiles are
stable. Add a scheduled automation or cron only when you are tired of opening
Cursor to trigger the same command.
