#!/bin/bash
#
# A simple smoke test to verify that the API server is running and responsive.
#

BASE_URL="http://localhost:8000"

echo "--- Running Smoke Test ---"

# Test 1: Check root endpoint
echo "Testing root endpoint..."
curl -s -o /dev/null -w "%{http_code}" $BASE_URL/
if [ $? -ne 0 ]; then
    echo "Root endpoint test FAILED. Is the server running?"
    exit 1
fi
echo " - OK"


# Test 2: Check /reset endpoint
echo "Testing /reset endpoint..."
RESET_RESPONSE=$(curl -s -X POST "$BASE_URL/reset" \
    -H "Content-Type: application/json" \
    -d '{"task_id": "task1", "episode_id": 0}')

if [[ "$RESET_RESPONSE" != *"observation"* ]]; then
    echo "/reset endpoint test FAILED. Response was: $RESET_RESPONSE"
    exit 1
fi
echo " - OK"


# Test 3: Check /step endpoint
echo "Testing /step endpoint..."
STEP_RESPONSE=$(curl -s -X POST "$BASE_URL/step" \
    -H "Content-Type: application/json" \
    -d '{"action": {"U_target": 0.5, "F_target": 0.5}}')

if [[ "$STEP_RESPONSE" != *"observation"* ]]; then
    echo "/step endpoint test FAILED. Response was: $STEP_RESPONSE"
    exit 1
fi
echo " - OK"

echo "--- Smoke Test Passed ---"