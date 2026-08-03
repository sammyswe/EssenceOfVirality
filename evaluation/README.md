# evaluation/

The lightweight phase-one evaluation harness. The creator remains the final quality gate; this
harness makes their review cheap and evidence-based. No universal "virality score" exists here —
rubrics are multidimensional by design.

## Layout

| Path | Purpose |
|---|---|
| `rubrics/` | Multidimensional quality rubrics (skill quality, video evaluation) |
| `fixtures/` | Six fixed hypothetical source videos + expected diagnoses (structural checks: `tools/run_fixtures.py`) |
| `regression/` | Before/after records for skill changes (`evaluation_report` YAML + prose diffs) |
| `reports/` | `evaluation_report` artifacts from the evaluation agent |

## Two evaluation tiers (ADR 0006)

1. **Deterministic (CI)**: schema validation, skill lint, ID integrity, fixture structure,
   markdownlint, secret scan, pytest. Runs on every PR; no model calls.
2. **Agent-driven (on demand)**: running skills against fixtures, before/after regression with
   critic review, instruction-quality assessment, human review packet. Invoked by
   `/evaluate-skill`; results are committed to `reports/` as review inputs, never CI gates.

## Regression rule

When a skill changes: run old and new versions against the same fixtures, record material
differences, have the skill critic identify improvements *and* regressions. A newer or longer
output is not presumed better.

## Honesty rule

Every evaluation report must fill `cannot_validate_without_real_data` — what only real TikTok
performance can confirm. Fixture success is necessary, not sufficient.
