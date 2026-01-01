#!/usr/bin/env python3
"""
Summarize smoke_test_probability_matrix JSON outputs or benchmark summaries.
Usage:
  python tools/summarize_smoke.py path/to/file.json
"""

import argparse
import json
from pathlib import Path

def summarize(path: Path) -> None:
    data = json.loads(path.read_text())

    # Support either raw smoke_test output or trimmed benchmark summary
    results = data.get("results", data)
    start_time = results.get("start_time")
    end_time = results.get("end_time")
    duration_minutes = results.get("duration_minutes")
    starting_capital = results.get("starting_capital") or data.get("starting_capital")
    ending_capital = results.get("ending_capital") or data.get("ending_capital")
    total_pnl = results.get("total_pnl")
    total_pnl_pct = results.get("total_pnl_pct")
    total_trades = results.get("total_trades")
    win_rate = results.get("win_rate")
    profit_factor = results.get("profit_factor")

    hourly = None
    daily = None
    weekly = None
    if total_pnl is not None and duration_minutes:
        hourly = (total_pnl / duration_minutes) * 60
        daily = hourly * 24
        weekly = daily * 7

    print(f"File: {path}")
    if start_time and end_time:
        print(f"  Window: {start_time} → {end_time} ({duration_minutes:.1f}m)")
    if starting_capital is not None and ending_capital is not None:
        print(f"  Capital: start={starting_capital:.2f}, end={ending_capital:.2f}, pnl={total_pnl:+.2f} ({total_pnl_pct:+.2f}%)")
    if total_trades is not None:
        print(f"  Trades: {total_trades}, win_rate={win_rate:.2f}%, profit_factor={profit_factor}")
    if hourly is not None:
        print(f"  Projections: hourly={hourly:+.2f}, daily={daily:+.2f}, weekly={weekly:+.2f}")

    params = data.get("parameters") or {}
    if params:
        print(f"  Params: position_pct={params.get('position_pct')}, position_size_fallback={params.get('position_size_fallback')}, minutes={params.get('minutes')}, fee_rate={params.get('fee_rate')}, pairs_fetched={params.get('pairs_fetched')} / {params.get('pairs_target')}")


def main():
    parser = argparse.ArgumentParser(description="Summarize smoke test or benchmark JSON")
    parser.add_argument("path", type=str, help="Path to JSON file")
    args = parser.parse_args()

    path = Path(args.path)
    if not path.exists():
        raise SystemExit(f"File not found: {path}")

    summarize(path)


if __name__ == "__main__":
    main()
