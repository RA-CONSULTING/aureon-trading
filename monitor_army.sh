#!/bin/bash
# 🦆 Specialized Army Monitor

while true; do
    clear
    echo "🦆⚔️ SPECIALIZED TRADING ARMY STATUS ⚔️🦆"
    echo "========================================"
    echo ""
    
    BOTS=$(pgrep -f aureon_specialized | wc -l)
    echo "🤖 Active Bots: $BOTS/5"
    echo ""
    
    [ -f aureon_buyer1.log ] && echo "💰 BUYER 1:" && tail -2 aureon_buyer1.log | grep -E "(POSITION|ENTERING|Cycle)"
    echo ""
    [ -f aureon_buyer2.log ] && echo "💰 BUYER 2:" && tail -2 aureon_buyer2.log | grep -E "(POSITION|ENTERING|Cycle)"
    echo ""
    [ -f aureon_seller1.log ] && echo "💎 SELLER 1:" && tail -2 aureon_seller1.log | grep -E "(SOLD|EXIT|Cycle)"
    echo ""
    [ -f aureon_seller2.log ] && echo "💎 SELLER 2:" && tail -2 aureon_seller2.log | grep -E "(SOLD|EXIT|Cycle)"
    echo ""
    [ -f aureon_watcher.log ] && echo "👁️ WATCHER:" && tail -2 aureon_watcher.log | grep -E "(SCAN|Cycle)"
    
    sleep 5
done
