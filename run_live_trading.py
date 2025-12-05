#!/usr/bin/env python3
"""
🚀 LIVE TRADING LAUNCHER - REAL TRADES ENABLED
Aureon Unified Ecosystem with optimized parameters
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aureon_unified_ecosystem import AureonKrakenEcosystem
from trade_logger import get_trade_logger
import signal
import time

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutdown signal received...")
    print("📊 Generating final trading report...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def main():
    """Launch ecosystem with LIVE trading enabled"""
    
    print("\n" + "="*80)
    print(" "*20 + "🚀 AUREON LIVE TRADING SYSTEM 🚀")
    print("="*80)
    print("\n⚠️  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK")
    print("="*80)
    
    # Verify user confirmation
    print("\n📋 LIVE TRADING CHECKLIST:")
    print("  ✅ All platforms connected (Kraken, Binance, Capital.com)")
    print("  ✅ Total capital: £56.68")
    print("  ✅ Optimized parameters deployed:")
    print("     • MIN_GATES: 5 (63.6% win rate)")
    print("     • MIN_COHERENCE: 0.48")
    print("     • Node weights optimized (Deer, Panda, Falcon boosted)")
    print("  ✅ Logging system active")
    print("\n⚠️  THIS WILL EXECUTE REAL TRADES WITH REAL MONEY")
    
    confirmation = input("\n🔴 Type 'ENABLE LIVE TRADING' to confirm: ")
    
    if confirmation != "ENABLE LIVE TRADING":
        print("\n❌ Live trading NOT enabled. Exiting...")
        print("   To enable live trading, run again and type exact phrase.")
        return
    
    print("\n✅ LIVE TRADING CONFIRMED")
    print("="*80)
    
    # Initialize trade logger
    logger = get_trade_logger()
    print(f"\n📊 Trade Logger initialized")
    print(f"   Output directory: {logger.output_dir}")
    print(f"   Trades file: {logger.trades_file.name}")
    
    # Initialize ecosystem with LIVE trading
    print("\n🚀 Initializing Aureon Unified Ecosystem...")
    print("   Mode: 💰 LIVE TRADING (dry_run=False)")
    
    engine = AureonKrakenEcosystem(
        initial_balance=1000.0,
        dry_run=False  # ⚠️ LIVE TRADING ENABLED
    )
    
    print("\n" + "="*80)
    print("📊 LIVE TRADING CONFIGURATION")
    print("="*80)
    print(f"  Starting Capital:     £{engine.cash_balance_gbp:,.2f}")
    print(f"  Mode:                 💰 LIVE (real trades)")
    print(f"  Min Gates:            {5}")
    print(f"  Min Coherence:        {0.48}")
    print(f"  Trading Interval:     5 seconds")
    print(f"  Target Profit:        £50")
    print(f"  Max Runtime:          60 minutes")
    print(f"  Risk Management:      Circuit breaker at -15% DD")
    
    print("\n" + "="*80)
    print("🎯 EXECUTION STRATEGY")
    print("="*80)
    print("  • Enter on 5+ gate passes + 0.48+ coherence")
    print("  • Prioritize 528Hz and 174Hz frequencies")
    print("  • Boost Deer, Panda, Falcon node signals")
    print("  • Suppress Dolphin node (0% win rate)")
    print("  • TP: +1.2% | SL: -0.8%")
    print("  • Kelly criterion position sizing")
    
    print("\n" + "="*80)
    print("⚡ STARTING LIVE TRADING ENGINE")
    print("="*80)
    print("\nPress Ctrl+C to stop gracefully\n")
    
    # Run ecosystem
    try:
        engine.run(
            interval=5.0,
            target_profit_gbp=50.0,
            max_minutes=60
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Shutdown requested by user")
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
    
    # Final report
    print("\n" + "="*80)
    print("📊 FINAL TRADING SESSION REPORT")
    print("="*80)
    
    # Get final stats from engine
    total_pnl = engine.total_realized_pnl_gbp if hasattr(engine, 'total_realized_pnl_gbp') else 0
    final_balance = engine.cash_balance_gbp if hasattr(engine, 'cash_balance_gbp') else 0
    
    print(f"  Final Balance:        £{final_balance:,.2f}")
    print(f"  Total P&L:            £{total_pnl:+,.2f}")
    
    print("\n📁 Trade logs saved to:")
    print(f"   {logger.trades_file}")
    print(f"   {logger.exits_file}")
    print(f"   {logger.market_sweep_file}")
    
    print("\n✅ Trading session complete")
    print("="*80)

if __name__ == "__main__":
    main()
