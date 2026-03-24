#!/bin/bash
# Quick test script for DigitalOcean deployment

echo "🦈 Aureon Trading - Docker Build Test"
echo "======================================"

# Check Docker installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not installed. Install with: curl -fsSL https://get.docker.com | sh"
    exit 1
fi

echo "✅ Docker installed"

# Check .env file
if [ ! -f .env ]; then
    echo "⚠️  .env file not found - creating template..."
    cat > .env << 'EOF'
# Exchange API Keys (REQUIRED)
KRAKEN_API_KEY=your_key_here
KRAKEN_API_SECRET=your_secret_here
BINANCE_API_KEY=your_key
BINANCE_API_SECRET=your_secret
ALPACA_API_KEY=your_key
ALPACA_API_SECRET=your_secret

# Trading Config
MODE=autonomous
MAX_POSITIONS=3
AMOUNT_PER_POSITION=5.0
TARGET_PCT=1.0
MIN_CHANGE_PCT=0.25
EOF
    echo "📝 Created .env template - edit it with your API keys!"
    exit 1
fi

echo "✅ .env file found"

# Build Docker image
echo ""
echo "🔨 Building Docker image..."
docker build -t aureon-trading:test . || {
    echo "❌ Docker build failed"
    exit 1
}

echo "✅ Docker image built successfully"

# Test container (dry run)
echo ""
echo "🧪 Testing container startup..."
docker run --rm --env-file .env -e MODE=autonomous aureon-trading:test python -c "
import sys
print('✅ Python imports OK')
try:
    from orca_complete_kill_cycle import OrcaKillCycle
    print('✅ Orca Kill Cycle module loaded')
except Exception as e:
    print(f'❌ Failed to load Orca: {e}')
    sys.exit(1)
" || {
    echo "❌ Container test failed"
    exit 1
}

echo ""
echo "✅ All tests passed!"
echo ""
echo "Next steps:"
echo "1. Edit .env with your real API keys"
echo "2. Run: docker-compose -f docker-compose.autonomous.yml up -d"
echo "3. Monitor: docker logs -f aureon-autonomous-trader"
