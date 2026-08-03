---
name: searchable-onscreen-text
description: Choose one honest on-screen text cue for a Spotify-mix video whose wording doubles as a search phrase, and verify post-hoc that the video was search-indexed. Use when planning overlays/captions for a post, or when a posted video shows no topical search-bar suggestion.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: low
  evidence_basis: [academic, observational, creator_statement]
  evidence_refs:
    - claim-20231009-onscreen-text-categorisation
    - claim-20260803-hyp-searchable-text
    - claim-20210621-hashtag-piling-ineffective
    - claim-20260803-pref-spotify-legibility
  requires_human_approval: false
---

# Searchable on-screen text

Intended viewer effect: improve `search_discovery` and interest matching while still serving
the hook's promise role — one cue, two jobs. Evidence tier: hypothesis (creator lore + one
documented anecdote + platform machine-classification background) — treat every
recommendation as provisional and verify per post
(`knowledge/production-techniques/metadata-and-discovery.md`).

## Inputs

Required: the video's actual content (genre, mood, transition description), the planned hook
text (if any), first-frame layout. Optional: past posts' search-bar observations.

## Steps

1. Candidate phrases: write 3-5 short phrases a target listener would plausibly type when
   looking for this content ("melodic house mix", "sunset house transition", "spotify house
   playlist mix"). Each must be true of this specific video. Complete when the list exists.
2. Merge with the hook: pick the one phrase that also works as the honest content promise. If
   the planned hook text and the search phrase cannot merge into a single cue, keep the hook
   and move the topical wording to the caption instead — never add a second on-screen text
   element for search alone. Complete when one cue (or caption fallback) is chosen.
3. Placement check: the cue must not obscure Spotify UI elements that establish authenticity
   (claim-20260803-pref-spotify-legibility) and must pass the one-second read test from
   `analyse-first-frame`. Complete when placement is specified.
4. Hashtag restraint: caption gets at most 2-3 content-descriptive tags; no #fyp/#foryou, no
   trending-tag piling (claim-20210621-hashtag-piling-ineffective). Complete when the caption
   tag list is written.
5. Post-hoc verification (when the video is posted): record whether the video's search-bar
   suggestion shows a topical phrase (indexed) or a generic "Find related content" (not
   indexed), and note it with the post record for future analytics. Complete when recorded or
   explicitly deferred.

## Output contract

```yaml
searchable_text_plan:
  candidate_phrases: []
  chosen_cue: ""            # or null if caption fallback used
  caption_wording: ""
  caption_hashtags: []      # max 3, content-descriptive only
  placement: ""             # where in frame, what it must not cover
  verification: {indexed: null, observed_phrase: ""}
```

## Anti-patterns

- Keyword stuffing or a second text element for SEO — violates the one-cue rule and risks
  overlay overload (fixture `fix-04-overlay-overload`).
- Wording that promises content the video does not deliver — honesty policy (fixture
  `fix-06-misleading-hook`).
- Treating indexing as guaranteed distribution: indexing is observable, its ranking effect is
  a hypothesis (claim-20260803-hyp-searchable-text).

## Example / counterexample

Example: 18s melodic-house transition at golden hour → cue "melodic house mix for sunset
drives" placed in the lower third clear of the Spotify progress bar; caption repeats the
phrase + #melodichouse #djmix; after posting, search bar shows "melodic house mix" → indexed:
true.
Counterexample: adding "VIRAL HOUSE MUSIC 2026 🔥" — not a listener search phrase, not honest
about this specific video, and competes with the hook cue.
