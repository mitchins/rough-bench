#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${0}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  cat <<'EOF'
Run the remaining router-backed Gemma benchmarks sequentially, starting after gemma_3_4b_router.

Environment overrides:
  PYTHON_BIN
  BENCHMARKS_DIR
  SUBJECTS_FILE
  RUNS_DIR
  JUDGE_MODE
  CACHE_MODE
EOF
  exit 0
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

subjects=(
  gemma_3_4b_router
  gemma_3_12b_router
  gemma_3_27b_router
  gemma_3n_e2b_router
  gemma_3n_e4b_router
  gemma_4_26b_a4b_router
)

cd "${REPO_ROOT}"

for subject in "${subjects[@]}"; do
  save_runs_dir="${RUNS_DIR}/${subject}_full_rule"
  printf '\n==> Running %s\n' "${subject}"
  "${PYTHON_BIN}" -m roughbench.cli compare \
    --benchmarks-dir "${BENCHMARKS_DIR}" \
    --subjects-file "${SUBJECTS_FILE}" \
    --subject "${subject}" \
    --save-runs-dir "${save_runs_dir}" \
    --judge-mode "${JUDGE_MODE}" \
    --cache="${CACHE_MODE}"
done
