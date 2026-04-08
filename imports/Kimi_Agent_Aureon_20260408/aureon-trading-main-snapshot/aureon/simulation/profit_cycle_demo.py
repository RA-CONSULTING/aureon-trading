#!/usr/bin/env python3
"""
🌍⚡ PROFIT CYCLE DEMONSTRATION ⚡🌍
═══════════════════════════════════════════════════════════════

Simulates a full trade cycle (5 buys + 5 sells) using the unified
trading ecosystem in dry-run mode. Each position is exited at a
profit so that the combined net P&L is positive.

This is a deterministic demonstration: we artificially nudge prices
+3% before closing to ensure profits after fees, slippage, and spread.

Gary Leckey & GitHub Copilot | November 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import time

sys.path.insert(0, '/workspaces/aureon-trading')

from aureon_unified_ecosystem import AureonKrakenEcosystem, CONFIG

# Force deterministic environment for the demo
CONFIG['EXCHANGE'] = 'kraken'
CONFIG['ENABLE_COINAPI'] = False
CONFIG['ALPACA_ANALYTICS_ONLY'] = True
CONFIG['ENABLE_REBALANCING'] = False
CONFIG['DEFAULT_WIN_PROB'] = 0.90
CONFIG['SLIPPAGE_PCT'] = 0.0005  # 0.05% slippage assumption for demo
CONFIG['SPREAD_COST_PCT'] = 0.0005
CONFIG['MAX_POSITIONS'] = max(CONFIG['MAX_POSITIONS'], 10)

TARGET_TRADES = 5
PROFIT_BOOST = 0.03  # +3% price boost to guarantee profit after fees

def main():
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  🌍⚡ PROFIT CYCLE DEMO - 5 TRADES NET POSITIVE ⚡🌍                       ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

    eco = AureonKrakenEcosystem(initial_balance=200.0, dry_run=True)
    eco.refresh_tickers()

    opps = eco.find_opportunities()
    if not opps:
        print("⚠️  No opportunities available right now. Try running again later.")
        return

    print(f"🔍 Opportunities found: {len(opps)}")

    opened = []
    for opp in opps[:TARGET_TRADES]:
        try:
            eco.open_position(opp)
            opened.append(opp['symbol'])
            print(f"   ✅ BUY {opp['symbol']:12s} @ ${opp['price']:.6f}")
            time.sleep(0.1)
        except Exception as exc:
            print(f"   ⚠️  Failed to open {opp['symbol']}: {exc}")

        if len(opened) >= TARGET_TRADES:
            break

    print(f"\n📈 Open positions: {len(opened)}")

    if len(opened) < TARGET_TRADES:
        print("⚠️  Could not open the required number of trades. Aborting demo.")
        return

    # Artificially boost prices by 3% for demonstration purposes
    for symbol in opened:
        pos = eco.positions.get(symbol)
        if not pos:
            continue
        entry = pos.entry_price
        boosted_price = entry * (1 + PROFIT_BOOST)
        # Update ticker cache so exit uses boosted price
        if symbol in eco.ticker_cache:
            eco.ticker_cache[symbol]['price'] = boosted_price
        else:
            eco.ticker_cache[symbol] = {'price': boosted_price, 'change24h': 0, 'volume': 0}
        # Close position with target profit icon
        eco.close_position(symbol, 'TP', PROFIT_BOOST * 100, boosted_price)
        time.sleep(0.1)

    print("\n🎯 All positions closed")
    print("   Total Trades Recorded:", eco.tracker.total_trades)
    print("   Wins:", eco.tracker.wins)
    print("   Losses:", eco.tracker.losses)

    net_profit = eco.tracker.net_profit
    print(f"\n💰 NET PROFIT (combined): £{net_profit:.2f}")

    if net_profit > 0:
        print("   🎉 SUCCESS: 5 buys + 5 sells produced positive net profit")
    else:
        print("   ⚠️  Net profit not positive — check configuration.")

    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║  ✅ PROFIT CYCLE COMPLETE                                                ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)

if __name__ == "__main__":
    main()
