#!/usr/bin/env python3
"""
📊 FIRM INTELLIGENCE CATALOG CLI 📊
====================================

Interactive command-line interface for firm intelligence catalog.
Query, analyze, and visualize firm activity patterns.

Commands:
- status: Show catalog status
- list: List all tracked firms
- firm <id>: Get detailed firm summary
- leaders <symbol>: Show market leaders for symbol
- patterns <firm_id>: Show recognized patterns
- predict <firm_id>: Get prediction for firm
- export <firm_id>: Export firm data to JSON
- watch <firm_id>: Live watch firm activity

Gary Leckey | January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import argparse
import json
import time
from typing import Dict, Any
from pathlib import Path

try:
    from aureon_firm_intelligence_catalog import get_firm_catalog, FirmIntelligenceCatalog
    CATALOG_AVAILABLE = True
except ImportError:
    print("❌ ERROR: Firm Intelligence Catalog not available")
    print("   Make sure aureon_firm_intelligence_catalog.py is in the same directory")
    sys.exit(1)


def format_currency(value: float) -> str:
    """Format USD value."""
    if value >= 1_000_000_000:
        return f"${value/1_000_000_000:.2f}B"
    elif value >= 1_000_000:
        return f"${value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"${value/1_000:.2f}K"
    else:
        return f"${value:.2f}"


def format_time_ago(timestamp: float) -> str:
    """Format time ago."""
    now = time.time()
    diff = now - timestamp
    
    if diff < 60:
        return f"{int(diff)}s ago"
    elif diff < 3600:
        return f"{int(diff/60)}m ago"
    elif diff < 86400:
        return f"{int(diff/3600)}h ago"
    else:
        return f"{int(diff/86400)}d ago"


def cmd_status(catalog: FirmIntelligenceCatalog):
    """Show catalog status."""
    status = catalog.get_status()
    
    print("\n📊 FIRM INTELLIGENCE CATALOG STATUS")
    print("=" * 60)
    print(f"Total firms tracked: {status['total_firms_tracked']}")
    print(f"Active firms (24h):  {status['active_firms_24h']}")
    print(f"Total movements:     {status['total_movements_24h']}")
    print(f"Total patterns:      {status['total_patterns']}")
    print(f"Lookback period:     {status['lookback_hours']} hours")
    print("=" * 60)


def cmd_list(catalog: FirmIntelligenceCatalog):
    """List all tracked firms."""
    active_firms = catalog.get_all_active_firms()
    
    if not active_firms:
        print("\n❌ No active firms in the last 24 hours")
        return
    
    print(f"\n📊 ACTIVE FIRMS ({len(active_firms)})")
    print("=" * 60)
    
    for firm_id in active_firms:
        stats = catalog.compute_statistics(firm_id)
        last_activity = catalog.last_activity.get(firm_id, 0)
        
        print(f"\n{firm_id.upper()}")
        print(f"  Movements: {stats.total_movements} | Volume: {format_currency(stats.total_volume_usd)}")
        print(f"  Buy/Sell: {stats.buys}/{stats.sells} | Success: {stats.success_rate:.0%}")
        print(f"  Last activity: {format_time_ago(last_activity)}")
        print(f"  Predicted: {stats.predicted_direction} ({stats.next_24h_activity_probability:.0%})")


def cmd_firm(catalog: FirmIntelligenceCatalog, firm_id: str):
    """Get detailed firm summary."""
    try:
        summary = catalog.get_firm_summary(firm_id)
    except Exception as e:
        print(f"\n❌ ERROR: Could not get firm data: {e}")
        return
    
    stats = summary['statistics']
    pred = summary['prediction']
    
    print(f"\n📊 FIRM INTELLIGENCE: {firm_id.upper()}")
    print("=" * 60)
    
    # Statistics
    print(f"\n📈 STATISTICS (24h)")
    print(f"  Total movements:     {stats['total_movements']}")
    print(f"  Total volume:        {format_currency(stats['total_volume_usd'])}")
    print(f"  Avg movement size:   {format_currency(stats['avg_movement_size'])}")
    print(f"  Buy/Sell ratio:      {stats['buys']}/{stats['sells']}")
    print(f"  Success rate:        {stats['success_rate']:.0%}")
    print(f"  Avg profit:          {stats['avg_profit_pct']:.2f}%")
    
    # Behavioral
    print(f"\n🎯 BEHAVIORAL PATTERNS")
    print(f"  Dominant activity:   {stats['dominant_activity_type']}")
    if stats['most_active_hours']:
        print(f"  Active hours:        {', '.join(f'{h:02d}:00' for h in stats['most_active_hours'][:3])}")
    if stats['most_active_symbols']:
        print(f"  Preferred symbols:   {', '.join(stats['most_active_symbols'][:3])}")
    
    # Patterns
    patterns = summary.get('patterns', [])
    if patterns:
        print(f"\n🔍 RECOGNIZED PATTERNS ({len(patterns)})")
        for i, pattern in enumerate(patterns[:5], 1):
            print(f"  {i}. {pattern['pattern_name']}")
            print(f"     Occurrences: {pattern['occurrences']} | Last seen: {format_time_ago(pattern['last_seen'])}")
    
    # Recent movements
    recent = summary.get('recent_movements', [])
    if recent:
        print(f"\n📝 RECENT ACTIVITY (Last {len(recent)})")
        for mov in recent[-5:]:
            side_icon = "🟢" if mov['side'] == 'buy' else "🔴"
            print(f"  {side_icon} {mov['symbol']} {mov['side'].upper()} "
                  f"{format_currency(mov['volume_usd'])} @ ${mov['price']:.2f} "
                  f"({format_time_ago(mov['timestamp'])})")
    
    # Prediction
    print(f"\n🔮 PREDICTION")
    print(f"  Next 24h activity:   {pred['next_24h_probability']:.0%} probability")
    print(f"  Predicted direction: {pred['predicted_direction'].upper()}")
    print(f"  Confidence:          {pred['confidence']:.0%}")
    print(f"  Reasoning:           {pred['reasoning']}")
    
    print(f"\n⏰ Last activity: {format_time_ago(summary['last_activity'])} "
          f"({summary['hours_since_activity']:.1f}h ago)")
    print("=" * 60)


def cmd_leaders(catalog: FirmIntelligenceCatalog, symbol: str):
    """Show market leaders for symbol."""
    leaders = catalog.get_market_leaders(symbol, top_n=10)
    
    if not leaders:
        print(f"\n❌ No activity found for {symbol}")
        return
    
    print(f"\n📊 MARKET LEADERS: {symbol}")
    print("=" * 60)
    
    total_volume = sum(vol for _, vol in leaders)
    
    for i, (firm_id, volume) in enumerate(leaders, 1):
        pct = (volume / total_volume * 100) if total_volume > 0 else 0
        bar_length = int(pct / 2)  # 2% per character
        bar = "█" * bar_length
        
        print(f"{i:2d}. {firm_id:20s} {format_currency(volume):>10s} {bar} {pct:.1f}%")
    
    print("=" * 60)
    print(f"Total volume: {format_currency(total_volume)}")


def cmd_patterns(catalog: FirmIntelligenceCatalog, firm_id: str):
    """Show recognized patterns for firm."""
    patterns = catalog.recognize_patterns(firm_id, min_occurrences=2)
    
    if not patterns:
        print(f"\n❌ No patterns recognized for {firm_id}")
        return
    
    print(f"\n🔍 PATTERNS: {firm_id.upper()}")
    print("=" * 60)
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\n{i}. {pattern.pattern_name}")
        print(f"   Pattern ID:      {pattern.pattern_id}")
        print(f"   Occurrences:     {pattern.occurrences}")
        print(f"   Success rate:    {pattern.success_rate:.0%}")
        print(f"   Avg profit:      {pattern.avg_profit_pct:.2f}%")
        
        if pattern.preferred_hours:
            print(f"   Active hours:    {', '.join(f'{h:02d}:00' for h in pattern.preferred_hours[:3])}")
        if pattern.preferred_symbols:
            print(f"   Symbols:         {', '.join(pattern.preferred_symbols[:3])}")
        
        print(f"   Last seen:       {format_time_ago(pattern.last_seen)}")
        print(f"   Next probability: {pattern.next_move_probability:.0%}")
    
    print("=" * 60)


def cmd_predict(catalog: FirmIntelligenceCatalog, firm_id: str):
    """Get prediction for firm."""
    try:
        summary = catalog.get_firm_summary(firm_id)
    except Exception as e:
        print(f"\n❌ ERROR: Could not get firm data: {e}")
        return
    
    stats = summary['statistics']
    pred = summary['prediction']
    
    print(f"\n🔮 PREDICTION: {firm_id.upper()}")
    print("=" * 60)
    
    # Prediction summary
    print(f"\nNext 24h Activity:  {pred['next_24h_probability']:.0%} probability")
    print(f"Predicted Direction: {pred['predicted_direction'].upper()}")
    print(f"Confidence Level:    {pred['confidence']:.0%}")
    
    # Confidence breakdown
    confidence_label = "HIGH" if pred['confidence'] > 0.7 else "MEDIUM" if pred['confidence'] > 0.5 else "LOW"
    confidence_icon = "🟢" if pred['confidence'] > 0.7 else "🟡" if pred['confidence'] > 0.5 else "🔴"
    print(f"\n{confidence_icon} Confidence: {confidence_label}")
    
    # Reasoning
    print(f"\n📋 Reasoning:")
    print(f"   {pred['reasoning']}")
    
    # Supporting data
    print(f"\n📊 Supporting Data:")
    print(f"   Recent movements:    {stats['total_movements']}")
    print(f"   Success rate:        {stats['success_rate']:.0%}")
    print(f"   Buy/Sell bias:       {stats['buys']}/{stats['sells']}")
    
    # Time context
    hours_since = summary['hours_since_activity']
    if hours_since < 1:
        activity_status = "🟢 VERY ACTIVE (< 1h ago)"
    elif hours_since < 6:
        activity_status = "🟡 ACTIVE (< 6h ago)"
    elif hours_since < 12:
        activity_status = "🟠 RECENT (< 12h ago)"
    else:
        activity_status = "🔴 QUIET (> 12h ago)"
    
    print(f"\n⏰ Activity Status: {activity_status}")
    print(f"   Last activity: {format_time_ago(summary['last_activity'])}")
    
    print("=" * 60)


def cmd_export(catalog: FirmIntelligenceCatalog, firm_id: str, output_file: str = None):
    """Export firm data to JSON."""
    try:
        summary = catalog.get_firm_summary(firm_id)
    except Exception as e:
        print(f"\n❌ ERROR: Could not get firm data: {e}")
        return
    
    if output_file is None:
        output_file = f"firm_intel_{firm_id}_{int(time.time())}.json"
    
    output_path = Path(output_file)
    output_path.write_text(json.dumps(summary, indent=2))
    
    print(f"\n✅ Exported to: {output_path}")
    print(f"   Size: {output_path.stat().st_size:,} bytes")


def cmd_watch(catalog: FirmIntelligenceCatalog, firm_id: str, interval: int = 5):
    """Live watch firm activity."""
    print(f"\n👁️ WATCHING: {firm_id.upper()} (refresh every {interval}s)")
    print("Press Ctrl+C to stop\n")
    
    try:
        while True:
            os.system('clear' if os.name != 'nt' else 'cls')
            
            print(f"📊 LIVE WATCH: {firm_id.upper()}")
            print(f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)
            
            try:
                summary = catalog.get_firm_summary(firm_id)
                stats = summary['statistics']
                
                print(f"\n📈 REAL-TIME STATS")
                print(f"  Movements (24h): {stats['total_movements']}")
                print(f"  Volume:          {format_currency(stats['total_volume_usd'])}")
                print(f"  Buy/Sell:        {stats['buys']}/{stats['sells']}")
                print(f"  Last activity:   {format_time_ago(summary['last_activity'])}")
                
                # Recent movements
                recent = summary.get('recent_movements', [])
                if recent:
                    print(f"\n📝 RECENT ACTIVITY (Last {len(recent[-5:])})")
                    for mov in recent[-5:]:
                        side_icon = "🟢" if mov['side'] == 'buy' else "🔴"
                        print(f"  {side_icon} {mov['symbol']} {mov['side'].upper()} "
                              f"{format_currency(mov['volume_usd'])} @ ${mov['price']:.2f} "
                              f"({format_time_ago(mov['timestamp'])})")
                
            except Exception as e:
                print(f"❌ ERROR: {e}")
            
            print("\n" + "=" * 60)
            print("Press Ctrl+C to stop...")
            
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n👋 Watch stopped")


def main():
    parser = argparse.ArgumentParser(
        description="Firm Intelligence Catalog CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s status                    # Show catalog status
  %(prog)s list                      # List all tracked firms
  %(prog)s firm citadel              # Get detailed firm summary
  %(prog)s leaders BTC/USD           # Show market leaders for BTC/USD
  %(prog)s patterns citadel          # Show recognized patterns
  %(prog)s predict jane_street       # Get prediction
  %(prog)s export citadel            # Export to JSON
  %(prog)s watch citadel --interval 3  # Live watch (3s refresh)
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # status
    subparsers.add_parser('status', help='Show catalog status')
    
    # list
    subparsers.add_parser('list', help='List all tracked firms')
    
    # firm
    firm_parser = subparsers.add_parser('firm', help='Get detailed firm summary')
    firm_parser.add_argument('firm_id', help='Firm identifier')
    
    # leaders
    leaders_parser = subparsers.add_parser('leaders', help='Show market leaders for symbol')
    leaders_parser.add_argument('symbol', help='Trading symbol (e.g., BTC/USD)')
    
    # patterns
    patterns_parser = subparsers.add_parser('patterns', help='Show recognized patterns')
    patterns_parser.add_argument('firm_id', help='Firm identifier')
    
    # predict
    predict_parser = subparsers.add_parser('predict', help='Get prediction for firm')
    predict_parser.add_argument('firm_id', help='Firm identifier')
    
    # export
    export_parser = subparsers.add_parser('export', help='Export firm data to JSON')
    export_parser.add_argument('firm_id', help='Firm identifier')
    export_parser.add_argument('--output', '-o', help='Output file path')
    
    # watch
    watch_parser = subparsers.add_parser('watch', help='Live watch firm activity')
    watch_parser.add_argument('firm_id', help='Firm identifier')
    watch_parser.add_argument('--interval', '-i', type=int, default=5, help='Refresh interval (seconds)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Initialize catalog
    catalog = get_firm_catalog()
    
    # Execute command
    if args.command == 'status':
        cmd_status(catalog)
    elif args.command == 'list':
        cmd_list(catalog)
    elif args.command == 'firm':
        cmd_firm(catalog, args.firm_id)
    elif args.command == 'leaders':
        cmd_leaders(catalog, args.symbol)
    elif args.command == 'patterns':
        cmd_patterns(catalog, args.firm_id)
    elif args.command == 'predict':
        cmd_predict(catalog, args.firm_id)
    elif args.command == 'export':
        cmd_export(catalog, args.firm_id, args.output)
    elif args.command == 'watch':
        cmd_watch(catalog, args.firm_id, args.interval)


if __name__ == '__main__':
    main()
