#!/usr/bin/env python3
"""
╔════════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                        ║
║                  📊 LIVE ECOSYSTEM MONITORING DASHBOARD 📊                            ║
║                                                                                        ║
║     Real-time tracking of:                                                            ║
║       • Trade data collection progress                                                ║
║       • Frequency distribution of trades                                              ║
║       • Node performance tracking                                                     ║
║       • Market sweep validation                                                       ║
║       • Probability matrix correlation                                                ║
║                                                                                        ║
╚════════════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
from pathlib import Path
from collections import defaultdict
import statistics

def monitor_logs(log_dir="/tmp/aureon_trade_logs"):
    """Monitor trade logs in real-time"""
    
    log_dir = Path(log_dir)
    if not log_dir.exists():
        print("❌ Log directory not found")
        return
    
    # Find the latest trades file
    trades_files = sorted(log_dir.glob("trades_*.jsonl"))
    if not trades_files:
        print("❌ No trade logs found yet")
        return
    
    latest_trades_file = trades_files[-1]
    latest_exits_file = Path(str(latest_trades_file).replace("trades_", "exits_"))
    latest_sweep_file = Path(str(latest_trades_file).replace("trades_", "market_sweep_"))
    
    print("\n" + "="*80)
    print("📊 LIVE ECOSYSTEM MONITORING DASHBOARD".center(80))
    print("="*80)
    
    # Read trades
    trades = []
    if latest_trades_file.exists():
        with open(latest_trades_file) as f:
            for line in f:
                try:
                    trades.append(json.loads(line))
                except:
                    pass
    
    # Read exits
    exits = []
    if latest_exits_file.exists():
        with open(latest_exits_file) as f:
            for line in f:
                try:
                    exits.append(json.loads(line))
                except:
                    pass
    
    # Read market sweeps
    sweeps = []
    if latest_sweep_file.exists():
        with open(latest_sweep_file) as f:
            for line in f:
                try:
                    sweeps.append(json.loads(line))
                except:
                    pass
    
    print(f"\n⏱️  Last Updated: {time.strftime('%H:%M:%S')}")
    print(f"📁 Log File: {latest_trades_file.name}")
    
    # Trade Statistics
    print(f"\n📈 TRADE COLLECTION PROGRESS:")
    print(f"   • Trades Entered: {len(trades)}")
    print(f"   • Trades Exited: {len(exits)}")
    print(f"   • Pending Trades: {len(trades) - len(exits)}")
    
    if exits:
        total_pnl = sum(e.get('net_pnl', 0) for e in exits)
        wins = sum(1 for e in exits if e.get('net_pnl', 0) > 0)
        win_rate = (wins / len(exits) * 100) if exits else 0
        
        print(f"\n💰 PROFITABILITY:")
        print(f"   • Total P&L: ${total_pnl:+.2f}")
        print(f"   • Win Rate: {win_rate:.1f}% ({wins}/{len(exits)})")
        print(f"   • Avg P&L per trade: ${total_pnl/len(exits):+.2f}")
    
    # Frequency Analysis
    if trades:
        freq_dist = defaultdict(int)
        for trade in trades:
            freq = trade.get('hnc_frequency', 0)
            freq_dist[freq] += 1
        
        print(f"\n🔊 HNC FREQUENCY DISTRIBUTION:")
        for freq in sorted(freq_dist.keys()):
            count = freq_dist[freq]
            bar = "█" * min(20, count)
            print(f"   {freq:4.0f}Hz: {count:3d} trades {bar}")
    
    # Node Performance
    if trades:
        node_dist = defaultdict(lambda: {'count': 0, 'coherence': []})
        for trade in trades:
            node = trade.get('dominant_node', 'Unknown')
            node_dist[node]['count'] += 1
            node_dist[node]['coherence'].append(trade.get('coherence', 0.5))
        
        print(f"\n🎯 NODE DISTRIBUTION:")
        for node in sorted(node_dist.keys()):
            data = node_dist[node]
            avg_coherence = statistics.mean(data['coherence']) if data['coherence'] else 0
            print(f"   {node:15s}: {data['count']:3d} trades | Γ_avg: {avg_coherence:.2f}")
    
    # Market Sweep Statistics
    if sweeps:
        total_found = sum(s.get('total_opportunities_found', 0) for s in sweeps)
        total_entered = sum(s.get('opportunities_entered', 0) for s in sweeps)
        total_rejected = sum(s.get('opportunities_rejected', 0) for s in sweeps)
        avg_coherence = statistics.mean([s.get('average_coherence', 0.5) for s in sweeps])
        
        print(f"\n🌍 MARKET SWEEP ANALYSIS:")
        print(f"   • Total Opportunities Found: {total_found}")
        print(f"   • Opportunities Entered: {total_entered}")
        print(f"   • Opportunities Rejected: {total_rejected}")
        print(f"   • Entry Rate: {(total_entered/total_found*100) if total_found > 0 else 0:.1f}%")
        print(f"   • Average Coherence: {avg_coherence:.2f}")
        print(f"   • Sweeps Completed: {len(sweeps)}")
    
    # Progress toward 50+ trades goal
    target_trades = 50
    current_trades = len(trades)
    progress_pct = (current_trades / target_trades * 100) if target_trades > 0 else 0
    bar_length = 30
    filled = int(bar_length * progress_pct / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    
    print(f"\n🎯 PROGRESS TOWARD 50-TRADE COLLECTION TARGET:")
    print(f"   [{bar}] {progress_pct:.1f}% ({current_trades}/{target_trades})")
    
    if current_trades > 0:
        time_per_trade = 0.5  # Rough estimate
        remaining_trades = max(0, target_trades - current_trades)
        eta_seconds = remaining_trades * time_per_trade
        eta_minutes = eta_seconds / 60
        print(f"   ⏱️  ETA: ~{eta_minutes:.1f} minutes ({remaining_trades} trades remaining)")
    
    print("\n" + "="*80)
    print("\n✨ Dashboard updated successfully")

if __name__ == '__main__':
    monitor_logs()
