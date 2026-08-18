# Hook profiles

Each Higgsfield hook clip can have a profile under
`production/config/hook-profiles/`. A profile describes what is actually on
screen, and binds that clip to overlay wording, allowed CTAs, and **exactly
three captions** that rotate across posts reusing the clip.

## Why

Global copy-bank rotation is the fallback. When a job's hook asset matches a
profile (filename stem or asset label), the planner uses that profile instead
— so captions can refer to the scene honestly, and each clip becomes its own
small A/B test.

## File shape

Copy `_template.yaml`, rename without the leading underscore, fill in:

| Field | Purpose |
| --- | --- |
| `id` | Stable profile id (usually matches the renamed clip stem) |
| `status` | `draft` / `testing` / `proven` / `retired` — same lifecycle as the copy bank |
| `asset_stems` | Filename stems / labels that match this profile |
| `description` | What happens on screen — written when the clip is analysed |
| `overlay_hook_ids` | Copy-bank hook ids allowed on this overlay (empty = global) |
| `overlay_texts` | Optional inline overlay lines when no bank id fits yet |
| `cta_ids` | Copy-bank CTA ids allowed for this clip (empty = global) |
| `captions` | Exactly three `{id, template, status}` entries |
| `fiction_signal` | How the stylised AI scene stays honest |

Draft profiles never drive a render. After you approve the wording,
set `status: testing` (or ask the agent to).

## Matching

The job's `role: hook` asset is preferred. The stem of its filename or its
`label` in `job.yaml` must equal one of `asset_stems` (case-insensitive).
Rename clips when they land (`hook-01-decks-spotify-green.mp4`) and keep the
stem stable forever so analytics attribute results to the right profile.

The first Higgsfield batch lives in Dropbox at
`/spotify-mix-videos/hooks/library/` under these stems (`hook-01-…` through
`hook-10-…`). Originals are archived in `hooks/imported/`. Profiles for that
batch start as `draft` until you approve them.

## Captions

Profile captions win over the global bank when a profile matched. They still
support `{pairing}`; unfillable placeholders are skipped for that job. Rotate
deterministically per job + revision so the three lines get tested over time.

See also [`copy-bank.md`](copy-bank.md) and the Dropbox loop in
[`phone-workflow.md`](phone-workflow.md).
