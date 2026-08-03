---
name: ingest-tiktok-analytics
description: Validate and store a TikTok analytics export or manual reading as an observation record linked to its production manifest. Phase-one scope is validate-and-store only.
disable-model-invocation: true
argument-hint: <csv-path-or-pasted-metrics> --video <video-id>
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Ingest TikTok analytics (scaffold)

Phase-one behaviour (ADR 0007): normalise → validate → store. **No comparison, no learning, no
recommendations** — that is phase 5.

## Steps

1. Verify lineage: the `--video` ID resolves to an existing `video_production_manifest`.
   Missing → stop and report the gap (metrics without lineage teach nothing). Complete when
   resolved.
2. Delegate normalisation to the `analytics-learning` agent: absolute counts and rates into
   their separate structures, retention curve if present, posting metadata, account context;
   capture date = today unless the export states one; redact sensitive audience data. Complete
   when a draft `analytics_observation` exists.
3. Validate (`python3 tools/validate_artifacts.py`) and store as a NEW snapshot file — never
   overwrite an existing observation for the same video/date. Raw export stays outside git
   (`analytics/raw/` locally). Complete when green and committed to the working branch.
4. Report: observation ID, which fields the export could not provide (recorded as absent, not
   zero), and a reminder of the phase boundary. Complete when reported.

## Output contract

One `analytics_observation` artifact per invocation; the production manifest's
`analytics_records` list updated with its ID.

## Failure handling

Unrecognised export format → store nothing; record the column layout in the report so the
phase-5 importer can be designed from real formats.
