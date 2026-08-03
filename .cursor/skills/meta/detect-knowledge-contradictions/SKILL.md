---
name: detect-knowledge-contradictions
description: Find and record disagreements between a set of claims and the existing evidence store. Use during ingestion contradiction checks, before promoting claims, or when another skill needs overlap analysis against existing knowledge.
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Detect knowledge contradictions

## Steps

1. Build the comparison set: for each input claim, gather existing records sharing any domain,
   any metric target, or the same production rule/topic terms (search `evidence/claims/`,
   `evidence/hypotheses/`, `research/sources/*/claims/`, and the owning `knowledge/` documents
   via `knowledge/index.md`). Complete when the set is listed with IDs.
2. Test each pair for genuine disagreement: they must make incompatible assertions about the
   same thing at the same scope. Different niches/metrics/definitions are *cause candidates*,
   not automatic dismissals. Complete when each pair is marked agree / disagree / orthogonal.
3. For each disagreement, draft a `contradiction_record`: all claim IDs, description of the
   incompatibility, cause analysis (different_niches / dates / audience_sizes / metrics /
   definitions / methods / genuine_conflict / unknown — multiple allowed), and a recommendation:
   - both survive in scoped contexts → `coexist` with the scoping stated;
   - a named test could discriminate → `experiment_proposed` (+ hand to /propose-experiment);
   - strictly stronger evidence on one side → `superseded`, justified;
   - taste/strategy judgement → `creator_review_required`.
   Complete when every disagreement has a record and a recommendation.
4. List the follow-up edits the PR must carry: `status: disputed` on affected claims and
   `contradictions` field additions. Complete when listed. If no disagreements: state "no
   contradictions found" explicitly for the PR summary.

## Output contract

`contradiction_record` YAML blocks + proposed status-change list. No silent edits to either side
of any disagreement.

## Failure handling

Cannot determine whether claims target the same scope → record the contradiction with cause
`unknown` and `creator_review_required` rather than guessing.
