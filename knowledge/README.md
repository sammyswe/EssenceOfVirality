# knowledge/

Canonical curated documents — the human- and agent-navigable synthesis of the evidence store.
Concise conclusions, not note dumps. Every conclusion cites claim IDs from `evidence/` or
`research/sources/*/claims/`.

## Layout

| Area | Holds |
|---|---|
| `algorithm-model/` | The evolving TikTok distribution model: `current-working-model.md`, `known-platform-disclosures.md`, `inferred-distribution-hypotheses.md`, `unknowns.md` |
| `viewer-behaviour/` | Human-attention knowledge: attention, comprehension, curiosity, anticipation, payoff, completion, rewatching, sharing, commenting, following |
| `production-techniques/` | Controllable production rules: hooks, first-frame, pacing, overlays, captions, motion, loops, CTAs, audio, packaging |
| `spotify-mix-niche/` | Niche knowledge: audience, value proposition, content formats, visual/audio requirements, conversion goals, hypotheses |
| `platform-constraints/` | TikTok technical/policy constraints affecting production |
| `glossary.md` | Epistemic taxonomy + niche vocabulary |
| `index.md` | Topic → document → related skills map |

## Document contract

Each canonical document contains: current conclusion, supporting claims (IDs), disputed claims,
open questions, practical implications, related skills, related experiments, revision date.

## Rules

- **The platform model is not a lever.** `algorithm-model/` and `viewer-behaviour/` describe how
  distribution and viewers *may* behave; only `production-techniques/` and `spotify-mix-niche/`
  contain rules the pipeline can act on, and each rule states its intended viewer effect.
- Changes land only via PR with citations (ADR 0006). Never duplicate a conclusion across files —
  link to the owning document.
- Phase-one state: structure plus vertical-slice seed content. Bulk knowledge acquisition is
  phase 2; do not pad these documents to look complete.
