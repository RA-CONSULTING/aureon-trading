#!/usr/bin/env python3
"""
🔴 AUREON LIVE WHALE PROFILER 🔴
=================================

LIVE INTEGRATION of all profiling systems:
├─ Reads Bot Shape Scanner detections
├─ Creates/updates whale profiles in real-time
├─ Tracks 24-hour activity
├─ Generates complete intelligence reports
└─ Displays active whales with full attribution

DISPLAYS:
┌─────────────────────────────────────────────────────────────────┐
│ 🦈 LIVE WHALE TRACKING - 3 Active Whales                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│ 1. Singapore Shark HFT (WH00237)                                │
│    ├─ Firm: Jump Trading (Singapore)                           │
│    ├─ Target: ETHUSDT (HFT_ALGO 4.03Hz)                        │
│    ├─ 24h: $2.3M bought, $1.8M sold, +$524K PnL                │
│    └─ Status: ACTIVE | Last seen: 2s ago                       │
│                                                                 │
│ 2. London Mega Spoofer (WH00184)                                │
│    ├─ Firm: Wintermute (London)                                │
│    ├─ Target: SOLUSDT (MM_SPOOF 0.77Hz)                        │
│    ├─ 24h: $890K bought, $1.2M sold, +$310K PnL                │
│    └─ Status: ACTIVE | Last seen: 45s ago                      │
│                                                                 │
│ 3. New York HFT (WH00092)                                       │
│    ├─ Firm: Citadel Securities (New York)                      │
│    ├─ Target: BTCUSDT (HFT_ALGO 3.21Hz)                        │
│    ├─ 24h: $5.4M bought, $5.1M sold, +$300K PnL                │
│    └─ Status: ACTIVE | Last seen: 12s ago                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

Gary Leckey | January 2026 | Live Whale Tracking
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import logging
from pathlib import Path
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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import profiling systems
try:
    from aureon_complete_profiler_integration import (
        get_complete_profiler, CompleteIntelligenceReport
    )
except ImportError as e:
    logger.error(f"Failed to import profiler: {e}")
    sys.exit(1)


class LiveWhaleProfiler:
    """
    🔴 LIVE WHALE PROFILER 🔴
    
    Monitors bot detections and creates real-time whale profiles.
    """
    
    def __init__(
        self,
        bot_scanner_state_file: str = "bot_shape_scanner_state.json",
        update_interval: int = 10  # seconds
    ):
        self.bot_scanner_state_file = Path(bot_scanner_state_file)
        self.update_interval = update_interval
        self.profiler = get_complete_profiler()
        
        # Track processed detections
        self.last_processed_time = time.time() - 3600  # Start 1 hour ago
        self.profile_map: Dict[str, str] = {}  # (exchange, symbol, bot_class) -> profile_id
        
        logger.info(f"🔴 Live Whale Profiler initialized")
        
    def read_bot_scanner_state(self) -> Dict:
        """Read latest bot scanner detections."""
        if not self.bot_scanner_state_file.exists():
            return {}
            
        try:
            with open(self.bot_scanner_state_file) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read bot scanner state: {e}")
            return {}
            
    def process_new_detections(self) -> int:
        """
        🤖 PROCESS NEW BOT DETECTIONS 🤖
        
        Read bot scanner state and create/update profiles.
        
        Returns: Number of profiles updated
        """
        state = self.read_bot_scanner_state()
        if not state:
            return 0
            
        updated_count = 0
        
        # Process each symbol's bot detections
        for symbol, symbol_data in state.items():
            if not isinstance(symbol_data, dict):
                continue
                
            # Get advanced classification if available
            advanced = symbol_data.get('advanced_classification', {})
            if not advanced:
                continue
                
            bot_class = advanced.get('class', 'UNKNOWN')
            frequency = advanced.get('frequency', 0.0)
            activities = symbol_data.get('activity_count', 0)
            confidence = symbol_data.get('confidence', 0.0)
            
            if bot_class == 'UNKNOWN' or frequency == 0:
                continue
                
            # Check if we've already processed this
            key = f"binance:{symbol}:{bot_class}"
            
            if key in self.profile_map:
                # Update existing profile
                profile_id = self.profile_map[key]
                self.profiler.whale_profiler.update_profile(
                    profile_id,
                    symbol=symbol,
                    action="watching",
                    volume_usd=activities * 100  # Rough estimate
                )
                updated_count += 1
            else:
                # Create new profile
                profile_id = self.profiler.process_bot_detection(
                    exchange="binance",
                    symbol=symbol,
                    bot_class=bot_class,
                    frequency=frequency,
                    activities=activities,
                    confidence=confidence
                )
                self.profile_map[key] = profile_id
                updated_count += 1
                logger.info(f"🆕 New whale profile created: {profile_id} for {symbol}")
                
        return updated_count
        
    def display_active_whales(self, max_display: int = 10) -> None:
        """
        📊 DISPLAY ACTIVE WHALES 📊
        
        Show summary of all active whale profiles.
        """
        reports = self.profiler.get_all_active_reports(min_confidence=0.5)
        
        if not reports:
            print("\n🔴 No active whales detected")
            return
            
        # Sort by net PnL descending
        reports.sort(key=lambda r: r.net_pnl, reverse=True)
        
        print("\n┌" + "─" * 67 + "┐")
        print(f"│ 🦈 LIVE WHALE TRACKING - {len(reports)} Active Whales" + " " * (44 - len(str(len(reports)))) + "│")
        print("├" + "─" * 67 + "┤")
        print("│" + " " * 67 + "│")
        
        for i, report in enumerate(reports[:max_display], 1):
            # Time since last seen
            if report.last_seen_seconds < 60:
                time_str = f"{report.last_seen_seconds}s ago"
            elif report.last_seen_seconds < 3600:
                time_str = f"{report.last_seen_seconds//60}m ago"
            else:
                time_str = f"{report.last_seen_seconds//3600}h ago"
                
            print(f"│ {i}. {report.nickname} ({report.profile_id})" + " " * (57 - len(str(i)) - len(report.nickname) - len(report.profile_id)) + "│")
            
            if report.firm:
                firm_str = f"{report.firm} ({report.office})" if report.office else report.firm
                print(f"│    ├─ Firm: {firm_str}" + " " * (53 - len(firm_str)) + "│")
                
            target_str = f"{report.primary_target} ({report.bot_type} {report.bot_frequency:.2f}Hz)"
            print(f"│    ├─ Target: {target_str}" + " " * (49 - len(target_str)) + "│")
            
            pnl_str = f"${abs(report.bought_usd):,.0f} bought, ${abs(report.sold_usd):,.0f} sold, {'+' if report.net_pnl >= 0 else ''}${abs(report.net_pnl):,.0f} PnL"
            print(f"│    ├─ 24h: {pnl_str}" + " " * (54 - len(pnl_str)) + "│")
            
            status_str = f"{report.status} | Last seen: {time_str}"
            print(f"│    └─ Status: {status_str}" + " " * (47 - len(status_str)) + "│")
            print("│" + " " * 67 + "│")
            
        print("└" + "─" * 67 + "┘")
        
    def display_detailed_report(self, profile_id: str) -> None:
        """Display detailed intelligence report for a specific whale."""
        report = self.profiler.get_complete_intelligence_report(profile_id)
        if report:
            print("\n" + self.profiler.format_complete_report(report))
        else:
            print(f"\n❌ Profile {profile_id} not found")
            
    def run_live_monitoring(self, duration_seconds: int = 300) -> None:
        """
        🔴 RUN LIVE MONITORING 🔴
        
        Continuously monitor and update whale profiles.
        """
        print(f"🔴 Starting live whale monitoring for {duration_seconds}s...")
        print(f"📊 Update interval: {self.update_interval}s")
        print(f"📂 Watching: {self.bot_scanner_state_file}")
        
        start_time = time.time()
        iteration = 0
        
        try:
            while time.time() - start_time < duration_seconds:
                iteration += 1
                
                # Process new detections
                updated = self.process_new_detections()
                
                # Display active whales
                print(f"\n{'='*69}")
                print(f"🔄 Update #{iteration} - {updated} profiles updated")
                print(f"{'='*69}")
                self.display_active_whales()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
            
        # Save profiles
        self.profiler.whale_profiler.save_profiles()
        print(f"\n💾 Whale profiles saved")
        
    def export_profiles_summary(self, output_file: str = "whale_profiles_summary.json") -> None:
        """Export summary of all whale profiles to JSON."""
        reports = self.profiler.get_all_active_reports(min_confidence=0.0)
        
        summary = {
            'timestamp': time.time(),
            'total_profiles': len(reports),
            'profiles': []
        }
        
        for report in reports:
            summary['profiles'].append({
                'profile_id': report.profile_id,
                'nickname': report.nickname,
                'firm': report.firm,
                'whale_class': report.whale_class,
                'strategy': report.bot_type,
                'primary_target': report.primary_target,
                'net_pnl_24h': report.net_pnl,
                'status': report.status,
                'confidence': report.primary_confidence
            })
            
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        logger.info(f"📊 Exported {len(reports)} profiles to {output_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Live Whale Profiler')
    parser.add_argument('--duration', type=int, default=300, help='Monitoring duration in seconds')
    parser.add_argument('--interval', type=int, default=10, help='Update interval in seconds')
    parser.add_argument('--export', type=str, help='Export profiles to JSON file')
    parser.add_argument('--show', type=str, help='Show detailed report for profile ID')
    
    args = parser.parse_args()
    
    profiler = LiveWhaleProfiler(update_interval=args.interval)
    
    if args.show:
        # Show detailed report for specific profile
        profiler.display_detailed_report(args.show)
    elif args.export:
        # Export and exit
        profiler.process_new_detections()
        profiler.export_profiles_summary(args.export)
    else:
        # Run live monitoring
        profiler.run_live_monitoring(duration_seconds=args.duration)


if __name__ == '__main__':
    main()
