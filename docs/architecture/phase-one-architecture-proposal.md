# Phase-One Architecture Proposal

Status: **PROPOSED — awaiting creator review. No scaffold has been created.**
Date: 2026-08-03. Grounded in the four documents under `docs/investigations/`.

## 1. What phase one delivers

Infrastructure so that the creator can paste a source into Cursor and ask for the full research
workflow: registration → extraction → claims → evidence assessment → contradiction check →
knowledge/skill proposals → evaluation → a pull request that a human reviews. Nothing that edits
video, posts content, or merges itself.

## 2. Proposed directory tree

Refined from the specification per the investigation findings (all deviations justified in
`docs/investigations/cursor-agent-capabilities-review.md` §6). Every listed directory has a
defined near-term purpose; directories from the original sketch with no phase-one workflow are
deferred, not created empty.

```
/
├── README.md                     # project, phase, how to run the first workflow
├── AGENTS.md                     # repo-wide agent expectations + agent-skills block
├── CONTEXT.md                    # creator objective, audience, niche, terminology
├── CONTRIBUTING.md               # commit standard, PR gate, changelog policy
├── LICENSE                       # proprietary/all-rights-reserved (creator to confirm)
├── SECURITY.md                   # secret handling, local-first media policy
├── CHANGELOG.md
├── .gitignore                    # tmp/, .env, media extensions, analytics/raw exports
├── .editorconfig
├── .env.example
│
├── .cursor/
│   ├── rules/                    # global + scoped .mdc rules (see §8)
│   ├── agents/                   # 13 specialist subagent definitions (see §4)
│   └── skills/                   # PROJECT-AUTHORED skills, auto-discovered by Cursor
│       ├── general-virality/     #   bank A (exemplars only in phase one)
│       ├── spotify-mix-content/  #   bank B (exemplars only)
│       ├── research-workflows/   #   user-invoked workflow skills: ingest-source,
│       │                         #   refine-skills-from-source, prepare-research-pr, ...
│       ├── meta/                 #   skill-authoring standard, classify-evidence-claim, ...
│       └── experimental/         #   candidate skills awaiting promotion
│
├── .agents/skills/               # THIRD-PARTY skills (skills CLI canonical dir; lockfile-managed)
├── skills-lock.json
│
├── .github/
│   ├── ISSUE_TEMPLATE/           # research-source, skill-proposal, experiment-proposal, bug, adr
│   ├── PULL_REQUEST_TEMPLATE.md  # the research-PR template from spec §21
│   ├── workflows/ci.yml          # deterministic checks only (see §7)
│   └── CODEOWNERS
│
├── schemas/                      # CANONICAL JSON Schemas (single source of truth)
│   ├── source-manifest.schema.json
│   ├── extraction-report.schema.json
│   ├── claim-record.schema.json
│   ├── evidence-assessment.schema.json
│   ├── technique-record.schema.json
│   ├── contradiction-record.schema.json
│   ├── knowledge-change-proposal.schema.json
│   ├── skill-change-proposal.schema.json
│   ├── evaluation-report.schema.json
│   ├── analytics-observation.schema.json      # scaffold (phase 5 consumer)
│   ├── experiment-proposal.schema.json
│   ├── pull-request-summary.schema.json
│   └── video-production-manifest.schema.json  # scaffold (phase 3+ consumer)
│
├── research/                     # per-source working artifacts (YAML validated against schemas/)
│   ├── sources/<source-id>/      #   manifest.yaml, extraction.yaml, claims/, assessment.yaml
│   ├── conflicts/                #   contradiction records spanning sources
│   └── rejected/                 #   rejected sources/claims with reasons (nothing silently dropped)
│
├── knowledge/                    # canonical curated documents (see §6)
│   ├── algorithm-model/
│   ├── viewer-behaviour/
│   ├── production-techniques/
│   ├── spotify-mix-niche/
│   ├── platform-constraints/
│   ├── glossary.md
│   └── index.md
│
├── evidence/
│   ├── claims/                   # promoted, cross-source claim records (YAML)
│   ├── hypotheses/
│   ├── experiments/              # experiment proposals + (later) results
│   └── contradictions/           # standing unresolved disagreements
│
├── analytics/                    # SCAFFOLD ONLY in phase one
│   ├── README.md                 # schema pointers, lineage model, what not to commit
│   └── examples/                 # one synthetic example record
│
├── evaluation/
│   ├── rubrics/                  # multidimensional rubrics (no single virality score)
│   ├── fixtures/                 # the six hypothetical-video fixtures (spec §17)
│   ├── regression/               # before/after records for skill changes
│   └── reports/                  # evaluation reports (YAML validated)
│
├── pipelines/                    # workflow manifests the Orchestrator reads (OpenMontage-inspired)
│   ├── research-ingestion.yaml
│   └── skill-refinement.yaml
│
├── integrations/openmontage/     # pinned ref, extension specs; no code in phase one
│
├── tools/                        # deterministic Python validators (see §7)
│   ├── validate_artifacts.py
│   ├── lint_skills.py
│   ├── check_ids.py
│   └── run_fixtures.py
│
├── tests/                        # unit tests for tools/
├── docs/
│   ├── architecture/             # system-overview, research-to-skill-flow, agent-topology,
│   │                             # evidence-model, openmontage-integration, future-video-pipeline
│   ├── adr/                      # 0001–0007 (proposed set exists)
│   ├── investigations/           # completed (this PR)
│   ├── workflows/                # human-facing walkthroughs of each workflow skill
│   ├── roadmap/                  # phases 1–6
│   ├── guides/content-and-source-handling.md
│   └── agents/                   # written by setup-matt-pocock-skills (tracker/domain/triage)
│
└── tmp/                          # gitignored scratch
```

