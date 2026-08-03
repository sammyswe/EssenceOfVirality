# ADR 0008: Creator-Directed Phase Gates (Intelligence Before Pipeline)

- Status: **Accepted** (creator decision, 2026-08-03)
- Date: 2026-08-03
- Supersedes: the phase numbering and exit criteria in `docs/roadmap/README.md` prior to this ADR
  (phases 2–6 are redefined; phase 1 unchanged)

## Context

The original roadmap placed OpenMontage pipeline integration at phase 3, with knowledge acquisition
at phase 2 described as open-ended volume. The creator has directed a stricter sequence:

1. Build a **large general TikTok-virality corpus** (~80 additional sources) and convert findings
   into durable **knowledge, skills, and rules** before any niche-specific or production work.
2. Run a **creator calibration phase** — structured grilling about the creator's actual Spotify-mix
   TikTok practice — to author **spotify-mix-content** skills grounded in creator preference and
   craft, not only external research.
3. Only then begin **pipeline development** (OpenMontage integration, edit plans, manifests).

Pipeline development without this intelligence layer would produce automation that edits before
the project knows what good general virality practice and good niche practice mean for this
account.

## Decision

Adopt the following phase gates (full detail in `docs/roadmap/README.md`):

| Phase | Name | Pipeline work |
|---|---|---|
| 1 | Intelligence infrastructure | **Forbidden** (complete) |
| 2 | General virality corpus (~80 sources) | **Forbidden** |
| 3 | Creator calibration (Spotify-mix grilling) | **Forbidden** |
| 4 | Production pipeline integration (OpenMontage) | **Allowed — first phase where allowed** |
| 5+ | Automation, analytics, continuous improvement | As previously sketched |

**Phase 2 scope (general virality only):**

- Ingest ~80 curated TikTok-virality sources via the existing research-ingestion workflow.
- Promote findings into `knowledge/` (algorithm-model, viewer-behaviour, production-techniques),
  `evidence/`, the **`general-virality`** skill bank, and scoped **`.cursor/rules/`** where a
  cross-cutting constraint deserves enforcement.
- The existing **13 specialist agents** are sufficient; phase 2 does **not** require ~80 new
  agents. "Turning sources into agents" means exercising the agent *topology* on each source, not
  creating one agent per source.

**Phase 3 scope (niche calibration only):**

- Structured creator sessions (Matt Pocock `grill-me` / `grill-with-docs` workflows, or
  equivalent) about the creator's Spotify-mix TikToks: format, audio capture, hooks, series,
  what they will and will not do, example posts, failures.
- Register sessions as sources; record preferences and constraints as claims; author and promote
  **`spotify-mix-content`** skills. No OpenMontage adapter work.

**Hard gate:** No work in `integrations/openmontage/` beyond the existing pin/README, no
`video_production_manifest` production paths, no edit-plan execution, until phases 2 **and** 3
exit criteria are met and recorded in a phase review document.

## Alternatives

- **Original roadmap (pipeline at phase 3)** — rejected by creator: risks automating before
  intelligence is deep enough.
- **Merge phases 2 and 3** — rejected: general virality knowledge must stay separable from niche
  calibration; mixing them would blur bank boundaries (ADR 0002 / `skills.mdc`).
- **Skip phase 3 (research-only niche skills)** — rejected: Spotify-mix content has creator-specific
  constraints (anonymous format, original audio, Spotify legibility) that external virality sources
  under-specify.

## Consequences

- OpenMontage integration (ADR 0001) remains valid but is **deferred to phase 4**.
- Phase 2 is a large, batch-oriented research campaign (`docs/roadmap/phase-two-virality-campaign.md`).
- Phase 3 requires explicit creator time; agents cannot substitute for it.
- `.cursor/rules/00-mission.mdc` and `README.md` must reflect the current phase and forbidden work.
- Future PRs that touch `integrations/openmontage/` beyond documentation should cite phase-4 readiness
  or be rejected at review.

## References

- Creator decision recorded 2026-08-03 (conversation preceding this ADR).
- `docs/roadmap/phase-two-virality-campaign.md`
- `docs/roadmap/phase-three-creator-calibration.md`
- ADR 0001 (OpenMontage — deferred execution)
- ADR 0006 (PR gate — unchanged)
