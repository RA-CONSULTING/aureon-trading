#!/bin/bash
# 🦈 Orca Kill Cycle Startup Script
# Waits for command center to be healthy before starting trading

echo "🦈 Orca Kill Cycle starting up..."
echo "   Waiting 30 seconds for Command Center health check..."

# Wait for command center to be healthy
sleep 30

# Check if command center is healthy
for i in {1..10}; do
    if curl -sf http://localhost:8080/health > /dev/null 2>&1; then
        echo "✅ Command Center is healthy - starting Orca Kill Cycle"
        break
    fi
    echo "   Waiting for Command Center... (attempt $i/10)"
    sleep 5
done

# Display API key status
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "🔑 API KEY STATUS CHECK"
echo "═══════════════════════════════════════════════════════════════════"

# Alpaca
if [ -n "$ALPACA_API_KEY" ] && [ -n "$ALPACA_SECRET_KEY" ]; then
    echo "   🦙 Alpaca:     ✅ CONFIGURED"
else
    echo "   🦙 Alpaca:     ❌ MISSING (set ALPACA_API_KEY, ALPACA_SECRET_KEY)"
fi

# Kraken
if [ -n "$KRAKEN_API_KEY" ] && [ -n "$KRAKEN_API_SECRET" ]; then
    echo "   🐙 Kraken:     ✅ CONFIGURED"
else
    echo "   🐙 Kraken:     ❌ MISSING (set KRAKEN_API_KEY, KRAKEN_API_SECRET)"
fi

# Binance
if [ -n "$BINANCE_API_KEY" ] && [ -n "$BINANCE_API_SECRET" ]; then
    echo "   🟡 Binance:    ✅ CONFIGURED"
else
    echo "   🟡 Binance:    ❌ MISSING (set BINANCE_API_KEY, BINANCE_API_SECRET)"
fi

# Capital.com
if [ -n "$CAPITAL_API_KEY" ] && [ -n "$CAPITAL_IDENTIFIER" ] && [ -n "$CAPITAL_PASSWORD" ]; then
    echo "   💼 Capital:    ✅ CONFIGURED"
else
    echo "   💼 Capital:    ❌ MISSING (set CAPITAL_API_KEY, CAPITAL_IDENTIFIER, CAPITAL_PASSWORD)"
fi

echo "═══════════════════════════════════════════════════════════════════"
echo ""

# Start the Orca Kill Cycle with trading parameters
# Args: max_positions=3, amount_per_position=$1.00, target_pct=1.0%
echo "🦈🔪 LAUNCHING ORCA AUTONOMOUS TRADING 🔪🦈"
exec python -u orca_complete_kill_cycle.py --autonomous 3 1.0 1.0
