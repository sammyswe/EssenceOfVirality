# Roadmap

Revision date: 2026-08-03 (revised per **ADR 0008** — creator-directed phase gates).

Seven phases. Each begins only when its definition of ready is met and its scope is deliberately
closed. Phase boundaries are enforced by `.cursor/rules/00-mission.mdc`, scoped rules, and the
phase-gate notes below. **Pipeline development (OpenMontage, edit execution, manifests) is forbidden
until phases 2 and 3 are complete.**

| Phase | Name | State |
|---|---|---|
| 1 | Intelligence infrastructure | **complete** — `../phase-one-review.md` |
| 2 | General virality corpus (~80 sources) | **in progress** — `phase-two-virality-campaign.md` |
| 3 | Creator calibration (Spotify-mix grilling) | **not started** — `phase-three-creator-calibration.md` |
| 4 | Production pipeline integration (OpenMontage) | designed only — `../architecture/future-video-pipeline.md` |
| 5 | End-to-end creative automation | sketch |
| 6 | Analytics learning loop | scaffolded schemas only (ADR 0007) |
| 7 | Continuous self-improvement | sketch |

### Renumbering from the original six-phase sketch

| Old | New |
|---|---|
| Phase 2 (knowledge at volume) | **Phase 2** — scoped to ~80 general virality sources + skills/rules |
| *(not present)* | **Phase 3** — creator grilling → niche skills |
| Phase 3 (OpenMontage) | **Phase 4** |
| Phase 4 (automation) | **Phase 5** |
| Phase 5 (analytics) | **Phase 6** |
| Phase 6 (continuous) | **Phase 7** |

---

## Phase 1 — Intelligence infrastructure ✓

Scaffold, schemas, agents, workflows, evaluation harness, PR gate, vertical slice. See
`../phase-one-review.md`.

**Exit:** met (PR #2 merged).

---

## Phase 2 — General virality corpus

**Goal:** Ingest ~80 additional TikTok-virality sources and convert durable findings into
**knowledge**, **`general-virality` skills**, and **scoped rules** — not into new specialist agents.

**In scope:**

- `/ingest-source` (and batch PRs via `research/batches/`) for general distribution, viewer
  behaviour, hooks, pacing, audio, packaging, platform mechanics, creator-education material, and
  peer-reviewed research.
- Populate planned canonical documents under `knowledge/algorithm-model/`, `knowledge/viewer-behaviour/`,
  and `knowledge/production-techniques/` as evidence arrives.
- Grow `.cursor/skills/general-virality/` and promote skills to at least `provisional` where
  evidence supports operational use.
- Add or tighten `.cursor/rules/*.mdc` when a finding should constrain all agents (e.g. epistemic
  patterns repeated across many sources).

**Out of scope:**

- Spotify-mix niche skills (`spotify-mix-content/` bank) — phase 3.
- OpenMontage adapter, edit plans, video execution — phase 4.
- Creator preference extraction beyond what sources already state — phase 3.

**Definition of ready:** Phase 1 merged; ingestion workflow proven (vertical slice + at least one
multi-source batch).

**Exit criteria:** See `phase-two-virality-campaign.md` (source count, canonical doc coverage,
skill bank checklist, rules audit, phase-two review doc).

---

## Phase 3 — Creator calibration (Spotify-mix grilling)

**Goal:** Capture the creator's actual practice, constraints, and taste for Spotify-mix TikToks
through structured grilling sessions, then author **`spotify-mix-content`** skills grounded in
**creator_statement** claims and optional review of real posts.

**In scope:**

- Grill sessions using `.agents/skills/grill-me`, `grill-with-docs`, or equivalent — documented in
  `docs/roadmap/phase-three-creator-calibration.md`.
- Register each session as a source; promote preferences/constraints to `evidence/` and
  `knowledge/spotify-mix-niche/`.
- Author, critic-review, and promote niche skills; cross-link to general-virality skills where
  niche adaptation is required.

**Out of scope:**

- OpenMontage / pipeline — phase 4.
- Bulk external virality ingestion — should be largely complete in phase 2.

**Definition of ready:** Phase 2 exit criteria met (or creator explicitly accepts partial phase-2
coverage with documented gaps).

**Exit criteria:** See `phase-three-creator-calibration.md`.

---

## Phase 4 — Production pipeline integration

Build `integrations/openmontage/` for real: materialise script, Spotify-mix manifest + stage skills
in the clone's project scope, `video_production_manifest` writing, evaluation adapters.

**Definition of ready:** Phases 2 **and** 3 exit criteria met; enough combined knowledge to compose
**defensible edit plans** citing both general and niche skills; re-run
`/review-openmontage-integration` and re-pin deliberately.

**Exit:** one raw capture becomes a post-ready video through the pinned clone with a complete
manifest.

---

## Phase 5 — End-to-end creative automation

Skill-composed edit plans selected from evidence; creator feedback loop into preference claims;
publishing recommendations.

**Exit:** creator effort ≈ record, review, post.

---

## Phase 6 — Analytics learning loop

Graduate scaffold schemas against real TikTok Studio exports; cohort comparisons; hypothesis/
experiment generation; experiment tracking through `evidence/experiments/`.

**Exit:** at least one skill-change proposal justified by measured first-party evidence.

---

## Phase 7 — Continuous self-improvement

Scheduled re-validation of `platform_dependent` claims; periodic source re-ingestion; skill-maturity
reviews; the system proposes its own research agenda.

**Exit criterion:** none — steady state.
