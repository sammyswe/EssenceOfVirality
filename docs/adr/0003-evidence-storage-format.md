# ADR 0003: Evidence Storage Format

- Status: **Proposed**
- Date: 2026-08-03

## Context

The evidence system must preserve epistemic status (fact / finding / hypothesis / heuristic /
pattern / anecdote / constraint / preference / experiment result), survive contradiction without
overwriting, be reviewable in PR diffs by a human, be editable by agents without a database, and be
validated deterministically in CI. The creator has ruled out automatic time decay and false-precision
confidence percentages.

## Decision

- **One YAML file per record** (claims, hypotheses, contradictions, experiments, assessments),
  validated against JSON Schemas in `schemas/` (see ADR 0004 for why JSON Schema).
- Records live under `evidence/` (promoted, cross-source) and `research/sources/<source-id>/`
  (per-source working artifacts). Knowledge documents in `knowledge/` cite records by ID and never
  restate them as new facts.
- Field set follows the specification's claim-record sketch: `id`, `statement`, `claim_type`,
  `source_ids`, `domain`, `metric_targets`, `evidence_basis`, `transferability`,
  `confidence: low|medium|high`, `status: active|disputed|superseded|rejected|testing`,
  `limitations`, `contradictions`, `proposed_actions`, plus the common artifact envelope
  (`created_at`, `produced_by`, `version`, `human_review`).
- **Supersession over mutation**: changing a claim's substance creates a new version or a new
  record with `superseded_by`/`supersedes` links; `status: disputed` plus a contradiction record
  represents live disagreement. History remains in git and in the records themselves.
- **No time decay**: publication dates are stored; platform-dependent findings carry a
  `platform_dependent: true` flag prompting revalidation, while enduring attention principles do
  not.

## Alternatives

- SQLite/database — rejected: not PR-reviewable, adds runtime dependency, blocks the PR-gated
  mutation model that is the project's core control.
- Markdown with YAML frontmatter per claim — rejected for records: prose bodies invite unvalidated
  drift; claims are structured data. (Knowledge documents, which are prose, remain Markdown.)
- One big YAML/JSON registry file — rejected: merge conflicts, unreviewable diffs.

## Consequences

- Everything is grep-able, diff-able and agent-writable; CI (`validate_artifacts.py`,
  `check_ids.py`) is the integrity layer.
- Cross-record queries (e.g. "all disputed claims about hooks") are directory walks — acceptable at
  phase-one scale; `knowledge/index.md` and generated indexes mitigate; a real index/database can be
  derived later from the same files without migration.
