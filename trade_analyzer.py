#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🔍 TRADE DATA ANALYZER & PROBABILITY MATRIX VALIDATOR 🔍                         ║
║     ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                               ║
║                                                                                      ║
║     Cross-reference trader data to validate:                                         ║
║       • Full market sweep completeness                                               ║
║       • Probability matrix accuracy (1m/5m outcomes)                                 ║
║       • HNC frequency correlation with profits                                       ║
║       • Gate effectiveness analysis                                                  ║
║       • Training data generation for ML models                                       ║
║                                                                                      ║
║     Output: Analytics reports, visualizations, training datasets                    ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)

class TradeDataAnalyzer:
    """Analyze logged trade data for validation and ML training"""
    
    def __init__(self, trades_file: str, exits_file: str, validations_file: str = None):
        self.trades_file = Path(trades_file)
        self.exits_file = Path(exits_file)
        self.validations_file = Path(validations_file) if validations_file else None
        
        self.trades: Dict = {}
        self.exits: Dict = {}
        self.validations: List = []
        
        self._load_data()
    
    def _load_data(self):
        """Load all logged data into memory"""
        # Load trades
        if self.trades_file.exists():
            with open(self.trades_file) as f:
                for line in f:
                    data = json.loads(line)
                    trade_id = data.get('trade_id', '')
                    self.trades[trade_id] = data
        
        # Load exits
        if self.exits_file.exists():
            with open(self.exits_file) as f:
                for line in f:
                    data = json.loads(line)
                    trade_id = data.get('trade_id', '')
                    self.exits[trade_id] = data
        
        # Load validations
        if self.validations_file and self.validations_file.exists():
            with open(self.validations_file) as f:
                self.validations = [json.loads(line) for line in f]
        
        logger.info(f"📂 Loaded {len(self.trades)} trades, {len(self.exits)} exits, {len(self.validations)} validations")
    
    def get_market_sweep_completeness(self) -> Dict:
        """Verify full market sweep coverage"""
        # Group trades by time window
        time_windows = defaultdict(list)
        
        for trade_id, trade_data in self.trades.items():
            timestamp = trade_data.get('entry_time', 0)
            window = int(timestamp / 300) * 300  # 5-minute windows
            time_windows[window].append(trade_data)
        
        # Analyze coverage
        sweep_stats = {
            'total_time_windows': len(time_windows),
            'total_trades': len(self.trades),
            'avg_trades_per_window': len(self.trades) / len(time_windows) if time_windows else 0,
            'symbols_traded': list(set(t.get('symbol') for t in self.trades.values())),
            'time_windows': {}
        }
        
        for window, trades in sorted(time_windows.items()):
            sweep_stats['time_windows'][str(window)] = len(trades)
        
        return sweep_stats
    
    def get_probability_accuracy(self) -> Dict:
        """Measure probability matrix prediction accuracy"""
        if not self.validations:
            return {'error': 'No validation data available'}
        
        accuracy_stats = {
            'total_predictions': len(self.validations),
            'by_frequency': defaultdict(lambda: {'correct': 0, 'total': 0}),
            'by_coherence': defaultdict(lambda: {'correct': 0, 'total': 0}),
            'by_action': defaultdict(lambda: {'correct': 0, 'total': 0}),
            'validation_1m_accuracy': 0.0,
            'validation_5m_accuracy': 0.0,
        }
        
        for val in self.validations:
            frequency = val.get('frequency_band', 'UNKNOWN')
            coherence = val.get('coherence_level', 'UNKNOWN')
            action = val.get('predicted_action', 'HOLD')
            outcome = val.get('actual_outcome', 'UNKNOWN')
            
            # Check if prediction was correct
            is_correct = (action == 'BUY' and outcome == 'WIN') or (action == 'SELL' and outcome == 'LOSS') or (action == 'HOLD' and outcome == 'HOLD')
            
            accuracy_stats['by_frequency'][frequency]['total'] += 1
            accuracy_stats['by_coherence'][coherence]['total'] += 1
            accuracy_stats['by_action'][action]['total'] += 1
            
            if is_correct:
                accuracy_stats['by_frequency'][frequency]['correct'] += 1
                accuracy_stats['by_coherence'][coherence]['correct'] += 1
                accuracy_stats['by_action'][action]['correct'] += 1
            
            # Check 1m/5m validation
            if val.get('validation_1m'):
                accuracy_stats['validation_1m_accuracy'] += 1
            if val.get('validation_5m'):
                accuracy_stats['validation_5m_accuracy'] += 1
        
        # Calculate percentages
        for key in accuracy_stats['by_frequency']:
            total = accuracy_stats['by_frequency'][key]['total']
            correct = accuracy_stats['by_frequency'][key]['correct']
            accuracy_stats['by_frequency'][key]['accuracy'] = (correct / total * 100) if total > 0 else 0
        
        for key in accuracy_stats['by_coherence']:
            total = accuracy_stats['by_coherence'][key]['total']
            correct = accuracy_stats['by_coherence'][key]['correct']
            accuracy_stats['by_coherence'][key]['accuracy'] = (correct / total * 100) if total > 0 else 0
        
        for key in accuracy_stats['by_action']:
            total = accuracy_stats['by_action'][key]['total']
            correct = accuracy_stats['by_action'][key]['correct']
            accuracy_stats['by_action'][key]['accuracy'] = (correct / total * 100) if total > 0 else 0
        
        accuracy_stats['validation_1m_accuracy'] = (accuracy_stats['validation_1m_accuracy'] / len(self.validations) * 100) if self.validations else 0
        accuracy_stats['validation_5m_accuracy'] = (accuracy_stats['validation_5m_accuracy'] / len(self.validations) * 100) if self.validations else 0
        
        return dict(accuracy_stats)
    
    def get_frequency_profitability(self) -> Dict:
        """Analyze which HNC frequencies are most profitable"""
        frequency_stats = defaultdict(lambda: {'pnl': [], 'wins': 0, 'losses': 0})
        
        for trade_id, exit_data in self.exits.items():
            if trade_id in self.trades:
                trade_data = self.trades[trade_id]
                frequency = trade_data.get('hnc_frequency', 0)
                net_pnl = exit_data.get('net_pnl', 0)
                
                frequency_stats[frequency]['pnl'].append(net_pnl)
                if net_pnl > 0:
                    frequency_stats[frequency]['wins'] += 1
                else:
                    frequency_stats[frequency]['losses'] += 1
        
        # Calculate stats per frequency
        profitability = {}
        for freq, data in frequency_stats.items():
            total_pnl = sum(data['pnl'])
            avg_pnl = statistics.mean(data['pnl']) if data['pnl'] else 0
            total_trades = len(data['pnl'])
            win_rate = (data['wins'] / total_trades * 100) if total_trades > 0 else 0
            
            profitability[str(freq)] = {
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'wins': data['wins'],
                'losses': data['losses'],
            }
        
        return profitability
    
    def get_node_performance(self) -> Dict:
        """Analyze performance by dominant node"""
        node_stats = defaultdict(lambda: {'pnl': [], 'coherence': [], 'wins': 0, 'losses': 0})
        
        for trade_id, exit_data in self.exits.items():
            if trade_id in self.trades:
                trade_data = self.trades[trade_id]
                node = trade_data.get('dominant_node', 'Unknown')
                net_pnl = exit_data.get('net_pnl', 0)
                coherence = trade_data.get('coherence', 0)
                
                node_stats[node]['pnl'].append(net_pnl)
                node_stats[node]['coherence'].append(coherence)
                if net_pnl > 0:
                    node_stats[node]['wins'] += 1
                else:
                    node_stats[node]['losses'] += 1
        
        # Calculate stats per node
        performance = {}
        for node, data in node_stats.items():
            total_pnl = sum(data['pnl'])
            avg_pnl = statistics.mean(data['pnl']) if data['pnl'] else 0
            avg_coherence = statistics.mean(data['coherence']) if data['coherence'] else 0
            total_trades = len(data['pnl'])
            win_rate = (data['wins'] / total_trades * 100) if total_trades > 0 else 0
            
            performance[node] = {
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'avg_coherence': avg_coherence,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'wins': data['wins'],
                'losses': data['losses'],
            }
        
        return performance
    
    def get_gate_effectiveness(self) -> Dict:
        """Analyze how effective gate thresholds are"""
        gate_stats = defaultdict(lambda: {'pnl': [], 'wins': 0, 'losses': 0})
        
        for trade_id, exit_data in self.exits.items():
            if trade_id in self.trades:
                trade_data = self.trades[trade_id]
                gates = trade_data.get('gates_passed', 0)
                net_pnl = exit_data.get('net_pnl', 0)
                
                gate_stats[gates]['pnl'].append(net_pnl)
                if net_pnl > 0:
                    gate_stats[gates]['wins'] += 1
                else:
                    gate_stats[gates]['losses'] += 1
        
        # Calculate stats per gate level
        effectiveness = {}
        for gates, data in sorted(gate_stats.items()):
            total_pnl = sum(data['pnl'])
            avg_pnl = statistics.mean(data['pnl']) if data['pnl'] else 0
            total_trades = len(data['pnl'])
            win_rate = (data['wins'] / total_trades * 100) if total_trades > 0 else 0
            
            effectiveness[str(gates)] = {
                'total_pnl': total_pnl,
                'avg_pnl': avg_pnl,
                'total_trades': total_trades,
                'win_rate': win_rate,
                'wins': data['wins'],
                'losses': data['losses'],
            }
        
        return effectiveness
    
    def generate_report(self, output_file: str = None) -> str:
        """Generate comprehensive analysis report"""
        if output_file is None:
            output_file = f"/tmp/trade_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': {
                'total_trades': len(self.trades),
                'completed_trades': len(self.exits),
                'pending_trades': len(self.trades) - len(self.exits),
            },
            'market_sweep_completeness': self.get_market_sweep_completeness(),
            'probability_accuracy': self.get_probability_accuracy(),
            'frequency_profitability': self.get_frequency_profitability(),
            'node_performance': self.get_node_performance(),
            'gate_effectiveness': self.get_gate_effectiveness(),
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Report generated: {output_file}")
        return output_file
    
    def print_summary(self):
        """Print summary to console"""
        print("\n" + "="*80)
        print("🔍 TRADE DATA ANALYSIS SUMMARY 🔍".center(80))
        print("="*80)
        
        print(f"\n📈 TRADE STATISTICS:")
        print(f"   Total Trades: {len(self.trades)}")
        print(f"   Completed: {len(self.exits)}")
        print(f"   Pending: {len(self.trades) - len(self.exits)}")
        
        # Calculate P&L
        total_pnl = sum(e.get('net_pnl', 0) for e in self.exits.values())
        wins = sum(1 for e in self.exits.values() if e.get('net_pnl', 0) > 0)
        print(f"\n💰 PROFITABILITY:")
        print(f"   Total P&L: ${total_pnl:+.2f}")
        print(f"   Wins: {wins}/{len(self.exits)} ({wins/len(self.exits)*100:.1f}%)" if self.exits else "   No completed trades")
        
        # Frequency analysis
        freq_prof = self.get_frequency_profitability()
        if freq_prof:
            print(f"\n🔊 FREQUENCY ANALYSIS:")
            for freq in sorted(freq_prof.keys(), key=lambda x: float(x)):
                data = freq_prof[freq]
                print(f"   {freq}Hz: P&L ${data['total_pnl']:+.2f} | Win Rate {data['win_rate']:.1f}% | {data['total_trades']} trades")
        
        # Node performance
        node_perf = self.get_node_performance()
        if node_perf:
            print(f"\n🎯 NODE PERFORMANCE:")
            for node in sorted(node_perf.keys()):
                data = node_perf[node]
                print(f"   {node}: P&L ${data['total_pnl']:+.2f} | Win Rate {data['win_rate']:.1f}% | Γ {data['avg_coherence']:.2f}")
        
        # Gate effectiveness
        gate_eff = self.get_gate_effectiveness()
        if gate_eff:
            print(f"\n🚪 GATE EFFECTIVENESS:")
            for gates in sorted(gate_eff.keys(), key=lambda x: int(x)):
                data = gate_eff[gates]
                print(f"   {gates} Gates: P&L ${data['total_pnl']:+.2f} | Win Rate {data['win_rate']:.1f}% | {data['total_trades']} trades")
        
        print("\n" + "="*80 + "\n")

if __name__ == '__main__':
    # Example usage
    import sys
    
    if len(sys.argv) > 1:
        trades_file = sys.argv[1]
        exits_file = sys.argv[2] if len(sys.argv) > 2 else trades_file.replace('trades_', 'exits_')
        validations_file = sys.argv[3] if len(sys.argv) > 3 else None
        
        analyzer = TradeDataAnalyzer(trades_file, exits_file, validations_file)
        analyzer.print_summary()
        analyzer.generate_report()
    else:
        print("Usage: python trade_analyzer.py <trades_file> [exits_file] [validations_file]")
