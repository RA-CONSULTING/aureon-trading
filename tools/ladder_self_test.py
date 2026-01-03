#!/usr/bin/env python3
"""Self-test for ConversionLadder.

This is safe to run locally because it uses dummy clients and never touches real exchanges.

Usage:
  AUREON_LADDER_ENABLED=1 python tools/ladder_self_test.py
  AUREON_LADDER_ENABLED=1 AUREON_LADDER_DIRECTION=DOWN python tools/ladder_self_test.py
  AUREON_LADDER_ENABLED=1 AUREON_LADDER_MODE=execute python tools/ladder_self_test.py
"""

import os
from pprint import pprint

from aureon_conversion_ladder import ConversionLadder


class DummyClient:
    dry_run = True

    def __init__(self):
        self.clients = {
            "binance": type("C", (), {"dry_run": True})(),
        }

    def get_all_balances(self):
        # Kraken has a larger holding, but ladder should still prefer Binance by default.
        return {
            "kraken": {"USDT": 5000.0, "BTC": 0.02},
            "binance": {"USDT": 250.0, "ADA": 120.0, "ETH": 0.05},
        }

    def convert_to_quote(self, exchange, asset, amount, quote):
        # crude USD estimates for test purposes
        if asset == "USDT":
            return float(amount)
        if asset == "ADA":
            return float(amount) * 0.5
        if asset == "ETH":
            return float(amount) * 2000.0
        return 0.0

    def get_all_convertible_assets(self):
        return {
            "binance": {
                "USDT": ["BTC", "ETH", "ADA"],
                "ADA": ["USDT", "BTC", "ETH"],
                "ETH": ["USDT", "BTC"],
            }
            ,
            "kraken": {
                "USDT": ["BTC", "ETH"],
                "BTC": ["USDT"],
            }
        }

    def find_conversion_path(self, exchange, from_asset, to_asset):
        # represent a simple 1-hop path when a direct edge exists
        conv = self.get_all_convertible_assets().get(exchange, {})
        if to_asset in conv.get(from_asset, []):
            return [{"pair": f"{from_asset}{to_asset}", "side": "BUY"}]
        return []

    def convert_crypto(self, exchange, from_asset, to_asset, amount):
        raise RuntimeError("should not be called in this self-test (dry_run=True)")


class DummyMycelium:
    def get_queen_signal(self):
        return 0.8

    def get_network_coherence(self):
        return 0.8

    def rank_symbols_by_memory(self, symbols, ascending=False):
        return list(symbols)

    def add_signal(self, symbol, signal):
        print("mycelium.add_signal:", symbol, signal)


def main():
    os.environ.setdefault("AUREON_LADDER_ENABLED", "1")
    os.environ.setdefault("AUREON_LADDER_MODE", "suggest")
    # Example dynamic gate: require at least max($0.01, equity*0.1%) net profit to allow UP.
    os.environ.setdefault("AUREON_LADDER_NET_PROFIT_PCT", "0.001")

    ladder = ConversionLadder(bus=None, mycelium=DummyMycelium(), client=DummyClient())

    decision = ladder.step(
        ticker_cache={
            "ADAUSDT": {"change24h": 2.0, "volume": 20_000_000},
            "BTCUSDT": {"change24h": 0.8, "volume": 50_000_000},
            "ETHUSDT": {"change24h": 1.2, "volume": 35_000_000},
        },
        scan_direction="A→Z",
        net_profit=1.23,
        portfolio_equity=10_000.0,
    )

    print("\nDecision:")
    pprint(decision)

    decision2 = ladder.step(
        ticker_cache={
            "ADAUSDT": {"change24h": 4.0, "volume": 25_000_000},
            "BTCUSDT": {"change24h": 1.0, "volume": 60_000_000},
            "ETHUSDT": {"change24h": 2.2, "volume": 40_000_000},
        },
        scan_direction="A→Z",
        net_profit=-0.50,
        portfolio_equity=10_000.0,
    )

    print("\nDecision (net_profit negative => de-risk DOWN / no stable churn):")
    pprint(decision2)


if __name__ == "__main__":
    main()
