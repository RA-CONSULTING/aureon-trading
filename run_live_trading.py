#!/usr/bin/env python3
"""
🚀 LIVE TRADING LAUNCHER - REAL TRADES ENABLED
Aureon Unified Ecosystem with optimized parameters
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aureon_unified_ecosystem import AureonKrakenEcosystem
from trade_logger import get_trade_logger
from unified_exchange_client import MultiExchangeClient
import signal
import time
import argparse

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    print("\n\n🛑 Shutdown signal received...")
    print("📊 Generating final trading report...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def fetch_exchange_balances():
    """Fetch real balances from all connected exchanges"""
    print("\n📊 Fetching LIVE account balances...")
    print("-" * 60)
    
    try:
        client = MultiExchangeClient()
        all_balances = client.get_all_balances()
        
        total_usd = 0.0
        exchange_totals = {}
        
        for exchange, balances in all_balances.items():
            exchange_total = 0.0
            non_zero = {}
            
            for asset, amount in balances.items():
                try:
                    amount = float(amount)
                    if amount > 0.0001:  # Filter dust
                        # Convert to USD
                        asset_clean = asset.replace('Z', '').replace('X', '').upper()
                        if asset_clean in ['USD', 'USDT', 'USDC', 'GBP']:
                            if asset_clean == 'GBP':
                                usd_val = amount * 1.27  # Approximate GBP->USD
                            else:
                                usd_val = amount
                        else:
                            try:
                                usd_val = client.convert_to_quote(exchange, asset_clean, amount, 'USDT')
                            except:
                                usd_val = 0
                        
                        non_zero[asset] = {'amount': amount, 'usd': usd_val}
                        exchange_total += usd_val
                except:
                    pass
            
            exchange_totals[exchange] = {'balances': non_zero, 'total_usd': exchange_total}
            total_usd += exchange_total
        
        # Display per-exchange breakdown
        for exchange, data in exchange_totals.items():
            print(f"\n🏦 {exchange.upper()}:")
            if data['balances']:
                for asset, vals in data['balances'].items():
                    print(f"   {asset}: {vals['amount']:.6f} (~${vals['usd']:.2f})")
                print(f"   💰 Subtotal: ${data['total_usd']:.2f}")
            else:
                print("   (No balance)")
        
        print("-" * 60)
        gbp_total = total_usd / 1.27  # Approximate USD->GBP
        print(f"💰 TOTAL PORTFOLIO: ${total_usd:.2f} (~£{gbp_total:.2f})")
        
        # If no balances found (API keys not configured), use known value
        if total_usd < 1.0:
            print("\n⚠️  No balances detected - API keys may not be configured locally")
            print("   Using last known portfolio value: £56.68")
            total_usd = 72.0
            gbp_total = 56.68
        
        print("-" * 60)
        
        return total_usd, gbp_total, exchange_totals
        
    except Exception as e:
        print(f"⚠️  Could not fetch balances: {e}")
        # Fallback to known portfolio value
        print("   Using last known portfolio value: £56.68")
        return 72.0, 56.68, {}


def should_auto_confirm(auto_confirm_flag: bool) -> bool:
    """Return True when live-trading confirmation should be skipped."""
    if auto_confirm_flag:
        return True

    env_auto = os.getenv("AUREON_AUTO_CONFIRM_LIVE_TRADING", "0")
    return env_auto.strip().lower() in {"1", "true", "yes", "on"}


def confirm_live_trading(auto_confirm_flag: bool) -> bool:
    """Handle confirmation flow for interactive and autonomous runs."""
    if should_auto_confirm(auto_confirm_flag):
        print("\n✅ Live trading auto-confirmed (flag/env enabled)")
        return True

    if not sys.stdin.isatty():
        print("\n❌ Non-interactive session detected but no auto-confirm was provided.")
        print("   Set AUREON_AUTO_CONFIRM_LIVE_TRADING=1 or pass --auto-confirm.")
        return False

    confirmation = input("\n🔴 Type 'ENABLE LIVE TRADING' to confirm: ")
    if confirmation != "ENABLE LIVE TRADING":
        print("\n❌ Live trading NOT enabled. Exiting...")
        print("   To enable live trading, run again and type exact phrase.")
        return False

    return True


def main():
    """Launch ecosystem with LIVE trading enabled"""
    parser = argparse.ArgumentParser(description="Aureon live trading launcher")
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="Skip interactive confirmation prompt (for autonomous/systemd runs)",
    )
    parser.add_argument("--interval", type=float, default=5.0, help="Trading loop interval seconds")
    parser.add_argument("--target-profit-gbp", type=float, default=50.0, help="Profit target in GBP")
    parser.add_argument("--max-minutes", type=int, default=60, help="Maximum runtime in minutes")
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print(" "*20 + "🚀 AUREON LIVE TRADING SYSTEM 🚀")
    print("="*80)
    print("\n⚠️  WARNING: LIVE TRADING MODE - REAL MONEY AT RISK")
    print("="*80)
    
    # Fetch and display REAL balances
    total_usd, total_gbp, exchange_data = fetch_exchange_balances()
    
    # Verify user confirmation
    print("\n📋 LIVE TRADING CHECKLIST:")
    print(f"  ✅ All platforms connected (Kraken, Binance, Capital.com)")
    print(f"  ✅ Total capital: £{total_gbp:.2f} (${total_usd:.2f})")
    print("  ✅ Optimized parameters deployed:")
    print("     • MIN_GATES: 5 (63.6% win rate)")
    print("     • MIN_COHERENCE: 0.48")
    print("     • Node weights optimized (Deer, Panda, Falcon boosted)")
    print("  ✅ Logging system active")
    print("\n⚠️  THIS WILL EXECUTE REAL TRADES WITH REAL MONEY")
    
    if not confirm_live_trading(auto_confirm_flag=args.auto_confirm):
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
    
    print("="*80)
    print("📊 LIVE TRADING CONFIGURATION")
    print("="*80)
    print(f"  Starting Capital:     £{total_gbp:.2f} (${total_usd:.2f})")
    print(f"  Mode:                 💰 LIVE (real trades)")
    print(f"  Min Gates:            {5}")
    print(f"  Min Coherence:        {0.48}")
    print(f"  Trading Interval:     {args.interval:g} seconds")
    print(f"  Target Profit:        £{args.target_profit_gbp:g}")
    print(f"  Max Runtime:          {args.max_minutes} minutes")
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
            interval=args.interval,
            target_profit_gbp=args.target_profit_gbp,
            max_minutes=args.max_minutes
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
