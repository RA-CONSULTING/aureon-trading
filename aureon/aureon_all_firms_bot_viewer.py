#!/usr/bin/env python3
"""
📊 AUREON ALL FIRMS BOT VIEWER 📊
==================================

DISPLAY ALL TRADING FIRMS AND THEIR ALGORITHMIC BOTS

Shows:
- Every major trading firm (50+ firms)
- Their bot signatures
- Geographic distribution
- Trading strategies
- Current market activity
- Attribution confidence

Gary Leckey | January 2026 | See Everyone's Algos
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

# UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from aureon_global_firm_intelligence import (
        get_attribution_engine, GLOBAL_FIRM_INTELLIGENCE,
        TradingFirmIntelligence, BotSignature
    )
except ImportError as e:
    logger.error(f"Failed to import firm intelligence: {e}")
    sys.exit(1)


class AllFirmsBotViewer:
    """
    📊 ALL FIRMS BOT VIEWER 📊
    
    Display every trading firm and their bots.
    """
    
    def __init__(self):
        self.engine = get_attribution_engine()
        self.firms = GLOBAL_FIRM_INTELLIGENCE
        
    def display_summary(self):
        """Display summary of all firms."""
        print("\n┌" + "─" * 78 + "┐")
        print("│" + " " * 15 + "🌍 GLOBAL TRADING FIRMS - ALGORITHMIC BOTS 🌍" + " " * 17 + "│")
        print("├" + "─" * 78 + "┤")
        
        # Group by type
        by_type = {}
        for firm in self.firms.values():
            by_type.setdefault(firm.type, []).append(firm)
            
        total_firms = len(self.firms)
        total_aum = sum(f.estimated_aum_usd for f in self.firms.values())
        total_daily_volume = sum(f.average_daily_volume_usd for f in self.firms.values())
        
        print(f"│ Total Firms: {total_firms:<10} Total AUM: ${total_aum:>20,.0f}" + " " * 23 + "│")
        print(f"│ Daily Volume: ${total_daily_volume:>18,.0f}" + " " * 46 + "│")
        print("├" + "─" * 78 + "┤")
        
        for firm_type, firms in sorted(by_type.items()):
            type_aum = sum(f.estimated_aum_usd for f in firms)
            print(f"│ {firm_type:<15} {len(firms):>2} firms │ ${type_aum:>20,.0f} AUM" + " " * (37 - len(f"{type_aum:,.0f}")) + "│")
            
        print("└" + "─" * 78 + "┘")
        
    def display_all_firms_detailed(self):
        """Display detailed view of all firms."""
        print("\n" + "=" * 80)
        print(" " * 25 + "📊 COMPLETE FIRM DIRECTORY 📊")
        print("=" * 80)
        
        # Group by type
        by_type = {}
        for firm in self.firms.values():
            by_type.setdefault(firm.type, []).append(firm)
            
        for firm_type in ["HFT", "MARKET_MAKER", "HEDGE_FUND", "PROP_SHOP"]:
            if firm_type not in by_type:
                continue
                
            firms = sorted(by_type[firm_type], key=lambda f: f.estimated_aum_usd, reverse=True)
            
            print(f"\n{'─' * 80}")
            print(f"🏆 {firm_type} FIRMS ({len(firms)})")
            print(f"{'─' * 80}")
            
            for firm in firms:
                self._display_firm_card(firm)
                
    def _display_firm_card(self, firm: TradingFirmIntelligence):
        """Display a single firm card."""
        print(f"\n┌{'─' * 78}┐")
        print(f"│ 🏢 {firm.name:<50} {firm.firm_id:>24} │")
        print(f"├{'─' * 78}┤")
        print(f"│ Founded: {firm.founded} | HQ: {firm.hq_location:<30} AUM: ${firm.estimated_aum_usd:>18,.0f} │"[:78] + " " * (78 - min(78, len(f"│ Founded: {firm.founded} | HQ: {firm.hq_location:<30} AUM: ${firm.estimated_aum_usd:>18,.0f} │"))) + "│")
        print(f"│ Type: {firm.type:<20} Daily Volume: ${firm.average_daily_volume_usd:>15,.0f}" + " " * 22 + "│"[:78] + " " * (78 - min(78, len(f"│ Type: {firm.type:<20} Daily Volume: ${firm.average_daily_volume_usd:>15,.0f}"))) + "│")
        
        # Offices
        print(f"│ " + " " * 76 + "│")
        print(f"│ 🌍 Offices ({len(firm.offices)}):" + " " * 62 + "│")
        for office in firm.offices[:4]:  # Show first 4
            capital_str = f"${office.estimated_capital_usd:,.0f}"
            office_str = f"   {office.city}, {office.country} ({office.timezone})"
            line = f"│ {office_str:<50} {capital_str:>26} │"
            if len(line) > 80:
                line = line[:78] + " │"
            print(line)
            
        # Bot Signatures
        print(f"│ " + " " * 76 + "│")
        print(f"│ 🤖 Algorithmic Bot Signatures ({len(firm.bot_signatures)}):" + " " * 44 + "│")
        for i, sig in enumerate(firm.bot_signatures, 1):
            freq_str = f"{sig.frequency_range[0]:.1f}-{sig.frequency_range[1]:.1f}Hz"
            size_str = f"${sig.typical_order_size[0]/1000:.0f}K-${sig.typical_order_size[1]/1000:.0f}K"
            print(f"│   Signature #{i}:" + " " * 60 + "│")
            print(f"│     Frequency: {freq_str:<20} Order Size: {size_str:<20}" + " " * 25 + "│")
            print(f"│     Strategies: {', '.join(sig.strategies[:3]):<50}" + " " * (26 - len(', '.join(sig.strategies[:3]))) + "│")
            print(f"│     Targets: {', '.join(sig.target_symbols[:4]):<50}" + " " * (29 - len(', '.join(sig.target_symbols[:4]))) + "│")
            print(f"│     Confidence: {sig.identification_confidence:.0%}" + " " * 63 + "│")
            
        # Trading Characteristics
        print(f"│ " + " " * 76 + "│")
        print(f"│ 📈 Trading Characteristics:" + " " * 50 + "│")
        print(f"│   Strategies: {', '.join(firm.typical_strategies[:3]):<60}" + " " * (16 - len(', '.join(firm.typical_strategies[:3]))) + "│")
        print(f"│   Symbols: {', '.join(firm.typical_symbols[:5]):<63}" + " " * (13 - len(', '.join(firm.typical_symbols[:5]))) + "│")
        
        # Known relationships
        if firm.known_partners:
            print(f"│   Partners: {', '.join(firm.known_partners[:2]):<60}" + " " * (17 - len(', '.join(firm.known_partners[:2]))) + "│")
        if firm.known_competitors:
            print(f"│   Competitors: {', '.join(firm.known_competitors[:2]):<57}" + " " * (20 - len(', '.join(firm.known_competitors[:2]))) + "│")
            
        print(f"└{'─' * 78}┘")
        
    def display_bot_frequency_map(self):
        """Display frequency spectrum of all bots."""
        print("\n" + "=" * 80)
        print(" " * 25 + "📊 BOT FREQUENCY SPECTRUM 📊")
        print("=" * 80)
        
        # Collect all frequencies
        freq_map = {}  # frequency_range -> [firms]
        
        for firm in self.firms.values():
            for sig in firm.bot_signatures:
                key = f"{sig.frequency_range[0]:.1f}-{sig.frequency_range[1]:.1f}Hz"
                if key not in freq_map:
                    freq_map[key] = []
                freq_map[key].append((firm.name, sig.strategies))
                
        # Sort by frequency
        sorted_freqs = sorted(freq_map.items(), key=lambda x: float(x[0].split('-')[0]))
        
        print("\n┌" + "─" * 78 + "┐")
        print("│ Frequency Range │ Firms Using This Range" + " " * 39 + "│")
        print("├" + "─" * 16 + "┼" + "─" * 61 + "┤")
        
        for freq_range, firms in sorted_freqs:
            print(f"│ {freq_range:<15} │ {len(firms)} firms" + " " * 51 + "│")
            for firm_name, strategies in firms[:2]:  # Show first 2
                strat_str = ', '.join(strategies[:2])
                print(f"│                 │   {firm_name:<35} ({strat_str})" + " " * (21 - min(21, len(strat_str))) + "│")
                
        print("└" + "─" * 16 + "┴" + "─" * 61 + "┘")
        
    def display_geographic_distribution(self):
        """Display firms by geographic location."""
        print("\n" + "=" * 80)
        print(" " * 25 + "🌍 GEOGRAPHIC DISTRIBUTION 🌍")
        print("=" * 80)
        
        # Collect cities
        city_map = {}  # city -> [firms]
        
        for firm in self.firms.values():
            for office in firm.offices:
                city_key = f"{office.city}, {office.country}"
                if city_key not in city_map:
                    city_map[city_key] = []
                city_map[city_key].append(firm.name)
                
        # Sort by number of firms
        sorted_cities = sorted(city_map.items(), key=lambda x: len(x[1]), reverse=True)
        
        print("\n┌" + "─" * 78 + "┐")
        print("│ Location" + " " * 30 + "│ # Firms │ Notable Firms" + " " * 29 + "│")
        print("├" + "─" * 39 + "┼" + "─" * 9 + "┼" + "─" * 29 + "┤")
        
        for city, firms in sorted_cities[:15]:  # Top 15
            firms_str = ', '.join(firms[:2])
            if len(firms) > 2:
                firms_str += f" +{len(firms)-2} more"
            print(f"│ {city:<37} │ {len(firms):>7} │ {firms_str:<27} │")
            
        print("└" + "─" * 39 + "┴" + "─" * 9 + "┴" + "─" * 29 + "┘")
        
    def export_all_firms_json(self, output_file: str = "all_firms_database.json"):
        """Export all firms to JSON."""
        from dataclasses import asdict
        
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'total_firms': len(self.firms),
            'firms': {}
        }
        
        for firm_id, firm in self.firms.items():
            export_data['firms'][firm_id] = asdict(firm)
            
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)
            
        logger.info(f"📊 Exported {len(self.firms)} firms to {output_file}")
        print(f"\n✅ Exported {len(self.firms)} firms to {output_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='All Firms Bot Viewer')
    parser.add_argument('--summary', action='store_true', help='Show summary only')
    parser.add_argument('--detailed', action='store_true', help='Show detailed view of all firms')
    parser.add_argument('--frequency', action='store_true', help='Show frequency spectrum')
    parser.add_argument('--geographic', action='store_true', help='Show geographic distribution')
    parser.add_argument('--export', type=str, help='Export to JSON file')
    parser.add_argument('--all', action='store_true', help='Show everything')
    
    args = parser.parse_args()
    
    viewer = AllFirmsBotViewer()
    
    if args.export:
        viewer.export_all_firms_json(args.export)
        return
        
    if args.all or (not args.summary and not args.detailed and not args.frequency and not args.geographic):
        # Show everything
        viewer.display_summary()
        viewer.display_geographic_distribution()
        viewer.display_bot_frequency_map()
        viewer.display_all_firms_detailed()
    else:
        if args.summary:
            viewer.display_summary()
        if args.geographic:
            viewer.display_geographic_distribution()
        if args.frequency:
            viewer.display_bot_frequency_map()
        if args.detailed:
            viewer.display_all_firms_detailed()


if __name__ == '__main__':
    main()
