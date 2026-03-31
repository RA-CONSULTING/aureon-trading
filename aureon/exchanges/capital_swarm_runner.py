#!/usr/bin/env python3
"""
Capital-only swarm runner.

Runs the Capital.com CFD swarm trader without booting the wider unified
exchange stack, so the process stays focused on Capital margin trading.
"""

from __future__ import annotations

import argparse
import logging
import json
import os
import time
from datetime import datetime
from pathlib import Path

from capital_cfd_trader import CapitalCFDTrader


logger = logging.getLogger("capital_swarm_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
HEARTBEAT_PATH = Path(os.getenv("AUREON_HEARTBEAT_FILE", os.path.join(os.path.dirname(__file__), "..", "..", ".aureon_heartbeat"))).resolve()


class CapitalSwarmRunner:
    def __init__(self) -> None:
        self.trader = CapitalCFDTrader()
        self.started_at = time.time()

    def write_heartbeat(self) -> None:
        payload = {
            "system": "capital_swarm_runner",
            "ts": time.time(),
            "runtime_sec": time.time() - self.started_at,
            "enabled": bool(self.trader.enabled),
            "init_error": str(getattr(self.trader, "init_error", "") or ""),
            "positions": len(getattr(self.trader, "positions", []) or []),
            "shadows": len(getattr(self.trader, "shadow_trades", []) or []),
        }
        HEARTBEAT_PATH.parent.mkdir(parents=True, exist_ok=True)
        HEARTBEAT_PATH.write_text(json.dumps(payload), encoding="utf-8")
        if hasattr(self.trader, "mark_deadman_heartbeat"):
            self.trader.mark_deadman_heartbeat()

    def print_status(self) -> None:
        print()
        print("=" * 78)
        print(f"  CAPITAL SWARM RUNNER | Runtime: {(time.time() - self.started_at) / 60.0:.1f}m")
        print("  Venue: Capital.com CFDs")
        print("-" * 78)
        if self.trader.enabled:
            for line in self.trader.status_lines():
                print(f"  {line}")
        else:
            reason = self.trader.init_error or getattr(getattr(self.trader, "client", None), "init_error", "") or "not_ready"
            print(f"  CAPITAL unavailable: {reason}")
        print("=" * 78)
        print()

    def run(self, interval_sec: float = 2.0) -> None:
        print("=" * 78)
        print("  CAPITAL SWARM RUNNER")
        print("  Venue: Capital.com CFDs only")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 78)

        if not self.trader.enabled:
            reason = self.trader.init_error or getattr(getattr(self.trader, "client", None), "init_error", "") or "client_disabled_or_blocked"
            print(f"Capital trader not available: {reason}")
            return

        try:
            while True:
                tick_started = time.time()
                self.write_heartbeat()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Capital tick starting...", flush=True)
                self.trader.tick()
                self.write_heartbeat()
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Capital tick complete "
                    f"({time.time() - tick_started:.1f}s)",
                    flush=True,
                )
                self.print_status()
                time.sleep(interval_sec)
        except KeyboardInterrupt:
            print("\nCapital swarm runner stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Capital.com swarm-only trader")
    parser.add_argument("--interval", type=float, default=2.0, help="Main loop interval in seconds")
    args = parser.parse_args()

    runner = CapitalSwarmRunner()
    runner.run(interval_sec=max(0.5, float(args.interval)))


if __name__ == "__main__":
    main()
