"""Official exchange API rate-limit profiles and cash-aware call planning.

This module gives Aureon one place to keep provider rate-limit facts, safe
runtime defaults, and the decision that idle/no-cash venues may spend more of
their budget on market discovery while venues with cash or positions reserve
capacity for account state, risk, and execution.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except Exception:
        return default
    if number != number:
        return default
    return number


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


@dataclass(frozen=True)
class ExchangeRateLimitProfile:
    exchange: str
    title: str
    official_doc_url: str
    official_limit_model: str
    official_limits: Mapping[str, Any]
    official_notes: tuple[str, ...]
    safe_governor_calls_per_min: float
    quote_budget_fraction_cash_active: float
    quote_budget_fraction_cash_idle: float
    execution_reserve_fraction_cash_active: float
    execution_reserve_fraction_cash_idle: float
    stream_preferred: bool = True
    env_calls_per_min: str = ""
    env_quote_fraction: str = ""
    provider_status: str = "official_documented"
    source_lines: tuple[str, ...] = field(default_factory=tuple)

    def configured_calls_per_min(self) -> float:
        if self.env_calls_per_min:
            return max(1.0, _env_float(self.env_calls_per_min, self.safe_governor_calls_per_min))
        return max(1.0, self.safe_governor_calls_per_min)

    def configured_quote_fraction(self, *, cash_active: bool) -> float:
        default = (
            self.quote_budget_fraction_cash_active
            if cash_active
            else self.quote_budget_fraction_cash_idle
        )
        if self.env_quote_fraction:
            default = _env_float(self.env_quote_fraction, default)
        return max(0.05, min(0.95, default))

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "exchange": self.exchange,
            "title": self.title,
            "provider_status": self.provider_status,
            "official_doc_url": self.official_doc_url,
            "official_limit_model": self.official_limit_model,
            "official_limits": dict(self.official_limits),
            "official_notes": list(self.official_notes),
            "safe_governor_calls_per_min": self.safe_governor_calls_per_min,
            "stream_preferred": self.stream_preferred,
            "env_overrides": {
                "calls_per_min": self.env_calls_per_min,
                "quote_budget_fraction": self.env_quote_fraction,
            },
            "source_lines": list(self.source_lines),
        }


OFFICIAL_EXCHANGE_RATE_LIMITS: Dict[str, ExchangeRateLimitProfile] = {
    "binance": ExchangeRateLimitProfile(
        exchange="binance",
        title="Binance Spot REST/WebSocket",
        official_doc_url="https://developers.binance.com/docs/binance-spot-api-docs/rest-api/limits",
        official_limit_model="request_weight_and_order_limits_from_exchangeInfo",
        official_limits={
            "rest_rate_limits_source": "/api/v3/exchangeInfo rateLimits",
            "rest_usage_header": "X-MBX-USED-WEIGHT-(intervalNum)(intervalLetter)",
            "rest_order_header": "X-MBX-ORDER-COUNT-(intervalNum)(intervalLetter)",
            "websocket_request_weight_per_minute_example": 6000,
            "websocket_connection_weight": 2,
            "websocket_connection_attempts_per_5_min_per_ip": 300,
            "rate_limit_status": "429",
            "ban_status": "418",
        },
        official_notes=(
            "Binance limits are weight-based, not simple call counts; endpoints with multiple symbols can cost more.",
            "The runtime should read exchangeInfo and response headers when available, then back off on Retry-After.",
            "Use streams for live market data so REST weight remains available for account, order, and recovery calls.",
        ),
        safe_governor_calls_per_min=240.0,
        quote_budget_fraction_cash_active=0.55,
        quote_budget_fraction_cash_idle=0.82,
        execution_reserve_fraction_cash_active=0.45,
        execution_reserve_fraction_cash_idle=0.18,
        env_calls_per_min="UNIFIED_BINANCE_CALLS_PER_MIN",
        env_quote_fraction="UNIFIED_BINANCE_QUOTE_BUDGET_FRACTION",
        source_lines=("Binance REST limits docs lines 58-67", "Binance WS limits docs lines 143-171"),
    ),
    "kraken": ExchangeRateLimitProfile(
        exchange="kraken",
        title="Kraken Spot REST/WebSocket",
        official_doc_url="https://support.kraken.com/hc/en-us/articles/206548367-what-are-the-api-rate-limits-",
        official_limit_model="public_ip_frequency_private_counter_and_trading_points",
        official_limits={
            "public_rest_safe_frequency_per_sec": 1,
            "private_counter_verified_max": 20,
            "private_counter_verified_decay_per_sec": 0.5,
            "private_counter_higher_limits_max": 20,
            "private_counter_higher_limits_decay_per_sec": 1.0,
            "private_history_counter_increment": 4,
            "private_standard_counter_increment": 1,
            "trading_counter_scope": "account_and_currency_pair",
        },
        official_notes=(
            "Kraken private history calls are expensive: Ledgers, TradesHistory, and ClosedOrders add +4 to the counter.",
            "AddOrder/CancelOrder do not use the private-account counter, but they use Kraken's separate trading limit model.",
            "Keep private account-history sync low priority; favor WebSocket/public market streams for live discovery.",
        ),
        safe_governor_calls_per_min=30.0,
        quote_budget_fraction_cash_active=0.40,
        quote_budget_fraction_cash_idle=0.70,
        execution_reserve_fraction_cash_active=0.72,
        execution_reserve_fraction_cash_idle=0.30,
        env_calls_per_min="UNIFIED_KRAKEN_CALLS_PER_MIN",
        env_quote_fraction="UNIFIED_KRAKEN_QUOTE_BUDGET_FRACTION",
        source_lines=("Kraken support rate-limit docs lines 49-77", "Kraken support rate-limit docs lines 79-102"),
    ),
    "alpaca": ExchangeRateLimitProfile(
        exchange="alpaca",
        title="Alpaca Trading and Market Data",
        official_doc_url="https://docs.alpaca.markets/us/v1.4.2/docs/about-market-data-api",
        official_limit_model="trading_rpm_plus_market_data_plan_limits",
        official_limits={
            "trading_api_default_requests_per_min_per_account": 200,
            "market_data_basic_historical_calls_per_min": 200,
            "market_data_algo_trader_plus_historical_calls_per_min": 10000,
            "equities_basic_websocket_symbols": 30,
            "equities_algo_trader_plus_websocket_symbols": "unlimited",
            "options_basic_websocket_quotes": 200,
            "options_algo_trader_plus_websocket_quotes": 1000,
            "typical_stream_connections_per_endpoint": 1,
        },
        official_notes=(
            "Alpaca's official market-data docs define plan-specific historical limits and WebSocket subscription limits.",
            "Alpaca support documents the Trading API default as 200 requests per minute per account.",
            "Use one stream connection per endpoint in most plans; use REST history budget for backfill, not live ticks.",
        ),
        safe_governor_calls_per_min=120.0,
        quote_budget_fraction_cash_active=0.60,
        quote_budget_fraction_cash_idle=0.82,
        execution_reserve_fraction_cash_active=0.40,
        execution_reserve_fraction_cash_idle=0.18,
        env_calls_per_min="UNIFIED_ALPACA_CALLS_PER_MIN",
        env_quote_fraction="UNIFIED_ALPACA_QUOTE_BUDGET_FRACTION",
        source_lines=("Alpaca market-data docs lines 154-180", "Alpaca WebSocket docs lines 184-191"),
    ),
    "capital": ExchangeRateLimitProfile(
        exchange="capital",
        title="Capital.com REST/WebSocket",
        official_doc_url="https://open-api.capital.com/",
        official_limit_model="per_user_request_rate_endpoint_limits_and_ws_instrument_cap",
        official_limits={
            "max_requests_per_sec_per_user": 10,
            "position_or_order_request_spacing_sec": 0.1,
            "session_endpoint_requests_per_sec_per_api_key": 1,
            "demo_positions_workingorders_requests_per_hour": 1000,
            "websocket_max_instruments": 40,
            "rest_session_inactive_ttl_min": 10,
            "websocket_session_ttl_min": 10,
        },
        official_notes=(
            "Capital supports REST and WebSocket real-time prices for platform instruments.",
            "Order/position requests must respect the endpoint limits and still need confirmation checks.",
            "Use WebSocket subscriptions for up to 40 active instruments and keep session refresh separate from market scans.",
        ),
        safe_governor_calls_per_min=45.0,
        quote_budget_fraction_cash_active=0.42,
        quote_budget_fraction_cash_idle=0.75,
        execution_reserve_fraction_cash_active=0.58,
        execution_reserve_fraction_cash_idle=0.25,
        env_calls_per_min="UNIFIED_CAPITAL_CALLS_PER_MIN",
        env_quote_fraction="UNIFIED_CAPITAL_QUOTE_BUDGET_FRACTION",
        source_lines=("Capital.com API docs lines 201-215",),
    ),
}


def get_exchange_rate_limit(exchange: str) -> Optional[ExchangeRateLimitProfile]:
    return OFFICIAL_EXCHANGE_RATE_LIMITS.get(str(exchange or "").strip().lower())


def official_rate_limit_profiles() -> Dict[str, Dict[str, Any]]:
    return {exchange: profile.to_public_dict() for exchange, profile in OFFICIAL_EXCHANGE_RATE_LIMITS.items()}


def _combined(runtime: Mapping[str, Any]) -> Mapping[str, Any]:
    combined = runtime.get("combined") if isinstance(runtime, Mapping) else {}
    return combined if isinstance(combined, Mapping) else {}


def _cash_estimate_usd(exchange: str, runtime: Mapping[str, Any]) -> float:
    combined = _combined(runtime)
    exchange = exchange.lower()
    if exchange == "capital":
        gbp = _as_float(combined.get("capital_equity_gbp"), 0.0)
        usd = _as_float(combined.get("capital_equity_usd"), 0.0)
        return usd if usd > 0 else gbp * _env_float("UNIFIED_GBP_USD_REFERENCE_RATE", 1.25)
    if exchange == "kraken":
        for key in ("kraken_equity_usd", "kraken_equity"):
            value = _as_float(combined.get(key), 0.0)
            if value > 0:
                return value
    if exchange == "alpaca":
        for key in ("alpaca_equity_usd", "alpaca_equity", "alpaca_portfolio_value"):
            value = _as_float(combined.get(key), 0.0)
            if value > 0:
                return value
    if exchange == "binance":
        for key in ("binance_equity_usd", "binance_equity", "binance_wallet_usd"):
            value = _as_float(combined.get(key), 0.0)
            if value > 0:
                return value
    balances = combined.get("exchange_balances")
    if isinstance(balances, Mapping):
        row = balances.get(exchange)
        if isinstance(row, Mapping):
            return max(
                _as_float(row.get("total_usd_estimate"), 0.0),
                _as_float(row.get("cash_usd"), 0.0),
                _as_float(row.get("equity_usd"), 0.0),
            )
    return 0.0


def _position_count(exchange: str, runtime: Mapping[str, Any]) -> int:
    combined = _combined(runtime)
    positions = combined.get("positions_by_exchange")
    if isinstance(positions, Mapping):
        return _as_int(positions.get(exchange), 0)
    exchange_positions = runtime.get("positions_by_exchange") if isinstance(runtime, Mapping) else {}
    if isinstance(exchange_positions, Mapping):
        return _as_int(exchange_positions.get(exchange), 0)
    return 0


def build_cash_aware_rate_plan(
    runtime: Optional[Mapping[str, Any]] = None,
    *,
    exchange: Optional[str] = None,
) -> Dict[str, Dict[str, Any]]:
    """Return execution-first, cash-aware data budgets for official profiles."""

    runtime = runtime if isinstance(runtime, Mapping) else {}
    low_cash_usd = max(0.0, _env_float("AUREON_RATE_BUDGET_LOW_CASH_USD", 2.0))
    exchanges = [str(exchange).lower()] if exchange else sorted(OFFICIAL_EXCHANGE_RATE_LIMITS)
    plan: Dict[str, Dict[str, Any]] = {}
    for name in exchanges:
        profile = get_exchange_rate_limit(name)
        if profile is None:
            continue
        safe_calls = profile.configured_calls_per_min()
        cash_usd = _cash_estimate_usd(name, runtime)
        positions = _position_count(name, runtime)
        cash_active = cash_usd >= low_cash_usd or positions > 0
        reserve_fraction = (
            profile.execution_reserve_fraction_cash_active
            if cash_active
            else profile.execution_reserve_fraction_cash_idle
        )
        quote_fraction = profile.configured_quote_fraction(cash_active=cash_active)
        execution_reserved = max(1.0, round(safe_calls * reserve_fraction, 3))
        quote_cap = max(1.0, round(safe_calls * quote_fraction, 3))
        market_data_budget = max(1.0, round(min(safe_calls - execution_reserved, quote_cap), 3))
        if not cash_active:
            market_data_budget = max(market_data_budget, quote_cap)
        plan[name] = {
            "exchange": name,
            "official_limit_model": profile.official_limit_model,
            "official_doc_url": profile.official_doc_url,
            "safe_calls_per_min": round(safe_calls, 3),
            "safe_calls_per_hour": round(safe_calls * 60.0, 3),
            "cash_usd_estimate": round(cash_usd, 4),
            "position_count": positions,
            "cash_or_position_active": cash_active,
            "data_boost_eligible": not cash_active,
            "execution_reserved_per_min": execution_reserved,
            "market_data_budget_per_min": market_data_budget,
            "market_data_budget_per_hour": round(market_data_budget * 60.0, 3),
            "quote_budget_fraction": round(quote_fraction, 4),
            "stream_preferred": profile.stream_preferred,
            "recommended_mode": "execution_positions_first" if cash_active else "idle_cash_market_discovery_boost",
            "operator_note": (
                "Reserve capacity for orders, balances, positions, and recovery before broad scans."
                if cash_active
                else "No meaningful cash/position detected, so use more budget for streams, quotes, and candidate discovery."
            ),
        }
    return plan


def governor_default_for_exchange(exchange: str, fallback: float) -> float:
    profile = get_exchange_rate_limit(exchange)
    if profile is None:
        return fallback
    return profile.configured_calls_per_min()


def quote_fraction_default_for_exchange(exchange: str, fallback: float, *, cash_active: bool = True) -> float:
    profile = get_exchange_rate_limit(exchange)
    if profile is None:
        return fallback
    return profile.configured_quote_fraction(cash_active=cash_active)
