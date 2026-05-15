import json
import sqlite3

from aureon.exchanges.capital_asset_registry import (
    SCHEMA_VERSION,
    build_capital_asset_registry,
    write_capital_asset_registry,
)


class FakeCapitalClient:
    enabled = True

    def __init__(self):
        self.markets = [
            {
                "symbol": "GOLD",
                "epic": "CS.D.CFDGOLD.CFD.IP",
                "instrumentName": "Gold",
                "instrumentType": "COMMODITIES",
            },
            {
                "symbol": "AAPL",
                "epic": "CS.D.AAPL.CFD.IP",
                "instrumentName": "Apple Inc",
                "instrumentType": "SHARES",
            },
            {
                "symbol": "BTCUSD",
                "epic": "CS.D.BTCUSD.CFD.IP",
                "instrumentName": "Bitcoin / US Dollar",
                "instrumentType": "CRYPTO",
            },
        ]
        self.snapshots = {
            "CS.D.CFDGOLD.CFD.IP": {
                "instrument": {
                    "epic": "CS.D.CFDGOLD.CFD.IP",
                    "name": "Gold",
                    "type": "COMMODITIES",
                    "currency": "USD",
                    "marginFactor": 5,
                    "marginFactorUnit": "PERCENTAGE",
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 2000.0, "offer": 2001.0},
                "dealingRules": {"minDealSize": {"value": 0.1}},
            },
            "CS.D.AAPL.CFD.IP": {
                "instrument": {
                    "epic": "CS.D.AAPL.CFD.IP",
                    "name": "Apple Inc",
                    "type": "SHARES",
                    "currency": "USD",
                    "marginDepositBands": [{"margin": 20, "unit": "PERCENTAGE"}],
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 180.0, "offer": 180.12},
                "dealingRules": {"minDealSize": {"value": 1}},
            },
            "CS.D.BTCUSD.CFD.IP": {
                "instrument": {
                    "epic": "CS.D.BTCUSD.CFD.IP",
                    "name": "Bitcoin / US Dollar",
                    "type": "CRYPTO",
                    "currency": "USD",
                    "marginFactor": 50,
                    "marginFactorUnit": "PERCENTAGE",
                },
                "snapshot": {"marketStatus": "TRADEABLE", "bid": 100000.0, "offer": 100010.0},
                "dealingRules": {"minDealSize": {"value": 0.01}},
            },
        }

    def get_all_markets(self, force_refresh=False):
        return list(self.markets)

    def _get_market_snapshot(self, epic, cache_ttl=300.0):
        return self.snapshots.get(epic)


def test_capital_asset_registry_builds_every_market_and_execution_routes():
    report = build_capital_asset_registry(client=FakeCapitalClient(), max_snapshots=-1)

    assert report["schema_version"] == SCHEMA_VERSION
    assert report["summary"]["total_markets"] == 3
    assert report["summary"]["snapshot_enriched_count"] == 3

    assets = {asset["symbol"]: asset for asset in report["assets"]}
    gold = assets["GOLD"]
    assert gold["asset_class"] == "commodity_cfd"
    assert gold["minimum_deal_size"] == 0.1
    assert gold["margin_factor_pct"] == 5.0
    assert gold["leverage_estimate"] == 20.0
    assert gold["min_notional_estimate"] == 200.05
    assert gold["margin_required_for_min_deal"] == 10.0025
    assert gold["trade_ready"] is True
    assert 'client.place_market_order(symbol, "BUY", size)' == gold["buy_call"]
    assert 'client.place_market_order(symbol, "SELL", size)' == gold["sell_call"]

    btc = assets["BTCUSD"]
    assert btc["can_buy"] is False
    assert btc["can_sell"] is False
    assert btc["trade_ready"] is False
    assert "capital_client_crypto_guard_blocks_direct_order" in btc["blockers"]


def test_capital_asset_registry_marks_unsampled_markets_as_known_but_not_ready():
    report = build_capital_asset_registry(client=FakeCapitalClient(), max_snapshots=1)

    assets = {asset["symbol"]: asset for asset in report["assets"]}
    assert assets["GOLD"]["snapshot_status"] == "fresh_snapshot"
    assert assets["AAPL"]["snapshot_status"] == "snapshot_not_sampled_budget"
    assert assets["AAPL"]["trade_ready"] is False
    assert "snapshot_not_sampled_budget" in assets["AAPL"]["blockers"]
    assert report["summary"]["known_but_not_sampled_count"] == 2


def test_write_capital_asset_registry_outputs_json_csv_sqlite_and_markdown(tmp_path):
    report = build_capital_asset_registry(client=FakeCapitalClient(), max_snapshots=-1)
    paths = write_capital_asset_registry(
        report,
        state_json=tmp_path / "state" / "registry.json",
        output_json=tmp_path / "docs" / "registry.json",
        output_csv=tmp_path / "docs" / "registry.csv",
        output_md=tmp_path / "docs" / "registry.md",
        output_db=tmp_path / "state" / "registry.sqlite",
        public_json=tmp_path / "public" / "registry.json",
    )

    for path in paths.values():
        assert path

    public_payload = json.loads((tmp_path / "public" / "registry.json").read_text(encoding="utf-8"))
    assert public_payload["summary"]["total_markets"] == 3
    assert "GOLD" in (tmp_path / "docs" / "registry.csv").read_text(encoding="utf-8")
    assert "Capital Tradable Asset Registry" in (tmp_path / "docs" / "registry.md").read_text(encoding="utf-8")

    conn = sqlite3.connect(str(tmp_path / "state" / "registry.sqlite"))
    try:
        count = conn.execute("SELECT COUNT(*) FROM capital_assets").fetchone()[0]
        gold = conn.execute(
            "SELECT trade_ready, buy_call FROM capital_assets WHERE symbol='GOLD'"
        ).fetchone()
    finally:
        conn.close()
    assert count == 3
    assert gold[0] == 1
    assert 'place_market_order(symbol, "BUY", size)' in gold[1]


def test_capital_asset_registry_does_not_emit_secret_like_market_fields():
    client = FakeCapitalClient()
    client.markets[0]["apiKey"] = "SECRET-DO-NOT-EMIT"
    report = build_capital_asset_registry(client=client, max_snapshots=-1)

    rendered = json.dumps(report)
    assert "SECRET-DO-NOT-EMIT" not in rendered
    assert "apiKey" not in rendered
