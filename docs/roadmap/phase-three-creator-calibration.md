# Phase 3 — Creator Calibration (Spotify-Mix Grilling)

Revision date: 2026-08-03. Authoritative phase gate: **ADR 0008**.

## Creator directive

After the general virality corpus (phase 2), the creator will be **grilled** about their actual
Spotify-mix TikTok practice. Findings become **`spotify-mix-content` skills** and
`knowledge/spotify-mix-niche/` documents grounded in **creator_statement** claims — not inferred
from generic virality research alone.

Pipeline development remains **forbidden** until this phase closes.

## Why this is a separate phase

General virality sources describe what works on TikTok broadly. This account is constrained in
ways external research under-specifies:

- Anonymous, no face-led strategy
- Original captured Spotify audio (no trending Sounds overlay)
- Spotify UI legibility as authenticity signal
- House-music listener norms (UK audience)
- Creator craft standards for transitions that generic hook advice can damage

Phase 3 makes those constraints operational in skills the pipeline will later invoke.

## Definition of ready

- Phase 2 exit criteria met (`phase-two-virality-campaign.md`), **or** creator documents accepted
  gaps and explicitly authorises phase 3 to proceed.
- Matt Pocock grill skills available (`.agents/skills/grill-me`, `grill-with-docs`) — already
  pinned in repo.

## Session plan (creator-facing)

Sessions are registered as sources (`source_type: manual_observation` or `creator_case_study`) with
manifests citing date and medium (Cursor chat, exported transcript, etc.).

### Recommended grill topics

Use `grill-me` for breadth, `grill-with-docs` when reviewing a specific draft video or knowledge
doc. Suggested modules (one or more sessions each):

1. **Format & capture** — screen recording setup, duration bands, portrait framing, what must stay
   visible in the Spotify UI, audio capture chain, failure modes you reject.
2. **The transition as product** — what makes a transition “post-worthy”, build-up length, how
   much context before the blend, when a transition is too subtle to post.
3. **Hooks & text** — what you will/won’t say on screen; honesty lines; series naming; search
   phrases your audience uses; banned gimmicks.
4. **Series & follow reason** — why someone follows an anonymous mix account; consistency signals;
   what a CTA may say without breaking anonymity.
5. **Posts post-mortem** — 3–5 real or representative videos: what worked, what didn’t, what you’d
   change; link or describe each for fixture-style learning later.
6. **Hard nos** — tactics you refuse even if virality sources recommend them (controversy hooks,
   trending sounds, face on camera, misleading packaging).
7. **Success metrics** — how *you* judge a video before analytics; which metrics you care about
   first when data exists.

### Artifacts per session

| Stage | Output |
|---|---|
| Intake | `research/sources/src-<date>-creator-grill-<topic>/manifest.yaml` |
| Extraction | preference, constraint, and anecdote claims → `evidence/claims/` |
| Knowledge | updates to `knowledge/spotify-mix-niche/*` via KCP PRs |
| Skills | `skill_change_proposal` → `.cursor/skills/spotify-mix-content/` or `experimental/` |
| Evaluation | fixtures extended or added where niche failures are repeatable |

## Planned deliverables checklist

### Knowledge (`spotify-mix-niche/`)

- [ ] `audience.md` — who the mixes are for, in the creator’s words
- [ ] `content-formats.md` — allowed formats, duration, series patterns
- [ ] `visual-requirements.md` — Spotify UI, framing, motion limits
- [ ] `audio-requirements.md` — capture, levels, what “damaged audio” means to this creator
- [ ] `conversion-goals.md` — follow, save, Spotify add — priority order for *this* account
- [ ] `hypotheses.md` — niche-specific testable propositions for phase 6 analytics

### Skills (`spotify-mix-content` bank)

Extend beyond the two phase-1 exemplars (`preserve-spotify-mix-audio`, `evaluate-transition-payoff`):

- [ ] Capture / technical QA skill (screen recording + audio chain audit)
- [ ] Series / packaging skill (anonymous identity, follow reason)
- [ ] Niche hook adapter (maps general hook rules → mix-native promises)
- [ ] Transition selection skill (which moments are worth posting)
- [ ] Optional: caption/hashtag skill niche-adapted from general metadata skill

Target: **≥ 5 operational niche skills** at `provisional` or above, each citing creator_statement
and/or adapted general claims.

### Cross-links

- [ ] Every niche skill documents which `general-virality` skills it adapts and how
- [ ] `spotify-mix-domain-analyst` gate recorded in technique records (transferability: adapted)

## Explicit non-goals

- OpenMontage integration (phase 4)
- Automated posting or analytics import (phase 6)
- Replacing phase-2 general knowledge — niche skills **adapt**, not duplicate

## Closing the phase

Write `docs/phase-three-review.md`. Update roadmap state. **Phase 4 (pipeline)** may begin only
after this review and ADR 0008 gate check.

## Creator preparation (optional, speeds the phase)

Before the first grill session, gather:

- 3–5 TikTok URLs or local descriptions of your best and worst posts
- Notes on recording setup (device, Spotify desktop/mobile, audio routing)
- A list of creators or formats you explicitly do *not* want to emulate

Paste “start phase 3 grilling” in Cursor with `/grill-me` or ask a cloud agent to run the session
plan above.
