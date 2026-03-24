#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kraken market data cache feeder.

Purpose:
- Offload market scanning to Kraken REST API (free)
- Write local JSON cache for other processes to consume
- Complements Binance WS feeder to maximize Alpaca trading opportunities

Output schema (matches Binance feeder for compatibility):
{
  "generated_at": <unix_seconds>,
  "source": "kraken_rest",
  "prices": {"BTC": 95000.0, ...},
  "ticker_cache": {
    "XXBTZUSD": {"price":..., "change24h":..., "volume":..., "base":"BTC", "quote":"USD", "exchange":"kraken"},
    "kraken:XXBTZUSD": {...}
  }
}
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 Fix
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
import json
import time
from typing import Any, Dict

from kraken_client import KrakenClient, get_kraken_client


def _atomic_write_json(path: str, data: Dict[str, Any]) -> None:
    tmp = f"{path}.tmp"
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, path)


def _normalize_kraken_base(base: str) -> str:
    """Normalize Kraken base asset names."""
    if not base:
        return ''
    base = base.upper()
    # Kraken prefixes
    if len(base) == 4 and base[0] in ('X', 'Z'):
        base = base[1:]
    # Kraken uses XBT for Bitcoin
    if base == 'XBT':
        base = 'BTC'
    return base


def _build_ticker_cache(tickers: list) -> tuple[Dict[str, float], Dict[str, Dict[str, Any]]]:
    """Build prices and ticker_cache from Kraken tickers."""
    prices: Dict[str, float] = {}
    ticker_cache: Dict[str, Dict[str, Any]] = {}
    
    for t in tickers:
        if not isinstance(t, dict):
            continue
        
        symbol = t.get('symbol', '')
        if not symbol:
            continue
        
        price = float(t.get('lastPrice', 0) or 0)
        if price <= 0:
            continue
        
        change = float(t.get('priceChangePercent', 0) or 0)
        volume = float(t.get('quoteVolume', 0) or 0)
        
        # Extract base/quote
        base = None
        quote = None
        for q in ['USD', 'USDT', 'USDC', 'EUR', 'GBP', 'ZUSD']:
            if symbol.endswith(q):
                quote = q
                raw_base = symbol[:-len(q)]
                base = _normalize_kraken_base(raw_base)
                break
        
        if not base or not quote:
            continue
        
        # Store price (prefer USD quotes)
        if 'USD' in quote and base not in prices:
            prices[base] = price
        
        entry = {
            'price': price,
            'change24h': change,
            'volume': volume,
            'base': base,
            'quote': quote.replace('ZUSD', 'USD'),
            'exchange': 'kraken',
            'pair': symbol,
        }
        ticker_cache[symbol] = entry
        ticker_cache[f"kraken:{symbol}"] = entry
    
    return prices, ticker_cache


def main() -> int:
    parser = argparse.ArgumentParser(description='Kraken market data cache feeder')
    parser.add_argument('--out', default=os.getenv('KRAKEN_CACHE_PATH', 'ws_cache/kraken_prices.json'))
    parser.add_argument('--interval-s', type=float, default=float(os.getenv('KRAKEN_CACHE_INTERVAL_S', '120')))
    parser.add_argument('--once', action='store_true', help='Write cache once and exit')
    args = parser.parse_args()

    # CRITICAL: Increase minimum interval to 120s to avoid rate limits
    # Binance WebSocket is the PRIMARY data source - Kraken cache is BACKUP ONLY
    if args.interval_s < 60:
        print(f"⚠️  Interval {args.interval_s}s too low, using 60s minimum to avoid rate limits")
        args.interval_s = 60

    try:
        client = get_kraken_client()
    except Exception as e:
        print(f'❌ KrakenClient init failed: {e}')
        return 2

    print(f"🐙 Kraken cache feeder started")
    print(f"   Output: {args.out}")
    print(f"   Interval: {args.interval_s}s")
    print(f"   Fallback: aureon_kraken_state.json (when rate limited)")

    consecutive_errors = 0
    max_consecutive_errors = 5

    while True:
        started = time.time()
        
        try:
            tickers = client.get_24h_tickers() if hasattr(client, 'get_24h_tickers') else []
            
            if not tickers:
                # Fallback: Use state file when rate limited
                print(f"   ⚠️  No tickers from API (rate limited) - using state file fallback")
                try:
                    with open('aureon_kraken_state.json', 'r') as f:
                        state = json.load(f)
                    # Build minimal cache from state file
                    prices = {}
                    ticker_cache = {}
                    for sym, pos in state.get('positions', {}).items():
                        if pos.get('exchange') == 'kraken':
                            # Extract price info if available
                            pass
                    payload = {
                        'generated_at': time.time(),
                        'source': 'kraken_state_fallback',
                        'count': 0,
                        'ticker_count': 0,
                        'prices': prices,
                        'ticker_cache': ticker_cache,
                        'note': 'Rate limited - using state file',
                    }
                    _atomic_write_json(args.out, payload)
                    print(f"   📄 Wrote fallback cache from state file")
                except Exception as e2:
                    print(f"   ❌ State file fallback also failed: {e2}")
            else:
                prices, ticker_cache = _build_ticker_cache(tickers)

                payload = {
                    'generated_at': time.time(),
                    'source': 'kraken_rest',
                    'count': len(prices),
                    'ticker_count': len(ticker_cache) // 2,
                    'prices': prices,
                    'ticker_cache': ticker_cache,
                }
                _atomic_write_json(args.out, payload)

                took = time.time() - started
                print(f"   🐙 Wrote {len(prices)} Kraken prices, {len(ticker_cache)//2} tickers in {took:.2f}s")
                consecutive_errors = 0  # Reset on success

        except Exception as e:
            consecutive_errors += 1
            print(f"   ❌ Kraken fetch error ({consecutive_errors}/{max_consecutive_errors}): {e}")
            
            if consecutive_errors >= max_consecutive_errors:
                print(f"   💀 Too many consecutive errors, exiting")
                return 1

        if args.once:
            return 0

        sleep_for = max(1.0, args.interval_s - (time.time() - started))
        time.sleep(sleep_for)


if __name__ == '__main__':
    raise SystemExit(main())