Deviations from the specification's sketch, with reasons:

| Specified | Proposed | Reason |
|---|---|---|
| `.cursor/commands/` | user-invoked skills | Commands are legacy in Cursor (2.4+) |
| top-level `skills/` | `.cursor/skills/<bank>/` | Only `.cursor/skills/`/`.agents/skills/` are discovered |
| top-level `agents/{definitions,protocols,prompts,teams}` | `.cursor/agents/` + `docs/architecture/agent-topology.md` + `schemas/` | Native subagent location; prompts live in definition bodies; protocols are schemas + docs |
| `packages/{evidence-model,source-ingestion,skill-linter,evaluation-runner,shared-schemas}` | `schemas/` + `tools/` | Five packages is premature for four small scripts and a schema set; extraction into packages is a later, mechanical refactor (ADR 0002) |
| `apps/{cli,future-studio}` | deferred | No phase-one workflow writes there |
| `research/{inbox,extracted,reviews,manifests}` as siblings | consolidated per-source under `research/sources/<id>/` | One directory per source keeps lineage trivially traceable; separate top-level trays invite orphaned files |
| `pipelines/{analytics-feedback,video-production,manifests}` | deferred to phases 3–5 | Documented in roadmap instead |
| `evidence/observations`, `evidence/schemas`, `evaluation/schemas`, `analytics/schemas` | single `schemas/` | Single source of truth for all schemas (anti-goal: manually synchronised copies) |

## 3. Artifact and evidence model

- **Canonical schema mechanism: JSON Schema draft 2020-12** in `schemas/`, one file per artifact
  type, validated by `tools/validate_artifacts.py` (Python `jsonschema` + `PyYAML`). Justification
  in `docs/investigations/integration-options.md` §4; formalised in ADR 0004.
- **Artifacts are YAML files** (human-diffable, agent-editable, PR-reviewable) with the common
  envelope required by the spec: `id`, `created_at`, `produced_by` (agent), `inputs` (artifact
  IDs), `status`, `version`, optional `confidence`, `human_review` state, `derived_artifacts`.
