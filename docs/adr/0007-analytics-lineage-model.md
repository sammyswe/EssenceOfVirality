# ADR 0007: Analytics Lineage Model

- Status: **Proposed** (deliberately weakly held: real TikTok export formats have not yet been
  inspected, and no videos have been produced)
- Date: 2026-08-03

## Context

Phase 5 will learn from published-video analytics. Learning is only possible if every metric can be
traced back to the decisions that produced the video. Phase one scaffolds the schemas; it must not
build importers, dashboards, or inference.

## Decision

Two linked artifact types, scaffolded now:

1. **`VideoProductionManifest`** (`schemas/video-production-manifest.schema.json`) — written when a
   video is produced (phase 3+): source assets, pipeline + OpenMontage versions, duration/format,
   content series, general-virality skills used (with versions), spotify-mix skills used, editing
   decisions, hook, CTA, audio/visual/export settings, quality reviews, creator feedback,
   published-post URL/date, and a pointer to its analytics record.
2. **`AnalyticsObservation`** (`schemas/analytics-observation.schema.json`) — one record per
   video per capture date (metrics evolve over time, so observations are snapshots, never
   overwritten): raw counts (views, likes, comments, shares, saves, followers gained, profile
   visits) kept separate from derived rates (per-view conversion, completion, retention curve),
   plus posting metadata (time, caption, hashtags, sound, cover), traffic sources, audience data
   where available, and `video_id` linking to the manifest.

Lineage chain: `AnalyticsObservation.video_id → VideoProductionManifest → skills[]/decisions[] →
evidence_refs → claims/sources`. Absolute counts and rates are distinct fields — never conflated —
and account-level context (follower count at posting) is recorded so distribution volume and
conversion can be separated later.

Phase-one deliverables: the two schemas, one synthetic example record under `analytics/examples/`,
a README stating what is and is not committed (raw platform exports stay out of git by default,
normalised records are committed), and the `ingest-tiktok-analytics` workflow skill limited to
validate-and-store.

## Alternatives

- Defer all analytics design to phase 5 — rejected: the production manifest must exist before the
  first produced video or lineage is unrecoverable; scaffolding now is cheap.
- Warehouse/database design now — rejected as premature (anti-goal).

## Consequences

- Field names and structures are provisional until real exports are seen; the schemas carry a
  `schema_maturity: scaffold` marker and this ADR stays `proposed` until phase 5 revalidates it.
- Snapshot-based observations naturally support delayed-performance analysis and repeated
  distribution waves without schema change.
- No causal inference machinery exists or is implied; small-sample caution is a rule for the
  analytics-learning agent, not a schema property.
