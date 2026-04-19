#!/usr/bin/env python3
"""
🎯 FORCE TRADE DEMO - Show System Working
==========================================
Forces a small profitable trade to demonstrate the system is working.
"""
from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import asyncio
from aureon.trading.micro_profit_labyrinth import MicroProfitLabyrinth

async def force_demo_trade():
    """Force a demonstration trade"""
    print("\n" + "=" * 80)
    print("🎯 FORCING TRADE DEMONSTRATION")
    print("=" * 80)
    print("\n🔴 Initializing trading engine...")
    
    # Initialize labyrinth
    labyrinth = MicroProfitLabyrinth()
    labyrinth.dry_run = False  # LIVE MODE
    
    print("✅ Engine initialized (LIVE MODE)")
    print("\n🔍 Scanning for opportunities across ALL exchanges...")
    
    # Force a scan on all exchanges
    exchanges = ['kraken', 'binance', 'alpaca', 'capital']
    
    for exchange in exchanges:
        print(f"\n📡 Scanning {exchange.upper()}...")
        try:
            opportunities = await labyrinth.find_opportunities_for_exchange(exchange)
            
            if opportunities:
                print(f"   ✅ Found {len(opportunities)} opportunities on {exchange.upper()}")
                
                # Show top 3 opportunities
                for i, opp in enumerate(opportunities[:3], 1):
                    print(f"\n   🎯 Opportunity #{i}:")
                    print(f"      Path: {opp.from_asset} → {opp.to_asset}")
                    print(f"      Expected Profit: ${opp.expected_pnl_usd:.6f}")
                    print(f"      Score: {opp.combined_score:.2f}")
                    print(f"      Value: ${opp.from_value_usd:.2f}")
                    
                    # Ask Queen for guidance
                    if hasattr(labyrinth, 'ask_queen_will_we_win'):
                        print(f"\n      👑 Asking Queen for guidance...")
                        will_win, confidence, reason = labyrinth.ask_queen_will_we_win(
                            from_asset=opp.from_asset,
                            to_asset=opp.to_asset,
                            exchange=exchange,
                            expected_profit=opp.expected_pnl_usd,
                            from_value=opp.from_value_usd,
                            opportunity=opp
                        )
                        
                        print(f"      👑 Queen Decision: {'✅ APPROVE' if will_win else '❌ VETO'}")
                        print(f"      👑 Confidence: {confidence:.1%}")
                        print(f"      👑 Reason: {reason[:100]}")
                        
                        if will_win:
                            print(f"\n      ⚡ EXECUTING TRADE...")
                            # Execute the trade
                            result = await labyrinth.execute_conversion_on_exchange(
                                from_asset=opp.from_asset,
                                to_asset=opp.to_asset,
                                exchange=exchange,
                                opportunity=opp
                            )
                            
                            if result and result.get('success'):
                                print(f"      ✅ TRADE EXECUTED SUCCESSFULLY!")
                                print(f"      💰 Actual Profit: ${result.get('actual_profit_usd', 0):.6f}")
                                print(f"      📊 Order ID: {result.get('order_id', 'N/A')}")
                                return True
                            else:
                                print(f"      ❌ Trade failed: {result.get('error', 'Unknown error')}")
                    
            else:
                print(f"   ℹ️ No opportunities found on {exchange.upper()}")
                
        except Exception as e:
            print(f"   ⚠️ Error scanning {exchange}: {e}")
    
    print("\n" + "=" * 80)
    print("🏁 SCAN COMPLETE")
    print("=" * 80)
    return False

if __name__ == "__main__":
    print("\n🚀 Starting Force Trade Demo...")
    success = asyncio.run(force_demo_trade())
    
    if success:
        print("\n✅ DEMONSTRATION SUCCESSFUL - Trade executed!")
    else:
        print("\nℹ️  No trades executed (Queen vetoed or no opportunities)")
    
    print("\n💡 Tip: Run with --help to see all options")
