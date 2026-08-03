---
name: compare-evidence
description: Compare a claim, source or topic against the existing evidence store and report agreements, contradictions and gaps.
disable-model-invocation: true
argument-hint: <claim-id | src-id | topic>
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Compare evidence

Answers: what does the repository already believe about this, and does the given claim/source/
topic agree?

## Steps

1. Resolve the argument: a `claim-*`/`src-*` ID → load those records; a topic → find related
   records by domain, metric targets and key terms across `evidence/` and
   `research/sources/*/claims/`, plus the owning `knowledge/` document via `knowledge/index.md`.
   Complete when you hold the full related-record set.
2. Delegate comparison to the `contradiction-synthesis` agent for disagreement analysis and,
   where the subject is claims touching distribution, to the `distribution-model-analyst` for
   placement against the working model. Complete when both return.
3. Report: per related record — agrees / disagrees (with cause analysis) / orthogonal; existing
   contradiction records touching the subject; which `knowledge/algorithm-model/unknowns.md`
   entries apply; recommended next action (nothing / new contradiction record / experiment /
   ingestion of a better source). Complete when the report cites every record by ID.

## Output contract

A comparison report in chat, citing record IDs. New `contradiction_record`s only via the
contradiction-synthesis agent in `research/conflicts/`; no other files change.

## Failure handling

Unknown ID → say so and list near matches. Empty evidence store for the topic → report the gap
honestly; do not pad with speculation.
