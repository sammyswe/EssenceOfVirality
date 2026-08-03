---
name: analyse-first-frame
description: Diagnose whether a video's first frame communicates an honest content promise, and produce concrete first-frame fixes. Use when evaluating a draft video or edit plan for early-skip risk, or when selecting a cover frame.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: low
  evidence_basis: [official, creator_statement]
  evidence_refs:
    - claim-20260803-hyp-early-skip-promise
    - claim-20200618-completion-strong-signal
    - claim-20260803-pref-spotify-legibility
  requires_human_approval: false
---

# Analyse the first frame

Intended viewer effect: reduce `early_skip_rate`, protecting `average_watch_time` and
`completion_rate`. Evidence tier: hypothesis + official completion-signal disclosure — treat
recommendations as provisional, not proven (`knowledge/production-techniques/hooks.md`,
`knowledge/viewer-behaviour/completion.md`).

## Inputs

Required: first-frame description or image, video duration, the video's actual content promise
(what the payoff is). Optional: hook text plan, series context.

## Steps

1. One-second read test: list everything a first-time viewer can register in ~1 second at mobile
   size (dominant visual, any text ≤ ~6 words, motion cue). Complete when the list is written.
2. Promise check: does that list communicate what the video will deliver (for this niche
   normally: a Spotify mix transition worth waiting for)? Answer yes/no with the specific
   missing or present element. Complete when answered.
3. Honesty check: is everything communicated true of the actual content? Any element promising
   something the video does not deliver fails regardless of attention value. Complete when
   answered.
4. Legibility check: is the Spotify context recognisable and unobscured
   (claim-20260803-pref-spotify-legibility)? Complete when answered.
5. If any check failed, produce fixes as edit-spec entries, each naming its intended viewer
   effect. Permitted fix classes: reframe/trim so the frame shows imminent-transition context;
   add/edit one short honest text cue; remove obscuring elements; pick a different cover frame.
   Complete when each failed check has ≥1 concrete fix or is explicitly accepted with reasons.

## Output contract

```yaml
first_frame_analysis:
  one_second_read: []          # what registers
  promise: {communicated: bool, detail: ""}
  honest: {value: bool, detail: ""}
  legible: {value: bool, detail: ""}
  fixes: [{change: "", intended_effect: early_skip_rate}]
```

## Anti-patterns

- Adding attention elements that misrepresent content — propose an honest alternative instead.
- Fixing a working frame: if all checks pass, output zero fixes (see fixture
  `fix-03-poor-audio`, where visual changes are a false positive).
- Text walls: more than one text element in frame one competes with itself — choose the
  strongest single cue.

## Example / counterexample

Example: static playlist screen, no text (fixture `fix-02-weak-first-frame`) → promise fail →
fix: open on now-playing view 4 s before the blend + cue text "wait for the switch".
Counterexample of a bad fix: "make the first frame more eye-catching" — not an edit-spec entry;
name the exact change instead.
