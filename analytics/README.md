# analytics/

**Scaffold only in phase one** (ADR 0007). The analytics learning loop is phase 5.

## Layout

| Path | Purpose | Source-controlled |
|---|---|---|
| `examples/` | Synthetic example records demonstrating the schemas | yes |
| `raw/` | Raw TikTok exports (created locally when phase 5 starts) | **no — gitignored** |
| normalised records (future `observations/`) | Schema-validated `analytics_observation` YAML | yes, after redaction |

## Rules

- Raw platform exports never enter git; only normalised, schema-validated, redacted-where-needed
  records are committed.
- One observation per video **per capture date** — snapshots, never overwritten, so delayed
  performance and repeated distribution waves stay visible.
- Absolute counts and rates are separate structures; never derive one silently from the other.
- Every observation links to a `video_production_manifest` via `video_id`; lineage runs
  observation → manifest → skills/decisions → evidence → sources.
- **No causal claims from small samples.** The analytics-learning agent proposes hypotheses and
  experiments, not conclusions, until cohorts exist.
- Schemas: `schemas/analytics-observation.schema.json`,
  `schemas/video-production-manifest.schema.json` (both `schema_maturity: scaffold`; field names
  are provisional until real exports are inspected — see ADR 0007).
