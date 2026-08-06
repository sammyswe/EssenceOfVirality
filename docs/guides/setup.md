# Setup

Getting the production pipeline running, on a laptop or in a Cursor cloud agent.

If you only ever drive this from a phone, you can skip most of this page: the
cloud agent environment already has everything, and
[`phone-workflow.md`](phone-workflow.md) is the guide you want.

## What is actually required

| Requirement | Why | Optional? |
| --- | --- | --- |
| Python 3.10+ | the pipeline itself | no |
| `ffmpeg` and `ffprobe` | every render and every measurement | no |
| `PyYAML` | job files, config, every artifact | no |
| `numpy` | transition detection and tempo estimation | no |
| `jsonschema` | validating artifacts before a PR | only for contributors |
| OpenMontage clone | probing, reframing, trimming, encoding | yes — ffmpeg fallbacks cover all of it |

No GPU. No API keys. No network access at render time.

## Install

```bash
git clone https://github.com/sammyswe/EssenceOfVirality.git
cd EssenceOfVirality

# Debian/Ubuntu
sudo apt-get install -y ffmpeg
# macOS
brew install ffmpeg

pip install -r tools/requirements.txt
```

Then confirm the pipeline agrees that it can run:

```bash
./process-job status
```

A healthy result looks like this. The `openmontage` line saying `absent` is
normal and not a problem — it means each capability will use its ffmpeg
fallback:

```
  ffmpeg         available
  openmontage    absent (ffmpeg fallbacks)
    probe                  ffmpeg:ffprobe
    ...
  formats        ai-scene, clean-showcase, comedy-hook, comment-prompt, curiosity,
                 picture-in-picture, reaction, split-screen, unexpected-combination
  jobs incoming  (none)
  renders        0
```

If `ffmpeg` reports `MISSING`, nothing else will work; fix that first.

## Optional: the OpenMontage clone

OpenMontage is AGPL-3.0, so it is consumed as a pinned clone rather than copied
into this repository (ADR 0001). Installing it changes which backend handles
probing, scene detection, frame sampling, reframing, trimming and the final
encode. It does not change what the pipeline can do.

```bash
git clone https://github.com/calesthio/OpenMontage.git integrations/openmontage/clone
git -C integrations/openmontage/clone checkout "$(cat integrations/openmontage/PINNED_REF)"
```

Re-run `./process-job status`; the capability lines should now name
`openmontage:` backends and the pin should report `matched`. A `MISMATCH`
means the clone has drifted from `PINNED_REF` — check out the pinned commit
again rather than working from a different version.

See [`openmontage-pipeline.md`](openmontage-pipeline.md) for the separate
agent-driven OpenMontage path.

## First run

The repository ships a synthetic Spotify-mix capture so you can prove the
install before committing any of your own media to it. The fixture is generated
rather than stored, because media never enters git:

```bash
python3 scripts/make-example-fixture.py
./process-job jobs/incoming/job-002
```

That should finish in well under a minute and end with `quality pass`. You now
have a render under `outputs/final/`, a posting package, a quality report and
an edit plan. [`new-job.md`](new-job.md) covers doing this with a real
recording.

## For contributors

Anything under `knowledge/`, `evidence/`, `.cursor/skills/`, `schemas/`,
`evaluation/rubrics/` or `docs/adr/` changes only through a pull request. Before
opening one:

```bash
python3 tools/validate_artifacts.py
python3 tools/lint_skills.py
python3 tools/check_ids.py
python3 tools/run_fixtures.py
```

All four must pass. They check that every artifact the pipeline wrote matches
its schema, that IDs are unique and well-formed, and that the skill documents
still lint.

## Where things live

| Path | What it holds |
| --- | --- |
| `jobs/` | your media and job config, moving through incoming → review → approved |
| `outputs/` | renders, previews, edit plans, posting packages, quality reports |
| `production/config/` | the tunable creative settings |
| `production/templates/` | the nine format families |
| `feedback/`, `preferences/`, `experiments/`, `analytics/` | the system's memory |
| `.cursor/skills/production/` | the ten stage skills |

`jobs/` and `outputs/` are deliberately not in git. Media never enters history,
and renders are reproducible from the job folder.
