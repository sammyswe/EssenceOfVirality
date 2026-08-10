# Edit stage — Spotify mix overrides

Extends: `pipelines/screen-demo/edit-director`

## Edit decisions metadata

Set in `edit_decisions.metadata`:

```json
{
  "profile": "tiktok",
  "compose_target": {"width": 1080, "height": 1920, "fit": "cover"},
  "preserve_original_audio": true,
  "reframe_method": "center_crop"
}
```

## Permitted edits

- Trim dead time before the musical build (structural only)
- Reframe/crop for 9:16 Spotify UI legibility
- One short honest hook text overlay, outside blend window
- End trim after groove settles (do not cut mid-blend)

## Forbidden edits

- Speed changes to the transition
- EQ/denoise/limiting on the mix audio without creator approval
- Overlays during the blend window
- Replacing audio with trending Sounds

Run `evaluate-transition-payoff` on the edit plan before compose.
