# Scroll-stop techniques

Active techniques distilled from creator-supplied education videos
(Dropbox `/spotify-mix-videos/education/hooks-incoming/`).

**Status: empty.** No education videos have been ingested yet. Do not invent
techniques to fill this file. After `./process-job dropbox pull-education` and
analysis, each technique is added as:

```yaml
- id: tech-YYYYMMDD-short-slug
  name: ""
  scroll_stop_move: ""          # what the opening does in one line
  intended_viewer_effect: ""  # e.g. reduce early_skip_rate (hypothesis)
  requirements: []
  contraindications: []
  channel_fit: pass | adapt | reject
  evidence: []                  # source note paths / claim ids once registered
  status: active | paused | rejected
```

Only `status: active` techniques are applied by `produce-scroll-stop-hook`.
