#!/bin/bash
# Quick status check for specialized bots
echo "🦆⚔️ BOT ARMY STATUS ⚔️🦆"
echo ""
echo "Running bots:"
ps aux | grep -E "python.*aureon" | grep -v grep | awk '{print $2, $NF}' || echo "None"
echo ""
echo "Log files:"
ls -lh buyer*.log seller*.log watcher*.log 2>/dev/null | awk '{print $9, $5}' || echo "Not created yet"
echo ""
echo "Recent activity (last 5 lines each):"
for log in buyer1.log buyer2.log seller1.log seller2.log watcher.log; do
    if [ -f "$log" ]; then
        echo "=== $log ==="
        tail -5 "$log" | grep -E "(💰|💎|👁️|ENTERING|SOLD|Profit|Trades)" || echo "  Initializing..."
    fi
done
