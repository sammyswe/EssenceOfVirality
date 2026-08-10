---
name: mobile-job-orchestrator
description: Run a job folder end to end from a phone-driven cloud agent, return the render and its package, and drive the revision cycle. Use when the creator asks to process a mix, revise a render, approve a job, or when a job is stuck in a lifecycle state.
metadata:
  version: 0.2.0
  maturity: experimental
  confidence: medium
  evidence_basis: []
  requires_human_approval: false
---

# Mobile job orchestrator

Stage 10. The only stage that knows the order of the others. Implementation:
`production/pipeline/orchestrator.py`, CLI in `production/cli.py`.

## Purpose

Take a job folder to a post-ready render with everything the creator needs to
decide, and make each step recoverable from a phone.

## When to invoke

- "Process the newest Spotify mix job."
- "Revise job-001 using this feedback: ..."
- Approving a reviewed job, or working out why one is stuck.
- Checking what the environment can actually do before promising it.

## When not to invoke

- To make a creative decision. The orchestrator sequences; the stages decide.
- To post. The pipeline produces a file and a package; the creator posts.

## Inputs

Required: a job reference — an ID, a folder path, or `newest`.

Optional: a format override, `--dry-run` to plan without rendering,
`--ignore-feedback` to plan from scratch, `--keep-in-place` to leave the folder
where it is.

## Workflow

1. Resolve the reference across `jobs/incoming`, `review`, `approved` and
   `failed`. An unresolvable reference names every place that was searched.
2. Load and validate the job. Warn about settings written where they do nothing
   — a top-level `layout:` block in `job.yaml` belongs under `config_overrides`.
3. Apply recorded feedback for this job as configuration overrides, before
   anything is planned.
4. Inspect. On a blocking problem, move the folder to `jobs/failed/` and stop
   with the reason.
5. Load research notes when research is enabled, and warn when none match — the
   copy will then avoid factual claims.
6. Plan, then apply any feedback adjustments to the plan.
7. Fingerprint every source file before rendering.
8. Render the final and the preview.
9. Run the quality checks. A failure leaves the job in place with the report
   written; the creator decides.
10. Create the experiment record, build the posting package, write the plan and
    the production manifest.
11. Move the folder to `jobs/review/` on success.
12. Done when the result names every artifact by path and states its status.

## Hard rules

- The creator's media is never modified, renamed or moved out of its job folder.
  Fingerprints before and after prove it.
- A job that fails quality is not moved to review and is not described as ready.
- Every render gets a new revision number. Nothing overwrites an earlier one.
- Never claim the workflow worked without having run it end to end.
- Report what is verified separately from what is assumed, especially anything
  depending on the cloud-agent environment.

## Recommendations

- Say what changed between revisions, not just that a new one exists. The
  creator is deciding on a phone.
- Surface the render notes. They carry the things the creator would otherwise
  have to discover by watching.
- Prefer the preview for review — it is a fraction of the size and downloads on
  a phone connection.
- When a stage warns, keep going and collect the warnings. A run that stops at
  the first imperfection is less useful than one that finishes and reports.

## Output

`JobResult`: `job_id`, `revision`, `status` (`review`, `planned`,
`quality_failed`, `failed`), paths to the final, preview, plan, package,
quality report and manifest, the experiment ID, and the messages and warnings
collected along the way.

## Failure conditions

| Condition | Response |
| --- | --- |
| Job reference resolves nowhere | Error naming every directory searched |
| No job folders at all | Error suggesting `./process-job new <id>` |
| FFmpeg missing | Error before any work begins |
| Inspection blocked | Move to `jobs/failed/`, report the problems |
| Render failed | Move to `jobs/failed/`, report with the filter graph |
| Quality failed | Leave in place, write the report, return `quality_failed` |
| Creative minimum failed | Leave in place, write creative-minimum report, return `needs_creative_input`; do not move to `jobs/review/` |
| Revising a job with no earlier render | Error; run the job first |

## Phone workflow

The verified path, in the environment this repository runs in, is: the creator
attaches the recording in the Cursor mobile client; the agent copies it into a
job folder and runs the pipeline; the agent copies the render into the cloud
agent's artifact directory and references it from the pull request, where it
becomes a link the creator can open and download on the phone. See
`docs/guides/phone-workflow.md` for what has been verified and what has not.

## Example

`./process-job job-001` returns: review status, clean-showcase, 21.00s with the
transition at 7.00s, quality pass with 25 checks, and six artifact paths. The
job folder has moved to `jobs/review/job-001/`.

`./process-job revise job-001 "the opening is too slow ..."` records the
feedback, re-plans, renders revision 2, and reports which directives were
applied and which preference proposals are waiting.

## Anti-patterns

- Moving a job to review because the render finished. Finished is not passed.
  Technical pass without creative minimum is `needs_creative_input`, not review.
- Deleting a failed revision to keep the output directory tidy. The failure is
  the evidence for the fix.
- Reporting a path the creator cannot reach from a phone. A path inside the
  container is not a delivery.

## Quality checklist

- [ ] Source fingerprints taken before rendering and compared after.
- [ ] Job folder ends in the state its outcome implies.
- [ ] Every artifact named by path in the result.
- [ ] Warnings surfaced rather than buried in a file.

## Related skills

Every other production skill runs inside this one.
`video-quality-controller` decides whether a job reaches review.
`feedback-interpreter` drives the revision cycle.

## Change history

- 0.1.0 — first version, written alongside `production/pipeline/orchestrator.py`.
