# integrations/openmontage/

The adapter + extension package for OpenMontage (ADR 0001). **Phase-one footprint: this README
and the pinned ref only.** No OpenMontage code is vendored here — it is AGPL-3.0 and stays at a
repository/process boundary.

## What will live here (phase 3)

| Item | Purpose |
|---|---|
| `PINNED_REF` | The exact upstream commit our extensions are authored against |
| `manifests/` | TikTok/Spotify-mix pipeline manifest sources (OpenMontage manifest format) |
| `stage-skills/` | Custom stage-director skill sources |
| `tools/` | Minimal `BaseTool` wrapper sources, if the sanctioned toolset needs extension |
| `materialise` script | Installs the above into the pinned clone's `projects/<name>/` scope |
| `evaluation-adapters/` | Mapping OpenMontage `final_review` output into our evaluation reports |

## Rules

- The clone lives **outside git** (`clone/` is gitignored) at `OPENMONTAGE_CLONE_PATH`.
- Sync direction is strictly **ours → clone**. Nothing is copied back from the clone into this
  repository (AGPL boundary).
- Upgrading the pin is a deliberate PR driven by `/review-openmontage-integration`, which diffs
  the upstream schemas and meta-skills we depend on (ADR 0001 upgrade strategy).
- Who writes here: the skill architect and evaluation agent (via PRs), phase 3 onward.
- Extension points, capability mapping and fork triggers:
  `docs/architecture/openmontage-integration.md`.
