"""Command-line entry point for the production pipeline.

Reachable as ``./process-job`` from the repository root, or
``python -m production.cli``.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

import yaml

from .pipeline import analytics, copybank, delivery, dropbox_sync, experiments, feedback, hookprofiles, orchestrator
from .pipeline import preferences as prefs
from .pipeline import research
from .pipeline.jobspec import JobError, load_job, write_job_template
from .pipeline.om import capability_report
from .pipeline.paths import (
    JOBS_INCOMING,
    OUTPUTS_FINAL,
    OUTPUTS_PREVIEWS,
    ensure_dirs,
    load_templates,
    rel,
)
from .pipeline.probe import MediaError, require_binaries

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
DIM = "\033[2m"
RESET = "\033[0m"


def _colour(text: str, code: str) -> str:
    return text if not sys.stdout.isatty() else f"{code}{text}{RESET}"


def _print_result(result: orchestrator.JobResult) -> None:
    status_colours = {
        "review": GREEN, "planned": GREEN, "quality_failed": YELLOW, "failed": RED,
    }
    print()
    print(f"  {result.job_id} revision {result.revision}: "
          f"{_colour(result.status, status_colours.get(result.status, DIM))}")

    if result.plan is not None:
        plan = result.plan
        print(f"  format         {plan.template_name} ({plan.format_family})")
        print(f"  duration       {plan.duration_seconds:.2f}s, "
              f"transition at {plan.transition_output_seconds:.2f}s")
        if plan.hook_text:
            print(f"  hook           {plan.hook_text!r}")
        if plan.cta_text:
            print(f"  call to action {plan.cta_text!r}")

    if result.quality_report is not None:
        report = result.quality_report
        summary = report.as_dict()["summary"]
        print(f"  quality        {report.status} "
              f"({summary['passed']} passed, {summary['warnings']} warnings, "
              f"{summary['failures']} failures)")
        for check in report.failures:
            print(f"                 {_colour('FAIL', RED)} {check.id}: {check.detail}")
        for check in report.warnings:
            print(f"                 {_colour('warn', YELLOW)} {check.id}: {check.detail}")

    print()
    for label, path in (
        ("final", result.final_path),
        ("preview", result.preview_path),
        ("package", result.package_path),
        ("quality", result.quality_path),
        ("plan", result.plan_path),
        ("manifest", result.manifest_path),
    ):
        if path:
            print(f"  {label:<9} {rel(path)}")

    if result.experiment_id:
        print(f"  experiment {result.experiment_id}")

    for message in result.messages:
        print(f"  {DIM}- {message}{RESET}" if sys.stdout.isatty() else f"  - {message}")
    for warning in result.warnings:
        print(f"  {_colour('warn', YELLOW)} {warning}")
    print()


def cmd_run(args: argparse.Namespace) -> int:
    reference = args.job
    if reference in {None, "", "newest", "latest"}:
        job_dir = orchestrator.newest_job()
    else:
        job_dir = orchestrator.find_job(reference)

    result = orchestrator.process(
        job_dir,
        format_override=args.format,
        apply_feedback=not args.ignore_feedback,
        make_preview=not args.no_preview,
        dry_run=args.dry_run,
        move_on_success=not args.keep_in_place,
    )
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
    else:
        _print_result(result)
    return 0 if result.status in {"review", "planned"} else 1


def cmd_revise(args: argparse.Namespace) -> int:
    record, result = orchestrator.revise(args.job, args.feedback)
    if args.json:
        print(json.dumps(
            {"feedback": record.as_dict(), "result": result.as_dict()}, indent=2, default=str
        ))
        return 0 if result.status == "review" else 1

    print()
    print(f"  feedback {record.id}")
    print(f"  scope    {record.scope} (confidence {record.confidence})")
    for issue in record.interpreted_issues:
        print(f"    issue    {issue}")
    for directive in record.directives:
        print(f"    change   {directive.action} "
              f"{directive.parameters or ''} — from {directive.trigger_phrase!r}")
    for phrase in record.unmatched_phrases:
        print(f"    {_colour('unread', YELLOW)}   {phrase!r}")
    for preference_id in record.proposed_preferences:
        print(f"    proposed {preference_id} "
              f"{DIM}(approve with `./process-job prefs approve <id>`){RESET}")
    _print_result(result)
    return 0 if result.status == "review" else 1


def cmd_new(args: argparse.Namespace) -> int:
    ensure_dirs()
    job_dir = JOBS_INCOMING / args.job_id
    if job_dir.exists() and any(job_dir.iterdir()):
        print(f"Job folder already exists and is not empty: {rel(job_dir)}", file=sys.stderr)
        return 1
    job_dir.mkdir(parents=True, exist_ok=True)

    spotify_name = "spotify-screen-recording.mp4"
    if args.recording:
        source = Path(args.recording)
        if not source.is_file():
            print(f"Recording not found: {source}", file=sys.stderr)
            return 1
        spotify_name = source.name
        shutil.copy2(source, job_dir / spotify_name)
        print(f"  copied {source.name} into {rel(job_dir)}")

    for extra in args.asset or []:
        source = Path(extra)
        if not source.is_file():
            print(f"Asset not found: {source}", file=sys.stderr)
            return 1
        shutil.copy2(source, job_dir / source.name)
        print(f"  copied {source.name} into {rel(job_dir)}")

    path = write_job_template(job_dir, args.job_id, spotify_name)
    print(f"  wrote {rel(path)}")
    print()
    print(f"Next: drop the Spotify recording in {rel(job_dir)}/ if you have not already,")
    print(f"then run  ./process-job {args.job_id}")
    return 0


def cmd_inspect(args: argparse.Namespace) -> int:
    from .pipeline import inspector

    job = load_job(orchestrator.find_job(args.job))
    report = inspector.inspect(job, analyse_beats=not args.skip_beats)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2))
        return 0 if report.ok else 1

    spotify = report.spotify
    print()
    print(f"  job            {job.job_id}")
    print(f"  recording      {rel(job.spotify_recording)}")
    print(f"  geometry       {spotify['width']}x{spotify['height']} "
          f"({spotify['aspect_ratio']:.3f}), {spotify['duration_seconds']:.2f}s, "
          f"{spotify['fps']:.2f} fps")
    print(f"  crop profile   {report.crop_profile.name} — {report.crop_profile.match_reason}")
    if report.transition:
        transition = report.transition
        print(f"  transition     {transition['seconds']:.2f}s "
              f"({transition['method']}, {transition['confidence']} confidence)")
        if transition.get("alternatives"):
            print(f"                 alternatives: "
                  f"{', '.join(f'{value:.2f}s' for value in transition['alternatives'])}")
    if report.beats:
        print(f"  tempo          {report.beats['bpm']:.1f} BPM "
              f"({report.beats['confidence']} confidence)")
    if report.loudness:
        loudness = report.loudness
        print(f"  loudness       {loudness['integrated_lufs']:.2f} LUFS, "
              f"peak {loudness['true_peak_db']:.2f} dBTP — {loudness['reason']}")
    for asset in report.assets:
        state = "usable" if asset.usable else "unusable"
        print(f"  asset          {asset.filename} [{asset.role}] {state}, "
              f"{asset.duration_seconds:.2f}s, {asset.width}x{asset.height}")
    for problem in report.blocking_problems:
        print(f"  {_colour('BLOCK', RED)}          {problem}")
    for warning in report.warnings:
        print(f"  {_colour('warn', YELLOW)}           {warning}")
    print()
    return 0 if report.ok else 1


def cmd_approve(args: argparse.Namespace) -> int:
    destination = orchestrator.approve(args.job)
    print(f"  approved; job folder moved to {rel(destination)}")
    promotable = prefs.promotable()
    if promotable:
        print()
        print("  Preferences with enough repeated support to approve:")
        for preference in promotable:
            print(f"    {preference.id}  {preference.statement!r} "
                  f"({preference.support_count} mentions)")
        print("  Approve with: ./process-job prefs approve <id>")
    return 0


def cmd_prefs(args: argparse.Namespace) -> int:
    if args.prefs_command == "list":
        print(json.dumps(prefs.summary(), indent=2, default=str))
        return 0
    if args.prefs_command == "approve":
        preference = prefs.approve(args.preference_id)
        print(f"  approved {preference.id}: {preference.statement}")
        print(f"  applies to scope {preference.scope!r} with value {preference.value!r}")
        return 0
    if args.prefs_command == "propose":
        preference = prefs.propose(
            key=args.key, value=_parse_value(args.value),
            statement=args.statement, scope=args.scope, scope_value=args.scope_value or "",
        )
        print(f"  proposed {preference.id} (not active until approved)")
        return 0
    return 1


def _parse_value(raw: str) -> Any:
    lowered = raw.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def cmd_analytics(args: argparse.Namespace) -> int:
    if args.analytics_command == "record":
        fields: dict[str, Any] = {"video_id": args.video_id}
        for pair in args.field or []:
            key, _, value = pair.partition("=")
            if not key or not _:
                print(f"Bad --field {pair!r}; expected key=value", file=sys.stderr)
                return 1
            fields[key.strip()] = _parse_value(value)
        record = analytics.record_post(**fields)
        print(f"  recorded {record.video_id} ({record.posted_date})")
        return 0
    if args.analytics_command == "report":
        print(json.dumps(analytics.report(), indent=2, default=str))
        return 0
    return 1


def cmd_experiments(args: argparse.Namespace) -> int:
    if args.experiments_command == "list":
        print(json.dumps(experiments.summary(), indent=2, default=str))
        return 0
    if args.experiments_command == "results":
        results: dict[str, Any] = {}
        for pair in args.metric or []:
            key, _, value = pair.partition("=")
            results[key.strip()] = _parse_value(value)
        experiment = experiments.record_results(
            args.experiment_id, results, interpretation=args.interpretation or ""
        )
        print(f"  results recorded for {experiment.id}")
        print("  more evidence is still required: one post cannot establish an effect")
        return 0
    return 1


def cmd_research(args: argparse.Namespace) -> int:
    if args.research_command == "add":
        try:
            note = research.add_note(
                subject=args.subject, kind=args.kind, summary=args.summary,
                source_url=args.url, source_name=args.source or args.url,
                published_date=args.published, event_date=args.event,
                caption_angle=args.caption_angle or "", hook_angle=args.hook_angle or "",
            )
        except research.ResearchError as exc:
            print(f"Rejected: {exc}", file=sys.stderr)
            return 1
        print(f"  added {note.id}")
        for warning in note.warnings:
            print(f"  {_colour('warn', YELLOW)} {warning}")
        return 0
    if args.research_command == "brief":
        print(json.dumps(research.research_brief(args.subject), indent=2, default=str))
        return 0
    return 1


def cmd_feedback(args: argparse.Namespace) -> int:
    if args.feedback_command == "list":
        records = feedback.load_for_job(args.job)
        print(json.dumps([record.as_dict() for record in records], indent=2, default=str))
        return 0
    if args.feedback_command == "interpret":
        record = feedback.interpret(args.text, job_id=args.job, revision=0)
        print(json.dumps(record.as_dict(), indent=2, default=str))
        return 0
    return 1


def cmd_deliver(args: argparse.Namespace) -> int:
    result = delivery.stage(args.video_id)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2))
        return 0 if result.available else 1

    print()
    if not result.staged:
        print(f"  {_colour('error', RED)} {result.reason}", file=sys.stderr)
        return 1
    for entry in result.staged:
        target = entry["published_path"] or "(not published)"
        print(f"  {entry['label']:<10} {entry['source']}")
        if entry["published_path"]:
            print(f"             -> {target}")
    if not result.available:
        print()
        print(f"  {_colour('note', YELLOW)} {result.reason}")
    else:
        print()
        print("  Reference these paths from the pull request body; the cloud agent")
        print("  uploads them and rewrites them to links openable on a phone.")
    for warning in result.warnings:
        print(f"  {_colour('warn', YELLOW)} {warning}")
    print()
    return 0 if result.available else 1


def cmd_copy(args: argparse.Namespace) -> int:
    if args.copy_command == "list":
        if args.json:
            print(json.dumps(copybank.load_bank(), indent=2, default=str))
            return 0
        print()
        for section in copybank.SECTIONS:
            rows = copybank.entries(section)
            if args.section and section != args.section:
                continue
            if args.status:
                rows = [row for row in rows if row.get("status") == args.status]
            if not rows:
                continue
            print(f"  {section}")
            for row in rows:
                text = str(row.get("text") or row.get("template") or "")
                extra = str(row.get("intent") or row.get("kind") or "")
                extra = f" [{extra}]" if extra else ""
                print(f"    {row['id']:<10} {row['status']:<8}{extra} {text!r}")
            print()
        summary = copybank.summary()["sections"]
        active_total = sum(
            counts["by_status"].get("testing", 0) + counts["by_status"].get("proven", 0)
            for counts in summary.values()
        )
        print(f"  {active_total} entr{'y' if active_total == 1 else 'ies'} active "
              "(testing or proven); drafts never render")
        profiles = hookprofiles.summary()
        if profiles["total"]:
            print()
            print(f"  hook profiles ({profiles['total']})")
            for row in profiles["profiles"]:
                print(f"    {row['id']:<28} {row['status']:<8} stems={row['stems']}")
        else:
            print()
            print("  hook profiles: none yet — drop clips in Dropbox, then analyse")
        print()
        return 0

    transitions = {"approve": "testing", "promote": "proven", "retire": "retired"}
    status = transitions[args.copy_command]
    entry = copybank.set_status(args.entry_id, status, note=args.note or "")
    text = str(entry.get("text") or entry.get("template") or "")
    print(f"  {entry['id']} -> {status}: {text!r}")
    if status == "testing":
        print("  now in rotation for future renders")
    elif status == "retired":
        print("  out of rotation; the entry and its notes stay on record")
    return 0


def cmd_dropbox(args: argparse.Namespace) -> int:
    if args.dropbox_command == "status":
        payload = dropbox_sync.status()
        if args.json:
            print(json.dumps(payload, indent=2))
            return 0 if payload.get("reachable") else 1
        print()
        if not payload.get("configured"):
            print(f"  {_colour('not configured', YELLOW)}: {payload['reason']}")
        elif not payload.get("reachable"):
            print(f"  {_colour('unreachable', RED)}: {payload['reason']}")
        else:
            print(f"  account       {payload['account']}")
            print(f"  drop mixes in {payload['incoming']}")
            print(f"  renders go to {payload['renders']}")
        print()
        return 0 if payload.get("reachable") else 1

    if args.dropbox_command == "pull":
        result = dropbox_sync.pull()
        if args.json and not args.run:
            print(json.dumps(result.as_dict(), indent=2))
            return 0
        print()
        for job in result.created:
            print(f"  imported {job.job_id}: recording {job.recording}"
                  + (f", assets {', '.join(job.assets)}" if job.assets else ""))
        for line in result.skipped:
            print(f"  {_colour('skip', YELLOW)} {line}")
        for line in result.messages:
            print(f"  {DIM}- {line}{RESET}" if sys.stdout.isatty() else f"  - {line}")
        print()

        if not args.run:
            if result.created:
                print("  Next: ./process-job newest   (or: dropbox pull --run)")
                print()
            return 0

        exit_code = 0
        for job in result.created:
            processed = orchestrator.process(orchestrator.find_job(job.job_id))
            _print_result(processed)
            if processed.status not in {"review", "planned"}:
                exit_code = 1
                continue
            video_id = f"{processed.job_id}-r{processed.revision}"
            pushed = dropbox_sync.push(video_id, delivery.render_paths(video_id))
            for entry in pushed.uploaded:
                print(f"  {entry['label']:<10} {entry['link'] or entry['dropbox_path']}")
            print()
        return exit_code

    if args.dropbox_command == "push":
        files = delivery.render_paths(args.video_id)
        result = dropbox_sync.push(args.video_id, files)
        if args.json:
            print(json.dumps(result.as_dict(), indent=2))
            return 0
        print()
        for entry in result.uploaded:
            print(f"  {entry['label']:<10} {entry['link'] or entry['dropbox_path']}")
        for line in result.messages:
            print(f"  {DIM}- {line}{RESET}" if sys.stdout.isatty() else f"  - {line}")
        print()
        return 0
    return 1


def cmd_status(args: argparse.Namespace) -> int:
    ensure_dirs()
    capabilities = capability_report()
    binaries_ok = True
    try:
        require_binaries()
    except MediaError as exc:
        binaries_ok = False
        capabilities["ffmpeg_error"] = str(exc)

    payload = {
        "ffmpeg_available": binaries_ok,
        **capabilities,
        "formats": sorted(load_templates()),
        "jobs": {
            "incoming": sorted(p.name for p in JOBS_INCOMING.iterdir() if p.is_dir())
            if JOBS_INCOMING.is_dir() else [],
        },
        "renders": sorted(p.name for p in OUTPUTS_FINAL.glob("*.mp4"))
        if OUTPUTS_FINAL.is_dir() else [],
        "previews": sorted(p.name for p in OUTPUTS_PREVIEWS.glob("*.mp4"))
        if OUTPUTS_PREVIEWS.is_dir() else [],
        "preferences": prefs.summary(),
        "experiments": experiments.summary(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, default=str))
        return 0

    print()
    print(f"  ffmpeg         {'available' if binaries_ok else _colour('MISSING', RED)}")
    om = capabilities["openmontage"]
    print(f"  openmontage    {'present' if om['available'] else 'absent (ffmpeg fallbacks)'}"
          + (f", pin {'matched' if om['matches_pin'] else 'MISMATCH'}" if om["available"] else ""))
    for name, backend in capabilities["capabilities"].items():
        print(f"    {name:<22} {backend}")
    print(f"  formats        {', '.join(payload['formats'])}")
    print(f"  jobs incoming  {', '.join(payload['jobs']['incoming']) or '(none)'}")
    print(f"  renders        {len(payload['renders'])}")
    preferences = payload["preferences"]
    print(f"  preferences    {preferences['approved_count']} approved, "
          f"{preferences['proposed_count']} proposed")
    print(f"  experiments    {payload['experiments']['total']} recorded")
    print()
    return 0


def cmd_formats(args: argparse.Namespace) -> int:
    templates = load_templates()
    if args.json:
        print(json.dumps(templates, indent=2, default=str))
        return 0
    print()
    for name, template in templates.items():
        needs = template.get("requires") or {}
        print(f"  {name}")
        print(f"    {str(template.get('description', '')).strip().splitlines()[0]}")
        print(f"    layout {(template.get('layout') or {}).get('mode', 'full')}, "
              f"needs {needs.get('minimum_supporting_assets', 0)}-"
              f"{needs.get('maximum_supporting_assets', 0)} supporting clip(s)")
        print()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="process-job",
        description="Spotify mix -> TikTok production pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="process a job folder (default command)")
    run.add_argument("job", nargs="?", help="job id, job folder path, or 'newest'")
    run.add_argument("--format", help="force a format family")
    run.add_argument("--dry-run", action="store_true", help="plan only, do not render")
    run.add_argument("--no-preview", action="store_true")
    run.add_argument("--ignore-feedback", action="store_true",
                     help="plan from scratch, ignoring recorded feedback")
    run.add_argument("--keep-in-place", action="store_true",
                     help="do not move the job folder between lifecycle states")
    run.add_argument("--json", action="store_true")
    run.set_defaults(func=cmd_run)

    revise = subparsers.add_parser("revise", help="record feedback and re-render")
    revise.add_argument("job")
    revise.add_argument("feedback", help="what to change, in plain language")
    revise.add_argument("--json", action="store_true")
    revise.set_defaults(func=cmd_revise)

    new = subparsers.add_parser("new", help="create a job folder")
    new.add_argument("job_id")
    new.add_argument("--recording", help="Spotify screen recording to copy in")
    new.add_argument("--asset", action="append", help="supporting clip to copy in")
    new.set_defaults(func=cmd_new)

    inspect = subparsers.add_parser("inspect", help="inspect inputs without rendering")
    inspect.add_argument("job")
    inspect.add_argument("--skip-beats", action="store_true")
    inspect.add_argument("--json", action="store_true")
    inspect.set_defaults(func=cmd_inspect)

    approve = subparsers.add_parser("approve", help="approve a reviewed job")
    approve.add_argument("job")
    approve.set_defaults(func=cmd_approve)

    deliver = subparsers.add_parser(
        "deliver", help="stage a render where it can be downloaded on a phone"
    )
    deliver.add_argument("video_id", help="e.g. job-001-r2")
    deliver.add_argument("--json", action="store_true")
    deliver.set_defaults(func=cmd_deliver)

    copy_parser = subparsers.add_parser("copy", help="the CTA/caption testing bank")
    copy_subs = copy_parser.add_subparsers(dest="copy_command", required=True)
    copy_list = copy_subs.add_parser("list", help="show bank entries and statuses")
    copy_list.add_argument("--section", choices=copybank.SECTIONS)
    copy_list.add_argument("--status", choices=copybank.STATUSES)
    copy_list.add_argument("--json", action="store_true")
    for verb, description in (
        ("approve", "draft -> testing: allow the entry into rotation"),
        ("promote", "testing -> proven: mark repeatedly strong wording"),
        ("retire", "pull an entry from rotation, keeping the record"),
    ):
        sub = copy_subs.add_parser(verb, help=description)
        sub.add_argument("entry_id")
        sub.add_argument("--note", default="", help="why, recorded on the entry")
    copy_parser.set_defaults(func=cmd_copy)

    dropbox_parser = subparsers.add_parser(
        "dropbox", help="phone file channel: pull mixes in, push renders out"
    )
    dropbox_subs = dropbox_parser.add_subparsers(dest="dropbox_command", required=True)
    dropbox_status = dropbox_subs.add_parser("status", help="is the channel configured?")
    dropbox_status.add_argument("--json", action="store_true")
    dropbox_pull = dropbox_subs.add_parser(
        "pull", help="import new recordings from <base>/incoming into job folders"
    )
    dropbox_pull.add_argument("--run", action="store_true",
                              help="process each imported job and push its render back")
    dropbox_pull.add_argument("--json", action="store_true")
    dropbox_push = dropbox_subs.add_parser(
        "push", help="upload a render to <base>/renders/<video-id>/ with share links"
    )
    dropbox_push.add_argument("video_id", help="e.g. job-001-r2")
    dropbox_push.add_argument("--json", action="store_true")
    dropbox_parser.set_defaults(func=cmd_dropbox)

    status = subparsers.add_parser("status", help="environment and pipeline state")
    status.add_argument("--json", action="store_true")
    status.set_defaults(func=cmd_status)

    formats = subparsers.add_parser("formats", help="list format families")
    formats.add_argument("--json", action="store_true")
    formats.set_defaults(func=cmd_formats)

    preferences = subparsers.add_parser("prefs", help="creator preferences")
    preference_subs = preferences.add_subparsers(dest="prefs_command", required=True)
    preference_subs.add_parser("list")
    approve_pref = preference_subs.add_parser("approve")
    approve_pref.add_argument("preference_id")
    propose_pref = preference_subs.add_parser("propose")
    propose_pref.add_argument("key")
    propose_pref.add_argument("value")
    propose_pref.add_argument("statement")
    propose_pref.add_argument("--scope", default="global")
    propose_pref.add_argument("--scope-value", default="")
    preferences.set_defaults(func=cmd_prefs)

    analytics_parser = subparsers.add_parser("analytics", help="TikTok results")
    analytics_subs = analytics_parser.add_subparsers(dest="analytics_command", required=True)
    record = analytics_subs.add_parser("record")
    record.add_argument("video_id")
    record.add_argument("--field", action="append",
                        help="key=value, repeatable (views=1200, format_family=curiosity)")
    analytics_subs.add_parser("report")
    analytics_parser.set_defaults(func=cmd_analytics)

    experiments_parser = subparsers.add_parser("experiments", help="experiment records")
    experiment_subs = experiments_parser.add_subparsers(
        dest="experiments_command", required=True
    )
    experiment_subs.add_parser("list")
    results = experiment_subs.add_parser("results")
    results.add_argument("experiment_id")
    results.add_argument("--metric", action="append", help="key=value, repeatable")
    results.add_argument("--interpretation", default="")
    experiments_parser.set_defaults(func=cmd_experiments)

    research_parser = subparsers.add_parser("research", help="artist and track notes")
    research_subs = research_parser.add_subparsers(dest="research_command", required=True)
    add = research_subs.add_parser("add")
    add.add_argument("--subject", required=True)
    add.add_argument("--kind", required=True)
    add.add_argument("--summary", required=True)
    add.add_argument("--url", required=True)
    add.add_argument("--published", required=True, help="YYYY-MM-DD")
    add.add_argument("--source")
    add.add_argument("--event")
    add.add_argument("--caption-angle")
    add.add_argument("--hook-angle")
    brief = research_subs.add_parser("brief")
    brief.add_argument("subject", nargs="+")
    research_parser.set_defaults(func=cmd_research)

    feedback_parser = subparsers.add_parser("feedback", help="feedback records")
    feedback_subs = feedback_parser.add_subparsers(dest="feedback_command", required=True)
    listing = feedback_subs.add_parser("list")
    listing.add_argument("job")
    interpret = feedback_subs.add_parser("interpret")
    interpret.add_argument("job")
    interpret.add_argument("text")
    feedback_parser.set_defaults(func=cmd_feedback)

    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    known = {
        "run", "revise", "new", "inspect", "approve", "status", "formats",
        "prefs", "analytics", "experiments", "research", "feedback", "deliver",
        "copy", "dropbox",
        "-h", "--help",
    }
    # `./process-job jobs/incoming/job-001` is the documented shorthand for `run`.
    if argv and argv[0] not in known:
        argv.insert(0, "run")
    if not argv:
        argv = ["run"]

    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1

    try:
        return int(args.func(args))
    except (
        JobError, orchestrator.PipelineError, MediaError,
        copybank.CopyBankError, dropbox_sync.DropboxError,
    ) as exc:
        print(f"\n  {_colour('error', RED)} {exc}\n", file=sys.stderr)
        return 1
    except FileNotFoundError as exc:
        print(f"\n  {_colour('error', RED)} {exc}\n", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n  interrupted", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
