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

External baseline (first calibration point): most viewers complete only a minority of videos —
~55% of recommended videos are *not* watched to the end, most users finish 30–50%, and this is
stable over tenure (`claim-20240424-completion-baseline`, academic, 2024). Full watch-through is
the exception; a mix video that earns it is outperforming typical behaviour, and targets should
be set against this reality rather than against 100%.

Nuances from the 2024 data-donation studies:

- Viewers complete videos from accounts they follow *less* while liking them more (social
  liking) — follower-heavy engagement can mask weak retention
  (`claim-20240424-followed-account-effects`).
- Scroll-past speed showed little observable effect on the skipper's subsequent
  recommendations (`claim-20240424-scroll-speed-weak-signal`) — early-skip reduction is
  motivated by watch time and completion themselves, not by a proven "skip penalty"
  (`contra-20260803-skip-speed-signal` keeps the lore version disputed).

Production levers believed to influence completion (heuristic tier):

- Early-skip reduction: a clear, honest content promise in the first second
  (`claim-20260803-hyp-early-skip-promise`, hypothesis).
- Payoff placement: the transition landing where anticipation peaks, with no dead time
  (`tech-20260803-optimise-for-completed-watches`, heuristic).
- Duration honesty: no padding after the payoff groove settles.
- Loop design (sub-20 s edits): a musically seamless loop may add rewatch on top of completion
  (`claim-20260803-hyp-loop-rewatch-lever`, hypothesis; `tech-20260803-design-for-loop`).

## Supporting claims

`claim-20200618-completion-strong-signal` (fact, official);
`claim-20240424-completion-baseline`, `claim-20240424-followed-account-effects` (findings,
academic); `claim-20231009-loop-rewatch-pattern` (pattern).

## Disputed claims

`claim-20250423-fast-skip-negative-signal` (skip-speed penalty — disputed, see
`contra-20260803-skip-speed-signal`).

## Open questions

- Is completion evaluated as a rate, absolute seconds, or percentile vs similar content?
  (`../algorithm-model/unknowns.md`)
- For sub-15 s videos, does loop-driven rewatch matter more than single completion? (Now a
  named hypothesis: `claim-20260803-hyp-loop-rewatch-lever`; loop *weighting* still unknown.)

## Practical implications

Evaluation skills treat predicted early-skip and payoff timing as first-order checks
(`evaluation/rubrics/video-evaluation.md`, sections A–B).

## Related skills

`analyse-first-frame`, `evaluate-hook-clarity`, `evaluate-transition-payoff`.

## Related experiments

None yet; payoff-placement comparison is the natural first experiment (phase 5).
