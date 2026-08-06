---
name: tiktok-retention-editor
description: Turn a chosen format into concrete timing, layout, text placement and transition emphasis for a Spotify mix video. Use when building an edit plan, when a video feels slow or cluttered, or when deciding where the transition should land in the output.
metadata:
  version: 0.1.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# TikTok retention editor

Stage 3. Decides when things happen and where they sit. Implementation:
`production/pipeline/creative.py` (timing, placement, text cues) and
`production/pipeline/textrender.py`.

## Purpose

Place the transition, set the lead-in, position the Spotify surface and any
secondary footage, and time the text so each cue earns its moment.

## When to invoke

- Building an edit plan, after the format is chosen.
- When the creator says the opening is slow, the video is cluttered, or the
  transition does not land.
- When text collides with the interface or with TikTok's own controls.

## When not to invoke

- To choose the format or write the hook wording. That is
  `spotify-mix-creative-director`.
- To change the mix. The transition itself is never edited.

## Inputs

Required: the format template, the `InputReport` (transition time, protected
regions), and the duration and layout configuration.

Optional: beat estimates, `layout` overrides from feedback, supporting clip
reports.

## Workflow

1. Set the lead-in from the template's preference, adjusted by
   `duration.lead_in_adjustment_seconds`, and clamped by
   `duration.max_pre_transition_seconds`.
2. Set the tail from `duration.post_transition_seconds`, then clamp the whole
   duration into the configured posting window.
3. Compute the source window so the transition lands where the format wants it,
   and keep every cut clear of the blend region.
4. Place the Spotify surface for the layout mode: full, split band, picture-in-
   picture inset or hook cutaway.
5. Place secondary clips so none of them overlaps the transition window.
6. Write the text cues: hook early, any anticipation cue before the blend, CTA
   after the payoff. Fit each into the safe area, and move any cue that would
   cover a hard protected region or a picture-in-picture inset.
7. Set the transition emphasis — a single zoom pulse, unless disabled.
8. Done when every cue and clip has a start and end, and nothing overlaps the
   transition window or a hard region.

## Hard rules

- One transition per video, and nothing may cover it. Not a clip, not a caption,
  not an inset.
- Text never covers the song labels or the waveform. Artwork is a soft region:
  overlapping is allowed but recorded.
- Text stays inside the safe area, which is symmetric about the canvas centre so
  a centred cue cannot drift into TikTok's action rail.
- The output duration stays inside the configured window. A format that wants
  more is clamped, and the clamp is recorded as a warning.
- Cuts land clear of the blend. A cut inside the transition destroys the payoff
  the whole video is built around.

## Recommendations

- Give the hook enough time to be read at arm's length, then take it away. A
  cue that outstays its moment is the same as dead time.
- Align visual changes to detected beats when the tempo estimate is confident,
  and to nothing when it is not. A change on a wrong beat reads worse than a
  change on no beat.
- Keep the lead-in short. The transition is the payoff; everything before it is
  a promise the viewer is waiting on.
- Prefer one deliberate visual change over three incidental ones.

## Output

Contributions to the `EditPlan`: `source_in_seconds`, `source_out_seconds`,
`duration_seconds`, `transition_output_seconds`, `transition_window`,
`layout_mode`, `spotify_placement`, `spotify_content_zoom`, `secondary_clips`,
`text_cues`, `emphasis`, `progress_bar`.

## Failure conditions

| Condition | Response |
| --- | --- |
| Recording too short for the window | Use the whole recording; warn that the minimum was not reachable |
| Transition too close to the start | Shorten the lead-in to what exists; warn |
| Text cannot fit the safe area at any size | Shorten the text; if still impossible, drop the cue and warn |
| A clip would overlap the transition | Move its end before the window; warn if that leaves it too short to read |

## Example

A 30s recording with the transition at 12.4s, clean-showcase asking for a 7s
lead-in and a 14s tail: the source window becomes 5.4s–26.4s, a 21s edit with
the transition at 7.0s. The hook runs 0.1–2.7s, the CTA 16.5–19.7s, and the zoom
pulse is centred on 7.0s.

After "the opening is too slow", the lead-in adjustment drops it to 5.0s and the
edit becomes 19s. Every other decision is unchanged, which is what makes the
effect of the feedback readable.

## Anti-patterns

- Cutting on every beat because the beats were detected. Detection is a tool for
  placing the changes the edit already needs, not a reason to add more.
- Filling the tail with a second CTA. One ask, after the payoff.
- Solving a text collision by shrinking the text until it fits. Below the
  readable size it is decoration, not communication — shorten the words instead.

## Quality checklist

- [ ] Nothing overlaps `transition_window`.
- [ ] Every text cue is inside the safe area and clear of hard regions.
- [ ] Duration is inside the configured window, or the clamp is recorded.
- [ ] Each timing decision has a rationale on the plan.

## Related skills

`spotify-mix-creative-director` supplies the format and hook.
`openmontage-editor` executes the plan this produces.
`evaluate-transition-payoff` diagnoses a transition that does not land.
`analyse-first-frame` diagnoses early abandonment.

## Change history

- 0.1.0 — first version, written alongside the timing and placement code.
