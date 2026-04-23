#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 🎮👑 AUREON TRADING SYSTEM - PRODUCTION ENTRYPOINT 👑🎮
# ═══════════════════════════════════════════════════════════════════════════
# Supports: supervisor, game, trading, orca, queen modes

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Environment defaults
AUREON_HOME="${AUREON_HOME:-/aureon}"
AUREON_DATA="${AUREON_DATA:-/aureon/data}"
AUREON_LOGS="${AUREON_LOGS:-/aureon/logs}"
AUREON_CONFIG="${AUREON_CONFIG:-/aureon/config}"
AUREON_MODE="${AUREON_MODE:-production}"

# Create directories if needed
mkdir -p "$AUREON_DATA" "$AUREON_LOGS" "$AUREON_CONFIG" "$AUREON_CONFIG/supervisor.d"

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
MODE="supervisor"  # Default to supervisor for parallel execution
DRY_RUN="false"
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

case $MODE in
    "supervisor")
        echo -e "${BLUE}🚀 Starting SUPERVISOR MODE (All 43 systems in parallel)...${NC}"
        echo -e "${GREEN}   ├─ Core Systems (9): Priority 1-9${NC}"
        echo -e "${GREEN}   ├─ Specialized Traders (28): Priority 10-37${NC}"
        echo -e "${GREEN}   ├─ Autonomous Control: ENABLED${NC}"
        echo -e "${GREEN}   ├─ Sovereignty Level: SOVEREIGN${NC}"
        echo -e "${GREEN}   ├─ Monitoring: $AUREON_LOGS${NC}"
        echo -e "${GREEN}   └─ Command: supervisorctl status${NC}"
        echo ""
        
        # Update supervisor config with environment variables
        export AUREON_DRY_RUN="$DRY_RUN"
        export AUREON_ENABLE_AUTONOMOUS_CONTROL="1"
        
        # Start supervisord in foreground (important for Docker)
        exec /usr/bin/supervisord \
            -c /etc/supervisor/conf.d/supervisord.conf \
            -n \
            --logfile="$AUREON_LOGS/supervisord.log"
        ;;
    
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
            exec python micro_profit_labyrinth.py --dry-run
        else
            echo -e "${RED}   └─ Mode: LIVE TRADING${NC}"
            exec python micro_profit_labyrinth.py
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
        echo "Available modes: supervisor, game, trading, orca, queen, shell"
        exit 1
        ;;
esac
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
