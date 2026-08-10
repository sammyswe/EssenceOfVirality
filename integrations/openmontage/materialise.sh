#!/usr/bin/env bash
# Materialise essence-of-virality extensions into the pinned OpenMontage clone.
# Sync direction: this repo → clone only (ADR 0001, AGPL boundary).
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
ADAPTER="${ROOT}/integrations/openmontage"
CLONE="${OPENMONTAGE_CLONE_PATH:-${ADAPTER}/clone}"
PROJECT="${OPENMONTAGE_PROJECT_ID:-essence-of-virality}"
PINNED="$(grep -E '^[0-9a-f]{40}$' "${ADAPTER}/PINNED_REF" | head -1)"

if [[ ! -d "${CLONE}/.git" ]]; then
  echo "ERROR: OpenMontage clone not found at ${CLONE}" >&2
  echo "Clone with:" >&2
  echo "  git clone https://github.com/calesthio/OpenMontage.git ${CLONE}" >&2
  echo "  cd ${CLONE} && git checkout ${PINNED}" >&2
  exit 1
fi

CURRENT="$(git -C "${CLONE}" rev-parse HEAD 2>/dev/null || echo unknown)"
if [[ "${CURRENT}" != "${PINNED}" ]]; then
  echo "WARNING: clone at ${CURRENT:0:12}…, expected ${PINNED:0:12}… (PINNED_REF)" >&2
  echo "         Run: git -C ${CLONE} checkout ${PINNED}" >&2
fi

PROJ_DIR="${CLONE}/projects/${PROJECT}"
mkdir -p "${PROJ_DIR}/skills" "${PROJ_DIR}/scripts" "${PROJ_DIR}/artifacts" \
         "${PROJ_DIR}/assets/video" "${PROJ_DIR}/renders" "${PROJ_DIR}/exports"

# Project config + brief template
cp "${ADAPTER}/manifests/essence-of-virality.yaml" "${PROJ_DIR}/pipeline-config.yaml"
cp "${ADAPTER}/manifests/brief-template.json" "${PROJ_DIR}/artifacts/brief-template.json"

# Stage skills
for skill in "${ADAPTER}/stage-skills/"*.md; do
  cp "${skill}" "${PROJ_DIR}/skills/$(basename "${skill}")"
done

# Symlink domain skills from this repo (read-only reference for agents)
SKILL_LINK="${PROJ_DIR}/skills/_essence-of-virality-bank"
rm -rf "${SKILL_LINK}"
mkdir -p "${SKILL_LINK}"
for bank in general-virality spotify-mix-content; do
  ln -sf "${ROOT}/.cursor/skills/${bank}" "${SKILL_LINK}/${bank}"
done

# Style playbook
cp "${ADAPTER}/playbooks/spotify-mix-tiktok.yaml" "${CLONE}/styles/spotify-mix-tiktok.yaml"

# Runner script (deterministic path)
cp "${ADAPTER}/run_pipeline.py" "${PROJ_DIR}/scripts/run_pipeline.py"
chmod +x "${PROJ_DIR}/scripts/run_pipeline.py"

# Marker for OpenMontage backlot
if [[ ! -f "${PROJ_DIR}/project.json" ]]; then
  cat > "${PROJ_DIR}/project.json" <<EOF
{
  "project_id": "${PROJECT}",
  "title": "Essence of Virality — Spotify Mix",
  "pipeline_type": "screen-demo",
  "style_playbook": "spotify-mix-tiktok",
  "materialised_from": "essence-of-virality",
  "openmontage_pin": "${PINNED}"
}
EOF
fi

echo "Materialised ${PROJECT} → ${PROJ_DIR}"
echo "  Skills:     ${PROJ_DIR}/skills/"
echo "  Playbook:   ${CLONE}/styles/spotify-mix-tiktok.yaml"
echo "  Runner:     ${PROJ_DIR}/scripts/run_pipeline.py"
