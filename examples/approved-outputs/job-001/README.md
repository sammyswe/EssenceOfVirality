# job-001 — worked example

The artifacts a full pipeline run produces, kept as committed evidence. The MP4s
themselves are not here: media never enters git (`SECURITY.md`), and these were
rendered from a synthetic fixture anyway.

## Reproducing this run

```bash
python3 scripts/make-example-fixture.py --out examples/inputs/demo-mix
./process-job new job-001 --recording examples/inputs/demo-mix/spotify-screen-recording.mp4
./process-job job-001
./process-job revise job-001 "the opening is too slow, make the waveform larger, and remove the final zoom"
```

The fixture generator is deterministic, so a fresh clone reproduces the same
timings and the same decisions.

## What the two revisions show

`r1` is the pipeline's own choice with no feedback on file: clean showcase,
21.0s, transition at 7.0s, an 8% zoom pulse at the blend.

`r2` is the same job after one plain-language revision request. Each clause of
the feedback became a directive with a visible consequence:

| Feedback clause | Directive | Effect in r2 |
| --- | --- | --- |
| the opening is too slow | `shorten_lead_in` | lead-in 7.0s → 5.0s, duration 21.0s → 19.0s |
| make the waveform larger | `increase_spotify_area` | content zoom 0 → 0.40, interface reads 1.02x larger |
| remove the final zoom | `disable_zoom` | transition zoom pulse dropped |

The second clause is also the honest limit worth knowing about. In this capture
the waveform already spans 92% of the frame width, so cropping towards it can
only reach about 1.04x before the waveform's own ends would be cut. The render
notes in `job-001-r2-manifest.yaml` say so and name the opt-in setting
(`layout.waveform_end_trim`) that buys more by accepting that cut. Nothing
silently pretends the request was fully satisfied.

Both revisions also proposed lasting preferences rather than applying them:
`preferences/proposed/` holds them until `./process-job prefs approve <id>`.
