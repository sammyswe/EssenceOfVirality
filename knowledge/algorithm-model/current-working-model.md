# Current Working Model

Revision date: 2026-08-03

The project's evolving behavioural model of TikTok discovery and distribution. **This is a model,
not reverse engineering.** It carries uncertainty by design and is updated only through reviewed
PRs citing claims.

## Current conclusion (v0 — single-source seed)

A video's distribution appears to be driven by *viewer responses to the video* rather than by
account-level status:

1. Videos that are eligible (moderation/quality gates passed) can enter recommendation
   (`claim-20200618-eligibility-gates`).
2. Viewer interactions with the video — watching to completion (strong), liking, sharing,
   commenting, following (strengths not disclosed) — feed ranking for further viewers with
   matched interests (`claim-20200618-ranking-factor-categories`,
   `claim-20200618-completion-strong-signal`).
3. Video metadata (captions, sounds, hashtags) contributes to interest matching — i.e. *who* is
   tested, not just how the video scores (`claim-20200618-ranking-factor-categories`).
4. Negative feedback suppresses similar future recommendations for that viewer
   (`claim-20200618-negative-feedback-shapes-feed`).
5. Follower count and past performance are not direct inputs
   (`claim-20200618-follower-count-not-direct`) — consistent with per-video testing behaviour.
6. Deliberate diversification means distribution is not a pure engagement maximiser
   (`claim-20200618-feed-diversification`).

Production consequence (the only way this model may be used): influence viewer behaviour —
earn the full watch, the share, the comment, the follow — through honest content decisions. The
chain is always: production decision → viewer perception/behaviour → observed metrics → possible
distribution effect.

## Supporting claims

See `known-platform-disclosures.md` (all seven claims, official, 2020, platform-dependent).

## Disputed claims

None yet.

## Open questions

The model is seeded from one official 2020 source; almost everything quantitative is unknown —
see `unknowns.md`. Hypotheses under consideration: `inferred-distribution-hypotheses.md`.

## Practical implications

Completion is the most defensible optimisation target for 10–40 s mix videos; early-skip
reduction and payoff placement are its production levers
(`viewer-behaviour/completion.md`, `production-techniques/hooks.md`).

## Related skills

`analyse-first-frame`, `evaluate-hook-clarity`, `evaluate-transition-payoff`.

## Related experiments

None yet.
