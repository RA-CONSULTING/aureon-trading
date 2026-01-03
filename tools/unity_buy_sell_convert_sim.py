#!/usr/bin/env python3
"""Unity Sim: BUY + SELL + CONVERT working toward one goal.

This is a self-contained simulation that demonstrates:
- A unified net-profit floor (penny minimum + optional equity scaling)
- BUY entries only when unity allows
- SELL exits when penny profit is achieved (after fees)
- CONVERT actions via AdaptiveConversionCommando + ConversionLadder

It does NOT call real exchanges.

Run:
  python tools/unity_buy_sell_convert_sim.py

Optional knobs:
  AUREON_LADDER_NET_PROFIT_PCT=0.001   # 0.1% of equity floor
  AUREON_LADDER_PENNY_MIN_NET=0.01
  AUREON_LADDER_ENABLED=1
  AUREON_LADDER_MODE=suggest
"""

from __future__ import annotations

import sys
from pathlib import Path

import math
import os
import random
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aureon_conversion_ladder import ConversionLadder
from aureon_conversion_commando import AdaptiveConversionCommando


STABLE = "USDT"
ASSETS = ["BTC", "ETH", "SOL", "ADA"]


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


class DummyExchangeClient:
    """Minimal MultiExchange-like client for sim."""

    def __init__(self):
        self.dry_run = True
        self.clients = {"binance": type("C", (), {"dry_run": True})()}

        self.balances: Dict[str, Dict[str, float]] = {"binance": {STABLE: 1000.0}}

        # conversion graph (simplified)
        self.convertible = {
            "binance": {
                STABLE: ["BTC", "ETH", "SOL", "ADA"],
                "BTC": [STABLE, "ETH"],
                "ETH": [STABLE, "BTC", "SOL"],
                "SOL": [STABLE, "ETH"],
                "ADA": [STABLE],
            }
        }

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
        # In sim, we only use USDT pricing and pass prices in via a global.
        if quote != STABLE:
            return 0.0
        price = SIM_PRICES.get(asset, 0.0)
        if asset == STABLE:
            price = 1.0
        return float(amount) * float(price)

    def convert_crypto(self, exchange: str, from_asset: str, to_asset: str, amount: float):
        # Sim conversion with a tiny conversion fee
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
        to_qty = to_val / (SIM_PRICES.get(to_asset, 1.0) if to_asset != STABLE else 1.0)

        b[from_asset] = b.get(from_asset, 0.0) - amt
        b[to_asset] = b.get(to_asset, 0.0) + to_qty
        return {"ok": True, "fee_usdt": fee, "from": from_asset, "to": to_asset, "to_qty": to_qty}


SIM_PRICES: Dict[str, float] = {STABLE: 1.0, "BTC": 40000.0, "ETH": 2500.0, "SOL": 110.0, "ADA": 0.6}


def make_ticker_cache() -> Dict[str, Dict[str, Any]]:
    # Create a minimal ticker cache used by ladder scoring.
    out: Dict[str, Dict[str, Any]] = {}
    for a in ASSETS:
        sym = f"{a}{STABLE}"
        out[sym] = {
            "price": SIM_PRICES[a],
            "volume": 20_000_000.0,
            "change24h": random.uniform(-3.0, 5.0),
        }
    return out


