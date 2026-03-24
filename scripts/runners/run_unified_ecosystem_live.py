#!/usr/bin/env python3
"""
🔥 UNIFIED ECOSYSTEM LIVE RUNNER 🔥
====================================

Run the FULL Aureon ecosystem with ALL systems connected:
  🦅⚔️ 1885 CAPM Conversion Commando (ZERO FEAR)
  🪜 Conversion Ladder (Net Profit Gating)
  🍄 Mycelium Network (Neural Intelligence)
  🏹 War Band (Scouts & Snipers)
  🌊 Harmonic Wave Fusion
  🐘 Elephant Memory
  📈 ALL Exchanges (Binance, Kraken, Alpaca, Capital)

Usage:
  # Dry run (paper trading) - DEFAULT
  python run_unified_ecosystem_live.py
  
  # LIVE TRADING (REAL MONEY!)
  LIVE=1 python run_unified_ecosystem_live.py
  
  # Custom settings
  LIVE=1 BALANCE=5000 INTERVAL=2 python run_unified_ecosystem_live.py

Gary Leckey | January 2026
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys

def main():
    # Banner
    print("""
    ╔═══════════════════════════════════════════════════════════════════════╗
    ║  🔥🦅 AUREON UNIFIED ECOSYSTEM - ZERO FEAR LIVE TRADING 🦅🔥         ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    ║                                                                       ║
    ║  SYSTEMS CONNECTED:                                                   ║
    ║    🦅⚔️  Conversion Commando (1885 CAPM - ZERO FEAR)                  ║
    ║    🪜    Conversion Ladder (Net Profit Gating)                        ║
    ║    🍄    Mycelium Network (Neural Intelligence)                       ║
    ║    🏹    War Band (Scouts & Snipers)                                  ║
    ║    🌊    Harmonic Wave Fusion                                         ║
    ║    🐘    Elephant Memory                                              ║
    ║    📈    Multi-Exchange (Binance, Kraken, Alpaca, Capital)            ║
    ║                                                                       ║
    ║  ZERO FEAR DOCTRINE:                                                  ║
    ║    🔥 NO HESITATION - Execute immediately                             ║
    ║    🔥 NO DOUBT - Trust the penny profit gate                          ║
    ║    🔥 NO RETREAT - Only strategic repositioning                       ║
    ║    🔥 NO LIMITS - Every pair on every exchange                        ║
    ║                                                                       ║
    ╠═══════════════════════════════════════════════════════════════════════╣
    """)
    
    # Check mode
    live_mode = os.getenv('LIVE', '0') == '1'
    balance = float(os.getenv('BALANCE', '1000'))
    interval = float(os.getenv('INTERVAL', '2'))  # 2 second cycles for speed
    
    if live_mode:
        print("""
    ║  ⚠️  LIVE MODE ENABLED - REAL MONEY TRADING ⚠️                        ║
    ║                                                                       ║
    """)
        # Confirmation
        confirm = input("    Type 'ZERO FEAR' to confirm LIVE trading: ").strip()
        if confirm != 'ZERO FEAR':
            print("\n    ❌ Live trading cancelled. Use dry run instead.")
            os.environ['LIVE'] = '0'
            live_mode = False
        else:
            print("\n    🔥 ZERO FEAR CONFIRMED - ENGAGING LIVE TRADING 🔥\n")
    else:
        print("""
    ║  🧪 DRY RUN MODE (Paper Trading)                                      ║
    ║     Set LIVE=1 to enable real trading                                 ║
    ║                                                                       ║
    """)
    
    print(f"""    ║  Settings:                                                            ║
    ║    MODE:     {'🔴 LIVE' if live_mode else '🟢 DRY RUN'}                                                   ║
    ║    BALANCE:  ${balance:,.2f}                                                ║
    ║    INTERVAL: {interval}s cycles                                              ║
    ╚═══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Set environment variables
    os.environ['BALANCE'] = str(balance)
    os.environ['INTERVAL'] = str(interval)
    
    # Import and run the ecosystem
    try:
        from aureon_unified_ecosystem import main as ecosystem_main
        ecosystem_main()
    except KeyboardInterrupt:
        print("\n\n    🛑 Ecosystem stopped by user.")
    except Exception as e:
        print(f"\n    ❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
