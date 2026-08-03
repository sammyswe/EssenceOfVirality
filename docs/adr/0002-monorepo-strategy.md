# ADR 0002: Monorepo Strategy

- Status: **Proposed**
- Date: 2026-08-03

## Context

Phase one produces several coupled concerns: schemas, research artifacts, knowledge documents,
skills, agent definitions, evaluation tooling and documentation. They share one review workflow
(the research PR), one validation toolchain, and dense cross-references by ID. The specification
mandates one primary repository designed so major areas could later be extracted.

## Decision

A single modular monorepo with **boundaries drawn by directory contract, not by package
machinery**:

- `schemas/` is the only source of truth for artifact shapes; everything else references it.
- `.cursor/skills/`, `knowledge/`, `evidence/`, `research/`, `evaluation/` are data/document areas
  whose write access is defined per agent and enforced by rules and PR review.
- Executable code is confined to `tools/` (deterministic validators) and, later,
  `integrations/openmontage/` adapters — the two areas that could become `packages/` when code
  volume justifies packaging.
- The `packages/{evidence-model,source-ingestion,skill-linter,evaluation-runner,shared-schemas}`
  split from the original sketch is **deferred**: in phase one it would wrap four small scripts and
  a schema directory in packaging ceremony. Extraction later is mechanical because dependencies
  already flow one way (tools → schemas; nothing imports tools).

## Alternatives

- Multi-repo (skills repo, knowledge repo, tooling repo) — rejected: breaks the atomic research PR
  (one source ingestion touches research, evidence, knowledge, skills and evaluation together) and
  multiplies agent-permission surface.
- Full package workspace now (npm/uv workspaces) — rejected as premature structure for the code
  volume; revisit when a second consumer of any tool appears or apps/CLI work begins (phase 3+).

## Consequences

- Atomic, traceable PRs across knowledge/skills/evidence.
- Extraction criteria are recorded: a directory graduates to a package when it gains an external
  consumer, its own release cadence, or a real dependency tree.
- Discipline lives in rules and CI rather than package boundaries in the interim.
