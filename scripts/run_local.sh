#!/usr/bin/env bash
#
# Builds the API server Docker image and runs it locally for endpoint smoke tests.
#

set -euo pipefail

IMAGE_NAME="${IMAGE_NAME:-thermal-plant-control:latest}"
PORT="${PORT:-7860}"

echo "Building API server image: $IMAGE_NAME..."
docker build -t "$IMAGE_NAME" .

echo "Starting local API server on http://localhost:${PORT} ..."
docker run --rm -p "${PORT}:7860" "$IMAGE_NAME"
