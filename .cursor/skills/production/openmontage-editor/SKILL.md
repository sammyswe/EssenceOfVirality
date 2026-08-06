---
name: openmontage-editor
description: Execute an edit plan as a deterministic render, coordinating OpenMontage and FFmpeg while preserving the Spotify audio exactly. Use when a render fails, when output geometry is wrong, or when deciding whether a capability belongs to OpenMontage or to FFmpeg.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# OpenMontage editor

Stage 4. Executes; decides nothing. Implementation:
`production/pipeline/render.py`, adapter in `production/pipeline/om.py`.

## Purpose

Turn an `EditPlan` into an MP4 that matches it, using one FFmpeg filter graph,
with OpenMontage owning the capabilities it genuinely provides.

## When to invoke

- A render fails and the filter graph needs reading.
- Output geometry, frame rate or encoding settings are wrong.
- A new capability is needed and the OpenMontage-or-FFmpeg question is open.
- The OpenMontage clone is missing, mismatched, or its pin needs updating.

## When not to invoke

- To change what the video contains. Change the plan; this stage only executes
  one.
- To judge the result. That is `video-quality-controller`.

## Inputs

Required: a valid `EditPlan`, the matching `InputReport`, an output path.

Optional: a preview path, a render preset name (default `tiktok_final`).

## Workflow

1. Load the preset. An unknown preset is an error, not a fallback.
2. Build the graph in fixed order: source split, blurred background, Spotify
   surface fit and overlay, secondary clips, transition emphasis, progress bar,
   text cues, output format.
3. Fit the Spotify surface with `fit_spotify_surface`, which protects the
   must-remain-visible regions and reports what it cropped and what it could
   not enlarge.
4. Build the audio chain from input 0 alone: loudness normalisation if the plan
   asks for it, resample, nothing else.
5. Run one FFmpeg invocation. On failure, surface the graph alongside the error;
   an FFmpeg message without its graph is unreadable.
6. Probe the output and confirm a file exists with the expected geometry.
7. Render the preview proxy if one was requested.
8. Done when the result reports its duration, geometry, audio inputs and the
   backend used for each capability.

## Hard rules

- Input 0's audio stream is the only audio. Every other input is mapped
  video-only. There is no configuration that adds a second source.
- The only permitted audio processing is loudness normalisation and resampling.
  No EQ, no compression, no effects, no crowd noise.
- Never re-time, re-pitch or re-cut the mix. The transition is untouchable.
- One render, one FFmpeg call. Intermediate files cost a generation of quality
  and introduce sync bugs.
- Never write to a source file. Outputs go to `outputs/` only.
- Do not invent OpenMontage APIs. Every adapter call maps to a tool that exists
  at the pinned ref, and every one has an FFmpeg fallback.

## Recommendations

- Prefer OpenMontage where it owns the capability outright — probing, scene
  detection, the TikTok media profile — and FFmpeg where precision matters more
  than abstraction.
- Keep filter expressions readable. A comment explaining why `zoompan` is used
  instead of `crop` saves the next reader an hour.
- Record the backend actually used per capability, so a machine without the
  clone produces a manifest that says so.

## Output

`RenderResult`: `output_path`, `preview_path`, `duration_seconds`, `width`,
`height`, `audio_inputs`, `filter_graph`, `command`, `backends`, `notes`.

The notes carry anything the creator would otherwise have to discover by
watching, including how much a requested enlargement actually achieved.

## Failure conditions

| Condition | Response |
| --- | --- |
| Unknown render preset | Raise, listing the available presets |
| Source recording missing at render time | Raise; do not substitute anything |
| FFmpeg exits non-zero | Raise with the full graph attached |
| Output written but unprobeable | Raise; a file that will not open is not a render |
| OpenMontage clone absent | Continue on FFmpeg fallbacks; record it in the manifest |
| Clone present but off the pin | Warn; results are no longer reproducible |

## Example

A clean-showcase plan produces a graph of roughly ten chains and one FFmpeg
call. The notes read: zoom pulse of 8% centred on 7.00s; loudness normalised,
-15.73 LUFS is 1.73 dB from the -14.0 LUFS target. Both are facts about what the
renderer did, in terms the creator can check against the file.

## Anti-patterns

- Rendering in passes to keep the graph simple. Each pass is a re-encode, and
  the audio drifts.
- Silently falling back when an OpenMontage tool errors. Record which backend
  ran; a manifest that cannot say what produced the file cannot support
  reproduction.
- Adding a filter because it looks good on this one video. Effects belong in a
  template where they can be turned off and compared.

## Quality checklist

- [ ] Exactly one audio input, from the Spotify recording.
- [ ] Output is 1080x1920 at the preset's frame rate.
- [ ] Rendered duration matches the plan.
- [ ] Every backend used is recorded.
- [ ] The graph is in the result, so a failure can be diagnosed from logs.

## Related skills

`tiktok-retention-editor` produces the plan this executes.
`video-quality-controller` checks the file this produces.
`preserve-spotify-mix-audio` owns the judgement about whether audio processing is warranted at all.
`review-openmontage-integration` covers changes to the pin or the adapter surface.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/render.py`.
