#!/usr/bin/env python3
"""
🧠 LEARNING ANALYTICS CLI
═══════════════════════════════════════════════════════════════

View what the probability matrix has learned from trade outcomes.
Shows optimal parameters based on historical performance.

Usage:
    python scripts/learning_analytics_cli.py                    # Full summary
    python scripts/learning_analytics_cli.py --symbol BTCUSDT   # Check specific symbol
    python scripts/learning_analytics_cli.py --recommend        # Get entry recommendation
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def load_learning_history():
    """Load the adaptive learning history."""
    history_file = 'adaptive_learning_history.json'
    if not os.path.exists(history_file):
        return None
    
    try:
        with open(history_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading history: {e}")
        return None

def print_full_summary(data):
    """Print comprehensive learning summary."""
    if not data:
        print("❌ No learning history found.")
        print("   The probability matrix learns from completed trades.")
        print("   Run some trades first, then check back!")
        return
        
    trades = data.get('trades', [])
    thresholds = data.get('thresholds', {})
    updated = data.get('updated_at', 'Unknown')
    
    print("═══════════════════════════════════════════════════════════════")
    print("                   🧠 ADAPTIVE LEARNING SUMMARY                 ")
    print("═══════════════════════════════════════════════════════════════")
    print(f"  Last Updated: {updated}")
    print(f"  Total Trades Analyzed: {len(trades)}")
    
    if trades:
        wins = sum(1 for t in trades if t.get('pnl', 0) > 0)
        losses = len(trades) - wins
        win_rate = wins / len(trades) * 100
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        print(f"  Overall Win Rate: {win_rate:.1f}%")
        print(f"  Total P&L: ${total_pnl:.2f}")
        print(f"  Wins: {wins} | Losses: {losses}")
    
    print()
    print("─── 🎚️ OPTIMIZED THRESHOLDS ───")
    for key, value in thresholds.items():
        if isinstance(value, float):
            print(f"  • {key}: {value:.3f}")
        else:
            print(f"  • {key}: {value}")
    
    # Analyze by frequency band
    print()
    print("─── 🎵 PERFORMANCE BY FREQUENCY BAND ───")
    
    freq_buckets = {}
    for trade in trades:
        freq = trade.get('frequency', 432)
        band = get_frequency_band(freq)
        if band not in freq_buckets:
            freq_buckets[band] = {'wins': 0, 'losses': 0, 'pnl': 0}
        
        if trade.get('pnl', 0) > 0:
            freq_buckets[band]['wins'] += 1
        else:
            freq_buckets[band]['losses'] += 1
        freq_buckets[band]['pnl'] += trade.get('pnl', 0)
    
    for band, stats in sorted(freq_buckets.items()):
        total = stats['wins'] + stats['losses']
        wr = stats['wins'] / total * 100 if total > 0 else 0
        pnl = stats['pnl']
        emoji = "🟢" if wr >= 55 else "🟡" if wr >= 45 else "🔴"
        print(f"  {emoji} {band}: {wr:.0f}% WR ({total} trades) | PnL: ${pnl:.2f}")
    
    # Analyze by hour
    print()
    print("─── ⏰ PERFORMANCE BY HOUR (UTC) ───")
    
    hour_buckets = {}
    for trade in trades:
        entry_time = trade.get('entry_time', 0)
        if entry_time:
            hour = datetime.fromtimestamp(entry_time).hour
            if hour not in hour_buckets:
                hour_buckets[hour] = {'wins': 0, 'losses': 0}
            
            if trade.get('pnl', 0) > 0:
                hour_buckets[hour]['wins'] += 1
            else:
                hour_buckets[hour]['losses'] += 1
    
    # Sort by win rate
    hour_stats = []
    for hour, stats in hour_buckets.items():
        total = stats['wins'] + stats['losses']
        if total >= 2:
            wr = stats['wins'] / total * 100
            hour_stats.append((hour, wr, total))
    
    hour_stats.sort(key=lambda x: x[1], reverse=True)
    
    for hour, wr, total in hour_stats[:5]:
        emoji = "🟢" if wr >= 60 else "🟡" if wr >= 50 else "🔴"
        print(f"  {emoji} {hour:02d}:00 UTC: {wr:.0f}% WR ({total} trades)")
    
    # Best symbols
    print()
    print("─── 🏆 TOP PERFORMING SYMBOLS ───")
    
    symbol_stats = {}
    for trade in trades:
        symbol = trade.get('symbol', 'UNKNOWN')
        if symbol not in symbol_stats:
            symbol_stats[symbol] = {'wins': 0, 'losses': 0, 'pnl': 0}
        
        if trade.get('pnl', 0) > 0:
            symbol_stats[symbol]['wins'] += 1
        else:
            symbol_stats[symbol]['losses'] += 1
        symbol_stats[symbol]['pnl'] += trade.get('pnl', 0)
    
    # Sort by PnL
    sorted_symbols = sorted(symbol_stats.items(), key=lambda x: x[1]['pnl'], reverse=True)
    
    for symbol, stats in sorted_symbols[:5]:
        total = stats['wins'] + stats['losses']
        wr = stats['wins'] / total * 100 if total > 0 else 0
        pnl = stats['pnl']
        emoji = "🟢" if pnl > 0 else "🔴"
        print(f"  {emoji} {symbol}: ${pnl:.2f} | {wr:.0f}% WR ({total} trades)")
    
    print()
    print("═══════════════════════════════════════════════════════════════")

def get_frequency_band(freq: float) -> str:
    """Map frequency to band name."""
    if freq <= 200:
        return '174_FOUNDATION'
    elif freq <= 300:
        return '256_ROOT'
    elif freq <= 410:
        return '396_LIBERATION'
    elif freq <= 438:
        return '432_NATURAL'
    elif freq <= 445:
        return '440_DISTORTION'
    elif freq <= 520:
        return '512_VISION'
    elif freq <= 580:
        return '528_LOVE'
    elif freq <= 700:
        return '639_CONNECTION'
    elif freq <= 800:
        return '741_AWAKENING'
    elif freq <= 900:
        return '852_INTUITION'
    else:
        return '963_UNITY'

def get_recommendation(data, symbol: str = None, frequency: float = 432, coherence: float = 0.6):
    """Get entry recommendation based on learned data."""
    if not data:
        print("❌ No learning data available yet.")
        return
    
    trades = data.get('trades', [])
    if not trades:
        print("❌ No trades recorded yet.")
        return
    
    band = get_frequency_band(frequency)
    current_hour = datetime.now().hour
    
    # Filter similar trades
    similar_trades = []
    for t in trades:
        t_band = get_frequency_band(t.get('frequency', 432))
        t_coh = t.get('coherence', 0.5)
        
        # Match by frequency band and similar coherence
        if t_band == band and abs(t_coh - coherence) < 0.2:
            similar_trades.append(t)
    
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"              🎯 ENTRY RECOMMENDATION                          ")
    print(f"═══════════════════════════════════════════════════════════════")
    print(f"  Analyzing: {symbol or 'Generic'}")
    print(f"  Frequency: {frequency:.0f}Hz ({band})")
    print(f"  Coherence: {coherence:.2f}")
    print(f"  Hour: {current_hour:02d}:00 UTC")
    print()
    
    if len(similar_trades) < 3:
        print(f"  ⚪ LOW CONFIDENCE: Only {len(similar_trades)} similar trades found")
        print(f"     Need more historical data for reliable prediction")
        print()
        print("  📊 Recommendation: Use default parameters")
        return
    
    wins = sum(1 for t in similar_trades if t.get('pnl', 0) > 0)
    expected_wr = wins / len(similar_trades)
    avg_pnl = sum(t.get('pnl', 0) for t in similar_trades) / len(similar_trades)
    
    winners = [t.get('pnl', 0) for t in similar_trades if t.get('pnl', 0) > 0]
    losers = [t.get('pnl', 0) for t in similar_trades if t.get('pnl', 0) < 0]
    
    print(f"  📈 Based on {len(similar_trades)} similar trades:")
    print(f"     Expected Win Rate: {expected_wr*100:.0f}%")
    print(f"     Avg P&L per Trade: ${avg_pnl:.4f}")
    
    if winners:
        avg_win = sum(winners) / len(winners)
        print(f"     Avg Win: +${avg_win:.4f}")
    
    if losers:
        avg_loss = sum(losers) / len(losers)
        print(f"     Avg Loss: ${avg_loss:.4f}")
    
    print()
    
    # Recommendation
    if expected_wr >= 0.55:
        print(f"  ✅ RECOMMENDATION: TRADE")
        print(f"     This setup has historically performed well")
    elif expected_wr >= 0.45:
        print(f"  🟡 RECOMMENDATION: CAUTIOUS")
        print(f"     Mixed results - use smaller position size")
    else:
        print(f"  ❌ RECOMMENDATION: SKIP")
        print(f"     This setup has historically underperformed")
    
    # Suggested parameters
    print()
    print("  💡 SUGGESTED PARAMETERS:")
    
    if winners:
        suggested_tp = sum(winners) / len(winners) * 0.8 * 100  # 80% of avg win
        print(f"     Take Profit: {max(1.0, suggested_tp):.1f}%")
    
    if losers:
        suggested_sl = abs(sum(losers) / len(losers)) * 1.2 * 100  # 120% of avg loss
        print(f"     Stop Loss: {max(0.8, suggested_sl):.1f}%")
    
    print(f"     Min Hold: {10 if expected_wr >= 0.5 else 15} cycles")
    
    print()
    print("═══════════════════════════════════════════════════════════════")

def main():
    parser = argparse.ArgumentParser(description='🧠 Learning Analytics CLI')
    parser.add_argument('--symbol', '-s', help='Check specific symbol')
    parser.add_argument('--recommend', '-r', action='store_true', help='Get entry recommendation')
    parser.add_argument('--frequency', '-f', type=float, default=432, help='Frequency for recommendation')
    parser.add_argument('--coherence', '-c', type=float, default=0.6, help='Coherence for recommendation')
    
    args = parser.parse_args()
    
    # Change to workspace directory
    os.chdir('/workspaces/aureon-trading')
    
    data = load_learning_history()
    
    if args.recommend:
        get_recommendation(data, args.symbol, args.frequency, args.coherence)
    else:
        print_full_summary(data)

if __name__ == '__main__':
    main()
