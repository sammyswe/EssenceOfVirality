# Idea stage — Spotify mix overrides

Extends: `pipelines/screen-demo/idea-director`

## Mandatory brief fields

Set `metadata.production_mode` to `real_capture`.  
Set `target_platform` to `tiktok`.  
Set `style` to `spotify-mix-tiktok`.  
Record `metadata.software_shown: ["Spotify"]`.  
Record blend window timestamps in `metadata.blend_window_seconds` when known.

## Decision checklist

Before completing the idea checkpoint:

1. Run `preserve-spotify-mix-audio` on the source capture (or note pending review).
2. Confirm duration target is 10–40 s unless creator overrides.
3. Lock `render_runtime`: prefer `ffmpeg` for minimal edits; use `remotion` only when
   word-highlight captions are required and approved.
4. Identify hook strategy — one honest cue, ≤ 8 words, cleared before blend window.

## Anti-patterns

- Promising a transition the capture does not contain
- Choosing synthetic_terminal mode (this niche uses real captures only)
