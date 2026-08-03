---
name: ingest-source
description: Run the full research-ingestion workflow on a URL, file or pasted source.
disable-model-invocation: true
argument-hint: <url-or-path> [creator note]
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: true
---

# Ingest a research source

Runs the complete research-to-PR workflow for one source:
registration → extraction → claims → assessment → distribution mapping → techniques → niche
adaptation → contradiction check → proposals → critic → evaluation → PR preparation.

## Steps

1. Read `pipelines/research-ingestion.yaml` and `CONTEXT.md`. Complete when you can name every
   stage, its agent and its gate.
2. Delegate execution to the `orchestrator` agent with the source argument and any creator note.
   The orchestrator runs the stages with the specialist agents; do not perform specialist stage
   work in this context. Complete when the orchestrator reports all stages done or stopped at a
   gate.
3. Verify the run: `python3 tools/validate_artifacts.py && python3 tools/check_ids.py` pass, and
   `research/sources/<src-id>/` contains manifest, extraction, assessments and pr-summary.
   Complete when validators are green.
4. Report to the creator: source ID, claims found (by type), contradictions (or explicit "none
   found"), proposals made, evaluation verdict, PR branch/URL, and every item in
   `requires_creator_review`. Complete when the report is delivered and the workflow has
   STOPPED before merge.

## Output contract

A registered `research/sources/<src-id>/` directory of valid artifacts, a draft PR (or PR-ready
branch), and the report above. Never a merge.

## Failure handling

Duplicate source → report the existing source ID and stop. Extraction impossible → the manifest
is still registered with the limitation recorded; report and stop. Validator failures → fix or
report; never open a PR on red validators.
