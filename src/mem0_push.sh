#!/bin/bash
# mem0_push.sh — Push a memory to Mem0 super brain
# Usage: mem0_push.sh "memory content" [category]
# Or pipe: echo "memory content" | mem0_push.sh - [category]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${SCRIPT_DIR}/config/.env" 2>/dev/null || true

MEM0_API_KEY="${MEM0_API_KEY:-REDACTED_MEM0_KEY}"
MEM0_URL="https://api.mem0.ai/v1/memories/"
USER_ID="${MEM0_USER_ID:-anmol-super-brain}"

# Get content from arg or stdin
if [ "${1:-}" = "-" ] || [ -z "${1:-}" ]; then
    CONTENT=$(cat)
else
    CONTENT="$1"
fi

CATEGORY="${2:-auto}"

# Skip empty content
if [ -z "$CONTENT" ]; then
    echo "Error: No content provided."
    echo "Usage: mem0_push.sh \"memory content\" [category]"
    exit 1
fi

# Escape for JSON
CONTENT_ESCAPED=$(echo "$CONTENT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])")

RESPONSE=$(curl -s --request POST \
  --url "$MEM0_URL" \
  --header "Authorization: Token $MEM0_API_KEY" \
  --header "Content-Type: application/json" \
  --data "{
    \"messages\": [{\"role\": \"user\", \"content\": \"$CONTENT_ESCAPED\"}],
    \"user_id\": \"$USER_ID\",
    \"metadata\": {\"category\": \"$CATEGORY\", \"owner\": \"anmol\", \"source\": \"cli\"}
  }")

echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        for item in data:
            event = item.get('event', 'UNKNOWN')
            mem = item.get('data', {}).get('memory', item.get('message', ''))
            print(f'[{event}] {mem}')
    elif isinstance(data, dict):
        print(data.get('message', json.dumps(data)))
except:
    print('Pushed to super brain.')
"
