#!/usr/bin/env python3
"""
Ingest Federal Reserve Economic Data (FRED) into Aureon's global history DB.

Uses the free FRED API (fredapi library) and stores data in the
macro_indicators table.  Supports resumable watermarks so re-runs only
fetch new observations.

Usage examples:
    # Ingest all default series (full history back to 1970)
    python scripts/python/ingest_fred.py --fred-key YOUR_KEY

    # Ingest only interest-rate series
    python scripts/python/ingest_fred.py --category rates

    # Ingest specific series
    python scripts/python/ingest_fred.py --series FEDFUNDS,UNRATE,CPIAUCSL

    # Fresh start (ignore watermarks)
    python scripts/python/ingest_fred.py --no-resume
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Repo-root bootstrap (same pattern as other scripts/python/*.py)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass

from aureon.core import aureon_global_history_db as ghdb

# ---------------------------------------------------------------------------
# Default FRED series organised by category
# ---------------------------------------------------------------------------
SERIES_BY_CATEGORY: Dict[str, List[str]] = {
    "rates": [
        "FEDFUNDS",       # Fed Funds Rate
        "DFF",            # Daily Fed Funds
        "DFEDTARU",       # Fed Funds Upper Target
        "DGS1",           # 1-Year Treasury
        "DGS2",           # 2-Year Treasury
        "DGS5",           # 5-Year Treasury
        "DGS10",          # 10-Year Treasury
        "DGS30",          # 30-Year Treasury
        "T10Y2Y",         # 10Y-2Y Spread (Yield Curve)
        "T10Y3M",         # 10Y-3M Spread
        "BAMLH0A0HYM2",  # High Yield Spread
        "AAA",            # Moody's AAA Corporate Bond Yield
        "BAA",            # Moody's BAA Corporate Bond Yield
    ],
    "gdp": [
        "GDP",                # Nominal GDP
        "GDPC1",              # Real GDP
        "A191RL1Q225SBEA",    # Real GDP % Change
        "GDPPOT",             # Potential GDP
    ],
    "inflation": [
        "CPIAUCSL",           # CPI All Urban Consumers
        "CPILFESL",           # Core CPI (less food & energy)
        "PCEPI",              # PCE Price Index
        "PCEPILFE",           # Core PCE
        "CPALTT01USM657N",    # CPI Year-over-Year
        "GOLDAMGBD228NLBM",   # Gold Price (London Fix)
        "DCOILWTICO",         # WTI Crude Oil
    ],
    "employment": [
        "UNRATE",   # Unemployment Rate
        "PAYEMS",   # Nonfarm Payrolls
        "ICSA",     # Initial Jobless Claims
        "JTSJOL",   # Job Openings (JOLTS)
        "U6RATE",   # U-6 Unemployment
    ],
    "money": [
        "M2SL",       # M2 Money Supply
        "WALCL",      # Fed Balance Sheet
        "TOTRESNS",   # Total Reserves
    ],
    "housing": [
        "CSUSHPINSA",    # Case-Shiller Home Price Index
        "HOUST",         # Housing Starts
        "MORTGAGE30US",  # 30-Year Mortgage Rate
    ],
    "consumer": [
        "UMCSENT",   # Michigan Consumer Sentiment
        "RSAFS",     # Retail Sales
        "INDPRO",    # Industrial Production
        "DGORDER",   # Durable Goods Orders
    ],
    "financial": [
        "VIXCLS",      # VIX
        "DTWEXBGS",    # Trade Weighted USD Index
        "SP500",       # S&P 500
        "NASDAQCOM",   # NASDAQ Composite
        "DEXUSEU",     # EUR/USD
        "DEXJPUS",     # JPY/USD
        "DEXUSUK",     # GBP/USD
    ],
    "global": [
        "GFDEBTN",   # Federal Debt Total
        "FYFSD",     # Federal Surplus/Deficit
        "STLFSI4",   # St. Louis Financial Stress Index
    ],
}

# Reverse lookup: series_id -> category
_SERIES_CATEGORY: Dict[str, str] = {}
for _cat, _ids in SERIES_BY_CATEGORY.items():
    for _sid in _ids:
        _SERIES_CATEGORY[_sid] = _cat

ALL_DEFAULT_SERIES: List[str] = [
    sid for ids in SERIES_BY_CATEGORY.values() for sid in ids
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _ts_ms(dt: datetime) -> int:
    """Convert a datetime to epoch milliseconds (UTC)."""
    return int(dt.replace(tzinfo=timezone.utc).timestamp() * 1000)


def _iso_to_date(s: str) -> str:
    """Validate and return an ISO date string (YYYY-MM-DD)."""
    datetime.strptime(s, "%Y-%m-%d")
    return s


def _watermark_name(series_id: str) -> str:
    return f"fred:{series_id}"


# ---------------------------------------------------------------------------
# Core ingestion
# ---------------------------------------------------------------------------

def ingest_series(
    fred,
    conn,
    series_id: str,
    start: str,
    end: str,
    use_watermark: bool = True,
) -> int:
    """Fetch one FRED series and store observations. Returns row count."""

    # Resolve watermark-based start if resuming
    effective_start = start
    if use_watermark:
        wm = ghdb.get_watermark_ms(conn, _watermark_name(series_id))
        if wm is not None:
            # Start one day after the watermark to avoid re-fetching
            wm_date = datetime.utcfromtimestamp(wm / 1000).strftime("%Y-%m-%d")
            if wm_date > effective_start:
                effective_start = wm_date

    # Fetch metadata
    try:
        info = fred.get_series_info(series_id)
    except Exception as exc:
        print(f"  [WARN] Could not fetch metadata for {series_id}: {exc}")
        info = {}

    series_name = info.get("title", series_id) if isinstance(info, dict) else getattr(info, "title", series_id)
    frequency = info.get("frequency_short", "") if isinstance(info, dict) else getattr(info, "frequency_short", "")
    units = info.get("units_short", "") if isinstance(info, dict) else getattr(info, "units_short", "")
    category = _SERIES_CATEGORY.get(series_id, "other")

    # Fetch observations
    try:
        data = fred.get_series(
            series_id,
            observation_start=effective_start,
            observation_end=end,
        )
    except Exception as exc:
        print(f"  [ERROR] Failed to fetch {series_id}: {exc}")
        return 0

    if data is None or data.empty:
        print(f"  {series_id}: 0 new observations")
        return 0

    inserted = 0
    max_obs_ms = 0
    batch_count = 0
    now_ms = int(time.time() * 1000)

    for obs_date, value in data.items():
        # Skip NaN values (FRED uses NaN for missing observations)
        if value != value:  # NaN check
            continue

        obs_dt = obs_date.to_pydatetime()
        obs_ms = _ts_ms(obs_dt)

        row = {
            "provider": "fred",
            "series_id": series_id,
            "series_name": series_name,
            "category": category,
            "region": "US",
            "frequency": frequency,
            "units": units,
            "observation_date_ms": obs_ms,
            "value": float(value),
            "ingested_at_ms": now_ms,
            "raw_json": json.dumps(
                {
                    "series_id": series_id,
                    "date": obs_dt.strftime("%Y-%m-%d"),
                    "value": float(value),
                },
                default=str,
            ),
        }

        if ghdb.insert_macro_indicator(conn, row):
            inserted += 1

        if obs_ms > max_obs_ms:
            max_obs_ms = obs_ms

        batch_count += 1
        if batch_count % 500 == 0:
            conn.commit()

    # Final commit for remaining rows
    if batch_count % 500 != 0:
        conn.commit()

    # Update watermark
    if max_obs_ms > 0 and use_watermark:
        ghdb.set_watermark_ms(conn, _watermark_name(series_id), max_obs_ms)
        conn.commit()

    print(f"  {series_id}: {inserted} inserted ({batch_count} processed, {data.shape[0]} total obs)")
    return inserted


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest FRED macro indicators into Aureon global history DB.",
    )
    p.add_argument("--db", default=None, help="SQLite DB path override")
    p.add_argument(
        "--no-resume",
        action="store_true",
        help="Ignore watermarks and re-fetch from --start",
    )
    p.add_argument("--start", default="1970-01-01", help="ISO start date (default: 1970-01-01)")
    p.add_argument("--end", default=None, help="ISO end date (default: today)")
    p.add_argument(
        "--series",
        default=None,
        help="Comma-separated FRED series IDs (overrides defaults)",
    )
    p.add_argument(
        "--category",
        default="all",
        help="Category filter: rates,gdp,inflation,employment,money,housing,consumer,financial,global,all",
    )
    p.add_argument(
        "--fred-key",
        default=None,
        help="FRED API key (or set env FRED_API_KEY)",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # ---- API key ----
    api_key = args.fred_key or os.getenv("FRED_API_KEY")
    if not api_key:
        print("ERROR: FRED API key required. Use --fred-key or set FRED_API_KEY env var.")
        print("  Get a free key at https://fred.stlouisfed.org/docs/api/api_key.html")
        sys.exit(1)

    try:
        from fredapi import Fred
    except ImportError:
        print("ERROR: fredapi not installed. Run:  pip install fredapi")
        sys.exit(1)

    fred = Fred(api_key=api_key)

    # ---- Dates ----
    start = _iso_to_date(args.start)
    end = _iso_to_date(args.end) if args.end else datetime.utcnow().strftime("%Y-%m-%d")

    # ---- Series selection ----
    if args.series:
        series_list = [s.strip().upper() for s in args.series.split(",") if s.strip()]
    elif args.category == "all":
        series_list = list(ALL_DEFAULT_SERIES)
    else:
        cats = [c.strip().lower() for c in args.category.split(",") if c.strip()]
        series_list = []
        for cat in cats:
            if cat not in SERIES_BY_CATEGORY:
                print(f"WARNING: Unknown category '{cat}', skipping. "
                      f"Valid: {', '.join(SERIES_BY_CATEGORY.keys())}")
                continue
            series_list.extend(SERIES_BY_CATEGORY[cat])

    if not series_list:
        print("No series to ingest.")
        sys.exit(0)

    # ---- Connect ----
    conn = ghdb.connect(args.db)
    paths = ghdb.resolve_paths(args.db)
    print(f"DB: {paths.db_path}")
    print(f"Period: {start} to {end}")
    print(f"Series: {len(series_list)} series, resume={'off' if args.no_resume else 'on'}")
    print()

    use_watermark = not args.no_resume
    total_inserted = 0
    errors = 0

    for i, sid in enumerate(series_list, 1):
        print(f"[{i}/{len(series_list)}] {sid}")
        try:
            n = ingest_series(fred, conn, sid, start, end, use_watermark=use_watermark)
            total_inserted += n
        except Exception as exc:
            print(f"  [ERROR] {sid}: {exc}")
            errors += 1

        # FRED rate limit: 120 req/min. Sleep 0.5s between series to stay safe.
        if i < len(series_list):
            time.sleep(0.5)

    print()
    print(f"Done. {total_inserted} observations inserted across {len(series_list)} series "
          f"({errors} errors).")

    conn.close()


if __name__ == "__main__":
    main()
