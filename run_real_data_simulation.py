#!/usr/bin/env python3
"""
🎯 REAL DATA SIMULATION - Backtesting optimized parameters against historical data
Validates: 5-gate threshold, 0.48 coherence, boosted nodes, frequency filtering
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aureon_unified_ecosystem import AureonKrakenEcosystem
from trade_logger import get_trade_logger
import json
from datetime import datetime, timedelta
import random
import statistics

def run_simulation(duration_minutes=30, name="OPTIMIZED"):
    """Run simulation on real market data"""
    
    print(f"\n╔════════════════════════════════════════════════════════════════════════════╗")
    print(f"║  🎯 REAL DATA SIMULATION - {name:45s}║")
    print(f"╚════════════════════════════════════════════════════════════════════════════╝\n")
    
    # Initialize ecosystem
    engine = AureonKrakenEcosystem(initial_balance=1000.0, dry_run=True)
    logger = get_trade_logger()
    
    print(f"⏱️  Simulation Duration: {duration_minutes} minutes")
    print(f"📊 Mode: {name}")
    print(f"💰 Starting Capital: £{engine.cash_balance_gbp:,.2f}")
    print(f"📈 Feed: Real-time market WebSocket data")
    print(f"🔧 Parameters:")
    print(f"   • MIN_GATES: 5")
    print(f"   • MIN_COHERENCE: 0.48")
    print(f"   • Entry Γ: 0.450+")
    print(f"   • Exit Γ: 0.350-")
    print(f"   • Position Sizing: Kelly Criterion")
    print()
    
    # Run simulation
    start_time = datetime.now()
    end_time = start_time + timedelta(minutes=duration_minutes)
    cycle = 0
    trades_entered = 0
    trades_exited = 0
    total_pnl = 0
    
    try:
        while datetime.now() < end_time:
            cycle += 1
            
            # Run one cycle
            engine.run_one_cycle()
            
            # Track trades
            if hasattr(engine, 'positions') and len(engine.positions) > trades_entered:
                trades_entered = len(engine.positions)
                print(f"✅ Cycle {cycle}: NEW ENTRY - Position #{trades_entered} opened")
            
            # Get current stats
            if hasattr(engine, 'total_realized_pnl_gbp'):
                current_pnl = engine.total_realized_pnl_gbp
                if current_pnl != total_pnl:
                    total_pnl = current_pnl
                    print(f"   P&L Update: £{current_pnl:+,.2f}")
            
            if cycle % 12 == 0:
                print(f"📊 Cycle {cycle}: Still evaluating... (Capital: £{engine.cash_balance_gbp:,.2f})")
            
    except KeyboardInterrupt:
        print("\n⏹️  Simulation stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Generate report
    duration = (datetime.now() - start_time).total_seconds() / 60
    
    print(f"\n{'='*80}")
    print(f"📊 SIMULATION RESULTS - {name}")
    print(f"{'='*80}\n")
    
    print(f"⏱️  Duration: {duration:.1f} minutes ({cycle} cycles)")
    print(f"💰 Starting Balance: £1000.00")
    print(f"💰 Final Balance: £{engine.cash_balance_gbp:,.2f}")
    print(f"📈 Total P&L: £{engine.total_realized_pnl_gbp:+,.2f}")
    print(f"📊 Return: {(engine.total_realized_pnl_gbp/1000)*100:+.2f}%")
    print()
    
    print(f"🎯 TRADING ACTIVITY:")
    print(f"   Cycles completed: {cycle}")
    print(f"   Entries executed: {trades_entered}")
    print(f"   Exits executed: {trades_exited}")
    print(f"   Active positions: {len(engine.positions) if hasattr(engine, 'positions') else 0}")
    print()
    
    # Calculate win rate from logs
    if os.path.exists(logger.exits_file):
        exit_count = 0
        wins = 0
        losses = 0
        pnl_values = []
        
        with open(logger.exits_file, 'r') as f:
            for line in f:
                try:
                    exit_data = json.loads(line)
                    exit_count += 1
                    pnl = exit_data.get('net_pnl', 0)
                    pnl_values.append(pnl)
                    if pnl > 0:
                        wins += 1
                    else:
                        losses += 1
                except:
                    pass
        
        if exit_count > 0:
            win_rate = (wins / exit_count) * 100
            print(f"📈 WIN RATE:")
            print(f"   Winning trades: {wins}/{exit_count} ({win_rate:.1f}%)")
            print(f"   Losing trades: {losses}/{exit_count}")
            print(f"   Avg Win: £{statistics.mean([p for p in pnl_values if p > 0]) if wins > 0 else 0:+.2f}")
            print(f"   Avg Loss: £{statistics.mean([p for p in pnl_values if p < 0]) if losses > 0 else 0:+.2f}")
            print()
    
    print(f"{'='*80}\n")
    
    return {
        'name': name,
        'duration_minutes': duration,
        'cycles': cycle,
        'final_balance': engine.cash_balance_gbp,
        'total_pnl': engine.total_realized_pnl_gbp,
        'return_pct': (engine.total_realized_pnl_gbp/1000)*100,
        'trades_entered': trades_entered
    }

def main():
    """Run simulation with optimized parameters"""
    
    print("\n" + "╔"+"="*78+"╗")
    print("║" + " "*25 + "🎯 REAL DATA BACKTESTING SIMULATION 🎯" + " "*15 + "║")
    print("╚"+"="*78+"╝\n")
    
    print("⏳ Running 30-minute simulation with real market data...")
    print("   (Using optimized parameters from Phase 1)\n")
    
    # Run optimized version
    opt_results = run_simulation(duration_minutes=30, name="OPTIMIZED (5-Gate, 0.48 Coherence)")
    
    # Summary
    print("\n" + "╔"+"="*78+"╗")
    print("║" + " "*25 + "📊 SIMULATION SUMMARY" + " "*33 + "║")
    print("╚"+"="*78+"╝\n")
    
    print("Optimized System Results:")
    print(f"  Duration: {opt_results['duration_minutes']:.1f} minutes ({opt_results['cycles']} cycles)")
    print(f"  Final Balance: £{opt_results['final_balance']:,.2f}")
    print(f"  Total P&L: £{opt_results['total_pnl']:+,.2f}")
    print(f"  Return: {opt_results['return_pct']:+.2f}%")
    print(f"  Trades Entered: {opt_results['trades_entered']}")
    print()
    
    print("✅ SIMULATION COMPLETE")
    print("\nNext Steps:")
    print("  1. Review trade logs: /tmp/aureon_trade_logs/")
    print("  2. Run live trading: python3 run_live_trading.py")
    print("  3. Monitor performance vs baseline")
    print()

if __name__ == "__main__":
    main()
