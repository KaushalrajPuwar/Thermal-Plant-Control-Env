#!/usr/bin/env bash
#
# A simple smoke test to verify that the API server is running and responsive.
#

set -euo pipefail

BASE_URL="${BASE_URL:-http://localhost:8000}"
PYTHON_BIN="${PYTHON_BIN:-}"

if [[ -z "$PYTHON_BIN" ]]; then
    if [[ -x "./.venv/bin/python" ]]; then
        PYTHON_BIN="./.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        PYTHON_BIN="python3"
    else
        echo "Smoke test FAILED. No Python interpreter available for JSON checks."
        exit 1
    fi
fi

RESPONSE_STATUS=""
RESPONSE_BODY=""

perform_request() {
    local method="$1"
    local path="$2"
    local payload="${3:-}"
    local response

    if [[ -n "$payload" ]]; then
        response="$(curl -sS -w $'\n%{http_code}' -X "$method" "$BASE_URL$path" \
            -H "Content-Type: application/json" \
            -d "$payload")"
    else
        response="$(curl -sS -w $'\n%{http_code}' -X "$method" "$BASE_URL$path")"
    fi

    RESPONSE_STATUS="${response##*$'\n'}"
    RESPONSE_BODY="${response%$'\n'*}"
}

assert_status() {
    local expected="$1"
    local label="$2"

    if [[ "$RESPONSE_STATUS" != "$expected" ]]; then
        echo "${label} FAILED. Expected HTTP ${expected}, got ${RESPONSE_STATUS}. Body: ${RESPONSE_BODY}"
        exit 1
    fi
}

assert_json_keys() {
    local label="$1"
    local body="$2"
    shift 2
    "$PYTHON_BIN" - "$label" "$body" "$@" <<'PY'
import json
import sys

label = sys.argv[1]
body = sys.argv[2]
expected_keys = sys.argv[3:]

try:
    payload = json.loads(body)
except json.JSONDecodeError as exc:
    raise SystemExit(f"{label} FAILED. Response was not valid JSON: {exc}: {body}")

missing = [key for key in expected_keys if key not in payload]
if missing:
    raise SystemExit(f"{label} FAILED. Missing keys {missing}. Body: {body}")
PY
}

echo "--- Running Smoke Test ---"

# Test 1: Check /reset endpoint
echo "Testing /reset endpoint..."
perform_request "POST" "/reset" '{"task_id": "task1", "episode_id": 0}'
assert_status "200" "/reset endpoint test"
assert_json_keys "/reset endpoint test" "$RESPONSE_BODY" "observation"
echo " - OK"


# Test 2: Check /step endpoint
echo "Testing /step endpoint..."
perform_request "POST" "/step" '{"action": {"U_target": 0.5, "F_target": 0.5}}'
assert_status "200" "/step endpoint test"
assert_json_keys "/step endpoint test" "$RESPONSE_BODY" "observation" "reward" "done" "info"
echo " - OK"


# Test 3: Check /state endpoint
echo "Testing /state endpoint..."
perform_request "GET" "/state"
assert_status "200" "/state endpoint test"
assert_json_keys "/state endpoint test" "$RESPONSE_BODY" "state"
echo " - OK"

echo "--- Smoke Test Passed ---"
