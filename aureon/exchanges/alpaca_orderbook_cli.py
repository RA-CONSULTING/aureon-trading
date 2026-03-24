#!/usr/bin/env python3
"""Alpaca full orderbook CLI

Fetches the crypto orderbook from Alpaca Data API and prints top levels.

Usage:
- `python alpaca_orderbook_cli.py BTC/USD --levels 25`

Notes:
- Alpaca's endpoint returns the depth it provides; this tool prints up to `--levels`.
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import sys

# WINDOWS UTF-8 FIX - MUST BE AT TOP BEFORE ANY PRINT STATEMENTS
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io

        def _is_utf8_wrapper(stream):
            return (
                isinstance(stream, io.TextIOWrapper)
                and hasattr(stream, 'encoding')
                and stream.encoding
                and stream.encoding.lower().replace('-', '') == 'utf8'
            )

        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import argparse
from typing import Any, Dict, List, Tuple

from alpaca_client import AlpacaClient


def _normalize_side(side: List[Any]) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    for lvl in side or []:
        if isinstance(lvl, dict):
            p = float(lvl.get('p', 0) or 0)
            s = float(lvl.get('s', 0) or 0)
        elif isinstance(lvl, (list, tuple)) and len(lvl) >= 2:
            p = float(lvl[0] or 0)
            s = float(lvl[1] or 0)
        else:
            continue
        if p > 0 and s > 0:
            out.append((p, s))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('symbol', help='Crypto symbol like BTC/USD or BTCUSD')
    ap.add_argument('--levels', type=int, default=25, help='Levels to print (default: 25)')
    args = ap.parse_args()

    client = AlpacaClient()
    book: Dict[str, Any] = client.get_crypto_orderbook(args.symbol) or {}

    bids = _normalize_side(book.get('bids') or book.get('b') or [])
    asks = _normalize_side(book.get('asks') or book.get('a') or [])

    print(f"symbol={book.get('symbol') or args.symbol} ts={book.get('t') or book.get('timestamp')}")

    if bids and asks:
        best_bid = bids[0][0]
        best_ask = asks[0][0]
        mid = (best_bid + best_ask) / 2
        spread = best_ask - best_bid
        spread_pct = (spread / mid) * 100 if mid else 0
        print(f"best_bid={best_bid} best_ask={best_ask} mid={mid} spread={spread} spread_pct={spread_pct:.6f}%")
    else:
        print("No bids/asks returned.")

    n = max(0, int(args.levels))
    print("\nBIDS")
    for i, (p, s) in enumerate(bids[:n], start=1):
        print(f"{i:>3}  p={p:<14g}  s={s:<14g}  notional={p*s:<14g}")

    print("\nASKS")
    for i, (p, s) in enumerate(asks[:n], start=1):
        print(f"{i:>3}  p={p:<14g}  s={s:<14g}  notional={p*s:<14g}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
