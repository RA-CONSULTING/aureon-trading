#!/usr/bin/env python3
"""WS Market Data Feeder

Purpose:
- Use FREE exchange WebSocket streams (heavy-lifting) to keep an on-disk price+ticker cache fresh.
- Designed to be OPTIONAL and production-friendly.
- Does NOT change trading logic; it only publishes data the trader can optionally consume.

Current backends:
- Binance: all-market tickers via !ticker@arr (free)

Output JSON schema (stable):
{
  "generated_at": 1234567890.0,
  "source": "binance_ws",
  "prices": {"BTC": 43000.0, ...},
  "ticker_cache": {
    "BTCUSDT": {"price": 43000.0, "change24h": 1.23, "volume": 1234.0, "base": "BTC", "quote": "USDT", "exchange": "binance"},
    "binance:BTCUSDT": {...}
  }
}
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import os
import sys

# ttt
# WINDOWS UTF-8 FIX - MUST BE AT TOP BEFORE ANY PRINT STATEMENTS
# ttt
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
import asyncio
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import websockets
except Exception:
    websockets = None


def _atomic_write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _binance_quote_priority(binance_uk_mode: bool) -> List[str]:
    # Keep consistent with micro_profit_labyrinth.py logic
    return ['USDC', 'USDT', 'USD', 'BUSD'] if binance_uk_mode else ['USDT', 'USD', 'BUSD', 'USDC']


def _extract_prices_and_tickers(
    tickers: List[Dict[str, Any]],
    *,
    binance_uk_mode: bool,
) -> tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    prices: Dict[str, float] = {}
    ticker_cache: Dict[str, Dict[str, Any]] = {}

    quote_priority = _binance_quote_priority(binance_uk_mode)

    # Binance !ticker@arr payload fields (common):
    # s=symbol, c=last price, P=priceChangePercent, v=volume
    for t in tickers:
        symbol = str(t.get('s', '')).upper()
        if not symbol:
            continue

        try:
            price = float(t.get('c', 0) or 0)
        except Exception:
            price = 0.0
        if price <= 0:
            continue

        try:
            change = float(t.get('P', 0) or 0)
        except Exception:
            change = 0.0

        try:
            volume = float(t.get('v', 0) or 0)
        except Exception:
            volume = 0.0

        matched_quote: Optional[str] = None
        base: Optional[str] = None
        for quote in quote_priority:
            if symbol.endswith(quote):
                matched_quote = quote
                base = symbol[: -len(quote)]
                break

        if not matched_quote or not base:
            continue

        # Prefer first-seen base per run (quote_priority orders it)
        if base not in prices:
            prices[base] = price

        entry = {
            'price': price,
            'change24h': change,
            'volume': volume,
            'base': base,
            'quote': matched_quote,
            'exchange': 'binance',
        }
        ticker_cache[symbol] = entry
        ticker_cache[f"binance:{symbol}"] = entry

    return prices, ticker_cache


async def run_binance_all_tickers(
    *,
    out_path: Path,
    binance_uk_mode: bool,
    write_interval_s: float,
    quiet: bool,
) -> None:
    if not websockets:
        raise RuntimeError("websockets package not installed")

    url = "wss://stream.binance.com:9443/ws/!ticker@arr"
    last_write = 0.0

    if not quiet:
        print(f"🌐 Binance WS feeder connecting: {url}")
        print(f"   Output: {out_path}")

    while True:
        try:
            async with websockets.connect(url, ping_interval=20, ping_timeout=20) as ws:
                if not quiet:
                    print("   ✅ Connected")

                async for raw in ws:
                    now = time.time()

                    # throttle writes to disk
                    if now - last_write < write_interval_s:
                        continue

                    try:
                        data = json.loads(raw)
                    except Exception:
                        continue

                    if not isinstance(data, list):
                        continue

                    prices, ticker_cache = _extract_prices_and_tickers(
                        data,
                        binance_uk_mode=binance_uk_mode,
                    )

                    payload = {
                        'generated_at': now,
                        'source': 'binance_ws',
                        'prices': prices,
                        'ticker_cache': ticker_cache,
                    }
                    _atomic_write_json(out_path, payload)
                    last_write = now

                    if not quiet:
                        print(f"   🟡 wrote {len(prices)} base prices / {len(ticker_cache)} tickers")

        except asyncio.CancelledError:
            raise
        except Exception as e:
            if not quiet:
                print(f"⚠️ Binance WS feeder error: {e} (reconnecting in 2s)")
            await asyncio.sleep(2)


def main() -> int:
    parser = argparse.ArgumentParser(description="WS market data feeder (free APIs)")
    parser.add_argument(
        "--out",
        default=os.getenv("WS_PRICE_CACHE_PATH", "ws_cache/ws_prices.json"),
        help="Output JSON cache path (default: ws_cache/ws_prices.json)",
    )
    parser.add_argument(
        "--binance",
        action="store_true",
        default=True,
        help="Enable Binance all-market tickers feed (default: on)",
    )
    parser.add_argument(
        "--binance-uk-mode",
        action="store_true",
        default=os.getenv("BINANCE_UK_MODE", "0") in ("1", "true", "TRUE", "yes", "YES"),
        help="Prefer USDC quotes (UK mode)",
    )
    parser.add_argument(
        "--write-interval-s",
        type=float,
        default=float(os.getenv("WS_FEED_WRITE_INTERVAL_S", "1.0")),
        help="Minimum seconds between cache writes (default: 1.0)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=os.getenv("WS_FEED_QUIET", "0") in ("1", "true", "TRUE"),
        help="Reduce console output",
    )

    args = parser.parse_args()

    out_path = Path(args.out)

    async def _run() -> None:
        tasks = []
        if args.binance:
            tasks.append(
                run_binance_all_tickers(
                    out_path=out_path,
                    binance_uk_mode=args.binance_uk_mode,
                    write_interval_s=max(0.1, args.write_interval_s),
                    quiet=args.quiet,
                )
            )
        if not tasks:
            raise SystemExit("No feeds enabled")
        await asyncio.gather(*tasks)

    asyncio.run(_run())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
