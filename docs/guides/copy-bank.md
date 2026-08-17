# The copy testing bank

`production/config/copy-bank.yaml` holds every piece of wording the pipeline
may use — hooks, on-screen calls to action, captions and pinned comments —
each with a lifecycle status. It exists so wording is a managed experiment
rather than something re-invented per job.

## Lifecycle

| Status | Meaning | Rendered? |
| --- | --- | --- |
| `draft` | Proposed; awaiting the creator's ruling (usually a grilling session) | never |
| `testing` | Approved into rotation; performance unknown | yes |
| `proven` | Repeatedly associated with strong posts | yes |
| `retired` | Pulled from rotation; the notes say why | never |

The pipeline draws only from `testing` and `proven` entries. A drafted idea
cannot reach a render until the creator approves it — that is the point.

## Commands

```bash
./process-job copy list                    # everything, grouped by section
./process-job copy list --status draft     # what is waiting for a ruling
./process-job copy approve cta-006         # draft -> testing
./process-job copy promote cta-001         # testing -> proven
./process-job copy retire hook-013 --note "reads as ragebait"
```

Status changes rewrite the YAML file, so commentary lives in each entry's
`notes` field — the tool preserves it and appends the transition history.

## How entries reach a render

- **Hooks and CTAs** merge into the format template's own pattern lists
  (deduplicated by text) and rotate deterministically per job. The chosen
  entry's bank id is recorded in the plan's rationale, so analytics can
  attribute results to wording.
- **CTA slot affinity**: an entry may declare `slots` (`build`,
  `post_payoff`, `closing`). "guess the second song before the switch" only
  makes sense before the transition, so its rotation is narrowed to `build`.
- **Captions and pinned comments** rotate per job and revision inside the
  posting package. `{pairing}` is filled from `job.yaml` tracks; an entry
  whose placeholders cannot be filled is skipped for that job, never posted
  broken.

## Rules the bank inherits

- Hooks and CTAs are rendered through FFmpeg `drawtext`: **no emoji** — they
  come out as tofu boxes. Captions and pinned comments are posted text, so
  emoji are fine there and should match the creator's reference density.
- Milestone promises ("playlist link at 1000 followers") are commitments.
  They stay `draft` until the creator states the promise is real, and they
  are retired the moment the promise is fulfilled or dropped.
- No wording may promise a performance outcome or assert an unverifiable
  fact. Entries that skirt the line carry a FLAG in their notes so the
  grilling session rules on them explicitly.

## Refining over time

After posting, record results against the video
(`./process-job analytics record <video-id> --field views=...`). The posting
package holds the exact caption and CTA text, and `copybank.find_by_text`
maps wording back to its bank id, so entries can be promoted or retired on
evidence rather than memory. One post proves nothing — promotion needs
repetition.
