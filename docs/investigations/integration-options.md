# Integration Options

Date: 2026-08-03. Companion to the three component reviews in this directory. Decisions are
formalised in [ADR 0001](../adr/0001-openmontage-integration-strategy.md) (OpenMontage) and touched
by ADR 0002 (monorepo boundaries).

## 1. OpenMontage

Evaluated against commit `4eab34c5` (2026-08-03). Full evidence in
[openmontage-architecture-review.md](openmontage-architecture-review.md). The decisive facts:

1. OpenMontage is consumed as a **cloned working directory** driven by the IDE agent, not a library.
2. It has **no external plugin roots**: custom pipelines/skills/tools live in-tree or as
   project-scoped extensions under `projects/<name>/{scripts,skills,tools}` (sanctioned by
   `skills/meta/capability-extension.md`).
3. It is **AGPL-3.0**; vendoring code into this repository risks copyleft attachment, while
   invoking an unmodified clone at a process boundary does not.
4. It is **high-churn** with strict, evolving schemas — anything authored against it must pin a
   commit.
5. Phase one needs none of its execution capability; production begins in phase 3.

### Option analysis

| Option | Assessment |
|---|---|
| A. Upstream dependency (installed package) | **Not currently possible as imagined.** There is no published package; `setup.py` exposes `lib`/`tools` but skills, manifests, and the Remotion composer are filesystem-coupled to the clone. The "installed version" is a pinned clone. |
| B. Git submodule | Workable for version pinning but adds submodule friction now, in a phase that runs zero OpenMontage code. Deferred; a pinned clone *outside* this repo (recorded ref, gitignored if local) achieves the same reproducibility when phase 3 starts. |
| C. Maintained fork | Maximum control, but immediately incurs upstream merge burden against ~130 commits/month, AGPL obligations on the fork, and divergence risk — before we have evidence that project-scoped extension is insufficient. Rejected for now with explicit re-entry conditions (ADR 0001). |
| D. Adapter + extension package | **Selected, with one refinement.** This repository maintains `integrations/openmontage/` containing: the pinned upstream ref; TikTok pipeline manifest sources; custom stage-skill sources; domain schemas; and a materialisation step that installs these into a pinned local clone's `projects/<name>/` scope (or, where a first-class pipeline is required, into a scratch clone's `pipeline_defs/` — never committed back here). OpenMontage stays at a process/repo boundary; our sources stay proprietary and PR-gated. |

The refinement matters: a naive reading of Option D assumes OpenMontage can *load* external
extension directories. It cannot. The adapter therefore owns the copy/sync direction
(ours → pinned clone), not a load path (clone → ours).

### Phase-one scope for the integration

- Record the decision (ADR 0001) and the extension points
  (`docs/architecture/openmontage-integration.md` at scaffold time).
- Create `integrations/openmontage/` with a README defining what will live there and the pinning
  policy. No clone, no code, no manifests yet.
- Re-evaluation triggers for moving to a fork: (a) project-scoped extensions rejected or removed
  upstream; (b) a needed manifest capability gated on in-tree changes upstream won't accept;
  (c) schema churn breaking the pinned integration more than once per phase.

## 2. mattpocock/skills

Full evidence in [matt-pocock-skills-review.md](matt-pocock-skills-review.md).

- **Decision: install, pinned.** `npx skills@latest add mattpocock/skills#<ref>` with an explicit
  tag/SHA; commit `.agents/skills/` and `skills-lock.json`; upgrades are deliberate PRs.
- MIT licence — no constraints on our usage.
- We adopt its conventions rather than copying its skills into project skills: writing-great-skills
  as authoring standard; user-invoked vs model-invoked split; `docs/agents/` for tracker/domain/
  triage configuration; in-progress/deprecated lifecycle mirrored via maturity metadata.
- Install set proposed in the review (setup, research, writing-great-skills, grilling variants,
  domain-modeling, handoff, triage/to-spec/to-tickets, code-review). Final selection recorded in
  `docs/investigations/installed-agent-skills.md` at setup time.

## 3. Cursor conventions

Full evidence in [cursor-agent-capabilities-review.md](cursor-agent-capabilities-review.md).

- Workflows ("commands") → user-invoked skills in `.cursor/skills/`.
- Domain skill banks → `.cursor/skills/<bank>/<skill>/` (auto-discovered; banks are organisational
  subfolders).
- Specialist agents → `.cursor/agents/*.md`; least privilege enforced in instructions plus
  `readonly: true` where applicable; hooks reserved as a future hard-enforcement point.
- Global + scoped rules → `.cursor/rules/*.mdc`; baseline expectations → root `AGENTS.md`.

## 4. Schema/validation tooling choice (feeds ADR 0004)

Candidates: JSON Schema, Pydantic, Zod.

**Recommendation: JSON Schema (draft 2020-12) as the single canonical definition, with a thin
Python validation runner (`jsonschema` + `PyYAML`) for CI and local checks.**

Justification:

- Language-neutral: artifacts are YAML/JSON files edited by agents and humans; no runtime object
  model is needed in phase one, so Pydantic/Zod would add a codegen or duplication burden for
  little benefit (the anti-goal is "several manually synchronised versions of the same schema").
- OpenMontage validates its manifests and checkpoints with JSON Schema — one mental model across
  both systems, and our future OpenMontage-facing schemas speak the same language.
- Deterministic, dependency-light CI (no hosted model calls), satisfying the requirement to
  separate deterministic checks from optional agent evaluations.
- If phase 3+ produces a real Python application, Pydantic models can be *generated or validated
  against* the same JSON Schemas rather than replacing them.
