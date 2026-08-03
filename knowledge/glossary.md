# Glossary

Revision date: 2026-08-03

## Epistemic taxonomy

Defined in `CONTEXT.md` and enforced by `schemas/claim-record.schema.json`: **fact**, **finding**,
**hypothesis**, **heuristic**, **pattern**, **anecdote**, **constraint**, **preference**,
**experiment result**. Never flattened into "best practices".

## Distribution and metrics vocabulary

| Term | Meaning here |
|---|---|
| Distribution volume | How many feeds a video is shown to; distinct from how viewers respond |
| Early skip | Viewer swipes away within the first seconds |
| Completion | Watching to the end; "full watch" |
| Rewatch / loop | Repeated views by the same viewer, deliberate or via seamless looping |
| Follow conversion | Viewers who follow after watching, per view |
| Content promise | What the first moments claim the video will deliver |
| Payoff | The promised moment landing (for us: the transition) |
| Cold start | Distribution/interest matching for new users or new accounts with no history |
| Negative feedback | "Not interested", hide-creator, hide-sound, reports |
| Eligibility | Whether a video can be recommended at all (moderation/quality gates) |

## Production vocabulary

| Term | Meaning here |
|---|---|
| Hook | First-seconds text/audio/visual device that earns continued watching — must be honest |
| First frame | Frame 1 as seen in-feed; also cover-frame when selected as such |
| Pattern interrupt | Deliberate change (visual/audio) that resets attention |
| Overlay | Any element added over the screen recording |
| Edit specification | Concrete, executable list of editing decisions output by evaluation skills |
| Production rule | A controllable decision linked to an intended viewer behaviour |

## Niche vocabulary (UK house / Spotify mix)

| Term | Meaning here |
|---|---|
| Spotify mix | A playlist crafted so consecutive tracks blend like a DJ set, using Spotify's own playback (crossfade/track order/edit points) |
| Transition | The blend moment between two tracks — the core payoff of this content |
| Beat-matched | Transition where tempos/phrasing align so the blend feels continuous |
| Blend window | The seconds during which both tracks are audible |
| Now-playing view | The Spotify screen showing current track, art and progress bar |
| Made-in-Spotify novelty | The core value proposition: DJ-like listening experiences achievable inside Spotify itself |
| Series consistency | Recognisable repeatable format across posts that builds follow intent |

## Project terms

| Term | Meaning here |
|---|---|
| Artifact | A schema-validated YAML record exchanged between agents (ADR 0004) |
| Bank | A top-level skill grouping under `.cursor/skills/` |
| Promotion | Moving a record/skill to higher trust (via PR only) |
| Vertical slice | One source run end-to-end through research-to-PR (phase-one proof) |
