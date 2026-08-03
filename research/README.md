# research/

Per-source working artifacts — the audit trail of every ingestion. Everything here is
source-controlled YAML validated against `schemas/` by CI.

## Layout

```
research/
  sources/<source-id>/        # one directory per ingested source
    manifest.yaml             # source_manifest
    extraction.yaml           # extraction_report
    claims/*.yaml             # claim_record (working copies)
    assessments/*.yaml        # evidence_assessment
    techniques/*.yaml         # technique_record
    proposals/*.yaml          # knowledge_change_proposal / skill_change_proposal
    pr-summary.yaml           # pull_request_summary
  conflicts/                  # contradiction_record spanning sources (working)
  rejected/                   # rejected sources/claims WITH recorded reasons
```

## Rules

- **Who writes**: the research-intake coordinator creates `sources/<id>/` and the manifest;
  specialist agents add their stage artifacts via the orchestrated workflows. Humans normally
  don't edit here except to correct metadata.
- **What belongs**: extracted findings, structured notes, metadata, assessments. **What does
  not**: complete copyrighted source copies, downloaded media, secrets
  (see `docs/guides/content-and-source-handling.md`).
- Nothing is deleted silently: rejected material moves to `rejected/` with a reason recorded in
  the artifact's `notes`.
- Working claims here are **not** accepted knowledge. Acceptance = promotion to `evidence/` and
  citation from `knowledge/`, which happens only through a reviewed PR (ADR 0006).
- Source IDs: `src-<yyyymmdd-of-publication-or-ingestion>-<slug>`. Duplicate checking is the
  intake coordinator's first step.
