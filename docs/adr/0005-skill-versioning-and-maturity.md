# ADR 0005: Skill Versioning and Maturity

- Status: **Proposed**
- Date: 2026-08-03

## Context

Skills will be generated and refined from research continually. Without lifecycle metadata, the
repository cannot distinguish a fresh candidate from a validated production skill, cannot gate
regression checks, and invites uncontrolled mutation. Cursor's Agent Skills frontmatter supports a
free-form `metadata` map, which is the compliant place for custom fields
(`docs/investigations/cursor-agent-capabilities-review.md`).

## Decision

Every project-authored skill carries, in `SKILL.md` frontmatter under `metadata`:

```yaml
metadata:
  version: 0.1.0            # semver; bumped on any behavioural change
  maturity: experimental    # experimental | provisional | validated | stable | deprecated
  confidence: low           # low | medium | high (no percentages)
  evidence_basis: []        # official | academic | observational | creator_experiment
                            # | first_party_analytics | expert_opinion
  evidence_refs: []         # claim/technique record IDs
  requires_human_approval: true
```

Lifecycle rules:

- New/generated skills start in `.cursor/skills/experimental/` with `maturity: experimental`.
- Promotion (experimental → provisional → validated → stable) and demotion happen only via PR, and
  promotion past `provisional` requires passing fixtures plus, for `validated`+, evidence refs that
  include first-party analytics or a creator experiment.
- `deprecated` skills keep their files (renamed bank or flag) so history and citations survive;
  the linter excludes them from active-bank checks and routers.
- Behavioural changes bump `version` and require a before/after regression record in
  `evaluation/regression/` (spec §17).
- `tools/lint_skills.py` enforces presence and validity of all fields, name==folder, bank
  placement, and no duplicate names.

## Alternatives

- Git history as the only version record — rejected: not machine-checkable at review time and
  invisible to the evaluation harness.
- Separate skill registry file — rejected: duplicates truth already in frontmatter; the linter can
  generate any needed index.

## Consequences

- Maturity becomes an operational gate, not decoration: orchestrator and pipelines may require
  `maturity >= provisional` for production-facing composition later.
- Slight authoring overhead per skill, accepted as the cost of controlled evolution.
