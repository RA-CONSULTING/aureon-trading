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
import json
import logging
import os
import threading
import time
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List

from kraken_margin_penny_trader import KrakenMarginArmyTrader
from capital_cfd_trader import CapitalCFDTrader

logger = logging.getLogger("unified_market_trader")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

LOCAL_HOST = "127.0.0.1"
LOCAL_PORT = 8790
EXCHANGE_REINIT_INTERVAL_SEC = 30.0


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
    def __init__(self, dry_run: bool = False):
        os.environ.setdefault("AUREON_DISABLE_LOCAL_DASHBOARD", "1")
        self.dry_run = dry_run
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
        self._local_dashboard_server: ThreadingHTTPServer | None = None
        self._local_dashboard_thread: threading.Thread | None = None
        self._init_exchanges()
        self._start_local_dashboard_server()

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
        print()
        print("=" * 78)
        print(f"  UNIFIED MARKET TRADER | Runtime: {(time.time() - self.start_time) / 60.0:.1f}m")
        print("  Exchanges: Kraken Margin + Capital CFDs")
        print("-" * 78)
        print("  [KRAKEN]")
        if self.kraken_ready and self.kraken is not None:
            for line in self.kraken._latest_status_lines[-10:]:
                print(f"  {line}")
        else:
            print(f"  KRAKEN unavailable: {self.kraken_error or 'not_ready'}")
        print("-" * 78)
        print("  [CAPITAL]")
        if self.capital_ready and self.capital is not None:
            for line in self.capital.status_lines():
                print(f"  {line}")
        else:
            print(f"  CAPITAL unavailable: {self.capital_error or 'not_ready'}")
        print("=" * 78)
        print()

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
        print("=" * 78)
        print("  UNIFIED MARKET TRADER")
        print(f"  Mode: {mode}")
        print("  Execution venues: Kraken margin + Capital CFDs")
        print("  Monitoring: local-first dashboard + terminal telemetry")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 78)

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
            print("\nUnified market trader stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Unified Kraken + Capital market trader")
    parser.add_argument("--dry-run", action="store_true", help="Run Kraken in dry-run mode")
    parser.add_argument("--interval", type=float, default=2.0, help="Main loop interval in seconds")
    args = parser.parse_args()

    trader = UnifiedMarketTrader(dry_run=args.dry_run)
    trader.run(interval_sec=max(0.5, float(args.interval)))


if __name__ == "__main__":
    main()
