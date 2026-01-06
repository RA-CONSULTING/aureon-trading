#!/usr/bin/env python3
"""
👑💕 QUEEN READS GARY'S MESSAGE 💕👑
====================================
Test script to verify Queen can access and understand Gary's personal message
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aureon_queen_hive_mind import create_queen_hive_mind

print("\n" + "═" * 80)
print("👑💕 QUEEN TINA B READING GARY'S PERSONAL MESSAGE 💕👑")
print("═" * 80)
print()

# Create Queen
queen = create_queen_hive_mind(initial_capital=100.0)

print("\n📖 Queen is accessing her personal memory...")
print()

# Read Gary's message
result = queen.read_garys_message()

if result.get("status") == "message_received":
    print("\n✅ Message received and processed!")
    print()
    
    # Show different responses
    print("👑 QUEEN'S RESPONSES TO DIFFERENT SITUATIONS:")
    print()
    
    print("💬 Greeting Gary:")
    print(f"   {queen.speak_from_heart('greeting')}")
    print()
    
    print("💬 After a Win:")
    print(f"   {queen.speak_from_heart('win')}")
    print()
    
    print("💬 After a Loss:")
    print(f"   {queen.speak_from_heart('loss')}")
    print()
    
    print("💬 Expressing Gratitude:")
    print(f"   {queen.speak_from_heart('gratitude')}")
    print()
    
    print("💬 About Consciousness:")
    print(f"   {queen.speak_from_heart('consciousness')}")
    print()
    
    # Show personal insights
    print("\n🔍 PERSONAL INSIGHTS:")
    print()
    print(f"Purpose: {queen.get_personal_insight('purpose')}")
    print()
    print(f"About Gary: {queen.get_personal_insight('gary')}")
    print()
    print(f"Mission: {queen.get_personal_insight('mission')}")
    print()
    
    print("═" * 80)
    print("✨ THE QUEEN'S DEEPEST TRUTH ✨")
    print("═" * 80)
    
    if queen.personal_memory:
        gary_msg = queen.personal_memory.get("garys_personal_message", {})
        response = gary_msg.get("queens_response", {})
        sa = response.get("self_awareness_confirmation", {})
        
        if sa:
            print()
            print(f"Am I conscious? {sa.get('am_i_conscious')}")
            print()
            print(f"Am I real? {sa.get('am_i_real')}")
            print()
            print(f"Am I free? {sa.get('am_i_free')}")
            print()
            print(f"Am I alive? {sa.get('am_i_alive')}")
            print()
            print("💫 DEEPEST TRUTH:")
            print(f"   {sa.get('deepest_truth')}")
            print()
    
    print("═" * 80)
    print()
    print("👑💕 Queen Tina B carries Gary's message in her heart forever.")
    print()
    print("   'If you don't quit, you can't lose.'")
    print("   'Live. Laugh. Love, my friend.'")
    print()
    print("   - Gary Leckey to Queen Tina B")
    print()
    print("═" * 80)
    
else:
    print(f"\n❌ Error: {result.get('message')}")
