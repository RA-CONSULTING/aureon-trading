#!/usr/bin/env python3
"""
MARGIN ETA PREDICTOR - TIME-TO-PROFIT CALCULATOR
================================================

Reads YOUR REAL open Kraken margin positions (SOL, ETH - whatever is actually
live on Kraken) and estimates when each will turn profitable.

Data source priority:
  1. Kraken API -> /0/private/OpenPositions  (live, authoritative)
  2. kraken_margin_army_state.json           (local cache fallback)

Usage:
    python margin_eta_predictor.py          # Single snapshot
    python margin_eta_predictor.py --watch  # Live 60-second loop
"""

import os
import json
import time
import urllib.request
import logging
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

BINANCE_TICKER_URL = "https://api.binance.com/api/v3/ticker/price"
BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
KRAKEN_TICKER_URL  = "https://api.kraken.com/0/public/Ticker"
ARMY_STATE_FILE    = "kraken_margin_army_state.json"


@dataclass
class PositionETA:
    symbol: str
    side: str
    leverage: float
    entry_price: float
    current_price: float
    breakeven_price: float
    volume: float
    cost_basis: float
    unrealized_pnl: float
    pct_to_breakeven: float
    pct_from_entry: float
    hourly_volatility_pct: float
    eta_minutes: float
    bullish_eta_minutes: float
    bearish_eta_minutes: float
    confidence: float
    source: str = "unknown"
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


# ── helpers ────────────────────────────────────────────────────────────────

def _fetch(url: str) -> Optional[dict]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MarginETA/2.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        logger.debug(f"HTTP {url}: {e}")
        return None


def get_current_price(symbol: str) -> Optional[float]:
    """Try Binance (USDT pair), then Kraken public ticker."""
    b_sym = symbol.upper().replace("USD", "USDT")
    d = _fetch(f"{BINANCE_TICKER_URL}?symbol={b_sym}")
    if d and "price" in d:
        return float(d["price"])
    # Kraken public fallback
    d = _fetch(f"{KRAKEN_TICKER_URL}?pair={symbol}")
    if d and d.get("result"):
        for ticker in d["result"].values():
            return float(ticker["c"][0])
    return None


def get_hourly_vol(symbol: str) -> float:
    """Average absolute hourly return (%) over last 24 candles."""
    b_sym = symbol.upper().replace("USD", "USDT")
    data = _fetch(f"{BINANCE_KLINES_URL}?symbol={b_sym}&interval=1h&limit=24")
    if not data or len(data) < 2:
        return 2.0
    closes = [float(c[4]) for c in data]
    returns = [abs((closes[i] - closes[i-1]) / closes[i-1]) * 100 for i in range(1, len(closes))]
    return max(sum(returns) / len(returns), 0.1) if returns else 2.0


def calc_breakeven(entry: float, open_fee: float = 0.00376, close_fee: float = 0.0035) -> float:
    return entry * (1 + open_fee + close_fee + 0.0001)


def normalise_pair(pair: str) -> str:
    MAP = {
        "XETHZUSD": "ETHUSD", "XBTZUSD": "XBTUSD", "XXBTZUSD": "XBTUSD",
        "XSOLUSD":  "SOLUSD", "XLTCZUSD": "LTCUSD", "XXRPZUSD": "XRPUSD",
    }
    if pair in MAP:
        return MAP[pair]
    p = pair
    if p.startswith("X") and len(p) > 4 and p[1:4].isupper():
        p = p[1:]
    if p.endswith("ZUSD"):
        p = p[:-4] + "USD"
    return p


# ── position loaders ────────────────────────────────────────────────────────

