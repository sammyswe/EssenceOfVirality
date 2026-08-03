---
name: prepare-research-pr
description: Assemble a completed workflow run into a reviewable draft pull request with the template filled and disagreements preserved.
disable-model-invocation: true
argument-hint: <src-id>
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: true
---

# Prepare a research PR

## Steps

1. Preconditions: an `evaluation_report` for the run exists with overall pass or
   pass_with_warnings; any `skill_change_proposal` has critic status `passed`; all four
   validators are green. Complete when verified — otherwise name the failing precondition and
   stop.
2. Delegate to the `pr-curator`: branch, logical commits, promoted claims into `evidence/`,
   knowledge edits, candidate skills, `pr-summary.yaml`, PR template body, draft PR. Complete
   when the curator returns the branch and PR URL.
3. Verify the PR body: every template section filled; contradictions section lists each
   disagreement or an explicit "none found"; human checklist untouched; recommendation matches
   the evaluation report's. Complete when verified.
4. Report the PR URL and the items awaiting creator judgement. STOP — merging is the creator's
   act alone. Complete when reported.

## Output contract

A draft PR whose story runs source → findings → changes → evaluation → recommendation, plus the
`pull_request_summary` artifact.

## Failure handling

Conflicting proposals for the same file → escalate both to the creator inside the PR body's
contradictions section; never pick silently.
