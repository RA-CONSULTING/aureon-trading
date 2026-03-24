#!/usr/bin/env python3
"""
🌌⚡ AUREON UNIFIED LIVE TRADING WITH IMPERIAL PREDICTABILITY ⚡🌌
Run live trading session with full cosmic synchronization
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time
import os
from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

def main():
    print('╔═══════════════════════════════════════════════════════════════════╗')
    print('║  🌌⚡ AUREON UNIFIED ECOSYSTEM - IMPERIAL PREDICTABILITY ⚡🌌      ║')
    print('║  Live Trading Session with Cosmic Synchronization                ║')
    print('╚═══════════════════════════════════════════════════════════════════╝')
    print()

    # Initialize ecosystem
    print('🚀 Initializing trading ecosystem...')
    # Safety: allow DRY_RUN override via env
    dry_run = (os.getenv('AUREON_DRY_RUN', '0') == '1')
    # Enforce smaller risk if LIVE_SAFETY mode enabled
    safety_mode = (os.getenv('AUREON_LIVE_SAFETY', '1') == '1')
    if safety_mode:
        CONFIG['MAX_POSITIONS'] = min(CONFIG['MAX_POSITIONS'], int(os.getenv('SAFE_MAX_POSITIONS', '5')))
        CONFIG['PORTFOLIO_RISK_BUDGET'] = min(CONFIG['PORTFOLIO_RISK_BUDGET'], float(os.getenv('SAFE_RISK_BUDGET', '0.15')))
    ecosystem = AureonKrakenEcosystem(dry_run=dry_run)

    # Goal parameters
    target_profit = float(os.getenv('TARGET_NET_PROFIT_GBP', '1000'))
    session_minutes = float(os.getenv('SESSION_MINUTES', '20'))
    starting_equity = ecosystem.total_equity_gbp
    if target_profit > starting_equity * 3 and os.getenv('SKIP_GOAL_WARNING','0') != '1':
        print("\n⚠️  WARNING: Target profit exceeds 3× starting equity in short session.")
        print(f"   Start: £{starting_equity:.2f} | Goal: £{target_profit:.2f} | Minutes: {session_minutes:.1f}")
        resp = input('Proceed with aggressive goal? (y/N): ')
        if resp.lower() != 'y':
            print('Aborted by user.')
            return

    print()
    print('📊 System Status:')
    print(f'   ├─ Exchange: {CONFIG.get("EXCHANGE", "both").upper()}')
    print(f'   ├─ Base Currency: {CONFIG["BASE_CURRENCY"]}')
    print(f'   ├─ Max Positions: {CONFIG["MAX_POSITIONS"]}')
    print(f'   ├─ Risk Budget: {CONFIG.get("PORTFOLIO_RISK_BUDGET", 0):.2f}')
    print(f'   ├─ Dry Run: {"YES" if dry_run else "NO"}')
    print(f'   ├─ Safety Mode: {"ON" if safety_mode else "OFF"}')
    print(f'   ├─ Target Profit: £{target_profit:.2f}')
    print(f'   └─ Session Limit: {session_minutes:.1f} min')
    print(f'   ├─ HNC Frequency: {"✅ ENABLED" if CONFIG.get("ENABLE_HNC_FREQUENCY") else "❌ DISABLED"}')
    print(f'   ├─ Probability Matrix: {"✅ ENABLED" if CONFIG.get("ENABLE_PROB_MATRIX") else "❌ DISABLED"}')
    print(f'   └─ Imperial Predictability: {"✅ ENABLED" if CONFIG.get("ENABLE_IMPERIAL") else "❌ DISABLED"}')

    # Get cosmic status
    print()
    print('🌌 Cosmic State:')
    cosmic = ecosystem.auris.get_cosmic_status()
    print(f'   ├─ Phase: {cosmic.get("phase", "UNKNOWN")}')
    print(f'   ├─ Coherence: {cosmic.get("coherence", 0):.2%}')
    print(f'   ├─ Distortion: {cosmic.get("distortion", 0):.3%}')
    print(f'   ├─ Planetary Torque: ×{cosmic.get("planetary_torque", 1):.2f}')
    print(f'   └─ Imperial Yield: {cosmic.get("imperial_yield", 0):.2e}')

    # Check if we should trade
    should_trade, reason = ecosystem.auris.should_trade_imperial()
    print()
    print(f'📊 Trading Gate: {"✅ OPEN" if should_trade else "🛑 CLOSED"}')
    print(f'   Reason: {reason}')

    # Optional hard halt if distortion & env flag
    halt_on_distortion = (os.getenv('HALT_ON_DISTORTION', '1') == '1')
    if not should_trade and halt_on_distortion:
        print()
        print('⚠️  Imperial Predictability recommends halting trading due to cosmic conditions.')
        print('   The system will monitor but not place new trades until conditions improve.')
        print()
        response = input('Continue anyway? (y/N): ')
        if response.lower() != 'y':
            print('Trading session cancelled.')
            return

    print()
    print('═' * 70)
    print('🎯 Starting Trading Session...')
    print('═' * 70)
    print()

    # Run trading loop
    try:
        ecosystem.run(
            interval=float(os.getenv('CYCLE_INTERVAL', '5.0')),
            target_profit_gbp=(None if dry_run else target_profit),
            max_minutes=session_minutes
        )
    except KeyboardInterrupt:
        print()
        print('🛑 Trading session interrupted by user')
    except Exception as e:
        print(f'❌ Error during trading session: {e}')
        import traceback
        traceback.print_exc()
    finally:
        print()
        print('═' * 70)
        print('📊 Session Summary')
        print('═' * 70)
        
        # Display final cosmic state
        cosmic = ecosystem.auris.get_cosmic_status()
        print()
        print('🌌 Final Cosmic State:')
        print(f'   Phase: {cosmic.get("phase", "UNKNOWN")}')
        print(f'   Coherence: {cosmic.get("coherence", 0):.2%}')
        print(f'   Planetary Torque: ×{cosmic.get("planetary_torque", 1):.2f}')
        
        # Display performance
        tracker = ecosystem.tracker
        print()
        print('💰 Performance:')
        print(f'   Total Trades: {tracker.total_trades}')
        print(f'   Win Rate: {tracker.win_rate:.1f}%')
        print(f'   Net P&L: ${tracker.total_profits:.2f}')
        
        print()
        print('✨ Trading session complete!')

if __name__ == '__main__':
    main()
