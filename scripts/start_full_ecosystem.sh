#!/bin/bash
# 🚀 AUREON FULL ECOSYSTEM LAUNCHER
# Runs: Piano Brain + Unified Ecosystem + Miner (all together)

set -e

cd /workspaces/aureon-trading

# Load environment variables
source .env 2>/dev/null || true

echo "╔════════════════════════════════════════════════════════════════════════╗"
echo "║                   🐙 AUREON FULL ECOSYSTEM 🐙                          ║"
echo "║                                                                        ║"
echo "║  Components:                                                           ║"
echo "║  1️⃣  Piano Brain (Quantum signal generation)                           ║"
echo "║  2️⃣  Unified Ecosystem (Trading orchestration)                         ║"
echo "║  3️⃣  Miner (Background BTC mining with LuminaCell)                     ║"
echo "║                                                                        ║"
echo "║  All three communicate for optimal trading + mining harmony            ║"
echo "╚════════════════════════════════════════════════════════════════════════╝"
echo ""

# Kill any existing processes
echo "🔴 Cleaning up existing processes..."
pkill -f "aureon_piano.py" 2>/dev/null || true
pkill -f "aureon_unified_ecosystem.py" 2>/dev/null || true
pkill -f "aureon_miner.py" 2>/dev/null || true
sleep 1

# Start Quantum Miner Brain (writes quantum state)
echo "🧠 Starting Quantum Miner Brain..."
nohup python3 aureon_miner.py > miner_output.log 2>&1 &
MINER_PID=$!
echo "   ✅ Quantum Miner Brain running (PID: $MINER_PID)"
sleep 5

# Verify Brain is writing state
if [ -f /tmp/aureon_multidimensional_brain_output.json ]; then
    echo "   ✅ Brain state file detected: /tmp/aureon_multidimensional_brain_output.json"
else
    echo "   ⚠️  Brain state file not yet created (will appear shortly)"
fi

echo ""
echo "⛏️  Starting Unified Ecosystem..."

# Configuration
export BINANCE_USE_TESTNET=false
export BINANCE_DRY_RUN=false
export EXCHANGE=binance
export ENABLE_MINING=1

if [ -z "$MINING_WORKER" ]; then
    echo "   ⚠️  MINING_WORKER not set! Mining disabled."
    echo "   Set MINING_WORKER in .env file"
else
    echo "   ✅ Mining Worker: $MINING_WORKER"
    echo "   ✅ Mining Platform: ${MINING_PLATFORM:-binance}"
    echo "   ✅ Mining Threads: ${MINING_THREADS:-2}"
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════"
echo "🚀 STARTING ECOSYSTEM..."
echo "════════════════════════════════════════════════════════════════════════"
echo ""
echo "   🧠 Quantum Brain: Generating quantum signals → /tmp/aureon_multidimensional_brain_output.json"
echo "   🐙 Ecosystem: Reading Brain state + deploying scouts + managing positions"
echo "   ⛏️  Miner: Running LuminaCell quantum laser mining to $MINING_WORKER"
echo ""
echo "   Press Ctrl+C to stop all components"
echo ""

# Start Unified Ecosystem (foreground so we can Ctrl+C)
python3 aureon_unified_ecosystem.py

# Cleanup on exit
echo ""
echo "🛑 Shutting down ecosystem..."
kill $MINER_PID 2>/dev/null || true
pkill -f "aureon_miner.py" 2>/dev/null || true
echo "✅ Cleaned up"
