# Inferred Distribution Hypotheses

Revision date: 2026-08-03

Testable propositions about distribution/viewer behaviour that are **not** officially confirmed.
Records live in `evidence/hypotheses/`; this document synthesises them. Unobservable-mechanism
claims from sources are rewritten here as behavioural hypotheses (distribution-model analyst's
duty) — never stored as purported algorithm facts.

## Active hypotheses

### `claim-20260803-hyp-completion-lever`

For 10–40 s Spotify-mix videos, increasing the proportion of viewers who watch to the end (by
reducing early skips and placing the transition payoff where anticipation peaks) may increase
subsequent distribution. Derived from `claim-20200618-completion-strong-signal` (official:
completion is a strong, highly weighted signal) — but the *causal, quantitative* effect on
distribution volume for short music content is unmeasured. Test: retention-curve + view
comparison across payoff placements once analytics exist (phase 5).

### `claim-20260803-hyp-early-skip-promise`

Videos whose first ~1 second fails to communicate a content promise may suffer higher early-skip
rates, lowering average watch time and completion. Grounded in general attention reasoning plus
the official weight on full watches; not itself disclosed by the platform. Test: first-frame
variants (promise vs neutral) on comparable posts.

### `claim-20260803-hyp-searchable-text`

One short, honest on-screen text cue naming genre/mood/context ("melodic house mix") may
improve interest matching and search discovery for mix videos without harming Spotify
legibility. Derived from `claim-20231009-onscreen-text-categorisation` (creator lore + one
documented anecdote + ByteDance's stated machine classification). Test: compare per-video
search-bar indexing and views for topical vs non-topical text on comparable posts (phase 5).

### `claim-20260803-hyp-loop-rewatch-lever`

For sub-20 s mix videos, a musically seamless loop (ending flows back into the opening) may
raise rewatch and total watch time per viewer, functioning as an extra retention signal beyond
single-view completion. Derived from `claim-20231009-loop-rewatch-pattern` (loops register as
plays) with loop *weighting* unknown. Test: loop-seamed vs hard-ending edits of comparable
transitions (phase 5).

## Rules for this document

- Every entry cites its motivating claims and names a concrete test.
- Nothing here may be cited by a skill as fact; skills reference these as `hypothesis` with
  `confidence: low|medium`.
- Confirmed hypotheses graduate via experiment-result claims; contradicted ones move to
  `status: rejected` with the experiment recorded — never silently deleted.

## Open questions

See `unknowns.md`.

## Related skills

`analyse-first-frame`, `evaluate-hook-clarity`, `evaluate-transition-payoff`.

## Related experiments

None yet (phase 5 will propose the two tests above).
