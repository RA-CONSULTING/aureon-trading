#!/usr/bin/env python3
"""
Capital-only swarm runner.

Runs the Capital.com CFD swarm trader without booting the wider unified
exchange stack, so the process stays focused on Capital margin trading.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

from capital_cfd_trader import CapitalCFDTrader


logger = logging.getLogger("capital_swarm_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


class CapitalSwarmRunner:
    def __init__(self) -> None:
        self.trader = CapitalCFDTrader()
        self.started_at = time.time()

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
            print(f"  CAPITAL unavailable: {self.trader.init_error or 'not_ready'}")
        print("=" * 78)
        print()

    def run(self, interval_sec: float = 2.0) -> None:
        print("=" * 78)
        print("  CAPITAL SWARM RUNNER")
        print("  Venue: Capital.com CFDs only")
        print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 78)

        if not self.trader.enabled:
            print(f"Capital trader not available: {self.trader.init_error or 'client_disabled_or_blocked'}")
            return

        try:
            while True:
                tick_started = time.time()
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Capital tick starting...", flush=True)
                self.trader.tick()
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
