# pipelines/

Workflow manifests read by the orchestrator agent — the declarative counterpart of the
user-invoked workflow skills. Pattern adapted from OpenMontage's pipeline manifests (stages,
required artifacts, gates) without reusing its code or schema
(see `docs/investigations/openmontage-architecture-review.md`).

- `research-ingestion.yaml` — `/ingest-source`: registration → extraction → claims → assessment
  → technique/hypothesis mapping → contradiction check → proposals → evaluation → PR summary.
- `skill-refinement.yaml` — `/refine-skills-from-source`: evidence reading → change decision →
  candidate generation → critic loop → validation → fixtures → regression → PR preparation.

Manifest contract: ordered `stages`, each with `agent`, `reads`, `produces` (artifact types),
`gate` (`none` | `orchestrator_check` | `human`). The orchestrator must not proceed past a stage
whose `produces` are missing, must not let one agent perform every stage, and must stop at
`human` gates.

Deferred (documented in `docs/roadmap/`): `analytics-feedback` (phase 5),
`video-production` (phase 3+, executes via the pinned OpenMontage clone).

Changes here are infrastructure changes: PR-gated, and must keep
`docs/workflows/` in sync.
