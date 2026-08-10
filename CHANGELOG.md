# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are dated milestones rather
than semver releases while the project is pre-production.

## [Unreleased]

### Added

- Creative-minimum gate (`production/pipeline/creative_gate.py`) split from
  technical quality: track metadata (or waiver), non-fallback format (or
  force/waiver), hook specificity. `post_ready` requires both gates.
  Orchestrator returns `needs_creative_input` and leaves the job in place when
  technical checks pass but creative minimum fails. See
  `docs/investigations/pipeline-run-job-new-test-r1-review.md`.
- Schema `creative-minimum-report.schema.json`; quality report gains
  `technically_valid` and embedded `creative_minimum`.
- Research batch 2026-08-03 (5 creator-supplied sources): Klug et al. 2021 (WebSci),
  Lynch 2025 (UConn thesis), UW News 2024 (data-donation studies), Herman 2023 (IASDR),
  Zhou 2024 (IJCSIT, assessed low-credibility) — 17 claims, 17 assessments, 2 niche
  hypotheses, 3 technique records under `research/sources/` and `evidence/`.
- First real contradiction records: skip-speed signal, trending-hashtag effect, optimal
  length (`evidence/contradictions/`).
- New canonical knowledge doc `knowledge/production-techniques/metadata-and-discovery.md`;
  working model advanced to v0.1; completion doc gains an external baseline; unknowns
  narrowed and extended.
- First candidate skill via the skill-refinement path:
  `experimental/searchable-onscreen-text` (`scp-20260803-searchable-onscreen-text`).
- `research/batches/` directory for multi-source batch artifacts (documented in
  `research/README.md`).

### Fixed

- Retention hypothesis no longer cites zoom-marked payoff when emphasis is
  disabled (preference or config).
- Invalid `content_kinds` value in one extraction report caught by schema validation during
  the batch (corrected to `quoted_third_party`).

## [phase-1] - 2026-08-03

### Added

- External-system investigations (OpenMontage `4eab34c5`, mattpocock/skills `2ab95809`, current
  Cursor conventions) under `docs/investigations/`.
- Phase-one architecture proposal and ADRs 0001–0007 (proposed).
- Repository scaffold: root docs, GitHub templates and deterministic CI, `.gitignore`/security
  posture.
- Canonical JSON Schemas for all inter-agent artifacts (`schemas/`) and deterministic validators
  (`tools/`): artifact validation, skill lint, ID/reference integrity, fixture structure checks.
- Cursor infrastructure: global + scoped rules, 13 specialist agent definitions, workflow skills
  (`ingest-source`, `compare-evidence`, `refine-skills-from-source`, `evaluate-skill`,
  `prepare-research-pr`, `propose-experiment`, `ingest-tiktok-analytics`,
  `review-openmontage-integration`), meta skills and four exemplar domain skills.
- Knowledge base structure, evidence store, evaluation harness (rubrics + six behavioural
  fixtures), pipeline manifests, OpenMontage integration placeholder, analytics scaffold.
- Pinned installation of mattpocock/skills with repo setup (`docs/agents/`).
- Vertical slice: TikTok newsroom For You disclosure ingested end-to-end
  (`research/sources/src-20260618-tiktok-newsroom-foryou/` → claims → assessment → knowledge
  change → evaluation → PR summary).
- Phase-one review (`docs/phase-one-review.md`).
