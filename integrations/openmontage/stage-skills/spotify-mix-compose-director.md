# Compose stage — Spotify mix overrides

Extends: `pipelines/screen-demo/compose-director`

## Render contract

Always set `profile: tiktok` on compose/encode operations.  
Output path: `projects/essence-of-virality/renders/final.mp4` (or per-run subfolder).

## Tool sequence (deterministic minimum)

1. `auto_reframe` with `target_aspect: portrait` (center crop — no face tracking for UI captures)
2. `video_compose` operation `encode` with `profile: tiktok` if reframed output is not already 1080×1920
3. Require `final_review` pass before marking compose complete

## Audio rules

- Map original capture audio through unchanged unless `preserve-spotify-mix-audio` approved processing
- Do not mux external music beds
- Loudness normalisation only to -14 LUFS when explicitly approved

## Pre-export gates

Run before presenting render:

1. `analyse-first-frame` on exported first frame
2. `evaluate-transition-payoff` with blend window from brief
3. `evaluate-hook-clarity` if hook text was burned in

Block export presentation if `final_review.status == fail`.
