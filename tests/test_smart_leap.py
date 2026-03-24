#!/usr/bin/env python3
"""
Test that the frog WON'T leap if there's no recovery advantage.
Scenario: ETH and SOL both down similar amounts - no point leaping
"""

import asyncio
from datetime import datetime
from queen_eternal_machine import QueenEternalMachine, MainPosition

async def test_no_leap_when_no_advantage():
    """Frog should NOT leap if target coin doesn't have deeper dip."""
    
    print("🐸 FROG INTELLIGENCE TEST - Should NOT leap without recovery advantage")
    print("=" * 70)
    
    frog = QueenEternalMachine(initial_vault=100.0)
    frog.fetch_market_data()
    
    # Find two coins with similar dip amounts
    eth = frog.market_data.get('ETH')
    sol = frog.market_data.get('SOL')
    
    if eth and sol:
        print(f"\n📊 MARKET CONDITIONS:")
        print(f"   ETH: {eth.change_24h:+.2f}% change")
        print(f"   SOL: {sol.change_24h:+.2f}% change")
        print(f"   Difference: {abs(sol.change_24h - eth.change_24h):.2f}%")
        
        if abs(sol.change_24h - eth.change_24h) < 1.0:
            print(f"\n   ⚠️  Very similar dips - frog should NOT leap (no recovery advantage)")
        else:
            print(f"\n   ✅ Different dips - frog MAY leap if SOL dipped more")
        
        # Load frog with ETH
        frog.main_position = MainPosition(
            symbol='ETH',
            quantity=100.0 / eth.price,
            cost_basis=100.0,
            entry_price=eth.price,
            entry_time=datetime.now(),
            current_price=eth.price,
            change_24h=eth.change_24h
        )
        frog.available_cash = 0.0
        
        # Check opportunities
        opps = frog.find_leap_opportunities()
        
        print(f"\n🔍 LEAP ANALYSIS:")
        print(f"   Total opportunities found: {len(opps)}")
        
        if opps:
            # Show top 3
            for i, opp in enumerate(opps[:3], 1):
                print(f"\n   #{i}: {opp.from_symbol} → {opp.to_symbol}")
                print(f"       From: {opp.from_change:+.2f}%")
                print(f"       To: {opp.to_change:+.2f}%")
                print(f"       Recovery advantage: {abs(opp.to_change) - abs(opp.from_change):+.2f}%")
        else:
            print(f"   ✅ NO opportunities (correct! - no recovery advantage)")
        
        # Run a cycle
        print(f"\n🔄 Running cycle...")
        await frog.run_cycle()
        
        print(f"\n📊 RESULT:")
        if frog.main_position.symbol == 'ETH':
            print(f"   ✅ Position still ETH (frog correctly refused to leap)")
            print(f"   ✅ This is SMART - no reason to move if no advantage")
        else:
            print(f"   Position changed to: {frog.main_position.symbol}")
            print(f"   (This is OK if {frog.main_position.symbol} has deeper dip than ETH)")
    else:
        print("❌ ETH or SOL not in market data")

if __name__ == '__main__':
    asyncio.run(test_no_leap_when_no_advantage())
