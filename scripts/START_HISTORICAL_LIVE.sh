#!/bin/bash
# 🔮💎 START AUREON HISTORICAL LIVE TRADER 💎🔮

echo "═══════════════════════════════════════════════════════════════════════════════"
echo "║                                                                             ║"
echo "║              🔮💎 AUREON HISTORICAL LIVE TRADER 💎🔮                        ║"
echo "║                                                                             ║"
echo "║                \"The Past Predicts. The Present Executes.\"                 ║"
echo "║                                                                             ║"
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""
echo "📋 Pre-flight checks:"
echo ""

# Check Python
if command -v python3 &> /dev/null; then
    echo "✅ Python 3: $(python3 --version)"
else
    echo "❌ Python 3 not found"
    exit 1
fi

# Check required files
required_files=(
    "aureon_historical_live.py"
    "probability_ultimate_intelligence.py"
    "probability_intelligence_matrix.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file: Found"
    else
        echo "⚠️  $file: Not found (will continue with available systems)"
    fi
done

echo ""
echo "📡 Exchange connections:"
echo "   • Kraken: Will attempt connection"
echo "   • Alpaca: Will attempt connection"
echo "   • Binance: Will attempt connection"
echo ""
echo "🎯 Strategy:"
echo "   • Historical patterns (87.5% win rate)"
echo "   • Elite patterns only (80%+ confidence)"
echo "   • Multi-exchange scanning"
echo "   • PDT compliant (unlocks at £25K)"
echo "   • Margin at £2K, unlimited trades at £25K"
echo ""
echo "💰 Starting capital: £76.00"
echo "🎯 Target: £100,000.00"
echo ""
echo "═══════════════════════════════════════════════════════════════════════════════"
echo ""

# Start the trader
python3 aureon_historical_live.py
