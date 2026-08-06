# Giving feedback

Say what is wrong in plain language. The pipeline turns that into concrete
changes, re-renders, and — separately — proposes any lasting rule it thinks it
heard. Nothing becomes permanent without you approving it.

```bash
./process-job revise job-003 "the opening is too slow and the hook is generic"
```

## What comes back

```
  feedback fb-20260806-111303-job-003-r1
  scope    one_off (confidence medium)
    issue    The opening takes too long to reach the payoff.
    issue    The hook is too generic.
    change   shorten_lead_in {'seconds': 2.0} — from 'opening is too slow'
    change   regenerate_hook {'avoid_previous': True} — from 'hook is generic'

  job-003 revision 2: review
  ...
```

Every change names the phrase that produced it. That is the point of the design:
when the system reads you wrong you can see exactly which words it caught, and
rephrase rather than argue with it.

## Interpretation is rule-based

Feedback is matched against a fixed list of patterns, not passed to a model.
The trade is deliberate. It cannot understand everything, but it never invents
an interpretation, and anything it did not understand is reported:

```
    unread   'the vibe is off'
```

Unread phrases are stored verbatim in the feedback record. They are not
guessed at and not silently dropped. If something goes unread, either rephrase
it using the vocabulary below or make the change yourself in `job.yaml`.

## What it understands

| Say something like | Effect |
| --- | --- |
| "the Spotify is too small", "make the waveform bigger" | enlarges the interface |
| "Spotify is too big" | shrinks it |
| "the hook is generic / boring / weak" | writes a different hook |
| "the opening is too slow / drags" | trims the lead-in |
| "the AI clip distracts / overpowers it" | shortens the supporting clip |
| "remove the hook clip" | drops it entirely |
| "remove the final zoom", "never use that zoom" | disables transition zoom |
| "more emphasis on the transition", "stronger punch" | increases it |
| "remove the progress bar" | disables it |
| "the caption sounds artificial / robotic" | rewrites it plainly |
| "keep this text style" | proposes it as a preference |
| "use this layout more" | proposes the format as a preference |
| "too long", "make it shorter" | trims about four seconds |
| "too short", "make it longer" | extends about four seconds |
| "no text", "remove the captions" | drops on-screen text |
| "the CTA is weak" | writes a different one |
| "switch to split-screen / PiP / clean showcase / comedy hook / curiosity / reaction" | changes format |

You can combine them in one sentence. Feedback is split on punctuation and on
"and" before a verb, so this produces three separate changes:

```bash
./process-job revise job-003 \
  "the opening is too slow, make the waveform larger, and remove the final zoom"
```

To see how something will be read without rendering:

```bash
./process-job feedback interpret job-003 "the hook is boring"
```

## One-off versus lasting

The wording decides whether a change applies once or gets proposed as a rule.

**Lasting** — "always", "never", "from now on", "going forward", "every time",
"as a rule", "by default", "keep this", "stop using", "use this more".

**One-off** — "this time", "just here", "on this one", "for this video", "in
this edit".

**Neither** is treated as one-off, at low confidence.

So "remove the zoom on this one" changes one render, while "never use that
zoom" also writes a preference proposal. Both re-render identically; they
differ in what they leave behind.

You can also scope a rule to a format with "but only for …":

> Use this layout more, but only for funny videos.

That proposes a preference scoped to the format family rather than globally.

## Promotion is explicit

```
raw text  →  feedback/raw/<id>.txt          verbatim, always
          →  feedback/structured/<id>.yaml  directives, each naming its trigger
          →  config overrides               applied to this revision
          →  preferences/proposed/<id>.yaml a rule, not yet in force
          →  preferences/approved/<id>.yaml only after you approve it
```

A proposal changes nothing. It becomes active when you approve it:

```bash
./process-job prefs list
./process-job prefs approve pref-20260806-zoom-emphasis-global-remove-the-final-zoo
```

The only other route is repetition: a preference proposed from three separate
feedback events becomes promotable, and `./process-job approve` lists those
with their support count. Even then you run the approve command — the system
does not promote itself.

Approving a preference that contradicts an active one supersedes it by link.
The superseded rule stays on disk, so a bad call is recoverable.

## Verifying that a preference did something

Approving `zoom_emphasis: false` should visibly change the next render. Diff
the plans rather than trusting the summary:

```bash
diff <(python3 -c "import yaml;print(yaml.safe_dump(yaml.safe_load(open('outputs/edit-plans/job-003-r2-edit-plan.yaml'))['emphasis']))") \
     <(python3 -c "import yaml;print(yaml.safe_dump(yaml.safe_load(open('outputs/edit-plans/job-003-r3-edit-plan.yaml'))['emphasis']))")
```

```
< enabled: true
---
> enabled: false
```

This is exactly how the loop was verified for this repository: feedback on
job-001 proposed the rule, approval activated it, and job-002's next render
dropped the zoom with no further instruction.

## When feedback does not seem to work

A few requests have physical limits, and the pipeline tells you rather than
silently under-delivering.

**"Make the waveform larger" barely changed anything.** The waveform already
spans most of the frame width, so it cannot grow much before its own ends are
cut. The run reports the ceiling it hit and names `layout.waveform_end_trim`,
which you set explicitly to trade the waveform's ends for a larger interface.
It is opt-in because it breaks a protected region on purpose.

**"Shorten the opening" stopped having an effect.** The lead-in is bounded by
`duration.max_pre_transition_seconds` and by how much footage exists before the
transition. If the recording only has three seconds before the mix, that is the
floor.

**A format change was refused.** Some families need assets you did not supply,
and unexpected-combination additionally needs two genuinely different genres in
`tracks`. The run explains which requirement failed.

## Approving the result

```bash
./process-job approve job-003
```

The folder moves to `jobs/approved/` with every revision it went through kept
under `outputs/`, and any preference with enough repeated support is listed for
approval.
