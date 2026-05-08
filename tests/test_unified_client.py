#!/usr/bin/env python3
"""Smoke tests and manual diagnostic for the unified exchange client."""

from types import SimpleNamespace

from aureon.core.aureon_baton_link import link_system as _baton_link

_baton_link(__name__)

from aureon.trading import unified_exchange_client as uec


def _fake_exchange_client(exchange_id: str):
    def get_24h_tickers():
        return [{"symbol": f"{exchange_id.upper()}USD", "lastPrice": 1.0}]

    return SimpleNamespace(
        exchange_id=exchange_id,
        dry_run=True,
        get_24h_tickers=get_24h_tickers,
        get_all_balances=lambda: {},
        get_balance=lambda _asset: 0.0,
    )


def test_multi_exchange_client_get_24h_tickers_tags_sources(monkeypatch):
    monkeypatch.setattr(uec, "UnifiedExchangeClient", _fake_exchange_client)

    client = uec.MultiExchangeClient()
    tickers = client.get_24h_tickers()

    assert [ticker["source"] for ticker in tickers] == [
        "kraken",
        "binance",
        "alpaca",
        "capital",
    ]
    assert all(ticker["lastPrice"] == 1.0 for ticker in tickers)


def run_diagnostic() -> int:
    """Manual real-client diagnostic. This may call exchange/network APIs."""
    print("Testing MultiExchangeClient.get_24h_tickers()...")
    print("=" * 60)

    client = uec.MultiExchangeClient()
    for name, exchange_client in getattr(client, "clients", {}).items():
        print(f"\n{name.upper()}:")
        print(f"   Client type: {type(exchange_client)}")
        print(f"   Has get_24h_tickers: {hasattr(exchange_client, 'get_24h_tickers')}")
        try:
            tickers = exchange_client.get_24h_tickers()
            print(f"   Returned: {len(tickers)} tickers")
            if tickers:
                print(f"   First ticker: {tickers[0]}")
        except Exception as exc:
            print(f"   ERROR: {type(exc).__name__}: {exc}")

    try:
        all_tickers = client.get_24h_tickers()
        print(f"\nTotal tickers from all exchanges: {len(all_tickers)}")
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(run_diagnostic())
