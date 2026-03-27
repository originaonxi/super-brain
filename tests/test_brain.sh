#!/bin/bash
# test_brain.sh — Validate super brain connectivity and retrieval quality
#
# Run: ./tests/test_brain.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SEARCH="${SCRIPT_DIR}/src/mem0_search.sh"
PUSH="${SCRIPT_DIR}/src/mem0_push.sh"
PASSED=0
FAILED=0

test_case() {
    local name="$1"
    local query="$2"
    local expected="$3"

    echo -n "  TEST: $name ... "

    RESULT=$($SEARCH "$query" 3 2>&1)

    if echo "$RESULT" | grep -qi "$expected"; then
        echo "PASS"
        PASSED=$((PASSED + 1))
    else
        echo "FAIL"
        echo "    Expected to find: $expected"
        echo "    Got: $(echo "$RESULT" | head -5)"
        FAILED=$((FAILED + 1))
    fi
}

echo "============================================"
echo "  SUPER BRAIN — Test Suite"
echo "============================================"
echo ""

echo "[Connectivity]"
test_case "API reachable" "test query" "Found"
echo ""

echo "[Project Retrieval]"
test_case "Find techm-intel" "techm-intel project" "techm"
test_case "Find nova-gtm" "nova GTM system" "nova"
test_case "Find frontier journey" "365 day research" "frontier"
test_case "Find email agents" "daily email agents cron" "cron"
echo ""

echo "[Cross-Project Relationships]"
test_case "Aonxi modules in techm" "techm-intel Aonxi modules" "router"
test_case "SimpleNursing projects" "SimpleNursing all projects" "simplenursing"
test_case "Research to production" "research feeds production" "frontier"
echo ""

echo "[Category Coverage]"
test_case "Agent category" "agent projects" "agent"
test_case "Research category" "research studies" "research"
test_case "GTM category" "GTM engines" "gtm"
echo ""

echo "============================================"
echo "  Results: $PASSED passed, $FAILED failed"
echo "============================================"

if [ $FAILED -gt 0 ]; then
    exit 1
fi
