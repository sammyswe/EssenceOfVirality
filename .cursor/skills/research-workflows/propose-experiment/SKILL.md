---
name: propose-experiment
description: Turn one or more hypotheses into a concrete, honest experiment proposal (variants, metrics, success criteria, sample-size caveat).
disable-model-invocation: true
argument-hint: <claim-id...> | <question>
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: true
---

# Propose an experiment

## Steps

1. Resolve the hypotheses: claim IDs → load them (must be `claim_type: hypothesis` or
   `status: disputed`); a question → find or draft the hypothesis claim first (via the
   distribution-model-analyst if it concerns distribution). Complete when every hypothesis under
   test exists as a claim record.
2. Design: choose ab_test / multivariate / sequential_comparison / observational_cohort — the
   simplest design that can discriminate the hypothesis. Define ≥2 variants that differ in one
   decision, the metric targets, and success criteria stated *before* running. Complete when a
   naive reader could execute the design.
3. Write the honest constraints: `sample_size_note` (how many posts/views before any conclusion —
   single-digit posts almost never conclude anything), risks (audience confusion, damage to the
   mix experience, confounding a running experiment), and what the experiment CANNOT show.
   Complete when both are non-empty and specific.
4. Write the `experiment_proposal` to `evidence/experiments/`, validate, link it from the
   hypothesis claims' `proposed_actions`, and report with `status: proposed` for creator
   approval. Complete when validated and reported.

## Output contract

An `experiment_proposal` artifact; hypothesis claims updated with the link; no experiment is
*run* by this skill — approval and posting are the creator's.

## Failure handling

Hypothesis untestable with creator-controlled decisions → say so and record it in the claim's
limitations instead of designing a fake test.
