# ADR 0006: Human Review and PR Gate

- Status: **Proposed**
- Date: 2026-08-03

## Context

The creator is the final quality gate. Research-derived knowledge and skill changes must never
merge automatically, contradictions must never be silently resolved, and agents must stop when
human review is required. GitHub is the tracker and review surface.

## Decision

- **All mutations to `knowledge/`, `evidence/`, `.cursor/skills/`, `schemas/`,
  `evaluation/rubrics/` and `docs/adr/` land via pull request.** No agent merges, closes review
  threads as resolved, or marks PRs ready on its own.
- The PR curator agent assembles changes on a branch and fills the repository PR template
  (source, findings, changes, contradictions, evaluation, recommendation, human checklist —
  spec §21). The `PullRequestSummary` artifact is committed alongside the PR body.
- **Main-branch protection is recommended configuration** (require PR, require CI, no force push);
  applied by the creator in GitHub settings since it cannot be committed. CODEOWNERS assigns all
  paths to the creator as a second layer.
- Disagreement between agents is preserved in contradiction records and surfaced in the PR's
  "requires creator review" section; the orchestrator must not fabricate consensus.
- Per-source working artifacts under `research/sources/<id>/` are committed by the workflow (they
  are the audit trail), but they are inputs to review, not knowledge: only their promotion into
  `evidence/` and `knowledge/` constitutes accepted state, and that promotion is what the human
  checklist approves.
- CI on PRs runs only deterministic checks (schema validation, linters, ID checks, tests); agent
  evaluations are attached as committed reports, keeping hosted-model cost out of routine CI.

## Alternatives

- Direct commits to main with post-hoc review — rejected: destroys the control point the whole
  system depends on.
- Auto-merge on green CI — rejected explicitly by the specification.

## Consequences

- Slower knowledge accretion, by design; every accepted claim has a reviewable provenance chain
  (source → extraction → claim → assessment → proposal → PR).
- The creator's review burden is managed by the human review packet (concise, one representative
  before/after, explicit uncertainty) rather than by weakening the gate.
