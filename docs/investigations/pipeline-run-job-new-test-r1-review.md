# Pipeline run review — `job-new-test` r1

| | |
|---|---|
| Date | 2026-08-10 |
| Job | `job-new-test` revision 1 |
| Source | `new.MOV` (ReplayKit Spotify screen recording, 33.7s, 1320×2868 HEVC) |
| Output | `outputs/final/job-new-test-r1.mp4` |
| Pipeline result | **Technical success** — quality pass (25/25), job moved to `jobs/review/` |
| Creator verdict | **Not competitive.** This is nowhere near a TikTok feed-ready creative product. A clean technical export is not a video people will stop for, finish, or share. |

This review separates three layers that the pipeline currently conflates:

1. **Did the machinery run?** Yes.
2. **Is the file uploadable?** Yes (`post_ready: true`).
3. **Would this hold attention in a For You feed among house / Spotify-mix content?** No — not as shipped.

Nothing below claims knowledge of TikTok’s private ranking. The claim is about **viewer behaviour fitness**: scroll-stop, curiosity, payoff clarity, and comment bait that feels earned. On those axes, r1 fails. Treating a broken-file gate as “success” taught the wrong lesson about what this harness is for.

## What worked (machinery)

End-to-end run completed after tooling was available:

- Job scaffolding from a raw `.MOV` (`./process-job new` → inspect → render).
- Probe / crop: detected `vertical_trimmed_chrome`, transition at **14.5s** (`spectral_flux_novelty`, high confidence), tempo ~132.5 BPM.
- Edit window: source 7.5s–28.5s → **21.0s** output with transition at **7.0s** (payoff at ~33% of runtime — structurally fine).
- Audio: loudnorm from measured −11.86 LUFS / +1.29 dBTP to ~−14 LUFS / safe true peak.
- Export: 1080×1920 h264/aac, single Spotify audio stream, sources unmodified.
- Artifacts written: final, preview, edit plan, posting package, quality report, manifest, experiment record.

**Conclusion:** the production harness is real. FFmpeg fallbacks without OpenMontage are enough to ship a file. That is necessary and nowhere near sufficient.

## What “quality pass” actually measured

All 25 checks are **conformance** checks: geometry, duration window, audio integrity, safe zones, Spotify visibility, no black/frozen stretches, transition not cut, CTA on screen long enough, codec suitability.

The quality report correctly says it does not predict distribution. That means **the gate the pipeline celebrates is orthogonal to the creator objective** (views → followers → shares → comments → likes). Passing quality today means “won’t get rejected for being a broken file,” not “worth posting.”

Calling the job `review` / `post_ready` after this gate is misleading. It should mean “technically valid draft,” not “ready for the feed.” Until a creative minimum is enforced, every recording-only blank-metadata job will keep graduating into `jobs/review/` looking green and reading dead.

## Why this video will not compete

1. **Creative collapse into empty-asset default** — Format `clean-showcase` because five supporting-clip formats were rejected (0 clips) and unexpected-combination refused without track metadata. Recording-only jobs silently ship the weakest format.
2. **Hook is generic** — “wait for the switch”; no track/artist/genre promise; thumbnail repeats the same line. Nothing names the pairing a house-music viewer would care about.
3. **CTA/caption filler** — “which song won?” with blank tracks is unanswerable; generic hashtag bag. Comment bait without a real choice is noise.
4. **Visual craft minimal / preference drift** — Zoom emphasis disabled by preference, but retention hypothesis still claims zoom-marked payoff. Hypothesis and render disagree; the experiment record overstates what was tested.
5. **Niche identity invisible** — No named pairing, craft signal, or series cue. A stranger scrolling house content has no reason to stop.
6. **Experiment framing overstates the test** — Default fallback format is not a useful format experiment. Logging it as one pretends a forced default was a creative choice.

## Pipeline product gaps (P0 — implement these)

| Priority | Gap | Direction |
|---|---|---|
| P0 | Quality gate ≠ feed fitness | Split gates: `technically_valid` vs `creative_minimum` (hook specificity, track metadata present or explicit waiver, format not empty-default unless forced) |
| P0 | Recording-only → forced weak format | Block or warn-hard when high-value formats need missing assets; surface “add a hook clip / fill tracks” before treating as review-ready |
| P0 | Blank track metadata | Require `tracks.first/second` title+artist (or explicit waiver in job.yaml) before calling a job review-ready |

Also fix P1 if cheap in the same PR: recompute retention hypothesis from the *actual* plan (never cite disabled emphasis).

## Behaviour this review expects after the fix

| Situation | Before | After |
|---|---|---|
| Recording-only, blank tracks, auto format | Technical 25/25 → `review`, `post_ready: true` | Technical pass possible; `creative_minimum` fails → status `needs_creative_input`; stays out of `jobs/review/`; report lists fill tracks / add clip / waive |
| Tracks filled, clip supplied, or explicit force/waiver | Same path as today toward review | `creative_minimum` can pass; `post_ready` only when both gates pass |
| Zoom preference disables emphasis | Hypothesis still mentions zoom-marked payoff | Hypothesis rewritten from the actual plan |

## Verdict

The pipeline works as a render factory. It does not yet work as a growth system. r1 is a fixture proof, not a model of what to post. Until creative minimum is a hard gate, “success” will keep meaning broken-file prevention only — and that is how more non-competitive videos will ship looking like wins.
