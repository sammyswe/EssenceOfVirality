# Completion

Revision date: 2026-08-03

Watching a video to its end — the viewer behaviour with the strongest official grounding as a
distribution signal, and the primary retention target for 10–40 s Spotify-mix videos.

## Current conclusion

TikTok officially states that finishing a longer video from beginning to end is a strong,
highly weighted interest indicator (`claim-20200618-completion-strong-signal`, official, 2020,
platform-dependent). For this project's short videos, completion is *plausibly* a distribution
lever (`claim-20260803-hyp-completion-lever` — hypothesis, unmeasured) and is anyway the honest
proxy for "the viewer enjoyed the whole mix moment".

Production levers believed to influence completion (heuristic tier):

- Early-skip reduction: a clear, honest content promise in the first second
  (`claim-20260803-hyp-early-skip-promise`, hypothesis).
- Payoff placement: the transition landing where anticipation peaks, with no dead time
  (`tech-20260803-optimise-for-completed-watches`, heuristic).
- Duration honesty: no padding after the payoff groove settles.

## Supporting claims

`claim-20200618-completion-strong-signal` (fact, official).

## Disputed claims

None yet.

## Open questions

- Is completion evaluated as a rate, absolute seconds, or percentile vs similar content?
  (`../algorithm-model/unknowns.md`)
- For sub-15 s videos, does loop-driven rewatch matter more than single completion?

## Practical implications

Evaluation skills treat predicted early-skip and payoff timing as first-order checks
(`evaluation/rubrics/video-evaluation.md`, sections A–B).

## Related skills

`analyse-first-frame`, `evaluate-hook-clarity`, `evaluate-transition-payoff`.

## Related experiments

None yet; payoff-placement comparison is the natural first experiment (phase 5).
