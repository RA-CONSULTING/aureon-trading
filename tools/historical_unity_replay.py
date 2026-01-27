#!/usr/bin/env python3
"""Historical Unity Replay (BUY + SELL + CONVERT) using real candles.

Goal: demonstrate the integrated Unity + Conversion Commando loop on historical
price data with high throughput (speed is key).

Data source:
- Coinbase Exchange public candles endpoint (1-minute granularity).

What it runs:
- Unity gate (dynamic net-profit floor: penny minimum + optional equity scaling)
- BUY (only when unity allows)
- SELL (only when penny net after fees is secured)
- CONVERT (via AdaptiveConversionCommando + ConversionLadder)

This does NOT require API keys and does NOT place real orders.

Examples:
  python -u tools/historical_unity_replay.py --minutes 180 --pairs BTC-USD,ETH-USD,SOL-USD
  AUREON_LADDER_NET_PROFIT_PCT=0.001 python -u tools/historical_unity_replay.py --minutes 240 --pairs BTC-USD,ETH-USD

Notes:
- If Coinbase is unreachable, the script will exit with a clear error.
"""

from __future__ import annotations
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aureon_conversion_ladder import ConversionLadder
from aureon_conversion_commando import AdaptiveConversionCommando


STABLE = "USDT"


def _http_get_json(url: str, timeout_s: float = 20.0) -> Any:
    req = Request(url, headers={"User-Agent": "aureon-historical-replay"})
    with urlopen(req, timeout=timeout_s) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_coinbase_candles(product: str, minutes: int) -> List[Tuple[int, float]]:
    """Return list of (ts, close) oldest->newest for last N minutes."""
    # Coinbase Exchange candles endpoint returns: [ time, low, high, open, close, volume ]
    # Max 300 candles per request.
    gran = 60
    remaining = int(minutes)
    out: List[Tuple[int, float]] = []
    end = int(time.time())

    while remaining > 0:
        batch = min(remaining, 300)
        start = end - batch * 60
        url = (
            f"https://api.exchange.coinbase.com/products/{product}/candles"
            f"?granularity={gran}&start={start}&end={end}"
        )
        data = _http_get_json(url)
        if not isinstance(data, list) or not data:
            raise RuntimeError(f"no candle data for {product}")

        # Data is newest-first; convert to oldest-first
        chunk: List[Tuple[int, float]] = []
        for row in data:
            try:
                ts = int(row[0])
                close = float(row[4])
            except Exception:
                continue
            chunk.append((ts, close))
        chunk.sort(key=lambda x: x[0])

        # Avoid duplicates across overlapping windows
        if out and chunk:
            last_ts = out[-1][0]
            chunk = [c for c in chunk if c[0] > last_ts]

        out.extend(chunk)
        remaining -= batch
        end = start

        # Respect public API a bit
        time.sleep(0.15)

    out.sort(key=lambda x: x[0])
    if len(out) < 10:
        raise RuntimeError(f"insufficient candles for {product}: {len(out)}")
    return out


def required_net_profit_floor(equity: float) -> float:
    penny = float(os.getenv("AUREON_LADDER_PENNY_MIN_NET", "0.01") or 0.01)
    abs_floor = float(os.getenv("AUREON_LADDER_NET_PROFIT_FLOOR", "0") or 0.0)
    pct = float(os.getenv("AUREON_LADDER_NET_PROFIT_PCT", "0") or 0.0)
    floor = max(penny, abs_floor)
    if pct > 0 and equity > 0:
        floor = max(floor, equity * pct)
    return floor


@dataclass
class Position:
    asset: str
    qty: float
    entry_price: float
    entry_fee: float


