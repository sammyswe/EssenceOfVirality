# Workflows

Revision date: 2026-08-03. Each workflow is a user-invoked skill in
`.cursor/skills/research-workflows/` (the executable truth); multi-stage ones are declared in
`pipelines/*.yaml`. This page is the reader's guide — purpose, trigger, artifacts, gates — and
deliberately does not duplicate the skills' step lists.

## /ingest-source `<url-or-path> [note]`

The primary workflow. Full research-ingestion chain over one source
(`pipelines/research-ingestion.yaml`, 12 stages, 11 agents). Produces
`research/sources/<src-id>/` (manifest, extraction, claims, assessments, techniques, proposals,
pr-summary), contradiction records, evaluation report, draft PR. Gates: orchestrator checks per
stage; human gate before merge. Typical uses: a study on short-form retention; a creator's
case-study video; a course transcript.

## /compare-evidence `<claim-id | src-id | topic>`

Read-mostly comparison of a claim/source/topic against the evidence store; reports agreements,
contradictions (with cause analysis), gaps and applicable unknowns. Writes at most
`research/conflicts/` records. Use before trusting a new finding or when the creator wonders
"don't we already know something about X?".

## /refine-skills-from-source `<src-id>`

Turns a completed ingestion into minimal changes (`pipelines/skill-refinement.yaml`): disposition
decisions → candidates → critic loop (2 rounds max) → validators → fixtures + regression → PR.
The disposition rule keeps skills rare: knowledge document / skill resource / skill / rubric /
manifest / experiment.

## /evaluate-skill `<skill-name> [--against <old-ref>]`

Full harness against one skill: deterministic validators, behavioural fixtures naming the skill,
optional before/after regression. Produces an `evaluation_report` in `evaluation/reports/`.

## /prepare-research-pr `<src-id>`

Assembly only: verifies preconditions (evaluation passed, critic passed, validators green), then
branch → logical commits → promoted claims into `evidence/` → PR template body → draft PR →
stop. The human checklist stays untouched for the creator.

## /propose-experiment `<claim-id...> | <question>`

Hypotheses → a concrete `experiment_proposal` (variants, metrics, success criteria stated before
running, honest sample-size caveat, risks). Never runs anything; `status: proposed` awaits
creator approval.

## /ingest-tiktok-analytics `<export> --video <video-id>` (scaffold)

Phase-one scope: verify lineage to a `video_production_manifest`, normalise, validate, store a
snapshot. No comparison or learning until phase 5 (ADR 0007).

## /review-openmontage-integration `[candidate-ref]`

The ADR 0001 upgrade checklist: diff our upstream dependency surface between the pin and a
candidate, check fork triggers and licence, recommend keep / re-pin (PR) / escalate.

## Conventions common to all workflows

- Stop means stop: no workflow merges, marks ready, or ticks the creator's checklist.
- Validators must be green before any PR: `python3 tools/validate_artifacts.py`,
  `lint_skills.py`, `check_ids.py`, `run_fixtures.py`.
- Disagreements between agents ride to the PR in `requires_creator_review` — fabricated
  consensus is prohibited everywhere.
