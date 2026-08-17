# OpenMontage PROMPT_GALLERY review

Date: 2026-08-17. Requested by the creator: a closer read of upstream
OpenMontage practice for anything this repository's pipeline should be using.
Source reviewed: `PROMPT_GALLERY.md` on the upstream `main` branch (retrieved
2026-08-17; our integration pin remains the ADR 0001 commit — this review reads
docs, it does not re-pin).

## What the gallery actually is

A catalogue of tested prompts for OpenMontage's narrated-explainer pipelines:
data explainers, anime-style animation from stills, HyperFrames (HTML/GSAP)
motion graphics, and full video-gen productions. Almost all of it presumes a
narrator, a script and generated visuals — a different product from ours, where
the mix audio is sacrosanct and the Spotify capture is the evidence.

The creator has also decided the **free path is irrelevant**: hooks are made
with their Higgsfield subscription, not with OpenMontage's zero-key
generation stack. That removes the Piper/stock-media/FLUX guidance from
consideration entirely.

## What transfers to this pipeline

| Upstream practice | Where it lands here |
| --- | --- |
| **Word-by-word captions synced to audio** ("TikTok-style word-by-word captions synced to narration", via `subtitle_gen` + `remotion_caption_burn`) | The strongest confirmation that word-timed captions are a first-class upstream capability. Our karaoke implementation (`production/pipeline/lyrics.py`) is the FFmpeg-fallback equivalent, consistent with how every other capability here has an FFmpeg fallback. The Remotion caption burn is the designated upgrade path when emoji and per-word highlight animation are wanted — it renders real text with real fonts, including emoji, which drawtext cannot. |
| **Kinetic typography as the retention layer** (HyperFrames: "SplitText-style word reveals", staggered callouts) | Validates the reference videos' pattern we are copying: over a mostly static surface, animated text is the motion. Phase-appropriate version: colour-rotated lyric groups. A HyperFrames-composited caption layer is a possible later backend, but it introduces Node ≥ 22 + headless Chrome into the render path — not worth it before the simple version has posted results. |
| **Be specific about visual components; specify duration; name the audience** (prompting tips) | Already our house style for Higgsfield hook prompts (concrete subject, camera, palette, end-on-a-beat, negatives). Adopted into the hook-prompt guidance rather than left implicit. |
| **`hyperframes lint`/`validate` gates before render** | Same shape as our deterministic validators + 25 quality checks. No action needed; noted as convergent design. |

## What does not transfer

- **Narration-first structure** (scripts, TTS voices, word budgets per duration):
  our audio is the mix; there is no narrator and never will be one mid-mix.
- **Zero-key generation paths** (Piper TTS, stock media, FLUX stills): the
  creator uses Higgsfield for all generated footage.
- **Registry blocks / charts / stat cards**: explainer furniture with no place
  over a Spotify capture.
- **Avatar spokesperson flows**: violates the anonymity preference.

## Actions taken

1. Karaoke captions implemented as FFmpeg drawtext cues with the Remotion
   caption burn noted as the emoji/per-word-highlight upgrade path
   (`docs/guides/hook-overlay-recipe.md`).
2. Hook-prompt guidance keeps the gallery's specificity discipline (subject,
   motion, palette, duration, negatives, end-on-a-beat).

## Actions deliberately not taken

- No re-pin: the gallery is documentation; nothing here changes the dependency
  surface assessed in ADR 0001. `/review-openmontage-integration` remains the
  route for a deliberate upgrade.
- No HyperFrames adoption: heavy new runtime for a marginal gain over the
  implemented caption layer, before any posted-results evidence.
