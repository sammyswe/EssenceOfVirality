# Making a new job

A job is a folder with your media and a `job.yaml`. Everything the pipeline
needs to make one video lives in it, and nothing outside it is modified.

## The short version

```bash
./process-job new job-003 --recording ~/Downloads/mix.mp4
./process-job jobs/incoming/job-003
```

The first command makes the folder, copies the recording in and writes a
starter `job.yaml`. The second runs the pipeline. If the render passes its
quality checks, the folder moves to `jobs/review/` and you have a video.

You can add supporting clips at the same time:

```bash
./process-job new job-003 \
  --recording ~/Downloads/mix.mp4 \
  --asset ~/Downloads/hook.mp4
```

## What a job folder looks like

```
jobs/incoming/job-003/
├── spotify-screen-recording.mp4   required
├── hook-clip.mp4                  optional
├── job.yaml                       required
└── notes.txt                      optional, free text
```

Only the recording and `job.yaml` are required. A job with nothing but a
Spotify capture is a completely normal job and produces a clean showcase or
curiosity edit.

## job.yaml

The generated template:

```yaml
job_id: job-003
spotify_recording: spotify-screen-recording.mp4
additional_assets: []
tracks:
  first: {title: "", artist: ""}
  second: {title: "", artist: ""}
transition:
  seconds: null
creative_direction:
  preferred_format: auto
  mood: ""
  must_include: []
  avoid: []
  notes: ""
render:
  target_platform: tiktok
  aspect_ratio: "9:16"
  minimum_duration_seconds: 15
  maximum_duration_seconds: 45
research:
  enabled: false
outputs:
  preview: true
  final: true
  posting_package: true
  quality_report: true
```

### The fields that actually change the output

**`tracks`** is the highest-value thing you can fill in. Track titles and
artists are what let the copywriter name the songs in the hook and caption, and
the `genre` fields decide whether the unexpected-combination format is even
allowed to run — that hook claims two songs clash, so it is refused unless the
genres genuinely differ.

```yaml
tracks:
  first:  {title: Night Drive, artist: Lowbeam, genre: synthwave}
  second: {title: Paper Lanterns, artist: Ashra Kite, genre: afrobeats}
```

**`creative_direction.preferred_format`** is `auto` by default, which scores all
nine families against your assets and preferences and explains why the losers
lost. Name one to force it:

```bash
./process-job formats     # see the nine, and what each needs
```

**`creative_direction.mood`** nudges the choice — `funny` favours comedy-hook
and reaction; leaving it blank favours the clean families.

**`transition.seconds`** overrides automatic detection. Leave it `null` unless
the detector gets it wrong; `./process-job inspect` tells you what it found and
how confident it is.

**`additional_assets`** takes either bare filenames or entries with a role,
which is how the renderer knows what a clip is for:

```yaml
additional_assets:
  - path: hook-clip.mp4
    role: hook          # hook | reaction | background | supporting
    label: dog reaction
```

**`research.enabled`** only controls whether existing notes are consulted. It
never fetches anything. Notes are added deliberately:

```bash
./process-job research add \
  --subject "Lowbeam" --kind release \
  --summary "New EP announced" \
  --url https://example.com/article --published 2026-08-01
```

No note, no factual claim in the copy. That is a hard rule, not a default.

### Overriding configuration for one job

Anything in `production/config/defaults.yaml` can be overridden per job, but it
has to go under `config_overrides` — settings placed at the top level are
ignored, and the pipeline warns when it sees that mistake:

```yaml
config_overrides:
  layout:
    split_spotify_fraction: 0.70
  duration:
    post_transition_seconds: 12
```

## Check before you render

```bash
./process-job inspect job-003
```

```
  job            job-003
  recording      jobs/incoming/job-003/spotify-screen-recording.mp4
  geometry       1080x1920 (0.562), 31.00s, 30.00 fps
  crop profile   vertical_full — source ratio 0.562 within [0.5, 0.6]
  transition     14.20s (spectral_flux_novelty, high confidence)
                 alternatives: 12.60s, 15.80s
  tempo          99.4 BPM (medium confidence)
  loudness       -15.73 LUFS, peak -10.19 dBTP — integrated loudness -15.73 LUFS
                 is 1.73 dB from the -14.0 LUFS target
```

This runs no encode and takes a second or two. If the transition time is wrong
or the crop profile looks off, fix it in `job.yaml` before spending a render on
it.

## Running

```bash
./process-job job-003                    # by id
./process-job jobs/incoming/job-003      # by path
./process-job newest                     # most recently added
```

Useful flags:

| Flag | Effect |
| --- | --- |
| `--dry-run` | plan and print, encode nothing |
| `--format curiosity` | force a family for this run |
| `--no-preview` | final only |
| `--ignore-feedback` | plan from scratch, ignoring recorded feedback |
| `--keep-in-place` | do not move the folder between lifecycle states |
| `--json` | machine-readable result |

`--dry-run` with `--format` is the cheap way to see what a family would do
before committing to the encode.

## What you get

```
outputs/final/job-003-r1.mp4                            the video
outputs/previews/job-003-r1-preview.mp4                 smaller, for review
outputs/posting-packages/job-003-r1-posting-package.yaml caption, hashtags, CTA…
outputs/quality-reports/job-003-r1-quality-report.yaml  25 checks
outputs/edit-plans/job-003-r1-edit-plan.yaml            every decision made
outputs/final/job-003-r1-manifest.yaml                  lineage
```

The posting package has the hook, the on-screen text transcript, the caption,
hashtags and their strategy, thumbnail frame and text, the CTA, a pinned
comment, prepared replies, the format used, the editing decisions, the
retention hypothesis and any research cited.

The edit plan is worth reading when something looks wrong. It is the complete
description the renderer worked from, so a surprising result is visible there
without re-running anything.

## Then

Watch it, and either approve:

```bash
./process-job approve job-003
```

or say what is wrong — see [`feedback.md`](feedback.md).
