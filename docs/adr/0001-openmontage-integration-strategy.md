# ADR 0001: OpenMontage Integration Strategy

- Status: **Proposed**
- Date: 2026-08-03
- Evidence: `docs/investigations/openmontage-architecture-review.md`,
  `docs/investigations/integration-options.md` (inspected commit `4eab34c5`, 2026-08-03)

## Context

OpenMontage is the candidate execution framework for the future video-production pipeline
(phase 3+). Investigation established that it is: (1) an AGPL-3.0, agent-orchestrated workbench
consumed as a cloned working directory, not an installable library; (2) extensible only in-tree or
via project-scoped extensions under `projects/<name>/{scripts,skills,tools}`
(`skills/meta/capability-extension.md`) — there are no external plugin roots; (3) high-churn
(~131 commits in the month before inspection) with strict (`additionalProperties: false`),
evolving manifest and checkpoint schemas; (4) already equipped with the capabilities the future
pipeline needs (`screen-demo` pipeline, `tiktok` 1080×1920 media profile, `auto_reframe`,
`video_compose`, subtitle/overlay tools, checkpoint audit trail). Phase one executes no video
production.

## Decision

Adopt **Option D — adapter plus extension package — with a materialisation refinement**:

1. This repository owns `integrations/openmontage/`: the pinned upstream ref, TikTok pipeline
   manifest sources, custom stage-skill sources, domain schemas, and evaluation adapters.
2. OpenMontage itself lives **outside this repository** as a clone pinned to a recorded commit.
3. When production work begins (phase 3), our extension sources are **materialised into the pinned
   clone's `projects/<name>/` scope** (the upstream-sanctioned extension path). If a capability
   requires a first-class pipeline, sources are copied into a scratch clone's `pipeline_defs/` and
   `skills/pipelines/` — never committed back into this repository from the clone.
4. Phase-one footprint is documentation only: this ADR, the integration review, and the
   `integrations/openmontage/` README defining the above.

## Alternatives

- **A. Upstream dependency (installed package)** — rejected: no published package exists; skills,
  manifests and the Remotion composer are filesystem-coupled to the clone, so "installed version"
  can only mean a pinned clone, which is what Option D uses.
- **B. Git submodule** — deferred: achieves pinning but adds submodule workflow friction during a
  phase that runs zero OpenMontage code. May be adopted at phase 3 as the mechanical form of the
  pinned clone if reproducibility across machines demands it.
- **C. Maintained fork** — rejected for now: immediate upstream-merge burden against very high
  churn, AGPL obligations on the fork, and divergence risk, all before evidence that project-scoped
  extension is insufficient. Re-entry conditions below.

## Consequences

- No OpenMontage code, schemas or skills are vendored into this repository; the AGPL boundary is a
  process/repository boundary.
- Our manifests and stage skills must track a pinned upstream schema version; upgrades are
  deliberate events, not drift.
- The production pipeline inherits OpenMontage's agent contract (Rule Zero, checkpoint protocol,
  reviewer meta-skill) rather than reimplementing orchestration.
- Some friction is accepted at phase 3: a materialisation/sync step instead of a load path.

## Upgrade strategy

Upgrades are explicit: run the `review-openmontage-integration` workflow against the candidate
ref; diff `schemas/pipelines/`, `schemas/checkpoints/`, `skills/meta/checkpoint-protocol.md` and
the tool signatures we depend on; update the pinned ref plus our extension sources in one PR;
never track a moving branch.

## Version-pinning strategy

`integrations/openmontage/PINNED_REF` records the exact commit SHA (currently the inspected
`4eab34c5cfcccaa4f1970554928feccce73ee930` as the reference point; re-pinned when phase 3 starts).
All extension sources state the schema versions they were authored against.

## Licensing implications

AGPL-3.0. Invoking an unmodified local clone imposes no obligations on this repository's contents.
Forking or vendoring would place derived work under AGPL, with source-provision obligations if the
system were ever distributed or offered as a network service. No CLA is required upstream; no
dual-licensing option exists. Flagged for legal review before any future distribution.

## Exit strategy

If OpenMontage becomes unsuitable, this repository retains: all domain schemas, manifests
(declarative YAML translatable to another executor), stage-skill sources (Markdown), the evidence
and knowledge bases, and the evaluation harness — none of which depend on OpenMontage code. The
replacement cost is confined to re-targeting the manifests and tool invocations.

## Conditions that would justify moving to a fork

1. Upstream removes or breaks the project-scoped extension mechanism.
2. A required capability needs in-tree changes upstream declines to accept.
3. Pinned-integration breakage from schema churn more than once per project phase.
4. Upstream licensing or governance changes that make pinned consumption unsafe.
