#!/bin/bash
#
# 🚀 AUREON STARTUP SCRIPT 🚀
# ═══════════════════════════════════════════════════════════════════════════════
#
# This script starts the Aureon trading system with automatic restart capability.
# It runs the watchdog which monitors and auto-restarts the main trading system.
#
# USAGE:
#     ./start_aureon.sh              # Start unified ecosystem with watchdog
#     ./start_aureon.sh kraken       # Start kraken ecosystem with watchdog
#     ./start_aureon.sh --no-watchdog # Start without watchdog (manual mode)
#
# The watchdog will:
#   1. Start the trading system
#   2. Monitor for crashes/hangs
#   3. Auto-restart if needed
#   4. Emergency harvest profits before restart
#
# Gary Leckey | December 2025
# "When the system falls, the watchdog rises."
# ═══════════════════════════════════════════════════════════════════════════════

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo "   🚀 AUREON TRADING SYSTEM STARTUP 🚀"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Parse arguments
TARGET="unified"
USE_WATCHDOG=true

for arg in "$@"; do
    case $arg in
        kraken)
            TARGET="kraken"
            ;;
        unified)
            TARGET="unified"
            ;;
        --no-watchdog)
            USE_WATCHDOG=false
            ;;
        --help|-h)
            echo "Usage: $0 [unified|kraken] [--no-watchdog]"
            echo ""
            echo "Options:"
            echo "  unified       Start aureon_unified_ecosystem.py (default)"
            echo "  kraken        Start aureon_kraken_ecosystem.py"
            echo "  --no-watchdog Start without the watchdog (manual mode)"
            echo ""
            exit 0
            ;;
    esac
done

# Determine script to run
if [ "$TARGET" == "kraken" ]; then
    SCRIPT="aureon_kraken_ecosystem.py"
else
    SCRIPT="aureon_unified_ecosystem.py"
fi

echo -e "${YELLOW}Target:${NC} $SCRIPT"
echo -e "${YELLOW}Watchdog:${NC} $([ "$USE_WATCHDOG" == true ] && echo "ENABLED" || echo "DISABLED")"
echo ""

# Check if script exists
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}❌ Error: $SCRIPT not found!${NC}"
    exit 1
fi

# Check for running instances
if pgrep -f "python3.*$SCRIPT" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Warning: $SCRIPT already running!${NC}"
    echo "   PIDs: $(pgrep -f "python3.*$SCRIPT")"
    read -p "   Kill existing and restart? (y/N): " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        pkill -f "python3.*$SCRIPT" || true
        pkill -f "python3.*aureon_watchdog.py" || true
        sleep 2
    else
        echo "   Exiting..."
        exit 0
    fi
fi

# Run emergency harvest first if there are profitable positions
echo -e "${BLUE}🔍 Checking for profitable positions to harvest...${NC}"
python3 emergency_harvest.py --dry-run 2>/dev/null | grep -E "READY TO SELL|Found.*profitable" || true
echo ""

# Start the system
if [ "$USE_WATCHDOG" == true ]; then
    echo -e "${GREEN}🐕 Starting with WATCHDOG (auto-restart enabled)...${NC}"
    echo ""
    
    # Run watchdog in foreground (it will manage the trading system)
    python3 aureon_watchdog.py --target "$TARGET"
else
    echo -e "${YELLOW}⚠️  Starting WITHOUT watchdog (manual mode)...${NC}"
    echo ""
    
    # Run trading system directly
    python3 "$SCRIPT"
fi
