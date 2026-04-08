#!/usr/bin/env python3
"""
Capital market universe and monitoring cache.

Builds a local symbol universe file plus a lightweight monitored quote cache
using Capital.com metadata and lower-cost public quote sources where possible.
This lets CapitalCFDTrader reuse local snapshots before hitting Capital's API.
"""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from capital_client import CapitalClient
from capital_cfd_trader import CAPITAL_UNIVERSE


DEFAULT_UNIVERSE_PATH = Path(os.getenv("CAPITAL_UNIVERSE_CACHE_PATH", "ws_cache/capital_universe.json"))
DEFAULT_MONITOR_PATH = Path(os.getenv("CAPITAL_MONITOR_CACHE_PATH", "ws_cache/capital_monitor.json"))

YAHOO_SYMBOL_MAP: Dict[str, str] = {
    "AAPL": "AAPL",
    "TSLA": "TSLA",
    "NVDA": "NVDA",
    "AMZN": "AMZN",
    "MSFT": "MSFT",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "USDJPY": "JPY=X",
    "AUDUSD": "AUDUSD=X",
    "USDCAD": "CAD=X",
    "EURGBP": "EURGBP=X",
    "UK100": "^FTSE",
    "US500": "^GSPC",
    "US30": "^DJI",
    "DE40": "^GDAXI",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "OIL_CRUDE": "CL=F",
    "NATURALGAS": "NG=F",
}


def _atomic_write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def _fetch_yahoo_quotes(symbols: List[str], timeout: float = 8.0) -> Dict[str, Dict[str, Any]]:
    if not symbols:
        return {}
    url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=" + urllib.parse.quote(",".join(symbols))
    req = urllib.request.Request(url, headers={"User-Agent": "Aureon-Capital-Monitor/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return {}

    out: Dict[str, Dict[str, Any]] = {}
    for quote in payload.get("quoteResponse", {}).get("result", []) or []:
        sym = str(quote.get("symbol") or "").upper()
        if not sym:
            continue
        bid = float(quote.get("bid", 0.0) or 0.0)
        ask = float(quote.get("ask", 0.0) or 0.0)
        price = float(quote.get("regularMarketPrice", 0.0) or 0.0)
        out[sym] = {
            "price": price,
            "bid": bid,
            "ask": ask,
            "change_pct": float(quote.get("regularMarketChangePercent", 0.0) or 0.0),
            "market_state": str(quote.get("marketState") or ""),
        }
    return out


def _build_universe_payload(client: CapitalClient) -> Dict[str, Any]:
    universe_rows: List[Dict[str, Any]] = []
    for symbol, cfg in CAPITAL_UNIVERSE.items():
        resolved: Dict[str, Any] = {}
        try:
            resolved = client._resolve_market(symbol) or {}  # type: ignore[attr-defined]
        except Exception:
            resolved = {}
        yahoo_symbol = YAHOO_SYMBOL_MAP.get(symbol, "")
        universe_rows.append({
            "symbol": symbol,
            "asset_class": cfg.get("class", "unknown"),
            "epic": str(resolved.get("epic") or ""),
            "instrument_name": str(resolved.get("instrumentName") or resolved.get("symbol") or ""),
            "yahoo_symbol": yahoo_symbol,
            "config": dict(cfg),
        })
    return {
        "generated_at": time.time(),
        "source": "capital_market_monitor.universe",
        "symbols": universe_rows,
    }


def _build_monitor_payload(client: CapitalClient, universe_payload: Dict[str, Any]) -> Dict[str, Any]:
    capital_symbols = [row["symbol"] for row in universe_payload.get("symbols", [])]
    yahoo_symbols = [row["yahoo_symbol"] for row in universe_payload.get("symbols", []) if row.get("yahoo_symbol")]
    yahoo_quotes = _fetch_yahoo_quotes(yahoo_symbols)

    prices: Dict[str, Dict[str, Any]] = {}
    for row in universe_payload.get("symbols", []):
        symbol = str(row.get("symbol") or "").upper()
        yahoo_symbol = str(row.get("yahoo_symbol") or "").upper()
        q = yahoo_quotes.get(yahoo_symbol, {})
        if q:
            prices[symbol] = {
                "symbol": symbol,
                "source": "yahoo",
                "price": float(q.get("price", 0.0) or 0.0),
                "bid": float(q.get("bid", 0.0) or 0.0),
                "ask": float(q.get("ask", 0.0) or 0.0),
                "change_pct": float(q.get("change_pct", 0.0) or 0.0),
                "epic": str(row.get("epic") or ""),
                "market_state": str(q.get("market_state") or ""),
            }

    # Backfill any missing symbols directly from Capital.
    missing = [sym for sym in capital_symbols if sym not in prices]
    if missing and getattr(client, "enabled", False):
        try:
            capital_quotes = client.get_tickers_for_symbols(missing)
        except Exception:
            capital_quotes = {}
        for symbol, q in capital_quotes.items():
            if not q:
                continue
            prices[str(symbol).upper()] = {
                "symbol": str(symbol).upper(),
                "source": "capital",
                "price": float(q.get("price", 0.0) or 0.0),
                "bid": float(q.get("bid", 0.0) or 0.0),
                "ask": float(q.get("ask", 0.0) or 0.0),
                "change_pct": float(q.get("change_pct", 0.0) or 0.0),
                "epic": str(q.get("epic") or ""),
                "market_state": "",
            }

    return {
        "generated_at": time.time(),
        "source": "capital_market_monitor.quotes",
        "count": len(prices),
        "prices": prices,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Capital universe and monitor cache")
    parser.add_argument("--universe-out", default=str(DEFAULT_UNIVERSE_PATH))
    parser.add_argument("--monitor-out", default=str(DEFAULT_MONITOR_PATH))
    parser.add_argument("--interval-s", type=float, default=float(os.getenv("CAPITAL_MONITOR_INTERVAL_S", "15")))
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    client = CapitalClient()
    universe_path = Path(args.universe_out)
    monitor_path = Path(args.monitor_out)

    while True:
        universe_payload = _build_universe_payload(client)
        monitor_payload = _build_monitor_payload(client, universe_payload)
        _atomic_write_json(universe_path, universe_payload)
        _atomic_write_json(monitor_path, monitor_payload)
        print(
            f"Wrote Capital universe ({len(universe_payload.get('symbols', []))}) "
            f"and monitor cache ({monitor_payload.get('count', 0)})"
        )
        if args.once:
            return 0
        time.sleep(max(1.0, float(args.interval_s)))


if __name__ == "__main__":
    raise SystemExit(main())
