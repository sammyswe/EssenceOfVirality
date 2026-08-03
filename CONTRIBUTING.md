# Contributing

This is a personal project; the creator is the only approver. These conventions exist so agents
and future collaborators behave consistently.

## Branches and pull requests

- Never commit directly to `main`. All changes to `knowledge/`, `evidence/`, `.cursor/skills/`,
  `schemas/`, `evaluation/rubrics/` and `docs/adr/` must arrive via PR using the template.
- Research-derived PRs are assembled by the PR curator workflow and are **never** self-merged.
- Recommended branch naming: `research/<source-id>`, `skills/<skill-name>`, `docs/<topic>`.

## Commit standard

Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`), with scopes
encouraged (`feat(skills): ...`, `docs(adr): ...`). One logical change per commit.

## Changelog policy

`CHANGELOG.md` follows Keep a Changelog. Update the Unreleased section in any PR that changes
behaviour of workflows, schemas, skills or validators. Documentation-only and artifact-only
(research data) changes do not require entries.

## Checks

CI runs deterministic checks only (schema validation, skill lint, ID checks, fixture structure,
markdownlint, secret scan, pytest). Run them locally first:

```bash
pip install -r tools/requirements.txt
python tools/validate_artifacts.py && python tools/lint_skills.py \
  && python tools/check_ids.py && python tools/run_fixtures.py && pytest -q
```

Agent evaluations (fixture behaviour, before/after regression) are committed as reports under
`evaluation/reports/` — they are review inputs, not CI gates.

## Skills

Author skills per `.cursor/skills/meta/skill-authoring-standard/`. New research-generated skills
start in `.cursor/skills/experimental/` with `maturity: experimental`; promotion follows
ADR 0005.
