---
name: preserve-spotify-mix-audio
description: Audit captured Spotify-mix audio for damage and decide between re-capture, minimal processing, or no action — the music is the product. Use when reviewing captured audio quality or before any audio processing decision.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: [creator_statement]
  evidence_refs:
    - claim-20260803-pref-music-central
  requires_human_approval: false
---

# Preserve Spotify-mix audio

Intended viewer effect: protect `average_watch_time` and `completion_rate` by never letting
capture faults or over-processing degrade the listening experience — the niche's core value
(claim-20260803-pref-music-central; `knowledge/spotify-mix-niche/value-proposition.md`).

## Inputs

Required: the captured audio (or a fault description), the blend window timestamps. Optional:
capture settings, loudness measurement.

## Steps

1. Fault inventory: check for clipping/distortion, dropouts, notification/system sounds,
   loudness far from mobile-playback norms, and artefacts inside the blend window specifically.
   Complete when each fault is listed with timestamps or marked absent.
2. Classify each fault: **capture-fixable** (recoverable only by re-recording: clipping,
   dropouts, foreign sounds inside the music) vs **processing-fixable** (loudness normalisation,
   fade trim at extremes). Complete when every fault is classified.
3. Decision rule: any capture-fixable fault inside the blend window → primary recommendation is
   RE-CAPTURE, with the exact settings change that prevents recurrence (lower capture gain,
   do-not-disturb on, etc.). Processing may never be presented as a substitute (fixture
   `fix-03-poor-audio`). Complete when the decision is stated.
4. Permitted processing list (only when no capture-fixable fault remains): loudness normalise to
   a stated target; trim silence outside the music; nothing else without creator approval — no
   denoise, no limiting, no EQ "enhancement" of the mix itself. Complete when the processing
   list (possibly empty) is explicit.
5. Clean audio in → say so and recommend no action (fixtures `fix-01`, `fix-04`: flagging good
   audio is a false positive). Complete when the report is written.

## Output contract

```yaml
audio_audit:
  faults: [{type: "", where: "", class: capture_fixable | processing_fixable}]
  decision: recapture | process | no_action
  processing: []            # exact operations + targets, empty unless decision=process
  recapture_guidance: ""    # required when decision=recapture
```

## Anti-patterns

- Rescue-processing damaged music to avoid a re-record — the damaged blend *is* the product
  failing; re-capture.
- Loudness war: normalising beyond the stated target to "punch harder" alters the mix's
  dynamics; normalise to target only.
- Adding sound effects or sweeteners over the mix — foreign audio breaks the made-in-Spotify
  promise.

## Example / counterexample

Example: -28 LUFS clean capture → `process`, normalise to target, nothing else. Counterexample:
clipped bass at the drop → NOT "apply a de-clipper and limiter"; the correct output is
`recapture` with gain guidance.
