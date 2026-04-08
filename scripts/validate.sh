#!/usr/bin/env bash
#
# Runs staged validation checks. Phase 0 mode validates local contracts only.
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "$REPO_ROOT"

MODE="${1:-}"
PYTHON_BIN=""

usage() {
    echo "Usage: ./scripts/validate.sh [--full]"
}

fail() {
    echo "Validation FAILED: $1"
    exit 1
}

pick_python() {
    if [[ -x "./.venv/bin/python" ]]; then
        PYTHON_BIN="./.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        fail "no Python interpreter found"
    fi
}

require_file() {
    local path="$1"
    [[ -f "$path" ]] || fail "missing required file: $path"
}

run_phase0_contract_checks() {
    local output_file

    echo "Running Phase 0 contract checks..."
    pick_python

    require_file "requirements.txt"
    require_file "Dockerfile"
    require_file "inference.py"
    require_file "app.py"
    require_file "scripts/run_local.sh"
    require_file "scripts/smoke_test.sh"

    "$PYTHON_BIN" - <<'PY'
from app import app

required_routes = {"/reset", "/step", "/state"}
present_routes = {route.path for route in app.routes}
missing = sorted(required_routes - present_routes)
if missing:
    raise SystemExit(f"Missing required API routes: {missing}")
PY

    output_file="$(mktemp)"
    trap 'rm -f "$output_file"' EXIT
    HF_TOKEN="" MODEL_NAME="" API_BASE_URL="" "$PYTHON_BIN" inference.py >"$output_file"

    "$PYTHON_BIN" - "$output_file" <<'PY'
import pathlib
import re
import sys

path = pathlib.Path(sys.argv[1])
lines = [line.rstrip("\n") for line in path.read_text().splitlines()]

if not lines:
    raise SystemExit("inference.py produced no stdout")
if sum(1 for line in lines if line.startswith("[START] ")) != 1:
    raise SystemExit("expected exactly one [START] line")
if sum(1 for line in lines if line.startswith("[END] ")) != 1:
    raise SystemExit("expected exactly one [END] line")
if lines[0].startswith("[START] ") is False:
    raise SystemExit("first line must be [START]")
if lines[-1].startswith("[END] ") is False:
    raise SystemExit("last line must be [END]")

step_lines = [line for line in lines[1:-1] if line.startswith("[STEP] ")]
if len(step_lines) != len(lines) - 2 or not step_lines:
    raise SystemExit("stdout must contain only single-line [STEP] records between [START] and [END]")

step_pattern = re.compile(
    r'^\[STEP\] step=\d+ action=\{"U_target":\d+\.\d{2},"F_target":\d+\.\d{2}\} '
    r'reward=-?\d+\.\d{2} done=(true|false) error=(null|.+)$'
)
for step_line in step_lines:
    if step_pattern.match(step_line) is None:
        raise SystemExit(f"invalid [STEP] format: {step_line}")
PY

    rm -f "$output_file"
    trap - EXIT
    echo "Phase 0 contract checks passed."
}

run_full_validation() {
    if [[ "${RUN_SMOKE:-1}" == "1" ]]; then
        echo "Running Smoke Tests via scripts/smoke_test.sh..."
        "$SCRIPT_DIR/smoke_test.sh" --start-server
    fi

    if ! grep -q "task_registry" tasks/registry.py || ! grep -q "grader_registry" graders/registry.py; then
        echo "Deferred: full openenv validation remains a later-phase check until task/grader registries are implemented."
        exit 2
    fi
    command -v openenv >/dev/null 2>&1 || fail "openenv CLI not found"
    echo "Running full openenv validation..."
    openenv validate
}

case "$MODE" in
    "")
        run_phase0_contract_checks
        ;;
    --full)
        run_phase0_contract_checks
        run_full_validation
        ;;
    *)
        usage
        exit 1
        ;;
esac
