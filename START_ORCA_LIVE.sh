#!/bin/bash
set -e

cd /workspaces/aureon-trading

echo ""
echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║              🔥🐙 ORCA KILL CYCLE - FULL LIVE AUTONOMOUS MODE 🐙🔥              ║"
echo "║                                                                                ║"
echo "║                   Capital Ready: £50 GBP + $130 USD                            ║"
echo "║                   Mode: 🔴 LIVE (REAL TRADES - NO SIMULATION)                  ║"
echo "║                   Autonomy: ✅ ACTIVATED                                        ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# ENVIRONMENT SETUP - FULL LIVE MODE
# ═════════════════════════════════════════════════════════════════════════════
export LIVE=1
export LIVE_MODE=true
export AUTONOMOUS_MODE=true
export DRY_RUN=0
export DRY_RUN_MODE=false

# Exchange settings - LIVE TRADING
export ALPACA_DRY_RUN=false
export ALPACA_PAPER=false
export KRAKEN_DRY_RUN=false
export BINANCE_DRY_RUN=false
export BINANCE_USE_TESTNET=false

# Deployment settings
export DEPLOY_SCOUTS_IMMEDIATELY=True
export ENABLE_FIRE_TRADER=true
export ENABLE_AVALANCHE_HARVESTER=true
export ENABLE_ETERNAL_MACHINE=true
export ENABLE_QUANTUM_FROG=true

# Queen settings - AGGRESSIVE MODE
export QUEEN_MIN_PROFIT_PCT=0.3
export AGGRESSIVE_MODE=true
export ORCA_MAX_POSITIONS=unlimited

# Logging
export AUREON_DEBUG_STARTUP=0

echo "✅ Environment Variables Set:"
echo "   LIVE=$LIVE"
echo "   ALPACA_DRY_RUN=$ALPACA_DRY_RUN"
echo "   KRAKEN_DRY_RUN=$KRAKEN_DRY_RUN"
echo "   BINANCE_DRY_RUN=$BINANCE_DRY_RUN"
echo ""

# ═════════════════════════════════════════════════════════════════════════════
# START ORCA IN FULL AUTONOMOUS MODE
# ═════════════════════════════════════════════════════════════════════════════
echo "🚀 Starting ORCA Kill Cycle..."
echo ""

/bin/python3 orca_complete_kill_cycle.py \
  --autonomous \
  0 \
  10.0 \
  0.5

