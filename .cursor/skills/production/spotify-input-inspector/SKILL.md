---
name: spotify-input-inspector
description: Inspect and validate a job's Spotify screen recording and supporting clips, locate the interface regions that must stay visible, and find the transition. Use before planning any edit, when a render looks mis-cropped, or when a recording is rejected and the reason is unclear.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Spotify input inspector

Stage 1. Everything downstream trusts this report, so it fails loudly rather
than guessing. Implementation: `production/pipeline/inspector.py`.

## Purpose

Turn a folder of media into a structured description of what the pipeline is
working with: geometry, crop profile, protected regions, transition time, tempo,
loudness, and the usability of each supporting clip.

## When to invoke

- Before `creative` plans anything, on every run.
- When a render crops or covers part of the Spotify interface.
- When a job fails at validation and the message needs interpreting.
- When a new recording setup is introduced and its geometry is unknown.

## When not to invoke

- To judge whether the musical transition is *good*. The creator checks that
  before submitting; this stage only locates it in time.
- To choose a format or write copy. That is `spotify-mix-creative-director`.

## Inputs

Required: a job folder containing a Spotify screen recording, resolvable through
`jobspec.load_job`.

Optional: supporting clips, `tracks` metadata, an explicit
`transition.seconds` in `job.yaml` when detection has previously been wrong.

## Workflow

1. Probe the recording. Absent video, absent audio, or zero duration is a
   blocking problem — stop and report; do not attempt a partial run.
2. Measure width, height, aspect ratio, duration and frame rate.
3. Select the crop profile whose aspect-ratio window contains the source, and
   record why it matched. Warn when the profile carries one (landscape captures
   lose horizontal information).
4. Map the profile's must-remain-visible fractions onto the output canvas,
   classifying each as hard (song labels, waveform) or soft (artwork).
5. Locate the transition: use `transition.seconds` if the job states one,
   otherwise detect it from spectral change and report the method, the
   confidence and the alternatives considered.
6. Estimate tempo where the audio supports it, and measure integrated loudness
   and true peak.
7. Inspect each supporting clip: duration, resolution, orientation, whether it
   carries audio that will be discarded, and whether it is usable at all.
8. Done when the report has either a non-empty `blocking_problems` list or a
   transition time with a stated confidence.

## Hard rules

- A recording with no audio stream is rejected. The mix is the product; there is
  nothing to make a video from.
- Never modify, move or rename the source files. Read only.
- Never invent a transition time. If detection finds nothing, say so and ask the
  creator for `transition.seconds` rather than picking the midpoint.
- Report low confidence as low confidence. A guess presented as a measurement
  produces an edit that lands on the wrong moment.

## Recommendations

- Prefer the creator's stated transition time over detection when both exist.
- Treat a detected transition in the first or last 8% of the recording as
  suspicious and say so; it is usually a fade-in or fade-out.
- When several candidate transitions score closely, report the alternatives
  rather than only the winner.

## Output

`InputReport` (`inspector.InputReport.as_dict()`): `spotify`, `crop_profile`,
`protected_regions`, `transition`, `beats`, `loudness`, `assets`,
`blocking_problems`, `warnings`, `backends`.

Inspect it directly with `./process-job inspect <job-id> --json`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Recording missing or unreadable | Blocking problem naming the expected path |
| No video or no audio stream | Blocking problem; the job cannot proceed |
| Aspect ratio matches no profile | Fall back to the default profile and warn |
| Transition undetectable | Warn, report low confidence, request `transition.seconds` |
| Supporting clip under 0.5s | Mark unusable; too brief to read on screen |

## Example

A 1080x1920, 30s capture selects `vertical_full`, needs no crop, and reports a
transition at 12.4s from spectral change with medium confidence, tempo 124 BPM,
integrated loudness -15.7 LUFS. The plan then places that transition where the
format wants it.

## Anti-patterns

- Reporting a transition without its confidence. Downstream cannot tell a
  measurement from a guess, and the edit lands wherever the guess fell.
- Widening a crop profile so a new recording "matches". Add a profile instead;
  a stretched window mis-crops the recordings it used to fit.
- Treating a clip's audio as a bonus. It is discarded, and saying so up front
  stops the creator wondering where it went.

## Quality checklist

- [ ] Every blocking problem names the file and what is wrong with it.
- [ ] The crop profile choice states the ratio and the window it fell in.
- [ ] The transition carries a method and a confidence.
- [ ] Each supporting clip is marked usable or unusable with a reason.

## Related skills

`spotify-mix-creative-director` consumes this report.
`video-quality-controller` re-checks the protected regions against the render.
`preserve-spotify-mix-audio` owns the audio-damage judgement this stage measures for.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/inspector.py`.
