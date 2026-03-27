#!/bin/bash
# mem0_search.sh — Search the Mem0 super brain
# Usage: mem0_search.sh "query" [top_k]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
source "${SCRIPT_DIR}/config/.env" 2>/dev/null || true

MEM0_API_KEY="${MEM0_API_KEY:-REDACTED_MEM0_KEY}"
MEM0_URL="https://api.mem0.ai/v1/memories/search/"
USER_ID="${MEM0_USER_ID:-anmol-super-brain}"

QUERY="${1:?Usage: mem0_search.sh \"query\" [top_k]}"
TOP_K="${2:-5}"

QUERY_ESCAPED=$(echo "$QUERY" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])")

curl -s --request POST \
  --url "$MEM0_URL" \
  --header "Authorization: Token $MEM0_API_KEY" \
  --header "Content-Type: application/json" \
  --data "{
    \"query\": \"$QUERY_ESCAPED\",
    \"user_id\": \"$USER_ID\",
    \"top_k\": $TOP_K
  }" | python3 -c "
import json, sys

data = json.load(sys.stdin)
results = data if isinstance(data, list) else data.get('results', [])

if not results:
    print('No results found.')
    sys.exit(0)

print(f'Found {len(results)} memories:\n')
for i, r in enumerate(results, 1):
    score = r.get('score', '?')
    cat = r.get('metadata', {}).get('category', '?')
    mem = r['memory']
    mid = r.get('id', '?')[:8]
    print(f'  {i}. [{cat}] (score: {score}) #{mid}')
    print(f'     {mem}')
    print()
"
