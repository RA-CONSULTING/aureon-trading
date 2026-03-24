#!/usr/bin/env python3
"""Check Kraken trades in the last 10 hours and calculate P&L."""

import time
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()
from kraken_client import KrakenClient

TEN_HOURS_AGO = int(time.time()) - (10 * 3600)

print(f"\n{'='*70}")
print("  KRAKEN TRADES - LAST 10 HOURS")
print(f"  From: {datetime.fromtimestamp(TEN_HOURS_AGO).strftime('%Y-%m-%d %H:%M:%S')}")
print(f"  To:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"{'='*70}\n")

client = KrakenClient()

trades = client.get_trades_history(since=TEN_HOURS_AGO)

if not trades:
    print("No trades found in the last 10 hours.")
    exit(0)

# Filter to only last 10 hours (API may return more)
trades_10h = [t for t in trades if float(t.get("time", 0)) >= TEN_HOURS_AGO]
print(f"Found {len(trades_10h)} trade(s) in the last 10 hours.\n")

if not trades_10h:
    print("No trades found in the last 10 hours after filtering.")
    exit(0)

# Sort by time ascending
trades_10h.sort(key=lambda t: float(t.get("time", 0)))

total_buy_cost = 0.0
total_sell_proceeds = 0.0
total_fees = 0.0
total_volume = 0.0

print(f"{'#':<4} {'Time':<20} {'Pair':<14} {'Type':<6} {'Vol':>14} {'Price':>14} {'Cost':>12} {'Fee':>10}")
print("-" * 100)

for i, trade in enumerate(trades_10h, 1):
    ts = float(trade.get("time", 0))
    dt = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
    pair = trade.get("pair", "?")
    ttype = trade.get("type", "?").upper()
    vol = float(trade.get("vol", 0))
    price = float(trade.get("price", 0))
    cost = float(trade.get("cost", 0))
    fee = float(trade.get("fee", 0))

    print(f"{i:<4} {dt:<20} {pair:<14} {ttype:<6} {vol:>14.6f} {price:>14.4f} {cost:>12.4f} {fee:>10.4f}")

    total_fees += fee
    total_volume += cost
    if ttype == "BUY":
        total_buy_cost += cost
    else:
        total_sell_proceeds += cost

print("-" * 100)

# P&L calculation
# Realized P&L = sell proceeds - buy costs - fees (for matched trades)
# Net flow = sells - buys (positive means you took more out than you put in)
net_flow = total_sell_proceeds - total_buy_cost - total_fees

print(f"\n{'='*50}")
print("  SUMMARY")
print(f"{'='*50}")
print(f"  Total trades:        {len(trades_10h)}")
print(f"  Total volume traded: ${total_volume:,.4f}")
print(f"  Total buy cost:      ${total_buy_cost:,.4f}")
print(f"  Total sell proceeds: ${total_sell_proceeds:,.4f}")
print(f"  Total fees paid:     ${total_fees:,.4f}")
print(f"{'='*50}")

if total_buy_cost > 0 and total_sell_proceeds > 0:
    print(f"  Net P&L (sells - buys - fees): ${net_flow:+,.4f}")
    if net_flow > 0:
        print(f"  RESULT: YOU MADE MONEY  (+${net_flow:.4f})")
    elif net_flow < 0:
        print(f"  RESULT: YOU LOST MONEY  (-${abs(net_flow):.4f})")
    else:
        print(f"  RESULT: BREAKEVEN")
elif total_sell_proceeds == 0 and total_buy_cost > 0:
    print(f"  Only BUY trades found — positions still open, no realized P&L yet.")
    print(f"  Total invested: ${total_buy_cost:,.4f} + ${total_fees:,.4f} fees")
elif total_buy_cost == 0 and total_sell_proceeds > 0:
    print(f"  Only SELL trades found — selling previously held positions.")
    print(f"  Proceeds: ${total_sell_proceeds:,.4f}, Fees: ${total_fees:,.4f}")
else:
    print(f"  Insufficient data for P&L calculation.")

print(f"{'='*50}\n")
