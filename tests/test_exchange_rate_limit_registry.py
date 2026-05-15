from aureon.core.exchange_rate_limit_registry import (
    build_cash_aware_rate_plan,
    get_exchange_rate_limit,
    official_rate_limit_profiles,
)


def test_official_exchange_rate_limit_profiles_cover_live_venues():
    profiles = official_rate_limit_profiles()

    for exchange in ("binance", "kraken", "alpaca", "capital"):
        profile = profiles[exchange]
        assert profile["official_doc_url"].startswith("https://")
        assert profile["official_limit_model"]
        assert profile["official_limits"]
        assert profile["safe_governor_calls_per_min"] > 0

    assert profiles["kraken"]["official_limits"]["private_history_counter_increment"] == 4
    assert profiles["capital"]["official_limits"]["max_requests_per_sec_per_user"] == 10
    assert profiles["alpaca"]["official_limits"]["market_data_basic_historical_calls_per_min"] == 200
    assert profiles["binance"]["official_limits"]["websocket_connection_weight"] == 2


def test_cash_aware_rate_plan_boosts_idle_venue_data_without_exceeding_safe_budget():
    runtime = {
        "combined": {
            "capital_equity_gbp": 100.0,
            "kraken_equity": 0.0,
            "positions_by_exchange": {"capital": 1, "kraken": 0},
        }
    }

    plan = build_cash_aware_rate_plan(runtime)

    assert plan["capital"]["cash_or_position_active"] is True
    assert plan["capital"]["recommended_mode"] == "execution_positions_first"
    assert plan["kraken"]["data_boost_eligible"] is True
    assert plan["kraken"]["recommended_mode"] == "idle_cash_market_discovery_boost"
    assert plan["kraken"]["market_data_budget_per_min"] <= plan["kraken"]["safe_calls_per_min"]


def test_get_exchange_rate_limit_unknown_is_none():
    assert get_exchange_rate_limit("not-an-exchange") is None
