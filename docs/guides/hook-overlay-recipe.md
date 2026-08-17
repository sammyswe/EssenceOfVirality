# The hook-overlay recipe

Revision date: 2026-08-17. The creator's structured recipe for producing a post
from exactly two supplied videos, with every editing decision owned by the
pipeline. Format template: `production/templates/hook-overlay.yaml`. The goal is
two posts a day with the creator's effort limited to: generate a hook, record a
mix, verify lyrics and hook wording, post.

## The two artifacts

| Artifact | Who makes it | Rules |
| --- | --- | --- |
| **Hook clip** (~4 s, 9:16) | Creator, with Higgsfield, using their own prompts | Obviously stylised AI scene (the ai-scene honesty rules apply: no fabricated reality, no real-person likeness passed off as an endorsement). Reused across many posts; a bank of hooks is expected. |
| **Spotify capture** (25–60 s, 9:16) | Creator, screen recording | Already carries everything on screen: track names, artwork, BPMs, waveforms. The pipeline does not crop it beyond the crop profile and does not alter its audio beyond loudness normalisation. |

Job shape:

```bash
./process-job new job-00N \
  --recording ~/mix-capture.mp4 \
  --asset ~/hook-bank/stussy-style-open.mp4
```

then in `job.yaml`:

```yaml
additional_assets:
  - {path: stussy-style-open.mp4, role: hook}
creative_direction:
  preferred_format: hook-overlay
```

## Invariants (the strict rules)

1. **The mix audio plays from the very first frame.** The hook clip is a muted
   full-frame overlay on top of the already-playing recording; the render maps
   audio only from the Spotify capture. This is enforced by the renderer's
   single-audio-input design, not by convention.
2. **Neither supplied video is cut.** `pacing.use_full_recording` renders the
   whole capture; the hook clip plays to its handover point. Output length is
   whatever the capture is (25–60 s admitted by the quality window).
3. **The handover is designed, not spliced.** The overlay's end is snapped to
   the nearest detected beat (within ±0.6 s of the 4 s target) and dissolves
   out over 0.3 s instead of hard-cutting.
4. **The Spotify surface is visible by 4.6 s** and nothing covers it during the
   transition window. Song labels and waveform are never obscured by text —
   the placement search moves or drops a caption before it violates this.
5. **Lyric captions render only from a creator-verified sheet.** No sheet, or
   `verified: false` → the render proceeds without karaoke and says so. Wrong
   lyrics never ship silently.
6. **One transition, untouched.** Unchanged from the pipeline's hard rules.

## On-screen captions

### Hook text (0.1 s – ~2.7 s, over the AI clip)

Text-claim hooks drawn from the template bank (`hook_patterns`), rotated
deterministically so consecutive jobs do not repeat. Subjective quality claims
only ("spotify mixes should not sound this good"); nothing that asserts an
unverifiable fact. The creator reviews wording before posting — posting stays
manual. Supply an exact hook with `creative_direction.hook` to override.

### Word-timed lyric karaoke

The job folder carries a `lyrics.yaml`:

```yaml
verified: false          # the creator flips this to true after checking
source_urls:
  - "https://…"          # where the words were checked
group_max_words: 3
words:
  - {text: "GOTTA", start: 12.40, end: 12.72}
  - {text: "LET",   start: 12.72, end: 12.95}
  - {text: "THE",   start: 12.95, end: 13.10}
  - {text: "MUSIC", start: 13.10, end: 13.62}
```

- Times are seconds **in the source recording**. The agent preparing the job
  drafts this sheet — looking the lyrics up online and citing the source — and
  the creator verifies words *and* timing before setting `verified: true`.
- Words are grouped (max 3, or a vocal pause > 0.6 s) into short caption
  windows, held briefly for readability, and colour-rotated
  (white → cyan → pink, heavy black outline, no plate) so the sequence reads as
  animated karaoke.
- Captions sit in the lower-middle band (`lyric` anchor) and are moved or
  dropped rather than allowed to cover song info or the waveform.
- Groups that fall under the opaque hook overlay are skipped.

**Emoji caveat (honest limitation).** FFmpeg's drawtext cannot render colour
emoji with the fonts this pipeline ships; they would come out as boxes. The
lyric renderer strips them with a warning. Matching the reference videos' emoji
density in burned-in captions needs an emoji-capable text backend — the
OpenMontage Remotion caption path is the designated upgrade (see
`docs/investigations/openmontage-prompt-gallery-review.md`). Until then, put
emoji in the TikTok caption text (posting package), which renders them natively.

### Call to action

Drawn from the template bank; the slot rotates per revision between:

| Slot | When | Why it might work |
| --- | --- | --- |
| `build` | after the hook, before the transition | captive audience waiting for the drop |
| `post_payoff` | just after the blend lands | goodwill moment |
| `closing` | final seconds | classic end-card |

The chosen slot is recorded on the edit plan as a decision and the render's
experiment record, so analytics can later compare slots on real numbers.
Milestone promises ("playlist link at 100 followers") are commitments, not
template text — supply them per job via `creative_direction.cta` when the
promise is real.

## What the creator still owns

1. Generating hook clips (a reusable bank; rotate them as experiments).
2. Recording the mix with labels, BPMs and waveform visible.
3. Verifying the drafted `lyrics.yaml` (words and timing) — one listen-through.
4. Approving hook/CTA wording where it makes a claim.
5. Posting, and feeding numbers back via `./process-job analytics record`.

Everything else — stitch, fade, beat snap, caption grouping, styling,
placement, CTA slotting, quality gates — is the pipeline's job.

## Daily runbook (two posts)

```bash
# per post
./process-job new job-XXX --recording <capture> --asset <hook-from-bank>
#   agent drafts lyrics.yaml, sets preferred_format: hook-overlay
#   creator verifies lyrics (verified: true), confirms hook wording
./process-job jobs/incoming/job-XXX
./process-job deliver <video-id>    # in a cloud agent: stages preview + final
#   creator posts manually; later records analytics
```

Revisions stay plain-language: `./process-job revise job-XXX "the captions are
too small and the CTA should come before the drop"`.
