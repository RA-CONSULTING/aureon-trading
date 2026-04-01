#!/usr/bin/env python3
"""
Unified market runner for the current live setup.

Runs:
- Kraken crypto margin trader
- Capital.com CFD trader

Provides:
- one autonomous loop
- one combined terminal status surface
- one local telemetry API for the dashboard
"""

from __future__ import annotations

import argparse
import asyncio
import copy
import json
import logging
import os
import shutil
import subprocess
import threading
import time
import io
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List

try:
    from kraken_margin_penny_trader import KrakenMarginArmyTrader
    from capital_cfd_trader import CAPITAL_UNIVERSE, CapitalCFDTrader
except Exception:
    from aureon.exchanges.kraken_margin_penny_trader import KrakenMarginArmyTrader
    from aureon.exchanges.capital_cfd_trader import CAPITAL_UNIVERSE, CapitalCFDTrader
try:
    from alpaca_client import AlpacaClient
except Exception:
    try:
        from aureon.exchanges.alpaca_client import AlpacaClient
    except Exception:
        AlpacaClient = None  # type: ignore[assignment]
try:
    from binance_client import BinanceClient
except Exception:
    try:
        from aureon.exchanges.binance_client import BinanceClient
    except Exception:
        BinanceClient = None  # type: ignore[assignment]

try:
    from aureon.utils.aureon_sero_client import get_sero_client
except Exception:
    try:
        from aureon_sero_client import get_sero_client
    except Exception:
        get_sero_client = None  # type: ignore[assignment]

