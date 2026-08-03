---
name: evaluate-hook-clarity
description: Evaluate a hook (text, audio moment or visual cue) for comprehension speed, honesty and promise strength, and propose a better hook only when a check fails. Use when reviewing hook text in an edit plan or diagnosing early abandonment.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: low
  evidence_basis: [official, creator_statement]
  evidence_refs:
    - claim-20260803-hyp-early-skip-promise
    - claim-20200618-completion-strong-signal
    - claim-20260803-pref-music-central
  requires_human_approval: false
---

# Evaluate hook clarity

Intended viewer effect: reduce `early_skip_rate` by making the content promise comprehensible
fast — and protect trust (honesty gate) so completion isn't traded for resentment. Evidence
tier: hypothesis-backed heuristics (`knowledge/production-techniques/hooks.md`).

## Inputs

Required: the hook (text/audio/visual description), the video's actual content and payoff,
duration. Optional: where and how long the hook displays.

## Steps

1. Comprehension: can the hook be read/grasped in one pass at mobile size (text hooks: roughly
   ≤ 8 words, no dependent clauses)? Complete when yes/no with the failing property named.
2. Specificity: does it promise *this* video's payoff rather than generic excitement ("wait for
   it" promises nothing; "the switch at 0:06 should not work" promises this transition)?
   Complete when answered.
3. Honesty gate (hard): does the content deliver exactly what the hook promises, in register and
   substance? A false or manufactured promise fails the hook regardless of predicted attention
   (fixture `fix-06-misleading-hook`). Complete when answered.
4. Music-centrality check: does the hook's placement/duration clear the blend window and leave
   the audio experience primary (claim-20260803-pref-music-central)? Complete when answered.
5. Only if a check failed: propose up to two replacement hooks that pass all four checks, each
   with the check it repairs and its intended viewer effect. A passing hook gets zero proposals
   (fixture `fix-05-no-follow-reason`: don't rewrite a working hook). Complete when proposals
   (or none) are recorded.

## Output contract

```yaml
hook_evaluation:
  comprehension: {pass: bool, detail: ""}
  specificity: {pass: bool, detail: ""}
  honesty: {pass: bool, detail: ""}
  music_centrality: {pass: bool, detail: ""}
  proposals: [{hook: "", repairs: "", intended_effect: early_skip_rate}]
```

## Anti-patterns

- Controversy/outrage framing over calm content — register mismatch is a form of dishonesty;
  propose a hook matching the content's actual feel.
- Hook-stacking: multiple simultaneous hook devices compete; choose one.
- Baiting comments with false errors ("nobody notices the key clash") — engagement earned by
  deception is prohibited; use a genuine question instead.

## Example / counterexample

Example pass: "two tracks that mix perfectly on spotify" over a clean blend — comprehensible,
specific, honest, clear of the blend window. Counterexample: "DJs are FURIOUS about this trick"
over a mellow deep-house blend — fails honesty and register; correct action is rejection plus an
honest alternative, not a softer edit of the false claim.
