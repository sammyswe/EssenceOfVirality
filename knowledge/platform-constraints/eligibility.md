# Recommendation Eligibility

Revision date: 2026-08-03

## Current conclusion

Some content is excluded from For You recommendation regardless of engagement: TikTok officially
lists just-uploaded/under-review videos, spam (including artificial traffic-seeking), and
shocking/graphic content as potentially ineligible (`claim-20200618-eligibility-gates`, fact,
official, 2020, platform-dependent). Eligibility is therefore a hard gate the pipeline must
clear before any optimisation matters.

For this niche the practical exposure is low (music screen recordings), with two watch-items:

- Anything reading as engagement manipulation (fake progress bars, deceptive loops) risks the
  spam gate — also prohibited by our integrity rules.
- Music/rights handling for captured Spotify audio is an unresolved legal-review area
  (`docs/guides/content-and-source-handling.md`) — a platform-policy constraint distinct from
  ranking.

## Supporting claims

`claim-20200618-eligibility-gates`.

## Disputed claims

None.

## Open questions

- Do screen recordings of the Spotify UI face classification friction
  (`../algorithm-model/unknowns.md`, niche unknowns)?
- Current (2026) moderation posture vs the 2020 disclosure.

## Practical implications

Rubric dimension E.16 (technical eligibility) is a veto gate. Future publish-stage checks
(phase 3) must verify eligibility risks before export.

## Related skills

None directly yet; enforced via the video-evaluation rubric.

## Related experiments

None.
