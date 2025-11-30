#!/bin/bash
# Monitor Aureon Ultimate bot performance

LOG_FILE=$(ls -t aureon_run_*.log 2>/dev/null | head -1)

if [ -z "$LOG_FILE" ]; then
    echo "❌ No log file found!"
    exit 1
fi

echo "📊 MONITORING: $LOG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Get latest cycle stats
echo ""
echo "💰 LATEST STATUS:"
tail -100 "$LOG_FILE" | grep -E "Total:|Hive:" | tail -4

echo ""
echo "📈 ACTIVE POSITIONS:"
tail -100 "$LOG_FILE" | grep -E "Entry.*Now" | tail -10

echo ""
echo "✅ PROFITABLE EXITS:"
grep -E "Harvested|Sold.*Order" "$LOG_FILE" | grep -E "Net PnL \+|Net \$[^-]" | tail -5

echo ""
echo "❌ LOSING EXITS:"
grep -E "Harvested|Sold.*Order" "$LOG_FILE" | grep -E "Net PnL -|Net \$-" | tail -5

echo ""
echo "🏆 SUMMARY:"
grep -E "Trades:|Wins:|WR:" "$LOG_FILE" | tail -3

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "💡 To watch live: tail -f $LOG_FILE"