def main():
    random.seed(7)

    os.environ.setdefault("AUREON_LADDER_ENABLED", "1")
    os.environ.setdefault("AUREON_LADDER_MODE", "suggest")
    os.environ.setdefault("AUREON_LADDER_BOOTSTRAP", "1")

    client = DummyExchangeClient()

    ladder = ConversionLadder(bus=None, mycelium=None, client=client)
    commando = AdaptiveConversionCommando(bus=None, mycelium=None, client=client, ladder=ladder)

    positions: Dict[str, Position] = {}

    total_fees = 0.0
    realized_pnl = 0.0

    print("=" * 78)
    print("UNITY SIM (BUY + SELL + CONVERT) | ONE GOAL: SCALE NET PROFIT")
    print("=" * 78)

    for cycle in range(1, 31):
        # Drift prices upward slightly to allow net profit compounding.
        for a in ASSETS:
            drift = 1.0 + random.uniform(-0.002, 0.006)  # slight positive bias
            SIM_PRICES[a] *= drift

        # Mark-to-market equity
        b = client.get_all_balances()["binance"]
        equity = 0.0
        for asset, qty in b.items():
            equity += qty * (SIM_PRICES.get(asset, 1.0) if asset != STABLE else 1.0)
        for pos in positions.values():
            equity += pos.qty * SIM_PRICES[pos.asset]

        net_profit = (equity - 1000.0)
        floor = required_net_profit_floor(equity)
        # Bootstrap so we can start from flat baseline and still take the first trades.
        if realized_pnl == 0.0 and net_profit >= 0:
            unity_mode = "ADVANCE"
        else:
            unity_mode = "ADVANCE" if net_profit >= floor else "HOLD_LINE"

        # Build opportunities
        ticker_cache = make_ticker_cache()
        opps = sorted(
            (
                (sym.replace(STABLE, ""), t["change24h"], t["price"]) for sym, t in ticker_cache.items()
            ),
            key=lambda x: x[1],
            reverse=True,
        )
        best_asset, best_change, best_price = opps[0]

        # ═══════════════════════════════════════════════════════════════════════
        # 💡 DUAL PROFIT PATH: SELL vs CONVERT decision for each position
        # THE SYSTEM KNOWS: SELL and CONVERT are TWO WAYS to net profit!
        # ═══════════════════════════════════════════════════════════════════════
        to_close: List[str] = []
        to_convert: Dict[str, str] = {}  # asset -> target asset
        
        for a, pos in positions.items():
            gross = (SIM_PRICES[a] - pos.entry_price) * pos.qty
            exit_fee = (SIM_PRICES[a] * pos.qty) * 0.00075
            sell_net = gross - pos.entry_fee - exit_fee
            
            # Evaluate SELL vs CONVERT using commando's dual path evaluator
            decision = commando.evaluate_exit_path(
                asset=a,
                exchange="binance",
                quantity=pos.qty,
                entry_price=pos.entry_price,
                current_price=SIM_PRICES[a],
                ticker_cache=ticker_cache,
            )
            
            if decision.action == 'SELL' and sell_net >= 0.01:
                to_close.append(a)
            elif decision.action == 'CONVERT' and decision.convert_target:
                to_convert[a] = decision.convert_target
                # Still log the reasoning
                if sell_net >= 0.005:  # Near penny threshold
                    print(f"C{cycle:02d} 💡 {a}: CONVERT beats SELL (${decision.convert_expected_gain:.3f} > ${sell_net:.3f})")

        # Execute SELL exits
        for a in to_close:
            pos = positions.pop(a)
            gross = (SIM_PRICES[a] - pos.entry_price) * pos.qty
            exit_fee = (SIM_PRICES[a] * pos.qty) * 0.00075
            net = gross - pos.entry_fee - exit_fee
            realized_pnl += net
            total_fees += (pos.entry_fee + exit_fee)
            # credit proceeds back to USDT
            proceeds = pos.qty * SIM_PRICES[a] - exit_fee
            b[STABLE] = b.get(STABLE, 0.0) + proceeds
            print(f"C{cycle:02d} SELL {a}: net=${net:.4f} realized_pnl=${realized_pnl:.4f}")

        # BUY logic: only if unity says ADVANCE
        if unity_mode == "ADVANCE":
            if best_asset not in positions and b.get(STABLE, 0.0) > 20.0:
                spend = min(80.0, b[STABLE] * 0.10)
                fee = spend * 0.00075
                qty = (spend - fee) / SIM_PRICES[best_asset]
                b[STABLE] -= spend
                positions[best_asset] = Position(asset=best_asset, qty=qty, entry_price=SIM_PRICES[best_asset], entry_fee=fee)
                total_fees += fee
                print(f"C{cycle:02d} BUY  {best_asset}: spend=${spend:.2f} (chg24h={best_change:+.2f}%)")

        # CONVERT logic: run commando to keep capital aligned with opp universe
        preferred_assets = [best_asset]
        locked_assets = list(positions.keys())
        mission = commando.step(
            ticker_cache=ticker_cache,
            scan_direction="A→Z" if cycle % 2 else "Z→A",
            net_profit=net_profit,
            portfolio_equity=equity,
            balances=client.get_all_balances(),
            preferred_assets=preferred_assets,
            locked_assets=locked_assets,
        )
        if mission:
            print(f"C{cycle:02d} CONVERT {mission.from_asset}->{mission.to_asset} dir={mission.direction} (mode={unity_mode})")

        # Print cycle summary
        pos_str = ",".join(sorted(positions.keys())) or "none"
        print(
            f"C{cycle:02d} MODE={unity_mode} equity=${equity:.2f} net=${net_profit:+.2f} floor=${floor:.2f} "
            f"cash=${b.get(STABLE,0):.2f} pos=[{pos_str}]"
        )

    print("=" * 78)
    print(f"END: equity=${equity:.2f} net_profit=${(equity-1000):+.2f} realized_pnl=${realized_pnl:.2f} fees=${total_fees:.2f}")
    print(f"💡 DUAL PATH: The system evaluated SELL vs CONVERT for every position exit")


if __name__ == "__main__":
    main()
