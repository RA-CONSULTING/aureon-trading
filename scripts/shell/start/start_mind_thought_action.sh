#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 🧠💭⚡ AUREON MIND → THOUGHT → ACTION HUB LAUNCHER
# ═══════════════════════════════════════════════════════════════════════════

cd "$(dirname "$0")"

echo "═══════════════════════════════════════════════════════════════════════════"
echo "🧠💭⚡ AUREON MIND → THOUGHT → ACTION HUB"
echo "═══════════════════════════════════════════════════════════════════════════"
echo ""
echo "COGNITIVE ARCHITECTURE:"
echo "  🧠 MIND:    Queen Hive + Intelligence Systems"
echo "  💭 THOUGHT: ThoughtBus Real-Time Streaming"
echo "  ⚡ ACTION:  Execution & Trading Monitoring"
echo ""

# Parse arguments
BACKGROUND=false

for arg in "$@"; do
    case $arg in
        --bg|--background)
            BACKGROUND=true
            ;;
    esac
done

if [ "$BACKGROUND" = true ]; then
    nohup python aureon_mind_thought_action_hub.py > /tmp/mind_thought_action.log 2>&1 &
    PID=$!
    echo "✅ Mind → Thought → Action Hub started (PID: $PID)"
    echo "📄 Log: /tmp/mind_thought_action.log"
    echo ""
    echo "🌐 Dashboard: http://localhost:13002"
    echo "📡 WebSocket: ws://localhost:13002/ws"
    echo ""
    echo "To stop: kill $PID"
else
    python aureon_mind_thought_action_hub.py
fi
