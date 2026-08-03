---
name: classify-evidence-claim
description: Classify a statement into the project's epistemic taxonomy and draft a valid claim record. Use when turning extracted findings into claims, when a statement's epistemic type is disputed, or when another skill needs a claim record drafted.
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Classify an evidence claim

## Steps

1. Isolate the claim: one self-contained statement, source-neutral wording, no bundled
   conjunctions (split "X and Y" into two claims). Complete when the statement stands alone.
2. Classify by decision tree — take the FIRST match:
   - Creator-supplied requirement → **preference**. Platform/legal/technical limit → **constraint**.
   - Documented outcome of a deliberate test → **experiment_result**.
   - Asserted by the platform/authoritative primary source, or measured in first-party data →
     **fact** (scoped: a 2020 disclosure is a fact *about the 2020 disclosure*).
   - Proposes an unmeasured explanation or prediction → **hypothesis**.
   - Association observed across multiple examples without causal claim → **pattern**.
   - One creator/account/uncontrolled example → **anecdote**.
   - Actionable rule of thumb without causal certainty → **heuristic**.
   - Otherwise, conclusion reasonably supported by source(s) → **finding**.
   Complete when exactly one type is assigned with a one-line justification.
3. Fill the record fields per `schemas/claim-record.schema.json`: domains, metric targets,
   evidence_basis, transferability (against 10–40 s Spotify house-mix screen recordings),
   confidence (start low; medium needs method transparency or corroboration; high needs official/
   measured/replicated support), `platform_dependent` (TikTok mechanics → true; human attention →
   false), publication date, limitations (never empty for informal sources). Complete when every
   required field is set.
4. Validate mentally against the schema and hand back the YAML. Complete when schema-valid.

## Output contract

One `claim_record` YAML block per claim, ready for the orchestrator to write.

## Failure handling

Statement too vague to classify → return it with the ambiguity named and the two candidate
types; do not force a classification.

## Counterexample

"Videos under 15 s get boosted" from a creator's blog is NOT a fact — it is a hypothesis (if
framed as mechanism) or anecdote/pattern (if framed from their results), `platform_dependent:
true`, confidence low.
