#!/usr/bin/env python3
from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

from alpaca_capital_style_trader import AlpacaCapitalStyleTrader


logger = logging.getLogger("alpaca_capital_runner")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def main() -> None:
    parser = argparse.ArgumentParser(description="Alpaca capital-style stock trader")
    parser.add_argument("--interval", type=float, default=2.0, help="Main loop interval in seconds")
    parser.add_argument("--free-assets", action="store_true", help="Close existing Alpaca spot positions before trading")
    parser.add_argument("--free-assets-only", action="store_true", help="Close existing Alpaca spot positions and exit")
    args = parser.parse_args()

    trader = AlpacaCapitalStyleTrader()
    print("=" * 78)
    print("  ALPACA CAPITAL-STYLE RUNNER")
    print("  Venue: Alpaca stocks")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 78)

    if not trader.enabled:
        print(f"Alpaca trader unavailable: {trader.init_error or 'not_authenticated'}")
        return

    if args.free_assets or args.free_assets_only:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Freeing Alpaca assets...", flush=True)
        liquidated = trader.free_existing_assets()
        print(f"Freed positions: {len(liquidated)}")
        for item in liquidated:
            print(
                f"  {item.get('symbol', '?')} {item.get('side', '?')} qty={float(item.get('qty', 0.0) or 0.0):.4f} "
                f"order={item.get('order_id', '')}"
            )
        if args.free_assets_only:
            return

    try:
        while True:
            tick_started = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Alpaca tick starting...", flush=True)
            trader.tick()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Alpaca tick complete ({time.time() - tick_started:.1f}s)", flush=True)
            for line in trader.status_lines():
                print(line)
            print("=" * 78)
            time.sleep(max(0.5, float(args.interval)))
    except KeyboardInterrupt:
        print("\nAlpaca capital-style runner stopped.")


if __name__ == "__main__":
    main()
