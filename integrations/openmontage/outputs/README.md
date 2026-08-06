# Pipeline run outputs (gitignored run folders except this README).

Each run creates a timestamped subdirectory with:

- `<video-id>/tiktok_ready.mp4` — 1080×1920 export
- `<video-id>/*-video_production_manifest.yaml` — lineage artifact
- Skill checklist YAML files for human/agent review
- `run_summary.json` — batch status

These directories are local-only; do not commit raw exports.
