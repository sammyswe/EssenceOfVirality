---
name: feedback-interpreter
description: Convert the creator's plain-language notes on a render into structured directives, separating one-off fixes from lasting preferences. Use when handling revision feedback, when a directive was read wrongly, or when deciding whether feedback should become a permanent rule.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Feedback interpreter

Stage 8. Where "the opening is too slow" becomes a number. Implementation:
`production/pipeline/feedback.py` and `production/pipeline/revision.py`.

## Purpose

Read what the creator said, record it verbatim, derive the concrete changes it
implies, and decide whether any of it is a lasting rule rather than a note about
this one video.

## When to invoke

- The creator gives feedback on a render.
- A directive was derived wrongly and the rule that produced it needs fixing.
- Deciding whether repeated feedback has earned promotion to a preference.

## When not to invoke

- To apply a change the creator has not asked for. Improvements the creator did
  not request belong in an experiment, not in their revision.
- To edit a skill file. Feedback proposes; nothing here rewrites a skill.

## Inputs

Required: the feedback text, the job ID, and the revision it refers to.

Optional: the previous plan (for hook and CTA context), the current format and
text style.

## Workflow

1. Store the raw text verbatim in `feedback/raw/`. This happens first and always,
   before any interpretation, so the original survives a wrong reading.
2. Split the text into statements and match each against the directive rules.
3. For each match, record the action, its parameters, the affected stage, the
   trigger phrase and a confidence.
4. Collect statements that matched nothing as unmatched phrases. Do not guess at
   them, and do not drop them.
5. Classify scope: one-off, format-specific, artist-specific, asset-specific, or
   a potential permanent preference.
6. Set confidence from how much of the feedback was understood. More unmatched
   than matched means low confidence.
7. Where the wording suggests a lasting rule, write a preference *proposal*. It
   does not take effect.
8. Merge the directive history for this job — later feedback wins for the same
   action, and contradictory pairs cancel so the creator can undo by saying the
   opposite.
9. Translate directives into configuration overrides and re-plan.
10. Done when every directive names its trigger phrase and the record states
    whether approval is required.

## Hard rules

- Raw feedback is stored before interpretation, always, and never rewritten.
- Every directive names the phrase that produced it. An unattributable directive
  cannot be corrected, only argued with.
- Feedback never edits a skill file, a knowledge document or an approved
  preference. It proposes; the creator approves.
- Ambiguous feedback never becomes a permanent rule. Low confidence sets
  `approval_required`.
- Unmatched phrases are reported to the creator. Silence implies the pipeline
  understood, and it did not.
- Previous revisions stay on disk. A revision is an addition, never a
  replacement.

## Recommendations

- Prefer a narrow directive over a broad one. "Shorten the lead-in by two
  seconds" is checkable; "make it snappier" is not.
- When feedback names a format — "I like this, but only for funny videos" —
  scope the proposal to that format rather than globally.
- Make sure a directive can actually change the output in the current layout. A
  directive that adjusts a setting the active layout ignores looks applied and
  is not; the revision code and the renderer both have to agree it moved.

## Output

`CreatorFeedback` (`schemas/creator-feedback.schema.json`): `raw_feedback`,
`interpreted_issues`, `directives`, `scope`, `confidence`,
`approval_required`, `proposed_preferences`, `unmatched_phrases`,
`interpretation_notes`.

Directives translate into `RevisionAdjustments`: configuration overrides, an
optional format override, and a list of what was applied.

## Failure conditions

| Condition | Response |
| --- | --- |
| Nothing matched any rule | Record with no directives, confidence low, and say so |
| Feedback contradicts earlier feedback | Both records kept; the later directive wins; the change is recorded |
| Feedback references a job with no render | Refuse; there is nothing to revise |
| Directive would break a hard rule | Refuse that directive, keep the others, explain which and why |

## Example

"The opening is too slow, make the waveform larger, and remove the final zoom"
produces three directives — `shorten_lead_in`, `increase_spotify_area`,
`disable_zoom` — each naming its clause, plus two preference proposals held for
approval. The next render is 19s instead of 21s, with the transition at 5.0s
instead of 7.0s and no zoom pulse.

The second clause also shows the honest limit: the waveform already spans most
of the frame width, so the render note states how much enlargement was actually
achieved and names the opt-in setting that would go further.

## Anti-patterns

- Inferring a general rule from one video. "Never use this zoom again" is a rule;
  "the zoom is distracting here" is a note about this edit.
- Applying an unmatched phrase by best guess. The creator then has to detect a
  change they did not ask for and undo it.
- Rewriting an earlier feedback record to reflect a better reading. Add a new
  record; the history is the audit trail.

## Quality checklist

- [ ] Raw text stored before anything was interpreted.
- [ ] Every directive names its trigger phrase.
- [ ] Unmatched phrases reported, not dropped.
- [ ] Preference proposals written, not applied.
- [ ] Each directive measurably changed the render, or said why it could not.

## Related skills

`preference-experiment-manager` owns promotion of a proposal.
`tiktok-retention-editor` and `spotify-mix-creative-director` consume the overrides.
`mobile-job-orchestrator` runs the revision cycle.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/feedback.py`.
