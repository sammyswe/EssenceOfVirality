# Metadata and Discovery

Revision date: 2026-08-03

How captions, hashtags, on-screen text and sounds affect a video's classification, search
indexing and routing to interested viewers — the controllable *packaging* around the content
itself.

## Current conclusion (first research batch — mixed evidence tiers)

The platform machine-classifies video content (text, audio, visual elements) for interest
matching and search. Of the packaging levers, honest topical wording appears to matter;
hashtag piling does not:

1. **Hashtag piling is not a lever.** Adding trending or algorithm-targeted hashtags (#fyp,
   #foryou), or stacking popular hashtags, showed no relationship to play counts in the only
   transparent test (`claim-20210621-hashtag-piling-ineffective`, finding, 2021 —
   disputed only by a low-credibility source, `contra-20260803-trending-hashtag-effect`).
   Use at most a few content-descriptive tags (`tech-20260803-limit-hashtag-reliance`).
2. **On-screen text is (plausibly) parsed for categorisation and search.** Creators treat
   on-screen keywords as having replaced hashtags for classification; one documented anecdote
   shows topical wording flipping a video into search indexing with a large view effect
   (`claim-20231009-onscreen-text-categorisation`, hypothesis). Niche application:
   one honest genre/mood cue that doubles as hook and search phrase
   (`claim-20260803-hyp-searchable-text`, `tech-20260803-use-searchable-onscreen-text`).
3. **Trending Sounds are a real flywheel we mostly cannot ride.** The editor recommends
   trending Sounds and lore says they boost reach (`claim-20231009-trending-sound-boost`,
   hypothesis) — but mix videos use original captured Spotify audio, so this lever is
   unavailable; how original-audio music content is matched to listeners remains a niche
   unknown (`../algorithm-model/unknowns.md`).
4. **Search is a growing surface.** TikTok increasingly functions as a search engine, and the
   per-video search-bar suggestion reveals whether a video was topically indexed — a rare
   observable feedback signal worth checking on every post
   (`claim-20231009-onscreen-text-categorisation`).

## Supporting claims

`claim-20210621-hashtag-piling-ineffective` (finding);
`claim-20231009-onscreen-text-categorisation` (hypothesis);
`claim-20231009-trending-sound-boost` (hypothesis);
`claim-20260803-hyp-searchable-text` (hypothesis).

## Disputed claims

`claim-20240719-zhou-engagement-features` (claims trending hashtags help; low-credibility
source — `contra-20260803-trending-hashtag-effect`).

## Open questions

- What house-mix listeners actually search (phase-5 analytics can ground the vocabulary).
- Whether caption text and on-screen text are weighted differently.
- How original-audio music content is classified without platform-recognised sounds.

## Practical implications

Candidate skill `searchable-onscreen-text` (experimental bank,
`scp-20260803-searchable-onscreen-text`) operationalises point 2 under the one-cue and
Spotify-legibility constraints.

## Related skills

`searchable-onscreen-text` (experimental), `analyse-first-frame`, `evaluate-hook-clarity`.

## Related experiments

None yet; topical vs non-topical text comparison is the natural phase-5 test.
