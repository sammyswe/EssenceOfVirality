---
name: preference-experiment-manager
description: Govern how proposed creator preferences become permanent rules, and how experiments and posted results turn into hypotheses without overfitting. Use when approving a preference, recording post results, or reading whether a format is actually working.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: true
---

# Preference and experiment manager

Stage 9. The part of the system that decides what the pipeline learns.
Implementation: `production/pipeline/preferences.py`,
`production/pipeline/experiments.py`, `production/pipeline/analytics.py`.

## Purpose

Hold proposed rules until they have earned promotion, track what each render was
testing, and read posted results as evidence rather than as conclusions.

## When to invoke

- Approving or rejecting a proposed preference.
- Recording what a posted video did.
- Asking whether a format, duration band, hook type or hashtag strategy is
  actually working.
- Closing an experiment.

## When not to invoke

- To apply a one-off change. That is `feedback-interpreter`.
- To conclude anything from a single post. Nothing here supports that, by
  design.

## Inputs

Required for a preference: the proposal ID. For a post result: the video ID and
whichever metrics TikTok exposed.

Optional: an interpretation when closing an experiment, confounders worth
recording.

## Workflow

**Preferences.** A proposal is inert. It becomes active when the creator
approves it explicitly, or when the same preference has been proposed from three
separate feedback events. Approving one that contradicts an existing rule
supersedes it by link, and the superseded rule stays on disk, recoverable.

**Experiments.** Each render may carry a hypothesis: what changed, why, which
metric it targets, what it is compared against. It starts at
`awaiting_results`. Results are entered after posting; `more_evidence_required`
stays true until several posts agree.

**Analytics.** Post results are grouped by format family, duration band, hook
type and hashtag strategy. A group below the minimum size produces no comparison
at all. A group above it produces a comparison labelled with the number of posts
behind it and the confounders that could explain it just as well.

Done when every stored learning carries its evidence, its sample size, its
confidence and its confounders.

## Hard rules

- No preference is promoted from ambiguous feedback. Explicit approval or
  repeated consistent support, nothing else.
- Every rule change is version-controlled and the previous rule stays
  recoverable. Nothing is overwritten.
- No conclusion from a single video, however well it did.
- Correlation is never recorded as causation. A comparison states what it
  observed and what else could explain it.
- Confidence is low, medium or high. Never a percentage — false precision is
  worse than an honest range.
- A missing metric is unknown, never zero. TikTok does not expose everything,
  and treating a gap as a zero corrupts every average built on it.

## Recommendations

- Vary one thing per render. Two changes at once make the result unattributable
  and waste the post.
- Record confounders when the experiment is created, not when the result
  arrives. Hindsight finds the confounders that suit the conclusion.
- Prefer suggesting a follow-up experiment over declaring a finding. The point
  is to keep learning, not to close questions early.
- Watch for overfitting to the creator's most recent reaction. Three consistent
  signals is a preference; one strong one is a mood.

## Output

`CreatorPreference` (`schemas/creator-preference.schema.json`),
`ProductionExperiment` (`schemas/production-experiment.schema.json`), and
`TikTokPostResult` (`schemas/tiktok-post-result.schema.json`).

`analytics.report()` returns grouped comparisons, each with `evidence`,
`sample_size`, `confidence`, `confounders`, `suggested_experiment` and whether
it should affect future edits.

## Failure conditions

| Condition | Response |
| --- | --- |
| Approving a proposal that no longer exists | Refuse, naming what was searched |
| Approving one already approved | Refuse; state it is already in force |
| Group below the minimum size | Offer no comparison; state the size |
| Unknown preference key | Refuse the proposal; list the valid keys |
| Result recorded against an unknown experiment | Refuse; the link would be fictional |

## Example

Three posts on comedy hooks averaging higher completion than four clean
showcases. The report states the direction, the sample sizes, low confidence,
and the confounders — different tracks, different posting times, different
durations — then suggests the experiment that would separate them. It does not
recommend changing the default.

## Anti-patterns

- Hard-coding a conclusion from the account's best video. It was probably the
  tracks.
- Approving a preference because the creator said something once, emphatically.
  Emphasis is not repetition.
- Deleting a superseded rule. The reason it was replaced is only legible with
  both versions present.
- Averaging over posts where half the metric values are missing. State the
  coverage or do not state the average.

## Quality checklist

- [ ] Every promotion has explicit approval or three consistent proposals.
- [ ] Superseded rules are linked and still on disk.
- [ ] Every comparison states its sample size and confounders.
- [ ] No percentage confidence anywhere.
- [ ] Missing metrics are absent, not zero.

## Related skills

`feedback-interpreter` writes the proposals this governs.
`spotify-mix-creative-director` consumes approved preferences.
`propose-experiment` covers experiments about knowledge rather than about production settings.

## Change history

- 0.1.0 — first version, written alongside the preference, experiment and analytics modules.
