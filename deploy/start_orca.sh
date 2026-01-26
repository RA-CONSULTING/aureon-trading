#!/bin/bash
# 🦈 Orca Kill Cycle Startup Script
# Waits for command center to be healthy before starting trading

set -e

echo "🦈 Orca Kill Cycle starting up..."
echo "   Waiting 30 seconds for Command Center health check..."

# Wait for command center to be healthy
sleep 30

# Check if command center is healthy
for i in {1..10}; do
    if curl -sf http://localhost:8800/health > /dev/null 2>&1; then
        echo "✅ Command Center is healthy - starting Orca Kill Cycle"
        break
    fi
    echo "   Waiting for Command Center... (attempt $i/10)"
    sleep 5
done

# Start required background services (market cache + dashboards)
LOG_DIR=${AUREON_LOG_DIR:-/app/logs}
mkdir -p "$LOG_DIR"
mkdir -p ${AUREON_STATE_DIR:-/app/state}

start_bg() {
    local name="$1"
    local cmd="$2"
    local log_file="$LOG_DIR/${name}.log"
    if pgrep -f "$cmd" > /dev/null 2>&1; then
        echo "✅ $name already running"
        return
    fi
    echo "🚀 Starting $name..."
    nohup bash -lc "$cmd" > "$log_file" 2>&1 &
    sleep 1
    if pgrep -f "$cmd" > /dev/null 2>&1; then
        echo "✅ $name started (log: $log_file)"
    else
        echo "⚠️ $name failed to start (check $log_file)"
    fi
}

# Market data feeder (Binance WebSocket → unified cache)
python - <<'PY'
try:
    import websocket  # noqa: F401
    print("✅ websocket-client installed")
except Exception:
    print("⚠️ websocket-client not installed - Binance WS cache may fail")
PY
start_bg "unified_market_cache" "python -u unified_market_cache.py --write-interval 1.0"

# Wait briefly for unified cache to produce first file
for i in {1..10}; do
    if [ -f "${MARKET_CACHE_DIR:-ws_cache}/unified_prices.json" ]; then
        echo "✅ Unified market cache ready"
        break
    fi
    echo "   Waiting for unified market cache... (attempt $i/10)"
    sleep 2
done

# Power Station Dashboard (API + UI)
start_bg "queen_power_dashboard" "python -u queen_power_dashboard.py"

# Optional: Queen Web Dashboard (if used)
if [ "${START_QUEEN_WEB_DASHBOARD:-false}" = "true" ]; then
    start_bg "queen_web_dashboard" "python -u queen_web_dashboard.py"
fi

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

# Enforce exchange connectivity before trading
if [ "${AUREON_REQUIRE_ALL_EXCHANGES:-true}" = "true" ]; then
    echo "🧪 EXCHANGE CONNECTIVITY CHECK"
    for i in {1..10}; do
        python - <<'PY'
import os
import sys

errors = []

def require_env(keys, label):
    missing = [k for k in keys if not os.getenv(k)]
    if missing:
        errors.append(f"{label} missing env: {', '.join(missing)}")
        return False
    return True

def check_alpaca():
    if not require_env(["ALPACA_API_KEY", "ALPACA_SECRET_KEY"], "Alpaca"):
        return
    try:
        from alpaca_client import AlpacaClient
        client = AlpacaClient()
        # Alpaca uses get_account_balance(), not get_balance()
        balance = client.get_account_balance()
        if not balance:
            errors.append("Alpaca returned empty balance")
    except Exception as e:
        errors.append(f"Alpaca connectivity failed: {e}")

def check_kraken():
    if not require_env(["KRAKEN_API_KEY", "KRAKEN_API_SECRET"], "Kraken"):
        return
    try:
        from kraken_client import KrakenClient
        client = KrakenClient()
        balance = client.get_balance()
        if balance is None:
            errors.append("Kraken returned None balance")
    except Exception as e:
        errors.append(f"Kraken connectivity failed: {e}")

def check_binance():
    if not require_env(["BINANCE_API_KEY", "BINANCE_API_SECRET"], "Binance"):
        return
    try:
        from binance_client import BinanceClient
        client = BinanceClient()
        balance = client.get_balance()
        if balance is None:
            errors.append("Binance returned None balance")
    except Exception as e:
        errors.append(f"Binance connectivity failed: {e}")

def check_capital():
    if not require_env(["CAPITAL_API_KEY", "CAPITAL_IDENTIFIER", "CAPITAL_PASSWORD"], "Capital.com"):
        return
    try:
        from capital_client import CapitalClient
        client = CapitalClient()
        # Capital uses get_account_balance(), not get_balance()
        balance = client.get_account_balance()
        if not balance:
            errors.append("Capital.com returned empty balance")
    except Exception as e:
        errors.append(f"Capital.com connectivity failed: {e}")

check_alpaca()
check_kraken()
check_binance()
check_capital()

if errors:
    for err in errors:
        print(f"❌ {err}")
    sys.exit(1)

print("✅ All exchange connectivity checks passed")
PY
        CHECK_CODE=$?
        if [ $CHECK_CODE -eq 0 ]; then
            break
        fi
        echo "⚠️ Exchange check failed (attempt $i/10). Retrying in 10s..."
        sleep 10
        if [ $i -eq 10 ]; then
            echo "❌ Exchange connectivity checks failed - blocking trading"
            exit 1
        fi
    done
    echo ""
fi

# Create state directory
mkdir -p ${AUREON_STATE_DIR:-/app/state}

# Write initial state so dashboard shows something
echo '{"timestamp": 0, "session_stats": {"cycles": 0}, "positions": [], "queen_message": "Orca starting..."}' > ${AUREON_STATE_DIR:-/app/state}/dashboard_snapshot.json

# Start the Orca Kill Cycle with trading parameters
# Args: max_positions=3, amount_per_position=$1.00, target_pct=1.0%
echo "🦈🔪 LAUNCHING ORCA AUTONOMOUS TRADING 🔪🦈"
echo "   Max positions: 3"
echo "   Amount per position: \$1.00"
echo "   Target profit: 1.0%"
echo ""

# Run with error handling - restart on crash
while true; do
    echo "$(date): Starting Orca autonomous mode..."
    
    # 🔍 Auto-detect Environment
    if [ -f "/root/aureon-trading/venv/bin/python" ]; then
        # Droplet / VM with venv
        PYTHON_CMD="/root/aureon-trading/venv/bin/python"
    elif [ -f "/app/venv/bin/python" ]; then
        # Deployment with custom venv
        PYTHON_CMD="/app/venv/bin/python"
    else
        # Docker / System default
        PYTHON_CMD="python"
    fi
    
    echo "   Using Python: $PYTHON_CMD"
    $PYTHON_CMD -u orca_complete_kill_cycle.py --autonomous 3 1.0 1.0
    EXIT_CODE=$?
    echo "$(date): Orca exited with code $EXIT_CODE"
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "Orca completed normally, restarting in 10 seconds..."
    else
        echo "⚠️ Orca crashed! Restarting in 30 seconds..."
        # Write error state
        echo "{\"timestamp\": $(date +%s), \"session_stats\": {\"cycles\": 0}, \"positions\": [], \"queen_message\": \"Orca crashed - restarting...\"}" > ${AUREON_STATE_DIR:-/app/state}/dashboard_snapshot.json
        sleep 20
    fi
    sleep 10
done
