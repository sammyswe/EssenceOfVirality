# Scroll-stop techniques

Active techniques distilled from creator-supplied education videos
(Dropbox `/spotify-mix-videos/education/hooks-incoming/`, pulled 2026-08-18).

Ingest notes: [education-batch-2026-08-18.md](education-batch-2026-08-18.md).
Only `status: active` techniques are applied by `produce-scroll-stop-hook`.

```yaml
- id: tech-20260818-pattern-interrupt-open
  name: Pattern-interrupt open
  scroll_stop_move: >
    First second breaks the feed pattern with one sudden visual change
    (depth jump, impossible motion, or stark contrast) before any copy load.
  intended_viewer_effect: >
    Hypothesis: lower early_skip_rate by forcing a re-orient glance before
    the thumb continues.
  requirements:
    - Must still be honest about a Spotify mix / switch payoff
    - Fiction signal required for AI footage
  contraindications:
    - Lifestyle vlog open that does not lead into the mix product
  channel_fit: adapt
  evidence:
    - education-batch-2026-08-18.md#v2-briarcochran
    - education-batch-2026-08-18.md#v1-myfriendshells
  status: active

- id: tech-20260818-depth-motion-entry
  name: Depth-motion entry
  scroll_stop_move: >
    Opening beat uses camera or subject motion that changes depth quickly
    (pull-back, push-in, or objects rushing toward/away from lens).
  intended_viewer_effect: >
    Hypothesis: motion that changes scale in-frame reduces early_skip_rate
    vs a static first frame.
  requirements:
    - Motion must belong to the hook fiction world, not a bait talking-head
  contraindications:
    - Step-back influencer entry that promises a lifestyle story
  channel_fit: adapt
  evidence:
    - education-batch-2026-08-18.md#v1-myfriendshells
  status: active

- id: tech-20260818-visual-confirm-fast
  name: Fast visual confirm
  scroll_stop_move: >
    Within ~1–2s of the scroll-stop promise, show a visual that proves the
    claim is not empty (for this niche: the Spotify UI / transition setup
    the overlay advertised).
  intended_viewer_effect: >
    Hypothesis: lower mid-open abandons by resolving "is this clickbait?"
    before the viewer decides the promise was fake.
  requirements:
    - Confirm must match overlay promise (switch, bass hit, blend)
  contraindications:
    - Fake metric badges or unrelated proof screenshots
  channel_fit: pass
  evidence:
    - education-batch-2026-08-18.md#v3-mino
  status: active

- id: tech-20260818-payoff-rehook
  name: Payoff re-hook
  scroll_stop_move: >
    After the open promise, briefly hint that a specific payoff lands later
    (the mix switch / drop) so the open is not the whole story.
  intended_viewer_effect: >
    Hypothesis: raise completion_rate toward the transition by creating
    anticipation of a named payoff.
  requirements:
    - Payoff must be the real transition; never invent a different ending
  contraindications:
    - Teasing a non-musical twist the video will not deliver
  channel_fit: pass
  evidence:
    - education-batch-2026-08-18.md#v3-mino
    - education-batch-2026-08-18.md#v2-briarcochran
  status: active

- id: tech-20260818-subjective-stakes-line
  name: Subjective stakes overlay
  scroll_stop_move: >
    One short overlay line states a subjective, keepable claim about the
    blend ("this switch hits harder than it should") — not a third-party
    reaction and not a life-advice template.
  intended_viewer_effect: >
    Hypothesis: a specific subjective claim raises stay intent vs generic
    "fire mix" text by giving one concrete reason to listen.
  requirements:
    - ≤ ~6 words preferred; drawtext-safe; honest for this pairing
  contraindications:
    - Templates like "YOU ARE DOING THIS WRONG" / "NO ONE TOLD YOU"
      applied as fake advice framing
    - "I almost didn't post this" drama for a routine mix drop
  channel_fit: adapt
  evidence:
    - education-batch-2026-08-18.md#v0-kienobi
  status: active

- id: tech-20260818-prop-incongruity
  name: Prop incongruity (fiction)
  scroll_stop_move: >
    First frame holds one surprising object or impossible prop in the
    Higgsfield scene so the eye locks before text is read.
  intended_viewer_effect: >
    Hypothesis: mild incongruity reduces early_skip_rate while the viewer
    waits to see how the prop connects to the music moment.
  requirements:
    - Prop stays inside fiction-signal AI world
    - Connection to bass / crowd / switch must be readable fast
  contraindications:
    - Props used only as guru teaching aids with no music link
  channel_fit: adapt
  evidence:
    - education-batch-2026-08-18.md#v3-mino
  status: active

- id: tech-20260818-listicle-templates
  name: Generic listicle hook templates
  scroll_stop_move: >
    Copy paste advice-list hooks ("NO ONE TOLD YOU", "YOU ARE DOING THIS
    WRONG", "YOU NEED TO HEAR THIS", fake vulnerability).
  intended_viewer_effect: n/a — rejected for this channel
  requirements: []
  contraindications:
    - Entire set fails honesty / music-as-product for Spotify mixes
  channel_fit: reject
  evidence:
    - education-batch-2026-08-18.md#v0-kienobi
  status: rejected

- id: tech-20260818-pain-dream-stack
  name: Pain-point + dream-outcome hook stack
  scroll_stop_move: >
    Stack fear consequences then grand life outcomes before delivering value.
  intended_viewer_effect: n/a — rejected for this channel
  requirements: []
  contraindications:
    - Fear-mongering and overpromise unfit for a mix listen
    - Delaying the music (the product) to inflate watch time
  channel_fit: reject
  evidence:
    - education-batch-2026-08-18.md#v2-briarcochran
  status: rejected

- id: tech-20260818-fake-metric-banner
  name: Fake social-proof metric banner
  scroll_stop_move: >
    Overlay fabricated play/view counts on the first frame to imply prior
    virality.
  intended_viewer_effect: n/a — rejected (deception)
  requirements: []
  contraindications:
    - Misrepresents content to win attention
  channel_fit: reject
  evidence:
    - education-batch-2026-08-18.md#v3-mino
  status: rejected
```
