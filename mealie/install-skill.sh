#!/bin/bash

# sync the virtual environment dependencies first
echo "Installing dependencies with uv sync..."
uv sync --no-dev
echo "Set execute permissions for bin/mealie..."
chmod +x bin/mealie
ENV_FILE="$HOME/.openclaw/.env"
 

if [ -f "$ENV_FILE" ]; then
    if grep -q '^MEALIE_URL=' "$ENV_FILE" && grep -q '^MEALIE_API_TOKEN=' "$ENV_FILE"; then
        echo "✓ found settings in $ENV_FILE"
        echo "MEALIE_URL=$(grep '^MEALIE_URL=' "$ENV_FILE" | cut -d'=' -f2-)"
        echo "MEALIE_API_TOKEN=$(grep '^MEALIE_API_TOKEN=' "$ENV_FILE" | cut -d'=' -f2-)"
    else
        echo "⚠ Warning: $ENV_FILE exists but is missing MEALIE_URL or MEALIE_API_TOKEN."
    fi
else
    echo "⚠ Warning: $ENV_FILE not found. Please set MEALIE_URL and MEALIE_API_TOKEN in it."
fi