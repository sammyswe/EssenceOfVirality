# The hook-overlay recipe

Revision date: 2026-08-18. The creator's structured recipe for producing a post
from exactly two supplied videos, with every editing decision owned by the
pipeline. Format template: `production/templates/hook-overlay.yaml`. Scroll-stop
craft lives in `.cursor/skills/experimental/produce-scroll-stop-hook/` and is
applied by `production/pipeline/scrollstop.py` on every hook-overlay plan. The
goal is two posts a day with the creator's effort limited to: generate a hook,
record a mix, verify lyrics and hook wording, post.

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

**Emoji caveat (interim limitation, not the target).** FFmpeg's drawtext cannot
render colour emoji with the fonts this pipeline ships; they would come out as
boxes, so the lyric renderer strips them with a warning. This is an interim
state only. **The creator has decided the paid path, not the free/zero-key one,
is this production line's target**: whatever provider connections the
emoji-capable OpenMontage Remotion caption backend needs will be supplied, and
matching the reference videos' emoji density in burned-in captions is required
work, not an optional extra (see
`docs/investigations/openmontage-prompt-gallery-review.md`). Until that backend
is wired in, put emoji in the TikTok caption text (posting package), which
renders them natively.

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

Hook and CTA wording beyond the template's baseline lives in the copy testing
bank (`production/config/copy-bank.yaml`, see
[`copy-bank.md`](copy-bank.md)): approved entries merge into the rotation,
drafts never render, and each render records which bank entry it used.

## What the final video looks like

Timeline (typical 25–45 s capture):

1. **0–~4 s — scroll-stop open.** Full-frame muted Higgsfield hook (fiction
   signal). Mix audio already playing underneath. Short subjective overlay
   text (from the matched hook profile, else the copy bank). Retained
   scroll-stop craft is recorded on the edit plan (pattern interrupt, depth
   motion, visual confirm, payoff re-hook, subjective stakes, fiction prop).
2. **~4 s — handover.** Overlay dissolves on a nearby beat; Spotify UI is
   fully visible by ~4.6 s (labels, BPM, waveform legible).
3. **Until the switch — Spotify capture, untrimmed.** Optional anticipation
   line (“wait for the switch”) if the open did not already say it. Optional
   karaoke lyrics only from a creator-verified `lyrics.yaml`. CTA may land in
   build / post-payoff / closing (rotated).
4. **Transition — untouched.** Mild zoom emphasis only; audio never altered
   beyond loudness normalisation.
5. **After —** rest of the capture + CTA if not already shown.

Deliverables per job: preview MP4, final MP4, thumbnail, posting package
(caption / hashtags / pinned comment). Dropbox `pull --run` uploads those to
`/spotify-mix-videos/renders/<video-id>/`.

## Dropbox production path

```bash
# Phone: drop the Spotify recording into /spotify-mix-videos/incoming/
# (optional: put a hook clip in the same folder; otherwise a library hook
#  is auto-attached from /spotify-mix-videos/hooks/library/)

./process-job dropbox pull --run
# imports → hook-overlay plan (scroll-stop techniques applied) → render →
# pushes preview/final/thumbnail to /spotify-mix-videos/renders/<id>/
```

Automation agents use the same command. Posting stays manual.

## What the creator still owns

1. Generating hook clips (a reusable bank; rotate them as experiments).
2. Recording the mix with labels, BPMs and waveform visible.
3. Verifying the drafted `lyrics.yaml` (words and timing) — one listen-through.
4. Approving hook/CTA wording where it makes a claim.
5. Posting, and feeding numbers back via `./process-job analytics record`.

Everything else — stitch, fade, beat snap, caption grouping, styling,
placement, CTA slotting, quality gates — is the pipeline's job.

## Ready for the first Spotify mix?

Yes — for a first Dropbox production run — when you have:

1. A 9:16 Spotify screen recording (labels + waveform visible, ~25–60 s) in
   `/spotify-mix-videos/incoming/` (or a folder with the mix + an optional hook).
2. At least one clip in `/spotify-mix-videos/hooks/library/` (ten are already
   there). Profiles for those clips are on `testing`, so profile overlay / CTA /
   caption trios drive the post.
3. Cloud Agent Secrets for Dropbox (already verified).
4. An Automation (or a manual `./process-job dropbox pull --run`) on branch
   `cursor/copy-bank-dropbox-cf50` until this PR merges.

Still optional / better after the first post: verified `lyrics.yaml` karaoke,
and retiring any profile overlay wording you dislike.

Not ready yet for: emoji-dense Remotion captions (interim FFmpeg drawtext),
TikTok auto-posting, or virality guarantees.

## Daily runbook (two posts)

```bash
# Dropbox (preferred)
#   drop capture (+ optional hook) into /spotify-mix-videos/incoming/
./process-job dropbox pull --run

# Or local
./process-job new job-XXX --recording <capture> --asset <hook-from-bank>
#   set preferred_format: hook-overlay; optional lyrics.yaml verified: true
./process-job jobs/incoming/job-XXX
./process-job dropbox push <video-id>
```

Revisions stay plain language:
`./process-job revise job-XXX "the captions are too small and the CTA should come before the drop"`.
