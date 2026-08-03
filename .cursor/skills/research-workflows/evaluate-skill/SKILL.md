---
name: evaluate-skill
description: Run the full evaluation harness (deterministic checks, behavioural fixtures, regression if versioned) against one skill and produce an evaluation report.
disable-model-invocation: true
argument-hint: <skill-name> [--against <old-version-ref>]
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Evaluate a skill

## Steps

1. Locate the skill in `.cursor/skills/`; read its metadata and `evidence_refs`. Complete when
   its bank, version and maturity are known.
2. Delegate to the `evaluation-agent`: deterministic tier (all four validators + pytest), then
   behavioural tier against every fixture in `evaluation/fixtures/` that names this skill in
   `expected_diagnoses`. With `--against`, also run the regression protocol (old vs new on the
   same fixtures, critic verdict on improvements and regressions). Complete when the
   `evaluation_report` exists in `evaluation/reports/` and validates.
3. Report: per-check results, per-fixture outcomes (expected diagnosis produced? false positives
   avoided? `must_preserve` respected?), regression findings, the report's
   `cannot_validate_without_real_data` list, and the recommendation. Complete when delivered
   with the report's artifact ID.

## Output contract

An `evaluation_report` artifact + chat summary. No skill edits — evaluation observes.

## Failure handling

Skill not referenced by any fixture → run deterministic tier, report the fixture gap, and
recommend a fixture addition rather than inventing ad-hoc scenarios.
