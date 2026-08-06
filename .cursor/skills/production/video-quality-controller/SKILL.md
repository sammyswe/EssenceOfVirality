---
name: video-quality-controller
description: Run the deterministic checks that decide whether a render is post-ready, covering geometry, audio integrity, safe zones, Spotify visibility and source-file integrity. Use after every render, when a check fails and the cause is unclear, or when adding a new check.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Video quality controller

Stage 7. The last thing between a render and the creator's phone.
Implementation: `production/pipeline/quality.py`, hard rules in
`production/pipeline/rules.py`.

## Purpose

Measure the finished file against the plan and the hard rules, and say plainly
whether it can be posted.

## When to invoke

- After every render, without exception.
- When a check fails and the cause needs tracing to a decision.
- When adding a check for a failure mode that reached the creator.

## When not to invoke

- To judge whether the video is *good*. These checks measure correctness, not
  quality of idea. A dull video can pass every one of them.
- To predict performance. Nothing here forecasts anything.

## Inputs

Required: the rendered file, the `EditPlan`, the `InputReport`, the
`RenderResult`, and hashes of the source files taken before the run.

## Workflow

1. File and container: exists, opens, carries a decodable video stream.
2. Geometry: 1080x1920, correct frame rate, correct pixel format.
3. Duration: inside the configured window, and matching the plan.
4. Audio: present; exactly one stream; sourced from the Spotify recording;
   no clipping; loudness measured and recorded; video and audio spans agree.
5. Frames: no unintended black stretches; no frozen stretches; the opening frame
   carries visible information.
6. Spotify: occupies at least the minimum share of the frame; the crop keeps the
   song labels and waveform whole; nothing covers the surface at the transition.
7. Text: every cue inside the safe area; none over a hard protected region; none
   below the readable size.
8. Sources: hash each input again and compare. A changed hash is a hard failure.
9. Done when every check has a status and a detail, and the report states
   `post_ready` with the hard-rule violations listed.

## Hard rules

- Any hard-rule violation fails the render. There is no override flag.
- A changed source hash fails the run outright. The pipeline never writes to the
  creator's media, and this is how that is proven rather than asserted.
- Never report a check as passing when it could not be run. An unmeasurable
  check is a warning that says so.
- Never describe a render as likely to perform. The vocabulary is retention
  hypothesis, creative rationale, expected advantage, experiment, confidence.

The single deliberate exception: when `layout.waveform_end_trim` is set, a crop
into the waveform's ends warns instead of failing, naming the setting that
allowed it. The creator opted in explicitly; the report still says what happened.

## Recommendations

- Attach a measurement to every check, not just a verdict. "-8.04 dBTP against a
  -0.5 ceiling" is actionable; "no clipping" is not.
- Use FFmpeg's own detectors — `blackdetect`, `freezedetect`, `signalstats` —
  over hand-rolled sampling. A mostly static Spotify interface defeats naive
  frame-difference heuristics.
- When a check fails, name the plan decision that caused it. The creator should
  not have to work backwards from a filter graph.

## Output

`QualityReport` (`schemas/quality-report.schema.json`): `status`,
`post_ready`, `summary`, `hard_rule_violations`, `checks`,
`source_fingerprints`. Each check carries `id`, `description`, `status`,
`detail` and an optional `measurement`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Render file missing | Fail immediately; nothing else is measurable |
| Second audio stream present | Hard-rule violation; the mix is not the only source |
| Source hash changed | Hard-rule violation; the run modified an input |
| Text over a hard region | Hard-rule violation naming the cue and the region |
| Spotify below the minimum share | Hard-rule violation naming the fraction and the floor |
| A measurement cannot be taken | Warn, stating what could not be measured and why |

## Example

A passing report: 25 checks, no warnings, no failures. Loudness -13.77 LUFS,
true peak -8.04 dBTP, black 0.0% of the video, Spotify occupying 100% of the
frame, song labels and waveform entirely inside the crop.

A failing one: `song_info_unobstructed` fails naming the CTA cue and the region
it covers. The fix is in the plan's text placement, not in the renderer, and the
detail says so.

## Anti-patterns

- Downgrading a hard rule to a warning to get a video out. The rules exist
  because each one has already produced a video worth not posting.
- A check with no measurement. Six months later nobody can tell whether the
  threshold was close or comfortable.
- Adding a subjective check. If it cannot be measured the same way twice, it
  belongs to a review skill, not to this stage.

## Quality checklist

- [ ] Every check has a status and a detail.
- [ ] Hard-rule violations are listed separately from warnings.
- [ ] `post_ready` is false whenever any check failed.
- [ ] Source fingerprints were compared, not just recorded.

## Related skills

`openmontage-editor` produces the file this measures.
`mobile-job-orchestrator` decides what happens to a job that fails here.
`preserve-spotify-mix-audio` owns the judgement behind the audio thresholds.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/quality.py`.
