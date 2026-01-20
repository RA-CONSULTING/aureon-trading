#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 🎮👑 AUREON TRADING SYSTEM - PRODUCTION ENTRYPOINT 👑🎮
# ═══════════════════════════════════════════════════════════════════════════

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Banner
echo -e "${CYAN}"
cat << 'EOF'
    ╔═══════════════════════════════════════════════════════════════════════════╗
    ║                                                                           ║
    ║     █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                   ║
    ║    ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                   ║
    ║    ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                   ║
    ║    ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                   ║
    ║    ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                   ║
    ║    ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                   ║
    ║                                                                           ║
    ║                    🎮 PRODUCTION MODE 🎮                                  ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Environment info
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}AUREON HOME:${NC}   $AUREON_HOME"
echo -e "${YELLOW}AUREON DATA:${NC}   $AUREON_DATA"
echo -e "${YELLOW}AUREON LOGS:${NC}   $AUREON_LOGS"
echo -e "${YELLOW}AUREON CONFIG:${NC} $AUREON_CONFIG"
echo -e "${YELLOW}AUREON MODE:${NC}   $AUREON_MODE"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"

# Parse arguments
MODE="game"
DRY_RUN="true"
EXCHANGE=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --mode)
            MODE="$2"
            shift 2
            ;;
        --live)
            DRY_RUN="false"
            shift
            ;;
        --dry-run)
            DRY_RUN="true"
            shift
            ;;
        --exchange)
            EXCHANGE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Check for first-run setup
CONFIG_FILE="$AUREON_CONFIG/aureon.json"
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${YELLOW}⚙️  First run detected - starting setup wizard...${NC}"
    cd /aureon/app
    python production/first_run_setup.py
fi

# Verify config exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ Configuration not found. Please run setup first.${NC}"
    exit 1
fi

# Start based on mode
cd /aureon/app

# Build exchange argument if provided
EXCHANGE_ARG=""
if [ -n "$EXCHANGE" ]; then
    EXCHANGE_ARG="--exchange $EXCHANGE"
fi

case $MODE in
    "game")
        echo -e "${CYAN}🎮 Starting GAME MODE...${NC}"
        echo -e "${GREEN}   └─ Command Center UI: http://localhost:8888${NC}"
        echo -e "${GREEN}   └─ Trading Engine: DRY_RUN=$DRY_RUN${NC}"
        
        # Honor DRY_RUN setting
        if [ "$DRY_RUN" = "true" ]; then
            exec python aureon_game_launcher.py --dry-run
        else
            echo -e "${RED}   ⚠️  LIVE MODE ENABLED${NC}"
            exec python aureon_game_launcher.py
        fi
        ;;
    
    "trading")
        echo -e "${CYAN}💰 Starting TRADING MODE...${NC}"
        if [ "$DRY_RUN" = "true" ]; then
            echo -e "${YELLOW}   └─ Mode: DRY RUN (paper trading)${NC}"
            exec python micro_profit_labyrinth.py --dry-run $EXCHANGE_ARG
        else
            echo -e "${RED}   └─ Mode: LIVE TRADING${NC}"
            exec python micro_profit_labyrinth.py $EXCHANGE_ARG
        fi
        ;;
    
    "orca")
        echo -e "${CYAN}🦈 Starting ORCA KILL MODE...${NC}"
        # Honor DRY_RUN setting for orca mode
        if [ "$DRY_RUN" = "true" ]; then
            exec python orca_complete_kill_cycle.py --dry-run
        else
            echo -e "${RED}   ⚠️  LIVE ORCA MODE${NC}"
            exec python orca_complete_kill_cycle.py
        fi
        ;;
    
    "queen")
        echo -e "${CYAN}👑 Starting QUEEN DASHBOARD...${NC}"
        exec python queen_unified_dashboard.py
        ;;
    
    "shell")
        echo -e "${CYAN}🐚 Starting interactive shell...${NC}"
        exec /bin/bash
        ;;
    
    *)
        echo -e "${RED}Unknown mode: $MODE${NC}"
        echo "Available modes: game, trading, orca, queen, shell"
        exit 1
        ;;
esac
