# Matt Pocock Skills Review

| | |
|---|---|
| Repository | <https://github.com/mattpocock/skills> |
| Commit inspected | `2ab958093e83e0ec752e6c1c5932da465bf23e0c` |
| Commit date | 2026-07-28 |
| Date inspected | 2026-08-03 |
| Package | `mattpocock-skills` v1.1.0 (private, no bin — installed via the separate `skills` CLI) |
| Licence | MIT |
| Verdict | **Install selected skills via the `skills` CLI, pinned to a tag/commit; adopt its authoring and lifecycle conventions for our own skills.** |

## Installation mechanics (current, verified against the repo)

The repo itself is not a CLI. Consumers use the external npm package `skills`
(skills.sh, currently `skills@1.5.x`):

```bash
npx skills@latest add mattpocock/skills            # interactive skill + agent selection
npx skills@latest add mattpocock/skills#v1.1.0     # pinned to a tag (also supports commit SHAs)
npx skills update                                   # intentional upgrade
```

What the installer does:

1. Clones the source repo and discovers `SKILL.md` files under `skills/<bucket>/<name>/`.
2. Lets you select which skills and which agents (Cursor → project path `.agents/skills/`).
3. Installs a **canonical copy** per skill into `.agents/skills/<skill-name>/` (flat — upstream
   bucket names are not preserved), with symlinks into other agents' directories if selected.
4. Writes **`skills-lock.json`** at the project root (source, optional `ref`, content hash).

A Claude Code plugin channel also exists (`claude plugins install mattpocock-skills`) but is
read-only and Claude-specific; the README warns against using both channels (double installs). For
this repository the `skills` CLI path is correct.

**Pinning policy for this project**: install with an explicit `#<tag-or-sha>` ref, commit
`.agents/skills/` and `skills-lock.json` to git, and treat `npx skills update` as a deliberate,
PR-reviewed upgrade. Installed skills and versions will be recorded in
`docs/investigations/installed-agent-skills.md` at setup time (step 6 of the working sequence).

## Skill format conventions

```
skills/<bucket>/<skill-name>/
  SKILL.md               # required; frontmatter: name, description,
                         #   optional disable-model-invocation, argument-hint
  agents/openai.yaml     # Codex display metadata + invocation policy
  <COMPANION>.md ...     # progressive-disclosure references
```

- `name` (kebab-case) must equal the directory name and doubles as the `/slash` invocation.
- **Invocation split** (`.agents/invocation.md`): *user-invoked* skills set
  `disable-model-invocation: true` and carry a human-facing one-line description (no trigger
  lists); *model-invoked* skills omit the flag and put rich "Use when..." triggers in the
  description. A user-invoked skill may call model-invoked skills, never another user-invoked one.
- Cross-skill reuse is by invoking the owning skill (`/grilling`), never by deep-linking another
  skill's companion files.

## `writing-great-skills` — the current authoring standard

`write-a-skill` was **removed** at v1.0.0 (breaking change in `CHANGELOG.md`);
`skills/productivity/writing-great-skills/SKILL.md` + `GLOSSARY.md` is the current guidance. Core
rules we will adopt for our own skill-authoring standard:

- **Root virtue: predictability** — the same *process* every run, not the same output.
- **Descriptions**: front-load the leading word; one trigger per genuine branch; collapse synonym
  restatements; strip identity already stated in the body.
- **Steps vs Reference**: steps are ordered actions each ending on a checkable **completion
  criterion**; reference is consulted-on-demand material. Push branch-specific material into
  companion files behind explicit context pointers (progressive disclosure); inline only what every
  branch needs.
- **Granularity**: split by invocation (a distinct leading word, or other skills need to reach it)
  or by sequence (hide post-completion steps behind a real context boundary).
- **Pruning discipline**: single source of truth per meaning; hunt no-op sentences and delete them;
  prefer strengthening a leading word over adding adverbs.
- **Named failure modes**: premature completion, duplication, sediment, sprawl, no-op, negation
  (prompt the positive; prohibitions only as hard guardrails paired with what to do instead).
- Model-invoked descriptions carry permanent context load — every model-invoked skill's description
  sits in the window, so the bar for making a skill model-invoked is high. Many user-invoked skills
  justify a **router skill** (upstream: `ask-matt`).

## What `setup-matt-pocock-skills` configures

Prompt-driven (explore → present → confirm → write). It creates in the consumer repo:

| Artifact | Content |
|---|---|
| `docs/agents/issue-tracker.md` | Tracker operations (GitHub via `gh` for us) incl. wayfinding operations; PRs-as-request-surface defaults to *no* |
| `docs/agents/triage-labels.md` | Only if `triage` installed. Default labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix` |
| `docs/agents/domain.md` | Points at root `CONTEXT.md` + `docs/adr/` (single-context default) |
| `## Agent skills` block | Added to existing `AGENTS.md` (or `CLAUDE.md`) |

`ready-for-agent` issues get a durable **agent brief** comment (behavioural acceptance criteria, no
stale file paths); `ready-for-human` uses the same brief structure plus why it cannot be delegated.
Hard dependencies on this setup: `to-tickets`, `to-spec`, `triage` (its ADR 0001).

This aligns naturally with our planned layout: we already intend root `CONTEXT.md`, `docs/adr/` and
GitHub as tracker, so the setup skill's defaults fit without customisation.

## Skills relevant to this repository

Recommended install set (final selection recorded at setup time):

| Skill | Why |
|---|---|
| `setup-matt-pocock-skills` | One-time repo configuration (required first) |
| `research` (model-invoked) | Primary-source investigation producing cited in-repo Markdown — complements but does not replace our domain-specific ingestion workflow |
| `writing-great-skills` | Authoring reference for every skill we write |
| `grilling` / `grill-with-docs` | Interview loops for sharpening `CONTEXT.md` and ADRs |
| `domain-modeling` | Maintains glossary + ADR discipline |
| `handoff` | Session-to-session continuity for long investigations |
| `triage`, `to-spec`, `to-tickets` | GitHub issue conventions (agent-ready vs human-review) |
| `code-review` | Diff review during skill-refinement PRs |

Not needed in phase one: `tdd`, `prototype`, `implement`, `wayfinder` (revisit when code volume
grows), anything in `misc/`/`personal/`.

## Lifecycle conventions to mirror

Upstream keeps `skills/in-progress/` (drafts, excluded from promotion channels) and
`skills/deprecated/` (retained for archaeology, excluded from install/link lists). We mirror this
with our own maturity metadata (`experimental → provisional → validated → stable → deprecated`,
see [ADR 0005](../adr/0005-skill-versioning-and-maturity.md)) plus an `experimental/` bank kept
physically separate from production banks.

## Distinctions this project must maintain

| Category | Location | Managed by |
|---|---|---|
| Third-party operational skills | `.agents/skills/` (flat) + `skills-lock.json` | `skills` CLI; never hand-edited |
| Project domain skills (general virality, Spotify mix, research, meta) | `.cursor/skills/<bank>/<skill>/` | Authored here, PR-gated |
| OpenMontage production skills | OpenMontage clone (phase 3); extension specs in `integrations/openmontage/` | Upstream + our extension package |
| Experimental / generated candidate skills | `.cursor/skills/experimental/` | Promoted or deleted via PR |
| Deprecated skills | `maturity: deprecated` + moved out of active banks | PR-gated |
