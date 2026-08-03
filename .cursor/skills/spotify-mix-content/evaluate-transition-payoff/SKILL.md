---
name: evaluate-transition-payoff
description: Assess whether the mix's transition lands as the video's payoff — timing, anticipation, clarity — and produce structural fixes that never alter the transition itself. Use when reviewing a draft mix video's structure or retention design.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: low
  evidence_basis: [official, creator_statement]
  evidence_refs:
    - tech-20260803-optimise-for-completed-watches
    - claim-20200618-completion-strong-signal
    - claim-20260803-hyp-completion-lever
    - claim-20260803-pref-music-central
  requires_human_approval: false
---

# Evaluate transition payoff

Intended viewer effects: `completion_rate` and `average_watch_time` (payoff placement sustains
the watch — tech-20260803-optimise-for-completed-watches, heuristic; completion is officially a
strong signal — claim-20200618-completion-strong-signal; its distribution effect for this niche
is a hypothesis — claim-20260803-hyp-completion-lever). Secondary: `rewatch_rate` when the
payoff rewards a second listen.

## Inputs

Required: video duration, blend window timestamps, description of what precedes/follows the
blend, overlay timeline. Optional: retention expectations, series format.

## Steps

1. Payoff identification: is the transition audibly the video's peak moment, and is it complete
   within the video? Complete when yes/no with timestamps.
2. Anticipation: between 0 s and the blend, does anything build expectation (progress-bar
   proximity, honest cue text, musical build)? Dead time = any stretch a viewer could skip
   without losing the promise. Complete when dead time is listed (or none).
3. Placement arithmetic: time-to-payoff relative to duration — for 10–40 s videos, a payoff
   starting after ~40% of runtime with no anticipation is an early-skip risk
   (claim-20260803-hyp-early-skip-promise reasoning; provisional threshold, not proven).
   Complete when placement is judged with numbers.
4. Payoff visibility: during the blend window, is the audio moment unobstructed — no competing
   overlays, no promised-but-past banners (fixture `fix-04-overlay-overload`)? Complete when
   answered.
5. Fixes: structural only — trim dead time, move the start point closer to the build, clear the
   blend window of overlays, end within the groove settle. **The transition audio itself is
   untouchable** (claim-20260803-pref-music-central); a weak transition means a different clip,
   never an edited blend. A strong, well-placed payoff gets zero fixes (fixtures `fix-01`,
   `fix-05`). Complete when each fix names its intended viewer effect.

## Output contract

```yaml
payoff_evaluation:
  payoff: {present: bool, window: "", peak_confirmed: bool}
  anticipation: {present: bool, dead_time: []}
  placement: {starts_at_pct: 0, judgement: ""}
  visibility: {clear: bool, obstructions: []}
  fixes: [{change: "", intended_effect: completion_rate}]
```

## Anti-patterns

- "Wait for it" banners that outlive the payoff — anticipation devices must resolve when the
  payoff lands.
- Cutting the build so hard the blend loses musical context (fixture `fix-02` must_not).
- Treating a placement heuristic as law: the ~40% threshold is provisional; note it as such in
  reports.

## Example / counterexample

Example: 25 s video, blend at 14–19 s, 9 s static open → fixes: trim open to ≤4 s of genuine
build, add honest anticipation cue, keep 14–19 s audio untouched. Counterexample of a bad fix:
"speed up the transition to hit earlier" — alters the music; prohibited.