logger = logging.getLogger("unified_market_trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

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
RUNTIME_STATUS_PATH = Path(__file__).resolve().parents[2] / "state" / "unified_runtime_status.json"
EXCHANGE_REINIT_INTERVAL_SEC = max(2.0, _env_float("UNIFIED_EXCHANGE_REINIT_INTERVAL_SEC", 30.0))
AURIS_FEED_MIN_INTERVAL_SEC = max(5.0, _env_float("UNIFIED_AURIS_FEED_MIN_INTERVAL_SEC", 45.0))
CENTRAL_BEAT_REFRESH_SEC = max(1.0, _env_float("UNIFIED_CENTRAL_BEAT_REFRESH_SEC", 20.0))
CENTRAL_BEAT_STALE_AFTER_SEC = max(
    CENTRAL_BEAT_REFRESH_SEC * 2.0,
    _env_float("UNIFIED_CENTRAL_BEAT_STALE_AFTER_SEC", 90.0),
)
READY_STALE_AFTER_SEC = max(5.0, _env_float("UNIFIED_READY_STALE_AFTER_SEC", 15.0))
CENTRAL_BEAT_HISTORY_LIMIT = 24
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


def _safe_print(*args: Any, **kwargs: Any) -> None:
    try:
        print(*args, **kwargs)
    except (ValueError, OSError):
        message = " ".join(str(arg) for arg in args)
        logger.info(message)


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
        self._local_dashboard_server: ThreadingHTTPServer | None = None
        self._local_dashboard_thread: threading.Thread | None = None
        if self.setup_kraken_cli:
            self._ensure_kraken_cli()
        self._init_exchanges()
        self._latest_dashboard_payload = self._build_bootstrap_dashboard_payload()
        self._write_runtime_status_file()
        self._start_local_dashboard_server()

    @staticmethod
    def _is_closed_stream_error(exc: Exception) -> bool:
        text = str(exc or "").strip().lower()
        return "closed file" in text or "i/o operation on closed file" in text

    def _retry_with_safe_streams(self, factory):
        """Retry constructor calls with captured stdout/stderr when terminal streams are unstable."""
        sink = io.StringIO()
        with redirect_stdout(sink), redirect_stderr(sink):
            return factory()

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
                "alpaca_passive",
                alpaca_ok,
                "warning" if not alpaca_ok else "ok",
                self.alpaca_error or str(getattr(self.alpaca, "init_error", "") or ("ready" if self.alpaca is not None else "not_initialized")),
            )
        )

        binance_diag = getattr(self, "_binance_diag", {}) or {}
        binance_network_ok = bool(binance_diag.get("network_ok", False))
        items.append(
            self._preflight_item(
                "binance_passive",
                self.binance is not None and binance_network_ok,
                "warning" if self.binance is not None else "warning",
                self.binance_error or ("ready" if binance_network_ok else "network_unavailable"),
                meta={
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
        try:
            self.kraken = KrakenMarginArmyTrader(dry_run=self.dry_run)
            if hasattr(self.kraken, "set_shared_portfolio_snapshot_provider"):
                self.kraken.set_shared_portfolio_snapshot_provider(self._shared_portfolio_snapshot)
            self.kraken_error = ""
        except Exception as e:
            retried = False
            if self._is_closed_stream_error(e):
                try:
                    self.kraken = self._retry_with_safe_streams(
                        lambda: KrakenMarginArmyTrader(dry_run=self.dry_run)
                    )
                    if hasattr(self.kraken, "set_shared_portfolio_snapshot_provider"):
                        self.kraken.set_shared_portfolio_snapshot_provider(self._shared_portfolio_snapshot)
                    self.kraken_error = ""
                    retried = True
                    logger.warning("Kraken init succeeded after safe-stream retry.")
                except Exception as retry_error:
                    e = retry_error
            if not retried:
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
            if hasattr(self.capital, "set_shared_portfolio_snapshot_provider"):
                self.capital.set_shared_portfolio_snapshot_provider(self._shared_portfolio_snapshot)
            self.capital_ready = bool(getattr(self.capital, "enabled", False))
            self.capital_error = ""
            if not self.capital_ready:
                self.capital_error = str(getattr(self.capital, "init_error", "") or "client_disabled_or_blocked")
        except Exception as e:
            retried = False
            if self._is_closed_stream_error(e):
                try:
                    self.capital = self._retry_with_safe_streams(lambda: CapitalCFDTrader())
                    if hasattr(self.capital, "set_shared_portfolio_snapshot_provider"):
                        self.capital.set_shared_portfolio_snapshot_provider(self._shared_portfolio_snapshot)
                    self.capital_ready = bool(getattr(self.capital, "enabled", False))
                    self.capital_error = ""
                    if not self.capital_ready:
                        self.capital_error = str(getattr(self.capital, "init_error", "") or "client_disabled_or_blocked")
                    retried = True
                    logger.warning("Capital init succeeded after safe-stream retry.")
                except Exception as retry_error:
                    e = retry_error
            if not retried:
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
            retried = False
            if self._is_closed_stream_error(e):
                try:
                    self.binance = self._retry_with_safe_streams(lambda: BinanceClient())
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
                    retried = True
                    logger.warning("Binance init succeeded after safe-stream retry.")
                except Exception as retry_error:
                    e = retry_error
            if not retried:
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
            try:
                self.kraken.discover_margin_universe()
                self.kraken.update_prices_free()
            except Exception as startup_error:
                if self._is_closed_stream_error(startup_error):
                    self._retry_with_safe_streams(lambda: self.kraken.discover_margin_universe())
                    self._retry_with_safe_streams(lambda: self.kraken.update_prices_free())
                    logger.warning("Kraken startup recovered after safe-stream retry.")
                else:
                    raise
            try:
                self.kraken.print_status()
            except Exception as status_error:
                if self._is_closed_stream_error(status_error):
                    logger.warning("Kraken status print skipped due closed output stream: %s", status_error)
                else:
                    logger.debug("Kraken status print failed: %s", status_error)
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
            status_error = None
            try:
                self.capital.status_lines()
            except Exception as status_exc:
                status_error = status_exc
            self.capital_ready = bool(getattr(self.capital, "enabled", False))
            if self.capital_ready:
                self.capital_error = ""
                if status_error is not None:
                    if self._is_closed_stream_error(status_error):
                        logger.warning(
                            "Capital status render skipped due closed output stream: %s",
                            status_error,
                        )
                    else:
                        logger.debug("Capital status render failed: %s", status_error)
            elif not self.capital_error:
                if status_error is not None:
                    self.capital_error = str(status_error)
                else:
                    self.capital_error = str(getattr(self.capital, "init_error", "") or "client_disabled_or_blocked")
        except Exception as e:
            self.capital_ready = False
            self.capital_error = str(e)
            logger.error("Capital startup unavailable: %s", e)

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
        try:
            RUNTIME_STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(RUNTIME_STATUS_PATH, "w", encoding="utf-8") as f:
                json.dump(self.get_runtime_health(), f, indent=2, default=str)
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
                "active_order_flow_count": 0,
                "active_order_flow": [],
                "kraken_tradables": 0,
                "capital_tradables": 0,
                "scope": "cross-exchange shared tradables only",
            },
            "preflight": preflight,
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
            "preflight": self._build_preflight_report(),
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
                    {"support_count": 0, "confidence_sum": 0.0, "buy_confidence": 0.0, "sell_confidence": 0.0, "sources": []},
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

        normalized_symbols: Dict[str, Dict[str, Any]] = {}
        for normalized, item in symbols.items():
            support_count = int(item.get("support_count", 0) or 0)
            confidence_sum = float(item.get("confidence_sum", 0.0) or 0.0)
            avg_confidence = confidence_sum / support_count if support_count > 0 else 0.0
            buy_conf = float(item.get("buy_confidence", 0.0) or 0.0)
            sell_conf = float(item.get("sell_confidence", 0.0) or 0.0)
            side = "BUY" if buy_conf >= sell_conf else "SELL"
            imbalance = abs(buy_conf - sell_conf)
            normalized_symbols[normalized] = {
                "confidence": round(avg_confidence, 4),
                "support_count": support_count,
                "side": side,
                "imbalance": round(imbalance, 4),
                "strength": round(avg_confidence * (1.0 + min(1.0, (support_count - 1) * 0.35)), 4),
                "sources": list(item.get("sources", [])),
            }

        total_pressure = buy_pressure + sell_pressure
        regime = {
            "buy_pressure": round(buy_pressure, 4),
            "sell_pressure": round(sell_pressure, 4),
            "bias": "BUY" if buy_pressure >= sell_pressure else "SELL",
            "confidence": round((max(buy_pressure, sell_pressure) / total_pressure) if total_pressure > 0 else 0.0, 4),
            "source_count": len(sources),
        }

        payload = {
            "generated_at": datetime.now().isoformat(),
            "sources": sources,
            "source_count": len(sources),
            "symbols": normalized_symbols,
            "regime": regime,
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

    def _extract_trader_source_snapshot(self, source_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        symbols: Dict[str, Dict[str, Any]] = {}

        def push(symbol: Any, confidence: Any, side: Any = "BUY") -> None:
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
            }

        for candidate in payload.get("candidate_snapshot", [])[:8]:
            if isinstance(candidate, dict):
                push(
                    candidate.get("symbol") or candidate.get("pair"),
                    self._extract_candidate_confidence(candidate),
                    candidate.get("direction") or candidate.get("side") or "BUY",
                )

        decision_snapshot = payload.get("decision_snapshot", {})
        if isinstance(decision_snapshot, dict):
            decision = decision_snapshot.get("decision", {}) if isinstance(decision_snapshot.get("decision"), dict) else {}
            push(
                decision_snapshot.get("symbol"),
                decision.get("confidence", 0.0),
                decision_snapshot.get("side") or decision.get("direction") or decision.get("type") or "BUY",
            )

        target_snapshot = payload.get("target_snapshot", {})
        if isinstance(target_snapshot, dict):
            push(
                target_snapshot.get("symbol"),
                self._extract_candidate_confidence(target_snapshot),
                target_snapshot.get("direction") or "BUY",
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
                ticker = client.get_ticker(crypto_symbol)
            except Exception:
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
                ticker = client.get_24h_ticker(binance_symbol)
            except Exception:
                continue
            change_pct = float(ticker.get("priceChangePercent", 0.0) or 0.0)
            if abs(change_pct) <= 0.0:
                continue
            symbols[normalized] = {
                "symbol": normalized,
                "raw_symbol": binance_symbol,
                "confidence": min(1.0, abs(change_pct) / 5.0),
                "side": "BUY" if change_pct >= 0 else "SELL",
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
            return f"{symbol[:-3]}/USD"
        return ""

    def _to_binance_symbol(self, normalized: str) -> str:
        symbol = str(normalized or "").upper()
        if symbol.endswith("USD") and len(symbol) > 3:
            return f"{symbol[:-3]}USDT"
        return ""

    def _capital_tradable_symbols(self) -> Dict[str, str]:
        return {self._normalize_symbol(symbol): symbol for symbol in CAPITAL_UNIVERSE.keys()}

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
        kraken_tradables = self._kraken_tradable_symbols()
        capital_tradables = self._capital_tradable_symbols()
        shared_keys = sorted(set(kraken_tradables.keys()) & set(capital_tradables.keys()))

        symbols_conf = shared_market_feed.get("symbols", {}) if isinstance(shared_market_feed, dict) else {}
        central_symbols = central_beat.get("symbols", {}) if isinstance(central_beat, dict) else {}
        ranked: List[Dict[str, Any]] = []
        for normalized in shared_keys:
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
            ranked.append(
                {
                    "symbol": normalized,
                    "kraken_symbol": kraken_tradables.get(normalized, normalized),
                    "capital_symbol": capital_symbol,
                    "side": side,
                    "confidence": max(0.0, min(1.0, confidence)),
                    "support_count": int(central_signal.get("support_count", 0) or 0) if isinstance(central_signal, dict) else 0,
                    "sources": list(central_signal.get("sources", [])) if isinstance(central_signal, dict) and isinstance(central_signal.get("sources"), list) else [],
                }
            )

        ranked.sort(key=lambda item: float(item.get("confidence", 0.0) or 0.0), reverse=True)
        return {
            "generated_at": datetime.now().isoformat(),
            "shared_tradable_count": len(shared_keys),
            "active_order_flow_count": len(ranked),
            "active_order_flow": ranked[:20],
            "kraken_tradables": len(kraken_tradables),
            "capital_tradables": len(capital_tradables),
            "scope": "cross-exchange shared tradables only",
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
                "capital_symbol": item.get("capital_symbol"),
                "shared_tradable_count": order_flow_feed.get("shared_tradable_count", 0),
            }
            for trader in (self.kraken, self.capital):
                if trader is None or not hasattr(trader, "_feed_unified_decision_engine"):
                    continue
                try:
                    trader._feed_unified_decision_engine(symbol=symbol, side=side, score=confidence, metadata=metadata)  # type: ignore[attr-defined]
                except Exception as e:
                    logger.debug("Shared decision feed failed for %s: %s", symbol, e)

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
        now = time.time()
        last_tick_completed_at = float(getattr(self, "_last_tick_completed_at", 0.0) or 0.0)
        last_tick_started_at = float(getattr(self, "_last_tick_started_at", 0.0) or 0.0)
        tick_age_sec = (now - last_tick_completed_at) if last_tick_completed_at > 0 else None
        stale = bool(last_tick_completed_at > 0 and tick_age_sec is not None and tick_age_sec > READY_STALE_AFTER_SEC)
        alpaca_ok = self.alpaca is not None and not bool(self.alpaca_error or getattr(self.alpaca, "init_error", ""))
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        binance_ok = self.binance is not None and bool(binance_diag.get("network_ok", False))
        trading_ready = bool(self.kraken_ready and self.capital_ready)
        data_ready = bool(alpaca_ok and binance_ok)
        return {
            "ok": bool(trading_ready and data_ready and not stale),
            "service": "unified-market-trader",
            "trading_ready": trading_ready,
            "data_ready": data_ready,
            "stale": stale,
            "last_tick_started_at": datetime.fromtimestamp(last_tick_started_at).isoformat() if last_tick_started_at > 0 else None,
            "last_tick_completed_at": datetime.fromtimestamp(last_tick_completed_at).isoformat() if last_tick_completed_at > 0 else None,
            "last_tick_age_sec": round(float(tick_age_sec), 3) if tick_age_sec is not None else None,
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
        }

    def _latest_monitor_line(self) -> str:
        capital_line = getattr(self.capital, "_latest_monitor_line", "") if self.capital is not None else ""
        kraken_line = getattr(self.kraken, "_latest_monitor_line", "") if self.kraken is not None else ""
        return capital_line or kraken_line

    def _shared_portfolio_snapshot(self) -> Dict[str, Any]:
        """Build a shared live portfolio view for all active traders."""
        kraken_local = (
            self.kraken._get_capital_snapshot(include_shared=False)
            if self.kraken_ready and self.kraken is not None
            else {"equity": 0.0, "free_margin": 0.0, "budget": 0.0}
        )
        capital_local = (
            self.capital.get_capital_snapshot(include_shared=False)
            if self.capital_ready and self.capital is not None
            else {"equity_gbp": 0.0, "free_gbp": 0.0, "budget_gbp": 0.0}
        )
        gbp_usd = 1.27
        portfolio_equity_usd = float(kraken_local.get("equity", 0.0) or 0.0) + float(capital_local.get("equity_gbp", 0.0) or 0.0) * gbp_usd
        portfolio_free_usd = float(kraken_local.get("free_margin", 0.0) or 0.0) + float(capital_local.get("free_gbp", 0.0) or 0.0) * gbp_usd
        return {
            "portfolio_equity_usd": portfolio_equity_usd,
            "portfolio_free_usd": portfolio_free_usd,
            "portfolio_equity_gbp": portfolio_equity_usd / gbp_usd if gbp_usd > 0 else 0.0,
            "portfolio_free_gbp": portfolio_free_usd / gbp_usd if gbp_usd > 0 else 0.0,
            "kraken": {
                "equity": float(kraken_local.get("equity", 0.0) or 0.0),
                "free_margin": float(kraken_local.get("free_margin", 0.0) or 0.0),
                "budget": float(kraken_local.get("budget", 0.0) or 0.0),
            },
            "capital": {
                "equity_gbp": float(capital_local.get("equity_gbp", 0.0) or 0.0),
                "free_gbp": float(capital_local.get("free_gbp", 0.0) or 0.0),
                "budget_gbp": float(capital_local.get("budget_gbp", 0.0) or 0.0),
            },
        }

    def get_status_lines(self) -> List[str]:
        lines = [
            f"UNIFIED MARKET STATUS | runtime={(time.time() - self.start_time) / 60.0:.1f}m",
            "Markets armed: Kraken margin + Capital CFDs | CentralBeat fed by Kraken + Capital + Alpaca + Binance",
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
        alpaca_state = "ready" if self.alpaca is not None else "unavailable"
        lines.append(f"ALPACA: passive_{alpaca_state} | {self.alpaca_error or 'ok'}")
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        if self.binance is not None:
            lines.append(
                "BINANCE: "
                f"passive_ready={bool(binance_diag.get('network_ok', False))} "
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
            try:
                lines.extend(self.capital.status_lines())
            except Exception as e:
                if self._is_closed_stream_error(e):
                    try:
                        lines.extend(self._retry_with_safe_streams(lambda: self.capital.status_lines()))
                    except Exception as retry_error:
                        lines.append(f"CAPITAL: status_unavailable | {retry_error}")
                else:
                    lines.append(f"CAPITAL: status_unavailable | {e}")
        else:
            lines.append(f"CAPITAL: unavailable | {self.capital_error or 'not_ready'}")
        return lines

    def print_status(self) -> None:
        _safe_print()
        _safe_print("=" * 78)
        _safe_print(f"  UNIFIED MARKET TRADER | Runtime: {(time.time() - self.start_time) / 60.0:.1f}m")
        _safe_print("  Exchanges: Kraken Margin + Capital CFDs")
        _safe_print("  CentralBeat: Kraken + Capital + Alpaca + Binance feed fusion")
        preflight = self._build_preflight_report()
        _safe_print(
            "  Preflight: "
            f"{str(preflight.get('overall', 'unknown')).upper()} "
            f"critical={int(preflight.get('critical_failures', 0) or 0)} "
            f"warnings={int(preflight.get('warnings', 0) or 0)}"
        )
        _safe_print(f"  ALPACA: {'passive_ready' if self.alpaca is not None else 'passive_unavailable'} | {self.alpaca_error or 'ok'}")
        binance_diag = getattr(self, "_binance_diag", {}) or {}
        if self.binance is not None:
            _safe_print(
                "  BINANCE: "
                f"passive_ready={bool(binance_diag.get('network_ok', False))} "
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
            status_lines = []
            try:
                status_lines = self.capital.status_lines()
            except Exception as e:
                if self._is_closed_stream_error(e):
                    try:
                        status_lines = self._retry_with_safe_streams(lambda: self.capital.status_lines())
                    except Exception as retry_error:
                        status_lines = [f"CAPITAL status unavailable: {retry_error}"]
                else:
                    status_lines = [f"CAPITAL status unavailable: {e}"]
            for line in status_lines:
                _safe_print(f"  {line}")
        else:
            _safe_print(f"  CAPITAL unavailable: {self.capital_error or 'not_ready'}")
        _safe_print("=" * 78)
        _safe_print()

    def tick(self) -> Dict[str, Any]:
        self._last_tick_started_at = time.time()
        self._last_tick_error = ""
        self._ensure_exchanges()
        kraken_closed: List[dict] = []
        capital_closed: List[dict] = []
        if self.kraken_ready and self.kraken is not None:
            try:
                kraken_closed = self.kraken.tick()
            except Exception as e:
                if self._is_closed_stream_error(e):
                    try:
                        kraken_closed = self._retry_with_safe_streams(lambda: self.kraken.tick())
                        self.kraken_error = ""
                        logger.warning("Kraken tick recovered after safe-stream retry.")
                    except Exception as retry_error:
                        self.kraken_error = str(retry_error)
                        self.kraken_ready = False
                        self.kraken = None
                        self._last_tick_error = str(retry_error)
                        logger.error("Kraken tick failed after retry: %s", retry_error)
                else:
                    self.kraken_error = str(e)
                    self.kraken_ready = False
                    self.kraken = None
                    self._last_tick_error = str(e)
                    logger.error("Kraken tick failed: %s", e)
        if self.capital_ready and self.capital is not None:
            try:
                capital_closed = self.capital.tick()
            except Exception as e:
                if self._is_closed_stream_error(e):
                    try:
                        capital_closed = self._retry_with_safe_streams(lambda: self.capital.tick())
                        self.capital_error = ""
                        logger.warning("Capital tick recovered after safe-stream retry.")
                    except Exception as retry_error:
                        self.capital_error = str(retry_error)
                        self.capital_ready = False
                        self.capital = None
                        self._last_tick_error = str(retry_error)
                        logger.error("Capital tick failed after retry: %s", retry_error)
                else:
                    self.capital_error = str(e)
                    self.capital_ready = False
                    self.capital = None
                    self._last_tick_error = str(e)
                    logger.error("Capital tick failed: %s", e)
        payload = self._build_combined_payload()
        self._last_tick_completed_at = time.time()
        self._write_runtime_status_file()
        return {
            "kraken_closed": kraken_closed,
            "capital_closed": capital_closed,
            "payload": payload,
        }

    def run(self, interval_sec: float = 0.5) -> None:
        mode = "DRY RUN" if self.dry_run else "LIVE"
        _safe_print("=" * 78)
        _safe_print("  UNIFIED MARKET TRADER")
        _safe_print(f"  Mode: {mode}")
        _safe_print("  Execution venues: Kraken margin + Capital CFDs")
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
    parser.add_argument("--interval", type=float, default=0.5, help="Main loop interval in seconds")
    parser.add_argument(
        "--setup-kraken-cli",
        action="store_true",
        help="Install Kraken CLI before startup if it is missing (uses Kraken's official installer).",
    )
    args = parser.parse_args()

    trader = UnifiedMarketTrader(dry_run=args.dry_run, setup_kraken_cli=args.setup_kraken_cli)
    trader.run(interval_sec=max(0.25, float(args.interval)))


if __name__ == "__main__":
    main()
