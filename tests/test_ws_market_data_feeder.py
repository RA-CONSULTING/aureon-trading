from aureon.data_feeds.ws_market_data_feeder import _extract_prices_and_tickers


def test_extract_prices_accepts_binance_websocket_payload():
    prices, ticker_cache = _extract_prices_and_tickers(
        [{"s": "BTCUSDT", "c": "50000.0", "P": "1.5", "v": "12.0"}],
        binance_uk_mode=False,
    )

    assert prices["BTC"] == 50000.0
    assert ticker_cache["BTCUSDT"]["change24h"] == 1.5
    assert ticker_cache["binance:BTCUSDT"]["volume"] == 12.0


def test_extract_prices_accepts_binance_rest_24hr_payload():
    prices, ticker_cache = _extract_prices_and_tickers(
        [
            {
                "symbol": "ETHUSDT",
                "lastPrice": "3200.0",
                "priceChangePercent": "2.25",
                "quoteVolume": "987654321.0",
            }
        ],
        binance_uk_mode=False,
    )

    assert prices["ETH"] == 3200.0
    assert ticker_cache["ETHUSDT"]["change24h"] == 2.25
    assert ticker_cache["ETHUSDT"]["volume"] == 987654321.0
