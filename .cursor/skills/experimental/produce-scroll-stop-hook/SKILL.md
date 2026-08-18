---
name: produce-scroll-stop-hook
description: >
  Produce a scroll-stop Higgsfield hook brief for a Spotify mix. Use when
  generating or revising an AI hook clip, when a hook feels generic, or when
  another skill needs a hook prompt that applies retained scroll-stop craft.
metadata:
  version: 0.1.1
  maturity: experimental
  confidence: low
  evidence_basis:
    - observational
    - expert_opinion
  evidence_refs: []
  requires_human_approval: false
---

# Produce a scroll-stop hook

A **scroll-stop** is the opening beat that interrupts the feed: one honest
promise, readable in about a second, that the mix video can keep. This skill
turns that demand into a Higgsfield brief the creator can generate.

Techniques come from creator-supplied education videos (Dropbox
`education/hooks-incoming/`), distilled into
[references/techniques.md](references/techniques.md) (batch notes:
[references/education-batch-2026-08-18.md](references/education-batch-2026-08-18.md)).
Channel constraints live in [references/channel-fit.md](references/channel-fit.md).
If techniques.md has zero *active* rows, refuse to invent scroll-stop craft —
ask for education videos or fall back to the live hook-profile / copy-bank
wording only.

Intended viewer effect (hypothesis, not guarantee): lower `early_skip_rate` by
delivering an immediate, honest promise; protect `completion_rate` by making
the switch the payoff the scroll-stop advertised.

## Inputs

Required: track pairing (or "unknown"), whether a hook profile already matches,
fiction-signal options the clip will use.

Optional: mood, previous hook stems to avoid repeating, education technique IDs
from `references/techniques.md`.

## Steps

1. **Load craft.** Read `references/techniques.md` and `references/channel-fit.md`.
   If techniques.md has zero active techniques, stop and report that education
   ingest is required before this skill can invent new scroll-stop concepts —
   you may still reuse an existing approved hook profile. Complete when either
   (a) at least one active technique is listed, or (b) the stop report is
   written.

2. **Promise.** State the one promise this hook will make (what the viewer gets
   if they stay). It must be true of the finished mix video (usually: a Spotify
   blend / switch worth hearing). Complete when the promise is one sentence and
   honesty-checked against channel-fit.

3. **Scroll-stop frame.** Describe the first second: dominant visual, any on-
   screen text ≤ ~6 words, motion cue. Apply every *active* technique in
   techniques.md that fits this promise; for each skipped technique, write why
   it does not fit. Complete when the first-second description exists and every
   active technique is either applied or explicitly skipped with a reason.

4. **Higgsfield brief.** Write the ready-to-paste prompt, negatives, duration
   (~4s), aspect notes, and fiction signal. Complete when the brief is paste-
   ready and names the technique IDs it used.

5. **Overlay candidates.** Offer three on-screen text options that match the
   brief and pass channel-fit (no "mixes itself", no invented third-party
   reactions). Complete when three options are listed.

## Output contract

```yaml
scroll_stop_hook:
  promise: ""
  first_second: {visual: "", text: "", motion: ""}
  techniques_applied: []      # ids from techniques.md
  techniques_skipped: []      # {id, reason}
  higgsfield:
    prompt: ""
    negatives: ""
    duration_seconds: 4
    fiction_signal: ""
  overlay_text_options: []    # exactly 3
  warnings: []
```

## Failure handling

| Condition | Response |
| --- | --- |
| No active techniques loaded | Stop; request education videos in Dropbox `education/hooks-incoming/` |
| Promise would be false for this mix | Rewrite or refuse; do not ship the brief |
| Technique conflicts with channel-fit | Skip it; record the reason |
| Creator asks for ragebait / fake third-party claims | Refuse; offer an honest scroll-stop alternative |

## Related skills

`analyse-first-frame` and `evaluate-hook-clarity` review the result.
`spotify-mix-creative-director` chooses format and may reach this skill for the
Higgsfield brief. Hook profiles under `production/config/hook-profiles/` bind a
finished clip to overlay/CTA/caption trios after generation.
