import json
import time

from aureon.data_feeds import unified_market_cache as cache_mod


def test_unified_market_cache_reads_ws_prices_default_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(cache_mod, "CACHE_DIR", str(tmp_path))
    monkeypatch.setattr(cache_mod, "WS_PRICE_CACHE_PATH", str(tmp_path / "ws_prices.json"))
    monkeypatch.setattr(cache_mod, "BINANCE_CACHE_PATH", str(tmp_path / "binance_ws_prices.json"))
    monkeypatch.setattr(cache_mod, "BINANCE_CACHE_PATHS", [str(tmp_path / "ws_prices.json"), str(tmp_path / "binance_ws_prices.json")])
    monkeypatch.setattr(cache_mod, "UNIFIED_CACHE_PATH", str(tmp_path / "unified_prices.json"))
    monkeypatch.setattr(cache_mod, "KRAKEN_CACHE_PATH", str(tmp_path / "kraken_prices.json"))
    cache_mod.UnifiedMarketCache._instance = None
    cache_mod._cache_instance = None

    now = time.time()
    (tmp_path / "ws_prices.json").write_text(
        json.dumps(
            {
                "generated_at": now,
                "source": "binance_ws",
                "prices": {"BTC": 50123.45},
                "ticker_cache": {
                    "BTCUSDT": {
                        "price": 50123.45,
                        "change24h": 1.8,
                        "volume": 2000.0,
                        "base": "BTC",
                        "quote": "USDT",
                        "exchange": "binance",
                    }
                },
            }
        ),
        encoding="utf-8",
    )

    ticker = cache_mod.get_ticker("BTC", max_age=5.0)

    assert ticker is not None
    assert ticker.price == 50123.45
    assert ticker.source == "binance_ws"
    cache_mod.UnifiedMarketCache._instance = None
    cache_mod._cache_instance = None
