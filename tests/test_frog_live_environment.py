# -*- coding: utf-8 -*-
"""
Live Environment Quantum Frog Test
===================================

Test the frog with REAL portfolio data:
1. Load actual portfolio positions
2. Pick a position with baggage (underwater)
3. Scan for leap opportunities
4. Verify cost basis target logic is working
5. Show decision making in detail
"""

import sys
sys.path.insert(0, '/workspaces/aureon-trading')

import asyncio
import json
import logging
from pathlib import Path
from queen_eternal_machine import QueenEternalMachine
from cost_basis_tracker import CostBasisTracker

# Setup logging to see frog's decision making
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)-8s | %(name)-30s | %(message)s'
)

# Suppress noisy loggers
for logger in ['unified_ecosystem', 'aureon_queen_hive_mind', 'aureon_elephant_learning', 
               'market_data_hub', 'global_rate_budget']:
    logging.getLogger(logger).setLevel(logging.WARNING)

async def test_frog_live():
    print("\n" + "=" * 90)
    print("🐸 QUANTUM FROG LIVE ENVIRONMENT TEST")
    print("=" * 90)
    
    # Initialize frog
    print("\n📡 Initializing Quantum Frog Machine...")
    frog = QueenEternalMachine()
    
    # Fetch real market data
    print("📊 Fetching live market data...")
    frog.fetch_market_data()
    
    # Show current position
    if frog.main_position:
        print(f"\n✅ FROG'S CURRENT POSITION (before scanning):")
        print(f"   Symbol: {frog.main_position.symbol}")
        print(f"   Quantity: {frog.main_position.quantity:.2f}")
        print(f"   Cost Basis Target: ${frog.main_position.cost_basis:.2f}")
        print(f"   Current Price: ${frog.main_position.current_price:.6f}")
        print(f"   Current Value: ${frog.main_position.current_value:.2f}")
        
        loss = frog.main_position.current_value - frog.main_position.cost_basis
        loss_pct = (loss / frog.main_position.cost_basis) * 100 if frog.main_position.cost_basis > 0 else 0
        
        print(f"   P&L: ${loss:.2f} ({loss_pct:.2f}%)")
        
        if loss < 0:
            print(f"   🔴 UNDERWATER: Frog is ${abs(loss):.2f} in the red")
        else:
            print(f"   🟢 IN PROFIT: Frog is ${loss:.2f} in the green")
        
        # Show breadcrumbs (trail of past positions)
        if hasattr(frog.main_position, 'breadcrumbs') and frog.main_position.breadcrumbs:
            print(f"\n   🍞 Breadcrumb Trail ({len(frog.main_position.breadcrumbs)} positions):")
            for i, bc in enumerate(frog.main_position.breadcrumbs[-3:], 1):
                print(f"      {i}. {bc.get('symbol', 'UNKNOWN')} @ ${bc.get('value', 0):.2f}")
        
        # Now scan for leap opportunities
        print(f"\n🔍 SCANNING FOR LEAP OPPORTUNITIES...")
        print(f"   Applying cost basis target logic...")
        print(f"   Looking for positions where recovery path leads back to ${frog.main_position.cost_basis:.2f}")
        
        opportunities = frog.find_leap_opportunities()
        
        # After scanning, show updated position (price from market_data)
        print(f"\n✅ FROG'S POSITION (AFTER MARKET UPDATE):")
        print(f"   Symbol: {frog.main_position.symbol}")
        print(f"   Current Price: ${frog.main_position.current_price:.6f}")
        print(f"   Current Value: ${frog.main_position.current_value:.2f}")
        print(f"   24h Change: {frog.main_position.change_24h:.2f}%")
        
        print(f"\n📊 SCAN RESULTS:")
        print(f"   Total opportunities found: {len(opportunities)}")
        
        if opportunities:
            print(f"\n   ✅ TOP 5 LEAP OPPORTUNITIES (filtered by recovery viability):\n")
            
            for i, opp in enumerate(opportunities[:5], 1):
                print(f"   {i}. {opp.from_symbol} → {opp.to_symbol}")
                print(f"      ├─ From Price: ${opp.from_price:.4f}")
                print(f"      ├─ To Price: ${opp.to_price:.4f}")
                print(f"      ├─ 24h Change: {opp.from_change:.2f}% → {opp.to_change:.2f}%")
                print(f"      ├─ Recovery Advantage: {opp.recovery_advantage:.2f}%")
                print(f"      ├─ Fee-Adjusted Multiplier: {opp.fee_adjusted_multiplier:.4f}")
                print(f"      ├─ Gross Value: ${opp.gross_value:.2f}")
                print(f"      ├─ Total Fees: ${opp.total_fees:.2f}")
                print(f"      └─ Net After Fees: ${opp.net_value_after_fees:.2f}")
                
                # Value preservation check
                value_preserved = (opp.net_value_after_fees / opp.gross_value) * 100
                print(f"         💰 Value Preserved: {value_preserved:.2f}%")
                
                # Recovery potential assessment
                if opp.fee_adjusted_multiplier > 0.95:
                    print(f"         🟢 EXCELLENT leap (minimal fees)")
                elif opp.fee_adjusted_multiplier > 0.90:
                    print(f"         🟡 GOOD leap (acceptable fees)")
                else:
                    print(f"         🔴 MARGINAL leap (high fees)")
                print()
        else:
            print(f"\n   🧊 NO OPPORTUNITIES FOUND")
            print(f"   The frog is HOLDING and CHILLING")
            print(f"   💭 No coins have recovery runway to reach ${frog.main_position.cost_basis:.2f}")
            print(f"   💭 Better to wait for better conditions than leap to nowhere!")
        
        # Show portfolio summary
        print(f"\n💰 PORTFOLIO SUMMARY:")
        print(f"   Friends (alt positions): {len(frog.friends)}")
        print(f"   Total Friends Value: ${sum(f.quantity * f.current_price for f in frog.friends.values()):.2f}")
        
        # Show top friend positions
        if frog.friends:
            print(f"\n   🤝 TOP FRIEND POSITIONS:")
            sorted_friends = sorted(frog.friends.values(), 
                                   key=lambda x: x.quantity * x.current_price, 
                                   reverse=True)
            for friend in sorted_friends[:5]:
                value = friend.quantity * friend.current_price
                print(f"      {friend.symbol}: {friend.quantity:.2f} @ ${friend.current_price:.4f} = ${value:.2f}")
    
    else:
        print("❌ No main position found!")
    
    print("\n" + "=" * 90)
    print("TEST COMPLETE")
    print("=" * 90 + "\n")

# Run the test
if __name__ == "__main__":
    asyncio.run(test_frog_live())
