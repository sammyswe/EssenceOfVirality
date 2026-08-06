# Drop your Spotify mix screen recordings here

Supported formats: `.mp4`, `.mov`, `.mkv`, `.webm`  
Raw media is gitignored (see repo root `.gitignore`).

## Quick run (two videos)

```bash
# 1. Ensure OpenMontage clone is present (one-time)
git clone https://github.com/calesthio/OpenMontage.git integrations/openmontage/clone
cd integrations/openmontage/clone && git checkout $(grep -E '^[0-9a-f]{40}$' ../PINNED_REF | head -1)

# 2. Install OpenMontage deps (one-time; needs ffmpeg + Python 3.10+)
make -C integrations/openmontage/clone setup

# 3. Copy your captures here, then run
python3 integrations/openmontage/run_pipeline.py --input-dir integrations/openmontage/inputs/
```

Optional blend window (for transition-payoff checklists):

```bash
python3 integrations/openmontage/run_pipeline.py \
  --input-dir integrations/openmontage/inputs/ \
  --blend-start 14 --blend-end 19
```

Outputs land in `integrations/openmontage/outputs/<timestamp>/` — each video gets a
`tiktok_ready.mp4` plus skill checklists and a `video_production_manifest`.

Full guide: `docs/guides/openmontage-pipeline.md`
