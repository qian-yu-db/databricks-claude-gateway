#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Get token from credential helper
TOKEN_JSON=$(cd "$PROJECT_DIR" && uv run python -m credential_helper)
TOKEN=$(echo "$TOKEN_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

# Read config for base URL
CONFIG_FILE="${CONFIG_FILE:-config.json}"
if [ -f "$PROJECT_DIR/$CONFIG_FILE" ]; then
    HOST=$(python3 -c "import json; c=json.load(open('$PROJECT_DIR/$CONFIG_FILE')); print(c['databricks_host'].rstrip('/'))")
    ENDPOINT=$(python3 -c "import json; c=json.load(open('$PROJECT_DIR/$CONFIG_FILE')); print(c['endpoint_name'])")
    MODEL=$(python3 -c "import json; c=json.load(open('$PROJECT_DIR/$CONFIG_FILE')); print(c['model'])")
else
    echo "Error: config.json not found" >&2
    exit 1
fi

export ANTHROPIC_BASE_URL="${HOST}/serving-endpoints/${ENDPOINT}/invocations"
export ANTHROPIC_AUTH_TOKEN="$TOKEN"
export ANTHROPIC_MODEL="$MODEL"

exec claude "$@"
