# Installed Agent Skills

Third-party operational skills installed under `.agents/skills/` — distinct from project domain
skills (`.cursor/skills/`), OpenMontage production skills (external, phase 3), and
experimental/candidate skills.

| | |
|---|---|
| Source | `mattpocock/skills` pinned to tag **`v1.1.0`** |
| Installer | `skills` CLI (`npx skills@latest add "mattpocock/skills#v1.1.0" --agent cursor --copy`) |
| Installed | 2026-08-03 |
| Lockfile | `skills-lock.json` (source, ref, per-skill content hashes) |
| Mode | `--copy` (independent copies; no symlinks — repo is self-contained) |
| Licence | MIT |
| Upgrade policy | Deliberate only: `npx skills update` on a branch, reviewed as a PR. Never hand-edit `.agents/skills/`. |

## Installed skills and their purpose here

| Skill | Invocation | Purpose in this repository |
|---|---|---|
| `setup-matt-pocock-skills` | user | One-time repo configuration (performed 2026-08-03; see below) |
| `writing-great-skills` | user | Prose-craft authority behind our `skill-authoring-standard` meta skill |
| `research` | model | General primary-source investigation; complements (does not replace) `/ingest-source`, which owns evidence classification and the artifact trail |
| `grilling` | model | Reusable interview loop |
| `grill-me` | user | Stateless requirement interviews |
| `grill-with-docs` | user | Interviews that update `CONTEXT.md`/ADRs |
| `domain-modeling` | model | Glossary + ADR discipline |
| `handoff` | user | Session-to-session continuity on long investigations |
| `triage` | user | GitHub issue state machine (labels below) |
| `to-spec` | user | Conversation → published spec |
| `to-tickets` | user | Spec → tracked tickets with blocking edges |
| `code-review` | model | Diff review during research/skill PRs |

Not installed (revisit when needed): `wayfinder`, `implement`, `tdd`, `prototype`,
`diagnosing-bugs`, `codebase-design`, `improve-codebase-architecture`, `ask-matt`,
`resolving-merge-conflicts`, `teach`, everything in `misc/`/`personal/`/`in-progress/`.

## Setup performed (per the setup skill's procedure)

- Issue tracker: **GitHub** via `gh` → `docs/agents/issue-tracker.md`
  (PRs-as-request-surface: no).
- Triage labels: defaults kept (`needs-triage`, `needs-info`, `ready-for-agent`,
  `ready-for-human`, `wontfix`) → `docs/agents/triage-labels.md`. Issue templates apply
  `needs-triage` on creation.
- Domain docs: single-context — root `CONTEXT.md` + `docs/adr/` → `docs/agents/domain.md`.
- `AGENTS.md` carries the "Agent skills" section pointing at the three docs.

## Interaction rules with project skills

- Project workflow skills own the research pipeline; installed skills are general-purpose
  engineering/productivity operations.
- A project skill may invoke an installed model-invoked skill (e.g. `/research` for background
  investigation) but installed skills never write to `research/`, `evidence/` or `knowledge/`
  artifact structures — only project workflows produce artifacts.
