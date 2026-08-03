---
name: refine-skills-from-source
description: Turn a completed source ingestion into minimal, well-justified skill or knowledge changes via the skill-refinement workflow.
disable-model-invocation: true
argument-hint: <src-id>
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: true
---

# Refine skills from a source

Runs `pipelines/skill-refinement.yaml`: context reading → disposition decisions → candidate
generation → critic loop → validation → fixtures + regression → PR preparation.

## Steps

1. Preconditions: `research/sources/<src-id>/` contains extraction and assessments. Missing →
   stop and instruct `/ingest-source` first. Complete when verified.
2. Delegate to the `orchestrator` with the manifest `pipelines/skill-refinement.yaml`. The
   disposition rule the skill-architect applies: each change lands in exactly one of — knowledge
   document / skill resource / skill / rubric / pipeline manifest / experiment — and a skill only
   for operational, triggerable, checkable behaviour. Complete when the orchestrator reports
   pr-preparation reached or an earlier stop.
3. Verify: critic status `passed` (or escalation recorded), regression bundle exists for any
   version bump, `python3 tools/lint_skills.py` green. Complete when verified.
4. Report: changes proposed (by disposition), critic findings summary, evaluation verdict,
   before/after example for any skill change, PR branch/URL, open disagreements. STOP before
   merge. Complete when reported.

## Output contract

Minimal candidate changes on a PR-ready branch; no source ever rewrites every related skill.
Proposals live in `research/sources/<src-id>/proposals/`; new skills in
`.cursor/skills/experimental/`.

## Failure handling

Critic fails twice → escalate to creator with both rounds' findings; do not run a third.
Evidence only supports a hypothesis → produce an `experiment_proposal` instead of a skill and
say so.
