# Phase-One Review

Date: 2026-08-03. Working-sequence step 10: the honest closing assessment of the phase-one
build, distinguishing **proven** (exercised end-to-end) from **built but not yet exercised**
(structure exists, first real use pending).

> **Phase gates revised 2026-08-03:** creator directed a stricter sequence before pipeline work —
> phase 2 (~80 general virality sources), phase 3 (creator grilling → niche skills), phase 4
> (OpenMontage). See **ADR 0008** and `docs/roadmap/README.md`.

## Completion criteria

| Criterion | State | Evidence |
|---|---|---|
| One example source passes the complete research-to-PR workflow | **Proven** | `research/sources/src-20200618-tiktok-newsroom-foryou/` — manifest → extraction → 7 claims + 7 assessments → 2 derived hypotheses → 1 technique record (niche-adapted) → knowledge change proposal → evaluation report → PR summary; knowledge documents seeded with citations |
| Epistemic status preserved end-to-end | **Proven** | Claim types fact/constraint/hypothesis/preference all exercised; hedges preserved verbatim; causal extensions split into hypotheses; confidence low/medium/high only |
| Contradictions can be represented without overwriting | **Built + schema-proven** | `contradiction_record` schema, contradiction-synthesis agent, `detect-knowledge-contradictions` skill, synthetic proof (`tests/fixtures/artifacts/contra-test-fixture-hook-length.yaml`); *not yet exercised on real conflicting sources* — the store was empty (recorded in `evaluation/reports/eval-20260803-foryou-ingestion.yaml`) |
| Skills can be created, criticised, evaluated, versioned | **Built + lint-proven** | 15 skills across 5 banks, all passing lint; skill-quality rubric; critic agent; regression protocol; ADR 0005 lifecycle; *the critic loop and regression protocol have not yet run against a real research-generated skill change* |
| PR-gated human review, no self-merge | **Proven by construction** | ADR 0006, PR template, pr-curator prohibitions, rules; this phase-one PR is itself the first instance |
| General vs niche knowledge separation | **Proven** | Separate banks (`general-virality/` vs `spotify-mix-content/`), separate knowledge areas, the domain analyst as mandatory transfer gate |
| Deterministic validation in CI | **Proven** | Four validators + pytest all green locally (33 artifacts, 33 IDs, 15 skills, 6 fixtures, 8 tests); markdownlint clean; CI workflow committed |
| Architecture documented, decisions recorded | **Proven** | 4 investigations, 7 ADRs, 6 architecture docs, workflow guide, roadmap, guides |

## What was learned building it

- **Cursor's 2026 conventions forced real deviations** from the original sketch (skills under
  `.cursor/skills/`, no `commands/`, subagent `readonly` handling) — recorded in the
  capabilities review and the architecture proposal rather than silently absorbed.
- **Read-only analysts need a scribe**: Cursor's `readonly` flag means five agents return
  artifact YAML for the orchestrator to write verbatim. This is documented in the topology doc;
  it is the design's most likely friction point in practice.
- **PyYAML date coercion** would have made every artifact author quote dates; normalising in the
  validator loader (`tools/common.py`) was the right trade.
- **`creator_statement`** was added to the evidence-basis enum: preferences need an honest basis
  value, and registering the creator brief as a source lets skills cite preferences by claim ID.

## Known weaknesses and risks

1. **Single-source knowledge base**: the working model rests on one 2020 corporate disclosure.
   This is by design (vertical slice, not volume) but nothing in `knowledge/` should be treated
   as settled.
2. **Unexercised loops**: contradiction handling on real conflicts, the critic revision loop,
   regression on a real version bump, and `/compare-evidence` against a populated store all
   await phase 2. Expect first-use friction.
3. **Instruction-level privilege enforcement**: agent boundaries rely on definitions and rules,
   not hard tooling. `.cursor/hooks.json` is the documented escalation if discipline fails.
4. **Behavioural fixture evaluation is untested against real agent runs** — expectations are
   written, but no skill has been executed against a fixture by an agent yet.
5. **OpenMontage churn**: the pin is 2026-08-03; by phase 3 the upstream will have moved.
   `/review-openmontage-integration` exists precisely for this.

## Recommended next steps (phase 2 readiness)

1. Merge this PR (creator decision), then ingest 2–3 further sources — ideally one that
   *conflicts* with the 2020 disclosure (e.g. creator folklore about account size) to exercise
   contradiction handling for real.
2. Run `/refine-skills-from-source` on one of those ingestions to exercise the critic loop and
   regression protocol on a real skill change.
3. Accept or amend the seven proposed ADRs.
4. Populate the planned canonical documents as evidence arrives — resisting the urge to
   pre-create them empty.
