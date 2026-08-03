# CONTEXT

Domain context for agents and contributors. Read this before making decisions.
ADRs live in `docs/adr/`. Terminology lives here and in `knowledge/glossary.md`.

## Creator objective

Build a personal, black-box video-production harness: input a short raw recording of a Spotify
mix; output a polished, post-ready TikTok video whose decisions are evidence-informed and whose
outcomes can be traced back to those decisions. Optimise, in order: views, followers, shares,
comments, likes, other positive engagement. Direct monetisation is not an objective.

## Target audience

English-speaking, primarily the UK house-music scene: house fans, Spotify users, people who want
playlists with polished DJ-like transitions, people who may add the creator's mixes to their
libraries, and people who may follow the TikTok account for future mixes.

## The niche and its value proposition

The novelty: polished, DJ-like listening experiences can be created and shared **within Spotify**.
Videos must communicate that the creator is unusually skilled at Spotify mixing (transitions,
sequencing), that following yields more strong mixes, and that viewers can use or recreate the
mixes in their own Spotify. The music is the product — overlays and tactics must never overwhelm
the listening experience or Spotify-interface legibility.

## Creator identity

Anonymous. No face-led strategy unless explicitly requested later. Identity signals come from
craft (transition quality, series consistency), not persona.

## Current input format (phase 3+ consumer)

10–40 s raw video, usually a screen recording of Spotify playing a manually refined house mix,
possibly including Spotify UI visuals and captured audio; optional creator instructions/feedback;
optional metadata (track names, mix theme, desired CTA).

## Current output vision (phase 4+)

Polished portrait TikTok video (1080×1920, correct export settings), high-quality audio and
visuals, hooks/overlays/captions/motion/pacing/CTAs selected using accumulated evidence, ready for
manual posting, with publishing recommendations where appropriate.

## Phase-one restrictions

This phase builds intelligence infrastructure only. Not in scope: video editing, posting, account
control, TikTok scraping, analytics warehouse, ML models, final UI, auto-merge, treating external
virality scores as ground truth. See `docs/roadmap/` and the anti-goals section of
`.cursor/rules/00-mission.mdc`.

## Key terminology (epistemic taxonomy)

| Term | Meaning |
|---|---|
| Fact | Directly supported by authoritative evidence or clearly measured first-party data |
| Finding | Reasonably supported by one or more sources but not necessarily universal |
| Hypothesis | Testable proposition that may explain performance |
| Heuristic | Practical rule that appears useful without claiming causal certainty |
| Pattern | Observed association across examples |
| Anecdote | Based primarily on one creator/account/uncontrolled example |
| Constraint | Platform, legal, ethical, technical or creator-specific limitation |
| Preference | Subjective requirement supplied by the creator |
| Experiment result | Documented outcome from a deliberate test |

These are never flattened into "best practices"; epistemic status is preserved end to end.

## The two bodies of knowledge

1. **TikTok distribution model** (`knowledge/algorithm-model/`, `knowledge/viewer-behaviour/`) —
   the evolving behavioural model of how discovery/distribution *may* work. Never presented as
   reverse engineering.
2. **Controllable production rules** (`knowledge/production-techniques/`,
   `knowledge/spotify-mix-niche/`) — decisions the pipeline can actually make. Every rule links to
   the viewer behaviour it intends to influence, via the chain:
   production decision → viewer perception/behaviour → observed metrics → possible distribution
   effect. Techniques never "please the algorithm" directly.

## Creator-stated evidence policies

- Curated informal sources are welcome; curated does not mean infallible.
- No automatic time decay on older findings; publication dates preserved; platform-dependent
  findings flagged for revalidation; enduring attention principles distinguished from
  platform-specific mechanics.
- Confidence is low/medium/high — no false-precision percentages.