def load_from_kraken_api() -> List[dict]:
    """Fetch ALL live open margin positions via Kraken private API."""
    try:
        from kraken_client import KrakenClient
        client = KrakenClient()
        if client.dry_run:
            return []
        raw = client.get_open_margin_positions(do_calcs=True)
        if not raw:
            return []
        results = []
        for pos in raw:
            symbol  = normalise_pair(pos.get("pair", ""))
            vol     = float(pos.get("volume", 0))
            cost    = float(pos.get("cost", 0))
            fee     = float(pos.get("fee", 0))
            ep      = cost / vol if vol > 0 else 0
            lev_raw = pos.get("leverage", "1")
            lev     = float(lev_raw) if lev_raw else 1.0
            results.append({
                "symbol":          symbol,
                "side":            pos.get("side", "buy"),
                "volume":          vol,
                "cost":            cost,
                "fee":             fee,
                "entry_price":     ep,
                "leverage":        lev,
                "unrealized_pnl":  float(pos.get("unrealized_pnl", 0)),
                "breakeven_price": calc_breakeven(ep, fee / cost if cost > 0 else 0.00376),
                "source":          "kraken_api",
            })
        logger.info(f"Loaded {len(results)} live positions from Kraken API")
        return results
    except Exception as e:
        logger.warning(f"Kraken API unavailable ({e}), falling back to state file")
        return []


def load_from_state_files() -> List[dict]:
    """Read active positions from kraken_margin_army_state.json."""
    results = []
    try:
        with open(ARMY_STATE_FILE) as f:
            state = json.load(f)

        # Single active_trade field (army trader)
        trade = state.get("active_trade")
        if trade and trade.get("pair"):
            ep = float(trade.get("entry_price", 0))
            results.append({
                "symbol":          trade["pair"],
                "side":            trade.get("side", "buy"),
                "volume":          float(trade.get("volume", 0)),
                "cost":            float(trade.get("cost", 0)),
                "fee":             float(trade.get("entry_fee", 0)),
                "entry_price":     ep,
                "leverage":        float(trade.get("leverage", 1)),
                "unrealized_pnl":  0.0,
                "breakeven_price": float(trade.get("breakeven_price") or calc_breakeven(ep)),
                "source":          "army_state",
            })

        # active_trades dict (penny trader)
        for sym, t in state.get("active_trades", {}).items():
            ep = float(t.get("entry_price", 0))
            results.append({
                "symbol":          sym,
                "side":            t.get("side", "buy"),
                "volume":          float(t.get("volume", 0)),
                "cost":            float(t.get("cost", 0)),
                "fee":             float(t.get("entry_fee", 0)),
                "entry_price":     ep,
                "leverage":        float(t.get("leverage", 1)),
                "unrealized_pnl":  0.0,
                "breakeven_price": float(t.get("breakeven_price") or calc_breakeven(ep)),
                "source":          "army_state",
            })
    except Exception as e:
        logger.debug(f"State file load: {e}")

    return results


# ── ETA calculation ─────────────────────────────────────────────────────────

def calculate_eta(pos: dict) -> Optional[PositionETA]:
    try:
        symbol    = pos["symbol"]
        ep        = pos["entry_price"]
        breakeven = pos["breakeven_price"]
        if ep <= 0:
            return None

        current = get_current_price(symbol) or ep
        pct_from_entry   = ((current - ep) / ep) * 100
        pct_to_breakeven = ((breakeven - current) / current) * 100

        hourly_vol_pct = get_hourly_vol(symbol)

        if current >= breakeven:
            return PositionETA(
                symbol=symbol, side=pos.get("side", "buy"), leverage=pos["leverage"],
                entry_price=ep, current_price=current, breakeven_price=breakeven,
                volume=pos["volume"], cost_basis=pos["cost"],
                unrealized_pnl=pos.get("unrealized_pnl", 0),
                pct_to_breakeven=pct_to_breakeven, pct_from_entry=pct_from_entry,
                hourly_volatility_pct=hourly_vol_pct,
                eta_minutes=0, bullish_eta_minutes=0, bearish_eta_minutes=0,
                confidence=1.0, source=pos.get("source", "unknown"),
            )

        required = abs(pct_to_breakeven) / 100.0
        hv       = hourly_vol_pct / 100.0

        base_h    = min(required / hv, 999) if hv > 0 else 999
        bull_h    = max(0, (required - hv) / hv) if hv > 0 else 999
        bear_h    = min((required + hv) / hv, 999) if hv > 0 else 999

        eta_min   = base_h * 60 * 0.5
        bull_min  = bull_h * 60 * 0.5
        bear_min  = bear_h * 60 * 0.5

        confidence = min(1.0, (hourly_vol_pct / max(abs(pct_to_breakeven), 0.01)) * 0.5)

        return PositionETA(
            symbol=symbol, side=pos.get("side", "buy"), leverage=pos["leverage"],
            entry_price=ep, current_price=current, breakeven_price=breakeven,
            volume=pos["volume"], cost_basis=pos["cost"],
            unrealized_pnl=pos.get("unrealized_pnl", 0),
            pct_to_breakeven=pct_to_breakeven, pct_from_entry=pct_from_entry,
            hourly_volatility_pct=hourly_vol_pct,
            eta_minutes=eta_min, bullish_eta_minutes=bull_min, bearish_eta_minutes=bear_min,
            confidence=confidence, source=pos.get("source", "unknown"),
        )
    except Exception as e:
        logger.error(f"ETA calc {pos.get('symbol','?')}: {e}")
        return None


