#!/bin/bash
cd /workspaces/aureon-trading

echo "╔════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                ║"
echo "║                  🔥 STARTING LIVE TRADING MODE 🔥                              ║"
echo "║                     Your £50 GBP will START TRADING                            ║"
echo "║                                                                                ║"
echo "╚════════════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "✅ Environment Setup:"
echo "   • LIVE MODE: YES"
echo "   • Kraken GBP Capital: £50.0058"
echo "   • DRY RUN: OFF (REAL TRADES)"
echo "   • Status: READY TO FIRE 🔥"
echo ""

export LIVE=1
export ALPACA_DRY_RUN=false
export KRAKEN_DRY_RUN=false
export BINANCE_DRY_RUN=false
export ALPACA_ONLY=false

/bin/python3 micro_profit_labyrinth.py --live --yes --multi-exchange
