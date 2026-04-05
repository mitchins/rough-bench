#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${0}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Run all live Gemma models exposed by the local Google/GenAI router sequentially.

The script:
  1. queries the router /v1/models list
  2. filters live Gemma models
  3. validates that every live Gemma has a matching *_router subject config
  4. runs RoughBench compare for each subject with --cache=resume by default

Options:
  --list    Print the resolved Gemma subject ids and exit

Environment overrides:
  PYTHON_BIN
  BENCHMARKS_DIR
  SUBJECTS_FILE
  RUNS_DIR
  JUDGE_MODE
  CACHE_MODE
  ROUTER_BASE_URL
EOF
  exit 0
fi

LIST_ONLY=0
if [[ "${1:-}" == "--list" ]]; then
  LIST_ONLY=1
  shift
fi

if [[ "$#" -gt 0 ]]; then
  echo "Unexpected positional arguments. Use --help for usage." >&2
  exit 2
fi

PYTHON_BIN="${PYTHON_BIN:-${REPO_ROOT}/.venv/bin/python}"
BENCHMARKS_DIR="${BENCHMARKS_DIR:-${REPO_ROOT}/benchmarks}"
SUBJECTS_FILE="${SUBJECTS_FILE:-${REPO_ROOT}/subjects/seed_subjects.yaml}"
RUNS_DIR="${RUNS_DIR:-${REPO_ROOT}/runs}"
JUDGE_MODE="${JUDGE_MODE:-rule}"
CACHE_MODE="${CACHE_MODE:-resume}"
ROUTER_BASE_URL="${ROUTER_BASE_URL:-http://192.168.1.26:8080/v1}"

cd "${REPO_ROOT}"

gemma_subjects_text="$("${PYTHON_BIN}" - "${SUBJECTS_FILE}" "${ROUTER_BASE_URL}" <<'PY'
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.request import urlopen

from roughbench.subjects import load_subjects


SPECIAL_SUBJECT_OVERRIDES = {
    "gemma-4-26b-a4b-it": "gemma_4_26b_a4b_compute_test",
}


def models_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    if base.endswith("/v1"):
        return f"{base}/models"
    return f"{base}/v1/models"


subjects_file = Path(sys.argv[1])
router_base_url = sys.argv[2].rstrip("/")

with urlopen(models_url(router_base_url), timeout=30) as response:
    payload = json.load(response)

live_gemma_models = []
for item in payload.get("data", []):
    root = str(item.get("root", "")).strip()
    model_id = str(item.get("id", "")).strip()
    candidate = root or model_id
    if candidate.startswith("gemma-"):
        live_gemma_models.append(candidate)

all_subjects = {subject.id: subject for subject in load_subjects(subjects_file)}
configured_router = {
    subject.model: subject.id
    for subject in all_subjects.values()
    if subject.id.endswith("_router") and subject.id.startswith("gemma_")
}

missing = []
for model in live_gemma_models:
    if model in SPECIAL_SUBJECT_OVERRIDES:
        if SPECIAL_SUBJECT_OVERRIDES[model] not in all_subjects:
            missing.append(model)
        continue
    if model not in configured_router:
        missing.append(model)
if missing:
    raise SystemExit(
        "Missing router subject config(s) for live Gemma model(s): "
        + ", ".join(missing)
    )

for model in live_gemma_models:
    if model in SPECIAL_SUBJECT_OVERRIDES:
        print(SPECIAL_SUBJECT_OVERRIDES[model])
    else:
        print(configured_router[model])
PY
)"

subjects=("${(@f)gemma_subjects_text}")

if (( ${#subjects[@]} == 0 )); then
  echo "No live Gemma models were found on ${ROUTER_BASE_URL}." >&2
  exit 1
fi

if (( LIST_ONLY )); then
  printf '%s\n' "${subjects[@]}"
  exit 0
fi

for subject in "${subjects[@]}"; do
  save_runs_dir="${RUNS_DIR}/${subject}_full_rule"
  printf '\n==> Running %s\n' "${subject}"
  cmd=(
    "${PYTHON_BIN}" -m roughbench.cli compare
    --benchmarks-dir "${BENCHMARKS_DIR}"
    --subjects-file "${SUBJECTS_FILE}"
    --subject "${subject}"
    --save-runs-dir "${save_runs_dir}"
    --judge-mode "${JUDGE_MODE}"
    --cache="${CACHE_MODE}"
  )
  if [[ "${subject}" == *_router ]]; then
    cmd+=(--base-url "${ROUTER_BASE_URL}")
  fi
  "${cmd[@]}"
done