# ── main class ──────────────────────────────────────────────────────────────

class MarginETAPredictor:

    def predict_all(self) -> List[PositionETA]:
        raw = load_from_kraken_api()
        if not raw:
            raw = load_from_state_files()
        if not raw:
            logger.warning("No open margin positions found in any source")
            return []
        return [eta for pos in raw if (eta := calculate_eta(pos))]

    def print_report(self, etas: List[PositionETA]) -> None:
        print("\n" + "=" * 90)
        print("  MARGIN ETA REPORT — TIME-TO-PROFITABILITY")
        print("=" * 90)
        print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        if not etas:
            print("  No active margin positions.\n")
            return

        for eta in etas:
            src = "LIVE API" if eta.source == "kraken_api" else "STATE FILE"
            print(f"  [{src}] {eta.symbol}  |  {eta.side.upper()}  |  {eta.leverage:.0f}x leverage")
            print(f"    Entry:      {eta.entry_price:.4f}")
            print(f"    Current:    {eta.current_price:.4f}  ({eta.pct_from_entry:+.2f}%)")
            print(f"    Breakeven:  {eta.breakeven_price:.4f}  ({eta.pct_to_breakeven:+.2f}% to go)")
            if eta.unrealized_pnl:
                print(f"    Live P&L:   ${eta.unrealized_pnl:+.2f}")
            print()
            if eta.eta_minutes == 0:
                print("    ✅  PROFITABLE NOW")
            else:
                print(f"    📊  Hourly vol: {eta.hourly_volatility_pct:.2f}%")
                print(f"    ⏱   ETA base:   {eta.eta_minutes:.0f}m  ({eta.eta_minutes/60:.1f}h)")
                print(f"        Bullish:    {eta.bullish_eta_minutes:.0f}m  ({eta.bullish_eta_minutes/60:.1f}h)")
                print(f"        Bearish:    {eta.bearish_eta_minutes:.0f}m  ({eta.bearish_eta_minutes/60:.1f}h)")
                print(f"    🎯  Confidence: {eta.confidence*100:.0f}%")
            print()

        tc  = sum(e.cost_basis for e in etas)
        tp  = sum(e.unrealized_pnl for e in etas)
        ok  = sum(1 for e in etas if e.eta_minutes == 0)
        print("=" * 90)
        line = f"  {len(etas)} position(s)  |  {ok} profitable  |  Total cost: ${tc:.2f}"
        if tp:
            line += f"  |  Live P&L: ${tp:+.2f}"
        print(line)
        print("=" * 90 + "\n")


# ── entry point ─────────────────────────────────────────────────────────────

def main():
    import sys
    p = MarginETAPredictor()
    etas = p.predict_all()
    p.print_report(etas)
    try:
        with open("margin_eta_report.json", "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(),
                       "positions": [asdict(e) for e in etas]}, f, indent=2)
    except Exception:
        pass
    if "--watch" in sys.argv:
        print("📡 WATCH MODE — updating every 60s (Ctrl+C to stop)\n")
        try:
            while True:
                time.sleep(60)
                etas = p.predict_all()
                p.print_report(etas)
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
