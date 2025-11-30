#!/bin/bash
# Live bot monitoring dashboard
while true; do
    clear
    echo "🦆⚔️ AUREON TRADING ARMY - LIVE STATUS ⚔️🦆"
    echo "================================================"
    echo ""
    
    # Count running bots
    BOT_COUNT=$(ps aux | grep -E "python.*aureon_ultimate" | grep -v grep | wc -l)
    echo "🤖 Active Bots: $BOT_COUNT/5"
    echo ""
    
    # Show recent activity from each bot
    for i in 4 5 6 8 9; do
        if [ -f "aureon_key$i.log" ]; then
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "🔑 KEY $i - Last 3 lines:"
            tail -3 aureon_key$i.log 2>/dev/null | grep -E "(POSITION|ENTERING|SOLD|Profit|✅|🦆)" || echo "  Scanning..."
            echo ""
        fi
    done
    
    sleep 3
done
