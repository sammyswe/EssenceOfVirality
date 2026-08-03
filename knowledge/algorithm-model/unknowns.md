# Unknowns

Revision date: 2026-08-03

What the project explicitly does not know about TikTok distribution. This list keeps agents
honest: a claim answering one of these questions needs strong evidence, and any source asserting
one confidently should be treated with suspicion.

## Quantitative unknowns

- Actual weights of any ranking signal, and how they changed since the 2020 disclosure.
- Whether/how initial distribution cohorts ("testing batches") work: size, selection, thresholds
  for further waves.
- Relative value of shares vs comments vs likes vs follows for further distribution.
- How rewatch/loop behaviour is measured and weighted, if at all.
- Whether average-watch-time and completion are used as rates, absolutes, or percentile
  comparisons against similar content.

## Structural unknowns

- How sound-based and search-based discovery interact with For You ranking.
- How audience clustering works (interest graphs vs behavioural lookalikes).
- Whether account-level history has *indirect* effects despite follower count not being a direct
  factor (e.g. audience-quality priors).
- How repeated distribution over time (resurfacing weeks later) is triggered.
- Interaction effects between engagement signals (e.g. does high completion amplify share value?).
- How content classification assigns niche/topic labels to screen-recording music content
  specifically.

## Niche unknowns

- Whether Spotify-interface screen recordings face any eligibility/classification friction.
- How original-audio music content is matched to house-music-interested viewers without
  platform-recognised sounds.
- UK-audience-specific distribution behaviour, if any.

## Policy for this document

Every phase-2 source ingestion should check: does this source *reduce* an unknown (cite it in
the relevant canonical doc and remove/narrow the entry here), *claim to answer* one without
adequate evidence (record as hypothesis with the source's limitations), or leave it untouched?
