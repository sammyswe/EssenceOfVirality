# Schemas

Canonical JSON Schemas (draft 2020-12) for every inter-agent artifact — the **single source of
truth** for artifact shapes (ADR 0004). Artifacts are YAML files carrying an `artifact_type`
field; `tools/validate_artifacts.py` maps that field to a schema via the registry below.

| `artifact_type` | Schema | ID prefix | Written to |
|---|---|---|---|
| `source_manifest` | `source-manifest.schema.json` | `src-` | `research/sources/<id>/` |
| `extraction_report` | `extraction-report.schema.json` | `ext-` | `research/sources/<id>/` |
| `claim_record` | `claim-record.schema.json` | `claim-` | `research/sources/<id>/claims/`, promoted to `evidence/claims/` (hypotheses to `evidence/hypotheses/`) |
| `evidence_assessment` | `evidence-assessment.schema.json` | `assess-` | `research/sources/<id>/assessments/` |
| `technique_record` | `technique-record.schema.json` | `tech-` | `research/sources/<id>/techniques/` |
| `contradiction_record` | `contradiction-record.schema.json` | `contra-` | `research/conflicts/`, standing ones in `evidence/contradictions/` |
| `knowledge_change_proposal` | `knowledge-change-proposal.schema.json` | `kcp-` | `research/sources/<id>/proposals/` |
| `skill_change_proposal` | `skill-change-proposal.schema.json` | `scp-` | `research/sources/<id>/proposals/` |
| `evaluation_report` | `evaluation-report.schema.json` | `eval-` | `evaluation/reports/` |
| `experiment_proposal` | `experiment-proposal.schema.json` | `exp-` | `evidence/experiments/` |
| `pull_request_summary` | `pull-request-summary.schema.json` | `prs-` | `research/sources/<id>/` |
| `analytics_observation` | `analytics-observation.schema.json` | `obs-` | `analytics/` (scaffold) |
| `video_production_manifest` | `video-production-manifest.schema.json` | `vpm-` | phase 3+ (scaffold) |
| `creative_minimum_report` | `creative-minimum-report.schema.json` | `cm-` | `outputs/quality-reports/` (live) |

`common.schema.json` holds the shared envelope (`artifact_type`, `id`, `created_at`,
`produced_by`, `inputs`, `version`, `human_review`, `derived_artifacts`) and shared enums
(confidence, evidence basis, domains, metric targets).

Conventions:

- IDs: `<prefix>-<yyyymmdd-or-context>-<slug>`, lowercase kebab-case. Uniqueness and reference
  integrity are enforced by `tools/check_ids.py`, not by the schemas.
- Schemas deliberately do **not** close objects with `additionalProperties: false`
  (OpenMontage's strict schemas proved brittle under churn); required fields carry the contract.
- Schema changes land via PR like everything else, bumping the top-level `description` where
  semantics change. The two `schema_maturity: scaffold` schemas (analytics, production manifest)
  are provisional until real data exists (ADR 0007).

What does not belong here: YAML instances (they live next to their workflows), rubrics
(evaluation/rubrics/), or OpenMontage's schemas (they stay upstream).
