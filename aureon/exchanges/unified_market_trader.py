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
import json
import logging
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

from kraken_margin_penny_trader import KrakenMarginArmyTrader
from capital_cfd_trader import CAPITAL_UNIVERSE, CapitalCFDTrader

try:
    from aureon.utils.aureon_sero_client import get_sero_client
except Exception:
    try:
        from aureon_sero_client import get_sero_client
    except Exception:
        get_sero_client = None  # type: ignore[assignment]

logger = logging.getLogger("unified_market_trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8790
EXCHANGE_REINIT_INTERVAL_SEC = 30.0
AURIS_FEED_MIN_INTERVAL_SEC = 45.0
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
        self.start_time = time.time()
        self.kraken_ready = False
        self.capital_ready = False
        self.kraken_error = ""
        self.capital_error = ""
        self._last_kraken_init_attempt = 0.0
        self._last_capital_init_attempt = 0.0
        self._last_kraken_startup_attempt = 0.0
        self._last_capital_startup_attempt = 0.0
        self._latest_dashboard_payload: Dict[str, Any] = {}
        self._shared_market_feed: Dict[str, float] = {}
        self._shared_market_feed_at: float = 0.0
        self._last_auris_feed_at: float = 0.0
        self._local_dashboard_server: ThreadingHTTPServer | None = None
        self._local_dashboard_thread: threading.Thread | None = None
        if self.setup_kraken_cli:
            self._ensure_kraken_cli()
        self._init_exchanges()
        self._start_local_dashboard_server()

    def _ensure_kraken_cli(self) -> None:
        if shutil.which("kraken"):
            logger.info("Kraken CLI detected in PATH.")
            return
        logger.info("Kraken CLI not found. Running installer...")
        try:
            subprocess.run(
                KRAKEN_CLI_INSTALL_CMD,
                shell=True,
                check=True,
                executable="/bin/bash",
            )
            logger.info("Kraken CLI installer completed.")
            if not shutil.which("kraken"):
                logger.warning("Kraken CLI install finished but binary was not found in PATH.")
        except Exception as e:
            logger.error("Kraken CLI installer failed: %s", e)

    def _init_exchanges(self) -> None:
        self._init_kraken(force=True)
        self._init_capital(force=True)

    def _init_kraken(self, force: bool = False) -> None:
        now = time.time()
        if not force and now - self._last_kraken_init_attempt < EXCHANGE_REINIT_INTERVAL_SEC:
            return
        self._last_kraken_init_attempt = now
        try:
            self.kraken = KrakenMarginArmyTrader(dry_run=self.dry_run)
            self.kraken_error = ""
        except Exception as e:
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

    def _ensure_exchanges(self) -> None:
        if self.kraken is None:
            self._init_kraken()
        elif not self.kraken_ready:
            self._startup_kraken()
        if self.capital is None:
            self._init_capital()
        elif not self.capital_ready:
            self._startup_capital()

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

    def _build_combined_payload(self) -> Dict[str, Any]:
        kraken_payload = self.kraken.get_local_dashboard_state() if self.kraken_ready and self.kraken is not None else {
            "ok": False,
            "exchange": "kraken",
            "error": self.kraken_error or "not_ready",
            "positions": [],
            "status_lines": [f"KRAKEN unavailable: {self.kraken_error or 'not_ready'}"],
        }
        capital_payload = self.capital.get_dashboard_payload() if self.capital_ready and self.capital is not None else {
            "ok": False,
            "exchange": "capital",
            "error": self.capital_error or "not_ready",
            "positions": [],
            "status_lines": [f"CAPITAL unavailable: {self.capital_error or 'not_ready'}"],
            "stats": {},
        }
        shared_market_feed = self._sync_shared_market_feed(kraken_payload, capital_payload)
        order_flow_feed = self._build_global_order_flow_feed(kraken_payload, capital_payload, shared_market_feed)
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
            "shared_order_flow": order_flow_feed,
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
        self._latest_dashboard_payload = payload
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

    def _sync_shared_market_feed(self, kraken_payload: Dict[str, Any], capital_payload: Dict[str, Any]) -> Dict[str, Any]:
        boosts: Dict[str, float] = {}
        aliases: Dict[str, List[str]] = {}

        def push(symbol: Any, confidence: Any) -> None:
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
            boosts[normalized] = max(boosts.get(normalized, 0.0), conf)
            if raw_symbol:
                known = aliases.setdefault(normalized, [])
                if raw_symbol not in known:
                    known.append(raw_symbol)

        for candidate in kraken_payload.get("candidate_snapshot", [])[:8]:
            if isinstance(candidate, dict):
                push(candidate.get("symbol") or candidate.get("pair"), self._extract_candidate_confidence(candidate))
        kraken_decision = kraken_payload.get("decision_snapshot", {})
        if isinstance(kraken_decision, dict):
            decision = kraken_decision.get("decision", {}) if isinstance(kraken_decision.get("decision"), dict) else {}
            push(kraken_decision.get("symbol"), decision.get("confidence", 0.0))

        for candidate in capital_payload.get("candidate_snapshot", [])[:8]:
            if isinstance(candidate, dict):
                push(candidate.get("symbol"), self._extract_candidate_confidence(candidate))
        capital_target = capital_payload.get("target_snapshot", {})
        if isinstance(capital_target, dict):
            push(capital_target.get("symbol"), self._extract_candidate_confidence(capital_target))

        self._shared_market_feed = boosts
        self._shared_market_feed_at = time.time()

        for trader in (self.kraken, self.capital):
            if trader is None:
                continue
            try:
                trader._hive_boosts = dict(boosts)  # type: ignore[attr-defined]
            except Exception:
                continue

        return {
            "symbols": dict(boosts),
            "aliases": dict(aliases),
            "count": len(boosts),
            "generated_at": datetime.now().isoformat(),
        }

    def _normalize_symbol(self, symbol: Any) -> str:
        raw = str(symbol or "").upper().strip()
        if not raw:
            return ""
        for needle in ("PERP", ".D", "-CFD"):
            raw = raw.replace(needle, "")
        alnum = "".join(ch for ch in raw if ch.isalnum())
        return SYMBOL_ALIASES.get(alnum, alnum)

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
        shared_market_feed: Dict[str, Any],
    ) -> Dict[str, Any]:
        kraken_tradables = self._kraken_tradable_symbols()
        capital_tradables = self._capital_tradable_symbols()
        shared_keys = sorted(set(kraken_tradables.keys()) & set(capital_tradables.keys()))

        symbols_conf = shared_market_feed.get("symbols", {}) if isinstance(shared_market_feed, dict) else {}
        ranked: List[Dict[str, Any]] = []
        for normalized in shared_keys:
            confidence = float(symbols_conf.get(normalized, 0.0) or 0.0)
            if confidence <= 0.0:
                continue
            capital_symbol = capital_tradables.get(normalized, normalized)
            side = "BUY"
            if "SHORT" in capital_symbol.upper():
                side = "SELL"
            ranked.append(
                {
                    "symbol": normalized,
                    "kraken_symbol": kraken_tradables.get(normalized, normalized),
                    "capital_symbol": capital_symbol,
                    "side": side,
                    "confidence": max(0.0, min(1.0, confidence)),
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
        return dict(self._build_combined_payload())

    def _latest_monitor_line(self) -> str:
        capital_line = getattr(self.capital, "_latest_monitor_line", "") if self.capital is not None else ""
        kraken_line = getattr(self.kraken, "_latest_monitor_line", "") if self.kraken is not None else ""
        return capital_line or kraken_line

    def get_status_lines(self) -> List[str]:
        lines = [
            f"UNIFIED MARKET STATUS | runtime={(time.time() - self.start_time) / 60.0:.1f}m",
            "Markets armed: Kraken margin + Capital CFDs",
        ]
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
        _safe_print("  Exchanges: Kraken Margin + Capital CFDs")
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

    def tick(self) -> Dict[str, Any]:
        self._ensure_exchanges()
        kraken_closed: List[dict] = []
        capital_closed: List[dict] = []
        if self.kraken_ready and self.kraken is not None:
            try:
                kraken_closed = self.kraken.tick()
            except Exception as e:
                self.kraken_error = str(e)
                self.kraken_ready = False
                self.kraken = None
                logger.error("Kraken tick failed: %s", e)
        if self.capital_ready and self.capital is not None:
            try:
                capital_closed = self.capital.tick()
            except Exception as e:
                self.capital_error = str(e)
                self.capital_ready = False
                self.capital = None
                logger.error("Capital tick failed: %s", e)
        payload = self._build_combined_payload()
        return {
            "kraken_closed": kraken_closed,
            "capital_closed": capital_closed,
            "payload": payload,
        }

    def run(self, interval_sec: float = 2.0) -> None:
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
