#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.." || exit 1

SUBJECTS=(
  glm_5_1_zai
  glm_4_7_zai
  glm_4_5_air_zai
  glm_4_5_zai
  glm_4_5_flash_zai
  glm_4_6_zai
  glm_4_7_flash_zai
  glm_4_7_flashx_zai
  glm_5_turbo_zai
)

if [[ -z "${ZAI_API_KEY:-}" ]]; then
  echo "ZAI_API_KEY is not set; the coding plan endpoints require it." >&2
  exit 1
fi

for subject in "${SUBJECTS[@]}"; do
  echo "Running ${subject}..."
  ./.venv/bin/python -m roughbench.cli compare \
    --benchmarks-dir ./benchmarks \
    --subjects-file ./subjects/seed_subjects.yaml \
    --subject "${subject}" \
    --save-runs-dir "./runs/${subject}_full_rule" \
    --judge-mode rule \
    --cache resume
done
