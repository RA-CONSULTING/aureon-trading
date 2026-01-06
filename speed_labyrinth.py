#!/usr/bin/env python3
"""
⚡🌍 SPEED LABYRINTH - Run the ACTUAL labyrinth in SPEED MODE!
Fractions of pennies - SPEED + VOLUME = WIN!

Gary Leckey & GitHub Copilot | January 2026
"""
import asyncio
from micro_profit_labyrinth import MicroProfitLabyrinth

async def run_speed_labyrinth():
    print("\n" + "⚡" * 35)
    print("   SPEED LABYRINTH - FRACTIONS OF PENNIES!")
    print("   Iron tight math + Speed + Volume = BILLION!")
    print("⚡" * 35 + "\n")
    
    # Create labyrinth in LIVE mode with SPEED settings
    lab = MicroProfitLabyrinth(live=True)
    
    # Override to SPEED mode
    lab.config['entry_score_threshold'] = 1  # Accept almost anything
    lab.config['min_profit_usd'] = 0.0       # Zero minimum
    lab.config['min_profit_pct'] = 0.0       # Zero minimum
    
    print("⚡ SPEED CONFIG:")
    print(f"   Entry threshold: 1 (accept all)")
    print(f"   Min profit: $0.00 (fractions OK)")
    print(f"   Mode: LIVE + SPEED")
    print()
    
    # Run for 150 seconds - let it find opportunities!
    await lab.run(duration_s=150)

if __name__ == "__main__":
    asyncio.run(run_speed_labyrinth())
