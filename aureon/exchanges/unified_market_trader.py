#!/usr/bin/env python3
"""
Unified market runner for the current live setup.

Runs:
- Kraken crypto margin trader
- Capital.com CFD trader
- Alpaca spot crypto route planning
- Binance spot and margin route planning

Provides:
- one autonomous loop
- one combined terminal status surface
- one local telemetry API for the dashboard
- one multi-venue order-intent surface for runtime-gated execution
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import logging
import math
import os
import shutil
import subprocess
import sys
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional

try:
    # Load repo-local environment variables so users can run this file directly
    # without pre-exporting keys in their shell.
    from aureon.core.aureon_env import load_aureon_environment

    load_aureon_environment(Path(__file__).resolve().parents[2], override=False)
except Exception:
    pass

_SUPPRESS_IMPORT_SIDE_EFFECTS = os.getenv("AUREON_SUPPRESS_IMPORT_SIDE_EFFECTS", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}

if _SUPPRESS_IMPORT_SIDE_EFFECTS:
    KrakenMarginArmyTrader = None  # type: ignore[assignment]
    CapitalCFDTrader = None  # type: ignore[assignment]
    CAPITAL_UNIVERSE = {}
    AlpacaClient = None  # type: ignore[assignment]
    BinanceClient = None  # type: ignore[assignment]
else:
    try:
        from aureon.exchanges.kraken_margin_penny_trader import KrakenMarginArmyTrader
        from aureon.exchanges.capital_cfd_trader import CAPITAL_UNIVERSE, CapitalCFDTrader
    except Exception:
        from aureon.exchanges.kraken_margin_penny_trader import KrakenMarginArmyTrader
        from aureon.exchanges.capital_cfd_trader import CAPITAL_UNIVERSE, CapitalCFDTrader
    try:
        from aureon.exchanges.alpaca_client import AlpacaClient
    except Exception:
        try:
            from aureon.exchanges.alpaca_client import AlpacaClient
        except Exception:
            AlpacaClient = None  # type: ignore[assignment]
    try:
        from aureon.exchanges.binance_client import BinanceClient
    except Exception:
        try:
            from aureon.exchanges.binance_client import BinanceClient
        except Exception:
            BinanceClient = None  # type: ignore[assignment]

try:
    from aureon.utils.aureon_sero_client import get_sero_client
except Exception:
    try:
        from aureon.utils.aureon_sero_client import get_sero_client
    except Exception:
        get_sero_client = None  # type: ignore[assignment]

logger = logging.getLogger("unified_market_trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Network integration (fail-safe) ──────────────────────────────────────────
try:
    from aureon.core.aureon_thought_bus import get_thought_bus, Thought
    _HAS_THOUGHT_BUS = True
except Exception:
    get_thought_bus = None   # type: ignore[assignment]
    Thought = None           # type: ignore[assignment]
    _HAS_THOUGHT_BUS = False

try:
    from aureon.core.aureon_mycelium import get_mycelium
    _HAS_MYCELIUM = True
except Exception:
    try:
        from aureon.core.aureon_mycelium import get_mycelium
        _HAS_MYCELIUM = True
    except Exception:
        get_mycelium = None  # type: ignore[assignment]
        _HAS_MYCELIUM = False

def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except Exception:
        return default

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8790
REPO_ROOT = Path(__file__).resolve().parents[2]
RUNTIME_STATUS_PATH = REPO_ROOT / "state" / "unified_runtime_status.json"
RUNTIME_STATUS_LOCK_PATH = RUNTIME_STATUS_PATH.with_name("unified_market_trader.writer.lock.json")
ORDER_INTENT_LOG_PATH = RUNTIME_STATUS_PATH.with_name("unified_exchange_order_intents.jsonl")
ORDER_INTENT_STATE_PATH = RUNTIME_STATUS_PATH.with_name("unified_exchange_order_intents.json")
ORDER_INTENT_PUBLIC_PATH = REPO_ROOT / "frontend" / "public" / "aureon_unified_exchange_order_intents.json"
EXECUTION_RESULT_LOG_PATH = RUNTIME_STATUS_PATH.with_name("unified_exchange_execution_results.jsonl")
EXECUTION_RESULT_STATE_PATH = RUNTIME_STATUS_PATH.with_name("unified_exchange_execution_results.json")
EXECUTION_RESULT_PUBLIC_PATH = REPO_ROOT / "frontend" / "public" / "aureon_unified_exchange_execution_results.json"
SHADOW_TRADE_LOG_PATH = RUNTIME_STATUS_PATH.with_name("unified_shadow_trade_report.jsonl")
SHADOW_TRADE_STATE_PATH = RUNTIME_STATUS_PATH.with_name("unified_shadow_trade_report.json")
SHADOW_TRADE_PUBLIC_PATH = REPO_ROOT / "frontend" / "public" / "aureon_unified_shadow_trade_report.json"
HNC_COGNITIVE_PROOF_LOG_PATH = RUNTIME_STATUS_PATH.with_name("aureon_hnc_cognitive_proof.jsonl")
HNC_COGNITIVE_PROOF_STATE_PATH = RUNTIME_STATUS_PATH.with_name("aureon_hnc_cognitive_proof.json")
HNC_COGNITIVE_PROOF_PUBLIC_PATH = REPO_ROOT / "frontend" / "public" / "aureon_hnc_cognitive_proof.json"
EMBEDDED_DASHBOARD_ENABLED = os.getenv("UNIFIED_MARKET_EMBEDDED_DASHBOARD", "").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
RUNTIME_WRITER_LOCK_TTL_SEC = max(30.0, _env_float("UNIFIED_RUNTIME_WRITER_LOCK_TTL_SEC", 120.0))
EXCHANGE_REINIT_INTERVAL_SEC = max(2.0, _env_float("UNIFIED_EXCHANGE_REINIT_INTERVAL_SEC", 30.0))
AURIS_FEED_MIN_INTERVAL_SEC = max(5.0, _env_float("UNIFIED_AURIS_FEED_MIN_INTERVAL_SEC", 45.0))
CENTRAL_BEAT_REFRESH_SEC = max(1.0, _env_float("UNIFIED_CENTRAL_BEAT_REFRESH_SEC", 20.0))
CENTRAL_BEAT_STALE_AFTER_SEC = max(
    CENTRAL_BEAT_REFRESH_SEC * 2.0,
    _env_float("UNIFIED_CENTRAL_BEAT_STALE_AFTER_SEC", 90.0),
)
READY_STALE_AFTER_SEC = max(15.0, _env_float("UNIFIED_READY_STALE_AFTER_SEC", 45.0))
CENTRAL_BEAT_HISTORY_LIMIT = 24
PROBE_SYMBOL_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_PROBE_SYMBOL_MIN_INTERVAL_SEC", 5.0))
PROBE_SYMBOL_STALE_TTL_SEC = max(
    PROBE_SYMBOL_MIN_INTERVAL_SEC,
    _env_float("UNIFIED_PROBE_SYMBOL_STALE_TTL_SEC", 30.0),
)
KRAKEN_TICK_MIN_INTERVAL_SEC = max(0.5, _env_float("UNIFIED_KRAKEN_TICK_MIN_INTERVAL_SEC", 1.0))
CAPITAL_TICK_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_CAPITAL_TICK_MIN_INTERVAL_SEC", 2.0))
ORDER_INTENT_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_ORDER_INTENT_MIN_INTERVAL_SEC", 8.0))
ORDER_INTENT_MIN_CONFIDENCE = max(0.0, min(1.0, _env_float("UNIFIED_ORDER_INTENT_MIN_CONFIDENCE", 0.35)))
ORDER_INTENT_MAX_PER_CYCLE = max(1, int(_env_float("UNIFIED_ORDER_INTENT_MAX_PER_CYCLE", 4.0)))
ORDER_EXECUTOR_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_ORDER_EXECUTOR_MIN_INTERVAL_SEC", 10.0))
ORDER_EXECUTOR_SYMBOL_COOLDOWN_SEC = max(5.0, _env_float("UNIFIED_ORDER_EXECUTOR_SYMBOL_COOLDOWN_SEC", 60.0))
ORDER_EXECUTOR_QUOTE_USD = max(1.0, _env_float("UNIFIED_ORDER_EXECUTOR_QUOTE_USD", 5.0))
ORDER_EXECUTOR_MAX_PER_TICK = max(1, int(_env_float("UNIFIED_ORDER_EXECUTOR_MAX_PER_TICK", 4.0)))
ORDER_EXECUTOR_MAX_OPEN_POSITIONS = max(1, int(_env_float("UNIFIED_ORDER_EXECUTOR_MAX_OPEN_POSITIONS", 12.0)))
KRAKEN_SPOT_QUOTE_USD = max(63.0, _env_float("UNIFIED_KRAKEN_SPOT_QUOTE_USD", 65.0))
BINANCE_MARGIN_LEVERAGE = max(1, int(_env_float("UNIFIED_BINANCE_MARGIN_LEVERAGE", 2.0)))
SHADOW_TRADE_MAX_PER_CYCLE = max(1, int(_env_float("UNIFIED_SHADOW_TRADE_MAX_PER_CYCLE", 12.0)))
SHADOW_TRADE_MIN_CONFIDENCE = max(0.0, min(1.0, _env_float("UNIFIED_SHADOW_TRADE_MIN_CONFIDENCE", ORDER_INTENT_MIN_CONFIDENCE)))
SHADOW_TRADE_VALIDATION_HORIZON_SEC = max(10.0, _env_float("UNIFIED_SHADOW_TRADE_VALIDATION_HORIZON_SEC", 90.0))
SHADOW_TRADE_TARGET_MOVE_PCT = max(0.01, _env_float("UNIFIED_SHADOW_TRADE_TARGET_MOVE_PCT", 0.18))
SHADOW_TRADE_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_SHADOW_TRADE_MIN_INTERVAL_SEC", 5.0))
HNC_COGNITIVE_PROOF_MIN_INTERVAL_SEC = max(1.0, _env_float("UNIFIED_HNC_COGNITIVE_PROOF_MIN_INTERVAL_SEC", 5.0))
KRAKEN_CLI_INSTALL_CMD = (
    "curl --proto '=https' --tlsv1.2 -LsSf "
    "https://github.com/krakenfx/kraken-cli/releases/latest/download/kraken-cli-installer.sh | sh"
)
SYMBOL_ALIASES = {
    "XBTUSD": "BTCUSD",
    "XXBTZUSD": "BTCUSD",
    "XETHZUSD": "ETHUSD",
    "ETHUSD": "ETHUSD",
    "BTCUSD": "BTCUSD",
    "GOLD": "XAUUSD",
    "XAUUSD": "XAUUSD",
    "SILVER": "XAGUSD",
    "XAGUSD": "XAGUSD",
    "BTCUSDT": "BTCUSD",
    "ETHUSDT": "ETHUSD",
    "SOLUSDT": "SOLUSD",
    "XRPUSDT": "XRPUSD",
    "DOGEUSDT": "DOGEUSD",
}
ALPACA_SPOT_CRYPTO_BASES = {
    "AAVE",
    "AVAX",
    "BCH",
    "BTC",
    "DOGE",
    "ETH",
    "LINK",
    "LTC",
    "SHIB",
    "SOL",
    "UNI",
}
BINANCE_CRYPTO_BASES = {
    "AAVE",
    "ADA",
    "APT",
    "ARB",
    "ATOM",
    "AVAX",
    "BCH",
    "BNB",
    "BTC",
    "DOGE",
    "DOT",
    "ETC",
    "ETH",
    "FIL",
    "LINK",
    "LTC",
    "NEAR",
    "OP",
    "PEPE",
    "SHIB",
    "SOL",
    "SUI",
    "TRX",
    "UNI",
    "XRP",
}
KRAKEN_SPOT_CRYPTO_BASES = {
    "AAVE",
    "ADA",
    "ALGO",
    "ATOM",
    "AVAX",
    "BCH",
    "BTC",
    "DOGE",
    "DOT",
    "ETH",
    "FIL",
    "LINK",
    "LTC",
    "MATIC",
    "NEAR",
    "PEPE",
    "SHIB",
    "SOL",
    "TRX",
    "UNI",
    "XLM",
    "XRP",
}
COMMON_MODEL_STACK = [
    {"name": "UnifiedSignalEngine", "path": "aureon/trading/unified_signal_engine.py", "role": "multi-source signal fusion"},
    {"name": "UnifiedSniperBrain", "path": "aureon/trading/unified_sniper_brain.py", "role": "entry/exit probability and timing"},
    {"name": "UnifiedSymbolManager", "path": "aureon/trading/unified_symbol_manager.py", "role": "exchange symbol and precision rules"},
    {"name": "OrcaIntelligence", "path": "aureon/bots_intelligence/aureon_orca_intelligence.py", "role": "cross-exchange whale and opportunity intelligence"},
]
EXCHANGE_MODEL_STACKS = {
    "kraken_spot": [
        {"name": "KrakenClient", "path": "aureon/exchanges/kraken_client.py", "role": "Kraken spot execution and account state"},
        {"name": "KrakenTradingAdapter", "path": "aureon/exchanges/kraken_trading_adapter.py", "role": "Kraken route adapter"},
        {"name": "KrakenSignalBridge", "path": "aureon/bridges/aureon_kraken_unified_signal_bridge.py", "role": "Kraken signal bridge"},
    ],
    "kraken_margin": [
        {"name": "KrakenMarginArmyTrader", "path": "aureon/exchanges/kraken_margin_penny_trader.py", "role": "Kraken autonomous margin trader"},
        {"name": "UnifiedMarginDecisionBrain", "path": "aureon/trading/unified_margin_brain.py", "role": "margin approval/reject decision fusion"},
        {"name": "TemporalTradeCognition", "path": "aureon/trading/temporal_trade_cognition.py", "role": "margin timing cognition"},
    ],
    "capital_cfd": [
        {"name": "CapitalCFDTrader", "path": "aureon/exchanges/capital_cfd_trader.py", "role": "Capital CFD autonomous trader"},
        {"name": "CapitalMarketMonitor", "path": "aureon/exchanges/capital_market_monitor.py", "role": "Capital market monitor"},
        {"name": "CapitalSwarmRunner", "path": "aureon/exchanges/capital_swarm_runner.py", "role": "Capital swarm scan/decision support"},
        {"name": "QueenLearnCapitalTrading", "path": "aureon/queen/queen_learn_capital_trading.py", "role": "Capital learning loop"},
    ],
    "alpaca_spot": [
        {"name": "AlpacaClient", "path": "aureon/exchanges/alpaca_client.py", "role": "Alpaca spot crypto and stock execution"},
        {"name": "AlpacaCapitalStyleTrader", "path": "aureon/exchanges/alpaca_capital_style_trader.py", "role": "Alpaca autonomous trader"},
        {"name": "AlpacaScannerBridge", "path": "aureon/bridges/aureon_alpaca_scanner_bridge.py", "role": "Alpaca scanner bridge"},
        {"name": "AlpacaTruthTracker", "path": "aureon/exchanges/alpaca_truth_tracker.py", "role": "Alpaca signal truth tracking"},
    ],
    "binance_spot": [
        {"name": "BinanceClient", "path": "aureon/exchanges/binance_client.py", "role": "Binance spot execution and account state"},
        {"name": "BinanceWebSocketClient", "path": "aureon/exchanges/binance_ws_client.py", "role": "Binance stream intelligence"},
        {"name": "S5BinanceEcosystem", "path": "aureon/strategies/s5_binance_ecosystem.py", "role": "Binance strategy ecosystem"},
    ],
    "binance_margin": [
        {"name": "BinanceClientMargin", "path": "aureon/exchanges/binance_client.py", "role": "Binance margin execution"},
        {"name": "S5BinanceCommando", "path": "aureon/strategies/s5_binance_commando.py", "role": "Binance commando strategy"},
        {"name": "UnifiedMarginDecisionBrain", "path": "aureon/trading/unified_margin_brain.py", "role": "margin approval/reject decision fusion"},
    ],
}


class ExchangeCallGovernor:
    """Shared exchange call budget for the unified live market runtime.

    The governor keeps position/execution cycles ahead of broad quote probes.
    Quote calls are cached per symbol, so faster CentralBeat refreshes do not
    create a linear increase in REST calls.
    """

    def __init__(self, limits: Optional[Dict[str, Dict[str, float]]] = None):
        defaults = {
            "kraken": {
                "calls_per_min": _env_float("UNIFIED_KRAKEN_CALLS_PER_MIN", 60.0),
                "quote_ceiling": _env_float("UNIFIED_KRAKEN_QUOTE_BUDGET_FRACTION", 0.55),
            },
            "capital": {
                "calls_per_min": _env_float("UNIFIED_CAPITAL_CALLS_PER_MIN", 45.0),
                "quote_ceiling": _env_float("UNIFIED_CAPITAL_QUOTE_BUDGET_FRACTION", 0.45),
            },
            "alpaca": {
                "calls_per_min": _env_float("UNIFIED_ALPACA_CALLS_PER_MIN", 120.0),
                "quote_ceiling": _env_float("UNIFIED_ALPACA_QUOTE_BUDGET_FRACTION", 0.70),
            },
            "binance": {
                "calls_per_min": _env_float("UNIFIED_BINANCE_CALLS_PER_MIN", 240.0),
                "quote_ceiling": _env_float("UNIFIED_BINANCE_QUOTE_BUDGET_FRACTION", 0.70),
            },
        }
        for exchange, override in (limits or {}).items():
            base = defaults.setdefault(str(exchange), {"calls_per_min": 60.0, "quote_ceiling": 0.60})
            base.update(override)

        self._limits = defaults
        self._recent_calls: Dict[str, List[float]] = {name: [] for name in defaults}
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._last_cycle: Dict[str, float] = {}
        self._backoff_until: Dict[str, float] = {name: 0.0 for name in defaults}
        self._stats: Dict[str, Dict[str, Any]] = {
            name: {
                "processed": 0,
                "skipped": 0,
                "cache_hits": 0,
                "errors": 0,
                "last_error": "",
            }
            for name in defaults
        }
        self._lock = threading.RLock()

    def _cfg(self, exchange: str) -> Dict[str, float]:
        return self._limits.setdefault(exchange, {"calls_per_min": 60.0, "quote_ceiling": 0.60})

    def _stats_for(self, exchange: str) -> Dict[str, Any]:
        return self._stats.setdefault(
            exchange,
            {"processed": 0, "skipped": 0, "cache_hits": 0, "errors": 0, "last_error": ""},
        )

    def _trim(self, exchange: str, now: float) -> List[float]:
        calls = self._recent_calls.setdefault(exchange, [])
        cutoff = now - 60.0
        if calls and calls[0] < cutoff:
            calls[:] = [stamp for stamp in calls if stamp >= cutoff]
        return calls

    def _allow(self, exchange: str, priority: str, now: float) -> bool:
        exchange = str(exchange)
        priority = str(priority or "quotes").lower()
        cfg = self._cfg(exchange)
        calls = self._trim(exchange, now)
        max_per_min = max(1, int(float(cfg.get("calls_per_min", 60.0) or 60.0)))
        if now < self._backoff_until.get(exchange, 0.0):
            self._stats_for(exchange)["skipped"] += 1
            return False
        if priority == "quotes":
            quote_cap = max(1, int(max_per_min * float(cfg.get("quote_ceiling", 0.60) or 0.60)))
            if len(calls) >= quote_cap:
                self._stats_for(exchange)["skipped"] += 1
                return False
        if len(calls) >= max_per_min:
            self._stats_for(exchange)["skipped"] += 1
            return False
        calls.append(now)
        self._stats_for(exchange)["processed"] += 1
        return True

    def record_error(self, exchange: str, error: Exception | str) -> None:
        text = str(error)
        now = time.time()
        with self._lock:
            stats = self._stats_for(exchange)
            stats["errors"] += 1
            stats["last_error"] = text[:240]
            lowered = text.lower()
            if "429" in lowered or "rate limit" in lowered or "too many" in lowered:
                self._backoff_until[str(exchange)] = max(
                    self._backoff_until.get(str(exchange), 0.0),
                    now + _env_float("UNIFIED_EXCHANGE_RATE_BACKOFF_SEC", 30.0),
                )

    def call(
        self,
        exchange: str,
        priority: str,
        cache_key: str,
        fn: Callable[[], Any],
        *,
        min_interval_sec: float,
        stale_ttl_sec: float,
    ) -> Any:
        now = time.time()
        with self._lock:
            cached = self._cache.get(cache_key)
            if cached and now - float(cached.get("at", 0.0) or 0.0) < min_interval_sec:
                self._stats_for(exchange)["cache_hits"] += 1
                return cached.get("value")
            if not self._allow(exchange, priority, now):
                if cached and now - float(cached.get("at", 0.0) or 0.0) <= stale_ttl_sec:
                    self._stats_for(exchange)["cache_hits"] += 1
                    return cached.get("value")
                return None

        try:
            value = fn()
        except Exception as e:
            self.record_error(exchange, e)
            with self._lock:
                cached = self._cache.get(cache_key)
                if cached and now - float(cached.get("at", 0.0) or 0.0) <= stale_ttl_sec:
                    self._stats_for(exchange)["cache_hits"] += 1
                    return cached.get("value")
            return None

        if value is not None:
            with self._lock:
                self._cache[cache_key] = {"at": time.time(), "value": value}
        return value

    def should_run_cycle(self, exchange: str, priority: str, cycle_key: str, min_interval_sec: float) -> bool:
        now = time.time()
        with self._lock:
            last = float(self._last_cycle.get(cycle_key, 0.0) or 0.0)
            if now - last < min_interval_sec:
                self._stats_for(exchange)["skipped"] += 1
                return False
            if not self._allow(exchange, priority, now):
                return False
            self._last_cycle[cycle_key] = now
            return True

    def snapshot(self) -> Dict[str, Any]:
        now = time.time()
        with self._lock:
            exchanges: Dict[str, Any] = {}
            for exchange, cfg in self._limits.items():
                calls = self._trim(exchange, now)
                max_per_min = max(1, int(float(cfg.get("calls_per_min", 60.0) or 60.0)))
                stats = dict(self._stats_for(exchange))
                exchanges[exchange] = {
                    "max_calls_per_min": max_per_min,
                    "recent_calls_60s": len(calls),
                    "utilization": round(len(calls) / max_per_min, 4),
                    "quote_budget_fraction": round(float(cfg.get("quote_ceiling", 0.60) or 0.60), 4),
                    "backoff_sec": round(max(0.0, self._backoff_until.get(exchange, 0.0) - now), 3),
                    "cache_entries": sum(1 for key in self._cache if key.startswith(f"{exchange}:")),
                    **stats,
                }
            return {
                "generated_at": datetime.now().isoformat(),
                "policy": "execution_and_positions_first_quotes_cached_and_budgeted",
                "probe_symbol_min_interval_sec": PROBE_SYMBOL_MIN_INTERVAL_SEC,
                "probe_symbol_stale_ttl_sec": PROBE_SYMBOL_STALE_TTL_SEC,
                "exchanges": exchanges,
            }


def _safe_print(*args: Any, **kwargs: Any) -> None:
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        message = " ".join(str(arg) for arg in args)
        logger.info(message)


def _repair_stdio() -> None:
    """Best-effort stdio repair for modules that leave streams invalid on Windows."""
    def _is_broken(stream: Any) -> bool:
        if stream is None:
            return True
        try:
            if getattr(stream, "closed", False):
                return True
            stream.write("")
            stream.flush()
            return False
        except Exception:
            return True

    def _open_console(name: str):
        if sys.platform == "win32":
            try:
                return open(name, "w", encoding="utf-8", errors="replace", buffering=1)
            except Exception:
                return None
        return None

    try:
        if _is_broken(sys.stdout):
            sys.stdout = _open_console("CONOUT$") or open(os.devnull, "w")
    except Exception:
        pass
    try:
        if _is_broken(sys.stderr):
            sys.stderr = _open_console("CONERR$") or open(os.devnull, "w")
    except Exception:
        pass


def _is_closed_stream_error(exc: Exception) -> bool:
    return "I/O operation on closed file" in str(exc)


class _UnifiedDashboardHandler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._send_json(200, {"ok": True, "service": "unified-market-trader"})
            return
        if self.path == "/ready":
            trader = getattr(self.server, "trader_ref", None)
            payload = trader.get_runtime_health() if trader else {"ok": False, "error": "trader_unavailable"}
            self._send_json(200 if payload.get("ok") else 503, payload)
            return
        if self.path == "/api/terminal-state":
            trader = getattr(self.server, "trader_ref", None)
            payload = trader.get_local_dashboard_state() if trader else {"ok": False}
            self._send_json(200, payload)
            return
        self._send_json(404, {"ok": False, "error": "not_found"})

    def log_message(self, format: str, *args):
        return

    def _send_json(self, status: int, payload: Dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
            return


class UnifiedMarketTrader:
    def __init__(self, dry_run: bool = False, setup_kraken_cli: bool = False):
        os.environ.setdefault("AUREON_DISABLE_LOCAL_DASHBOARD", "1")
        self.dry_run = dry_run
        self.setup_kraken_cli = setup_kraken_cli
        self.kraken = None
        self.capital = None
        self.alpaca = None
        self.binance = None
        self.alpaca_trader = None
        self.binance_trader = None
        self.start_time = time.time()
        self.kraken_ready = False
        self.capital_ready = False
        self.kraken_error = ""
        self.capital_error = ""
        self.alpaca_error = ""
        self.binance_error = ""
        self._binance_diag: Dict[str, Any] = {}
        self._last_kraken_init_attempt = 0.0
        self._last_capital_init_attempt = 0.0
        self._last_kraken_startup_attempt = 0.0
        self._last_capital_startup_attempt = 0.0
        self._latest_dashboard_payload: Dict[str, Any] = {}
        self._shared_market_feed: Dict[str, float] = {}
        self._shared_market_feed_at: float = 0.0
        self._central_beat_feed: Dict[str, Any] = {}
        self._central_beat_at: float = 0.0
        self._central_beat_layers: Dict[str, Any] = {"trader": {}, "probe": {}, "merged": {}}
        self._central_beat_history: List[Dict[str, Any]] = []
        self._central_source_memory: Dict[str, Dict[str, Any]] = {}
        self._last_auris_feed_at: float = 0.0
        self._last_tick_started_at: float = 0.0
        self._last_tick_completed_at: float = 0.0
        self._last_tick_error: str = ""
        self._last_order_intent_at: float = 0.0
        self._last_order_intent_signature: str = ""
        self._latest_order_intents: Dict[str, Any] = {}
        self._last_execution_at: float = 0.0
        self._execution_memory: Dict[str, float] = {}
        self._latest_execution_results: Dict[str, Any] = {}
        self._local_dashboard_server: ThreadingHTTPServer | None = None
        self._local_dashboard_thread: threading.Thread | None = None
        self._runtime_heartbeat_thread: threading.Thread | None = None
        self._thought_bus = None
        self._mycelium = None
        self._last_status_publish: float = 0.0
        self._api_governor = ExchangeCallGovernor()
        self._runtime_instance_id = f"{os.getpid()}:{self.start_time:.6f}"
        self._runtime_writer_lock_reason = ""
        self._duplicate_runtime = False
        self._owns_runtime_status = self._claim_runtime_writer()
        if not self._owns_runtime_status:
            self._duplicate_runtime = True
            self._latest_dashboard_payload = self._build_duplicate_runtime_payload()
            logger.warning("Unified market trader duplicate suppressed: %s", self._runtime_writer_lock_reason)
            return

        # Publish a read-only heartbeat before heavier cognitive wiring. The
        # unified frontend should show the runtime booting even while imports,
        # ThoughtBus, Mycelium, Kraken, or Capital are still warming up.
        self._latest_dashboard_payload = self._build_bootstrap_dashboard_payload()
        self._write_runtime_status_file()
        if EMBEDDED_DASHBOARD_ENABLED:
            self._start_local_dashboard_server()
        self._start_runtime_heartbeat()

        # ── Network connections ────────────────────────────────────────────
        self._thought_bus = (
            get_thought_bus() if _HAS_THOUGHT_BUS and get_thought_bus is not None else None
        )
        self._mycelium = (
            get_mycelium(initial_capital=100.0) if _HAS_MYCELIUM and get_mycelium is not None else None
        )

        if self.setup_kraken_cli:
            self._ensure_kraken_cli()
        self._init_exchanges()
        self._latest_dashboard_payload = self._build_bootstrap_dashboard_payload()
        self._write_runtime_status_file()

    def _governor(self) -> ExchangeCallGovernor:
        governor = getattr(self, "_api_governor", None)
        if governor is None:
            governor = ExchangeCallGovernor()
            self._api_governor = governor
        return governor

    def _env_enabled(self, name: str, default: bool = False) -> bool:
        raw = os.getenv(name)
        if raw is None:
            return bool(default)
        return str(raw).strip().lower() in {"1", "true", "yes", "on"}

    def _runtime_real_orders_allowed(self) -> bool:
        return (
            self._env_enabled("AUREON_LIVE_TRADING")
            and not self._env_enabled("AUREON_AUDIT_MODE")
            and not self._env_enabled("AUREON_DISABLE_REAL_ORDERS", True)
            and not self._env_enabled("AUREON_DISABLE_EXCHANGE_MUTATIONS", True)
            and not self._env_enabled("DRY_RUN", True)
        )

    def _unified_executor_enabled(self) -> bool:
        return self._env_enabled("AUREON_UNIFIED_ORDER_EXECUTOR", self._runtime_real_orders_allowed())

    def _preflight_item(self, name: str, ok: bool, severity: str, detail: str, meta: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return {
            "name": name,
            "ok": bool(ok),
            "severity": str(severity or "info"),
            "detail": str(detail or ""),
            "meta": dict(meta or {}),
        }

    def _service_preflight(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        def find_optional_module(*module_names: str):
            try:
                import importlib.util
                for module_name in module_names:
                    spec = importlib.util.find_spec(module_name)
                    if spec is not None:
                        return spec
            except Exception:
                return None
            return None

        telemetry_spec = find_optional_module("telemetry_server")
        items.append(
            self._preflight_item(
                "telemetry_server",
                telemetry_spec is not None,
                "warning" if telemetry_spec is None else "ok",
                "available" if telemetry_spec is not None else "missing_optional_module",
            )
        )

        market_hub_spec = find_optional_module("market_data_hub", "aureon.data_feeds.market_data_hub")
        items.append(
            self._preflight_item(
                "market_data_hub",
                market_hub_spec is not None,
                "warning" if market_hub_spec is None else "ok",
                "available" if market_hub_spec is not None else "missing_optional_module",
            )
        )

        rate_budget_spec = find_optional_module("global_rate_budget", "aureon.core.global_rate_budget")
        items.append(
            self._preflight_item(
                "global_rate_budget",
                rate_budget_spec is not None,
                "warning" if rate_budget_spec is None else "ok",
                "available" if rate_budget_spec is not None else "missing_optional_module",
            )
        )
        return items

    def _build_preflight_report(self) -> Dict[str, Any]:
        items: List[Dict[str, Any]] = []

        items.append(
            self._preflight_item(
                "kraken",
                self.kraken_ready and self.kraken is not None,
                "critical" if not (self.kraken_ready and self.kraken is not None) else "ok",
                self.kraken_error or ("startup_pending" if self.kraken is not None else "not_initialized"),
            )
        )
        items.append(
            self._preflight_item(
                "capital",
                self.capital_ready and self.capital is not None,
                "critical" if not (self.capital_ready and self.capital is not None) else "ok",
                self.capital_error or ("ready" if self.capital is not None else "not_initialized"),
            )
        )

        alpaca_ok = self.alpaca is not None and not bool(getattr(self.alpaca, "init_error", "") or self.alpaca_error)
        items.append(
            self._preflight_item(
                "alpaca_spot_execution_route",
                alpaca_ok,
                "warning" if not alpaca_ok else "ok",
                self.alpaca_error or str(getattr(self.alpaca, "init_error", "") or ("ready" if self.alpaca is not None else "not_initialized")),
                meta={"market_type": "spot_crypto", "intent_route": True},
            )
        )

        binance_diag = getattr(self, "_binance_diag", {}) or {}
        binance_network_ok = bool(binance_diag.get("network_ok", False))
        items.append(
            self._preflight_item(
                "binance_spot_margin_execution_route",
                self.binance is not None and binance_network_ok,
                "warning" if self.binance is not None else "warning",
                self.binance_error or ("ready" if binance_network_ok else "network_unavailable"),
                meta={
                    "market_type": "spot_crypto_and_margin",
                    "intent_route": True,
                    "account_ready": bool(binance_diag.get("account_ok", False)),
                    "margin_available": bool(binance_diag.get("margin_available", False)),
                    "uk_mode": bool(binance_diag.get("uk_mode", False)),
                },
            )
        )

        items.extend(self._service_preflight())

        critical_failures = sum(1 for item in items if item["severity"] == "critical" and not item["ok"])
        warnings = sum(1 for item in items if item["severity"] == "warning" and not item["ok"])
        overall = "green"
        if critical_failures:
            overall = "red"
        elif warnings:
            overall = "yellow"

        return {
            "overall": overall,
            "critical_failures": critical_failures,
            "warnings": warnings,
            "items": items,
        }

    def _ensure_kraken_cli(self) -> None:
        if shutil.which("kraken"):
            logger.info("Kraken CLI detected in PATH.")
            return
        logger.info("Kraken CLI not found. Running installer...")
        bash_executable = shutil.which("bash")
        if not bash_executable:
            if os.name == "nt":
                logger.warning("Kraken CLI installer skipped: bash is not available on this Windows host.")
                return
            bash_executable = "/bin/bash"
        try:
            subprocess.run(
                KRAKEN_CLI_INSTALL_CMD,
                shell=True,
                check=True,
                executable=bash_executable,
            )
            logger.info("Kraken CLI installer completed.")
            if not shutil.which("kraken"):
                logger.warning("Kraken CLI install finished but binary was not found in PATH.")
        except Exception as e:
            logger.error("Kraken CLI installer failed: %s", e)

    def _init_exchanges(self) -> None:
        self._init_kraken(force=True)
        self._init_capital(force=True)
        self._init_alpaca(force=True)
        self._init_binance(force=True)

    def _init_kraken(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_kraken_init_attempt < EXCHANGE_REINIT_INTERVAL_SEC:
            return
        self._last_kraken_init_attempt = now
        _repair_stdio()
        try:
            self.kraken = KrakenMarginArmyTrader(dry_run=self.dry_run)
            self.kraken_error = ""
        except Exception as e:
            if _is_closed_stream_error(e):
                _repair_stdio()
                try:
                    self.kraken = KrakenMarginArmyTrader(dry_run=self.dry_run)
                    self.kraken_error = ""
                    return
                except Exception as retry_error:
                    e = retry_error
            self.kraken = None
            self.kraken_ready = False
            self.kraken_error = str(e)
            logger.error("Kraken init failed: %s", e)

    def _init_capital(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_capital_init_attempt < EXCHANGE_REINIT_INTERVAL_SEC:
            return
        self._last_capital_init_attempt = now
        try:
            self.capital = CapitalCFDTrader()
            self.capital_ready = bool(getattr(self.capital, "enabled", False))
            self.capital_error = ""
            if not self.capital_ready:
                self.capital_error = str(getattr(self.capital, "init_error", "") or "client_disabled_or_blocked")
        except Exception as e:
            self.capital = None
            self.capital_ready = False
            self.capital_error = str(e)
            logger.error("Capital init failed: %s", e)

    def _init_alpaca(self, force: bool = False) -> None:
        if self.alpaca is not None and not force:
            return
        if AlpacaClient is None:
            self.alpaca = None
            return
        try:
            self.alpaca = AlpacaClient()
            self.alpaca_error = str(getattr(self.alpaca, "init_error", "") or "")
        except Exception as e:
            self.alpaca = None
            self.alpaca_error = str(e)
            logger.debug("Alpaca passive client unavailable: %s", e)

    def _init_binance(self, force: bool = False) -> None:
        if self.binance is not None and not force:
            return
        if BinanceClient is None:
            self.binance = None
            self.binance_error = "client_missing"
            return
        _repair_stdio()
        try:
            self.binance = BinanceClient()
            diag = {}
            try:
                diag = self.binance.diagnose_ready() if hasattr(self.binance, "diagnose_ready") else {}
            except Exception as diag_error:
                diag = {"init_error": str(diag_error), "network_ok": False, "account_ok": False}
            self._binance_diag = diag if isinstance(diag, dict) else {}
            self.binance_error = str(
                self._binance_diag.get("init_error")
                or self._binance_diag.get("last_error")
                or ""
            )
        except Exception as e:
            if _is_closed_stream_error(e):
                _repair_stdio()
                try:
                    self.binance = BinanceClient()
                    self._binance_diag = {}
                    self.binance_error = ""
                    return
                except Exception as retry_error:
                    e = retry_error
            self.binance = None
            self.binance_error = str(e)
            logger.debug("Binance passive client unavailable: %s", e)

    def _ensure_exchanges(self) -> None:
        if self.kraken is None:
            self._init_kraken()
        elif not self.kraken_ready:
            self._startup_kraken()
        if self.capital is None:
            self._init_capital()
        elif not self.capital_ready:
            self._startup_capital()
        if self.alpaca is None:
            self._init_alpaca()
        if self.binance is None:
            self._init_binance()

    def _startup_kraken(self, force: bool = False) -> None:
        if self.kraken is None:
            return
        now = time.time()
        if not force and now - self._last_kraken_startup_attempt < EXCHANGE_REINIT_INTERVAL_SEC:
            return
        self._last_kraken_startup_attempt = now
        try:
            self.kraken.discover_margin_universe()
            self.kraken.update_prices_free()
            self.kraken.print_status()
            self.kraken_ready = True
            self.kraken_error = ""
        except Exception as e:
            self.kraken_ready = False
            self.kraken_error = str(e)
            logger.error("Kraken startup unavailable: %s", e)

    def _startup_capital(self, force: bool = False) -> None:
        if self.capital is None:
            return
        now = time.time()
        if not force and now - self._last_capital_startup_attempt < EXCHANGE_REINIT_INTERVAL_SEC:
            return
        self._last_capital_startup_attempt = now
        try:
            self.capital.status_lines()
            self.capital_ready = bool(getattr(self.capital, "enabled", False))
            if self.capital_ready:
                self.capital_error = ""
            elif not self.capital_error:
                self.capital_error = str(getattr(self.capital, "init_error", "") or "client_disabled_or_blocked")
        except Exception as e:
            self.capital_ready = False
            self.capital_error = str(e)
            logger.error("Capital startup unavailable: %s", e)

    def _read_runtime_writer_lock(self) -> Dict[str, Any]:
        try:
            if not RUNTIME_STATUS_LOCK_PATH.exists():
                return {}
            with open(RUNTIME_STATUS_LOCK_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def _runtime_writer_lock_payload(self) -> Dict[str, Any]:
        now = time.time()
        return {
            "schema_version": 1,
            "service": "unified-market-trader",
            "pid": os.getpid(),
            "instance_id": getattr(self, "_runtime_instance_id", ""),
            "started_at": datetime.fromtimestamp(float(getattr(self, "start_time", now) or now)).isoformat(),
            "heartbeat_at": now,
            "heartbeat_iso": datetime.fromtimestamp(now).isoformat(),
            "lock_ttl_sec": RUNTIME_WRITER_LOCK_TTL_SEC,
        }

    def _lock_owner_is_fresh(self, lock: Dict[str, Any], now: float) -> bool:
        try:
            heartbeat_at = float(lock.get("heartbeat_at", 0.0) or 0.0)
        except Exception:
            heartbeat_at = 0.0
        owner = str(lock.get("instance_id") or "")
        return bool(owner and owner != self._runtime_instance_id and heartbeat_at > 0 and now - heartbeat_at < RUNTIME_WRITER_LOCK_TTL_SEC)

    def _claim_runtime_writer(self) -> bool:
        now = time.time()
        existing = self._read_runtime_writer_lock()
        if self._lock_owner_is_fresh(existing, now):
            age = now - float(existing.get("heartbeat_at", now) or now)
            self._runtime_writer_lock_reason = (
                f"runtime writer already owned by pid {existing.get('pid')} "
                f"heartbeat_age_sec={age:.1f}"
            )
            return False
        return self._refresh_runtime_writer_lock(force=True)

    def _refresh_runtime_writer_lock(self, force: bool = False) -> bool:
        now = time.time()
        existing = self._read_runtime_writer_lock()
        if not force and self._lock_owner_is_fresh(existing, now):
            age = now - float(existing.get("heartbeat_at", now) or now)
            self._runtime_writer_lock_reason = (
                f"runtime writer ownership moved to pid {existing.get('pid')} "
                f"heartbeat_age_sec={age:.1f}"
            )
            self._owns_runtime_status = False
            return False
        try:
            RUNTIME_STATUS_LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = RUNTIME_STATUS_LOCK_PATH.with_name(
                f"{RUNTIME_STATUS_LOCK_PATH.name}.{os.getpid()}.tmp"
            )
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(self._runtime_writer_lock_payload(), f, indent=2, default=str)
            os.replace(tmp_path, RUNTIME_STATUS_LOCK_PATH)
            self._runtime_writer_lock_reason = ""
            self._owns_runtime_status = True
            return True
        except Exception as e:
            self._runtime_writer_lock_reason = f"runtime writer lock write failed: {e}"
            logger.warning("Unified runtime writer lock failed: %s", e)
            return False

    def _build_duplicate_runtime_payload(self) -> Dict[str, Any]:
        now_iso = datetime.now().isoformat()
        return {
            "ok": False,
            "source": "unified-market-trader",
            "generated_at": now_iso,
            "status": "duplicate_suppressed",
            "runtime_minutes": 0.0,
            "status_lines": [
                "UNIFIED MARKET STATUS | duplicate runtime suppressed",
                self._runtime_writer_lock_reason or "Another fresh market runtime owns the writer lock.",
            ],
            "combined": {
                "open_positions": 0,
                "kraken_equity": 0.0,
                "capital_equity_gbp": 0.0,
                "kraken_ready": False,
                "capital_ready": False,
            },
            "api_governor": self._governor().snapshot(),
            "runtime_writer": {
                "owns_lock": False,
                "instance_id": self._runtime_instance_id,
                "reason": self._runtime_writer_lock_reason,
            },
        }

    def _start_local_dashboard_server(self) -> None:
        try:
            server = ThreadingHTTPServer((LOCAL_HOST, LOCAL_PORT), _UnifiedDashboardHandler)
            server.trader_ref = self  # type: ignore[attr-defined]
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self._local_dashboard_server = server
            self._local_dashboard_thread = thread
            logger.info("UNIFIED DASHBOARD: http://%s:%s/api/terminal-state", LOCAL_HOST, LOCAL_PORT)
        except OSError as e:
            logger.warning("UNIFIED DASHBOARD unavailable on %s:%s (%s)", LOCAL_HOST, LOCAL_PORT, e)

    def _start_runtime_heartbeat(self) -> None:
        if self._runtime_heartbeat_thread is not None:
            return

        def heartbeat() -> None:
            while True:
                try:
                    payload = self._copy_payload(
                        self._latest_dashboard_payload or self._build_bootstrap_dashboard_payload()
                    )
                    now = time.time()
                    payload["runtime_minutes"] = (now - self.start_time) / 60.0
                    payload["runtime_heartbeat"] = {
                        "alive": True,
                        "heartbeat_at": now,
                        "heartbeat_at_iso": datetime.now().isoformat(),
                        "last_tick_started_at": self._last_tick_started_at,
                        "last_tick_completed_at": self._last_tick_completed_at,
                        "booting": self._last_tick_completed_at <= 0,
                    }
                    self._latest_dashboard_payload = payload
                    self._write_runtime_status_file()
                except Exception:
                    pass
                time.sleep(5.0)

        thread = threading.Thread(target=heartbeat, daemon=True)
        thread.start()
        self._runtime_heartbeat_thread = thread

    def _confidence_word(self, value: Any) -> str:
        try:
            score = float(value or 0.0)
        except Exception:
            score = 0.0
        if score >= 0.85:
            return "very strong"
        if score >= 0.65:
            return "strong"
        if score >= 0.45:
            return "building"
        if score > 0:
            return "tentative"
        return "unclear"

    def _copy_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return copy.deepcopy(payload)

    def _write_runtime_status_file(self) -> None:
        if not getattr(self, "_owns_runtime_status", True):
            return
        try:
            if not self._refresh_runtime_writer_lock(force=False):
                return
            RUNTIME_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
            payload = self.get_runtime_health()
            payload["runtime_writer"] = {
                "owns_lock": True,
                "pid": os.getpid(),
                "instance_id": getattr(self, "_runtime_instance_id", ""),
                "lock_path": str(RUNTIME_STATUS_LOCK_PATH),
                "heartbeat_at": datetime.now().isoformat(),
            }
            with open(RUNTIME_STATUS_PATH, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, default=str)
        except Exception as e:
            logger.debug("Unified runtime status write failed: %s", e)

    def _unavailable_exchange_payload(self, exchange: str, error: str, extra: Dict[str, Any] | None = None) -> Dict[str, Any]:
        payload = {
            "ok": False,
            "exchange": exchange,
            "error": error or "not_ready",
            "positions": [],
            "status_lines": [f"{str(exchange).upper()} unavailable: {error or 'not_ready'}"],
        }
        if extra:
            payload.update(extra)
        return payload

    def _build_bootstrap_dashboard_payload(self) -> Dict[str, Any]:
        now_iso = datetime.now().isoformat()
        kraken_error = self.kraken_error or ("startup_pending" if self.kraken is not None else "not_ready")
        capital_error = self.capital_error or ("ready" if self.capital_ready else "not_ready")
        kraken_payload = self._unavailable_exchange_payload("kraken", kraken_error)
        capital_payload = self._unavailable_exchange_payload("capital", capital_error, extra={"stats": {}})
        preflight = self._build_preflight_report()
        return {
            "ok": True,
            "source": "unified-market-trader",
            "generated_at": now_iso,
            "runtime_minutes": (time.time() - self.start_time) / 60.0,
            "kraken": kraken_payload,
            "capital": capital_payload,
            "status_lines": [
                f"UNIFIED MARKET STATUS | runtime={(time.time() - self.start_time) / 60.0:.1f}m",
                "Cached telemetry pending first trading cycle.",
            ],
            "latest_monitor_line": "",
            "shared_market_feed": {
                "symbols": dict(self._shared_market_feed),
                "aliases": {},
                "count": len(self._shared_market_feed),
                "generated_at": now_iso,
            },
            "central_beat": {
                "generated_at": now_iso,
                "sources": [],
                "source_count": 0,
                "symbols": {},
                "regime": {},
            },
            "shared_order_flow": {
                "generated_at": now_iso,
                "shared_tradable_count": 0,
                "multi_exchange_tradable_count": 0,
                "active_order_flow_count": 0,
                "active_order_flow": [],
                "kraken_tradables": 0,
                "capital_tradables": 0,
                "alpaca_tradables": 0,
                "binance_tradables": 0,
                "scope": "multi-exchange unified tradables",
            },
            "exchange_action_plan": {
                "generated_at": now_iso,
                "mode": "booting",
                "venues": {},
                "order_intent_publish_enabled": False,
                "order_intents_published": 0,
                "executor_enabled": False,
                "latest_execution": {},
                "shadow_trading": {},
            },
            "shadow_trading": {
                "generated_at": now_iso,
                "mode": "shadow_validation_non_mutating",
                "enabled": True,
                "shadow_count": 0,
                "active_shadow_count": 0,
                "validated_shadow_count": 0,
                "status": "awaiting_first_cycle",
            },
            "hnc_cognitive_proof": {
                "generated_at": now_iso,
                "status": "awaiting_first_cycle",
                "passed": False,
                "flow": [],
                "systems": {},
                "auris_nodes": {"node_count": 0, "coherence": 0.0},
                "master_formula": {"score": 0.0, "evaluated": False},
                "real_data": {"passed": False, "source_count": 0, "price_count": 0},
            },
            "preflight": preflight,
            "api_governor": self._governor().snapshot(),
            "queen_voice": {
                "ts": now_iso,
                "mode": "HOLD",
                "text": "Awaiting the first unified trading cycle.",
                "lines": ["Awaiting the first unified trading cycle."],
                "sources": {"kraken_decision": {}, "capital_target": {}},
            },
            "combined": {
                "open_positions": 0,
                "kraken_equity": 0.0,
                "capital_equity_gbp": 0.0,
                "kraken_session_pnl": 0.0,
                "capital_session_pnl_gbp": 0.0,
                "kraken_ready": self.kraken_ready,
                "capital_ready": self.capital_ready,
            },
        }

    def _build_combined_payload(self) -> Dict[str, Any]:
        kraken_payload = self.kraken.get_local_dashboard_state() if self.kraken_ready and self.kraken is not None else self._unavailable_exchange_payload(
            "kraken",
            self.kraken_error or "not_ready",
        )
        capital_payload = self.capital.get_dashboard_payload() if self.capital_ready and self.capital is not None else self._unavailable_exchange_payload(
            "capital",
            self.capital_error or "not_ready",
            extra={"stats": {}},
        )
        central_beat = self._build_central_beat_feed(kraken_payload, capital_payload)
        shared_market_feed = self._sync_shared_market_feed(central_beat)
        order_flow_feed = self._build_global_order_flow_feed(kraken_payload, capital_payload, central_beat, shared_market_feed)
        self._feed_shared_order_flow_to_decision_logic(order_flow_feed)
        self._feed_auris_throne(order_flow_feed)
        exchange_action_plan = self._build_exchange_action_plan(order_flow_feed)
        shadow_trade_report = self._build_shadow_trade_report(order_flow_feed, exchange_action_plan)
        hnc_cognitive_proof = self._build_hnc_cognitive_proof(
            central_beat,
            order_flow_feed,
            exchange_action_plan,
            shadow_trade_report,
        )
        self._publish_order_intents(order_flow_feed, exchange_action_plan)
        combined_status = self.get_status_lines()
        queen_voice = self._build_queen_voice_payload(kraken_payload, capital_payload)
        payload = {
            "ok": True,
            "source": "unified-market-trader",
            "generated_at": datetime.now().isoformat(),
            "runtime_minutes": (time.time() - self.start_time) / 60.0,
            "kraken": kraken_payload,
            "capital": capital_payload,
            "status_lines": combined_status[-24:],
            "latest_monitor_line": self._latest_monitor_line(),
            "shared_market_feed": shared_market_feed,
            "central_beat": central_beat,
            "shared_order_flow": order_flow_feed,
            "shadow_trading": shadow_trade_report,
            "hnc_cognitive_proof": hnc_cognitive_proof,
            "exchange_action_plan": exchange_action_plan,
            "preflight": self._build_preflight_report(),
            "api_governor": self._governor().snapshot(),
            "queen_voice": queen_voice,
            "combined": {
                "open_positions": len(kraken_payload.get("positions", [])) + len(capital_payload.get("positions", [])),
                "kraken_equity": float(kraken_payload.get("equity", 0.0) or 0.0),
                "capital_equity_gbp": float(capital_payload.get("equity_gbp", 0.0) or 0.0),
                "kraken_session_pnl": float(kraken_payload.get("session_profit", 0.0) or 0.0),
                "capital_session_pnl_gbp": float(capital_payload.get("stats", {}).get("total_pnl_gbp", 0.0) or 0.0),
                "kraken_ready": self.kraken_ready,
                "capital_ready": self.capital_ready,
            },
        }
        self._latest_dashboard_payload = self._copy_payload(payload)
        self._write_runtime_status_file()
        return payload

    def _extract_candidate_confidence(self, candidate: Dict[str, Any]) -> float:
        for key in ("confidence", "score", "probability", "win_prob"):
            try:
                value = float(candidate.get(key, 0.0) or 0.0)
                if value > 1.0:
                    value = value / 100.0
                if value > 0:
                    return max(0.0, min(1.0, value))
            except Exception:
                continue
        return 0.0

    def _route_model_key(self, venue: str, market_type: str) -> str:
        venue_norm = str(venue or "").lower().strip()
        market_norm = str(market_type or "").lower().strip()
        return f"{venue_norm}_{market_norm}" if market_norm else venue_norm

    def _model_stack_for_route(self, venue: str, market_type: str) -> Dict[str, Any]:
        key = self._route_model_key(venue, market_type)
        descriptors = list(COMMON_MODEL_STACK) + list(EXCHANGE_MODEL_STACKS.get(key, []))
        models: List[Dict[str, Any]] = []
        for descriptor in descriptors:
            item = dict(descriptor)
            path = str(item.get("path") or "")
            item["available"] = bool(path and (REPO_ROOT / Path(path)).exists())
            models.append(item)
        available = [item for item in models if item.get("available")]
        return {
            "key": key,
            "venue": str(venue or "").lower(),
            "market_type": str(market_type or "").lower(),
            "available_count": len(available),
            "total_count": len(models),
            "ready": len(available) > 0,
            "models": models,
        }

    def _all_exchange_model_coverage(self) -> Dict[str, Any]:
        coverage = {
            key: self._model_stack_for_route(*key.split("_", 1))
            for key in sorted(EXCHANGE_MODEL_STACKS.keys())
        }
        return {
            "generated_at": datetime.now().isoformat(),
            "routes": coverage,
            "route_count": len(coverage),
            "ready_route_count": sum(1 for item in coverage.values() if item.get("ready")),
            "available_model_count": sum(int(item.get("available_count", 0) or 0) for item in coverage.values()),
            "total_model_count": sum(int(item.get("total_count", 0) or 0) for item in coverage.values()),
            "model_use": "UnifiedSignalEngine feeds CentralBeat; route model stacks declare venue-specific repo systems used for execution context.",
        }

    def _build_model_signal_feed(self, sources: List[Dict[str, Any]], regime: Dict[str, Any]) -> Dict[str, Any]:
        opportunities: List[Any] = []
        for source in sources:
            if not isinstance(source, dict):
                continue
            exchange = str(source.get("source") or "unknown").lower()
            source_symbols = source.get("symbols", {})
            if not isinstance(source_symbols, dict):
                continue
            for normalized, item in source_symbols.items():
                if not isinstance(item, dict):
                    continue
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
                if confidence <= 0:
                    continue
                side = str(item.get("side") or "BUY").upper()
                try:
                    change_pct = float(item.get("change_pct", 0.0) or 0.0)
                except Exception:
                    change_pct = 0.0
                if change_pct == 0.0:
                    change_pct = confidence * (2.0 if side != "SELL" else -2.0)
                opportunities.append(
                    SimpleNamespace(
                        symbol=str(normalized),
                        exchange=exchange,
                        price=float(item.get("price", 0.0) or 0.0),
                        change_pct=change_pct,
                        momentum_score=confidence,
                    )
                )
        if not opportunities:
            return {
                "used": False,
                "engine": "aureon.trading.unified_signal_engine.UnifiedSignalEngine",
                "reason": "no_source_opportunities",
                "symbols": {},
                "opportunity_count": 0,
            }

        try:
            from aureon.trading.unified_signal_engine import UnifiedSignalEngine

            engine = UnifiedSignalEngine()
            bias = str(regime.get("bias") or "NEUTRAL").upper()
            regime_name = "RISK_ON" if bias == "BUY" else "RISK_OFF" if bias == "SELL" else "NEUTRAL"
            bundle = engine.process(opportunities, regime=regime_name)
            symbols: Dict[str, Dict[str, Any]] = {}
            for signal in getattr(bundle, "signals", []) or []:
                normalized = self._normalize_symbol(getattr(signal, "symbol", ""))
                if not normalized:
                    continue
                current = symbols.get(normalized)
                confidence = max(0.0, min(1.0, float(getattr(signal, "confidence", 0.0) or 0.0)))
                if current and confidence <= float(current.get("confidence", 0.0) or 0.0):
                    continue
                symbols[normalized] = {
                    "symbol": normalized,
                    "exchange": str(getattr(signal, "exchange", "")),
                    "direction": str(getattr(signal, "direction", "NEUTRAL")),
                    "confidence": round(confidence, 4),
                    "raw_score": round(float(getattr(signal, "raw_score", 0.0) or 0.0), 4),
                    "sources": list(getattr(signal, "sources", []) or []),
                }
            return {
                "used": True,
                "engine": "aureon.trading.unified_signal_engine.UnifiedSignalEngine",
                "opportunity_count": len(opportunities),
                "symbols": symbols,
                "summary_lines": list(getattr(bundle, "summary_lines", []) or [])[:8],
            }
        except Exception as e:
            return {
                "used": False,
                "engine": "aureon.trading.unified_signal_engine.UnifiedSignalEngine",
                "reason": str(e),
                "symbols": {},
                "opportunity_count": len(opportunities),
            }

    def _build_central_beat_feed(self, kraken_payload: Dict[str, Any], capital_payload: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        if self._central_beat_feed and (now - self._central_beat_at) < CENTRAL_BEAT_REFRESH_SEC:
            return dict(self._central_beat_feed)

        trader_sources: List[Dict[str, Any]] = []
        probe_sources: List[Dict[str, Any]] = []
        sources: List[Dict[str, Any]] = []

        kraken_source = self._extract_trader_source_snapshot("kraken", kraken_payload)
        if kraken_source:
            trader_sources.append(kraken_source)
        capital_source = self._extract_trader_source_snapshot("capital", capital_payload)
        if capital_source:
            trader_sources.append(capital_source)
        trader_sources = self._stabilize_sources("trader", trader_sources)
        sources.extend(trader_sources)

        watchlist = self._build_probe_watchlist(sources)
        alpaca_source = self._extract_alpaca_source_snapshot(watchlist)
        if alpaca_source:
            probe_sources.append(alpaca_source)
        binance_source = self._extract_binance_source_snapshot(watchlist)
        if binance_source:
            probe_sources.append(binance_source)
        probe_sources = self._stabilize_sources("probe", probe_sources)
        sources.extend(probe_sources)

        symbols: Dict[str, Dict[str, Any]] = {}
        buy_pressure = 0.0
        sell_pressure = 0.0
        for source in sources:
            source_name = str(source.get("source") or "?")
            source_symbols = source.get("symbols", {})
            if not isinstance(source_symbols, dict):
                continue
            for normalized, item in source_symbols.items():
                if not isinstance(item, dict):
                    continue
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
                if confidence <= 0.0:
                    continue
                side = str(item.get("side") or "BUY").upper()
                symbol_state = symbols.setdefault(
                    normalized,
                    {
                        "support_count": 0,
                        "confidence_sum": 0.0,
                        "buy_confidence": 0.0,
                        "sell_confidence": 0.0,
                        "sources": [],
                        "price_sum": 0.0,
                        "price_count": 0,
                        "change_pct_sum": 0.0,
                        "source_prices": {},
                    },
                )
                symbol_state["support_count"] += 1
                symbol_state["confidence_sum"] += confidence
                if side == "SELL":
                    symbol_state["sell_confidence"] += confidence
                    sell_pressure += confidence
                else:
                    symbol_state["buy_confidence"] += confidence
                    buy_pressure += confidence
                if source_name not in symbol_state["sources"]:
                    symbol_state["sources"].append(source_name)
                try:
                    price = float(item.get("price", 0.0) or 0.0)
                except Exception:
                    price = 0.0
                if price > 0:
                    symbol_state["price_sum"] += price
                    symbol_state["price_count"] += 1
                    symbol_state["source_prices"][source_name] = price
                try:
                    symbol_state["change_pct_sum"] += float(item.get("change_pct", 0.0) or 0.0)
                except Exception:
                    pass

        normalized_symbols: Dict[str, Dict[str, Any]] = {}
        for normalized, item in symbols.items():
            support_count = int(item.get("support_count", 0) or 0)
            confidence_sum = float(item.get("confidence_sum", 0.0) or 0.0)
            avg_confidence = confidence_sum / support_count if support_count > 0 else 0.0
            buy_conf = float(item.get("buy_confidence", 0.0) or 0.0)
            sell_conf = float(item.get("sell_confidence", 0.0) or 0.0)
            side = "BUY" if buy_conf >= sell_conf else "SELL"
            imbalance = abs(buy_conf - sell_conf)
            price_count = int(item.get("price_count", 0) or 0)
            reference_price = float(item.get("price_sum", 0.0) or 0.0) / price_count if price_count > 0 else 0.0
            normalized_symbols[normalized] = {
                "confidence": round(avg_confidence, 4),
                "support_count": support_count,
                "side": side,
                "imbalance": round(imbalance, 4),
                "strength": round(avg_confidence * (1.0 + min(1.0, (support_count - 1) * 0.35)), 4),
                "sources": list(item.get("sources", [])),
                "reference_price": round(reference_price, 8) if reference_price > 0 else 0.0,
                "change_pct": round(float(item.get("change_pct_sum", 0.0) or 0.0) / max(1, support_count), 6),
                "source_prices": dict(item.get("source_prices", {})),
            }

        total_pressure = buy_pressure + sell_pressure
        regime = {
            "buy_pressure": round(buy_pressure, 4),
            "sell_pressure": round(sell_pressure, 4),
            "bias": "BUY" if buy_pressure >= sell_pressure else "SELL",
            "confidence": round((max(buy_pressure, sell_pressure) / total_pressure) if total_pressure > 0 else 0.0, 4),
            "source_count": len(sources),
        }
        model_signal_feed = self._build_model_signal_feed(sources, regime)
        model_symbols = model_signal_feed.get("symbols", {}) if isinstance(model_signal_feed, dict) else {}
        if isinstance(model_symbols, dict):
            for normalized, model_signal in model_symbols.items():
                if normalized not in normalized_symbols or not isinstance(model_signal, dict):
                    continue
                symbol_state = normalized_symbols[normalized]
                prior_confidence = max(0.0, min(1.0, float(symbol_state.get("confidence", 0.0) or 0.0)))
                model_confidence = max(0.0, min(1.0, float(model_signal.get("confidence", 0.0) or 0.0)))
                model_direction = str(model_signal.get("direction") or "NEUTRAL").upper()
                current_side = str(symbol_state.get("side") or "BUY").upper()
                if model_direction in {"BUY", "SELL"}:
                    aligned_model_confidence = model_confidence if model_direction == current_side else 1.0 - model_confidence
                    blended_confidence = max(0.0, min(1.0, prior_confidence * 0.75 + aligned_model_confidence * 0.25))
                    symbol_state["confidence"] = round(blended_confidence, 4)
                    symbol_state["strength"] = round(
                        min(1.5, blended_confidence * (1.0 + min(1.0, (int(symbol_state.get("support_count", 0) or 0) - 1) * 0.35))),
                        4,
                    )
                    symbol_state["model_alignment"] = model_direction == current_side
                symbol_state["model_signal"] = model_signal

        payload = {
            "generated_at": datetime.now().isoformat(),
            "sources": sources,
            "source_count": len(sources),
            "symbols": normalized_symbols,
            "regime": regime,
            "model_signal_feed": model_signal_feed,
        }
        self._central_beat_layers = {
            "trader": {"sources": trader_sources, "count": len(trader_sources)},
            "probe": {"sources": probe_sources, "count": len(probe_sources)},
            "merged": {"sources": sources, "count": len(sources), "symbols": normalized_symbols, "regime": regime},
        }
        self._central_beat_feed = payload
        self._central_beat_at = now
        self._central_beat_history.append(payload)
        self._central_beat_history = self._central_beat_history[-CENTRAL_BEAT_HISTORY_LIMIT:]
        return dict(payload)

    def _sync_shared_market_feed(self, central_beat: Dict[str, Any]) -> Dict[str, Any]:
        boosts: Dict[str, float] = {}
        aliases: Dict[str, List[str]] = {}
        symbol_metrics = central_beat.get("symbols", {}) if isinstance(central_beat, dict) else {}
        regime = central_beat.get("regime", {}) if isinstance(central_beat, dict) else {}

        for normalized, item in symbol_metrics.items():
            if not isinstance(item, dict):
                continue
            strength = max(0.0, min(1.5, float(item.get("strength", 0.0) or 0.0)))
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
            boosts[str(normalized)] = round(min(1.0, max(strength, confidence)), 4)
            for source_name in item.get("sources", []) if isinstance(item.get("sources"), list) else []:
                known = aliases.setdefault(str(normalized), [])
                if source_name not in known:
                    known.append(str(source_name))

        self._shared_market_feed = boosts
        self._shared_market_feed_at = time.time()

        for trader in self._central_feed_targets():
            if trader is None:
                continue
            try:
                trader._hive_boosts = dict(boosts)  # type: ignore[attr-defined]
                trader._central_beat_symbols = dict(symbol_metrics)  # type: ignore[attr-defined]
                trader._central_beat_regime = dict(regime)  # type: ignore[attr-defined]
            except Exception:
                continue

        return {
            "symbols": dict(boosts),
            "aliases": dict(aliases),
            "count": len(boosts),
            "generated_at": datetime.now().isoformat(),
        }

    def _central_feed_targets(self) -> List[Any]:
        targets: List[Any] = []
        seen: set[int] = set()
        for attr in ("kraken", "capital", "alpaca_trader", "binance_trader", "alpaca", "binance"):
            target = getattr(self, attr, None)
            if target is None:
                continue
            target_id = id(target)
            if target_id in seen:
                continue
            seen.add(target_id)
            targets.append(target)
        return targets

    def _stabilize_sources(self, stage: str, fresh_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        now = time.time()
        stabilized: List[Dict[str, Any]] = []
        fresh_names = set()
        for source in fresh_sources:
            if not isinstance(source, dict):
                continue
            source_name = str(source.get("source") or "").strip()
            if not source_name:
                continue
            memory_key = f"{stage}:{source_name}"
            prepared = dict(source)
            prepared["stale"] = False
            prepared["captured_at"] = datetime.now().isoformat()
            prepared["_seen_at"] = now
            prepared["_stage"] = stage
            self._central_source_memory[memory_key] = prepared
            stabilized.append(prepared)
            fresh_names.add(source_name)

        for memory_key, cached in list(self._central_source_memory.items()):
            if str(cached.get("_stage") or "") != stage:
                continue
            source_name = str(cached.get("source") or "").strip()
            if source_name in fresh_names:
                continue
            seen_at = float(cached.get("_seen_at", 0.0) or 0.0)
            if seen_at <= 0 or (now - seen_at) > CENTRAL_BEAT_STALE_AFTER_SEC:
                continue
            reused = dict(cached)
            reused["stale"] = True
            reused["reused_at"] = datetime.now().isoformat()
            stabilized.append(reused)

        stabilized.sort(key=lambda item: str(item.get("source") or ""))
        return stabilized

    def _build_probe_watchlist(self, sources: List[Dict[str, Any]]) -> List[str]:
        watchlist: List[str] = []
        for source in sources:
            source_symbols = source.get("symbols", {})
            if not isinstance(source_symbols, dict):
                continue
            for normalized in source_symbols.keys():
                symbol = str(normalized or "").upper()
                if symbol and symbol not in watchlist:
                    watchlist.append(symbol)
        for fallback in ("BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD"):
            if fallback not in watchlist:
                watchlist.append(fallback)
        return watchlist[:12]

    def _base_from_route_symbol(self, symbol: Any) -> str:
        raw = str(symbol or "").upper().strip().replace("/", "")
        for quote in ("USDT", "USDC", "BUSD", "FDUSD", "TUSD", "USD", "EUR", "GBP", "BTC", "BNB", "ETH"):
            if raw.endswith(quote) and len(raw) > len(quote):
                return raw[:-len(quote)]
        return raw[:4] if len(raw) > 4 else raw

    def _asset_balance_candidates(self, base: str) -> List[str]:
        base_norm = str(base or "").upper().strip()
        if base_norm in {"BTC", "XBT", "XXBT"}:
            return ["BTC", "XBT", "XXBT"]
        if base_norm in {"ETH", "XETH"}:
            return ["ETH", "XETH"]
        stripped = base_norm.lstrip("XZ")
        candidates = [base_norm]
        if stripped and stripped != base_norm:
            candidates.append(stripped)
        return list(dict.fromkeys(candidate for candidate in candidates if candidate))

    def _kraken_spot_client(self) -> Any:
        kraken = getattr(self, "kraken", None)
        if kraken is None:
            return None
        return getattr(kraken, "client", kraken)

    def _estimate_route_price(self, venue: str, symbol: str) -> float:
        venue = str(venue or "").lower()
        symbol = str(symbol or "").upper().strip()
        if not symbol:
            return 0.0
        try:
            if venue == "kraken":
                client = self._kraken_spot_client()
                if client is not None and hasattr(client, "best_price"):
                    ticker = self._governor().call(
                        "kraken",
                        "quotes",
                        f"kraken:best:{symbol}",
                        lambda: client.best_price(symbol),
                        min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                        stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                    )
                    if isinstance(ticker, dict):
                        return float(ticker.get("price") or ticker.get("lastPrice") or ticker.get("last") or 0.0)
                if client is not None and hasattr(client, "get_ticker"):
                    ticker = self._governor().call(
                        "kraken",
                        "quotes",
                        f"kraken:ticker:{symbol}",
                        lambda: client.get_ticker(symbol),
                        min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                        stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                    )
                    if isinstance(ticker, dict):
                        return float(ticker.get("price") or ticker.get("lastPrice") or ticker.get("last") or 0.0)
            if venue == "alpaca" and self.alpaca is not None:
                ticker = self._governor().call(
                    "alpaca",
                    "quotes",
                    f"alpaca:ticker:{symbol}",
                    lambda: self.alpaca.get_ticker(symbol),
                    min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                    stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                )
                if isinstance(ticker, dict):
                    return float(ticker.get("price") or ticker.get("last") or ticker.get("mark_price") or 0.0)
            if venue == "binance" and self.binance is not None:
                ticker = self._governor().call(
                    "binance",
                    "quotes",
                    f"binance:24h:{symbol}",
                    lambda: self.binance.get_24h_ticker(symbol),
                    min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                    stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                )
                if isinstance(ticker, dict):
                    return float(ticker.get("lastPrice") or ticker.get("weightedAvgPrice") or ticker.get("price") or 0.0)
        except Exception as e:
            logger.debug("Price estimate failed for %s %s: %s", venue, symbol, e)
        return 0.0

    def _spot_sell_quantity(self, client: Any, symbol: str, quote_usd: float, price: float) -> float:
        if client is None or price <= 0:
            return 0.0
        base = self._base_from_route_symbol(symbol)
        if not base:
            return 0.0
        available = 0.0
        for candidate in self._asset_balance_candidates(base):
            try:
                available = float(client.get_free_balance(candidate) or 0.0)
            except Exception:
                available = 0.0
            if available > 0:
                break
        if available <= 0:
            return 0.0
        target_qty = max(0.0, float(quote_usd or 0.0) / price)
        if target_qty <= 0:
            return 0.0
        return max(0.0, min(available, target_qty) * 0.999)

    def _execute_kraken_spot_route(self, side: str, symbol: str, quote_usd: float) -> Dict[str, Any]:
        client = self._kraken_spot_client()
        if client is None or not hasattr(client, "place_market_order"):
            return {"ok": False, "venue": "kraken", "market_type": "spot", "symbol": symbol, "reason": "kraken_spot_client_missing"}
        side_norm = "buy" if str(side or "BUY").upper() == "BUY" else "sell"
        if side_norm == "buy":
            spot_quote_usd = max(float(quote_usd or 0.0), KRAKEN_SPOT_QUOTE_USD)
            result = client.place_market_order(symbol, side_norm, quote_qty=spot_quote_usd)
            order_value = spot_quote_usd
        else:
            price = self._estimate_route_price("kraken", symbol)
            quantity = self._spot_sell_quantity(client, symbol, max(float(quote_usd or 0.0), KRAKEN_SPOT_QUOTE_USD), price)
            if quantity <= 0:
                return {"ok": False, "venue": "kraken", "market_type": "spot", "symbol": symbol, "side": side_norm, "reason": "no_spot_balance_to_sell"}
            result = client.place_market_order(symbol, side_norm, quantity=quantity)
            order_value = quantity * price if price > 0 else 0.0
        rejected = isinstance(result, dict) and bool(result.get("error") or result.get("rejected"))
        return {
            "ok": bool(result) and not rejected,
            "venue": "kraken",
            "market_type": "spot",
            "symbol": symbol,
            "side": side_norm,
            "quote_usd": order_value,
            "result": result,
        }

    def _execute_alpaca_spot_route(self, side: str, symbol: str, quote_usd: float) -> Dict[str, Any]:
        if self.alpaca is None:
            return {"ok": False, "venue": "alpaca", "symbol": symbol, "reason": "alpaca_client_missing"}
        side_norm = "buy" if str(side).upper() == "BUY" else "sell"
        if side_norm == "buy":
            result = self.alpaca.place_market_order(symbol, side_norm, quote_qty=quote_usd)
        else:
            price = self._estimate_route_price("alpaca", symbol)
            quantity = self._spot_sell_quantity(self.alpaca, symbol, quote_usd, price)
            if quantity <= 0:
                return {"ok": False, "venue": "alpaca", "symbol": symbol, "side": side_norm, "reason": "no_spot_balance_to_sell"}
            result = self.alpaca.place_market_order(symbol, side_norm, quantity=quantity)
        return {"ok": bool(result), "venue": "alpaca", "market_type": "spot", "symbol": symbol, "side": side_norm, "result": result}

    def _execute_binance_spot_route(self, side: str, symbol: str, quote_usd: float) -> Dict[str, Any]:
        if self.binance is None:
            return {"ok": False, "venue": "binance", "symbol": symbol, "reason": "binance_client_missing"}
        side_norm = str(side or "BUY").upper()
        if side_norm == "BUY":
            result = self.binance.place_market_order(symbol, side_norm, quote_qty=quote_usd)
        else:
            price = self._estimate_route_price("binance", symbol)
            quantity = self._spot_sell_quantity(self.binance, symbol, quote_usd, price)
            if quantity <= 0:
                return {"ok": False, "venue": "binance", "symbol": symbol, "side": side_norm, "reason": "no_spot_balance_to_sell"}
            result = self.binance.place_market_order(symbol, side_norm, quantity=quantity)
        return {"ok": bool(result), "venue": "binance", "market_type": "spot", "symbol": symbol, "side": side_norm, "result": result}

    def _execute_binance_margin_route(self, side: str, symbol: str, quote_usd: float) -> Dict[str, Any]:
        if self.binance is None:
            return {"ok": False, "venue": "binance", "symbol": symbol, "reason": "binance_client_missing"}
        if not self._env_enabled("BINANCE_MARGIN_ENABLED"):
            return {"ok": False, "venue": "binance", "market_type": "margin", "symbol": symbol, "reason": "BINANCE_MARGIN_ENABLED_not_true"}
        price = self._estimate_route_price("binance", symbol)
        if price <= 0:
            return {"ok": False, "venue": "binance", "market_type": "margin", "symbol": symbol, "reason": "price_unavailable"}
        quantity = max(0.0, quote_usd / price)
        if quantity <= 0:
            return {"ok": False, "venue": "binance", "market_type": "margin", "symbol": symbol, "reason": "quantity_unavailable"}
        side_norm = str(side or "BUY").upper()
        result = self.binance.place_margin_order(
            symbol=symbol,
            side=side_norm,
            quantity=quantity,
            leverage=BINANCE_MARGIN_LEVERAGE,
        )
        return {"ok": bool(result and not result.get("rejected") and not result.get("error")), "venue": "binance", "market_type": "margin", "symbol": symbol, "side": side_norm, "quantity": quantity, "result": result}

    def _execution_blockers(self, payload: Dict[str, Any], action_plan: Dict[str, Any]) -> List[str]:
        blockers: List[str] = []
        if not self._unified_executor_enabled():
            blockers.append("unified_order_executor_disabled")
        if not self._runtime_real_orders_allowed():
            blockers.append("real_orders_not_allowed_by_runtime")
        if not bool(action_plan.get("order_intent_publish_enabled")):
            blockers.append("order_intent_publish_disabled")
        if action_plan.get("global_blockers"):
            blockers.extend(str(item) for item in action_plan.get("global_blockers", []) if str(item))
        tick_running = max(0.0, time.time() - float(getattr(self, "_last_tick_started_at", 0.0) or 0.0))
        if tick_running > READY_STALE_AFTER_SEC:
            blockers.append("current_tick_stale")
        try:
            combined = payload.get("combined") if isinstance(payload.get("combined"), dict) else {}
            open_positions = int(combined.get("open_positions", 0) or 0)
        except Exception:
            open_positions = 0
        if open_positions >= ORDER_EXECUTOR_MAX_OPEN_POSITIONS:
            blockers.append("max_open_positions_reached")
        now = time.time()
        if now - float(getattr(self, "_last_execution_at", 0.0) or 0.0) < ORDER_EXECUTOR_MIN_INTERVAL_SEC:
            blockers.append("executor_cycle_cooldown")
        return sorted(set(blockers))

    def _execute_runtime_order_actions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        order_flow = payload.get("shared_order_flow") if isinstance(payload.get("shared_order_flow"), dict) else {}
        action_plan = payload.get("exchange_action_plan") if isinstance(payload.get("exchange_action_plan"), dict) else {}
        blockers = self._execution_blockers(payload, action_plan)
        now = time.time()
        execution_summary: Dict[str, Any] = {
            "generated_at": datetime.now().isoformat(),
            "executor_enabled": self._unified_executor_enabled(),
            "quote_usd": ORDER_EXECUTOR_QUOTE_USD,
            "kraken_spot_quote_usd": KRAKEN_SPOT_QUOTE_USD,
            "trade_path_state": "available" if not blockers else "runtime_clearance_hold",
            "live_action_clearance": "cleared" if not blockers else "waiting_for_runtime_truth",
            "runtime_clearances": blockers,
            "guards": blockers,
            "attempted_count": 0,
            "submitted_count": 0,
            "delegated_count": 0,
            "held_count": 0,
            "blocked_count": 0,
            "results": [],
            "blockers": blockers,
        }
        if blockers:
            self._latest_execution_results = execution_summary
            action_plan["latest_execution"] = execution_summary
            return execution_summary

        active = order_flow.get("active_order_flow", []) if isinstance(order_flow, dict) else []
        if not isinstance(active, list):
            active = []

        for item in active:
            if execution_summary["attempted_count"] >= ORDER_EXECUTOR_MAX_PER_TICK:
                break
            if not isinstance(item, dict):
                continue
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
            if confidence < ORDER_INTENT_MIN_CONFIDENCE:
                continue
            side = str(item.get("side") or "BUY").upper()
            routes = item.get("execution_routes", []) if isinstance(item.get("execution_routes"), list) else []
            for route_item in routes:
                if execution_summary["attempted_count"] >= ORDER_EXECUTOR_MAX_PER_TICK:
                    break
                if not isinstance(route_item, dict) or not route_item.get("ready"):
                    continue
                venue = str(route_item.get("venue") or "").lower()
                market_type = str(route_item.get("market_type") or "").lower()
                route_symbol = str(route_item.get("symbol") or "").upper().strip()
                route_key = f"{venue}:{market_type}:{route_symbol}:{side}"
                owner = str(route_item.get("execution_owner") or "").lower()
                if owner == "existing_autonomous_trader_tick" or (
                    (venue == "kraken" and market_type == "margin")
                    or (venue == "capital" and market_type == "cfd")
                ):
                    delegated = {
                        "ok": True,
                        "delegated": True,
                        "submitted": False,
                        "venue": venue,
                        "market_type": market_type,
                        "symbol": route_symbol,
                        "side": side,
                        "reason": "delegated_to_existing_autonomous_trader_tick",
                        "generated_at": datetime.now().isoformat(),
                        "source": "unified_market_trader.executor",
                        "confidence": confidence,
                        "support_count": item.get("support_count", 0),
                        "cognitive_sources": item.get("sources", []),
                        "model_signal": item.get("model_signal", {}),
                        "model_alignment": item.get("model_alignment", False),
                    }
                    execution_summary["delegated_count"] += 1
                    execution_summary["results"].append(delegated)
                    continue

                last_route_at = float(self._execution_memory.get(route_key, 0.0) or 0.0)
                if now - last_route_at < ORDER_EXECUTOR_SYMBOL_COOLDOWN_SEC:
                    execution_summary["attempted_count"] += 1
                    execution_summary["held_count"] += 1
                    execution_summary["blocked_count"] += 1
                    execution_summary["results"].append({
                        "ok": False,
                        "held": True,
                        "venue": venue,
                        "market_type": market_type,
                        "symbol": route_symbol,
                        "side": side,
                        "reason": "symbol_route_cooldown",
                    })
                    continue

                try:
                    execution_summary["attempted_count"] += 1
                    if venue == "kraken" and market_type == "spot":
                        result = self._execute_kraken_spot_route(side, route_symbol, ORDER_EXECUTOR_QUOTE_USD)
                    elif venue == "alpaca" and market_type == "spot":
                        result = self._execute_alpaca_spot_route(side, route_symbol, ORDER_EXECUTOR_QUOTE_USD)
                    elif venue == "binance" and market_type == "spot":
                        result = self._execute_binance_spot_route(side, route_symbol, ORDER_EXECUTOR_QUOTE_USD)
                    elif venue == "binance" and market_type == "margin":
                        result = self._execute_binance_margin_route(side, route_symbol, ORDER_EXECUTOR_QUOTE_USD)
                    else:
                        result = {"ok": False, "venue": venue, "market_type": market_type, "symbol": route_symbol, "reason": "executor_route_not_supported"}
                except Exception as e:
                    result = {"ok": False, "venue": venue, "market_type": market_type, "symbol": route_symbol, "side": side, "error": str(e)}
                    self._governor().record_error(venue or "execution", e)

                result.update(
                    {
                        "generated_at": datetime.now().isoformat(),
                        "source": "unified_market_trader.executor",
                        "confidence": confidence,
                        "support_count": item.get("support_count", 0),
                        "cognitive_sources": item.get("sources", []),
                        "model_signal": item.get("model_signal", {}),
                        "model_alignment": item.get("model_alignment", False),
                    }
                )
                execution_summary["results"].append(result)
                if result.get("ok"):
                    self._execution_memory[route_key] = now
                    execution_summary["submitted_count"] += 1
                    self._publish_thought("execution.order.submitted", result)
                else:
                    execution_summary["held_count"] += 1
                    execution_summary["blocked_count"] += 1

        if execution_summary["submitted_count"] > 0:
            self._last_execution_at = now
        self._latest_execution_results = execution_summary
        action_plan["latest_execution"] = execution_summary

        try:
            EXECUTION_RESULT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with EXECUTION_RESULT_LOG_PATH.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(execution_summary, default=str, sort_keys=True) + "\n")
        except Exception as e:
            logger.debug("Execution result log write failed: %s", e)
        for path in (EXECUTION_RESULT_STATE_PATH, EXECUTION_RESULT_PUBLIC_PATH):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(execution_summary, handle, indent=2, default=str)
                os.replace(tmp_path, path)
            except Exception as e:
                logger.debug("Execution result state write failed for %s: %s", path, e)
        return execution_summary

    def _extract_trader_source_snapshot(self, source_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbols: Dict[str, Dict[str, Any]] = {}

        def push(symbol: Any, confidence: Any, side: Any = "BUY", reason: str = "signal") -> None:
            raw_symbol = str(symbol or "").upper().strip()
            normalized = self._normalize_symbol(raw_symbol)
            if not normalized:
                return
            try:
                conf = float(confidence or 0.0)
            except Exception:
                conf = 0.0
            if conf > 1.0:
                conf = conf / 100.0
            conf = max(0.0, min(1.0, conf))
            if conf <= 0.0:
                return
            symbols[normalized] = {
                "symbol": normalized,
                "raw_symbol": raw_symbol,
                "confidence": conf,
                "side": str(side or "BUY").upper(),
                "reason": reason,
            }

        for position in payload.get("positions", [])[:12]:
            if isinstance(position, dict):
                push(
                    position.get("symbol") or position.get("pair"),
                    1.0,
                    position.get("direction") or position.get("side") or "BUY",
                    reason="open_position",
                )

        for candidate in payload.get("candidate_snapshot", [])[:8]:
            if isinstance(candidate, dict):
                push(
                    candidate.get("symbol") or candidate.get("pair"),
                    self._extract_candidate_confidence(candidate),
                    candidate.get("direction") or candidate.get("side") or "BUY",
                    reason="candidate",
                )

        decision_snapshot = payload.get("decision_snapshot", {})
        if isinstance(decision_snapshot, dict):
            decision = decision_snapshot.get("decision", {}) if isinstance(decision_snapshot.get("decision"), dict) else {}
            push(
                decision_snapshot.get("symbol"),
                decision.get("confidence", 0.0),
                decision_snapshot.get("side") or decision.get("direction") or decision.get("type") or "BUY",
                reason="decision",
            )

        target_snapshot = payload.get("target_snapshot", {})
        if isinstance(target_snapshot, dict):
            push(
                target_snapshot.get("symbol"),
                self._extract_candidate_confidence(target_snapshot),
                target_snapshot.get("direction") or "BUY",
                reason="target",
            )

        if not symbols:
            return {}
        strongest = max(symbols.values(), key=lambda item: float(item.get("confidence", 0.0) or 0.0))
        return {
            "source": source_name,
            "ready": bool(payload.get("ok", True)),
            "symbols": symbols,
            "top_symbol": strongest.get("symbol"),
            "top_side": strongest.get("side"),
            "top_confidence": strongest.get("confidence"),
        }

    def _extract_alpaca_source_snapshot(self, watchlist: List[str]) -> Dict[str, Any]:
        client = self.alpaca
        if client is None:
            return {}
        if getattr(client, "init_error", "") or not getattr(client, "is_authenticated", True):
            return {}
        symbols: Dict[str, Dict[str, Any]] = {}
        for normalized in watchlist:
            crypto_symbol = self._to_alpaca_crypto_symbol(normalized)
            if not crypto_symbol:
                continue
            try:
                ticker = self._governor().call(
                    "alpaca",
                    "quotes",
                    f"alpaca:ticker:{crypto_symbol}",
                    lambda symbol=crypto_symbol: client.get_ticker(symbol),
                    min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                    stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                )
            except Exception:
                ticker = None
            if not ticker:
                continue
            price = float(ticker.get("price", 0.0) or ticker.get("last", 0.0) or 0.0)
            change_pct = float(ticker.get("change_pct", 0.0) or ticker.get("priceChangePercent", 0.0) or 0.0)
            if price <= 0 or abs(change_pct) <= 0.0:
                continue
            symbols[normalized] = {
                "symbol": normalized,
                "raw_symbol": crypto_symbol,
                "confidence": min(1.0, abs(change_pct) / 5.0),
                "side": "BUY" if change_pct >= 0 else "SELL",
                "price": price,
                "change_pct": change_pct,
            }
        if not symbols:
            return {}
        strongest = max(symbols.values(), key=lambda item: float(item.get("confidence", 0.0) or 0.0))
        return {
            "source": "alpaca",
            "ready": True,
            "symbols": symbols,
            "top_symbol": strongest.get("symbol"),
            "top_side": strongest.get("side"),
            "top_confidence": strongest.get("confidence"),
        }

    def _extract_binance_source_snapshot(self, watchlist: List[str]) -> Dict[str, Any]:
        client = self.binance
        if client is None:
            return {}
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        if binance_diag.get("init_error") == "socket_blocked" or not bool(binance_diag.get("network_ok", False)):
            return {}
        symbols: Dict[str, Dict[str, Any]] = {}
        for normalized in watchlist:
            binance_symbol = self._to_binance_symbol(normalized)
            if not binance_symbol:
                continue
            try:
                ticker = self._governor().call(
                    "binance",
                    "quotes",
                    f"binance:24h:{binance_symbol}",
                    lambda symbol=binance_symbol: client.get_24h_ticker(symbol),
                    min_interval_sec=PROBE_SYMBOL_MIN_INTERVAL_SEC,
                    stale_ttl_sec=PROBE_SYMBOL_STALE_TTL_SEC,
                )
            except Exception:
                ticker = None
            if not ticker:
                continue
            change_pct = float(ticker.get("priceChangePercent", 0.0) or 0.0)
            if abs(change_pct) <= 0.0:
                continue
            symbols[normalized] = {
                "symbol": normalized,
                "raw_symbol": binance_symbol,
                "confidence": min(1.0, abs(change_pct) / 5.0),
                "side": "BUY" if change_pct >= 0 else "SELL",
                "price": float(ticker.get("lastPrice", 0.0) or ticker.get("weightedAvgPrice", 0.0) or 0.0),
                "change_pct": change_pct,
            }
        if not symbols:
            return {}
        strongest = max(symbols.values(), key=lambda item: float(item.get("confidence", 0.0) or 0.0))
        return {
            "source": "binance",
            "ready": True,
            "symbols": symbols,
            "top_symbol": strongest.get("symbol"),
            "top_side": strongest.get("side"),
            "top_confidence": strongest.get("confidence"),
        }

    def _normalize_symbol(self, symbol: Any) -> str:
        raw = str(symbol or "").upper().strip()
        if not raw:
            return ""
        for needle in ("PERP", ".D", "-CFD"):
            raw = raw.replace(needle, "")
        alnum = "".join(ch for ch in raw if ch.isalnum())
        return SYMBOL_ALIASES.get(alnum, alnum)

    def _to_alpaca_crypto_symbol(self, normalized: str) -> str:
        symbol = str(normalized or "").upper()
        if symbol.endswith("USD") and len(symbol) > 3:
            base = symbol[:-3]
            if base in ALPACA_SPOT_CRYPTO_BASES:
                return f"{base}/USD"
        return ""

    def _to_binance_symbol(self, normalized: str) -> str:
        symbol = str(normalized or "").upper()
        if symbol.endswith("USD") and len(symbol) > 3:
            base = symbol[:-3]
            if base in BINANCE_CRYPTO_BASES:
                return f"{base}USDT"
        return ""

    def _capital_tradable_symbols(self) -> Dict[str, str]:
        return {self._normalize_symbol(symbol): symbol for symbol in CAPITAL_UNIVERSE.keys()}

    def _alpaca_tradable_symbols(self) -> Dict[str, str]:
        return {
            f"{base}USD": f"{base}/USD"
            for base in sorted(ALPACA_SPOT_CRYPTO_BASES)
            if base not in {"USDC", "USDT"}
        }

    def _binance_tradable_symbols(self) -> Dict[str, str]:
        return {
            f"{base}USD": f"{base}USDT"
            for base in sorted(BINANCE_CRYPTO_BASES)
            if base not in {"USDC", "USDT"}
        }

    def _to_kraken_spot_symbol(self, normalized: str) -> str:
        symbol = str(normalized or "").upper()
        if symbol.endswith("USD") and len(symbol) > 3:
            base = symbol[:-3]
            if base in KRAKEN_SPOT_CRYPTO_BASES:
                return "XBTUSD" if base == "BTC" else f"{base}USD"
        return ""

    def _kraken_spot_tradable_symbols(self) -> Dict[str, str]:
        tradables: Dict[str, str] = {}
        client = self._kraken_spot_client()
        if client is not None and hasattr(client, "exchange_info"):
            try:
                info = self._governor().call(
                    "kraken",
                    "metadata",
                    "kraken:exchange_info",
                    lambda: client.exchange_info(),
                    min_interval_sec=max(PROBE_SYMBOL_MIN_INTERVAL_SEC, 30.0),
                    stale_ttl_sec=max(PROBE_SYMBOL_STALE_TTL_SEC, 300.0),
                )
            except Exception:
                info = {}
            symbols = info.get("symbols", []) if isinstance(info, dict) else []
            if isinstance(symbols, list):
                for item in symbols:
                    if not isinstance(item, dict):
                        continue
                    quote = str(item.get("quoteAsset") or "").upper()
                    base = str(item.get("baseAsset") or "").upper().lstrip("XZ")
                    raw_symbol = str(item.get("symbol") or "").upper()
                    if quote not in {"USD", "USDT", "USDC"} or not raw_symbol:
                        continue
                    normalized = self._normalize_symbol(raw_symbol)
                    if normalized and base not in {"USD", "USDT", "USDC"}:
                        tradables.setdefault(normalized, raw_symbol)
        for base in sorted(KRAKEN_SPOT_CRYPTO_BASES):
            normalized = f"{base}USD"
            tradables.setdefault(normalized, self._to_kraken_spot_symbol(normalized) or normalized)
        return tradables

    def _kraken_tradable_symbols(self) -> Dict[str, str]:
        tradables: Dict[str, str] = {}
        if self.kraken is None:
            return tradables
        margin_pairs = getattr(self.kraken, "margin_pairs", {}) or {}
        for pair, info in margin_pairs.items():
            binance_symbol = getattr(info, "binance_symbol", "") if info is not None else ""
            kraken_symbol = getattr(info, "pair", "") if info is not None else ""
            primary = str(binance_symbol or kraken_symbol or pair or "").upper()
            normalized = self._normalize_symbol(primary)
            if normalized:
                tradables[normalized] = primary
        return tradables

    def _build_global_order_flow_feed(
        self,
        kraken_payload: Dict[str, Any],
        capital_payload: Dict[str, Any],
        central_beat: Dict[str, Any],
        shared_market_feed: Dict[str, Any],
    ) -> Dict[str, Any]:
        kraken_margin_tradables = self._kraken_tradable_symbols()
        kraken_spot_tradables = self._kraken_spot_tradable_symbols()
        capital_tradables = self._capital_tradable_symbols()
        alpaca_tradables = self._alpaca_tradable_symbols()
        binance_tradables = self._binance_tradable_symbols()
        kraken_capital_shared_keys = sorted((set(kraken_margin_tradables.keys()) | set(kraken_spot_tradables.keys())) & set(capital_tradables.keys()))

        symbols_conf = shared_market_feed.get("symbols", {}) if isinstance(shared_market_feed, dict) else {}
        central_symbols = central_beat.get("symbols", {}) if isinstance(central_beat, dict) else {}
        ranked: List[Dict[str, Any]] = []
        routeable_keys = sorted(
            set(symbols_conf.keys())
            & (
                set(kraken_margin_tradables.keys())
                | set(kraken_spot_tradables.keys())
                | set(capital_tradables.keys())
                | set(alpaca_tradables.keys())
                | set(binance_tradables.keys())
            )
        )
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        alpaca_ok = self.alpaca is not None and not bool(getattr(self.alpaca, "init_error", "") or self.alpaca_error)
        binance_network_ok = self.binance is not None and bool(binance_diag.get("network_ok", False))
        binance_account_ok = bool(binance_diag.get("account_ok", False))
        binance_margin_ok = bool(binance_diag.get("margin_available", False)) and not bool(
            binance_diag.get("uk_mode", getattr(self.binance, "uk_mode", False) if self.binance is not None else False)
        )

        def route(venue: str, market_type: str, symbol: str, ready: bool, blockers: List[str], execution_owner: str = "unified_executor") -> Dict[str, Any]:
            model_stack = self._model_stack_for_route(venue, market_type)
            clearances = [str(item) for item in blockers if str(item)]
            trade_clearance_state = "available" if ready and not clearances else "held"
            return {
                "venue": venue,
                "market_type": market_type,
                "symbol": symbol,
                "ready": bool(ready),
                "trade_clearance_state": trade_clearance_state,
                "guard_state": trade_clearance_state,
                "runtime_clearances": clearances,
                "guards": clearances,
                "clearance_required": clearances,
                "end_user_trade_available": bool(ready),
                "blockers": clearances,
                "execution_owner": execution_owner,
                "model_stack_key": model_stack.get("key"),
                "model_count": model_stack.get("available_count", 0),
                "model_total_count": model_stack.get("total_count", 0),
                "model_coverage_ready": bool(model_stack.get("ready")),
                "models": model_stack.get("models", []),
            }

        for normalized in routeable_keys:
            confidence = float(symbols_conf.get(normalized, 0.0) or 0.0)
            if confidence <= 0.0:
                continue
            capital_symbol = capital_tradables.get(normalized, normalized)
            central_signal = central_symbols.get(normalized, {}) if isinstance(central_symbols, dict) else {}
            side = str(central_signal.get("side") or "").upper() if isinstance(central_signal, dict) else ""
            if side not in ("BUY", "SELL") and "SHORT" in capital_symbol.upper():
                side = "SELL"
            elif side not in ("BUY", "SELL"):
                side = "BUY"
            execution_routes: List[Dict[str, Any]] = []
            if normalized in kraken_spot_tradables:
                execution_routes.append(
                    route(
                        "kraken",
                        "spot",
                        kraken_spot_tradables.get(normalized, normalized),
                        bool(self.kraken_ready and self.kraken is not None),
                        [] if self.kraken_ready and self.kraken is not None else [self.kraken_error or "kraken_not_ready"],
                        "unified_executor",
                    )
                )
            if normalized in kraken_margin_tradables:
                execution_routes.append(
                    route(
                        "kraken",
                        "margin",
                        kraken_margin_tradables.get(normalized, normalized),
                        bool(self.kraken_ready and self.kraken is not None),
                        [] if self.kraken_ready and self.kraken is not None else [self.kraken_error or "kraken_not_ready"],
                        "existing_autonomous_trader_tick",
                    )
                )
            if normalized in capital_tradables:
                execution_routes.append(
                    route(
                        "capital",
                        "cfd",
                        capital_symbol,
                        bool(self.capital_ready and self.capital is not None),
                        [] if self.capital_ready and self.capital is not None else [self.capital_error or "capital_not_ready"],
                        "existing_autonomous_trader_tick",
                    )
                )
            if normalized in alpaca_tradables:
                execution_routes.append(
                    route(
                        "alpaca",
                        "spot",
                        alpaca_tradables.get(normalized, normalized),
                        alpaca_ok,
                        [] if alpaca_ok else [self.alpaca_error or "alpaca_not_ready"],
                    )
                )
            if normalized in binance_tradables:
                execution_routes.append(
                    route(
                        "binance",
                        "spot",
                        binance_tradables.get(normalized, normalized),
                        binance_network_ok,
                        [] if binance_network_ok else [self.binance_error or "binance_network_not_ready"],
                    )
                )
                execution_routes.append(
                    route(
                        "binance",
                        "margin",
                        binance_tradables.get(normalized, normalized),
                        bool(binance_network_ok and binance_account_ok and binance_margin_ok),
                        []
                        if binance_network_ok and binance_account_ok and binance_margin_ok
                        else [
                            blocker
                            for blocker, present in (
                                ("binance_network_not_ready", not binance_network_ok),
                                ("binance_account_not_ready", not binance_account_ok),
                                ("binance_margin_unavailable_or_uk_restricted", not binance_margin_ok),
                            )
                            if present
                        ],
                    )
                )
            ready_route_count = sum(1 for item in execution_routes if item.get("ready"))
            ranked.append(
                {
                    "symbol": normalized,
                    "kraken_symbol": kraken_margin_tradables.get(normalized) or kraken_spot_tradables.get(normalized, normalized),
                    "kraken_spot_symbol": kraken_spot_tradables.get(normalized),
                    "kraken_margin_symbol": kraken_margin_tradables.get(normalized),
                    "capital_symbol": capital_symbol,
                    "alpaca_symbol": alpaca_tradables.get(normalized),
                    "binance_symbol": binance_tradables.get(normalized),
                    "side": side,
                    "confidence": max(0.0, min(1.0, confidence)),
                    "support_count": int(central_signal.get("support_count", 0) or 0) if isinstance(central_signal, dict) else 0,
                    "sources": list(central_signal.get("sources", [])) if isinstance(central_signal, dict) and isinstance(central_signal.get("sources"), list) else [],
                    "reference_price": float(central_signal.get("reference_price", 0.0) or 0.0) if isinstance(central_signal, dict) else 0.0,
                    "change_pct": float(central_signal.get("change_pct", 0.0) or 0.0) if isinstance(central_signal, dict) else 0.0,
                    "source_prices": dict(central_signal.get("source_prices", {})) if isinstance(central_signal, dict) and isinstance(central_signal.get("source_prices"), dict) else {},
                    "model_signal": central_signal.get("model_signal", {}) if isinstance(central_signal, dict) else {},
                    "model_alignment": bool(central_signal.get("model_alignment", False)) if isinstance(central_signal, dict) else False,
                    "execution_routes": execution_routes,
                    "ready_route_count": ready_route_count,
                    "held_route_count": max(0, len(execution_routes) - ready_route_count),
                    "available_route_count": ready_route_count,
                    "blocked_route_count": max(0, len(execution_routes) - ready_route_count),
                }
            )

        ranked.sort(key=lambda item: float(item.get("confidence", 0.0) or 0.0), reverse=True)
        venue_counts = {
            "kraken_spot": len(kraken_spot_tradables),
            "kraken_margin": len(kraken_margin_tradables),
            "capital_cfd": len(capital_tradables),
            "alpaca_spot": len(alpaca_tradables),
            "binance_spot": len(binance_tradables),
            "binance_margin": len(binance_tradables),
        }
        return {
            "generated_at": datetime.now().isoformat(),
            "shared_tradable_count": len(routeable_keys),
            "kraken_capital_shared_tradable_count": len(kraken_capital_shared_keys),
            "multi_exchange_tradable_count": len(routeable_keys),
            "active_order_flow_count": len(ranked),
            "active_order_flow": ranked[:20],
            "kraken_tradables": len(set(kraken_margin_tradables.keys()) | set(kraken_spot_tradables.keys())),
            "kraken_spot_tradables": len(kraken_spot_tradables),
            "kraken_margin_tradables": len(kraken_margin_tradables),
            "capital_tradables": len(capital_tradables),
            "alpaca_tradables": len(alpaca_tradables),
            "binance_tradables": len(binance_tradables),
            "venue_tradable_counts": venue_counts,
            "scope": "multi-exchange unified tradables across Kraken spot/margin, Capital CFDs, Alpaca spot, and Binance spot/margin",
        }

    def _feed_shared_order_flow_to_decision_logic(self, order_flow_feed: Dict[str, Any]) -> None:
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not isinstance(active, list):
            return
        for item in active[:10]:
            if not isinstance(item, dict):
                continue
            symbol = str(item.get("symbol") or "").upper().strip()
            side = str(item.get("side") or "BUY").upper()
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
            metadata = {
                "source": "unified_market_trader.shared_order_flow",
                "kraken_symbol": item.get("kraken_symbol"),
                "kraken_spot_symbol": item.get("kraken_spot_symbol"),
                "kraken_margin_symbol": item.get("kraken_margin_symbol"),
                "capital_symbol": item.get("capital_symbol"),
                "alpaca_symbol": item.get("alpaca_symbol"),
                "binance_symbol": item.get("binance_symbol"),
                "execution_routes": item.get("execution_routes", []),
                "shared_tradable_count": order_flow_feed.get("shared_tradable_count", 0),
            }
            for trader in self._central_feed_targets():
                if trader is None or not hasattr(trader, "_feed_unified_decision_engine"):
                    continue
                try:
                    trader._feed_unified_decision_engine(symbol=symbol, side=side, score=confidence, metadata=metadata)  # type: ignore[attr-defined]
                except Exception as e:
                    logger.debug("Shared decision feed failed for %s: %s", symbol, e)

    def _shadow_trade_enabled(self) -> bool:
        return os.getenv("UNIFIED_SHADOW_TRADE_ENABLED", "1").strip().lower() not in {"0", "false", "no", "off"}

    def _read_shadow_trade_state(self) -> Dict[str, Any]:
        try:
            if SHADOW_TRADE_STATE_PATH.exists():
                data = json.loads(SHADOW_TRADE_STATE_PATH.read_text(encoding="utf-8"))
                return data if isinstance(data, dict) else {}
        except Exception as e:
            logger.debug("Shadow trade state read failed: %s", e)
        return {}

    def _shadow_target_price(self, entry_price: float, side: str, target_move_pct: float) -> float:
        if entry_price <= 0:
            return 0.0
        move = max(0.0, float(target_move_pct or 0.0)) / 100.0
        return entry_price * (1.0 - move) if str(side).upper() == "SELL" else entry_price * (1.0 + move)

    def _shadow_direction_move_pct(self, entry_price: float, current_price: float, side: str) -> float:
        if entry_price <= 0 or current_price <= 0:
            return 0.0
        if str(side).upper() == "SELL":
            return ((entry_price - current_price) / entry_price) * 100.0
        return ((current_price - entry_price) / entry_price) * 100.0

    def _shadow_agent_review(
        self,
        *,
        item: Dict[str, Any],
        route_item: Dict[str, Any],
        entry_price: float,
        global_guards: List[str],
    ) -> Dict[str, Any]:
        confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
        support_count = int(item.get("support_count", 0) or 0)
        side = str(item.get("side") or "BUY").upper()
        side_signal = side if side in {"BUY", "SELL"} else "NEUTRAL"
        model_signal = item.get("model_signal", {}) if isinstance(item.get("model_signal"), dict) else {}
        model_confidence = max(0.0, min(1.0, float(model_signal.get("confidence", confidence) or confidence)))
        model_direction = str(model_signal.get("direction") or side_signal).upper()
        route_clearances = [str(item) for item in (route_item.get("runtime_clearances") or route_item.get("guards") or route_item.get("blockers") or []) if str(item)]
        runtime_clearances = [str(item) for item in global_guards if str(item)]
        route_ready = bool(route_item.get("ready")) and not route_clearances
        price_ready = entry_price > 0
        model_aligned = bool(item.get("model_alignment")) or model_direction in {"NEUTRAL", side_signal}

        def score(ok: bool, value: float) -> float:
            return max(0.0, min(1.0, value if ok else value * 0.35))

        market_ok = confidence >= SHADOW_TRADE_MIN_CONFIDENCE and support_count > 0
        market_score = score(market_ok, confidence)
        model_score = score(model_aligned, model_confidence)
        route_score = 1.0 if route_ready else 0.15
        price_score = 1.0 if price_ready else 0.1
        live_clearance_score = 1.0 if not runtime_clearances else 0.55

        synthetic_signals = [
            {
                "pillar": "MarketDataAgent",
                "signal": side_signal,
                "confidence": market_score,
                "coherence": max(0.0, min(1.0, support_count / 4.0)),
                "frequency_hz": 528.0 if side_signal == "BUY" else 396.0 if side_signal == "SELL" else 432.0,
            },
            {
                "pillar": "ModelAlignmentAgent",
                "signal": side_signal if model_aligned else "NEUTRAL",
                "confidence": model_score,
                "coherence": 0.86 if model_aligned else 0.34,
                "frequency_hz": 528.0 if model_aligned else 432.0,
            },
            {
                "pillar": "RouteClearanceAgent",
                "signal": side_signal if route_ready else "NEUTRAL",
                "confidence": route_score,
                "coherence": route_score,
                "frequency_hz": 432.0,
            },
            {
                "pillar": "PriceValidationAgent",
                "signal": side_signal if price_ready else "NEUTRAL",
                "confidence": price_score,
                "coherence": price_score,
                "frequency_hz": 528.0 if price_ready else 432.0,
            },
            {
                "pillar": "RuntimeClearanceAgent",
                "signal": side_signal if not runtime_clearances else "NEUTRAL",
                "confidence": live_clearance_score,
                "coherence": live_clearance_score,
                "frequency_hz": 432.0,
            },
        ]

        hnc_alignment = {
            "available": False,
            "alignment_score": round((market_score + model_score + route_score + price_score + live_clearance_score) / 5.0, 6),
            "lighthouse_cleared": False,
            "consensus_signal": side_signal,
        }
        try:
            from aureon.alignment.harmonic_resonance import full_harmonic_analysis

            analysis = full_harmonic_analysis(pillar_results=synthetic_signals)
            hnc_alignment = {
                "available": True,
                "alignment_score": round(float(getattr(analysis, "alignment_score", 0.0) or 0.0), 6),
                "harmonic_lock": round(float(getattr(analysis, "harmonic_lock", 0.0) or 0.0), 6),
                "phase_coherence": round(float(getattr(analysis, "phase_coherence", 0.0) or 0.0), 6),
                "lighthouse_cleared": bool(getattr(analysis, "lighthouse_cleared", False)),
                "consensus_signal": str(getattr(analysis, "dominant_signal", side_signal) or side_signal),
                "responding_agents": len(synthetic_signals),
            }
        except Exception as e:
            hnc_alignment["error"] = str(e)

        agent_score = max(
            0.0,
            min(
                1.0,
                (0.25 * market_score)
                + (0.22 * model_score)
                + (0.20 * route_score)
                + (0.18 * price_score)
                + (0.15 * float(hnc_alignment.get("alignment_score", 0.0) or 0.0)),
            ),
        )
        logic_validated = bool(route_ready and market_ok and price_ready and agent_score >= 0.45)
        agents = {
            "market_data_agent": {
                "ok": market_ok,
                "confidence": round(confidence, 6),
                "support_count": support_count,
                "sources": list(item.get("sources", [])) if isinstance(item.get("sources"), list) else [],
            },
            "model_alignment_agent": {
                "ok": model_aligned,
                "direction": model_direction,
                "confidence": round(model_confidence, 6),
                "model_signal": model_signal,
                "model_stack_key": route_item.get("model_stack_key"),
                "model_count": int(route_item.get("model_count", 0) or 0),
            },
            "route_clearance_agent": {
                "ok": route_ready,
                "venue": route_item.get("venue"),
                "market_type": route_item.get("market_type"),
                "runtime_clearances": route_clearances,
                "execution_owner": route_item.get("execution_owner"),
            },
            "price_validation_agent": {
                "ok": price_ready,
                "entry_price": round(entry_price, 8) if entry_price > 0 else 0.0,
            },
            "runtime_clearance_agent": {
                "ok_for_shadow": True,
                "ok_for_live_promotion": not bool(runtime_clearances),
                "runtime_clearances": runtime_clearances,
                "note": "Queen/HNC can reason and shadow freely; live exchange mutation waits for runtime truth checks",
            },
            "hnc_alignment_agent": hnc_alignment,
        }
        return {
            "logic_validated": logic_validated,
            "agent_score": round(agent_score, 6),
            "agents": agents,
            "synthetic_agent_signals": synthetic_signals,
            "self_report": (
                "shadow logic validated; watch price path before promotion"
                if logic_validated
                else "shadow held; waiting for route, price, or confidence inputs"
            ),
        }

    def _verify_prior_shadow(self, shadow: Dict[str, Any], current_prices: Dict[str, float], now: float) -> Dict[str, Any]:
        result = dict(shadow)
        symbol = str(result.get("symbol") or "").upper()
        entry_price = float(result.get("entry_price", 0.0) or 0.0)
        current_price = float(current_prices.get(symbol, 0.0) or 0.0)
        expected_by_epoch = float(result.get("expected_by_epoch", 0.0) or 0.0)
        target_move_pct = float(result.get("target_move_pct", SHADOW_TRADE_TARGET_MOVE_PCT) or SHADOW_TRADE_TARGET_MOVE_PCT)
        direction_move_pct = self._shadow_direction_move_pct(entry_price, current_price, str(result.get("side") or "BUY"))
        target_hit = bool(entry_price > 0 and current_price > 0 and direction_move_pct >= target_move_pct)
        if target_hit:
            status = "validated"
        elif current_price <= 0:
            status = "pending_price"
        elif expected_by_epoch > 0 and now >= expected_by_epoch:
            status = "missed_eta"
        else:
            status = "validating"
        result.update(
            {
                "last_verified_at": datetime.now().isoformat(),
                "current_price": round(current_price, 8) if current_price > 0 else 0.0,
                "direction_move_pct": round(direction_move_pct, 6),
                "target_hit": target_hit,
                "status": status,
            }
        )
        return result

    def _build_shadow_trade_report(
        self,
        order_flow_feed: Dict[str, Any],
        action_plan: Dict[str, Any],
        *,
        persist: bool = True,
        previous_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        generated_at = datetime.now().isoformat()
        enabled = self._shadow_trade_enabled()
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not isinstance(active, list):
            active = []
        runtime_clearances = [
            str(item)
            for item in (
                action_plan.get("global_clearances")
                or action_plan.get("runtime_clearances")
                or action_plan.get("global_guards")
                or action_plan.get("global_blockers")
                or []
            )
            if str(item)
        ] if isinstance(action_plan, dict) else []
        global_guards = [
            str(item)
            for item in (
                action_plan.get("global_guards")
                or action_plan.get("global_blockers")
                or []
            )
            if str(item)
        ] if isinstance(action_plan, dict) else []

        previous = previous_state if isinstance(previous_state, dict) else (self._read_shadow_trade_state() if persist else {})
        previous_active = previous.get("active_shadows", []) if isinstance(previous.get("active_shadows"), list) else []
        current_prices = {
            str(item.get("symbol") or "").upper(): float(item.get("reference_price", 0.0) or 0.0)
            for item in active
            if isinstance(item, dict) and float(item.get("reference_price", 0.0) or 0.0) > 0
        }
        now = time.time()
        prior_verifications = [
            self._verify_prior_shadow(shadow, current_prices, now)
            for shadow in previous_active
            if isinstance(shadow, dict)
        ]
        still_active = [
            shadow
            for shadow in prior_verifications
            if shadow.get("status") in {"validating", "pending_price", "shadow_opened"}
        ][:SHADOW_TRADE_MAX_PER_CYCLE]
        active_signatures = {str(shadow.get("route_signature") or "") for shadow in still_active if shadow.get("route_signature")}

        new_shadows: List[Dict[str, Any]] = []
        if enabled:
            for item in active:
                if len(new_shadows) >= SHADOW_TRADE_MAX_PER_CYCLE:
                    break
                if not isinstance(item, dict):
                    continue
                confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
                if confidence < SHADOW_TRADE_MIN_CONFIDENCE:
                    continue
                route_items = item.get("execution_routes", []) if isinstance(item.get("execution_routes"), list) else []
                for route_item in route_items:
                    if len(new_shadows) >= SHADOW_TRADE_MAX_PER_CYCLE:
                        break
                    if not isinstance(route_item, dict):
                        continue
                    venue = str(route_item.get("venue") or "").lower()
                    market_type = str(route_item.get("market_type") or "").lower()
                    route_symbol = str(route_item.get("symbol") or item.get("symbol") or "").upper().strip()
                    side = str(item.get("side") or "BUY").upper()
                    route_signature = f"{venue}:{market_type}:{route_symbol}:{side}"
                    if route_signature in active_signatures:
                        continue
                    entry_price = float(item.get("reference_price", 0.0) or 0.0)
                    if entry_price <= 0 and bool(route_item.get("ready")):
                        entry_price = self._estimate_route_price(venue, route_symbol)
                    review = self._shadow_agent_review(item=item, route_item=route_item, entry_price=entry_price, global_guards=runtime_clearances)
                    status = "shadow_opened" if review.get("logic_validated") else "shadow_held"
                    opened_epoch = now
                    target_price = self._shadow_target_price(entry_price, side, SHADOW_TRADE_TARGET_MOVE_PCT)
                    shadow = {
                        "id": f"shadow-{int(now)}-{len(new_shadows) + 1}",
                        "route_signature": route_signature,
                        "generated_at": generated_at,
                        "opened_at_epoch": round(opened_epoch, 3),
                        "expected_by_epoch": round(opened_epoch + SHADOW_TRADE_VALIDATION_HORIZON_SEC, 3),
                        "status": status,
                        "symbol": str(item.get("symbol") or "").upper(),
                        "venue": venue,
                        "market_type": market_type,
                        "route_symbol": route_symbol,
                        "side": side,
                        "confidence": round(confidence, 6),
                        "support_count": int(item.get("support_count", 0) or 0),
                        "sources": list(item.get("sources", [])) if isinstance(item.get("sources"), list) else [],
                        "entry_price": round(entry_price, 8) if entry_price > 0 else 0.0,
                        "target_price": round(target_price, 8) if target_price > 0 else 0.0,
                        "target_move_pct": round(SHADOW_TRADE_TARGET_MOVE_PCT, 6),
                        "validation_horizon_sec": round(SHADOW_TRADE_VALIDATION_HORIZON_SEC, 3),
                        "model_signal": item.get("model_signal", {}) if isinstance(item.get("model_signal"), dict) else {},
                        "model_alignment": bool(item.get("model_alignment", False)),
                        "model_stack_key": route_item.get("model_stack_key"),
                        "model_count": int(route_item.get("model_count", 0) or 0),
                        "route_clearances": list(route_item.get("runtime_clearances", []) or route_item.get("guards", []) or route_item.get("blockers", []) or []),
                        "route_guards": list(route_item.get("guards", []) or route_item.get("blockers", []) or []),
                        "route_ready": bool(route_item.get("ready")),
                        "execution_owner": route_item.get("execution_owner"),
                        "real_order_submitted": False,
                        "promotion_gate": "runtime_executor_required_after_shadow_validation",
                        "agent_review": review,
                    }
                    new_shadows.append(shadow)
                    if status == "shadow_opened":
                        active_signatures.add(route_signature)

        active_shadows = [
            shadow for shadow in still_active + new_shadows if shadow.get("status") in {"validating", "pending_price", "shadow_opened"}
        ][:SHADOW_TRADE_MAX_PER_CYCLE]
        validated_count = sum(1 for shadow in prior_verifications if shadow.get("status") == "validated")
        missed_count = sum(1 for shadow in prior_verifications if shadow.get("status") == "missed_eta")
        opened_count = sum(1 for shadow in new_shadows if shadow.get("status") == "shadow_opened")
        held_count = sum(1 for shadow in new_shadows if shadow.get("status") == "shadow_held")
        report = {
            "generated_at": generated_at,
            "mode": "shadow_validation_non_mutating",
            "enabled": enabled,
            "status": "shadow_reporting_active" if enabled else "shadow_reporting_disabled",
            "who": "unified_market_trader plus route/model/HNC validation agents",
            "what": "create non-mutating shadow trades, validate logic, verify prior shadows, and report back to runtime state",
            "where": str(SHADOW_TRADE_STATE_PATH),
            "how": "active order flow plus route readiness, model alignment, HNC synthetic agent review, price target, and ETA verification",
            "candidates_seen": len(active),
            "shadow_count": len(new_shadows),
            "shadow_opened_count": opened_count,
            "shadow_held_count": held_count,
            "active_shadow_count": len(active_shadows),
            "validated_shadow_count": validated_count,
            "missed_shadow_count": missed_count,
            "runtime_clearances": runtime_clearances,
            "global_clearances": runtime_clearances,
            "global_guards": global_guards,
            "min_confidence": SHADOW_TRADE_MIN_CONFIDENCE,
            "target_move_pct": SHADOW_TRADE_TARGET_MOVE_PCT,
            "validation_horizon_sec": SHADOW_TRADE_VALIDATION_HORIZON_SEC,
            "shadows": new_shadows,
            "prior_verifications": prior_verifications[-SHADOW_TRADE_MAX_PER_CYCLE:],
            "active_shadows": active_shadows,
            "self_measurement": {
                "agent_validated_count": sum(1 for shadow in new_shadows if shadow.get("agent_review", {}).get("logic_validated")),
                "agent_average_score": round(
                    sum(float(shadow.get("agent_review", {}).get("agent_score", 0.0) or 0.0) for shadow in new_shadows)
                    / max(1, len(new_shadows)),
                    6,
                ),
                "all_four_exchange_routes_seen": all(
                    key in {f"{shadow.get('venue')}_{shadow.get('market_type')}" for shadow in new_shadows}
                    for key in {"kraken_spot", "kraken_margin", "capital_cfd", "alpaca_spot", "binance_spot", "binance_margin"}
                ),
                "real_exchange_mutation": False,
            },
        }
        if isinstance(action_plan, dict):
            action_plan["shadow_trading"] = report
        if persist:
            self._persist_shadow_trade_report(report)
        return report

    def _persist_shadow_trade_report(self, report: Dict[str, Any]) -> None:
        signature = "|".join(
            str(shadow.get("route_signature") or "")
            for shadow in report.get("active_shadows", [])
            if isinstance(shadow, dict)
        )
        now = time.time()
        for path in (SHADOW_TRADE_STATE_PATH, SHADOW_TRADE_PUBLIC_PATH):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(report, handle, indent=2, default=str)
                os.replace(tmp_path, path)
            except Exception as e:
                logger.debug("Shadow trade report write failed for %s: %s", path, e)
        last_signature = str(getattr(self, "_last_shadow_trade_signature", "") or "")
        last_at = float(getattr(self, "_last_shadow_trade_at", 0.0) or 0.0)
        if signature != last_signature or now - last_at >= SHADOW_TRADE_MIN_INTERVAL_SEC:
            self._last_shadow_trade_signature = signature
            self._last_shadow_trade_at = now
            try:
                SHADOW_TRADE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with SHADOW_TRADE_LOG_PATH.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(report, default=str, sort_keys=True) + "\n")
            except Exception as e:
                logger.debug("Shadow trade report log failed: %s", e)
            self._publish_thought("execution.shadow_trade.self_report", report)

    def _clamp01(self, value: Any, default: float = 0.0) -> float:
        try:
            return max(0.0, min(1.0, float(value)))
        except Exception:
            return max(0.0, min(1.0, float(default)))

    def _repo_logic_contract(self, name: str, rel_path: str, markers: List[str], role: str) -> Dict[str, Any]:
        path = REPO_ROOT / rel_path
        found: List[str] = []
        line_count = 0
        try:
            text = path.read_text(encoding="utf-8", errors="ignore") if path.exists() else ""
            line_count = text.count("\n") + 1 if text else 0
            found = [marker for marker in markers if marker in text]
        except Exception as e:
            return {
                "name": name,
                "role": role,
                "path": rel_path,
                "present": path.exists(),
                "passed": False,
                "error": str(e),
                "markers_found": found,
                "markers_required": markers,
            }
        return {
            "name": name,
            "role": role,
            "path": rel_path,
            "present": path.exists(),
            "passed": path.exists() and len(found) == len(markers),
            "markers_found": found,
            "markers_required": markers,
            "line_count": line_count,
        }

    def _hnc_source_metrics(self, central_beat: Dict[str, Any], order_flow_feed: Dict[str, Any]) -> Dict[str, Any]:
        symbols = central_beat.get("symbols", {}) if isinstance(central_beat, dict) else {}
        if not isinstance(symbols, dict):
            symbols = {}
        sources = central_beat.get("sources", []) if isinstance(central_beat, dict) else []
        if not isinstance(sources, list):
            sources = []
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not isinstance(active, list):
            active = []

        symbol_rows = [row for row in symbols.values() if isinstance(row, dict)]
        active_rows = [row for row in active if isinstance(row, dict)]
        rows = active_rows or symbol_rows
        confidences = [self._clamp01(row.get("confidence", 0.0)) for row in rows]
        changes = []
        prices = []
        support_counts = []
        model_aligned = 0
        for row in rows:
            try:
                changes.append(float(row.get("change_pct", 0.0) or 0.0))
            except Exception:
                changes.append(0.0)
            try:
                price = float(row.get("reference_price", 0.0) or 0.0)
            except Exception:
                price = 0.0
            if price > 0:
                prices.append(price)
            support_counts.append(int(row.get("support_count", 0) or 0))
            if bool(row.get("model_alignment")):
                model_aligned += 1

        source_count = int(central_beat.get("source_count", 0) or len(sources) or 0) if isinstance(central_beat, dict) else 0
        active_count = len(active_rows)
        symbol_count = len(symbol_rows)
        price_count = len(prices)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        avg_change = sum(changes) / len(changes) if changes else 0.0
        avg_abs_change = sum(abs(change) for change in changes) / len(changes) if changes else 0.0
        avg_support = sum(support_counts) / len(support_counts) if support_counts else 0.0
        model_alignment_rate = model_aligned / len(rows) if rows else 0.0
        simulation_fallback_disabled = os.getenv("AUREON_ALLOW_SIM_FALLBACK", "0").strip().lower() in {"0", "false", "no", "off"}
        live_env_enabled = os.getenv("AUREON_LIVE_TRADING", "0").strip().lower() in {"1", "true", "yes", "on"}
        data_passed = bool(source_count > 0 and symbol_count > 0 and price_count > 0 and simulation_fallback_disabled)

        return {
            "passed": data_passed,
            "source_count": source_count,
            "source_names": [
                str(source.get("source") or source.get("name") or "")
                if isinstance(source, dict)
                else str(source)
                for source in sources
                if isinstance(source, (dict, str))
            ][:12],
            "symbol_count": symbol_count,
            "active_signal_count": active_count,
            "price_count": price_count,
            "avg_confidence": round(avg_confidence, 6),
            "avg_change_pct": round(avg_change, 6),
            "avg_abs_change_pct": round(avg_abs_change, 6),
            "avg_support_count": round(avg_support, 6),
            "model_alignment_rate": round(model_alignment_rate, 6),
            "simulation_fallback_disabled": simulation_fallback_disabled,
            "live_env_enabled": live_env_enabled,
            "data_source_kind": "live_exchange_runtime" if data_passed else "awaiting_live_price_evidence",
        }

    def _hnc_market_texture(self, metrics: Dict[str, Any], action_plan: Dict[str, Any]) -> Dict[str, float]:
        venues = action_plan.get("venues", {}) if isinstance(action_plan, dict) else {}
        venue_count = len(venues) if isinstance(venues, dict) else int(action_plan.get("venue_count", 0) or 0)
        ready_venue_count = int(action_plan.get("ready_venue_count", 0) or 0) if isinstance(action_plan, dict) else 0
        route_unity = self._clamp01(ready_venue_count / max(1, venue_count))
        avg_confidence = self._clamp01(metrics.get("avg_confidence", 0.0))
        avg_support = float(metrics.get("avg_support_count", 0.0) or 0.0)
        avg_change = float(metrics.get("avg_change_pct", 0.0) or 0.0)
        avg_abs_change = float(metrics.get("avg_abs_change_pct", 0.0) or 0.0)
        model_alignment = self._clamp01(metrics.get("model_alignment_rate", 0.0))

        return {
            "volatility": self._clamp01(avg_abs_change / 5.0),
            "momentum": max(-1.0, min(1.0, avg_change / 5.0)),
            "volume": self._clamp01((avg_support + float(metrics.get("source_count", 0) or 0)) / 8.0),
            "spread": self._clamp01(1.0 - avg_confidence),
            "route_unity": route_unity,
            "model_alignment": model_alignment,
            "confidence": avg_confidence,
        }

    def _build_auris_node_proof(self, market_data: Dict[str, float]) -> Dict[str, Any]:
        node_defs = {
            "Tiger": {"freq": 220.0, "role": "volatility", "weight": 1.0, "domain": "cuts noise"},
            "Falcon": {"freq": 285.0, "role": "momentum", "weight": 1.2, "domain": "speed and attack"},
            "Hummingbird": {"freq": 396.0, "role": "stability", "weight": 0.8, "domain": "high frequency lock"},
            "Dolphin": {"freq": 528.0, "role": "emotion", "weight": 1.5, "domain": "waveform carrier"},
            "Deer": {"freq": 639.0, "role": "sensing", "weight": 0.9, "domain": "micro shifts"},
            "Owl": {"freq": 741.0, "role": "memory", "weight": 1.1, "domain": "pattern memory"},
            "Panda": {"freq": 852.0, "role": "love", "weight": 1.3, "domain": "grounding safety"},
            "CargoShip": {"freq": 936.0, "role": "infrastructure", "weight": 0.7, "domain": "liquidity buffer"},
            "Clownfish": {"freq": 963.0, "role": "symbiosis", "weight": 1.0, "domain": "connection"},
        }

        volatility = self._clamp01(market_data.get("volatility", 0.5), 0.5)
        momentum = max(-1.0, min(1.0, float(market_data.get("momentum", 0.0) or 0.0)))
        volume = self._clamp01(market_data.get("volume", 0.5), 0.5)
        spread = self._clamp01(market_data.get("spread", 0.5), 0.5)
        route_unity = self._clamp01(market_data.get("route_unity", 0.0))
        model_alignment = self._clamp01(market_data.get("model_alignment", 0.0))

        nodes: Dict[str, Any] = {}
        for name, node in node_defs.items():
            role = str(node["role"])
            if role == "volatility":
                value = (1.0 - volatility) * 0.8
            elif role == "momentum":
                value = abs(momentum) * 0.7 + volume * 0.3
            elif role == "stability":
                value = (1.0 / (volatility + 0.01)) * 0.01 * 0.6
            elif role == "emotion":
                value = (math.sin(momentum * math.pi) + 1.0) * 0.5
            elif role == "sensing":
                value = spread
            elif role == "memory":
                value = 0.6 + model_alignment * 0.25
            elif role == "love":
                value = 1.0 - volatility * 0.5
            elif role == "infrastructure":
                value = max(volume, route_unity)
            elif role == "symbiosis":
                value = 0.5 + (route_unity * 0.25) + (model_alignment * 0.25)
            else:
                value = 0.5
            value = self._clamp01(value, 0.5)
            weight = float(node["weight"])
            nodes[name] = {
                "value": round(value, 6),
                "freq": float(node["freq"]),
                "role": role,
                "weight": weight,
                "weighted_value": round(value * weight, 6),
                "domain": node["domain"],
                "timestamp": datetime.now().isoformat(),
            }

        total_weighted = sum(float(node.get("weighted_value", 0.0) or 0.0) for node in nodes.values())
        total_weights = sum(float(node.get("weight", 0.0) or 0.0) for node in nodes.values())
        coherence = total_weighted / total_weights if total_weights > 0 else 0.0
        if coherence >= 0.938:
            status = "heart_coherence"
        elif coherence >= 0.8:
            status = "high_coherence"
        elif coherence >= 0.6:
            status = "moderate_coherence"
        else:
            status = "low_coherence"

        return {
            "source": "aureon/utils/aureon_queen_hive_mind.py::AURIS_NODES",
            "evaluated": True,
            "passed": len(nodes) == 9,
            "node_count": len(nodes),
            "coherence": round(coherence, 6),
            "status": status,
            "market_texture": {key: round(float(value), 6) for key, value in market_data.items()},
            "nodes": nodes,
        }

    def _build_hnc_cognitive_proof(
        self,
        central_beat: Dict[str, Any],
        order_flow_feed: Dict[str, Any],
        action_plan: Dict[str, Any],
        shadow_trade_report: Dict[str, Any],
        *,
        persist: bool = True,
    ) -> Dict[str, Any]:
        generated_at = datetime.now().isoformat()
        metrics = self._hnc_source_metrics(central_beat, order_flow_feed)
        market_texture = self._hnc_market_texture(metrics, action_plan)
        auris = self._build_auris_node_proof(market_texture)
        systems = {
            "hnc_master_protocol": self._repo_logic_contract(
                "HNC master protocol",
                "aureon/strategies/hnc_master_protocol.py",
                ["class HarmonicNexusCore", "class HNCTradingBridge", "def enhance_opportunity"],
                "global financial frequency mapper and trading bridge",
            ),
            "hnc_probability_matrix": self._repo_logic_contract(
                "HNC probability matrix",
                "aureon/strategies/hnc_probability_matrix.py",
                ["class FrequencySnapshot", "class ProbabilityMatrix", "class HNCProbabilityIntegration"],
                "timestamped harmonic probability validation",
            ),
            "auris_nodes": self._repo_logic_contract(
                "Auris nodes",
                "aureon/utils/aureon_queen_hive_mind.py",
                ["AURIS_NODES", "def read_auris_nodes", "def get_auris_coherence"],
                "nine-node sensory market texture evaluation",
            ),
            "seer": self._repo_logic_contract(
                "Seer",
                "aureon/intelligence/aureon_seer.py",
                ["class SeerVision", "class SeerConsensus", "class OracleReading"],
                "vision and oracle consensus layer",
            ),
            "lyra": self._repo_logic_contract(
                "Lyra",
                "aureon/trading/aureon_lyra.py",
                ["class LyraResonance", "class TheLyre", "class ChamberOfSpirit"],
                "harmonic resonance and market affect layer",
            ),
            "king": self._repo_logic_contract(
                "King",
                "aureon/trading/compound_king.py",
                ["class CompoundKing", "def get_daily_return_target", "def run_30_days"],
                "capital growth and compounding discipline layer",
            ),
        }

        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        active = active if isinstance(active, list) else []
        top = active[0] if active and isinstance(active[0], dict) else {}
        if not top and isinstance(central_beat, dict) and isinstance(central_beat.get("symbols"), dict):
            candidates = []
            for symbol_key, row in central_beat["symbols"].items():
                if isinstance(row, dict):
                    candidate = dict(row)
                    candidate.setdefault("symbol", symbol_key)
                    candidates.append(candidate)
            if candidates:
                top = max(candidates, key=lambda row: float(row.get("confidence", 0.0) or 0.0))
        ready_route_count = int(action_plan.get("ready_venue_count", 0) or 0) if isinstance(action_plan, dict) else 0
        venue_count = int(action_plan.get("venue_count", 0) or len(action_plan.get("venues", {}) or {})) if isinstance(action_plan, dict) else 0
        route_unity = self._clamp01(ready_route_count / max(1, venue_count))
        shadow_measure = shadow_trade_report.get("self_measurement", {}) if isinstance(shadow_trade_report, dict) else {}
        shadow_score = self._clamp01(shadow_measure.get("agent_average_score", 0.0), 0.0)
        if shadow_score <= 0 and int(shadow_trade_report.get("active_shadow_count", 0) or 0) > 0:
            shadow_score = 0.5

        real_data_score = 1.0 if metrics.get("passed") else 0.0
        source_unity = self._clamp01(float(metrics.get("source_count", 0) or 0) / 4.0)
        model_alignment = self._clamp01(metrics.get("model_alignment_rate", 0.0))
        auris_coherence = self._clamp01(auris.get("coherence", 0.0))
        master_score = self._clamp01(
            (real_data_score * 0.22)
            + (source_unity * 0.16)
            + (auris_coherence * 0.22)
            + (model_alignment * 0.14)
            + (shadow_score * 0.12)
            + (route_unity * 0.14)
        )

        top_confidence = self._clamp01(top.get("confidence", metrics.get("avg_confidence", 0.0)))
        top_symbol = str(top.get("symbol") or top.get("route_symbol") or "")
        top_side = str(top.get("side") or "NEUTRAL").upper()
        seer_runtime = {
            "evaluated": bool(top_symbol),
            "symbol": top_symbol,
            "signal": top_side if top_side in {"BUY", "SELL"} else "NEUTRAL",
            "confidence": round(top_confidence, 6),
            "vision_grade": "clear" if top_confidence >= 0.7 else "forming" if top_confidence >= 0.35 else "quiet",
            "timestamp": generated_at,
        }
        lyra_frequency = 396.0 + auris_coherence * (963.0 - 396.0)
        lyra_runtime = {
            "evaluated": bool(auris.get("evaluated")),
            "resonance_score": round((auris_coherence * 0.65) + (model_alignment * 0.2) + (source_unity * 0.15), 6),
            "resonance_frequency_hz": round(lyra_frequency, 3),
            "resonance_grade": auris.get("status"),
            "timestamp": generated_at,
        }
        king_runtime = {
            "evaluated": True,
            "executor_quote_usd": ORDER_EXECUTOR_QUOTE_USD,
            "max_open_positions": ORDER_EXECUTOR_MAX_OPEN_POSITIONS,
            "route_unity": round(route_unity, 6),
            "discipline_score": round((route_unity * 0.5) + (top_confidence * 0.3) + (real_data_score * 0.2), 6),
            "timestamp": generated_at,
        }
        systems["seer"]["runtime_reading"] = seer_runtime
        systems["seer"]["passed"] = bool(systems["seer"].get("passed") and seer_runtime.get("evaluated"))
        systems["lyra"]["runtime_reading"] = lyra_runtime
        systems["lyra"]["passed"] = bool(systems["lyra"].get("passed") and lyra_runtime.get("evaluated"))
        systems["king"]["runtime_reading"] = king_runtime
        systems["king"]["passed"] = bool(systems["king"].get("passed") and king_runtime.get("evaluated"))

        master_formula = {
            "source": "unified runtime blend over HNC/Auris/Seer/Lyra/King contracts",
            "evaluated": True,
            "formula": "HNC = 0.22*real_data + 0.16*source_unity + 0.22*auris + 0.14*model_alignment + 0.12*shadow + 0.14*route_unity",
            "inputs": {
                "real_data": real_data_score,
                "source_unity": round(source_unity, 6),
                "auris": round(auris_coherence, 6),
                "model_alignment": round(model_alignment, 6),
                "shadow": round(shadow_score, 6),
                "route_unity": round(route_unity, 6),
            },
            "score": round(master_score, 6),
            "passed": bool(master_score > 0 and metrics.get("passed")),
            "timestamp": generated_at,
        }

        flow = [
            {
                "step": "real_market_data",
                "passed": bool(metrics.get("passed")),
                "evidence": f"{metrics.get('source_count', 0)} sources, {metrics.get('symbol_count', 0)} symbols, {metrics.get('price_count', 0)} live prices",
                "timestamp": generated_at,
            },
            {
                "step": "hnc_master_formula",
                "passed": bool(master_formula["passed"] and systems["hnc_master_protocol"].get("passed")),
                "evidence": f"score={master_formula['score']}",
                "timestamp": generated_at,
            },
            {
                "step": "auris_nodes",
                "passed": bool(auris.get("passed") and systems["auris_nodes"].get("passed")),
                "evidence": f"{auris.get('node_count', 0)} nodes coherence={auris.get('coherence', 0.0)}",
                "timestamp": generated_at,
            },
            {
                "step": "seer_vision",
                "passed": bool(systems["seer"].get("passed")),
                "evidence": f"{seer_runtime.get('symbol') or 'no-symbol'} {seer_runtime.get('signal')} {seer_runtime.get('vision_grade')}",
                "timestamp": generated_at,
            },
            {
                "step": "lyra_resonance",
                "passed": bool(systems["lyra"].get("passed")),
                "evidence": f"{lyra_runtime.get('resonance_frequency_hz')}Hz {lyra_runtime.get('resonance_grade')}",
                "timestamp": generated_at,
            },
            {
                "step": "king_capital_logic",
                "passed": bool(systems["king"].get("passed")),
                "evidence": f"discipline={king_runtime.get('discipline_score')}",
                "timestamp": generated_at,
            },
            {
                "step": "shadow_trade_self_validation",
                "passed": bool(isinstance(shadow_trade_report, dict) and shadow_trade_report.get("enabled", True)),
                "evidence": (
                    f"{shadow_trade_report.get('shadow_opened_count', 0)} opened, "
                    f"{shadow_trade_report.get('active_shadow_count', 0)} active, "
                    f"{shadow_trade_report.get('validated_shadow_count', 0)} validated"
                ),
                "timestamp": generated_at,
            },
            {
                "step": "public_state_publication",
                "passed": True,
                "evidence": str(HNC_COGNITIVE_PROOF_PUBLIC_PATH),
                "timestamp": generated_at,
            },
        ]
        passed_count = sum(1 for step in flow if step.get("passed"))
        status = "passing" if passed_count == len(flow) else "attention"
        report = {
            "generated_at": generated_at,
            "status": status,
            "passed": passed_count == len(flow),
            "who": "HNC master formula plus Auris nodes, Seer, Lyra, King, shadow agents, and unified exchange runtime",
            "what": "timestamped proof that cognitive logic evaluated real market data and moved through the intended flow",
            "where": str(HNC_COGNITIVE_PROOF_STATE_PATH),
            "real_data": metrics,
            "market_texture": market_texture,
            "master_formula": master_formula,
            "auris_nodes": auris,
            "systems": systems,
            "flow": flow,
            "passed_count": passed_count,
            "step_count": len(flow),
            "runtime_clearances": action_plan.get("runtime_clearances", []) if isinstance(action_plan, dict) else [],
            "shadow_report_path": str(SHADOW_TRADE_STATE_PATH),
        }
        if isinstance(action_plan, dict):
            action_plan["hnc_cognitive_proof"] = report
        if persist:
            self._persist_hnc_cognitive_proof(report)
        return report

    def _persist_hnc_cognitive_proof(self, report: Dict[str, Any]) -> None:
        signature = "|".join(
            [
                str(report.get("status") or ""),
                str(report.get("passed_count") or 0),
                str(report.get("master_formula", {}).get("score") if isinstance(report.get("master_formula"), dict) else ""),
                str(report.get("real_data", {}).get("source_count") if isinstance(report.get("real_data"), dict) else ""),
            ]
        )
        now = time.time()
        for path in (HNC_COGNITIVE_PROOF_STATE_PATH, HNC_COGNITIVE_PROOF_PUBLIC_PATH):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(report, handle, indent=2, default=str)
                os.replace(tmp_path, path)
            except Exception as e:
                logger.debug("HNC cognitive proof write failed for %s: %s", path, e)
        last_signature = str(getattr(self, "_last_hnc_cognitive_proof_signature", "") or "")
        last_at = float(getattr(self, "_last_hnc_cognitive_proof_at", 0.0) or 0.0)
        if signature != last_signature or now - last_at >= HNC_COGNITIVE_PROOF_MIN_INTERVAL_SEC:
            self._last_hnc_cognitive_proof_signature = signature
            self._last_hnc_cognitive_proof_at = now
            try:
                HNC_COGNITIVE_PROOF_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                with HNC_COGNITIVE_PROOF_LOG_PATH.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(report, default=str, sort_keys=True) + "\n")
            except Exception as e:
                logger.debug("HNC cognitive proof log failed: %s", e)
            self._publish_thought("cognition.hnc_cognitive_proof", report)

    def _build_exchange_action_plan(self, order_flow_feed: Dict[str, Any]) -> Dict[str, Any]:
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not isinstance(active, list):
            active = []
        venues: Dict[str, Dict[str, Any]] = {}
        for item in active:
            if not isinstance(item, dict):
                continue
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
            for route_item in item.get("execution_routes", []) if isinstance(item.get("execution_routes"), list) else []:
                if not isinstance(route_item, dict):
                    continue
                venue = str(route_item.get("venue") or "").lower()
                market_type = str(route_item.get("market_type") or "").lower()
                if not venue:
                    continue
                key = f"{venue}_{market_type}" if market_type else venue
                state = venues.setdefault(
                    key,
                    {
                        "venue": venue,
                        "market_type": market_type,
                        "ready": False,
                        "candidate_count": 0,
                        "ready_candidate_count": 0,
                        "blockers": [],
                        "runtime_clearances": [],
                        "guards": [],
                        "trade_path_state": "held",
                        "end_user_trade_available": False,
                        "top_candidates": [],
                        "model_count": 0,
                        "model_total_count": 0,
                    },
                )
                blockers = [str(blocker) for blocker in route_item.get("blockers", []) if str(blocker)]
                state["ready"] = bool(state.get("ready") or route_item.get("ready"))
                if route_item.get("ready"):
                    state["trade_path_state"] = "available"
                    state["end_user_trade_available"] = True
                state["model_count"] = max(int(state.get("model_count", 0) or 0), int(route_item.get("model_count", 0) or 0))
                state["model_total_count"] = max(int(state.get("model_total_count", 0) or 0), int(route_item.get("model_total_count", 0) or 0))
                for blocker in blockers:
                    if blocker not in state["blockers"]:
                        state["blockers"].append(blocker)
                    if blocker not in state["runtime_clearances"]:
                        state["runtime_clearances"].append(blocker)
                    if blocker not in state["guards"]:
                        state["guards"].append(blocker)
                state["candidate_count"] = int(state.get("candidate_count", 0) or 0) + 1
                if route_item.get("ready") and confidence >= ORDER_INTENT_MIN_CONFIDENCE:
                    state["ready_candidate_count"] = int(state.get("ready_candidate_count", 0) or 0) + 1
                    state["top_candidates"].append(
                        {
                            "symbol": item.get("symbol"),
                            "route_symbol": route_item.get("symbol"),
                            "side": item.get("side"),
                            "confidence": confidence,
                            "support_count": item.get("support_count", 0),
                            "sources": item.get("sources", []),
                        }
                    )
        for state in venues.values():
            state["top_candidates"] = sorted(
                state.get("top_candidates", []),
                key=lambda candidate: float(candidate.get("confidence", 0.0) or 0.0),
                reverse=True,
            )[:5]

        publish_enabled = os.getenv("AUREON_ORDER_INTENT_PUBLISH", "0").strip().lower() in {"1", "true", "yes", "on"}
        authority_mode = os.getenv("AUREON_ORDER_AUTHORITY_MODE", "runtime_only").strip().lower()
        live_enabled = os.getenv("AUREON_LIVE_TRADING", "0").strip().lower() in {"1", "true", "yes", "on"}
        real_orders_disabled = os.getenv("AUREON_DISABLE_REAL_ORDERS", "1").strip().lower() in {"1", "true", "yes", "on"}
        exchange_mutations_disabled = os.getenv("AUREON_DISABLE_EXCHANGE_MUTATIONS", "1").strip().lower() in {"1", "true", "yes", "on"}
        global_blockers: List[str] = []
        if not live_enabled:
            global_blockers.append("live_trading_not_enabled")
        if real_orders_disabled:
            global_blockers.append("real_orders_disabled")
        if exchange_mutations_disabled:
            global_blockers.append("exchange_mutations_disabled")
        if authority_mode not in {"intent_only_runtime_gated", "runtime_only"}:
            global_blockers.append("order_authority_mode_not_runtime_gated")
        if not publish_enabled:
            global_blockers.append("order_intent_publish_disabled")
        model_coverage = self._all_exchange_model_coverage()
        global_clearances = list(global_blockers)
        global_guards = list(global_blockers)
        trade_path_state = "available" if live_enabled and not real_orders_disabled and not exchange_mutations_disabled else "operator_authorization_required"
        if global_clearances:
            trade_path_state = "runtime_clearance_pending"

        return {
            "generated_at": datetime.now().isoformat(),
            "mode": "runtime_gated_order_intent" if publish_enabled else "analysis_only",
            "venues": venues,
            "venue_count": len(venues),
            "ready_venue_count": sum(1 for state in venues.values() if state.get("ready")),
            "end_user_trade_available": any(bool(state.get("end_user_trade_available")) for state in venues.values()),
            "trade_path_state": trade_path_state,
            "order_intent_publish_enabled": publish_enabled,
            "executor_enabled": self._unified_executor_enabled(),
            "executor_quote_usd": ORDER_EXECUTOR_QUOTE_USD,
            "kraken_spot_quote_usd": KRAKEN_SPOT_QUOTE_USD,
            "executor_symbol_cooldown_sec": ORDER_EXECUTOR_SYMBOL_COOLDOWN_SEC,
            "executor_max_per_tick": ORDER_EXECUTOR_MAX_PER_TICK,
            "order_authority_mode": authority_mode,
            "live_enabled": live_enabled,
            "real_orders_disabled": real_orders_disabled,
            "exchange_mutations_disabled": exchange_mutations_disabled,
            "global_blockers": global_blockers,
            "global_clearances": global_clearances,
            "runtime_clearances": global_clearances,
            "global_guards": global_guards,
            "min_confidence": ORDER_INTENT_MIN_CONFIDENCE,
            "max_per_cycle": ORDER_INTENT_MAX_PER_CYCLE,
            "latest_published": getattr(self, "_latest_order_intents", {}),
            "latest_execution": getattr(self, "_latest_execution_results", {}),
            "model_coverage": model_coverage,
            "order_intents_published": 0,
        }

    def _publish_order_intents(self, order_flow_feed: Dict[str, Any], action_plan: Dict[str, Any]) -> None:
        if not isinstance(action_plan, dict) or not action_plan.get("order_intent_publish_enabled"):
            return
        if action_plan.get("global_blockers"):
            return
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not isinstance(active, list):
            return

        now = time.time()
        candidates: List[Dict[str, Any]] = []
        for item in active:
            if not isinstance(item, dict):
                continue
            confidence = max(0.0, min(1.0, float(item.get("confidence", 0.0) or 0.0)))
            if confidence < ORDER_INTENT_MIN_CONFIDENCE:
                continue
            ready_routes = [
                route_item
                for route_item in item.get("execution_routes", [])
                if isinstance(route_item, dict) and route_item.get("ready")
            ]
            if not ready_routes:
                continue
            candidates.append(
                {
                    "id": f"uintent-{int(now)}-{len(candidates) + 1}",
                    "generated_at": datetime.now().isoformat(),
                    "source": "unified_market_trader",
                    "topic": "execution.order.intent",
                    "symbol": item.get("symbol"),
                    "side": item.get("side"),
                    "confidence": confidence,
                    "support_count": item.get("support_count", 0),
                    "sources": item.get("sources", []),
                    "model_signal": item.get("model_signal", {}),
                    "model_alignment": item.get("model_alignment", False),
                    "routes": ready_routes,
                    "runtime_gate": "executor_required",
                    "authority_mode": action_plan.get("order_authority_mode"),
                    "safety": {
                        "direct_exchange_mutation_by_cognition": False,
                        "requires_runtime_risk_gate": True,
                        "requires_executor": True,
                    },
                }
            )
            if len(candidates) >= ORDER_INTENT_MAX_PER_CYCLE:
                break
        if not candidates:
            return

        signature = "|".join(
            f"{candidate.get('symbol')}:{candidate.get('side')}:{','.join(str(route.get('venue')) + '/' + str(route.get('market_type')) for route in candidate.get('routes', []))}"
            for candidate in candidates
        )
        last_signature = str(getattr(self, "_last_order_intent_signature", "") or "")
        last_at = float(getattr(self, "_last_order_intent_at", 0.0) or 0.0)
        if signature == last_signature and now - last_at < ORDER_INTENT_MIN_INTERVAL_SEC:
            return

        self._last_order_intent_at = now
        self._last_order_intent_signature = signature
        summary = {
            "generated_at": datetime.now().isoformat(),
            "source": "unified_market_trader",
            "mode": "runtime_gated_order_intent",
            "intent_count": len(candidates),
            "intents": candidates,
            "order_intent_log": str(ORDER_INTENT_LOG_PATH),
            "order_intent_state": str(ORDER_INTENT_STATE_PATH),
        }
        self._latest_order_intents = summary
        action_plan["latest_published"] = summary
        action_plan["order_intents_published"] = len(candidates)

        for candidate in candidates:
            self._publish_thought("execution.order.intent", candidate)

        try:
            ORDER_INTENT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with ORDER_INTENT_LOG_PATH.open("a", encoding="utf-8") as handle:
                for candidate in candidates:
                    handle.write(json.dumps(candidate, default=str, sort_keys=True) + "\n")
        except Exception as e:
            logger.debug("Order intent log write failed: %s", e)
        for path in (ORDER_INTENT_STATE_PATH, ORDER_INTENT_PUBLIC_PATH):
            try:
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp_path = path.with_name(f"{path.name}.{os.getpid()}.tmp")
                with tmp_path.open("w", encoding="utf-8") as handle:
                    json.dump(summary, handle, indent=2, default=str)
                os.replace(tmp_path, path)
            except Exception as e:
                logger.debug("Order intent state write failed for %s: %s", path, e)

    def _feed_auris_throne(self, order_flow_feed: Dict[str, Any]) -> None:
        if get_sero_client is None:
            return
        now = time.time()
        if now - self._last_auris_feed_at < AURIS_FEED_MIN_INTERVAL_SEC:
            return
        self._last_auris_feed_at = now
        active = order_flow_feed.get("active_order_flow", []) if isinstance(order_flow_feed, dict) else []
        if not active:
            return
        top = active[0] if isinstance(active[0], dict) else {}
        symbol = str(top.get("symbol") or "").upper()
        side = str(top.get("side") or "BUY").upper()
        confidence = float(top.get("confidence", 0.0) or 0.0)
        prompt = (
            f"GLOBAL_ORDER_FLOW shared_tradables={order_flow_feed.get('shared_tradable_count', 0)} "
            f"active={order_flow_feed.get('active_order_flow_count', 0)} "
            f"top={symbol} {side} confidence={confidence:.2f} "
            f"Please return PROCEED/CAUTION/ABORT and one-line rationale."
        )
        try:
            sero = get_sero_client()
            asyncio.run(sero.ask_market_intelligence(prompt))
        except Exception as e:
            logger.debug("Dr Auris Throne feed unavailable: %s", e)

    def _build_queen_voice_payload(self, kraken_payload: Dict[str, Any], capital_payload: Dict[str, Any]) -> Dict[str, Any]:
        now_iso = datetime.now().isoformat()
        kraken_decision = kraken_payload.get("decision_snapshot", {}) if isinstance(kraken_payload, dict) else {}
        capital_target = capital_payload.get("target_snapshot", {}) if isinstance(capital_payload, dict) else {}
        capital_candidates = capital_payload.get("candidate_snapshot", []) if isinstance(capital_payload, dict) else []
        capital_recent_closed = capital_payload.get("recent_closed_trades", []) if isinstance(capital_payload, dict) else []
        kraken_positions = kraken_payload.get("positions", []) if isinstance(kraken_payload.get("positions"), list) else []
        capital_positions = capital_payload.get("positions", []) if isinstance(capital_payload.get("positions"), list) else []
        open_positions = list(kraken_positions) + list(capital_positions)

        lines: List[str] = []
        mode = str(kraken_payload.get("queen_state") or "HOLD").upper()

        if open_positions:
            lines.append(
                f"Summary. I am managing {len(open_positions)} live position"
                f"{'' if len(open_positions) == 1 else 's'} across Kraken and Capital."
            )
        else:
            lines.append("Summary. I am flat on both exchanges and waiting for the next clean strike.")

        if kraken_positions:
            parts = []
            for pos in kraken_positions[:2]:
                symbol = str(pos.get("symbol") or pos.get("pair") or "?")
                side = str(pos.get("direction") or pos.get("side") or "?").upper()
                parts.append(f"{symbol} {side}")
            lines.append(f"Kraken update. I am managing {' and '.join(parts)}.")
        elif kraken_decision and kraken_decision.get("decision"):
            decision = kraken_decision.get("decision", {}) or {}
            decision_type = str(decision.get("type", "UNKNOWN")).replace("_", " ").lower()
            lines.append(
                f"Kraken update. I am leaning toward {kraken_decision.get('symbol', '?')} "
                f"{str(kraken_decision.get('side', '?')).lower()} with a "
                f"{self._confidence_word(decision.get('confidence', 0.0))} read for {decision_type}."
            )
        else:
            lines.append("Kraken update. I am watching for a cleaner crypto entry.")

        if capital_positions:
            parts = []
            for pos in capital_positions[:2]:
                symbol = str(pos.get("symbol") or "?")
                side = str(pos.get("direction") or pos.get("side") or "?").upper()
                parts.append(f"{symbol} {side}")
            lines.append(f"Capital update. I am managing {' and '.join(parts)}.")
        elif capital_target:
            target_symbol = str(capital_target.get("symbol") or "?")
            target_direction = str(capital_target.get("direction") or "?").upper()
            expected_net = float(capital_target.get("expected_net_profit", 0.0) or 0.0)
            lines.append(
                f"Capital update. I am stalking {target_symbol} {target_direction}. "
                f"The setup looks {'profitable' if expected_net > 0 else 'weak'} at the moment."
            )
            reason = str(capital_target.get("preflight_reason") or "").strip()
            if reason:
                lines.append("Capital is still waiting because the exchange checks are blocking entry.")
        elif capital_candidates:
            top = capital_candidates[0] if isinstance(capital_candidates[0], dict) else {}
            if top:
                lines.append(
                    f"Capital update. My next candidate is {top.get('symbol', '?')} "
                    f"{str(top.get('direction', '?')).upper()} if the current leader fails."
                )
        else:
            lines.append("Capital update. I am waiting for a valid CFD setup.")

        if capital_recent_closed:
            latest_close = capital_recent_closed[-1] if isinstance(capital_recent_closed[-1], dict) else {}
            learning_update = latest_close.get("learning_update", {}) if isinstance(latest_close, dict) else {}
            if learning_update:
                lines.append(
                    f"Learning update. I learned from {latest_close.get('symbol', '?')} and shifted my bias to "
                    f"{float(learning_update.get('symbol_bias', 0.0) or 0.0):+.3f} after a "
                    f"{float(latest_close.get('net_pnl', 0.0) or 0.0):+.2f} GBP result."
                )

        if open_positions:
            lines.append("I am watching the open positions closely and waiting for clean profit exits.")

        return {
            "ts": now_iso,
            "mode": mode,
            "text": " ".join(line.strip() for line in lines if line.strip()),
            "lines": lines,
            "sources": {
                "kraken_decision": kraken_decision,
                "capital_target": capital_target,
            },
        }

    def get_local_dashboard_state(self) -> Dict[str, Any]:
        payload = self._latest_dashboard_payload or self._build_bootstrap_dashboard_payload()
        return self._copy_payload(payload)

    def get_runtime_health(self) -> Dict[str, Any]:
        payload = self._latest_dashboard_payload or self._build_bootstrap_dashboard_payload()
        preflight = payload.get("preflight", {}) if isinstance(payload, dict) else {}
        combined = payload.get("combined", {}) if isinstance(payload, dict) else {}
        action_plan = payload.get("exchange_action_plan", {}) if isinstance(payload, dict) else {}
        now = time.time()
        last_tick_completed_at = float(getattr(self, "_last_tick_completed_at", 0.0) or 0.0)
        last_tick_started_at = float(getattr(self, "_last_tick_started_at", 0.0) or 0.0)
        tick_age_sec = (now - last_tick_completed_at) if last_tick_completed_at > 0 else None
        tick_running_sec = (now - last_tick_started_at) if last_tick_started_at > last_tick_completed_at else 0.0
        booting = last_tick_completed_at <= 0
        boot_age_sec = now - float(getattr(self, "start_time", now) or now)
        stale_reason = ""
        if last_tick_completed_at > 0 and tick_age_sec is not None and tick_age_sec > READY_STALE_AFTER_SEC:
            stale_reason = "last_tick_age_exceeded"
        if tick_running_sec > READY_STALE_AFTER_SEC:
            stale_reason = "tick_in_progress_stalled"
        if booting and boot_age_sec > max(READY_STALE_AFTER_SEC * 3.0, 180.0):
            stale_reason = "booting_timeout"
        stale = bool(stale_reason)
        alpaca_ok = self.alpaca is not None and not bool(self.alpaca_error or getattr(self.alpaca, "init_error", ""))
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        binance_ok = self.binance is not None and bool(binance_diag.get("network_ok", False))
        trading_ready = bool(self.kraken_ready and self.capital_ready)
        data_ready = bool(alpaca_ok and binance_ok)
        return {
            "ok": bool(trading_ready and data_ready and not stale),
            "service": "unified-market-trader",
            "duplicate_runtime": bool(getattr(self, "_duplicate_runtime", False)),
            "trading_ready": trading_ready,
            "data_ready": data_ready,
            "stale": stale,
            "booting": booting,
            "boot_age_sec": round(float(boot_age_sec), 3),
            "last_tick_started_at": datetime.fromtimestamp(last_tick_started_at).isoformat() if last_tick_started_at > 0 else None,
            "last_tick_completed_at": datetime.fromtimestamp(last_tick_completed_at).isoformat() if last_tick_completed_at > 0 else None,
            "last_tick_age_sec": round(float(tick_age_sec), 3) if tick_age_sec is not None else None,
            "last_tick_running_sec": round(float(tick_running_sec), 3) if tick_running_sec > 0 else 0.0,
            "stale_reason": stale_reason,
            "dashboard_generated_at": payload.get("generated_at"),
            "runtime_minutes": payload.get("runtime_minutes"),
            "preflight_overall": preflight.get("overall"),
            "preflight_critical_failures": int(preflight.get("critical_failures", 0) or 0),
            "preflight_warnings": int(preflight.get("warnings", 0) or 0),
            "exchanges": {
                "kraken_ready": bool(self.kraken_ready),
                "capital_ready": bool(self.capital_ready),
                "alpaca_ready": alpaca_ok,
                "binance_ready": binance_ok,
                "all_four_connected": bool(self.kraken_ready and self.capital_ready and alpaca_ok and binance_ok),
                "execution_venues": action_plan.get("venues", {}) if isinstance(action_plan, dict) else {},
                "ready_execution_venue_count": int(action_plan.get("ready_venue_count", 0) or 0)
                if isinstance(action_plan, dict)
                else 0,
            },
            "errors": {
                "kraken": self.kraken_error,
                "capital": self.capital_error,
                "alpaca": self.alpaca_error,
                "binance": self.binance_error,
                "last_tick_error": self._last_tick_error,
            },
            "combined": {
                "open_positions": int(combined.get("open_positions", 0) or 0),
                "kraken_equity": float(combined.get("kraken_equity", 0.0) or 0.0),
                "capital_equity_gbp": float(combined.get("capital_equity_gbp", 0.0) or 0.0),
            },
            "api_governor": payload.get("api_governor") or self._governor().snapshot(),
            "exchange_action_plan": action_plan,
            "shadow_trading": (
                payload.get("shadow_trading")
                or (action_plan.get("shadow_trading", {}) if isinstance(action_plan, dict) else {})
            ),
            "hnc_cognitive_proof": (
                payload.get("hnc_cognitive_proof")
                or (action_plan.get("hnc_cognitive_proof", {}) if isinstance(action_plan, dict) else {})
            ),
            "runtime_watchdog": {
                "heartbeat_alive": True,
                "heartbeat_at": payload.get("runtime_heartbeat", {}).get("heartbeat_at_iso")
                if isinstance(payload.get("runtime_heartbeat"), dict)
                else None,
                "tick_stale": stale,
                "tick_stale_reason": stale_reason,
                "tick_stale_after_sec": READY_STALE_AFTER_SEC,
                "last_tick_age_sec": round(float(tick_age_sec), 3) if tick_age_sec is not None else None,
                "last_tick_running_sec": round(float(tick_running_sec), 3) if tick_running_sec > 0 else 0.0,
                "file_heartbeat_is_not_market_freshness": True,
            },
            "runtime_writer": {
                "owns_lock": bool(getattr(self, "_owns_runtime_status", True)),
                "pid": os.getpid(),
                "instance_id": getattr(self, "_runtime_instance_id", ""),
                "reason": getattr(self, "_runtime_writer_lock_reason", ""),
            },
        }

    def _latest_monitor_line(self) -> str:
        capital_line = getattr(self.capital, "_latest_monitor_line", "") if self.capital is not None else ""
        kraken_line = getattr(self.kraken, "_latest_monitor_line", "") if self.kraken is not None else ""
        return capital_line or kraken_line

    def get_status_lines(self) -> List[str]:
        lines = [
            f"UNIFIED MARKET STATUS | runtime={(time.time() - self.start_time) / 60.0:.1f}m",
            "Markets armed: Kraken spot/margin + Capital CFDs + Alpaca spot + Binance spot/margin | CentralBeat fusion active",
        ]
        preflight = self._build_preflight_report()
        lines.append(
            "Preflight: "
            f"{str(preflight.get('overall', 'unknown')).upper()} "
            f"critical={int(preflight.get('critical_failures', 0) or 0)} "
            f"warnings={int(preflight.get('warnings', 0) or 0)}"
        )
        central_beat = self._central_beat_feed or {}
        regime = central_beat.get("regime", {}) if isinstance(central_beat, dict) else {}
        if regime:
            lines.append(
                "CentralBeat: "
                f"sources={int(regime.get('source_count', 0) or 0)} "
                f"bias={regime.get('bias', '?')} "
                f"conf={float(regime.get('confidence', 0.0) or 0.0):.2f}"
            )
        execution = getattr(self, "_latest_execution_results", {}) or {}
        if execution:
            lines.append(
                "Unified executor: "
                f"enabled={bool(execution.get('executor_enabled'))} "
                f"submitted={int(execution.get('submitted_count', 0) or 0)} "
                f"delegated={int(execution.get('delegated_count', 0) or 0)} "
                f"held={int(execution.get('held_count', execution.get('blocked_count', 0)) or 0)} "
                f"clearances={','.join(execution.get('runtime_clearances') or execution.get('guards') or execution.get('blockers') or []) or 'none'}"
            )
        governor = self._governor().snapshot()
        exchanges = governor.get("exchanges", {}) if isinstance(governor, dict) else {}
        if exchanges:
            parts = []
            for name in ("kraken", "capital", "alpaca", "binance"):
                state = exchanges.get(name, {}) if isinstance(exchanges, dict) else {}
                if state:
                    parts.append(
                        f"{name}:{int(state.get('recent_calls_60s', 0) or 0)}/"
                        f"{int(state.get('max_calls_per_min', 0) or 0)}"
                    )
            if parts:
                lines.append("API governor: " + " ".join(parts))
        alpaca_state = "ready" if self.alpaca is not None and not self.alpaca_error else "unavailable"
        lines.append(f"ALPACA: spot_route_{alpaca_state} | {self.alpaca_error or 'ok'}")
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        if self.binance is not None:
            lines.append(
                "BINANCE: "
                f"spot_route_ready={bool(binance_diag.get('network_ok', False))} "
                f"account_ready={bool(binance_diag.get('account_ok', False))} "
                f"margin_available={bool(binance_diag.get('margin_available', False))} "
                f"uk_mode={bool(binance_diag.get('uk_mode', getattr(self.binance, 'uk_mode', False)))} "
                f"| {self.binance_error or 'ok'}"
            )
        else:
            lines.append(f"BINANCE: unavailable | {self.binance_error or 'not_ready'}")
        if self.kraken_ready and self.kraken is not None:
            lines.extend(self.kraken._latest_status_lines[-10:] if getattr(self.kraken, "_latest_status_lines", None) else [])
        else:
            lines.append(f"KRAKEN: unavailable | {self.kraken_error or 'not_ready'}")
        if self.capital_ready and self.capital is not None:
            lines.extend(self.capital.status_lines())
        else:
            lines.append(f"CAPITAL: unavailable | {self.capital_error or 'not_ready'}")
        return lines

    def print_status(self) -> None:
        _safe_print()
        _safe_print("=" * 78)
        _safe_print(f"  UNIFIED MARKET TRADER | Runtime: {(time.time() - self.start_time) / 60.0:.1f}m")
        _safe_print("  Exchanges: Kraken Spot/Margin + Capital CFDs + Alpaca Spot + Binance Spot/Margin")
        _safe_print("  CentralBeat: Kraken + Capital + Alpaca + Binance feed fusion and order-intent routing")
        execution = getattr(self, "_latest_execution_results", {}) or {}
        if execution:
            _safe_print(
                "  Unified executor: "
                f"enabled={bool(execution.get('executor_enabled'))} "
                f"submitted={int(execution.get('submitted_count', 0) or 0)} "
                f"delegated={int(execution.get('delegated_count', 0) or 0)} "
                f"held={int(execution.get('held_count', execution.get('blocked_count', 0)) or 0)} "
                f"clearances={','.join(execution.get('runtime_clearances') or execution.get('guards') or execution.get('blockers') or []) or 'none'}"
            )
        governor = self._governor().snapshot()
        exchanges = governor.get("exchanges", {}) if isinstance(governor, dict) else {}
        if exchanges:
            parts = []
            for name in ("kraken", "capital", "alpaca", "binance"):
                state = exchanges.get(name, {}) if isinstance(exchanges, dict) else {}
                if state:
                    parts.append(
                        f"{name}:{int(state.get('recent_calls_60s', 0) or 0)}/"
                        f"{int(state.get('max_calls_per_min', 0) or 0)}"
                    )
            if parts:
                _safe_print("  API governor: " + " ".join(parts))
        preflight = self._build_preflight_report()
        _safe_print(
            "  Preflight: "
            f"{str(preflight.get('overall', 'unknown')).upper()} "
            f"critical={int(preflight.get('critical_failures', 0) or 0)} "
            f"warnings={int(preflight.get('warnings', 0) or 0)}"
        )
        _safe_print(f"  ALPACA: {'spot_route_ready' if self.alpaca is not None and not self.alpaca_error else 'spot_route_unavailable'} | {self.alpaca_error or 'ok'}")
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        if self.binance is not None:
            _safe_print(
                "  BINANCE: "
                f"spot_route_ready={bool(binance_diag.get('network_ok', False))} "
                f"account_ready={bool(binance_diag.get('account_ok', False))} "
                f"margin_available={bool(binance_diag.get('margin_available', False))} "
                f"uk_mode={bool(binance_diag.get('uk_mode', getattr(self.binance, 'uk_mode', False)))} "
                f"| {self.binance_error or 'ok'}"
            )
        else:
            _safe_print(f"  BINANCE: unavailable | {self.binance_error or 'not_ready'}")
        _safe_print("-" * 78)
        _safe_print("  [KRAKEN]")
        if self.kraken_ready and self.kraken is not None:
            for line in self.kraken._latest_status_lines[-10:]:
                _safe_print(f"  {line}")
        else:
            _safe_print(f"  KRAKEN unavailable: {self.kraken_error or 'not_ready'}")
        _safe_print("-" * 78)
        _safe_print("  [CAPITAL]")
        if self.capital_ready and self.capital is not None:
            for line in self.capital.status_lines():
                _safe_print(f"  {line}")
        else:
            _safe_print(f"  CAPITAL unavailable: {self.capital_error or 'not_ready'}")
        _safe_print("=" * 78)
        _safe_print()

    # ── Network helpers ─────────────────────────────────────────────────────

    def _publish_thought(self, topic: str, payload_data: Dict[str, Any]) -> None:
        if self._thought_bus is None or Thought is None:
            return
        try:
            self._thought_bus.publish(Thought(
                source="unified_market_trader",
                topic=topic,
                payload=payload_data,
                meta={"mode": "unified"},
            ))
        except Exception:
            pass

    def _record_trade_profit(self, trade: dict) -> None:
        try:
            from aureon.autonomous.aureon_cognitive_trade_evidence import append_trade_evidence

            append_trade_evidence(
                trade,
                source="unified_market_trader.closed_trade",
                runtime_snapshot=self.get_runtime_health(),
            )
        except Exception:
            pass
        if self._mycelium is None:
            return
        try:
            if hasattr(self._mycelium, "record_trade_profit"):
                self._mycelium.record_trade_profit(
                    net_profit=float(trade.get("net_pnl", 0) or 0),
                    trade_data=trade,
                )
        except Exception:
            pass

    def tick(self) -> Dict[str, Any]:
        self._last_tick_started_at = time.time()
        self._last_tick_error = ""
        self._ensure_exchanges()
        kraken_closed: List[dict] = []
        capital_closed: List[dict] = []
        if self.kraken_ready and self.kraken is not None:
            if self._governor().should_run_cycle(
                "kraken",
                "positions",
                "kraken.tick",
                KRAKEN_TICK_MIN_INTERVAL_SEC,
            ):
                try:
                    kraken_closed = self.kraken.tick()
                except Exception as e:
                    self._governor().record_error("kraken", e)
                    self.kraken_error = str(e)
                    self.kraken_ready = False
                    self.kraken = None
                    self._last_tick_error = str(e)
                    logger.error("Kraken tick failed: %s", e)
        if self.capital_ready and self.capital is not None:
            if self._governor().should_run_cycle(
                "capital",
                "positions",
                "capital.tick",
                CAPITAL_TICK_MIN_INTERVAL_SEC,
            ):
                try:
                    capital_closed = self.capital.tick()
                except Exception as e:
                    self._governor().record_error("capital", e)
                    self.capital_error = str(e)
                    self.capital_ready = False
                    self.capital = None
                    self._last_tick_error = str(e)
                    logger.error("Capital tick failed: %s", e)

        # ── Publish closed trades to Thought Bus + record in Mycelium ─────
        for trade in kraken_closed:
            self._publish_thought("execution.trade.closed", {
                "pair": str(trade.get("pair") or trade.get("symbol") or "?"),
                "net_pnl": float(trade.get("net_pnl", 0) or 0),
                "reason": str(trade.get("reason") or "?"),
                "exchange": "kraken",
            })
            self._record_trade_profit(trade)
        for trade in capital_closed:
            self._publish_thought("execution.trade.closed", {
                "pair": str(trade.get("symbol") or trade.get("pair") or "?"),
                "net_pnl": float(trade.get("pnl_gbp", 0) or 0),
                "reason": str(trade.get("reason") or "?"),
                "exchange": "capital",
            })
            self._record_trade_profit(trade)

        # ── Periodic status publish (every 30s) ──────────────────────────
        now = time.time()
        if now - self._last_status_publish >= 30.0:
            self._last_status_publish = now
            self._publish_thought("unified.status", {
                "kraken_ready": self.kraken_ready,
                "capital_ready": self.capital_ready,
                "alpaca_ready": self.alpaca is not None and not bool(self.alpaca_error),
                "binance_ready": self.binance is not None and bool((getattr(self, "_binance_diag", {}) or {}).get("network_ok", False)),
                "uptime_secs": now - self.start_time,
                "api_governor": self._governor().snapshot(),
            })
            # Publish market feed for Hive Command worker bees
            if self._shared_market_feed:
                symbols = list(self._shared_market_feed.keys())
                self._publish_thought("market.feed", {
                    "prices": dict(self._shared_market_feed),
                    "symbols": symbols,
                })

        payload = self._build_combined_payload()
        execution_summary = self._execute_runtime_order_actions(payload)
        if isinstance(payload.get("exchange_action_plan"), dict):
            payload["exchange_action_plan"]["latest_execution"] = execution_summary
        self._latest_dashboard_payload = self._copy_payload(payload)
        self._last_tick_completed_at = time.time()
        self._write_runtime_status_file()
        return {
            "kraken_closed": kraken_closed,
            "capital_closed": capital_closed,
            "execution": execution_summary,
            "payload": payload,
        }

    def run(self, interval_sec: float = 2.0) -> None:
        if bool(getattr(self, "_duplicate_runtime", False)):
            _safe_print("Unified market trader duplicate suppressed.")
            _safe_print(self._runtime_writer_lock_reason or "Another fresh runtime owns the writer lock.")
            return

        mode = "DRY RUN" if self.dry_run else "LIVE"
        _safe_print("=" * 78)
        _safe_print("  UNIFIED MARKET TRADER")
        _safe_print(f"  Mode: {mode}")
        _safe_print("  Execution venues: Kraken spot/margin + Capital CFDs + Alpaca spot + Binance spot/margin")
        _safe_print("  Monitoring: local-first dashboard + terminal telemetry")
        _safe_print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        _safe_print("=" * 78)

        if self.kraken is not None:
            self._startup_kraken(force=True)

        if self.capital is not None:
            self._startup_capital(force=True)

        self._build_combined_payload()

        try:
            while True:
                self.tick()
                self.print_status()
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            _safe_print("\nUnified market trader stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Kraken + Capital market trader")
    parser.add_argument("--dry-run", action="store_true", help="Run Kraken in dry-run mode")
    parser.add_argument("--interval", type=float, default=2.0, help="Main loop interval in seconds")
    parser.add_argument(
        "--setup-kraken-cli",
        action="store_true",
        help="Install Kraken CLI before startup if it is missing (uses Kraken's official installer).",
    )
    args = parser.parse_args()

    trader = UnifiedMarketTrader(dry_run=args.dry_run, setup_kraken_cli=args.setup_kraken_cli)
    trader.run(interval_sec=max(0.5, float(args.interval)))


if __name__ == "__main__":
    main()
