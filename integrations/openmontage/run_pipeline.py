#!/usr/bin/env python3
"""Deterministic TikTok export pipeline for Spotify mix screen recordings.

Uses OpenMontage tools from the pinned clone (ffmpeg path — no API keys required).
Domain skill checklists are written as YAML artifacts for agent/human review.

Usage:
  python3 integrations/openmontage/run_pipeline.py video1.mp4 [video2.mp4 ...]
  python3 integrations/openmontage/run_pipeline.py --input-dir integrations/openmontage/inputs/

Options:
  --blend-start SEC  Blend window start (for transition-payoff checklist)
  --blend-end SEC    Blend window end
  --trim-start SEC   Trim source from this timestamp
  --trim-end SEC     Trim source to this timestamp
  --output-dir DIR   Output root (default: integrations/openmontage/outputs/<run-id>/)
  --skip-materialise Skip materialise.sh (if already run)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore


REPO_ROOT = Path(__file__).resolve().parents[2]
ADAPTER = REPO_ROOT / "integrations" / "openmontage"
CLONE = Path(os.environ.get("OPENMONTAGE_CLONE_PATH", ADAPTER / "clone"))
PINNED = (ADAPTER / "PINNED_REF").read_text().splitlines()
PINNED_SHA = next((ln.strip() for ln in PINNED if len(ln.strip()) == 40), "")

PIPELINE_VERSION = "0.1.0"
DOMAIN_SKILLS = {
    "general_virality": [
        {"name": "analyse-first-frame", "version": "0.1.0"},
        {"name": "evaluate-hook-clarity", "version": "0.1.0"},
    ],
    "spotify_mix": [
        {"name": "preserve-spotify-mix-audio", "version": "0.1.0"},
        {"name": "evaluate-transition-payoff", "version": "0.1.0"},
    ],
}


def _ensure_yaml() -> None:
    if yaml is None:
        raise SystemExit("PyYAML required: pip install pyyaml")


def _read_pinned_ref() -> str:
    return PINNED_SHA


def _ensure_clone() -> None:
    if not (CLONE / "tools" / "video" / "video_compose.py").exists():
        raise SystemExit(
            f"OpenMontage clone missing at {CLONE}.\n"
            f"Run: git clone https://github.com/calesthio/OpenMontage.git {CLONE}\n"
            f"     cd {CLONE} && git checkout {_read_pinned_ref()}"
        )


def _add_clone_to_path() -> None:
    clone_str = str(CLONE.resolve())
    if clone_str not in sys.path:
        sys.path.insert(0, clone_str)


def materialise() -> None:
    script = ADAPTER / "materialise.sh"
    if not script.is_file():
        raise SystemExit(f"materialise.sh not found: {script}")
    subprocess.run(["bash", str(script)], check=True, cwd=str(REPO_ROOT))


def ffprobe_video(path: Path) -> dict[str, Any]:
    cmd = [
        "ffprobe", "-v", "quiet", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
    data = json.loads(proc.stdout)
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    audio = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fps_raw = video.get("r_frame_rate", "30/1")
    parts = fps_raw.split("/")
    fps = float(parts[0]) / float(parts[1]) if len(parts) == 2 else float(parts[0])
    return {
        "duration_seconds": float(fmt.get("duration", 0)),
        "resolution": f"{video.get('width', 0)}x{video.get('height', 0)}",
        "fps": round(fps, 3),
        "video_codec": video.get("codec_name", "unknown"),
        "audio_codec": audio.get("codec_name", ""),
        "audio_present": bool(audio),
        "file_size_bytes": int(fmt.get("size", 0)),
    }


def run_reframe(input_path: Path, output_path: Path) -> dict[str, Any]:
    _add_clone_to_path()
    from tools.video.auto_reframe import AutoReframe

    tool = AutoReframe()
    result = tool.execute({
        "input_path": str(input_path),
        "output_path": str(output_path),
        "target_aspect": "portrait",
        "target_width": 1080,
        "target_height": 1920,
    })
    if not result.success:
        raise RuntimeError(f"auto_reframe failed: {result.error}")
    return result.data or {}


def run_trim(input_path: Path, output_path: Path, start: float, end: float | None) -> Path:
    _add_clone_to_path()
    from tools.video.video_trimmer import VideoTrimmer

    payload: dict[str, Any] = {
        "operation": "cut",
        "input_path": str(input_path),
        "output_path": str(output_path),
        "start_seconds": start,
    }
    if end is not None:
        payload["end_seconds"] = end
    result = VideoTrimmer().execute(payload)
    if not result.success:
        raise RuntimeError(f"video_trimmer failed: {result.error}")
    return Path(result.data.get("output", output_path))


def run_encode_tiktok(input_path: Path, output_path: Path) -> dict[str, Any]:
    _add_clone_to_path()
    from tools.video.video_compose import VideoCompose

    probe = ffprobe_video(input_path)
    w, h = probe["resolution"].split("x")
    if w == "1080" and h == "1920":
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if input_path.resolve() != output_path.resolve():
            subprocess.run(
                ["ffmpeg", "-y", "-i", str(input_path), "-c", "copy", str(output_path)],
                check=True,
                capture_output=True,
            )
        return {"output": str(output_path), "skipped_encode": True}

    result = VideoCompose().execute({
        "operation": "encode",
        "input_path": str(input_path),
        "output_path": str(output_path),
        "profile": "tiktok",
    })
    if not result.success:
        raise RuntimeError(f"video_compose encode failed: {result.error}")
    return result.data or {}


def extract_first_frame(video_path: Path, frame_path: Path) -> None:
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video_path), "-vframes", "1", "-q:v", "2", str(frame_path)],
        check=True,
        capture_output=True,
    )


def build_audio_checklist(probe: dict[str, Any]) -> dict[str, Any]:
    """Structured output aligned with preserve-spotify-mix-audio contract."""
    faults: list[dict[str, str]] = []
    if not probe.get("audio_present"):
        faults.append({
            "type": "missing_audio",
            "where": "full",
            "class": "capture_fixable",
        })
    decision = "recapture" if faults else "no_action"
    return {
        "audio_audit": {
            "faults": faults,
            "decision": decision,
            "processing": [],
            "recapture_guidance": (
                "Re-record with screen capture including system audio; enable Do Not Disturb."
                if decision == "recapture" else ""
            ),
        },
        "skill": "preserve-spotify-mix-audio",
        "requires_human_review": decision != "no_action",
    }


def build_first_frame_checklist(probe: dict[str, Any]) -> dict[str, Any]:
    """Placeholder checklist — agent/creator completes after viewing frame still."""
    return {
        "first_frame_analysis": {
            "one_second_read": ["auto: review integrations/openmontage/outputs/.../first_frame.jpg"],
            "promise": {"communicated": None, "detail": "Review manually or with agent + analyse-first-frame skill"},
            "honest": {"value": None, "detail": ""},
            "legible": {
                "value": None,
                "detail": f"Source resolution {probe.get('resolution')} — verify Spotify UI at 9:16",
            },
            "fixes": [],
        },
        "skill": "analyse-first-frame",
        "requires_human_review": True,
    }


def build_payoff_checklist(
    duration: float,
    blend_start: float | None,
    blend_end: float | None,
) -> dict[str, Any]:
    starts_at_pct = None
    if blend_start is not None and duration > 0:
        starts_at_pct = round(100 * blend_start / duration, 1)
    judgement = ""
    if starts_at_pct is not None and starts_at_pct > 40:
        judgement = (
            f"Provisional: payoff starts at {starts_at_pct}% — early-skip risk if no anticipation "
            "(evaluate-transition-payoff heuristic; not proven)."
        )
    return {
        "payoff_evaluation": {
            "payoff": {
                "present": blend_start is not None,
                "window": f"{blend_start}-{blend_end}s" if blend_start is not None else "",
                "peak_confirmed": None,
            },
            "anticipation": {"present": None, "dead_time": []},
            "placement": {"starts_at_pct": starts_at_pct or 0, "judgement": judgement},
            "visibility": {"clear": None, "obstructions": []},
            "fixes": [],
        },
        "skill": "evaluate-transition-payoff",
        "requires_human_review": True,
    }


def write_manifest(
    out_dir: Path,
    video_id: str,
    source: Path,
    final_video: Path,
    probe: dict[str, Any],
    decisions: list[dict[str, str]],
) -> Path:
    _ensure_yaml()
    manifest = {
        "artifact_type": "video_production_manifest",
        "schema_maturity": "scaffold",
        "id": f"vpm-{video_id}",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "produced_by": "workflow:openmontage-pipeline",
        "video_id": video_id,
        "source_assets": [str(source.resolve())],
        "pipeline_version": PIPELINE_VERSION,
        "openmontage_version": _read_pinned_ref(),
        "duration_seconds": probe["duration_seconds"],
        "format": "9:16",
        "audience": "TikTok — anonymous Spotify mix niche",
        "content_series": "essence-of-virality",
        "general_virality_skills": DOMAIN_SKILLS["general_virality"],
        "spotify_mix_skills": DOMAIN_SKILLS["spotify_mix"],
        "editing_decisions": decisions,
        "audio": {
            "source": "original_screen_capture",
            "processing": [],
        },
        "visual": {
            "crop": "center_crop_portrait_1080x1920",
            "overlays": [],
            "motion": [],
        },
        "export": {
            "codec": "libx264",
            "resolution": "1080x1920",
            "frame_rate": 30,
        },
        "quality_reviews": ["auto_reframe", "tiktok_encode", "ffprobe"],
    }
    path = out_dir / f"{video_id}-video_production_manifest.yaml"
    path.write_text(yaml.dump(manifest, sort_keys=False, allow_unicode=True))
    return path


def process_one(
    source: Path,
    run_dir: Path,
    blend_start: float | None,
    blend_end: float | None,
    trim_start: float | None,
    trim_end: float | None,
) -> dict[str, Any]:
    source = source.resolve()
    if not source.is_file():
        raise FileNotFoundError(source)

    slug = source.stem.replace(" ", "-").lower()[:40]
    video_id = f"{slug}-{uuid.uuid4().hex[:8]}"
    out_dir = run_dir / video_id
    out_dir.mkdir(parents=True, exist_ok=True)

    working = source
    decisions: list[dict[str, str]] = []

    src_probe = ffprobe_video(source)
    (out_dir / "source_probe.json").write_text(json.dumps(src_probe, indent=2))

    audio_check = build_audio_checklist(src_probe)
    _ensure_yaml()
    (out_dir / "preserve-spotify-mix-audio.yaml").write_text(
        yaml.dump(audio_check, sort_keys=False)
    )
    if audio_check["audio_audit"]["decision"] == "recapture":
        return {
            "video_id": video_id,
            "status": "blocked",
            "reason": "missing or faulty audio — re-capture required",
            "output_dir": str(out_dir),
        }

    if trim_start is not None or trim_end is not None:
        trimmed = out_dir / "trimmed.mp4"
        working = run_trim(source, trimmed, trim_start or 0.0, trim_end)
        decisions.append({
            "decision": "trim_source",
            "rationale": f"trim {trim_start or 0}s to {trim_end or 'end'}",
        })

    reframed_path = out_dir / "reframed.mp4"
    reframe_data = run_reframe(working, reframed_path)
    decisions.append({
        "decision": "auto_reframe_portrait",
        "rationale": json.dumps(reframe_data),
    })

    final_path = out_dir / "tiktok_ready.mp4"
    encode_data = run_encode_tiktok(Path(reframe_data.get("output", reframed_path)), final_path)
    decisions.append({
        "decision": "encode_tiktok_profile",
        "rationale": json.dumps(encode_data),
    })

    final_probe = ffprobe_video(final_path)
    (out_dir / "export_probe.json").write_text(json.dumps(final_probe, indent=2))

    frame_path = out_dir / "first_frame.jpg"
    extract_first_frame(final_path, frame_path)

    first_frame = build_first_frame_checklist(final_probe)
    (out_dir / "analyse-first-frame.yaml").write_text(yaml.dump(first_frame, sort_keys=False))

    payoff = build_payoff_checklist(
        final_probe["duration_seconds"], blend_start, blend_end
    )
    (out_dir / "evaluate-transition-payoff.yaml").write_text(yaml.dump(payoff, sort_keys=False))

    manifest_path = write_manifest(out_dir, video_id, source, final_path, final_probe, decisions)

    ok = final_probe["resolution"] == "1080x1920"
    return {
        "video_id": video_id,
        "status": "ok" if ok else "resolution_mismatch",
        "tiktok_ready": str(final_path),
        "manifest": str(manifest_path),
        "output_dir": str(out_dir),
        "resolution": final_probe["resolution"],
        "duration_seconds": final_probe["duration_seconds"],
    }


def collect_inputs(args: argparse.Namespace) -> list[Path]:
    paths: list[Path] = []
    if args.input_dir:
        d = Path(args.input_dir)
        for ext in ("*.mp4", "*.mov", "*.mkv", "*.webm"):
            paths.extend(sorted(d.glob(ext)))
    paths.extend(Path(p) for p in args.inputs)
    # dedupe preserving order
    seen: set[str] = set()
    unique: list[Path] = []
    for p in paths:
        key = str(p.resolve())
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def main() -> int:
    parser = argparse.ArgumentParser(description="Spotify mix → TikTok pipeline")
    parser.add_argument("inputs", nargs="*", help="Screen recording file(s)")
    parser.add_argument("--input-dir", help="Directory of screen recordings")
    parser.add_argument("--blend-start", type=float, help="Blend window start (seconds)")
    parser.add_argument("--blend-end", type=float, help="Blend window end (seconds)")
    parser.add_argument("--trim-start", type=float, help="Trim in-point (seconds)")
    parser.add_argument("--trim-end", type=float, help="Trim out-point (seconds)")
    parser.add_argument("--output-dir", help="Output directory for this run")
    parser.add_argument("--skip-materialise", action="store_true")
    args = parser.parse_args()

    _ensure_yaml()
    _ensure_clone()

    if not args.skip_materialise:
        materialise()

    inputs = collect_inputs(args)
    if not inputs:
        print("No input videos. Drop files in integrations/openmontage/inputs/ or pass paths.", file=sys.stderr)
        return 1

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(args.output_dir) if args.output_dir else ADAPTER / "outputs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    for src in inputs:
        print(f"Processing {src} …")
        try:
            result = process_one(
                src, run_dir,
                args.blend_start, args.blend_end,
                args.trim_start, args.trim_end,
            )
            results.append(result)
            print(f"  → {result['status']}: {result.get('tiktok_ready', result.get('reason', ''))}")
        except Exception as exc:
            results.append({"source": str(src), "status": "error", "error": str(exc)})
            print(f"  → error: {exc}", file=sys.stderr)

    summary_path = run_dir / "run_summary.json"
    summary_path.write_text(json.dumps({"run_id": run_id, "results": results}, indent=2))
    print(f"\nRun summary: {summary_path}")

    failed = [r for r in results if r.get("status") not in ("ok",)]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
