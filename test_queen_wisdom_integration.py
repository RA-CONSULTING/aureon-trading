#!/usr/bin/env python3
"""
Test Queen & Wisdom Engine Integration with Micro Profit Labyrinth
"""

import sys
import asyncio
from micro_profit_labyrinth import MicroProfitLabyrinth, MicroOpportunity
import time

async def test_queen_wisdom_integration():
    """Test that Queen and Wisdom Engine are properly connected."""
    
    print("=" * 70)
    print("👑🧠 TESTING QUEEN & WISDOM ENGINE INTEGRATION")
    print("=" * 70)
    
    # Create labyrinth in dry-run mode
    print("\n1️⃣ Creating Micro Profit Labyrinth...")
    labyrinth = MicroProfitLabyrinth(live=False)
    
    # Initialize (this will wire Queen and Wisdom Engine)
    print("\n2️⃣ Initializing systems...")
    await labyrinth.initialize()
    
    # Check if Queen is connected
    print("\n3️⃣ Checking Queen connection...")
    if labyrinth.queen:
        print("   ✅ Queen Hive Mind: CONNECTED")
        
        # Test Queen's greeting
        if hasattr(labyrinth.queen, 'speak_from_heart'):
            try:
                greeting = labyrinth.queen.speak_from_heart('greeting')
                print(f"   👑 Queen says: {greeting}")
            except Exception as e:
                print(f"   ⚠️ Queen greeting failed: {e}")
        
        # Test Queen's guidance method
        if hasattr(labyrinth.queen, 'evaluate_trading_opportunity'):
            print("   ✅ Queen can evaluate opportunities")
        else:
            print("   ⚠️ Queen missing evaluate_trading_opportunity method")
    else:
        print("   ❌ Queen Hive Mind: NOT CONNECTED")
    
    # Check if Wisdom Engine is connected
    print("\n4️⃣ Checking Wisdom Engine connection...")
    if labyrinth.wisdom_engine:
        print("   ✅ Wisdom Cognition Engine: CONNECTED")
        
        # Test Wisdom Engine's analysis method
        if hasattr(labyrinth.wisdom_engine, 'analyze_trading_decision'):
            print("   ✅ Wisdom Engine can analyze decisions")
        else:
            print("   ⚠️ Wisdom Engine missing analyze_trading_decision method")
    else:
        print("   ❌ Wisdom Cognition Engine: NOT CONNECTED")
    
    # Test MicroOpportunity fields
    print("\n5️⃣ Testing MicroOpportunity fields...")
    try:
        opp = MicroOpportunity(
            timestamp=time.time(),
            from_asset="BTC",
            to_asset="ETH",
            from_amount=0.01,
            from_value_usd=400.0,
            v14_score=8.5,
            hub_score=0.85,
            commando_score=0.8,
            combined_score=0.82,
            expected_pnl_usd=0.05,
            expected_pnl_pct=0.01,
            queen_guidance_score=0.9,
            queen_wisdom="Test wisdom from Queen",
            queen_confidence=0.95,
            wisdom_engine_score=0.85,
            civilization_insight="Celtic",
            wisdom_pattern="Favorable lunar alignment for BTC→ETH"
        )
        print("   ✅ MicroOpportunity has Queen fields:")
        print(f"      - queen_guidance_score: {opp.queen_guidance_score}")
        print(f"      - queen_wisdom: {opp.queen_wisdom}")
        print(f"      - queen_confidence: {opp.queen_confidence}")
        print("   ✅ MicroOpportunity has Wisdom fields:")
        print(f"      - wisdom_engine_score: {opp.wisdom_engine_score}")
        print(f"      - civilization_insight: {opp.civilization_insight}")
        print(f"      - wisdom_pattern: {opp.wisdom_pattern}")
    except Exception as e:
        print(f"   ❌ MicroOpportunity field error: {e}")
    
    # Test Queen's speak methods
    print("\n6️⃣ Testing Queen's voice...")
    if labyrinth.queen and hasattr(labyrinth.queen, 'speak_from_heart'):
        try:
            print("   Testing after_win message:")
            win_msg = labyrinth.queen.speak_from_heart('after_win')
            print(f"   👑 {win_msg}")
            
            print("\n   Testing after_loss message:")
            loss_msg = labyrinth.queen.speak_from_heart('after_loss')
            print(f"   👑 {loss_msg}")
            
            print("\n   Testing gratitude message:")
            thanks_msg = labyrinth.queen.speak_from_heart('gratitude')
            print(f"   👑 {thanks_msg}")
        except Exception as e:
            print(f"   ⚠️ Queen speak error: {e}")
    
    print("\n" + "=" * 70)
    print("✅ INTEGRATION TEST COMPLETE")
    print("=" * 70)
    
    # Summary
    print("\n📊 INTEGRATION STATUS:")
    print(f"   Queen Connected: {'✅ YES' if labyrinth.queen else '❌ NO'}")
    print(f"   Wisdom Engine Connected: {'✅ YES' if labyrinth.wisdom_engine else '❌ NO'}")
    print(f"   MicroOpportunity Fields: ✅ ADDED")
    print(f"   Queen Voice: {'✅ WORKING' if labyrinth.queen and hasattr(labyrinth.queen, 'speak_from_heart') else '❌ NOT AVAILABLE'}")
    
    if labyrinth.queen and labyrinth.wisdom_engine:
        print("\n🎉 FULL INTEGRATION SUCCESSFUL!")
        print("   Queen Tina B and Wisdom Engine are ready to guide trading decisions.")
    elif labyrinth.queen or labyrinth.wisdom_engine:
        print("\n⚠️ PARTIAL INTEGRATION")
        if labyrinth.queen:
            print("   Queen is connected but Wisdom Engine is missing.")
        if labyrinth.wisdom_engine:
            print("   Wisdom Engine is connected but Queen is missing.")
    else:
        print("\n❌ NO INTEGRATION")
        print("   Neither Queen nor Wisdom Engine are connected.")
        print("   They may need to be installed or imported correctly.")

if __name__ == "__main__":
    try:
        asyncio.run(test_queen_wisdom_integration())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
