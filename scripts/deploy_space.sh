#!/usr/bin/env bash

set -euo pipefail

if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <space_url>"
    echo "Example: $0 https://huggingface.co/spaces/your-username/your-space-name"
    exit 1
fi

SPACE_URL="$1"

if [[ -z "${HF_TOKEN:-}" ]]; then
    echo "Error: HF_TOKEN environment variable must be set for deployment."
    echo "Export it using: export HF_TOKEN=\"hf_...\""
    exit 1
fi

SPACE_URL="${SPACE_URL%/}"
AUTH_URL="$(echo "$SPACE_URL" | sed "s|https://|https://oauth2:${HF_TOKEN}@|")"

echo "Deploying to $SPACE_URL..."

# Add the Hugging Face remote, update it if it exists
git remote add hf "$AUTH_URL" 2>/dev/null || git remote set-url hf "$AUTH_URL"

# Push the current branch to the main branch of the space
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "Pushing local branch '$CURRENT_BRANCH' to Hugging Face 'main' branch..."
git push hf "$CURRENT_BRANCH:main" --force

echo "Deployment pushed successfully! It may take a few minutes for the space to build and become accessible."
