---
name: spotify-mix-creative-director
description: Choose the format family, hook and supporting-clip concepts for a Spotify mix video, and write Higgsfield prompts for footage the creator should generate. Use when planning a new edit, when a hook feels generic, or when deciding what AI clip to make before shooting anything.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Spotify mix creative director

Stage 2. Decides what kind of video this is. Implementation:
`production/pipeline/creative.py`, format families in `production/templates/`.

## Purpose

Interpret the tracks and the supplied assets, pick a format family, generate a
hook that the video can actually deliver on, and — where useful — describe the
supporting footage worth creating.

## When to invoke

- Planning a new edit, after inspection and before timing or layout.
- When the creator says a hook is generic, repetitive or overclaiming.
- When deciding what AI clip to generate for an upcoming mix.
- When a format keeps being chosen and the creator wants to know why.

## When not to invoke

- To place text or time cuts. That is `tiktok-retention-editor`.
- To write the caption or hashtags. That is `tiktok-copywriter`.
- To assert a fact about an artist. That needs `artist-trend-researcher` first.

## Inputs

Required: the `InputReport`, the `JobSpec` (tracks, mood, preferred format,
must-include and avoid lists), and resolved creator preferences.

Optional: research note IDs for this job's artists, an explicit
`creative_direction.preferred_format`.

## Workflow

1. Score every format family against the usable assets, the mood hint and
   approved preferences. Record why each rejected family lost.
2. Refuse any family whose hook makes a claim the inputs cannot support. The
   unexpected-combination family asserts two tracks clash; without genre or
   metadata evidence of a contrast, it is not eligible.
3. Choose the hook from the winning family's candidates, excluding any used in
   the recent past, and record how many candidates were valid.
4. Choose a call to action whose answer the video actually gives the viewer
   something to say about.
5. Where a supporting clip would help, describe it: the idea, what happens in
   the first second, what happens at the transition, duration, framing, whether
   it shares the screen, and a ready-to-paste Higgsfield prompt with its
   negatives.
6. Done when the format, hook, CTA and rationale are all recorded on the plan
   and every rejected family has a stated reason.

## Hard rules

- Never state something about an artist, track or trend that a sourced research
  note does not support. No invented releases, tours, feuds or quotations.
- Never promise a result. A format carries a retention hypothesis, not a claim
  about reach.
- Never choose a family the supplied assets cannot fill. A picture-in-picture
  format with no second clip is a broken edit, not a fallback.
- Never present AI-generated footage as real events. Parody and obvious fiction
  are fine; fabricated reality is not.
- The Spotify surface stays legible in every family. A format that would hide
  the song labels or waveform is not a format, it is a bug.

## Recommendations

- Prefer the family that uses what was actually supplied over the family that
  scores highest in the abstract.
- Rotate hook wording. A hook that worked twice is a pattern; the same hook five
  times is a rut, and the account reads as automated.
- Let contrast between the tracks drive the concept when the metadata supports
  it — it is the most honest source of surprise available.
- Keep the first second doing one thing. Two competing ideas at the open read as
  neither.

## Output

Contributions to the `EditPlan`: `format_family`, `template_name`, `hook_text`,
`cta_text`, `creative_rationale`, `decisions` (including one per rejected
family), `retention_hypothesis`, `experiment`.

Clip concepts are returned as a list, each with `idea`, `first_second`,
`at_transition`, `duration_seconds`, `framing`, `spotify_placement`,
`higgsfield_prompt`, `avoid`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Job names a format its assets cannot fill | Raise `CreativeError` naming the shortfall |
| No family fits at all | Raise, suggesting `clean-showcase` explicitly |
| Every hook candidate recently used | Fall back to the most neutral candidate and warn |
| Research enabled but no notes match | Warn; write copy that makes no factual claim |

## Example

Two tracks with different stated genres and one supplied clip: comedy-hook wins
on the funny mood and the available asset; unexpected-combination stays eligible
because the genres genuinely differ. The plan records both, so the choice can be
argued with.

The same job without genres: unexpected-combination is refused with "hook
asserts the tracks clash, but no track metadata confirms a contrast — would risk
a false claim". The pipeline declines a small creative angle rather than make an
unsupported claim.

## Anti-patterns

- "This should not work" over two tracks that plainly do work together. The
  hook writes a cheque the video cannot cash and the comments say so. Use a
  contrast the metadata supports, or a different family.
- A full-screen AI opening long enough that the viewer forgets Spotify is the
  point. Hand over before the transition window.
- Ranking a family highly because it is new. Novelty is a reason to run an
  experiment, not a reason to score higher.

## Quality checklist

- [ ] Every rejected family has a recorded reason.
- [ ] The hook can be delivered by what is actually in the video.
- [ ] No factual claim without a research reference.
- [ ] The retention hypothesis names a viewer behaviour, not a reach outcome.

## Related skills

`spotify-input-inspector` supplies the report this reads.
`tiktok-retention-editor` turns the choice into timing and layout.
`evaluate-hook-clarity` and `analyse-first-frame` diagnose a hook that underperforms.
`artist-trend-researcher` is a precondition for any factual angle.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/creative.py`.
