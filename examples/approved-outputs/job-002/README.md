# job-002 — worked example with a supporting clip

The same pipeline given one extra visual asset alongside the Spotify recording,
and a `mood: funny` hint in `job.yaml`. It shows the format decision changing
because of what was supplied rather than because of a setting.

## Reproducing this run

```bash
python3 scripts/make-example-fixture.py --out examples/inputs/demo-mix
./process-job new job-002 \
  --recording examples/inputs/demo-mix/spotify-screen-recording.mp4 \
  --asset examples/inputs/demo-mix/hook-clip.mp4
# then set creative_direction.mood to "funny" in jobs/incoming/job-002/job.yaml
./process-job job-002
```

## What it shows

The comedy-hook family wins here: the supporting clip satisfies its minimum, and
the funny mood adds to its score. Every family that was considered and lost is
listed in the `decisions` block of `job-002-r1-edit-plan.yaml`, so the choice can
be argued with rather than merely accepted.

Because this job names a genre for both tracks, the unexpected-combination family
is eligible — its hook asserts the two tracks clash, and the metadata supports
that claim. Job 001 names no genres, and there the same family is refused with
"would risk a false claim". The difference is worth seeing side by side: the
pipeline declines creative angles it cannot support, however small.

The supporting clip plays full-screen at the opening and hands over to Spotify
before the transition window, so nothing overlaps the blend. That constraint is
checked, not assumed: see `spotify_visible_at_transition` in the quality report.
