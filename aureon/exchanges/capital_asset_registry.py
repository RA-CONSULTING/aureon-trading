"""Capital.com tradable asset registry.

This module builds the local asset book Aureon needs before it can route
Capital CFD decisions cleanly: every discovered Capital market, its epic,
cost/margin evidence when sampled, and the internal BUY/SELL code path.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sqlite3
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from aureon.exchanges.capital_client import CapitalClient


SCHEMA_VERSION = "aureon-capital-tradable-asset-registry-v1"
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STATE_JSON = REPO_ROOT / "state/aureon_capital_tradable_asset_registry.json"
DEFAULT_OUTPUT_JSON = REPO_ROOT / "docs/audits/aureon_capital_tradable_asset_registry.json"
DEFAULT_OUTPUT_CSV = REPO_ROOT / "docs/audits/aureon_capital_tradable_asset_registry.csv"
DEFAULT_OUTPUT_MD = REPO_ROOT / "docs/audits/aureon_capital_tradable_asset_registry.md"
DEFAULT_OUTPUT_DB = REPO_ROOT / "state/capital_tradable_asset_registry.sqlite"
DEFAULT_PUBLIC_JSON = REPO_ROOT / "frontend/public/aureon_capital_tradable_asset_registry.json"

CRYPTO_PATTERNS = (
    "USDT",
    "USDC",
    "BTC",
    "ETH",
    "XBT",
    "SOL",
    "ADA",
    "XRP",
    "DOGE",
    "SHIB",
    "AVAX",
    "DOT",
    "LINK",
    "MATIC",
    "UNI",
    "ATOM",
    "LTC",
    "BCH",
    "ETC",
    "XLM",
    "ALGO",
    "FIL",
    "VET",
)

TRADEABLE_MARKET_STATES = {
    "TRADEABLE",
    "OPEN",
    "OPENED",
    "ONLINE",
    "AVAILABLE",
}

CSV_FIELDS = [
    "symbol",
    "epic",
    "instrument_name",
    "asset_class",
    "instrument_type",
    "market_status",
    "currency",
    "snapshot_status",
    "bid",
    "ask",
    "mid_price",
    "spread",
    "spread_pct",
    "minimum_deal_size",
    "min_notional_estimate",
    "margin_factor_pct",
    "margin_required_for_min_deal",
    "leverage_estimate",
    "can_buy",
    "can_sell",
    "trade_ready",
    "blockers",
    "buy_call",
    "sell_call",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
        if math.isfinite(number):
            return number
    except Exception:
        pass
    return default


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _canonical(value: Any) -> str:
    return "".join(ch for ch in str(value or "").upper() if ch.isalnum())


def _first_text(*values: Any) -> str:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return ""


def _nested(mapping: dict[str, Any], *path: str) -> Any:
    cur: Any = mapping
    for key in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(key)
    return cur


def _normalize_margin_pct(candidate: Any, unit: str = "") -> float:
    value = _as_float(candidate, 0.0)
    if value <= 0:
        return 0.0
    unit_text = str(unit or "").strip().upper()
    if unit_text in {"PERCENT", "PERCENTAGE", "PCT", "%"}:
        return value
    if unit_text in {"FACTOR", "DECIMAL", "FRACTION", "RATIO"}:
        return value * 100.0
    if value < 1.0:
        return value * 100.0
    return value


def extract_min_deal_size(market_info: dict[str, Any]) -> float:
    if not isinstance(market_info, dict):
        return 0.0
    candidates = [
        _nested(market_info, "dealingRules", "minDealSize", "value"),
        _nested(market_info, "dealingRules", "minDealSize"),
        _nested(market_info, "dealingRules", "minimumDealSize", "value"),
        _nested(market_info, "dealingRules", "minimumDealSize"),
        _nested(market_info, "instrument", "minDealSize"),
        _nested(market_info, "instrument", "minimumDealSize"),
        market_info.get("minDealSize"),
        market_info.get("minimumDealSize"),
    ]
    for candidate in candidates:
        value = _as_float(candidate, 0.0)
        if value > 0:
            return value
    return 0.0


def extract_margin_factor_pct(market_info: dict[str, Any]) -> float:
    if not isinstance(market_info, dict):
        return 0.0
    instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
    dealing_rules = market_info.get("dealingRules", {}) if isinstance(market_info.get("dealingRules"), dict) else {}
    snapshot = market_info.get("snapshot", {}) if isinstance(market_info.get("snapshot"), dict) else {}
    margin_unit = _first_text(
        instrument.get("marginFactorUnit"),
        dealing_rules.get("marginFactorUnit"),
        snapshot.get("marginFactorUnit"),
        market_info.get("marginFactorUnit"),
    )
    candidates: list[tuple[Any, str]] = [
        (instrument.get("marginFactor"), margin_unit),
        (instrument.get("marginFactorPercent"), "PERCENTAGE"),
        (instrument.get("marginRate"), margin_unit),
        (dealing_rules.get("marginFactor"), _first_text(dealing_rules.get("marginFactorUnit"), margin_unit)),
        (snapshot.get("marginFactor"), _first_text(snapshot.get("marginFactorUnit"), margin_unit)),
        (market_info.get("marginFactor"), _first_text(market_info.get("marginFactorUnit"), margin_unit)),
    ]
    band_sources = [
        instrument.get("marginDepositBands"),
        instrument.get("depositBands"),
        market_info.get("marginDepositBands"),
        market_info.get("depositBands"),
    ]
    for bands in band_sources:
        if not isinstance(bands, list):
            continue
        for band in bands:
            if not isinstance(band, dict):
                continue
            band_unit = _first_text(band.get("marginFactorUnit"), band.get("unit"), margin_unit)
            candidates.extend(
                [
                    (band.get("margin"), band_unit),
                    (band.get("marginFactor"), band_unit),
                    (band.get("marginRate"), band_unit),
                    (band.get("value"), band_unit),
                ]
            )
    for candidate, unit in candidates:
        value = _normalize_margin_pct(candidate, unit)
        if value > 0:
            return value
    return 0.0


def market_status_text(market_info: dict[str, Any], market_row: Optional[dict[str, Any]] = None) -> str:
    row = market_row or {}
    for candidate in (
        _nested(market_info, "snapshot", "marketStatus"),
        market_info.get("marketStatus") if isinstance(market_info, dict) else None,
        _nested(market_info, "instrument", "marketStatus"),
        _nested(market_info, "instrument", "tradingStatus"),
        row.get("marketStatus"),
        row.get("status"),
    ):
        text = _clean_text(candidate)
        if text:
            return text.upper()
    return "UNKNOWN"


def _infer_asset_class(market_row: dict[str, Any], market_info: dict[str, Any]) -> str:
    instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
    raw = " ".join(
        str(value or "")
        for value in (
            market_row.get("assetClass"),
            market_row.get("nodeName"),
            market_row.get("instrumentType"),
            market_row.get("marketType"),
            instrument.get("type"),
            instrument.get("instrumentType"),
            instrument.get("name"),
            market_row.get("instrumentName"),
        )
    )
    raw = " ".join(raw.replace("_", " ").upper().split())
    if any(token in raw for token in ("FOREX", "CURRENCY", "FX")):
        return "forex"
    if any(token in raw for token in ("SHARE", "STOCK", "EQUITY")):
        return "stock_cfd"
    if "INDEX" in raw or "INDICES" in raw:
        return "index_cfd"
    if any(token in raw for token in ("COMMODITY", "METAL", "ENERGY", "OIL", "GOLD", "SILVER")):
        return "commodity_cfd"
    if "CRYPTO" in raw:
        return "crypto_guarded"
    return "unknown"


def _is_crypto_guarded(*values: Any) -> bool:
    text = " ".join(str(value or "").upper() for value in values)
    return any(pattern in text for pattern in CRYPTO_PATTERNS)


def _asset_from_market(
    market_row: dict[str, Any],
    market_info: dict[str, Any],
    *,
    snapshot_status: str,
    snapshot_error: str = "",
) -> dict[str, Any]:
    instrument = market_info.get("instrument", {}) if isinstance(market_info.get("instrument"), dict) else {}
    snapshot = market_info.get("snapshot", {}) if isinstance(market_info.get("snapshot"), dict) else {}
    epic = _first_text(market_row.get("epic"), instrument.get("epic"), market_row.get("marketId"))
    instrument_name = _first_text(
        market_row.get("instrumentName"),
        instrument.get("name"),
        market_row.get("name"),
        market_row.get("symbol"),
        epic,
    )
    symbol = _first_text(market_row.get("symbol"), market_row.get("ticker"), instrument.get("symbol"), instrument_name, epic)
    market_status = market_status_text(market_info, market_row)
    bid = _as_float(snapshot.get("bid"), 0.0)
    ask = _as_float(snapshot.get("offer", snapshot.get("ask")), 0.0)
    mid_price = _as_float(snapshot.get("netChange"), 0.0)
    if bid > 0 and ask > 0:
        mid_price = (bid + ask) / 2.0
    elif _as_float(snapshot.get("price"), 0.0) > 0:
        mid_price = _as_float(snapshot.get("price"), 0.0)
    elif bid > 0:
        mid_price = bid
    elif ask > 0:
        mid_price = ask
    spread = max(ask - bid, 0.0) if bid > 0 and ask > 0 else 0.0
    spread_pct = (spread / mid_price * 100.0) if mid_price > 0 and spread > 0 else 0.0
    min_size = extract_min_deal_size(market_info)
    margin_pct = extract_margin_factor_pct(market_info)
    min_notional = max(min_size * mid_price, 0.0) if min_size > 0 and mid_price > 0 else 0.0
    margin_required = min_notional * margin_pct / 100.0 if min_notional > 0 and margin_pct > 0 else 0.0
    leverage_estimate = 100.0 / margin_pct if margin_pct > 0 else 0.0
    asset_class = _infer_asset_class(market_row, market_info)
    instrument_type = _first_text(
        market_row.get("instrumentType"),
        market_row.get("marketType"),
        instrument.get("type"),
        instrument.get("instrumentType"),
    )
    currency = _first_text(instrument.get("currency"), market_row.get("currency"), snapshot.get("currency"))
    crypto_guarded = _is_crypto_guarded(symbol, epic, instrument_name, asset_class)

    blockers: list[str] = []
    if not epic:
        blockers.append("missing_epic")
    if snapshot_status != "fresh_snapshot":
        blockers.append(snapshot_status)
    if market_status not in TRADEABLE_MARKET_STATES:
        blockers.append(f"market_status_{market_status.lower()}")
    if min_size <= 0:
        blockers.append("minimum_deal_size_unknown")
    if mid_price <= 0:
        blockers.append("price_unknown")
    if margin_pct <= 0:
        blockers.append("margin_factor_unknown")
    if crypto_guarded:
        blockers.append("capital_client_crypto_guard_blocks_direct_order")
    if snapshot_error:
        blockers.append("snapshot_error")

    can_trade_route = bool(epic) and not crypto_guarded
    trade_ready = can_trade_route and not blockers
    return {
        "symbol": symbol.upper(),
        "epic": epic,
        "market_id": _first_text(market_row.get("marketId"), market_row.get("id")),
        "instrument_name": instrument_name,
        "asset_class": asset_class,
        "instrument_type": instrument_type,
        "market_status": market_status,
        "currency": currency,
        "expiry": _first_text(instrument.get("expiry"), market_row.get("expiry")),
        "snapshot_status": snapshot_status,
        "snapshot_error": snapshot_error,
        "last_snapshot_at": utc_now() if snapshot_status == "fresh_snapshot" else "",
        "bid": round(bid, 8),
        "ask": round(ask, 8),
        "mid_price": round(mid_price, 8),
        "spread": round(spread, 8),
        "spread_pct": round(spread_pct, 8),
        "minimum_deal_size": round(min_size, 8),
        "min_notional_estimate": round(min_notional, 8),
        "margin_factor_pct": round(margin_pct, 8),
        "margin_required_for_min_deal": round(margin_required, 8),
        "leverage_estimate": round(leverage_estimate, 8),
        "can_buy": can_trade_route,
        "can_sell": can_trade_route,
        "trade_ready": trade_ready,
        "blockers": blockers,
        "buy_code_path": "aureon.exchanges.capital_cfd_trader.CapitalCFDTrader._open_position",
        "sell_code_path": "aureon.exchanges.capital_cfd_trader.CapitalCFDTrader._open_position",
        "client_order_path": "aureon.exchanges.capital_client.CapitalClient.place_market_order",
        "client_working_order_path": "aureon.exchanges.capital_client.CapitalClient.place_working_order",
        "buy_call": 'client.place_market_order(symbol, "BUY", size)',
        "sell_call": 'client.place_market_order(symbol, "SELL", size)',
        "pending_buy_call": 'client.place_working_order(symbol, "BUY", size, level, profit_level=take_profit)',
        "pending_sell_call": 'client.place_working_order(symbol, "SELL", size, level, profit_level=take_profit)',
        "cancel_pending_call": "client.delete_working_order(deal_id)",
        "close_call": "client.close_position(deal_id)",
        "rest_order_route": "POST /positions",
        "rest_working_order_route": "POST /workingorders",
        "rest_cancel_working_order_route": "DELETE /workingorders/{dealId}",
        "rest_close_route": "DELETE /positions/{dealId}",
    }


def _snapshot_budget(max_snapshots: Optional[int], total_markets: int) -> int:
    if max_snapshots is None:
        max_snapshots = int(os.getenv("CAPITAL_ASSET_REGISTRY_MAX_SNAPSHOTS", "100") or "100")
    if max_snapshots < 0:
        return total_markets
    return max_snapshots


def build_capital_asset_registry(
    *,
    client: Optional[CapitalClient] = None,
    force_refresh: bool = False,
    max_snapshots: Optional[int] = None,
    snapshot_cache_ttl: float = 300.0,
) -> dict[str, Any]:
    client = client or CapitalClient()
    generated_at = utc_now()
    enabled = bool(getattr(client, "enabled", False))
    markets: list[dict[str, Any]] = []
    errors: list[str] = []
    if enabled:
        try:
            markets = list(client.get_all_markets(force_refresh=force_refresh) or [])
        except Exception as exc:
            errors.append(f"market_catalogue_error:{exc}")
    else:
        errors.append("capital_client_disabled_or_missing_credentials")

    budget = _snapshot_budget(max_snapshots, len(markets))
    assets: list[dict[str, Any]] = []
    for index, row in enumerate(markets):
        if not isinstance(row, dict):
            continue
        epic = _first_text(row.get("epic"), row.get("marketId"))
        market_info: dict[str, Any] = {}
        snapshot_status = "snapshot_not_sampled_budget"
        snapshot_error = ""
        if epic and index < budget:
            try:
                snapshot = client._get_market_snapshot(epic, cache_ttl=snapshot_cache_ttl)  # type: ignore[attr-defined]
                if isinstance(snapshot, dict) and snapshot:
                    market_info = snapshot
                    snapshot_status = "fresh_snapshot"
                else:
                    snapshot_status = "snapshot_unavailable"
            except Exception as exc:
                snapshot_status = "snapshot_error"
                snapshot_error = str(exc)
        assets.append(
            _asset_from_market(
                row,
                market_info,
                snapshot_status=snapshot_status,
                snapshot_error=snapshot_error,
            )
        )

    asset_class_counts = Counter(asset.get("asset_class", "unknown") for asset in assets)
    blocker_counts: Counter[str] = Counter()
    for asset in assets:
        blocker_counts.update(asset.get("blockers", []) or [])

    snapshot_enriched_count = sum(1 for asset in assets if asset.get("snapshot_status") == "fresh_snapshot")
    summary = {
        "total_markets": len(assets),
        "snapshot_budget": budget,
        "snapshot_enriched_count": snapshot_enriched_count,
        "known_but_not_sampled_count": sum(1 for asset in assets if asset.get("snapshot_status") == "snapshot_not_sampled_budget"),
        "trade_route_configured_count": sum(1 for asset in assets if asset.get("can_buy") and asset.get("can_sell")),
        "trade_ready_count": sum(1 for asset in assets if asset.get("trade_ready")),
        "cost_known_count": sum(1 for asset in assets if _as_float(asset.get("mid_price"), 0.0) > 0),
        "margin_known_count": sum(1 for asset in assets if _as_float(asset.get("margin_factor_pct"), 0.0) > 0),
        "crypto_guarded_count": sum(1 for asset in assets if "capital_client_crypto_guard_blocks_direct_order" in (asset.get("blockers") or [])),
        "asset_classes": dict(sorted(asset_class_counts.items())),
        "top_blockers": [{"name": key, "count": value} for key, value in blocker_counts.most_common(12)],
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "source": "aureon.exchanges.capital_asset_registry",
        "capital_client_enabled": enabled,
        "catalogue_source": "CapitalClient.get_all_markets",
        "snapshot_source": "CapitalClient._get_market_snapshot",
        "execution_contract": {
            "owner": "aureon.exchanges.capital_cfd_trader.CapitalCFDTrader",
            "client": "aureon.exchanges.capital_client.CapitalClient",
            "buy": 'CapitalClient.place_market_order(symbol, "BUY", size)',
            "sell": 'CapitalClient.place_market_order(symbol, "SELL", size)',
            "pending_buy": 'CapitalClient.place_working_order(symbol, "BUY", size, level, profit_level=take_profit)',
            "pending_sell": 'CapitalClient.place_working_order(symbol, "SELL", size, level, profit_level=take_profit)',
            "cancel_pending": "CapitalClient.delete_working_order(deal_id)",
            "close": "CapitalClient.close_position(deal_id)",
            "order_route": "POST /positions",
            "working_order_route": "POST /workingorders",
            "cancel_working_order_route": "DELETE /workingorders/{dealId}",
            "close_route": "DELETE /positions/{dealId}",
            "note": "Registry records tradability and route evidence only; live orders still pass through runtime gates.",
        },
        "summary": summary,
        "errors": errors,
        "assets": assets,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(tmp, path)
    return path


def _write_csv(path: Path, assets: list[dict[str, Any]]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for asset in assets:
            row = {field: asset.get(field, "") for field in CSV_FIELDS}
            row["blockers"] = ";".join(asset.get("blockers", []) or [])
            writer.writerow(row)
    os.replace(tmp, path)
    return path


def _write_sqlite(path: Path, report: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=15)
    try:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS capital_assets (
                symbol TEXT,
                epic TEXT PRIMARY KEY,
                instrument_name TEXT,
                asset_class TEXT,
                instrument_type TEXT,
                market_status TEXT,
                currency TEXT,
                snapshot_status TEXT,
                bid REAL,
                ask REAL,
                mid_price REAL,
                spread REAL,
                spread_pct REAL,
                minimum_deal_size REAL,
                min_notional_estimate REAL,
                margin_factor_pct REAL,
                margin_required_for_min_deal REAL,
                leverage_estimate REAL,
                can_buy INTEGER,
                can_sell INTEGER,
                trade_ready INTEGER,
                blockers TEXT,
                buy_call TEXT,
                sell_call TEXT,
                client_order_path TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS registry_metadata (
                key TEXT PRIMARY KEY,
                value TEXT
            )
            """
        )
        conn.execute("DELETE FROM capital_assets")
        conn.execute("DELETE FROM registry_metadata")
        generated_at = str(report.get("generated_at") or utc_now())
        rows = []
        for asset in report.get("assets", []) or []:
            rows.append(
                (
                    asset.get("symbol", ""),
                    asset.get("epic", ""),
                    asset.get("instrument_name", ""),
                    asset.get("asset_class", ""),
                    asset.get("instrument_type", ""),
                    asset.get("market_status", ""),
                    asset.get("currency", ""),
                    asset.get("snapshot_status", ""),
                    _as_float(asset.get("bid"), 0.0),
                    _as_float(asset.get("ask"), 0.0),
                    _as_float(asset.get("mid_price"), 0.0),
                    _as_float(asset.get("spread"), 0.0),
                    _as_float(asset.get("spread_pct"), 0.0),
                    _as_float(asset.get("minimum_deal_size"), 0.0),
                    _as_float(asset.get("min_notional_estimate"), 0.0),
                    _as_float(asset.get("margin_factor_pct"), 0.0),
                    _as_float(asset.get("margin_required_for_min_deal"), 0.0),
                    _as_float(asset.get("leverage_estimate"), 0.0),
                    1 if asset.get("can_buy") else 0,
                    1 if asset.get("can_sell") else 0,
                    1 if asset.get("trade_ready") else 0,
                    ";".join(asset.get("blockers", []) or []),
                    asset.get("buy_call", ""),
                    asset.get("sell_call", ""),
                    asset.get("client_order_path", ""),
                    generated_at,
                )
            )
        conn.executemany(
            """
            INSERT OR REPLACE INTO capital_assets (
                symbol, epic, instrument_name, asset_class, instrument_type,
                market_status, currency, snapshot_status, bid, ask, mid_price,
                spread, spread_pct, minimum_deal_size, min_notional_estimate,
                margin_factor_pct, margin_required_for_min_deal, leverage_estimate,
                can_buy, can_sell, trade_ready, blockers, buy_call, sell_call,
                client_order_path, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        metadata = {
            "schema_version": report.get("schema_version", ""),
            "generated_at": report.get("generated_at", ""),
            "summary": json.dumps(report.get("summary", {}), sort_keys=True),
        }
        conn.executemany("INSERT OR REPLACE INTO registry_metadata (key, value) VALUES (?, ?)", metadata.items())
        conn.commit()
    finally:
        conn.close()
    return path


def _write_markdown(path: Path, report: dict[str, Any]) -> Path:
    summary = report.get("summary", {}) if isinstance(report.get("summary"), dict) else {}
    lines = [
        "# Aureon Capital Tradable Asset Registry",
        "",
        f"Generated: {report.get('generated_at', '')}",
        f"Schema: {report.get('schema_version', SCHEMA_VERSION)}",
        "",
        "This registry records Capital.com market metadata and the Aureon code route used to buy, sell, or close a CFD. It does not submit orders; live orders still pass through the existing runtime, portfolio, confidence, and exchange gates.",
        "",
        "## Summary",
        "",
        f"- Total Capital markets discovered: {summary.get('total_markets', 0)}",
        f"- Snapshot enriched this run: {summary.get('snapshot_enriched_count', 0)} / budget {summary.get('snapshot_budget', 0)}",
        f"- Trade route configured: {summary.get('trade_route_configured_count', 0)}",
        f"- Trade ready with sampled cost and margin: {summary.get('trade_ready_count', 0)}",
        f"- Cost known: {summary.get('cost_known_count', 0)}",
        f"- Margin known: {summary.get('margin_known_count', 0)}",
        "",
        "## Execution Route",
        "",
        "- BUY: `CapitalClient.place_market_order(symbol, \"BUY\", size)` via `POST /positions`",
        "- SELL: `CapitalClient.place_market_order(symbol, \"SELL\", size)` via `POST /positions`",
        "- CLOSE: `CapitalClient.close_position(deal_id)` via `DELETE /positions/{dealId}`",
        "",
        "## Top Blockers",
        "",
    ]
    for blocker in summary.get("top_blockers", []) or []:
        lines.append(f"- {blocker.get('name')}: {blocker.get('count')}")
    lines.extend(
        [
            "",
            "## Asset Class Counts",
            "",
        ]
    )
    for name, count in (summary.get("asset_classes", {}) or {}).items():
        lines.append(f"- {name}: {count}")
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    os.replace(tmp, path)
    return path


def write_capital_asset_registry(
    report: dict[str, Any],
    *,
    state_json: Path = DEFAULT_STATE_JSON,
    output_json: Path = DEFAULT_OUTPUT_JSON,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    output_md: Path = DEFAULT_OUTPUT_MD,
    output_db: Path = DEFAULT_OUTPUT_DB,
    public_json: Path = DEFAULT_PUBLIC_JSON,
) -> dict[str, str]:
    assets = list(report.get("assets", []) or [])
    written = {
        "state_json": str(_write_json(state_json, report)),
        "output_json": str(_write_json(output_json, report)),
        "output_csv": str(_write_csv(output_csv, assets)),
        "output_md": str(_write_markdown(output_md, report)),
        "output_db": str(_write_sqlite(output_db, report)),
        "public_json": str(_write_json(public_json, report)),
    }
    return written


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Capital.com tradable asset registry")
    parser.add_argument("--force-refresh", action="store_true", help="Refresh the Capital market catalogue instead of using cache")
    parser.add_argument(
        "--max-snapshots",
        type=int,
        default=int(os.getenv("CAPITAL_ASSET_REGISTRY_MAX_SNAPSHOTS", "100") or "100"),
        help="Detailed market snapshots to sample this run; use -1 for all, 0 for catalogue only",
    )
    parser.add_argument("--snapshot-cache-ttl", type=float, default=300.0)
    parser.add_argument("--state-json", default=str(DEFAULT_STATE_JSON))
    parser.add_argument("--output-json", default=str(DEFAULT_OUTPUT_JSON))
    parser.add_argument("--output-csv", default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--output-md", default=str(DEFAULT_OUTPUT_MD))
    parser.add_argument("--output-db", default=str(DEFAULT_OUTPUT_DB))
    parser.add_argument("--public-json", default=str(DEFAULT_PUBLIC_JSON))
    args = parser.parse_args(argv)

    report = build_capital_asset_registry(
        force_refresh=args.force_refresh,
        max_snapshots=args.max_snapshots,
        snapshot_cache_ttl=args.snapshot_cache_ttl,
    )
    written = write_capital_asset_registry(
        report,
        state_json=Path(args.state_json),
        output_json=Path(args.output_json),
        output_csv=Path(args.output_csv),
        output_md=Path(args.output_md),
        output_db=Path(args.output_db),
        public_json=Path(args.public_json),
    )
    summary = report.get("summary", {})
    print(
        "Capital asset registry: "
        f"{summary.get('total_markets', 0)} markets, "
        f"{summary.get('snapshot_enriched_count', 0)} enriched, "
        f"{summary.get('trade_ready_count', 0)} trade-ready"
    )
    print(json.dumps(written, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
