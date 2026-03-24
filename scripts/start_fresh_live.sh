#!/bin/bash
# 🚀 START FRESH LIVE TRADING
# Resets circuit breaker and begins with clean slate

echo "🌌 AUREON UNIFIED ECOSYSTEM - FRESH START"
echo "==========================================="
echo ""
echo "This will:"
echo "  ✅ Reset circuit breaker (drawdown counter)"
echo "  ✅ Import existing holdings as managed positions"
echo "  ✅ Start with all JSON feeds integrated"
echo "  ✅ Begin live trading on all exchanges"
echo ""

cd /workspaces/aureon-trading
FRESH_START=1 LIVE=1 python aureon_unified_ecosystem.py
