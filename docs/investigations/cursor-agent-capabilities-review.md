# Cursor Agent Capabilities Review

| | |
|---|---|
| Date inspected | 2026-08-03 |
| Sources | cursor.com/docs (rules, skills, subagents, hooks, cloud-agent setup, customize overview), agentskills.io spec |
| Verdict | **Use rules (`.mdc`), Agent Skills (`SKILL.md`), and subagents (`.cursor/agents/*.md`). Do not use `.cursor/commands/` — it is legacy.** |

This review exists because the specification's proposed structure predates several 2026 changes.
Deviations from the original proposed tree are justified here and in the
[architecture proposal](../architecture/phase-one-architecture-proposal.md).

## 1. Project rules — `.cursor/rules/*.mdc`

- One rule per `.mdc` file (extension required; plain `.md` in that directory is ignored).
  Subfolders are allowed for organisation.
- Frontmatter: `description`, `globs` (comma-separated), `alwaysApply`. Four types:

| Type | `alwaysApply` | `description` | `globs` |
|---|---|---|---|
| Always | `true` | — | — |
| Auto-attached (file-scoped) | `false` | — | provided |
| Agent-requested | `false` | provided | omitted |
| Manual (`@`-mention) | `false` | omitted | omitted |

- Note: "agent-requested" (description-only) rules are themselves being migrated toward skills by
  Cursor's own `/migrate-to-skills`; for this repo we use **always** rules for global discipline and
  **glob-scoped** rules for directory-specific constraints, which remain firmly in the rules system.
- Best practice per docs: keep rules under 500 lines, split composable rules, reference files with
  `@filename` rather than pasting content. This endorses the specification's "no one enormous rule"
  requirement.
- `AGENTS.md` (root, and nested per-directory) is fully supported and coexists with rules: always-on
  baseline instructions in `AGENTS.md`, conditional/scoped constraints in rules.

## 2. Commands are legacy — use user-invoked skills

The dedicated commands docs page has been removed. Cursor 2.4 shipped `/migrate-to-skills`, which
converts workspace commands into skills with `disable-model-invocation: true`; invocation UX is
identical (`/name` in chat).

**Consequence**: the specification's `/ingest-source`, `/refine-skills-from-source`,
`/prepare-research-pr` etc. will be implemented as **user-invoked skills** under
`.cursor/skills/`, not as `.cursor/commands/` files. This also happily converges with the
mattpocock convention (user-invoked skills are slash-invoked and carry
`disable-model-invocation: true`).

## 3. Subagents — `.cursor/agents/*.md`

- One markdown file per subagent: YAML frontmatter + the system prompt as body.
- Documented frontmatter: `name` (kebab-case, `/name` invocable), `description` (drives automatic
  delegation), `model` (default `inherit`), `readonly` (bool), `is_background` (bool).
- **There is no `tools` allowlist field** in Cursor's schema. Least privilege must be enforced at
  the instruction level (explicit allowed/prohibited files and actions in the body) plus
  `readonly: true` for analysis-only agents. Hooks (`subagentStart`) can deny by type if hard
  enforcement is ever needed.
- Subagents run in isolated context windows and return a summary — the right vehicle for our
  specialist analysts. Docs guidance: single-purpose one-shot tasks should be skills, not subagents.
- Since Cursor 2.5 subagents may spawn one level of child subagents — sufficient for an
  orchestrator that fans out to specialists.

**Consequence**: the specification's `agents/definitions/` maps to `.cursor/agents/`. Handoff
protocols and team topology become documentation (`docs/architecture/agent-topology.md`,
`agents/protocols/` content folded into docs) rather than a parallel top-level tree that Cursor
would not read.

## 4. Agent Skills — the open standard, natively supported

- Cursor discovers skills recursively in `.cursor/skills/` and `.agents/skills/` (project and user
  level; `.claude/skills/` and `.codex/skills/` read for compatibility). A skills folder anywhere in
  the repo is discovered, and skills in nested directories are auto-scoped to files under that
  directory.
- Category subfolders are purely organisational; identity comes from the folder directly containing
  `SKILL.md`, and frontmatter `name` must match that folder's name. So
  `.cursor/skills/general-virality/analyse-first-frame/SKILL.md` is valid and discovered.
- Frontmatter: `name` (required), `description` (required), `paths` (glob scoping; `globs` is a
  legacy fallback), `disable-model-invocation`, `metadata` (arbitrary key-value map).
- **`metadata` is where our custom fields live** (maturity, confidence, evidence basis, version) —
  spec-compliant without inventing frontmatter keys that tooling might reject.
- Progressive disclosure: `scripts/`, `references/`, `assets/` subdirectories, referenced by
  relative path from a lean `SKILL.md`. Matches the writing-great-skills guidance.
- Built-in skills relevant to us: `/create-skill`, `/create-rule`, `/create-subagent`,
  `/migrate-to-skills`.

**Consequence**: the specification's top-level `skills/` tree would **not** be auto-discovered by
Cursor. The domain skill banks therefore live at `.cursor/skills/<bank>/<skill>/`, keeping the
bank separation (`general-virality/`, `spotify-mix-content/`, `research-workflows/`, `meta/`,
`experimental/`) as organisational subfolders. Third-party installed skills stay in
`.agents/skills/` (the `skills` CLI's canonical location), giving a clean physical separation
between installed and authored skills.

## 5. Hooks and cloud environment

- `.cursor/hooks.json` (project-level, version-controlled) with events across the agent loop
  (`preToolUse`, `beforeShellExecution`, `afterFileEdit`, `subagentStart`, ...). Command hooks run
  in cloud agents too. Not needed in phase one; noted as the future hard-enforcement point for
  agent least-privilege if instruction-level discipline proves insufficient.
- `.cursor/environment.json` defines reproducible cloud-agent environments (`install`, `start`,
  `terminals`, snapshot/Dockerfile). Worth adding once the repo has real dependencies (validators,
  linters) so cloud agents run checks without ad-hoc setup.

## 6. Mapping the specification's proposed tree to current conventions

| Specified | Current-convention replacement | Reason |
|---|---|---|
| `.cursor/commands/` | User-invoked skills in `.cursor/skills/` | Commands are legacy (Cursor 2.4) |
| Top-level `skills/` banks | `.cursor/skills/<bank>/<skill>/` | Discovery only under `.cursor/skills/` / `.agents/skills/` |
| `agents/definitions/` | `.cursor/agents/*.md` | Native subagent location |
| `agents/protocols/`, `teams/`, `prompts/` | `docs/architecture/agent-topology.md` + handoff schemas in `schemas/` | Prompts live in the subagent body; protocols are docs + schemas |
| Third-party skill copies | `.agents/skills/` + `skills-lock.json` | `skills` CLI canonical layout |

Everything else in the specified tree (research/, knowledge/, evidence/, analytics/, evaluation/,
pipelines/, integrations/, docs/, schemas-as-`packages/shared-schemas`) is tool-agnostic and is
addressed in the architecture proposal on its own merits.
