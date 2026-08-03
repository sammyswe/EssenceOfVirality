# Known Platform Disclosures

Revision date: 2026-08-03

Officially disclosed information about TikTok's recommendation system. Everything here is
`claim_type: fact` with `evidence_basis: official` — but disclosures describe the system *at
publication time* and are marketing-reviewed communications; all are `platform_dependent: true`
and dated.

## Current conclusion

TikTok has officially confirmed (2020) that For You ranking uses three factor categories —
user interactions, video information, and (lower-weighted) device/account settings — that signal
strength matters (completing a longer video outweighs weak signals), that follower count and past
video performance are **not direct** ranking factors, that the feed deliberately diversifies, and
that eligibility gates exclude some content from recommendation entirely.

## Supporting claims

Source: [src-20200618-tiktok-newsroom-foryou](../../research/sources/src-20200618-tiktok-newsroom-foryou/manifest.yaml)
(TikTok Newsroom, 2020-06-18).

| Claim | Statement (condensed) |
|---|---|
| `claim-20200618-ranking-factor-categories` | Ranking combines user interactions (likes, shares, follows, comments, content created), video information (captions, sounds, hashtags), and device/account settings — the last weighted lower |
| `claim-20200618-completion-strong-signal` | Finishing a longer video from beginning to end is a *strong* interest indicator, weighted above weak indicators such as viewer/creator co-location |
| `claim-20200618-follower-count-not-direct` | Neither follower count nor previous high-performing videos are direct ranking factors |
| `claim-20200618-new-user-cold-start` | New users pick interest categories or receive a generalized popular feed; early likes/comments/replays initiate personalisation |
| `claim-20200618-feed-diversification` | The feed avoids two consecutive videos with the same sound or creator; duplicated, already-seen and spam content is not recommended; deliberate diversity is injected |
| `claim-20200618-negative-feedback-shapes-feed` | "Not interested", hide-creator and hide-sound actions shape future recommendations |
| `claim-20200618-eligibility-gates` | Just-uploaded or under-review videos, spam, and shocking/graphic content may be ineligible for recommendation |

## Disputed claims

None yet.

## Open questions

- How have factor weights changed since 2020? (see `unknowns.md`)
- Does "content you create" as an interaction signal affect creator-side distribution, or only
  viewer-side personalisation? The disclosure is viewer-framed.

## Practical implications

- Optimising completed watches is the best-grounded retention target we have
  (`viewer-behaviour/completion.md`).
- Account size is not an excuse: small accounts are not directly down-ranked
  (`claim-20200618-follower-count-not-direct`) — though audience-history effects may exist
  indirectly (see `inferred-distribution-hypotheses.md`).
- Sound reuse across our own posts may interact with diversification
  (`claim-20200618-feed-diversification`) — relevant when a mix series reuses audio.
- Eligibility gates make platform-constraint compliance a precondition, not an optimisation
  (`platform-constraints/eligibility.md`).

## Related skills

`evaluate-transition-payoff`, `evaluate-hook-clarity` (completion/skip reasoning).

## Related experiments

None yet.
