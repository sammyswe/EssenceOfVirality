# Changelog

All notable changes to this project are documented here. Format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); versions are dated milestones rather
than semver releases while the project is pre-production.

## [Unreleased]

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
