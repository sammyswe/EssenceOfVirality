# ADR 0004: Agent Communication Artifacts

- Status: **Proposed**
- Date: 2026-08-03

## Context

Specialist agents must communicate through structured artifacts rather than uncontrolled
conversational context. Twelve artifact types are required (SourceManifest, ExtractionReport,
ClaimRecord, EvidenceAssessment, TechniqueRecord, ContradictionRecord, KnowledgeChangeProposal,
SkillChangeProposal, EvaluationReport, AnalyticsObservation, ExperimentProposal,
PullRequestSummary). The specification demands one canonical schema mechanism with justification,
explicitly avoiding manually synchronised duplicates. Candidates: JSON Schema, Pydantic, Zod.

## Decision

- **JSON Schema draft 2020-12 is the single canonical definition**, one `schemas/<artifact>.schema.json`
  per type, with a shared `schemas/common.schema.json` for the envelope every artifact carries:
  `id`, `created_at`, `produced_by`, `inputs` (artifact IDs), `status`, `version`, optional
  `confidence`, `human_review`, `derived_artifacts`.
- Artifacts are written as **YAML instances** and validated by a thin Python runner
  (`tools/validate_artifacts.py`, using `jsonschema` + `PyYAML`) locally and in CI.
- Agents exchange artifact **IDs/paths** in handoffs; a downstream agent reads the artifact file,
  never a paraphrase of it.

## Alternatives

- **Pydantic-first** — rejected for phase one: artifacts have no runtime object model yet (agents
  and humans edit files); Pydantic would either duplicate schemas or force codegen. If phase 3+
  builds a Python application, models can be generated from or validated against these schemas.
- **Zod-first** — rejected: same duplication issue, plus the toolchain gravity here is
  Python-adjacent (OpenMontage, analytics importers), and JSON Schema is what OpenMontage itself
  uses for manifests and checkpoints — one mental model across both systems.
- **Prose handoff conventions only** — rejected: unvalidatable, and the whole point is preventing
  uncontrolled context transfer.

## Consequences

- Deterministic, model-free validation in CI; language-neutral schemas any future component can
  consume.
- JSON Schema's expressiveness limits (cross-record referential integrity) are covered by
  `tools/check_ids.py` rather than schema contortions.
- Schema changes are versioned (`$id` + semantic version field) and land via the same PR gate as
  everything else.
