# Phase 2 — General Virality Corpus Campaign

Revision date: 2026-08-03. Authoritative phase gate: **ADR 0008**.

## Creator directive

Before any Spotify-mix-specific calibration or pipeline development, ingest **roughly 80 additional
sources** on TikTok virality (distribution, viewer behaviour, hooks, editing, audio, packaging,
platform mechanics, and credible research). Convert durable findings into **knowledge**, **`general-virality`
skills**, and **scoped rules** by running each source through the existing agent topology — not by
inventing ~80 new agents.

## Current baseline (start of phase 2)

| Metric | Count | Notes |
|---|---|---|
| Sources ingested | 7 | For You disclosure, creator brief, batch 2026-08-03 (5 links) |
| Target additional sources | **~80** | Creator-directed; curated, not indiscriminate |
| **Campaign target total** | **~87** | 7 + 80 |
| `general-virality` skills | 2 exemplars | `analyse-first-frame`, `evaluate-hook-clarity` |
| Canonical production docs | 2 + algorithm set | `hooks.md`, `metadata-and-discovery.md`; viewer-behaviour mostly planned |
| Real contradiction records | 3 | skip-speed, hashtags, optimal length |

Track progress in `research/batches/` and update the table below as batches merge.

## What “turn into agents, skills, and rules” means

| Output | Phase-2 meaning | Not this |
|---|---|---|
| **Agents** | The existing 13 specialists (`source-extraction`, `evidence-analyst`, `virality-technique-analyst`, `skill-architect`, …) process each source via `/ingest-source` | One new agent per source |
| **Skills** | New or revised skills in `.cursor/skills/general-virality/` (and `experimental/` candidates promoted after critic + evaluation) | Niche skills (`spotify-mix-content/`) — phase 3 |
| **Rules** | New or tightened `.cursor/rules/*.mdc` when many sources support the same hard constraint | Duplicating knowledge already in `knowledge/` without enforcement need |
| **Knowledge** | Canonical docs under `knowledge/` with cited claims; `unknowns.md` narrowed | Silent overwrite; lore stated as fact |

## Source intake process

1. **Curate** — add links to GitHub issues using `.github/ISSUE_TEMPLATE/research-source.md`, or paste
   batches to a cloud agent / run `/ingest-source <url>` in Cursor. Tag with topic labels (see below).
2. **Batch** — aim for **5–15 sources per PR** (`research/batches/batch-<yyyymmdd>-<nn>/`) so review
   stays human-scale.
3. **Ingest** — full pipeline: manifest → extraction → claims → assessments → contradictions →
   techniques → knowledge/skill proposals → evaluation → PR summary.
4. **Review** — creator merges PRs; no auto-merge (ADR 0006).

### Suggested topic quotas (adjust as evidence dictates)

Rough guide so the ~80 sources cover the planned canonical set evenly:

| Topic bucket | Target sources | Feeds |
|---|---|---|
| Algorithm / distribution disclosures & audits | 10–15 | `algorithm-model/` |
| Viewer behaviour & attention | 10–15 | `viewer-behaviour/` |
| Hooks, first frame, packaging | 10–12 | `production-techniques/hooks.md`, `first-frame.md`, … |
| Pacing, length, loops, retention | 8–10 | `completion.md`, `loops.md`, `pacing.md` |
| Audio, music-on-TikTok (general) | 6–8 | `production-techniques/audio.md` |
| Overlays, captions, text-on-screen | 6–8 | `overlays.md`, `captions.md`, `metadata-and-discovery.md` |
| CTAs, follows, comments, shares | 5–8 | `viewer-behaviour/sharing.md`, `following.md`, … |
| Creator-education / folklore (for contradiction testing) | 8–10 | contradictions + anti-patterns in skills |
| Platform constraints & policy | 5–8 | `platform-constraints/` |

## Planned deliverables checklist

Copy into the phase-two review doc when closing the phase.

### Knowledge

- [ ] All documents listed in `knowledge/viewer-behaviour/README.md` exist with cited conclusions
- [ ] All documents listed in `knowledge/production-techniques/README.md` exist with cited conclusions
- [ ] `knowledge/algorithm-model/unknowns.md` materially shorter than at phase-2 start (entries removed or narrowed with claim citations)
- [ ] `knowledge/index.md` reflects coverage; no “planned (phase 2)” rows left for general topics

### Skills (`general-virality` bank)

Minimum skill set to cover controllable levers before niche calibration (names may vary; each needs
`evidence_refs`, critic pass, and `maturity >= provisional`):

- [ ] First frame / hook (extend existing exemplars or promote)
- [ ] Pacing / dead-time trimming
- [ ] Payoff / transition timing (may stay cross-bank with niche analyst gate)
- [ ] Overlay / text restraint
- [ ] Caption / metadata / search discovery
- [ ] Loop / rewatch structure (short-form)
- [ ] Audio clarity / levels (general short-form — niche audio audit stays phase 3)
- [ ] Packaging / cover frame
- [ ] CTA / follow reason (light touch — anonymous account constraints noted)

Target: **≥ 8 operational general-virality skills** at `provisional` or above.

### Rules

- [ ] Audit `.cursor/rules/` against repeated cross-source findings; add scoped rules only where
  enforcement beats documentation (e.g. “never cite hashtag piling as a lever” if still appearing in
  agent outputs)
- [ ] `00-mission.mdc` phase gate updated when phase 2 closes

### Process proof

- [ ] ≥ 10 batch PRs merged (implies ~80 sources at ~8 per batch average)
- [ ] Contradiction workflow exercised on ≥ 5 real disagreements (not only the first batch’s three)
- [ ] At least one skill promoted through full critic → evaluation → regression path
- [ ] `/compare-evidence` run at least once on the populated store

## Explicit non-goals (defer to phase 3+)

- Spotify-mix niche skills and `knowledge/spotify-mix-niche/` beyond `value-proposition.md`
- Creator grilling and preference claims from live sessions
- OpenMontage clone setup, manifests, rendering
- TikTok analytics import and experiment results from live posts

## Progress log

| Batch | PR | Sources | Merged | Notes |
|---|---|---|---|---|
| batch-20260803-01 | #3 | 5 | yes | First multi-source batch; 3 contradictions; `searchable-onscreen-text` experimental |
| | | | | |
| *Add rows as batches land* | | | | |

## Closing the phase

When exit criteria are met, write `docs/phase-two-review.md` (same honesty standard as
`phase-one-review.md`: proven vs built-but-unexercised) and update `docs/roadmap/README.md` phase
table. Only then may phase 3 (creator calibration) begin.