- **Claim records** carry the epistemic taxonomy verbatim from the spec: `claim_type`
  (fact/finding/hypothesis/heuristic/pattern/anecdote/constraint/preference/experiment_result),
  `evidence_basis`, `transferability`, `confidence` (low/medium/high — no false-precision
  percentages), `status` (active/disputed/superseded/rejected/testing), `limitations`,
  `contradictions`, `proposed_actions`. No automatic time decay; publication dates preserved;
  platform-dependent findings flagged for revalidation (ADR 0003).
- **ID scheme**: `src-`, `claim-`, `tech-`, `contra-`, `eval-`, `exp-`, `kcp-`/`scp-` prefixes with
  date + slug (e.g. `claim-20260803-hook-first-second-comprehension`). Uniqueness enforced by
  `tools/check_ids.py` in CI.
- Flow (each arrow is a validated artifact, not conversation):
  `SourceManifest → ExtractionReport → ClaimRecords → EvidenceAssessments →
  TechniqueRecords / distribution hypotheses → ContradictionRecords →
  Knowledge/SkillChangeProposals → EvaluationReport → PullRequestSummary`.

## 4. Agent topology

Thirteen subagents in `.cursor/agents/`, exactly as specified (§11 of the spec): research-intake
coordinator, source-extraction, evidence-analyst, distribution-model-analyst,
virality-technique-analyst, spotify-mix-domain-analyst, contradiction-synthesis, skill-architect,
skill-critic, evaluation-agent, analytics-learning (scaffold-level duties only in phase one),
pr-curator, orchestrator.

Cursor-specific constraints discovered in the investigation:

- No `tools` frontmatter allowlist exists. Least privilege is enforced by (a) explicit
  allowed/prohibited file paths and actions in each definition body, (b) `readonly: true` on
  analysis-only agents (evidence-analyst, distribution-model-analyst, virality-technique-analyst,
  spotify-mix-domain-analyst, skill-critic), and (c) the always-on rules (PR-only mutation, no
  silent contradiction resolution). Hooks are the documented future hard-enforcement point.
- One level of subagent nesting is supported — the orchestrator (invoked in the main session by
  the workflow skills) fans out to specialists; specialists do not spawn further agents.
- Handoffs are the YAML artifacts of §3; the orchestrator reads `pipelines/*.yaml` manifests
  (stage → responsible agent → required input/output artifacts → gate), an audit-trail pattern
  adapted from OpenMontage's manifest/checkpoint design without reusing its code.

## 5. Research workflows

User-invoked skills (the current-convention replacement for commands), each documented in
`docs/workflows/`:

| Skill | Covers spec commands |
|---|---|
| `ingest-source` | `/ingest-source`, `/analyse-source` (analysis stages are the same manifest) |
| `compare-evidence` | `/compare-evidence` |
| `refine-skills-from-source` | `/refine-skills-from-source`, `/propose-skill-change` |
| `evaluate-skill` | `/evaluate-skill` |
| `prepare-research-pr` | `/prepare-research-pr` |
| `propose-experiment` | `/propose-experiment` |
| `ingest-tiktok-analytics` | scaffold: validates a CSV against the analytics schema, stores an observation; no learning loop yet |
| `review-openmontage-integration` | re-runs the pinned-ref review checklist |

`/setup-project` is covered by the installed `setup-matt-pocock-skills` plus a short
`docs/guides/` setup page rather than a bespoke skill.

Phase-one source connectors: web URLs (fetch + readability extraction), plain text/Markdown, PDFs
(text extraction), YouTube (provided transcripts; URL fetch of transcript where lawful), CSV
analytics files. A `source_type` field plus per-type extraction notes keep the interface
extensible without building every connector.

## 6. Knowledge base

Canonical documents exactly as sketched in spec §15 (algorithm-model, viewer-behaviour,
production-techniques, spotify-mix-niche), each with: current conclusion, supporting claims (by
ID), disputed claims, open questions, practical implications, related skills, related experiments,
revision date. `knowledge/index.md` maps topics → documents → related skills;
`knowledge/glossary.md` holds the epistemic taxonomy and UK-house/Spotify vocabulary. In phase one
these are created with structure and seed content only where the fixture workflow needs them —
knowledge acquisition is phase two.

