# evidence/

Promoted, cross-source epistemic records — the machine-readable memory of what the project
believes, doubts and wants to test. Everything is source-controlled YAML validated against
`schemas/` by CI. Storage format rationale: ADR 0003.

## Layout

| Directory | Contains | Written by |
|---|---|---|
| `claims/` | Promoted `claim_record`s (facts, findings, heuristics, patterns, anecdotes, constraints, preferences, experiment results) | PR curator, via reviewed PRs only |
| `hypotheses/` | `claim_record`s with `claim_type: hypothesis` — kept separate because they are test targets, not accepted knowledge | same |
| `contradictions/` | Standing `contradiction_record`s (unresolved or coexisting disagreements) | contradiction-synthesis agent, via PR |
| `experiments/` | `experiment_proposal`s and, later, their results | via PR |

## Rules

- Promotion into this directory happens **only through a reviewed PR** (ADR 0006). Working
  copies live in `research/sources/<id>/`.
- Records are superseded, never mutated in substance: new record + `supersedes`/`superseded_by`
  links (ADR 0003). Status changes (`active → disputed` etc.) are the only in-place edits.
- Contradictions are preserved until an experiment, a superseding source, or the creator resolves
  them. Silent resolution is prohibited.
- No time decay: old records stay `active` while evidence supports them; `platform_dependent:
  true` marks revalidation candidates.
- `knowledge/` documents must cite records here by ID rather than restating them.
