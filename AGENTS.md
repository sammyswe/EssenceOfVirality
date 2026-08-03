# AGENTS

Repository-wide expectations for any agent working here. Scoped constraints live in
`.cursor/rules/`; this file is the baseline.

## Orientation

- Read `CONTEXT.md` first for mission, audience, niche, terminology and phase boundaries.
- Canonical sources of truth:
  - Artifact shapes: `schemas/` (JSON Schema; YAML instances everywhere else).
  - Accepted knowledge: `knowledge/` (cites claim IDs; never restates unvetted findings).
  - Claims/hypotheses/contradictions/experiments: `evidence/`.
  - Per-source working artifacts: `research/sources/<source-id>/`.
  - Decisions: `docs/adr/`. Architecture: `docs/architecture/`.
- Workflow selection: user-invoked skills in `.cursor/skills/research-workflows/` are the entry
  points (`/ingest-source`, `/refine-skills-from-source`, `/evaluate-skill`,
  `/prepare-research-pr`, ...). Specialist subagents in `.cursor/agents/` do the stage work; the
  orchestrator reads `pipelines/*.yaml`.

## Evidence rules

- Preserve epistemic status (see the taxonomy in `CONTEXT.md`). Never flatten to "best practices".
- Every claim needs `claim_type`, `evidence_basis`, `confidence` (low/medium/high only),
  `transferability`, `status` and source references.
- Contradictions are recorded, never silently resolved. Supersede via linked records, never by
  overwriting.
- Distribution-model statements are hypotheses about behaviour unless officially disclosed or
  measured first-party. Rewrite unobservable-mechanism claims as testable behavioural hypotheses.
- No unsupported virality guarantees, anywhere, ever.

## Modification boundaries

- `knowledge/`, `evidence/`, `.cursor/skills/`, `schemas/`, `evaluation/rubrics/`, `docs/adr/`
  change **only via pull request** with the repository PR template filled in.
- `.agents/skills/` is third-party (lockfile-managed); never hand-edit.
- Never commit raw video, unpublished media, secrets, or bulk copyrighted source copies
  (see `SECURITY.md` and `docs/guides/content-and-source-handling.md`).
- No agent merges PRs, resolves review threads, or marks PRs ready for review.

## Validation requirements

Before proposing changes, run and pass:

```bash
python tools/validate_artifacts.py
python tools/lint_skills.py
python tools/check_ids.py
python tools/run_fixtures.py
```

## Human review

Stop and request creator review when: a contradiction has `resolution: creator_review_required`;
a skill change targets `maturity: validated` or `stable`; evaluation recommends anything other
than `merge`; or agents disagree (preserve the disagreement in the PR — do not fabricate
consensus).

## Agent skills

Third-party skills are installed under `.agents/skills/` (see
`docs/investigations/installed-agent-skills.md`). Repo configuration for them:

- Issue tracker: `docs/agents/issue-tracker.md`
- Domain docs: `docs/agents/domain.md`
- Triage labels: `docs/agents/triage-labels.md`
