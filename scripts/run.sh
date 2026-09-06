#!/usr/bin/env bash
# Single-command entry point for the 3D localization benchmark.
#
# This script:
#   1. creates/reuses a local virtual environment and installs dependencies
#   2. runs the full test suite
#   3. validates the experiment configuration
#   4. runs the smoke benchmark, then the standard benchmark
#   5. writes all result tables and builds the Excel workbook
#   6. validates the generated outputs
#   7. prints the output locations
#
# It does not exec/replace the calling shell, so your interactive shell
# stays open after it finishes.
#
# Usage:
#   ./scripts/run.sh              # smoke + standard benchmark
#   ./scripts/run.sh --smoke-only # smoke benchmark only (fast)
#   ./scripts/run.sh --skip-tests # skip the pytest run (not recommended)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

SMOKE_ONLY=0
SKIP_TESTS=0
for arg in "$@"; do
  case "$arg" in
    --smoke-only) SMOKE_ONLY=1 ;;
    --skip-tests) SKIP_TESTS=1 ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: $0 [--smoke-only] [--skip-tests]" >&2
      exit 2
      ;;
  esac
done

echo "=== [1/7] Preparing runtime ==="
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="$PROJECT_ROOT/.venv"
if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtual environment at $VENV_DIR"
  "$PYTHON_BIN" -m venv "$VENV_DIR"
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

if [ "$SKIP_TESTS" -eq 0 ]; then
  echo ""
  echo "=== [2/7] Running the test suite ==="
  python -m pytest -q
else
  echo ""
  echo "=== [2/7] Skipping test suite (--skip-tests) ==="
fi

echo ""
echo "=== [3/7] Validating experiment configuration ==="
python -m locbench3d.cli validate-config examples/experiment_smoke.yaml
if [ "$SMOKE_ONLY" -eq 0 ]; then
  python -m locbench3d.cli validate-config examples/experiment_standard.yaml
fi

echo ""
echo "=== [4/7] Running the smoke benchmark ==="
python -m locbench3d.cli run-all --smoke --out output/smoke

if [ "$SMOKE_ONLY" -eq 0 ]; then
  echo ""
  echo "=== [5/7] Running the standard benchmark ==="
  python -m locbench3d.cli run-all --config examples/experiment_standard.yaml --out output/standard
else
  echo ""
  echo "=== [5/7] Skipping standard benchmark (--smoke-only) ==="
fi

echo ""
echo "=== [6/7] Result tables and workbook already validated by run-all ==="

echo ""
echo "=== [7/7] Output locations ==="
echo "  Smoke run tables:    $PROJECT_ROOT/output/smoke/tables/"
echo "  Smoke run workbook:  $PROJECT_ROOT/output/smoke/workbook.xlsx"
if [ "$SMOKE_ONLY" -eq 0 ]; then
  echo "  Standard run tables:   $PROJECT_ROOT/output/standard/tables/"
  echo "  Standard run workbook: $PROJECT_ROOT/output/standard/workbook.xlsx"
fi
echo ""
echo "Done. This shell is still yours."
echo "The virtual environment used here lives at $VENV_DIR."
echo "It was only activated inside this script's own subshell, not your"
echo "interactive shell; to use it directly, run: source .venv/bin/activate"
