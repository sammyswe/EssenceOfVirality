# Agent Topology

Revision date: 2026-08-03. Thirteen specialists with narrow decision rights, defined in
`.cursor/agents/`. Full duties/prohibitions live in each definition; this document is the map.

## Decision-rights matrix

| Agent | Decides | Writes | Read-only |
|---|---|---|---|
| orchestrator | Stage sequencing, gate stops, artifact completeness | Artifacts on behalf of read-only analysts; audit notes | |
| research-intake-coordinator | Source identity, type, duplicate verdict, routing | `research/sources/<id>/manifest.yaml` | |
| source-extraction | Sectioning, content kinds, limitations | `research/sources/<id>/extraction.yaml` | |
| evidence-analyst | Claim identification, epistemic type, assessment | — (returns YAML) | ✓ |
| distribution-model-analyst | Model placement, hypothesis rewrites | — (returns YAML) | ✓ |
| virality-technique-analyst | Technique extraction, mechanism chains, dispositions | — (returns YAML) | ✓ |
| spotify-mix-domain-analyst | Transfer judgements, niche adaptations, music-risk vetoes | — (returns YAML) | ✓ |
| contradiction-synthesis | Disagreement detection, cause analysis, resolution recommendation | `research/conflicts/` | |
| skill-architect | Change disposition, granularity, candidate authoring | `proposals/`, `.cursor/skills/experimental/`, staged knowledge edits | |
| skill-critic | Pass / revisions-required verdicts | — (returns review) | ✓ |
| evaluation-agent | Check execution, regression verdicts, recommendations | `evaluation/reports/`, `evaluation/regression/` | |
| analytics-learning | Normalisation, lineage verification (phase-one: validate-and-store) | `analytics/` observations | |
| pr-curator | Branch/commit assembly, PR body | PR branch, `pr-summary.yaml` | |

## Least privilege (Cursor constraints)

Cursor subagents have no `tools` allowlist, so privilege is enforced by: (1) explicit
allowed/prohibited files and actions in each definition; (2) `readonly: true` on the five
analysis agents — they return complete artifact YAML in their reply and the **orchestrator writes
it verbatim**, preserving their `produced_by`; (3) the always-on rules (PR-only mutation, no
merging); (4) `.cursor/hooks.json` documented as the future hard-enforcement point if
instruction-level discipline proves insufficient.

## Handoff protocol

Handoffs are artifact IDs/paths, never paraphrases: a downstream agent reads the artifact file.
Schemas: `schemas/` (ADR 0004). The orchestrator verifies each stage's `produces` exist and
validate before the next stage starts, and records skips and disagreements as it goes.

## Disagreement handling

No agent overrides another's judgement. Conflicting outputs are preserved side by side:
contradiction records for claims, `requires_creator_review` entries in the PR summary for
everything else. The orchestrator must not fabricate consensus (its definition prohibits it);
the PR is the surface where the creator arbitrates.

## Why subagents (not skills) for specialists

Each specialist needs an isolated context window (its own reading set), its own prohibitions,
and parallelisability. Single-purpose one-shot operations (classify a claim, detect
contradictions) are skills in `.cursor/skills/meta/` that any agent can invoke.
