#!/bin/bash
# 🌌 AUREON UNIFIED ECOSYSTEM RUNNER 🌌

# Default to both if not set
export EXCHANGE=${EXCHANGE:-both}
export LIVE=${LIVE:-1}
export FRESH_START=${FRESH_START:-0}

echo "🚀 Launching Aureon Unified Ecosystem on $EXCHANGE..."

# Activate virtual environment
source .venv/bin/activate

# Run the unified ecosystem
python aureon_unified_ecosystem.py
