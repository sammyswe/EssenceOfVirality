# evaluation/reports/

`evaluation_report` artifacts (schema: `schemas/evaluation-report.schema.json`) produced by the
evaluation agent for source ingestions, skill changes and knowledge changes.

- **Who writes**: the evaluation agent only, via the workflows.
- **What belongs**: schema-valid `eval-*.yaml` files. **What does not**: prose essays (put a
  `details` string in a check entry), regression bundles (use `../regression/`).
- **Validation**: schema-validated by CI; every report must fill
  `cannot_validate_without_real_data`.
- Reports are review inputs for PRs, never CI gates (ADR 0006).
- Source-controlled: yes.
