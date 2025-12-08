#!/bin/bash
# Check all system logs and recent activity

echo "=== CHECKING SYSTEM STATUS ==="
echo ""

echo "1. Last 50 lines of any .log files:"
find /workspaces/aureon-trading -name "*.log" -type f -exec echo "File: {}" \; -exec tail -50 {} \; 2>/dev/null

echo ""
echo "2. Checking if system is currently running:"
ps aux | grep -E "aureon_unified|aureon_live" | grep -v grep

echo ""
echo "3. Last modified Python files (possible crashes):"
find /workspaces/aureon-trading -name "*.py" -type f -mmin -60 -ls 2>/dev/null

echo ""
echo "4. Checking state file:"
if [ -f aureon_kraken_state.json ]; then
    echo "State file exists, contents:"
    cat aureon_kraken_state.json | python3 -m json.tool 2>/dev/null || cat aureon_kraken_state.json
else
    echo "❌ State file not found"
fi

echo ""
echo "5. Checking for error dumps:"
ls -lah core.* 2>/dev/null || echo "No core dumps found"

echo ""
echo "6. Recent terminal commands:"
history | tail -20

echo ""
echo "7. Environment check:"
echo "LIVE mode: ${LIVE:-not set}"
echo "DRY_RUN: ${DRY_RUN:-not set}"
echo "EXCHANGE: ${EXCHANGE:-not set}"
