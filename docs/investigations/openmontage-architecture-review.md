# OpenMontage Architecture Review

| | |
|---|---|
| Repository | <https://github.com/calesthio/OpenMontage> |
| Commit inspected | `4eab34c5cfcccaa4f1970554928feccce73ee930` |
| Commit date | 2026-08-03 |
| Date inspected | 2026-08-03 |
| Licence | GNU AGPL-3.0 (no CLA required; CLA gate removed in PR #404; no dual-licence or commercial exception found) |
| Verdict | **Reference now, invoke as a pinned external clone later (adapter approach). Do not fork or vendor in phase one.** |

## What OpenMontage is

OpenMontage is an **instruction-driven, agent-orchestrated video production workbench**. There is no
Python control plane: the IDE coding agent *is* the orchestrator, and Python is limited to tools and
persistence. It is used as a **cloned working directory** (`git clone` → `make setup` → open in an AI
assistant), not as an installable library. A `setup.py` exists (`openmontage` 0.1.0) but the product
is not positioned as a pip package: skills, manifests, and the Remotion composer are
filesystem-coupled to the clone.

### The layered operating model

Every platform entrypoint (`AGENTS.md`, `CURSOR.md`, `.cursor/rules/openmontage.mdc`) force-reads
`AGENT_GUIDE.md`, which routes by user intent and enforces "Rule Zero": any production request must
go through the pipeline system. The core loop is:

```
pipeline manifest (YAML)
  → stage-director skill (Markdown)
    → tools (Python BaseTool subclasses)
      → reviewer meta-skill (self-review)
        → checkpoint (JSON, schema-validated)
          → human approval gate
```

| Layer | Role | Location |
|---|---|---|
| Pipeline manifests | Declarative process: stages, tools, review focus, approval gates | `pipeline_defs/*.yaml` |
| Stage-director skills | *How* to execute a stage | `skills/pipelines/<pipeline>/*-director.md` |
| Meta-skills | Cross-cutting protocols: review, checkpoints, capability extension | `skills/meta/*.md` |
| Layer-3 skills | Provider/technology knowledge (ffmpeg, Remotion, TTS providers, ...) | `.agents/skills/` |
| Tools | Executable capabilities with schemas, tiers, fallbacks, cost tracking | `tools/` via `tools/tool_registry.py` |

## Pipeline manifest anatomy

Manifests validate against `schemas/pipelines/pipeline_manifest.schema.json`
(`additionalProperties: false` — the format is strict and evolving). Using
`pipeline_defs/screen-demo.yaml` (v2.1, `stability: production`) as the worked example, a manifest
declares:

- Identity: `name`, `version`, `description`, `category`, `stability`.
- `default_checkpoint_policy`: `guided` | `manual_all` | `auto_noncreative`.
- `orchestration`: executive-producer skill path, budget defaults, revision/send-back limits.
- `extensions`: whether custom scripts/playbooks/skills/tools are permitted
  (screen-demo sets `custom_tools: false`).
- `required_skills`: stage directors plus `meta/reviewer`, `meta/checkpoint-protocol`.
- Per stage: artifacts produced, `checkpoint_required`, `human_approval_default`, `review_focus`,
  `success_criteria`, required/optional artifacts in, and required/optional tools.

Screen-demo's stages: `idea → script → scene_plan → assets → edit → compose → publish`, with human
gates at idea, script, scene_plan, assets and publish. `clip-factory.yaml` (beta) has the same shape
optimised for producing N short clips from one long source, with explicit vertical-format framing in
its scene plan.

## Checkpoints, review and audit trails

- `schemas/checkpoints/checkpoint.schema.json`: required `version`, `project_id`, `pipeline_type`,
  `stage`, `status` (`in_progress | awaiting_human | completed | failed`), `timestamp`, `artifacts`;
  optional review, cost snapshot, `human_approved`.
- `skills/meta/checkpoint-protocol.md`: gated stages cannot be marked `completed` without
  `human_approved=True` ("GATE VIOLATION"); on a gate the agent presents a summary and **ends its
  turn**. Approval is per gate. Resume via `get_next_stage()`.
- `skills/meta/reviewer.md`: advisory self-review before every checkpoint, max two revision rounds
  then pass-with-warnings, severities critical/suggestion/nitpick/investigation, loads the
  manifest's `review_focus` and `success_criteria`.
- Run workspace: `projects/<project-id>/` (via `lib/paths.py`, overridable with
  `OPENMONTAGE_PROJECTS_DIR`) containing per-stage checkpoints, `artifacts/`, `renders/`,
  `history/`, and an append-only `decision_log.json` with options considered.
- Note a config drift: `config.yaml` still declares legacy `pipeline`/`library` paths; the live
  convention is `projects/`. Treat `lib/paths.py` as the source of truth.

This checkpoint/decision-log/audit pattern is directly reusable *as a design* for this project's
research workflow, independent of whether OpenMontage code runs.

## Tool architecture and dependencies

Tools subclass `tools/base_tool.py` `BaseTool` (tier, capability, provider, dependencies, schemas,
`fallback_tools`, `agent_skills`, `execute() → ToolResult`) and are auto-discovered by
`tools/tool_registry.py` walking the `tools` package. Requirements: Python ≥ 3.10, FFmpeg, Node 18+
(Remotion) / 22+ (HyperFrames); heavy media stacks and ~20 provider API keys (`.env.example`) are
optional and lazy.

Tools relevant to a Spotify screen-recording → TikTok pipeline:

| Need | OpenMontage tools |
|---|---|
| Crop/resize to 9:16 | `auto_reframe` (portrait preset), `video_compose` (`profile: tiktok`), `video_trimmer`, `video_stitch` |
| Audio | `audio_mixer`, `audio_enhance`, `audio_probe` / `audio_energy` |
| Overlays/captions | `subtitle_gen`, `remotion_caption_burn`, `video_compose` overlay ops, Remotion callouts |
| Export | `export_bundle` (local packaging only — explicitly **no** TikTok/YouTube upload) |
| Analysis/QA | `transcriber` (faster-whisper), `scene_detect`, `frame_sampler`, `visual_qa`, `composition_validator` |

TikTok-relevant capability confirmed: `lib/media_profiles.py` defines a `tiktok` profile
(1080×1920), `brief.schema.json` accepts `target_platform: "tiktok"`, and
`skills/creative/short-form.md` documents TikTok/Reels/Shorts safe zones and hooks. There is **no
TikTok API, no posting capability, and no Spotify-specific functionality** of any kind.

## Extension points (critical finding)

There is **no first-class mechanism for external skill/pipeline directories**. Evidence:

- `lib/pipeline_loader.py` defaults to the in-repo `pipeline_defs/`; a `defs_dir=` override exists
  only as a Python API, not an agent-visible or config-driven discovery feature.
- Tool discovery defaults to the in-clone `tools` package.
- `AGENT_GUIDE.md` and the README always point agents at in-tree `pipeline_defs/` and
  `skills/pipelines/`.

Sanctioned extension paths are:

1. **In-tree contribution**: new `pipeline_defs/<name>.yaml` + `skills/pipelines/<name>/` + contract
   tests; new tools under `tools/<capability>/` (per `PROJECT_CONTEXT.md`).
2. **Project-scoped extensions** (`skills/meta/capability-extension.md`): during a run, an agent may
   create `projects/<name>/scripts/`, `projects/<name>/skills/`, `projects/<name>/tools/`
   (must inherit `BaseTool`) and `styles/custom/<project-name>.yaml` — without forking core code.

Implication: an "adapter + extension package" integration cannot mean "OpenMontage loads our
external directories". It must mean: **this repository authors OpenMontage-compatible manifests,
stage skills and (if needed) tool wrappers, and materialises them into a pinned local clone** —
either into that clone's `projects/<name>/` scope (preferred, no tree modification) or by a sync
step that copies manifests into `pipeline_defs/` of a scratch clone. This is recorded in
[ADR 0001](../adr/0001-openmontage-integration-strategy.md).

## Licensing implications (AGPL-3.0)

Not legal advice; flagged for later review in `docs/guides/content-and-source-handling.md` when it
is created.

| Usage mode | Implication |
|---|---|
| Invoke an unmodified local clone at a process boundary | Typical personal AGPL use; keep the licence intact; no copyleft leakage into this repository |
| Fork/modify | Modifications remain AGPL; conveying the software or offering it as a network service requires corresponding source under AGPL |
| Vendor code into this repository | High risk: strong copyleft could attach to the combined work if ever distributed or offered as a network service. Avoid. |

Since this project is personal and non-distributed today, all modes are *legally survivable*, but
keeping OpenMontage at a process boundary preserves the option of the project ever becoming a
product or service without an AGPL entanglement.

## Risks and concerns

- **Very high churn**: ~131 commits since 2026-07-01; merges on the day of inspection. Manifest and
  schema formats are strict (`additionalProperties: false`) and evolving — anything we author
  against them must be pinned to a commit.
- **Agent-as-runtime**: there is no stable library API to call from our own orchestrator; using
  OpenMontage means adopting its agent contract for the production phase.
- **Beta status of the most relevant batch pipeline**: `clip-factory` is beta; `screen-demo` is
  production.
- **Heavy optional footprint**: Remotion, HyperFrames, whisper, and many provider keys — far more
  surface than a Spotify-mix job needs.
- **Human-gate philosophy**: guided checkpoints are core to the product; a future low-friction
  production harness will need deliberate `checkpoint_policy` configuration rather than fighting
  the gates.

## Component-level verdicts

| Component | Decision for this project |
|---|---|
| OpenMontage as production engine (phase 3+) | **Reference now, invoke later** as pinned external clone; do not install in phase one |
| Manifest / checkpoint / decision-log patterns | **Adapt the patterns** for our research workflow manifests and audit trail (no code reuse) |
| `screen-demo` / `clip-factory` pipelines | Candidate execution targets in phase 3; document as extension targets only |
| `tiktok` media profile, `auto_reframe`, `video_compose` | Note as the future export path; no phase-one action |
| Layer-3 provider skills (`.agents/skills/`) | Do not copy; they arrive with the clone when needed |
| Fork | **No** — only if upstream churn breaks a pinned integration and project-scoped extension proves insufficient (exit conditions in ADR 0001) |
