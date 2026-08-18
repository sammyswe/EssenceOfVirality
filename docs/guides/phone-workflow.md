# Working from a phone

The intended loop: record a mix, hand it to a cloud agent, get a video back,
say what is wrong with it, get a better one. This page documents what has been
verified in the actual Cursor cloud agent environment, and what has not.

## The loop

1. Record the Spotify mix on your phone.
2. Open Cursor, start a cloud agent on this repository.
3. Attach the recording and any supporting clip, and say what you want.
4. The agent runs the pipeline and stages the render.
5. Tap the artifact link in the pull request to download it.
6. Reply with feedback in plain language.
7. The agent re-renders and stages the new version.
8. When a preference is worth keeping, approve it — the next job inherits it.

What you type in step 3 can be as loose as:

> Process the newest Spotify mix job using the best current editing strategy.

and in step 6:

> Revise job-001: the opening is too slow, make the waveform larger, and remove
> the final zoom.

The agent maps those onto `./process-job` and `./process-job revise`. You never
need to type a command yourself, though the commands in
[`new-job.md`](new-job.md) work if you prefer them.

## Getting the video back — what was verified

This is the part worth being precise about, because it is the step most likely
to quietly not work.

**Verified.** The cloud agent has a writable artifact directory at
`/opt/cursor/artifacts`. `./process-job deliver <video-id>` copies the preview,
the final MP4 and the thumbnail into it. When those paths are referenced from a
pull request body, the agent uploads the files and rewrites each path to a link
of the form `cursor.com/agents/<agent-id>/artifacts?path=…`. This was confirmed
by staging a real render and reading the resulting pull request body back.

**What that means in practice.** You get a tappable link, not an inline player.
Tapping it downloads the file through Cursor, so you need to be signed in on the
phone. A 19-second render is a few megabytes, which is fine on mobile data.

**Not verified.** Whether the artifact links survive after the agent run ends,
and for how long. Treat them as available while the agent is live and download
promptly rather than assuming they will still resolve. If you need a render to
outlive the session, use a fallback below.

**Deliberately not used.** Renders are not committed to git. Media never enters
history (`SECURITY.md`), and a render is reproducible from the job folder
anyway, so committing it would trade repository size for nothing.

## Ask for the preview first

`deliver` stages the preview before the final, and that ordering is the point.
The preview is roughly a fifth of the size and is enough to judge pacing, hook
and whether the Spotify interface reads. Download the final only when you are
close to posting.

| File | Typical size | Use |
| --- | --- | --- |
| `<id>-preview.mp4` | ~0.6 MB | reviewing on mobile data |
| `<id>.mp4` | ~3–4 MB | the file you post |
| `<id>-thumbnail.jpg` | ~55 KB | checking the cover frame |

## The Dropbox loop

The artifact links above live inside a Cursor session. Dropbox gives the loop
a channel that outlives the agent and works entirely from the Dropbox app on
the phone. Once configured, the whole exchange is two folders:

1. **Upload**: drop the screen recording (and the hook clip, together in one
   subfolder if both belong to one job) into `<base>/incoming/` from the
   Dropbox app. The base folder is `/spotify-mix-videos` unless
   `DROPBOX_BASE_FOLDER` says otherwise.
2. **Wake** (pick one):
   - **Unattended:** a Cursor Automation (schedule or Dropbox webhook) starts
     a cloud agent that runs `./process-job dropbox pull --run`. Setup:
     [`dropbox-wake-agent.md`](dropbox-wake-agent.md). You do not open Cursor.
   - **Manual:** open any cloud agent and say “Process Dropbox uploads.”
3. **Download**: open the shared link (or the folder in the Dropbox app) and
   save the final to the camera roll for posting. Renders land in
   `<base>/renders/<video-id>/`.

Imported uploads are moved to `<base>/imported/` inside Dropbox — never
deleted — so a second pull cannot import the same mix twice. A loose video
file becomes one job named after the file; a subfolder becomes one job
containing all of its files, with the Spotify recording picked by filename
hint (`spotify`, `mix`, `screen-recording`) and otherwise by size, so name
the capture accordingly when uploading a hook clip alongside it.

### One-time setup

Full walkthrough: [`dropbox-setup.md`](dropbox-setup.md). Short version:
create a Dropbox app, obtain a refresh token once, then store
`DROPBOX_APP_KEY`, `DROPBOX_APP_SECRET`, and `DROPBOX_REFRESH_TOKEN` as Cloud
Agent secrets in the Cursor Dashboard. Optional: `DROPBOX_BASE_FOLDER`
(defaults to `/spotify-mix-videos`). Secrets are injected into new cloud agent
runs and never enter git. `./process-job dropbox status` confirms the channel
is reachable; on first pull the folder structure is created automatically.

## Fallbacks

If the artifact link does not work for you, in rough order of effort:

1. **Ask the agent to re-stage and re-link.** Cheapest fix and usually enough.
2. **Run it locally instead.** The pipeline is deterministic; the same job
   folder gives the same render on a laptop. See [`setup.md`](setup.md).
3. **Push the render to Dropbox** with `./process-job dropbox push <video-id>`
   — see [the Dropbox loop](#the-dropbox-loop) above. This is the fallback
   that also survives the agent session ending.

A GitHub release asset would also work, but it means a binary in a public
repository, which the content-handling policy rules out for unpublished media.

## Getting the recording in

Attach the file to the agent conversation and ask for a job to be made from it.
The agent copies it into a job folder with `./process-job new`, which never
moves or renames your original.

Upload size limits are set by the Cursor client rather than by this repository,
and have not been probed. A vertical phone capture of 30–60 seconds is a few
tens of megabytes and has not been a problem. If a long recording is refused,
trim it around the transition before uploading — the pipeline only needs a
short lead-in and about fifteen seconds after the transition.

## Recording guidelines

The pipeline reads geometry from whatever you give it, but these make its job
easier and the result better:

- Record in **portrait**, full screen, with the Spotify now-playing view
  showing both song labels and the waveform.
- Keep the **transition roughly 5–10 seconds in**. A very long lead-in is
  trimmed away; a transition in the first second leaves no room for a hook.
- Include **about fifteen seconds after the transition** so there is a payoff
  to sit in.
- Avoid notification banners and the pull-down shade over the interface.
- Do not screen-record with a **microphone** enabled. The mix must be the only
  audio; the pipeline will reject a second source.

`./process-job inspect <job>` reports what it found — geometry, crop profile,
transition time, tempo, loudness — without rendering anything. It is the fastest
way to check a recording is usable.

## What the agent will and will not do

It will pick a format, write a hook and a CTA, render, run 25 quality checks,
write a posting package, and re-render on feedback.

It will not post to TikTok, generate AI clips, or invent facts about an artist.
Posting is manual. AI clips are supplied by you — the pipeline writes Higgsfield
prompts but does not call anything. Any factual claim in a caption requires a
research note with a URL and a date, or the copy will not make it.
