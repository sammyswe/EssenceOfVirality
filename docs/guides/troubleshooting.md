# Troubleshooting

Symptoms in roughly the order you are likely to hit them. Errors name their own
cause where they can; this page covers the ones where the fix is not obvious
from the message.

Start here:

```bash
./process-job status              # can it run at all?
./process-job inspect <job>       # can it read this recording?
```

`inspect` runs no encode and answers most input questions in a second or two.

## The pipeline will not start

**`Missing required binaries: ffmpeg. Install FFmpeg…`**
`apt install ffmpeg` or `brew install ffmpeg`. Nothing works without it.

**`ModuleNotFoundError: numpy` / `yaml`**
`pip install -r tools/requirements.txt`.

**`openmontage absent (ffmpeg fallbacks)` in status**
Not an error. Every capability has an ffmpeg fallback and the output is the
same. Install the clone only if you want its backends — see
[`setup.md`](setup.md).

**`pin MISMATCH`**
The clone has drifted from `PINNED_REF`. Check the pinned commit out again
rather than running a different version:

```bash
git -C integrations/openmontage/clone checkout "$(cat integrations/openmontage/PINNED_REF)"
```

## The job will not load

**`No job folder for 'job-003'`**
The name is looked for under `jobs/incoming/`, `jobs/review/` and
`jobs/approved/`. A job that already rendered has moved to `review`, and the id
still resolves — so this usually means a typo or a folder that was never
created. `./process-job new job-003` makes one.

**`No video files in jobs/incoming/job-003`**
The folder has a `job.yaml` but no media. Copy the recording in.

**`N videos present but job.yaml does not name spotify_recording`**
With more than one video the pipeline guesses only when a filename contains
"spotify". Either rename the capture or set `spotify_recording:` explicitly.

**`additional asset not found` / `asset role 'x' invalid`**
Paths in `additional_assets` are relative to the job folder. Roles must be one
of `hook`, `reaction`, `background`, `supporting`.

**`render.aspect_ratio must be '9:16'`**
Quote it. Unquoted `9:16` is parsed by YAML as a sexagesimal number. The
pipeline accepts both forms now, so if you still see this the value is
something else entirely.

**`job.yaml sets 'layout' at the top level, where it does nothing`**
Configuration overrides go under `config_overrides`, not at the root:

```yaml
config_overrides:
  layout:
    split_spotify_fraction: 0.70
```

## The transition is found in the wrong place

`inspect` reports the detected time, the method and a confidence, plus
alternatives it considered:

```
  transition     14.20s (spectral_flux_novelty, high confidence)
                 alternatives: 12.60s, 15.80s
```

Detection keys on spectral flux — a change in timbre. A transition between two
tracks with similar instrumentation gives it little to find, and will usually
report `low` confidence. When it is wrong, say so in the job file:

```yaml
transition:
  seconds: 8.4
```

An override is used as given and is never second-guessed.

**`audio too short to analyse` / `audio too short for transition analysis`**
The recording is shorter than the analysis window. Record more around the
transition; a couple of seconds either side is not enough.

## Quality checks fail

A failure blocks the render and names the rule. The ones with non-obvious fixes:

**`crop cuts a must-remain-visible region: song_info, waveform`**
The crop needed to fit the placement would cut the labels or the waveform.
Usually caused by pushing `spotify_content_zoom` too far, or a split layout with
too little room. Lower the zoom, or raise `layout.split_spotify_fraction`.

If you *meant* to cut into the waveform's ends in exchange for a bigger
interface, that is what `layout.waveform_end_trim` is for. Setting it converts
this failure into a warning that names the setting, so the trade stays visible.

**`spotify_recognisable`**
Overlays have covered too much of the interface. Reduce the secondary clip's
size, move it, or drop it.

**`cue 'hook-1' overlaps protected region song_info`**
Text placement could not find a spot clear of the labels and waveform. The
safe text band is in `safe-zones.yaml`; shortening the hook usually solves it,
since a shorter box has more places to sit.

