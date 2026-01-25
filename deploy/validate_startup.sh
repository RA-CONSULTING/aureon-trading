#!/bin/bash
# Digital Ocean Startup Validation
# Ensures all systems are ready before starting services

set -e

echo "🔍 Validating Digital Ocean deployment..."

# Check Python version
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Check required packages
echo "📦 Checking critical packages..."
python -c "import requests; import aiohttp; import websockets; import flask; print('✅ Core packages installed')"

# Check environment variables
echo "🌍 Checking environment..."
if [ -z "$PYTHONIOENCODING" ]; then
    export PYTHONIOENCODING=utf-8
    echo "⚠️ Set PYTHONIOENCODING=utf-8"
fi

if [ -z "$AUREON_STATE_DIR" ]; then
    export AUREON_STATE_DIR=/app/state
    echo "⚠️ Set AUREON_STATE_DIR=/app/state"
fi

# Create required directories
echo "📁 Creating directories..."
mkdir -p /app/state /app/logs /var/log/supervisor
echo "✅ Directories created"

# Initialize state files with proper JSON
echo "📄 Initializing state files..."
cat > /app/queen_redistribution_state.json << 'EOF'
{
  "last_update": 0.0,
  "total_net_energy_gained": 0.0,
  "total_blocked_drains_avoided": 0.0,
  "decisions_count": 0,
  "executions_count": 0,
  "recent_decisions": [],
  "recent_executions": []
}
EOF

cat > /app/power_station_state.json << 'EOF'
{
  "status": "STOPPED",
  "cycles_run": 0,
  "total_energy_now": 0.0,
  "energy_deployed": 0.0,
  "net_flow": 0.0,
  "efficiency": 0.0
}
EOF

cat > /app/queen_energy_balance.json << 'EOF'
{
  "last_update": 0,
  "total_energy_in": 0.0,
  "total_energy_out": 0.0,
  "net_balance": 0.0
}
EOF

echo "✅ State files initialized"

# Check critical Python files exist
echo "🐍 Checking critical files..."
critical_files=(
    "queen_power_redistribution.py"
    "queen_power_dashboard.py"
    "aureon_queen_true_consciousness.py"
    "adaptive_prime_profit_gate.py"
    "kraken_cache_feeder.py"
)

for file in "${critical_files[@]}"; do
    if [ -f "/app/$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ Missing: $file"
        exit 1
    fi
done

# Test imports
echo "🧪 Testing critical imports..."
python -c "
import sys
import os
sys.path.insert(0, '/app')
try:
    from adaptive_prime_profit_gate import AdaptivePrimeProfitGate
    print('✅ AdaptivePrimeProfitGate imported')
except Exception as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"

echo "🎉 Validation complete! Ready to start services."
echo ""
echo "🚀 Starting supervisor..."
