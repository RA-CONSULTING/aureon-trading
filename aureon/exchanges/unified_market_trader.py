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
        self.wfile.write(body)


class UnifiedMarketTrader:
    def __init__(self, dry_run: bool = False):
        os.environ.setdefault("AUREON_DISABLE_LOCAL_DASHBOARD", "1")
        self.kraken = KrakenMarginArmyTrader(dry_run=dry_run)
        self.capital = CapitalCFDTrader()
        self.start_time = time.time()
        self.kraken_ready = False
        self.capital_ready = bool(getattr(self.capital, "enabled", False))
        self.kraken_error = ""
        self.capital_error = ""
        self._latest_dashboard_payload: Dict[str, Any] = {}
        self._local_dashboard_server: ThreadingHTTPServer | None = None
        self._local_dashboard_thread: threading.Thread | None = None
        self._start_local_dashboard_server()

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

    def _build_combined_payload(self) -> Dict[str, Any]:
        kraken_payload = self.kraken.get_local_dashboard_state() if self.kraken_ready else {
            "ok": False,
            "exchange": "kraken",
            "error": self.kraken_error or "not_ready",
            "positions": [],
            "status_lines": [f"KRAKEN unavailable: {self.kraken_error or 'not_ready'}"],
        }
        capital_payload = self.capital.get_dashboard_payload() if self.capital_ready else {
            "ok": False,
            "exchange": "capital",
            "error": self.capital_error or "not_ready",
            "positions": [],
            "status_lines": [f"CAPITAL unavailable: {self.capital_error or 'not_ready'}"],
            "stats": {},
        }
        combined_status = self.get_status_lines()
        payload = {
            "ok": True,
            "source": "unified-market-trader",
            "generated_at": datetime.now().isoformat(),
            "runtime_minutes": (time.time() - self.start_time) / 60.0,
            "kraken": kraken_payload,
            "capital": capital_payload,
            "status_lines": combined_status[-24:],
            "latest_monitor_line": self._latest_monitor_line(),
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

    def get_local_dashboard_state(self) -> Dict[str, Any]:
        return dict(self._build_combined_payload())

    def _latest_monitor_line(self) -> str:
        capital_line = getattr(self.capital, "_latest_monitor_line", "")
        kraken_line = getattr(self.kraken, "_latest_monitor_line", "")
        return capital_line or kraken_line

    def get_status_lines(self) -> List[str]:
        lines = [
            f"UNIFIED MARKET STATUS | runtime={(time.time() - self.start_time) / 60.0:.1f}m",
            "Markets armed: Kraken margin + Capital CFDs",
        ]
        if self.kraken_ready:
            lines.extend(self.kraken._latest_status_lines[-10:] if getattr(self.kraken, "_latest_status_lines", None) else [])
        else:
            lines.append(f"KRAKEN: unavailable | {self.kraken_error or 'not_ready'}")
        if self.capital_ready:
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
        if self.kraken_ready:
            for line in self.kraken._latest_status_lines[-10:]:
                print(f"  {line}")
        else:
            print(f"  KRAKEN unavailable: {self.kraken_error or 'not_ready'}")
        print("-" * 78)
        print("  [CAPITAL]")
        if self.capital_ready:
            for line in self.capital.status_lines():
                print(f"  {line}")
        else:
            print(f"  CAPITAL unavailable: {self.capital_error or 'not_ready'}")
        print("=" * 78)
        print()

    def tick(self) -> Dict[str, Any]:
        kraken_closed: List[dict] = []
        capital_closed: List[dict] = []
        if self.kraken_ready:
            try:
                kraken_closed = self.kraken.tick()
            except Exception as e:
                self.kraken_error = str(e)
                self.kraken_ready = False
                logger.error("Kraken tick failed: %s", e)
        if self.capital_ready:
            try:
                capital_closed = self.capital.tick()
            except Exception as e:
                self.capital_error = str(e)
                self.capital_ready = False
                logger.error("Capital tick failed: %s", e)
        payload = self._build_combined_payload()
        return {
            "kraken_closed": kraken_closed,
            "capital_closed": capital_closed,
            "payload": payload,
        }

    def run(self, interval_sec: float = 2.0) -> None:
        mode = "DRY RUN" if self.kraken.dry_run else "LIVE"
        print("=" * 78)
        print("  UNIFIED MARKET TRADER")
        print(f"  Mode: {mode}")
        print("  Execution venues: Kraken margin + Capital CFDs")
        print("  Monitoring: local-first dashboard + terminal telemetry")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 78)

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

        try:
            self.capital.status_lines()
            self.capital_ready = bool(getattr(self.capital, "enabled", False))
            if not self.capital_ready and not self.capital_error:
                self.capital_error = "client_disabled_or_blocked"
        except Exception as e:
            self.capital_ready = False
            self.capital_error = str(e)
            logger.error("Capital startup unavailable: %s", e)

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
