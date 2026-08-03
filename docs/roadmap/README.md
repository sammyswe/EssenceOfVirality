# Roadmap

Revision date: 2026-08-03. Six phases; each begins only when its "definition of ready" is met
and its scope is deliberately closed until then. Phase boundaries are enforced by
`.cursor/rules/00-mission.mdc` and the phase-gate notes in scoped rules.

| Phase | Name | State |
|---|---|---|
| 1 | Intelligence infrastructure | **complete — see `../phase-one-review.md`** |
| 2 | Knowledge acquisition at volume | next |
| 3 | Production pipeline integration (OpenMontage) | designed only (`../architecture/future-video-pipeline.md`) |
| 4 | End-to-end creative automation | sketch |
| 5 | Analytics learning loop | scaffolded schemas only (ADR 0007) |
| 6 | Continuous self-improvement | sketch |

## Phase 2 — Knowledge acquisition at volume

Run `/ingest-source` across a curated source list (creator-supplied + issues labelled
`research-source`); populate the planned canonical documents (viewer-behaviour set,
production-techniques set, spotify-mix-niche set); grow both skill banks from evidence; retire
entries in `knowledge/algorithm-model/unknowns.md` where sources genuinely narrow them.
Definition of ready: phase-one PR merged. Exit: canonical documents cover the planned topics
with cited claims; ≥ a handful of validated-tier skills; contradiction handling exercised on
real conflicting sources.

## Phase 3 — Production pipeline integration

Build `integrations/openmontage/` for real: materialise script, Spotify-mix manifest + stage
skills in the clone's project scope, `video_production_manifest` writing, evaluation adapters.
Definition of ready: enough production-technique knowledge to compose defensible edit plans;
re-run `/review-openmontage-integration` and re-pin deliberately. Exit: one raw capture becomes
a post-ready video through the pinned clone with a complete manifest.

## Phase 4 — End-to-end creative automation

Skill-composed edit plans selected from evidence (not hand-picked per video); creator feedback
loop into preference claims; publishing recommendations. Exit: creator effort ≈ record, review,
post.

## Phase 5 — Analytics learning loop

Graduate the scaffold schemas against real TikTok Studio exports (importer, field-name
reconciliation — ADR 0007 review trigger); cohort comparisons; hypothesis/experiment generation
from performance; experiment tracking through `evidence/experiments/`. Exit: at least one
skill-change proposal justified by measured first-party evidence.

## Phase 6 — Continuous self-improvement

Scheduled re-validation of `platform_dependent` claims; periodic source re-ingestion;
skill-maturity reviews driven by accumulated regression and analytics history; the system
proposes its own research agenda. Exit criterion: none — this is the steady state.
