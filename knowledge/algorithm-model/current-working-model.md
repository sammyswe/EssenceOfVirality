# Current Working Model

Revision date: 2026-08-03 (v0.1 — first research batch merged into the v0 seed)

The project's evolving behavioural model of TikTok discovery and distribution. **This is a model,
not reverse engineering.** It carries uncertainty by design and is updated only through reviewed
PRs citing claims.

## Current conclusion (v0.1)

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
   (`claim-20200618-feed-diversification`); independently, a 2024 audit found only 30–50% of a
   user's first 1,000 videos were interest-matched "exploitation" recommendations — a large
   exploration share, consistent with genuine per-video testing on non-matched audiences
   (`claim-20240424-exploitation-share`).
7. The For You page is the dominant distribution surface (reported >75% of views — weakly
   evidenced secondary citation, `claim-20231009-fyp-dominant-surface`), so FYP selection, not
   follower delivery, is the battleground.
8. Engagement and plays rise together among trending videos (comments, likes, shares each
   correlate with play counts — correlational, `claim-20210621-engagement-correlates-plays`);
   platform objectives centre on retention and watch time per the leaked engineering document
   as reported secondhand (`claim-20250423-retention-watchtime-core-metrics`).
9. Followers change *who* sees a video and *how they respond*: following raises the odds of
   being shown an account's videos, yet followed-account videos are completed less and liked
   more (partly social/support liking) — follower-heavy metrics can flatter content quality
   (`claim-20240424-followed-account-effects`).
10. Posting time correlated with top play counts among trending videos (2021, UTC-only —
    directionally useful, not schedulable from this evidence;
    `claim-20210621-posting-time-effect`), and trending can lag posting by days to weeks.

Production consequence (the only way this model may be used): influence viewer behaviour —
earn the full watch, the share, the comment, the follow — through honest content decisions. The
chain is always: production decision → viewer perception/behaviour → observed metrics → possible
distribution effect.

## Supporting claims

See `known-platform-disclosures.md` (seven official 2020 claims, platform-dependent) plus the
first research batch: `claim-20210621-*` (Klug 2021, peer-reviewed trending-data analysis),
`claim-20240424-*` (UW 2024 data-donation audits), `claim-20231009-*` (Herman 2023,
design research), `claim-20250423-*` (Lynch 2025 thesis, secondhand leaked-document reporting).

## Disputed claims

- Skip-speed as a negative signal: `claim-20250423-fast-skip-negative-signal` (lore/uncited)
  vs `claim-20240424-scroll-speed-weak-signal` (measured, little effect) —
  `contra-20260803-skip-speed-signal`. Working position: do not assume a skip penalty.
- Trending hashtags: `claim-20240719-zhou-engagement-features` (low-credibility source) vs
  `claim-20210621-hashtag-piling-ineffective` — `contra-20260803-trending-hashtag-effect`.
  Working position: hashtag piling is not a lever.
- Optimal length: `claim-20231009-length-42s-peak` vs `claim-20240719-zhou-engagement-features`
  — `contra-20260803-optimal-length`. No working position; candidate phase-5 experiment.

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