The platform-model vs production-rules distinction is structural: distribution behaviour lives in
`knowledge/algorithm-model/` + `knowledge/viewer-behaviour/` and is *never* cited as a direct
lever; production rules live in `knowledge/production-techniques/` and every technique record
links `production_rule → intended viewer effects → observable metrics`, per spec §3.

## 7. Evaluation harness and CI

Deterministic (CI, no model calls):

- `validate_artifacts.py` — every YAML artifact against its schema.
- `lint_skills.py` — required frontmatter and `metadata` fields (maturity, confidence,
  evidence_basis, version), name==folder, bank placement, no duplicate names, experimental
  separation, references resolve, banned patterns (e.g. "guaranteed viral", bare "make it
  engaging" without operational detail).
- `check_ids.py` — global ID uniqueness and dangling references.
- `run_fixtures.py` — structural fixture checks (expected artifact outputs exist and validate).
- markdownlint + link checking + secret scanning (gitleaks) + pytest for `tools/`.

Agent-driven (not in CI; invoked by `evaluate-skill` / the evaluation agent): running skills
against the six behavioural fixtures, before/after regression comparison with critic review, and
the human review packet. Multidimensional rubrics in `evaluation/rubrics/`; no universal virality
score.

## 8. Cursor rules plan

- `00-mission.mdc` (always): mission, phase boundary, evidence discipline, PR-only mutation, no
  virality guarantees, no silent contradiction resolution, read canonical knowledge before editing
  skills.
- Scoped (glob-attached, one concern each): `skills.mdc` (`.cursor/skills/**`), `research.mdc`,
  `knowledge.mdc`, `evidence.mdc`, `evaluation.mdc`, `adr.mdc` (`docs/adr/**`),
  `openmontage.mdc` (`integrations/openmontage/**`), `analytics.mdc`.
- Root `AGENTS.md` carries the baseline orientation (what this repo is, where canonical sources
  live, which workflow skill to use) so any agent — including non-Cursor ones — starts correctly.

## 9. GitHub workflow

Protected `main` (documented recommendation — settings are applied by the creator), PR template
per spec §21, CODEOWNERS assigning everything to the creator, issue templates (research-source,
skill-proposal, experiment-proposal, bug, ADR), a single `ci.yml` running only the deterministic
checks of §7, Dependabot for pip/github-actions, Conventional Commits, Keep-a-Changelog policy.
Research-derived changes always arrive as PRs; nothing self-merges.

## 10. OpenMontage strategy (summary)

Option D, refined: adapter + extension sources in `integrations/openmontage/`, materialised into a
pinned external clone's project scope when phase 3 begins; AGPL kept at a process boundary; fork
only on defined triggers. Full reasoning in ADR 0001 and the investigation documents. Phase-one
footprint: documentation and the pinned-ref record only.

## 11. Risks and unresolved decisions

| Item | State |
|---|---|
| OpenMontage churn may invalidate extension assumptions before phase 3 | Accepted; `review-openmontage-integration` skill re-checks the pinned ref; ADR 0001 lists fork triggers |
| Cursor subagents lack hard tool allowlists | Mitigated by instructions + `readonly` + rules; hooks documented as escalation |
| LICENSE choice for this repo (private/proprietary vs none) | **Creator decision needed** — proposal assumes all-rights-reserved private repo |
| Exact mattpocock skill selection | Proposed set in the review doc; finalised at setup (step 6) and recorded in `installed-agent-skills.md` |
| YouTube transcript acquisition method (lawful tooling) | Deferred; phase one accepts pasted transcripts, which is sufficient for the vertical slice |
| Whether analytics importers need Python packaging earlier than expected | Revisit when real exports arrive (phase 5) |
| ADR 0007 (analytics lineage) depends on unseen real TikTok export formats | Kept `proposed`; schema fields marked provisional |

## 12. Acceptance

If this proposal is approved (or amended), the next steps are the working sequence's steps 5–10:
minimal scaffold → mattpocock setup → Cursor rules/agents/skills → schemas + validators → one
vertical-slice source through the complete research-to-PR workflow → phase-one review.
