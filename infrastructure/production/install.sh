#!/bin/bash
# ═══════════════════════════════════════════════════════════════════════════
# 🎮👑 AUREON TRADING SYSTEM - LINUX/macOS INSTALLER 👑🎮
# ═══════════════════════════════════════════════════════════════════════════
# One-click installer for Unix systems
# Usage: chmod +x install.sh && ./install.sh
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
    ║                    🎮 UNIX INSTALLER 🎮                                   ║
    ║                                                                           ║
    ╚═══════════════════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
fi

echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${YELLOW}Step 1: Checking Prerequisites${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo

# Check for Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found!${NC}"
    echo
    echo "   AUREON runs in a secure Docker container."
    echo "   Please install Docker first:"
    echo
    if [[ "$OS" == "macos" ]]; then
        echo "   https://www.docker.com/products/docker-desktop"
        echo "   Or: brew install --cask docker"
    else
        echo "   curl -fsSL https://get.docker.com | sh"
        echo "   sudo usermod -aG docker \$USER"
    fi
    echo
    exit 1
fi
echo -e "${GREEN}✅ Docker found${NC}"

# Check Docker is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker is not running!${NC}"
    echo "   Please start Docker and try again."
    exit 1
fi
echo -e "${GREEN}✅ Docker is running${NC}"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${YELLOW}Step 2: Building AUREON Trading System${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🔨 Building Docker image (this may take a few minutes)..."
docker build -t aureon-trading:latest -f "$SCRIPT_DIR/Dockerfile" "$PROJECT_DIR"
echo -e "${GREEN}✅ Docker image built successfully${NC}"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${YELLOW}Step 3: Creating Data Volumes${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo

docker volume create aureon-data > /dev/null 2>&1 || true
docker volume create aureon-logs > /dev/null 2>&1 || true
docker volume create aureon-config > /dev/null 2>&1 || true
echo -e "${GREEN}✅ Data volumes created${NC}"

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${YELLOW}Step 4: Creating Launch Script${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo

# Create launcher script
LAUNCHER="$HOME/.local/bin/aureon"
mkdir -p "$HOME/.local/bin"

cat > "$LAUNCHER" << 'LAUNCHER_EOF'
#!/bin/bash
# AUREON Trading System Launcher

ACTION="${1:-start}"

# Version for updates
AUREON_VERSION="1.0.0"

case "$ACTION" in
    start)
        echo "🚀 Starting AUREON Trading System v${AUREON_VERSION}..."
        docker start aureon-game 2>/dev/null || \
        docker run -d --name aureon-game \
            -p 8888:8888 \
            -v aureon-data:/aureon/data \
            -v aureon-logs:/aureon/logs \
            -v aureon-config:/aureon/config \
            --memory=2g --cpus=2.0 \
            --restart=unless-stopped \
            aureon-trading:latest
        sleep 3
        echo "✅ AUREON is running at: http://localhost:8888"
        
        # Open browser
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:8888
        elif command -v open &> /dev/null; then
            open http://localhost:8888
        fi
        ;;
    stop)
        echo "🛑 Stopping AUREON..."
        docker stop aureon-game
        ;;
    logs)
        docker logs -f aureon-game
        ;;
    shell)
        docker exec -it aureon-game /bin/bash
        ;;
    update)
        echo "🔄 Updating AUREON Trading System..."
        docker stop aureon-game 2>/dev/null || true
        docker rm aureon-game 2>/dev/null || true
        docker pull aureon-trading:latest 2>/dev/null || \
            echo "ℹ️  No remote image - rebuild locally with: cd aureon-trading && ./production/install.sh"
        echo "✅ Update complete. Run 'aureon start' to launch."
        ;;
    version)
        echo "AUREON Trading System v${AUREON_VERSION}"
        docker images aureon-trading:latest --format "Image: {{.Repository}}:{{.Tag}} ({{.Size}})"
        ;;
    *)
        echo "AUREON Trading System v${AUREON_VERSION}"
        echo "Usage: aureon [start|stop|logs|shell|update|version]"
        ;;
esac
LAUNCHER_EOF

chmod +x "$LAUNCHER"
echo -e "${GREEN}✅ Launcher created: $LAUNCHER${NC}"

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo "   Add this to your ~/.bashrc or ~/.zshrc:"
    echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo -e "  ${GREEN}✅ INSTALLATION COMPLETE!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"
echo
echo "  🎮 AUREON Trading System has been installed!"
echo
echo "  To start trading:"
echo "    aureon start    - Launch AUREON"
echo "    aureon stop     - Stop AUREON"
echo "    aureon logs     - View logs"
echo "    aureon shell    - Open shell in container"
echo
echo "  Or run directly:"
echo "    docker run -it -p 8888:8888 aureon-trading:latest"
echo
echo "  Dashboard URL: http://localhost:8888"
echo
echo -e "${GREEN}═══════════════════════════════════════════════════════════════════════════${NC}"

# Ask to launch
echo
read -p "Would you like to launch AUREON now? (y/n): " LAUNCH
if [[ "$LAUNCH" =~ ^[Yy]$ ]]; then
    echo
    "$LAUNCHER" start
fi