class ReplayClient:
    """Client facade for ConversionLadder/Commando during replay."""

    def __init__(self, *, initial_usdt: float, universe_assets: List[str]):
        self.dry_run = True
        self.clients = {"binance": type("C", (), {"dry_run": True})()}

        self.balances: Dict[str, Dict[str, float]] = {"binance": {STABLE: float(initial_usdt)}}

        # simple conversion graph: USDT <-> any asset, plus some bluechip cross edges
        conv = {STABLE: list(universe_assets)}
        for a in universe_assets:
            conv[a] = [STABLE]
        if "BTC" in universe_assets and "ETH" in universe_assets:
            conv["BTC"].append("ETH")
            conv["ETH"].append("BTC")

        self.convertible = {"binance": conv}
        self.prices: Dict[str, float] = {STABLE: 1.0}

    def set_prices(self, prices: Dict[str, float]) -> None:
        self.prices = {**{STABLE: 1.0}, **{k: float(v) for k, v in prices.items()}}

    def get_all_balances(self):
        return self.balances

    def get_all_convertible_assets(self):
        return self.convertible

    def find_conversion_path(self, exchange: str, from_asset: str, to_asset: str):
        ex = exchange.lower()
        nxt = self.convertible.get(ex, {}).get(from_asset, [])
        if to_asset in nxt:
            return [{"pair": f"{from_asset}{to_asset}", "side": "CONVERT"}]
        return []

    def convert_to_quote(self, exchange: str, asset: str, amount: float, quote: str):
        if quote != STABLE:
            return 0.0
        if asset == STABLE:
            return float(amount)
        return float(amount) * float(self.prices.get(asset, 0.0))

    def convert_crypto(self, exchange: str, from_asset: str, to_asset: str, amount: float):
        # conversion with a small fee
        ex = exchange.lower()
        b = self.balances.setdefault(ex, {})
        amt = float(amount)
        if amt <= 0:
            return {"error": "amount<=0"}
        if b.get(from_asset, 0.0) < amt:
            return {"error": "insufficient"}
        if not self.find_conversion_path(ex, from_asset, to_asset):
            return {"error": "no_path"}

        fee_rate = 0.0005
        from_val = self.convert_to_quote(ex, from_asset, amt, STABLE)
        fee = from_val * fee_rate
        to_val = max(0.0, from_val - fee)
        to_qty = to_val / (self.prices.get(to_asset, 1.0) if to_asset != STABLE else 1.0)

        b[from_asset] = b.get(from_asset, 0.0) - amt
        b[to_asset] = b.get(to_asset, 0.0) + to_qty
        return {"ok": True, "fee_usdt": fee, "from": from_asset, "to": to_asset, "to_qty": to_qty}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--minutes", type=int, default=180)
    p.add_argument("--pairs", type=str, default="BTC-USD,ETH-USD")
    p.add_argument("--initial", type=float, default=1000.0)
    p.add_argument("--max-lines", type=int, default=120)
    args = p.parse_args()

    pairs = [s.strip().upper() for s in args.pairs.split(",") if s.strip()]
    if not pairs:
        print("No pairs provided")
        return 2

    # Map Coinbase products to internal assets
    asset_by_product: Dict[str, str] = {}
    for pr in pairs:
        asset_by_product[pr] = pr.split("-")[0]

    # Fetch candles
    candles_by_asset: Dict[str, List[Tuple[int, float]]] = {}
    for pr in pairs:
        asset = asset_by_product[pr]
        print(f"📥 Fetching {args.minutes}m candles for {pr}...")
        try:
            candles = fetch_coinbase_candles(pr, args.minutes)
        except Exception as e:
            print(f"❌ Failed to fetch {pr}: {e}")
            return 3
        candles_by_asset[asset] = candles
        print(f"   ✅ {asset}: {len(candles)} candles")

    # Align timeline (use the shortest series)
    min_len = min(len(v) for v in candles_by_asset.values())
    for a in list(candles_by_asset.keys()):
        candles_by_asset[a] = candles_by_asset[a][-min_len:]

    assets = sorted(candles_by_asset.keys())
    client = ReplayClient(initial_usdt=args.initial, universe_assets=assets)

    os.environ.setdefault("AUREON_LADDER_ENABLED", "1")
    os.environ.setdefault("AUREON_LADDER_MODE", "suggest")
    os.environ.setdefault("AUREON_LADDER_BOOTSTRAP", "1")

    ladder = ConversionLadder(bus=None, mycelium=None, client=client)
    commando = AdaptiveConversionCommando(bus=None, mycelium=None, client=client, ladder=ladder)

    positions: Dict[str, Position] = {}
    realized_pnl = 0.0
    total_fees = 0.0

    start_ts = time.perf_counter()
    printed = 0

    print("=" * 78)
    print("HISTORICAL UNITY REPLAY | BUY + SELL + CONVERT | SPEED RUN")
    print("=" * 78)

    for i in range(min_len):
        # Build current prices
        prices: Dict[str, float] = {}
        for a in assets:
            prices[a] = candles_by_asset[a][i][1]
        client.set_prices(prices)

        # Build ticker_cache (momentum as 1-step return; volume constant)
        ticker_cache: Dict[str, Dict[str, Any]] = {}
        for a in assets:
            sym = f"{a}{STABLE}"
            if i > 0:
                prev = candles_by_asset[a][i - 1][1]
                mom = ((prices[a] / prev) - 1.0) * 100.0 if prev else 0.0
            else:
                mom = 0.0
            ticker_cache[sym] = {"price": prices[a], "volume": 20_000_000.0, "change24h": mom}

        # Mark-to-market equity
        b = client.get_all_balances()["binance"]
        equity = b.get(STABLE, 0.0)
        for asset, qty in b.items():
            if asset == STABLE:
                continue
            equity += qty * prices.get(asset, 0.0)
        for pos in positions.values():
            equity += pos.qty * prices[pos.asset]

        net_profit = equity - args.initial
        floor = required_net_profit_floor(equity)
        unity_mode = "ADVANCE" if (net_profit >= floor or (realized_pnl == 0.0 and net_profit >= 0)) else "HOLD_LINE"

        # SELL: take penny net after fees
        to_close: List[str] = []
        for a, pos in positions.items():
            gross = (prices[a] - pos.entry_price) * pos.qty
            exit_fee = (prices[a] * pos.qty) * 0.00075
            net = gross - pos.entry_fee - exit_fee
            if net >= 0.01:
                to_close.append(a)

        for a in to_close:
            pos = positions.pop(a)
            gross = (prices[a] - pos.entry_price) * pos.qty
            exit_fee = (prices[a] * pos.qty) * 0.00075
            net = gross - pos.entry_fee - exit_fee
            realized_pnl += net
            total_fees += (pos.entry_fee + exit_fee)
            proceeds = pos.qty * prices[a] - exit_fee
            b[STABLE] = b.get(STABLE, 0.0) + proceeds
            if printed < args.max_lines:
                print(f"T{i:04d} SELL {a}: net=${net:.4f} realized=${realized_pnl:.4f}")
                printed += 1

        # BUY: choose top momentum asset
        best = max(assets, key=lambda a: ticker_cache[f"{a}{STABLE}"]["change24h"])
        if unity_mode == "ADVANCE":
            if best not in positions and b.get(STABLE, 0.0) > 20.0:
                spend = min(80.0, b[STABLE] * 0.10)
                fee = spend * 0.00075
                qty = (spend - fee) / prices[best]
                b[STABLE] -= spend
                positions[best] = Position(asset=best, qty=qty, entry_price=prices[best], entry_fee=fee)
                total_fees += fee
                if printed < args.max_lines:
                    print(f"T{i:04d} BUY  {best}: spend=${spend:.2f} mom={ticker_cache[f'{best}{STABLE}']['change24h']:+.3f}%")
                    printed += 1

        # CONVERT: keep capital aligned with current best
        preferred_assets = [best]
        locked_assets = list(positions.keys())
        mission = commando.step(
            ticker_cache=ticker_cache,
            scan_direction="A→Z" if i % 2 else "Z→A",
            net_profit=net_profit,
            portfolio_equity=equity,
            balances=client.get_all_balances(),
            preferred_assets=preferred_assets,
            locked_assets=locked_assets,
        )
        if mission and printed < args.max_lines:
            print(f"T{i:04d} CONVERT {mission.from_asset}->{mission.to_asset} dir={mission.direction} mode={unity_mode}")
            printed += 1

        if printed < args.max_lines and (i % 20 == 0):
            pos_str = ",".join(sorted(positions.keys())) or "none"
            print(f"T{i:04d} MODE={unity_mode} equity=${equity:.2f} net=${net_profit:+.2f} floor=${floor:.2f} cash=${b.get(STABLE,0):.2f} pos=[{pos_str}]")
            printed += 1

    elapsed = time.perf_counter() - start_ts
    tps = min_len / max(elapsed, 1e-9)
    print("=" * 78)
    print(f"END: steps={min_len} elapsed={elapsed:.2f}s ({tps:.1f} steps/s) equity=${equity:.2f} net=${(equity-args.initial):+.2f} realized=${realized_pnl:.2f} fees=${total_fees:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
