import time

from aureon.strategies.hnc_probability_matrix import HNCProbabilityIntegration


def test_short_horizon_prediction_returns_forecast():
    h = HNCProbabilityIntegration()
    base_ts = time.time()

    # Feed an upward tape with buy-side imbalance
    for i in range(8):
        price = 100.0 + (i * 0.02)
        h.feed_live_ticker_frame(
            symbol="BTCUSD",
            source="kraken",
            price=price,
            bid=price - 0.01,
            ask=price + 0.01,
            bid_size=120 + i * 5,
            ask_size=80,
            trade_volume=50 + i,
            coherence=0.7,
            planetary_alignment=0.2,
            solar_risk=0.05,
            timestamp=base_ts + (i * 5),
        )

    pred = h.predict_short_horizon("BTCUSD")

    assert pred["status"] == "ok"
    assert pred["probability_up"] > pred["probability_down"]
    assert pred["expected_price_30s"] > 0
    assert pred["expected_price_40s"] > 0
    assert 0.0 < pred["confidence"] <= 0.99


def test_short_horizon_insufficient_data_guardrail():
    h = HNCProbabilityIntegration()

    pred = h.predict_short_horizon("ETHUSD")
    assert pred["status"] == "insufficient_data"
