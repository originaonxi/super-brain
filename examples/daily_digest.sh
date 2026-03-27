#!/bin/bash
# daily_digest.sh — Generate a daily brain digest
#
# Queries the super brain for a morning summary.
# Can be added to cron for automated daily briefings.
# Run: ./examples/daily_digest.sh

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SEARCH="${SCRIPT_DIR}/src/mem0_search.sh"

DAY_OF_WEEK=$(date +%A)
HOUR=$(date +%H)

echo "============================================"
echo "  SUPER BRAIN — Daily Digest"
echo "  $(date '+%A, %B %d, %Y %I:%M %p')"
echo "============================================"
echo ""

echo "--- Active Projects ---"
$SEARCH "What projects am I actively working on this week?" 5
echo ""

echo "--- Agent Health ---"
$SEARCH "What agents should be running today and their status?" 5
echo ""

echo "--- Research Progress ---"
$SEARCH "Latest research progress and next steps?" 3
echo ""

echo "--- Client Work ---"
$SEARCH "What client work needs attention?" 3
echo ""

if [ "$DAY_OF_WEEK" = "Monday" ]; then
    echo "--- Weekly Review ---"
    $SEARCH "What was accomplished last week across all projects?" 5
    echo ""
fi

echo "============================================"
echo "  Digest complete. Have a productive day."
echo "============================================"
