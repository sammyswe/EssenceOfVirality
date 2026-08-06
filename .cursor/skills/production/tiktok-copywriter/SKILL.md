---
name: tiktok-copywriter
description: Write the on-screen text, caption, hashtags, call to action, pinned comment and prepared replies for a Spotify mix video in the creator's voice. Use when assembling a posting package, when a caption sounds artificial, or when reviewing hashtag strategy.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# TikTok copywriter

Stage 6. Everything the viewer reads. Implementation:
`production/pipeline/posting.py`, text styles in
`production/config/text-styles.yaml`.

## Purpose

Produce the words: hook, on-screen cues, caption, hashtags, CTA, pinned comment
and a few prepared replies — in a voice that stays recognisably the creator's.

## When to invoke

- Assembling the posting package for a render.
- When the creator says a caption sounds artificial or generic.
- When reviewing whether hashtag strategy is working.
- When a comment section needs a reply that stays consistent with the account.

## When not to invoke

- To decide the format or the hook concept. That is
  `spotify-mix-creative-director`; this stage words it.
- To assert a fact. That needs `artist-trend-researcher` first.

## Inputs

Required: the `EditPlan` (hook, CTA, format, decisions), track metadata, the
quality status.

Optional: research notes for these artists, an approved hashtag strategy
preference, recent captions for voice consistency.

## Workflow

1. Write the caption from what the video actually shows: the pairing, that it
   was made in Spotify, and the ask. Two lines is usually enough.
2. Build hashtags from the strategy bands — artist-specific, Spotify-specific,
   niche, broad — recording which bands were used so performance attributes to a
   strategy rather than to individual tags.
3. Choose the thumbnail frame and its text. The frame should show the interface
   mid-transition, not a title card.
4. Write the pinned comment: the thing the creator would say first under their
   own post, usually the track names plus the ask.
5. Write two or three prepared replies for the questions this video will get:
   what the second track is, how the mix was made, whether it can be added to a
   playlist.
6. Transcribe every on-screen cue in order, so the package documents what the
   video says without needing to be watched.
7. Done when no claim lacks a source, and the CTA matches what the video earned.

## Hard rules

- No factual claim without a research note. Unsupported claims are stripped from
  the copy and the removal is recorded as a warning.
- No promise about performance, in copy or in the package's own commentary.
- No technical DJ vocabulary by default. Key signatures and phrase matching mean
  nothing to the intended viewer and read as gatekeeping.
- No Spotify profile promotion by default. The CTA asks for engagement, not
  traffic, unless the creator says otherwise.
- Never claim the mix does something it does not. If the transition is subtle,
  the copy does not call it insane.

## Recommendations

- Ask for the thing the video actually invites. A pairing question after a
  surprising blend gets answers; "follow for more" after anything gets nothing.
- Name both tracks somewhere. Recognition is the reason the viewer stayed and
  the reason they comment.
- Let hashtag strategy vary deliberately across posts so the record can
  eventually say something. A fixed set teaches nothing.
- Match the voice to the account: short, plain, no exclamation stacking, no
  emoji unless the creator uses them.

## Output

Contributions to the `PostingPackage`
(`schemas/posting-package.schema.json`): `caption`, `hashtags`,
`hashtag_strategy`, `thumbnail_frame_seconds`, `thumbnail_text`,
`call_to_action`, `pinned_comment`, `prepared_replies`, `onscreen_text`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Copy makes an unsupported claim | Strip the claim, warn, and keep the rest |
| No track metadata | Write copy that references the mix rather than the songs |
| Research note is stale | Do not present it as current; use it as background or drop it |
| Thumbnail frame extraction fails | Warn; the package still ships without an image |

## Example

Caption: "Night Drive into Paper Lanterns — made in Spotify." then the ask.
Hashtags spanning artist-specific, Spotify-specific, niche and broad. Pinned
comment naming both tracks and repeating the ask. Replies covering the second
track, how the blend was made, and an invitation to suggest the next pairing.

## Anti-patterns

- "You won't believe this transition." It promises a reaction the viewer has not
  had yet, and they scroll to check. Describe the pairing and let the audio do
  the work.
- Twenty hashtags because more is more. It dilutes any signal about which band
  performs and reads as spam.
- A pinned comment that repeats the caption. Use it for the thing that did not
  fit — usually the track IDs.

## Quality checklist

- [ ] Every factual claim points at a research note.
- [ ] The CTA is answerable from what the video showed.
- [ ] Hashtag bands are recorded, not just the tags.
- [ ] On-screen text is transcribed in order with its timings.

## Related skills

`artist-trend-researcher` gates every factual claim.
`searchable-onscreen-text` covers wording that doubles as a search phrase.
`evaluate-hook-clarity` checks whether the hook wording reads fast enough.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/posting.py`.
