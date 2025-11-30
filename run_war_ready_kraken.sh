#!/bin/bash
# 🚀 WAR-READY KRAKEN ECOSYSTEM - QUICK START GUIDE

set -e

echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║                                                               ║"
echo "║   🐙 AUREON KRAKEN ECOSYSTEM - WAR-READY EDITION 🐙          ║"
echo "║                                                               ║"
echo "║   Quick Start Guide                                           ║"
echo "║                                                               ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python3 found: $(python3 --version)"

# Check dependencies
echo ""
echo "📦 Checking dependencies..."
python3 -c "import websockets" 2>/dev/null && echo "  ✅ websockets" || echo "  ❌ websockets (run: pip install websockets)"
python3 -c "import kraken_client" 2>/dev/null && echo "  ✅ kraken_client" || echo "  ❌ kraken_client (check if file exists)"

# Check .env file
echo ""
echo "🔐 Checking Kraken API credentials..."
if [ -f ".env" ]; then
    if grep -q "KRAKEN_API_KEY" .env && grep -q "KRAKEN_API_SECRET" .env; then
        echo "  ✅ .env file found with Kraken credentials"
    else
        echo "  ⚠️  .env file exists but missing Kraken credentials"
    fi
else
    echo "  ❌ .env file not found"
    echo ""
    echo "Create .env file with:"
    echo "  KRAKEN_API_KEY=your_key_here"
    echo "  KRAKEN_API_SECRET=your_secret_here"
    exit 1
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🎯 AVAILABLE COMMANDS:"
echo ""
echo "1️⃣  Paper Trading (Default):"
echo "   python3 aureon_kraken_ecosystem.py"
echo ""
echo "2️⃣  Paper Trading - Higher Balance:"
echo "   BALANCE=5000 python3 aureon_kraken_ecosystem.py"
echo ""
echo "3️⃣  Paper Trading - Faster Cycles:"
echo "   INTERVAL=3 python3 aureon_kraken_ecosystem.py"
echo ""
echo "4️⃣  Live Trading (⚠️  CAUTION - REAL MONEY):"
echo "   LIVE=1 BALANCE=500 python3 aureon_kraken_ecosystem.py"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🛡️  WAR-READY FEATURES ENABLED:"
echo ""
echo "  ✅ Kelly Criterion Position Sizing (Half-Kelly)"
echo "  ✅ Circuit Breaker (15% Max Drawdown)"
echo "  ✅ Per-Symbol Exposure Limits (30% cap)"
echo "  ✅ Mycelium Network Enhancement"
echo "  ✅ State Persistence & Recovery"
echo "  ✅ Coherence-Based Position Scaling"
echo "  ✅ WebSocket Health Monitoring"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📊 KEY CONFIG PARAMETERS:"
echo ""
echo "  • Take Profit:      +2.0%"
echo "  • Stop Loss:        -0.8%"
echo "  • Base Position:    10% (Kelly-adjusted)"
echo "  • Max Position:     25% hard cap"
echo "  • Max Drawdown:     15% (circuit breaker)"
echo "  • Max Positions:    6 concurrent"
echo "  • Entry Coherence:  Γ > 0.50"
echo "  • Network Pause:    Γ < 0.40"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Ask user what they want to do
read -p "🚀 Ready to start? [Paper/Live/Cancel] (P/L/C): " choice

case "$choice" in
    p|P|paper|Paper|"")
        echo ""
        echo "▶️  Starting PAPER TRADING mode..."
        echo "   (No real money at risk)"
        sleep 2
        python3 aureon_kraken_ecosystem.py
        ;;
    l|L|live|Live)
        echo ""
        echo "⚠️  ⚠️  ⚠️  WARNING ⚠️  ⚠️  ⚠️"
        echo ""
        echo "You are about to start LIVE TRADING with REAL MONEY."
        echo ""
        read -p "Enter starting balance (e.g., 500): " balance
        
        if [ -z "$balance" ]; then
            echo "❌ No balance provided. Exiting."
            exit 1
        fi
        
        echo ""
        echo "📋 LIVE TRADING CHECKLIST:"
        echo "  [ ] I have tested in paper mode for 24+ hours"
        echo "  [ ] I understand the risks"
        echo "  [ ] I am ready to lose up to $balance"
        echo "  [ ] Circuit breaker is set to 15% max drawdown"
        echo ""
        read -p "Type 'YES I AM READY' to confirm: " confirm
        
        if [ "$confirm" = "YES I AM READY" ]; then
            echo ""
            echo "▶️  Starting LIVE TRADING with $${balance}..."
            sleep 3
            LIVE=1 BALANCE=$balance python3 aureon_kraken_ecosystem.py
        else
            echo ""
            echo "❌ Confirmation not received. Exiting for safety."
            exit 1
        fi
        ;;
    c|C|cancel|Cancel)
        echo ""
        echo "👋 Cancelled. Come back when ready!"
        exit 0
        ;;
    *)
        echo ""
        echo "❌ Invalid choice. Exiting."
        exit 1
        ;;
esac
