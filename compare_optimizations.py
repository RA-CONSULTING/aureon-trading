#!/usr/bin/env python3
"""
Compare baseline vs optimized ecosystem performance
Loads both trade datasets and validates improvements
"""

import json
from pathlib import Path
from collections import defaultdict

def load_trades(trades_file, exits_file):
    """Load and merge entry/exit JSONL data"""
    entries = {}
    try:
        with open(trades_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    entry = json.loads(line)
                    entries[entry['trade_id']] = entry
    except FileNotFoundError:
        pass
    
    exits = {}
    try:
        with open(exits_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    exit_data = json.loads(line)
                    exits[exit_data['trade_id']] = exit_data
    except FileNotFoundError:
        pass
    
    # Merge: each exit gets entry data
    merged = []
    for tid, exit_data in exits.items():
        if tid in entries:
            entry = entries[tid]
            merged_record = {**entry, **exit_data}
            merged.append(merged_record)
    
    return merged

def analyze_trades(merged_data, label):
    """Analyze trade performance metrics"""
    if not merged_data:
        print(f"❌ {label}: No trades found")
        return None
    
    print(f"\n{'='*70}")
    print(f"📊 {label}")
    print(f"{'='*70}")
    
    print(f"Total Trades: {len(merged_data)}")
    
    # P&L analysis
    total_pnl = sum(t.get('net_pnl', 0) for t in merged_data)
    wins = sum(1 for t in merged_data if t.get('net_pnl', 0) > 0)
    win_rate = (wins / len(merged_data) * 100) if merged_data else 0
    
    print(f"\n💰 PROFITABILITY:")
    print(f"  Total P&L: ${total_pnl:+.2f}")
    print(f"  Wins: {wins}/{len(merged_data)} ({win_rate:.1f}%)")
    
    # Frequency analysis
    freq_data = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'wins': 0})
    for trade in merged_data:
        freq = trade.get('hnc_frequency', 'unknown')
        freq_data[freq]['trades'] += 1
        freq_data[freq]['pnl'] += trade.get('net_pnl', 0)
        if trade.get('net_pnl', 0) > 0:
            freq_data[freq]['wins'] += 1
    
    print(f"\n🔊 TOP FREQUENCIES:")
    sorted_freqs = sorted(freq_data.items(), key=lambda x: x[1]['pnl'], reverse=True)[:3]
    for freq, data in sorted_freqs:
        wr = (data['wins']/data['trades']*100) if data['trades'] > 0 else 0
        print(f"  {freq}Hz: ${data['pnl']:+.2f} | {wr:.0f}% WR | {data['trades']} trades")
    
    # Node analysis
    node_data = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'wins': 0})
    for trade in merged_data:
        node = trade.get('dominant_node', 'unknown')
        node_data[node]['trades'] += 1
        node_data[node]['pnl'] += trade.get('net_pnl', 0)
        if trade.get('net_pnl', 0) > 0:
            node_data[node]['wins'] += 1
    
    print(f"\n🎯 TOP NODES:")
    sorted_nodes = sorted(node_data.items(), key=lambda x: x[1]['pnl'], reverse=True)[:3]
    for node, data in sorted_nodes:
        wr = (data['wins']/data['trades']*100) if data['trades'] > 0 else 0
        print(f"  {node}: ${data['pnl']:+.2f} | {wr:.0f}% WR | {data['trades']} trades")
    
    # Gate effectiveness
    gates_data = defaultdict(lambda: {'trades': 0, 'pnl': 0, 'wins': 0})
    for trade in merged_data:
        gates = trade.get('gates_passed', 0)
        gates_data[gates]['trades'] += 1
        gates_data[gates]['pnl'] += trade.get('net_pnl', 0)
        if trade.get('net_pnl', 0) > 0:
            gates_data[gates]['wins'] += 1
    
    print(f"\n🚪 GATE EFFECTIVENESS:")
    for gates in sorted(gates_data.keys()):
        data = gates_data[gates]
        wr = (data['wins']/data['trades']*100) if data['trades'] > 0 else 0
        print(f"  {gates} gates: ${data['pnl']:+.2f} | {wr:.0f}% WR | {data['trades']} trades")
    
    return {
        'total_pnl': total_pnl,
        'win_rate': win_rate,
        'exit_count': len(merged_data),
        'frequencies': freq_data,
        'nodes': node_data,
        'gates': gates_data
    }

# Load data
baseline_exits = load_trades(
    "/tmp/aureon_trade_logs/trades_20251204_232543.jsonl",
    "/tmp/aureon_trade_logs/exits_20251204_232543.jsonl"
)
optimized_exits = load_trades(
    "/tmp/aureon_trade_logs/trades_20251205_002718.jsonl",
    "/tmp/aureon_trade_logs/exits_20251205_002718.jsonl"
)

# Analyze
baseline_stats = analyze_trades(baseline_exits, "BASELINE (MIN_GATES=2, MIN_COH=0.45)")
optimized_stats = analyze_trades(optimized_exits, "OPTIMIZED (MIN_GATES=5, MIN_COH=0.48)")

# Compare
if baseline_stats and optimized_stats:
    print(f"\n{'='*70}")
    print(f"🎯 OPTIMIZATION RESULTS")
    print(f"{'='*70}")
    
    pnl_improvement = ((optimized_stats['total_pnl'] - baseline_stats['total_pnl']) / abs(baseline_stats['total_pnl']) * 100) if baseline_stats['total_pnl'] != 0 else 0
    wr_improvement = optimized_stats['win_rate'] - baseline_stats['win_rate']
    
    print(f"P&L Change: {pnl_improvement:+.1f}% (${baseline_stats['total_pnl']:+.2f} → ${optimized_stats['total_pnl']:+.2f})")
    print(f"Win Rate Change: {wr_improvement:+.1f}% ({baseline_stats['win_rate']:.1f}% → {optimized_stats['win_rate']:.1f}%)")
    print(f"Exit Trades: {baseline_stats['exit_count']} → {optimized_stats['exit_count']}")
