---
name: artist-trend-researcher
description: Gather sourced, dated context about the artists and tracks in a mix so hooks and captions can reference something real. Use before writing copy that makes any factual claim, or when a hook idea depends on current artist news or a trend.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Artist and trend researcher

Stage 5. The gate between "this would be a great angle" and "this is true".
Implementation: `production/pipeline/research.py`.

## Purpose

Find current, verifiable context about the artists and tracks in a mix, record
it with its source and date, and state how it could be used — or why it cannot.

## When to invoke

- Before any copy that references a release, a tour, a trend, a meme, a lyric or
  a relationship between artists.
- When a hook idea depends on something being currently true.
- When a note in `research/tracks/` may have aged out of usefulness.

## When not to invoke

- For a video that makes no factual claim. Most clean showcases need none, and
  the pipeline runs fine without research.
- To decide the format. Research informs the angle; it does not pick the family.

## Inputs

Required per note: subject, kind, summary, source URL, publication date.

Optional: source name, event date, a caption angle, a hook angle.

## Workflow

1. Identify the subjects: both artists, both tracks, and any connection between
   them the job hints at.
2. Search for context of a recognised kind: recent release, tour announcement,
   viral clip, meme, fan discussion, lyric or theme, artist connection, track
   contrast, TikTok trend, upcoming event, cultural context.
3. For each candidate, record the source URL and the publication date. A claim
   without both is not a note and is rejected at write time.
4. Compute its age. Past the staleness threshold it is background only, and the
   note says so; it may not be presented as current.
5. State the angle: how a hook or caption could use it, in one sentence.
6. Store the note. Notes accumulate per subject and are reused across jobs.
7. Done when every factual claim the copy intends to make has a note behind it,
   or the claim has been dropped.

## Hard rules

- No note without a source URL and a publication date. There is no exception for
  "everyone knows this".
- Never present a stale item as current. Age is recorded and enforced, not left
  to judgement in the moment.
- Never invent artist news, trends, relationships or quotations. A fabricated
  angle is the one failure mode that damages the account rather than the video.
- Never force context into a video that does not need it. A weak trend reference
  is worse than none: it dates the video and reads as chasing.
- A note with a future publication date is rejected. It is a data-entry error.

## Recommendations

- Prefer primary sources: the artist's own post, the label's announcement, the
  event listing.
- A genuine contrast between the two tracks is often the strongest available
  angle and needs no external source beyond the tracks themselves.
- Record the angle when the note is written, not later. The connection is
  obvious now and will not be in three weeks.
- Re-check a note before reusing it on a new job. Tours end.

## Output

`TrackResearchNote` (`schemas/track-research-note.schema.json`): `subject`,
`kind`, `summary`, `source_url`, `source_name`, `published_date`,
`event_date`, `caption_angle`, `hook_angle`, `usable_in_copy`,
`staleness_note`, `warnings`.

Add with `./process-job research add`, read with `./process-job research brief`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Missing URL or publication date | Reject the note; nothing is stored |
| Publication date in the future | Reject; flag as a data-entry error |
| Past the staleness threshold | Store with `usable_in_copy: false` and a staleness note |
| Unrecognised kind | Reject, listing the accepted kinds |
| No network access | Proceed without research; the copy makes no factual claim |

## Example

A note recording that an artist announced a UK tour on a dated label post, with
the hook angle "the second track is from someone playing here in spring". Usable
until the tour is over, at which point its age makes it background.

A counterexample: "this pairing is trending on TikTok right now" with no source.
Rejected. The copy falls back to the pairing itself, which needs no defending.

## Anti-patterns

- Writing the caption first and looking for a source afterwards. That is how a
  half-remembered fact becomes an on-screen claim.
- Citing an aggregator that cites the real source. Link the original; the
  aggregator may be wrong about what it summarised.
- Keeping a stale note "just in case". It will be reused by someone who does not
  read the staleness field.

## Quality checklist

- [ ] Every note has a URL and a publication date.
- [ ] Age has been computed and acted on.
- [ ] The angle is stated in one sentence.
- [ ] Every factual claim in the copy points at a note ID.

## Related skills

`tiktok-copywriter` may only make claims this stage has backed.
`spotify-mix-creative-director` uses angles from here for hook concepts.
`ingest-source` is the route for durable knowledge, as opposed to per-job context.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/research.py`.
