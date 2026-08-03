---
name: skill-authoring-standard
description: The repository's standard for writing and revising skills. Use when authoring a new skill, revising an existing skill, or reviewing a skill change proposal.
metadata:
  version: 0.1.0
  maturity: provisional
  confidence: high
  evidence_basis: []
  requires_human_approval: false
---

# Skill authoring standard

Reference skill (no steps). Based on the installed `writing-great-skills` guidance
(`.agents/skills/writing-great-skills/`) plus this repository's evidence discipline. The
authority for structure is this document; for prose craft, writing-great-skills.

## Required shape

```
.cursor/skills/<bank>/<skill-name>/
  SKILL.md            # lean; steps or reference, not both muddled
  references/*.md     # progressive disclosure for branch-specific material
```

Frontmatter: `name` (== folder), `description`, optional `disable-model-invocation`,
`argument-hint`, and `metadata` (version/maturity/confidence/evidence_basis/
requires_human_approval; domain banks: evidence_refs). Lint: `python3 tools/lint_skills.py`.

## Invocation choice

User-invoked (`disable-model-invocation: true`): workflow entry points a human types. Human-facing
one-line description, no trigger lists. Model-invoked: skills other skills or relevance must
reach. Rich "Use when..." triggers — one per genuine branch, leading word first. Every
model-invoked description is permanent context load; justify it.

## Body requirements

- **Steps** end on a checkable completion criterion. No "consider X" without a decision rule.
- **Output contract**: the artifact/format the skill produces, assertable by a fixture.
- **Failure handling**: what to do when preconditions fail — named, not implied.
- **Domain skills additionally**: intended viewer effects per technique (metric targets);
  evidence honesty (`evidence_refs` claims actually support the instructions, at their
  confidence); anti-patterns with the positive alternative stated; at least one worked example
  and one counterexample.

## Prohibitions (hard guardrails)

- No promises of certain virality; no direct-algorithm-effect claims — state viewer behaviour.
- No vague quality adjectives as instructions; replace with the check that would verify them.
- No knowledge dumps: conclusions live in `knowledge/`, linked not restated.
- No new skill when an existing skill owns the decision — modify it instead.

## Pruning discipline

Single source of truth per meaning; delete no-op sentences; prefer a stronger leading word over
stacked adverbs; disclose branch-specific reference material rather than inlining. Failure modes
to hunt: premature completion, duplication, sediment, sprawl, no-ops, negation-without-
alternative.

## Lifecycle

New skills start in `experimental/`, `maturity: experimental`, `version: 0.1.0`. Promotion and
version bumps per ADR 0005 (regression bundle required for behavioural changes). Deprecation
keeps the file with `maturity: deprecated`.
