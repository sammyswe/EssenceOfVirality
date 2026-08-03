# research/conflicts/

Working `contradiction_record`s spanning sources, written by the contradiction-synthesis agent
during ingestion/comparison runs. Standing contradictions are promoted to
`evidence/contradictions/` by the PR. Schema: `schemas/contradiction-record.schema.json`;
rules: `../README.md` and `.cursor/rules/evidence.mdc`.

Empty right now: the vertical-slice ingestion found no contradictions (the store was empty — see
`evaluation/reports/eval-20260803-foryou-ingestion.yaml`). The record format is proven by the
synthetic examples in `tests/fixtures/artifacts/`.
