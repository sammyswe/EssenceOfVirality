# Changing how the pipeline behaves

Most of what you would want to change is configuration, not code, and not a
skill. This page is about picking the right layer, then changing it safely.

## Pick the layer first

| You want to change | Change this | Needs a PR |
| --- | --- | --- |
| how big Spotify is, how long the lead-in runs, hashtag mix, text style | `production/config/*.yaml` | no |
| what a format family does, or add a tenth | `production/templates/*.yaml` | no |
| a rule for this job only | `config_overrides` in `job.yaml` | no |
| a lasting creative rule | a preference, via feedback | no |
| how a stage decides or renders | `production/pipeline/*.py` | no |
| the documented contract for a stage | `.cursor/skills/production/*/SKILL.md` | **yes** |
| a hard rule | `production/pipeline/rules.py` + the skill | **yes**, and think hard |

Work down that table, not up. If a config value gets you there, stop.

## Configuration

`production/config/` holds everything creative that is meant to move:

| File | Holds |
| --- | --- |
| `defaults.yaml` | durations, layout proportions, zoom, hook and CTA behaviour, quality thresholds |
| `crop-profiles.yaml` | how each source shape is cropped, and which regions are hard or soft protected |
| `safe-zones.yaml` | where text may be placed on the canvas |
| `text-styles.yaml` | fonts, sizes, colours, animations |
| `render-presets.yaml` | encoder settings per output target |

Changing one takes effect on the next run. To try a value without committing to
it, put it in one job's `config_overrides` first.

The distinction that matters in `crop-profiles.yaml` is `region_enforcement`.
Regions listed under `hard` — the song labels and the waveform — can never be
cropped away or covered by text. Regions under `soft` — the album artwork —
are preferred but yielding. Moving a region between those lists changes a hard
rule, so it belongs in a PR with a reason.

## Format families

A family is a YAML file in `production/templates/`. Adding one is adding a file;
it does not involve the renderer.

```bash
cp production/templates/curiosity.yaml production/templates/my-format.yaml
$EDITOR production/templates/my-format.yaml
./process-job formats
./process-job job-003 --format my-format --dry-run
```

A template declares what it needs (how many supporting clips, whether it needs
track genres), where things go, and what it is trying to do for the viewer.
`creative.choose_format` scores it against the others automatically.

Test it with `--dry-run` before rendering. A family that asks for assets a job
does not have is refused with a reason, which is the intended behaviour rather
than a bug.

## Pipeline code

The ten stages under `production/pipeline/` map one-to-one onto the ten skills.
Two structural rules keep the design from eroding:

**The renderer decides nothing.** `render.py` reads only the `EditPlan`. It
consults no configuration and no preferences. If you find yourself wanting to
read a config value inside the renderer, the decision belongs upstream in
`creative.py` and the result belongs in a new `EditPlan` field.

**Hard rules are checked twice.** Once in `rules.py` before rendering, once in
`quality.py` against the finished file. A new hard rule needs both, or it is a
suggestion.

After any change:

```bash
./process-job job-002 --ignore-feedback
python3 tools/validate_artifacts.py && python3 tools/lint_skills.py \
  && python3 tools/check_ids.py && python3 tools/run_fixtures.py
```

`--ignore-feedback` plans from scratch, which is what you want when comparing
against a previous render rather than continuing a revision chain.

## Skill documents

`.cursor/skills/production/*/SKILL.md` documents each stage's contract: purpose,
inputs, workflow, hard rules, output, failure conditions, anti-patterns. These
change **only via pull request** (`AGENTS.md`), and they must stay true to the
code — a skill describing behaviour the implementation does not have is worse
than no skill.

Follow `.cursor/skills/meta/skill-authoring-standard/SKILL.md`. In short:

- Frontmatter carries `name` (matching the folder), `description`, and
  `metadata` with `version`, `maturity`, `confidence`, `evidence_basis`,
  `requires_human_approval`.
- Steps end on something checkable. "Consider the pacing" is not an instruction;
  "reject the plan if the lead-in exceeds `max_pre_transition_seconds`" is.
- No promises about virality, and no claims that a technique acts on TikTok's
  ranking. State the viewer behaviour you expect instead.
- Conclusions live in `knowledge/`, linked rather than restated.

```bash
python3 tools/lint_skills.py
```

### Versioning

Per ADR 0005: behavioural changes bump `version` and need a before/after
regression record in `evaluation/regression/`. Maturity moves
`experimental → provisional → validated → stable` only by PR, and anything past
`provisional` needs evidence refs backed by first-party analytics or a creator
experiment. The production skills are all `0.1.0` and `experimental`, which is
honest: they describe a pipeline validated against one synthetic capture.

Deprecated skills keep their files with `maturity: deprecated` so citations
survive.

## Hard rules

The list in `rules.py` — Spotify audio only, protected regions intact, one
transition, vertical output inside the duration window, inputs never modified,
no unsourced factual claims — is deliberately hard to change. Each exists
because breaking it either misrepresents the content or destroys the thing the
video is about.

If a hard rule genuinely blocks something worth doing, the pattern to copy is
`layout.waveform_end_trim`: an explicit, opt-in setting that names what it
sacrifices and downgrades the check to a warning that says so, rather than
loosening the rule for everyone.

## Learning from results, not guesses

The system's memory lives in `feedback/`, `preferences/`, `experiments/`,
`analytics/posts/` and `research/tracks/`, all of it in git, so what the
pipeline has learned is reviewable in a diff.

After posting:

```bash
./process-job analytics record job-003-r2 \
  --field views=12400 --field likes=830 --field comments=64 \
  --field format_family=comedy-hook --field duration_seconds=19

./process-job analytics report
```

The report groups by format family, duration band, hook type and hashtag
strategy, but only above a minimum group size, always labelled with how many
posts sit behind each comparison, and always `more_evidence_required` until
several posts agree. One good video establishes nothing. Do not encode a
conclusion from it — run it again as an experiment:

```bash
./process-job experiments list
./process-job experiments results exp-20260806-job-003-r2 \
  --field retention_3s=0.62 --interpretation "held better than the r1 control"
```

When several posts do agree, the change that follows is usually a config value
or a template — the bottom of the table, not the top.