**`cue 'cta-1' box (…) leaves the text area`**
The text is too long for the safe band. Shorten it, or reduce the size in
`text-styles.yaml`.

**`sources_immutable: spotify-screen-recording.mp4`**
Your input file changed during the run. The pipeline hashes inputs before and
after and never writes to them, so this means something else touched the file —
a sync client, or an editor with it open.

**`claim '…' lacks a dated source`**
Copy asserted something factual without a research note. Either add one
(`./process-job research add …` with a URL and a publication date) or remove
the claim. There is no flag to skip this.

**`cut at 6.10s falls inside the transition region`**
An edit landed on the mix itself. The transition is never cut across; if this
appears after a config change, the lead-in or duration settings have pushed a
boundary into it.

## The video renders but looks wrong

**Nothing changed after feedback.** Check the revise output for `unread`
phrases — if the wording was not matched, nothing was applied. Rephrase using
the vocabulary in [`feedback.md`](feedback.md), or edit `job.yaml` directly.

**"Make the waveform larger" barely moved.** The waveform already spans most of
the frame width, so enlargement hits a physical ceiling quickly. The run
reports the ceiling it reached and names `layout.waveform_end_trim` as the
opt-in way past it.

**"Shorten the opening" stopped working.** The lead-in is bounded by
`duration.max_pre_transition_seconds` and by how much footage exists before the
transition. If the capture has three seconds before the mix, three seconds is
the floor.

**A format was refused.** Families declare what they need. Split-screen and PiP
need a supporting clip; unexpected-combination needs two genuinely different
genres in `tracks`, because its hook claims the songs clash. The run says which
requirement failed. `./process-job formats` lists the requirements.

**The same hook keeps appearing.** Hook selection avoids the previous hook for a
job, not across jobs. Say "the hook is generic" to force a different one, or
fill in `tracks` — track and artist names unlock hooks that generic phrasing
cannot reach.

**Text sits somewhere odd.** It was moved to clear a protected region; the run
warns when this happens and says why. That warning is the system working. If
the new position is bad, shorten the text so it has more room to fit.

## Getting the file

**`no render found for job-003-r2`**
Nothing has been rendered under that id. `./process-job status` lists what
exists. Note the `-rN` suffix: the newest render is not always `r1`.

**`/opt/cursor/artifacts is not present or not writable`**
You are not in a cloud agent. The files exist under `outputs/`; fetch them with
your editor, `scp`, or by running locally. See
[`phone-workflow.md`](phone-workflow.md) for the fallbacks.

**A staged artifact link does not resolve.** Ask the agent to re-stage and
re-link. Link lifetime after the agent run ends has not been verified — download
promptly rather than relying on it later.

## Validators fail

```bash
python3 tools/validate_artifacts.py
python3 tools/lint_skills.py
python3 tools/check_ids.py
python3 tools/run_fixtures.py
```

**`ERROR …: <field>: … is not of type 'string'`**
An artifact does not match its schema in `schemas/`. If you added a field to a
dataclass, add it to the schema too.

**`lint_skills` failure**
Usually missing frontmatter, or a `name` that does not match its folder. See
`.cursor/skills/meta/skill-authoring-standard/SKILL.md`.

**`check_ids` failure**
Artifact IDs must be unique and carry a registered prefix (`plan-`, `qr-`,
`pkg-`, `fb-`, `pref-`, `exp-`, `post-`, `res-`, `vpm-`). New artifact types
need their prefix in `schemas/common.schema.json` and `tools/common.py`.

## Starting clean

Renders are reproducible from the job folder, so deleting them loses nothing:

```bash
rm -rf outputs/final/* outputs/previews/* outputs/edit-plans/*
./process-job job-003 --ignore-feedback
```

`--ignore-feedback` plans from scratch rather than continuing the revision
chain, which is what you want when comparing two runs.

Do not delete `feedback/`, `preferences/`, `experiments/` or `analytics/` — that
is the system's memory, and it is the only thing here that cannot be
regenerated.
