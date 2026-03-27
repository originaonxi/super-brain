#!/bin/bash
# cross_project_query.sh — Demo: Cross-project relationship queries
#
# Shows how the super brain connects dots across completely separate repos.
# Run: ./examples/cross_project_query.sh

SEARCH="$(dirname "$0")/../src/mem0_search.sh"

echo "============================================"
echo "  SUPER BRAIN — Cross-Project Query Demo"
echo "============================================"
echo ""

echo "--- Query 1: Module Sharing ---"
echo "Q: What modules does techm-intel share with other Aonxi projects?"
echo ""
$SEARCH "What modules does techm-intel share with other Aonxi projects?" 5
echo ""

echo "--- Query 2: Client Coverage ---"
echo "Q: Everything related to SimpleNursing across all projects"
echo ""
$SEARCH "Everything related to SimpleNursing across all projects" 5
echo ""

echo "--- Query 3: Daily Operations ---"
echo "Q: What is the daily workflow and what agents run automatically?"
echo ""
$SEARCH "What is the daily workflow and what agents run automatically?" 5
echo ""

echo "--- Query 4: Research → Production ---"
echo "Q: How does research feed into production systems?"
echo ""
$SEARCH "How does research feed into production systems?" 5
echo ""

echo "--- Query 5: Hard Relational ---"
echo "Q: If aonxi-router breaks, what other projects are affected?"
echo ""
$SEARCH "If aonxi-router breaks what other projects are affected?" 5
echo ""

echo "============================================"
echo "  All queries completed. Brain is alive."
echo "============================================"
