#!/bin/bash
# mem0_hook.sh — Claude Code PostToolUse hook
# Auto-pushes meaningful actions to the super brain
# Configured in ~/.claude/settings.json under hooks.PostToolUse

set -euo pipefail

MEM0_API_KEY="${MEM0_API_KEY:?Error: MEM0_API_KEY not set. Source config/.env or export it.}"
MEM0_URL="https://api.mem0.ai/v1/memories/"
USER_ID="${MEM0_USER_ID:-anmol-super-brain}"

# Read hook input from stdin
INPUT=$(cat)

# Extract meaningful content
TOOL_INPUT=$(echo "$INPUT" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    tool = data.get('tool_name', '')
    inp = data.get('tool_input', {})
    out = str(data.get('tool_output', ''))[:500]

    if tool == 'Write':
        path = inp.get('file_path', 'unknown')
        print(f'Created/wrote file: {path}')
    elif tool == 'Edit':
        path = inp.get('file_path', 'unknown')
        print(f'Edited file: {path}')
    elif tool == 'Bash':
        cmd = inp.get('command', '')
        # Only track meaningful commands (git, npm, pip, docker, etc.)
        meaningful = ['git ', 'npm ', 'pip ', 'docker ', 'curl ', 'python', 'make', 'cargo']
        if any(cmd.startswith(m) or m in cmd for m in meaningful):
            print(f'Ran command: {cmd[:200]}. Result: {out[:200]}')
        else:
            print('')
    else:
        print('')
except:
    print('')
" 2>/dev/null)

# Skip empty or trivial
if [ -z "$TOOL_INPUT" ] || [ ${#TOOL_INPUT} -lt 20 ]; then
    exit 0
fi

# Push in background (non-blocking)
CONTENT_ESCAPED=$(echo "$TOOL_INPUT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read().strip())[1:-1])")

curl -s --request POST \
  --url "$MEM0_URL" \
  --header "Authorization: Token $MEM0_API_KEY" \
  --header "Content-Type: application/json" \
  --data "{
    \"messages\": [{\"role\": \"user\", \"content\": \"$CONTENT_ESCAPED\"}],
    \"user_id\": \"$USER_ID\",
    \"metadata\": {\"category\": \"live-session\", \"owner\": \"anmol\", \"source\": \"claude-code-hook\"}
  }" > /dev/null 2>&1 &

exit 0
