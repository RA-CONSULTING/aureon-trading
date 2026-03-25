#!/bin/bash
# 🌌👑💭⚡ START AUREON UNIFIED MASTER HUB
# ALL SYSTEMS IN ONE PLACE

echo "🌌 Starting AUREON UNIFIED MASTER HUB..."
echo "═══════════════════════════════════════════════════════════════════════════"

if [ "$1" == "--bg" ]; then
    echo "📡 Starting in background mode..."
    nohup python aureon_unified_master_hub.py > unified_master_hub.log 2>&1 &
    echo "✅ Started! Log: unified_master_hub.log"
    echo "🌐 Dashboard: http://localhost:13333"
else
    python aureon_unified_master_hub.py
fi
