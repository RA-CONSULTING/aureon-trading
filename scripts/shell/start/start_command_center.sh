#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 👑 AUREON COMMAND CENTER - QUICK LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════
# 
# Launches the unified UI with all systems connected
#
# Usage:
#   ./start_command_center.sh          - Start Command Center UI
#   ./start_command_center.sh --bg     - Start in background
#   ./start_command_center.sh --trading - Start with live trading
#
# ═══════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "👑🌌 AUREON COMMAND CENTER LAUNCHER"
echo "═══════════════════════════════════════════════════════════════════════════"

# Check Python
if ! command -v python &> /dev/null; then
    echo "❌ Python not found!"
    exit 1
fi

# Parse arguments
BACKGROUND=false
TRADING=false

for arg in "$@"; do
    case $arg in
        --bg|--background)
            BACKGROUND=true
            ;;
        --trading|--live)
            TRADING=true
            ;;
    esac
done

# Start Command Center
echo ""
echo "🚀 Starting Aureon Command Center (Enhanced with Live Streaming)..."
echo ""

if [ "$BACKGROUND" = true ]; then
    nohup python aureon_command_center_enhanced.py > /tmp/aureon_command_center.log 2>&1 &
    PID=$!
    echo "✅ Command Center started in background (PID: $PID)"
    echo "📄 Log file: /tmp/aureon_command_center.log"
    echo ""
    echo "🌐 Dashboard: http://localhost:8800"
    echo "📡 WebSocket: ws://localhost:8800/ws (LIVE STREAMING)"
    echo ""
    echo "To stop: kill $PID"
else
    python aureon_command_center_enhanced.py
fi

# Optionally start trading system
if [ "$TRADING" = true ]; then
    echo ""
    echo "🤖 Starting MicroProfitLabyrinth trading system..."
    python micro_profit_labyrinth.py --live --yes &
fi
