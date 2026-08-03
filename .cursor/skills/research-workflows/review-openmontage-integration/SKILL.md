---
name: review-openmontage-integration
description: Re-inspect the pinned OpenMontage upstream against a candidate ref and report schema, skill and licence drift before any re-pin.
disable-model-invocation: true
argument-hint: [candidate-ref]
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: true
---

# Review the OpenMontage integration

Executes the ADR 0001 upgrade checklist. Without a candidate ref, reviews upstream HEAD.

## Steps

1. Read `integrations/openmontage/PINNED_REF`, ADR 0001, and
   `docs/investigations/openmontage-architecture-review.md`. Complete when the current pin and
   our dependency surface are listed.
2. Fetch upstream into a scratch clone **outside the repo** (`tmp/` or
   `integrations/openmontage/clone/` — both gitignored). Complete when the candidate ref is
   checked out.
3. Diff our dependency surface between pin and candidate: `schemas/pipelines/`,
   `schemas/checkpoints/`, `skills/meta/checkpoint-protocol.md`, `skills/meta/reviewer.md`,
   `skills/meta/capability-extension.md`, `lib/media_profiles.py` (tiktok profile),
   `pipeline_defs/screen-demo.yaml`, `pipeline_defs/clip-factory.yaml`, `LICENSE`, and the
   extension mechanism. Complete when each item is marked unchanged / changed-compatible /
   changed-breaking, with evidence.
4. Check fork triggers (ADR 0001): extension mechanism removed? needed capability gated
   upstream? repeated breakage? licence change? Complete when each is answered yes/no.
5. Report: drift table, licence status, recommendation (keep pin / re-pin via PR / escalate a
   fork trigger to the creator). A re-pin is a PR that updates `PINNED_REF` + any affected
   extension sources together. Complete when reported; make no changes without the PR.

## Output contract

A drift report in chat (and, when re-pinning, a PR). Never vendors upstream code into this
repository.

## Failure handling

Upstream unreachable → report and stop; never substitute a mirror without creator approval.
