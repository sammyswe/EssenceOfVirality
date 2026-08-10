# integrations/openmontage/

Adapter + extension package for OpenMontage (ADR 0001). OpenMontage code stays in a pinned
external clone (AGPL boundary); this directory owns our pipeline sources and runner.

## Layout

| Path | Purpose |
|---|---|
| `PINNED_REF` | Exact upstream commit (`4eab34c5…` at time of writing) |
| `manifests/` | Pipeline config + brief template for `essence-of-virality` |
| `stage-skills/` | Project-scoped skill sources (materialised into clone) |
| `playbooks/` | `spotify-mix-tiktok` style playbook |
| `materialise.sh` | Copies extensions → `clone/projects/essence-of-virality/` |
| `run_pipeline.py` | Deterministic Spotify mix → TikTok runner (ffmpeg path) |
| `inputs/` | Drop screen recordings here (gitignored media) |
| `outputs/` | Run artifacts (local only) |
| `clone/` | **Gitignored** — pin with `PINNED_REF` |

## Quick start

```bash
python3 integrations/openmontage/run_pipeline.py --input-dir integrations/openmontage/inputs/
```

Full guide: [`docs/guides/openmontage-pipeline.md`](../../docs/guides/openmontage-pipeline.md).

## OpenMontage capabilities we consume

- Pipeline: `screen-demo` (real_capture mode)
- Profile: `tiktok` (1080×1920)
- Tools: `auto_reframe`, `video_trimmer`, `video_compose`, `export_bundle`
- Audit: checkpoint protocol + `final_review` (agent path)

## Domain skills

Materialised references point at `.cursor/skills/general-virality/` and
`.cursor/skills/spotify-mix-content/`. See `manifests/essence-of-virality.yaml`.

## Rules

- Sync direction: **ours → clone** only (`.cursor/rules/openmontage.mdc`).
- Upgrades: `/review-openmontage-integration` + deliberate `PINNED_REF` change.
- Extension points: `docs/architecture/openmontage-integration.md`.
