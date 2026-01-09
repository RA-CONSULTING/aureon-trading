#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# 🌍 GAIA CLOSED LOOP SUPERVISOR 🌍
# ═══════════════════════════════════════════════════════════════
# Auto-restarts the planetary reclaimer if it crashes
# Ensures 24/7 continuous operation toward $1 BILLION goal
# ═══════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

LOG_FILE="reclaimer.log"
TRADER_SCRIPT="gaia_planetary_reclaimer.py"
RESTART_DELAY=5
MAX_RESTARTS_PER_HOUR=10
RESTART_COUNT=0
HOUR_START=$(date +%s)

echo "═══════════════════════════════════════════════════════════════"
echo "🌍 GAIA CLOSED LOOP SUPERVISOR - ACTIVATED 🌍"
echo "═══════════════════════════════════════════════════════════════"
echo "Script: $TRADER_SCRIPT"
echo "Log: $LOG_FILE"
echo "Started: $(date)"
echo "═══════════════════════════════════════════════════════════════"

# Function to check if process is running
is_running() {
    pgrep -f "$TRADER_SCRIPT" > /dev/null 2>&1
}

# Function to kill existing instances
kill_existing() {
    pkill -9 -f "$TRADER_SCRIPT" 2>/dev/null
    sleep 1
}

# Function to start the trader
start_trader() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Starting $TRADER_SCRIPT..."
    python -u "$TRADER_SCRIPT" >> "$LOG_FILE" 2>&1 &
    TRADER_PID=$!
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Started with PID: $TRADER_PID"
}

# Reset restart counter every hour
check_restart_limit() {
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - HOUR_START))
    
    if [ $ELAPSED -ge 3600 ]; then
        HOUR_START=$CURRENT_TIME
        RESTART_COUNT=0
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📊 Hourly restart counter reset"
    fi
    
    if [ $RESTART_COUNT -ge $MAX_RESTARTS_PER_HOUR ]; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  Too many restarts ($RESTART_COUNT/hour). Waiting 10 minutes..."
        sleep 600
        RESTART_COUNT=0
    fi
}

# Main closed loop
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🔄 Entering closed loop..."

# Kill any existing instances first
kill_existing

while true; do
    if ! is_running; then
        check_restart_limit
        
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚡ Trader not running. Restarting..."
        start_trader
        RESTART_COUNT=$((RESTART_COUNT + 1))
        
        # Give it time to initialize
        sleep 10
        
        if is_running; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Trader successfully restarted (restart #$RESTART_COUNT this hour)"
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Failed to start trader. Retrying in $RESTART_DELAY seconds..."
        fi
    fi
    
    # Check every 30 seconds
    sleep 30
done
