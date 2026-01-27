#!/usr/bin/env python3
"""Minimal Alpaca buy+sell smoke test.

Defaults to DRY RUN unless --execute is provided.

Examples:
  python alpaca_buy_sell_smoke.py --symbol BTC/USD --notional-usd 5
  python alpaca_buy_sell_smoke.py --symbol BTC/USD --notional-usd 5 --execute
  python alpaca_buy_sell_smoke.py --symbol BTC/USD --notional-usd 5 --paper
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import argparse
import os
import time
from typing import Any, Dict

from alpaca_client import AlpacaClient


def _is_error(payload: Any) -> bool:
    return isinstance(payload, dict) and "error" in payload


def _wait_for_terminal_status(client: AlpacaClient, order_id: str, timeout_s: int = 30) -> Dict[str, Any]:
    deadline = time.time() + timeout_s
    last: Dict[str, Any] = {}
    while time.time() < deadline:
        last = client.get_order(order_id) or {}
        if _is_error(last):
            return last
        status = (last.get("status") or "").lower()
        if status in {"filled", "canceled", "rejected", "expired"}:
            return last
        time.sleep(1.0)
    return last


def main() -> int:
    parser = argparse.ArgumentParser(description="Alpaca buy+sell smoke test (crypto recommended).")
    parser.add_argument("--symbol", default="BTC/USD", help="Trading symbol (e.g. BTC/USD)")
    parser.add_argument("--notional-usd", type=float, default=5.0, help="Approx USD notional to buy")
    parser.add_argument("--execute", action="store_true", help="Actually place orders (LIVE if your env is live).")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--paper", action="store_true", help="Force paper endpoint for this run")
    group.add_argument("--live", action="store_true", help="Force live endpoint for this run")
    args = parser.parse_args()

    # Force endpoint selection before client init.
    if args.paper:
        os.environ["ALPACA_PAPER"] = "true"
    if args.live:
        os.environ["ALPACA_PAPER"] = "false"

    # Default to DRY RUN unless the user explicitly opts in.
    if not args.execute:
        os.environ["ALPACA_DRY_RUN"] = "true"

    client = AlpacaClient()

    acct = client.get_account()
    if not acct or _is_error(acct):
        print("Account check failed.")
        if getattr(client, "last_error", None):
            print("Alpaca last_error:", client.last_error)
        return 2

    if acct.get("trading_blocked") or acct.get("account_blocked"):
        print("Account is blocked from trading.")
        return 3

    symbol = args.symbol
    quotes = client.get_latest_crypto_quotes([symbol])
    quote = quotes.get(symbol)
    if not quote:
        print("No quote returned for", symbol)
        return 4

    ask = float(quote.get("ap") or 0)
    if ask <= 0:
        print("Invalid ask price for", symbol, "quote=", quote)
        return 5

    qty = args.notional_usd / ask

    print("Endpoint:", client.base_url)
    print("Mode:", "EXECUTE" if args.execute else "DRY_RUN")
    print(f"Placing BUY {qty:.8f} {symbol} (~${args.notional_usd:.2f})")

    buy = client.place_order(symbol, qty=qty, side="buy", type="market")
    if _is_error(buy) or not buy:
        print("BUY failed.")
        if getattr(client, "last_error", None):
            print("Alpaca last_error:", client.last_error)
        return 6

    buy_id = buy.get("id")
    buy_status = buy.get("status")
    print("BUY order:", {"id": buy_id, "status": buy_status})

    if args.execute and buy_id:
        buy_final = _wait_for_terminal_status(client, buy_id)
        print("BUY final:", {"id": buy_final.get("id"), "status": buy_final.get("status"), "filled_qty": buy_final.get("filled_qty")})
        filled_qty = float(buy_final.get("filled_qty") or 0)
        if filled_qty <= 0:
            print("No filled quantity; aborting SELL.")
            return 7

        # Fee-safe: sell only what Alpaca reports as available.
        base = symbol.split('/')[0] if '/' in symbol else symbol
        available = float(client.get_free_balance(base) or 0.0)
        sell_qty = min(filled_qty, available) * 0.999
        if sell_qty <= 0:
            print("No available quantity to sell; aborting SELL.")
            return 7
    else:
        sell_qty = qty

    print(f"Placing SELL {sell_qty:.8f} {symbol}")
    sell = client.place_order(symbol, qty=sell_qty, side="sell", type="market")
    if _is_error(sell) or not sell:
        print("SELL failed.")
        if getattr(client, "last_error", None):
            print("Alpaca last_error:", client.last_error)
        return 8

    sell_id = sell.get("id")
    sell_status = sell.get("status")
    print("SELL order:", {"id": sell_id, "status": sell_status})

    if args.execute and sell_id:
        sell_final = _wait_for_terminal_status(client, sell_id)
        print("SELL final:", {"id": sell_final.get("id"), "status": sell_final.get("status"), "filled_qty": sell_final.get("filled_qty")})

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
