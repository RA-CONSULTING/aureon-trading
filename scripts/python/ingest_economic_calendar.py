#!/usr/bin/env python3
"""
Ingest economic calendar events and geopolitical data into Aureon's
single-file global history SQLite database.

Data sources (all FREE public APIs / hard-coded seed data):
  1. FMP Economic Calendar  (FMP_API_KEY, free tier 250 calls/day)
  2. FOMC / Central Bank Decisions  (hard-coded + FMP)
  3. Earnings Calendar  (FMP)
  4. IPO Calendar  (FMP)
  5. Dividends Calendar  (FMP)
  6. Geopolitical Events  (hard-coded seed + optional World News API)

Hard-coded geopolitical events and FOMC dates load without any API key.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Repo-root / sys.path setup (same pattern as other scripts/python/ files)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(_REPO_ROOT / ".env")
except Exception:
    pass

from aureon.core import aureon_global_history_db as db

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _json_safe(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=True, separators=(",", ":"), default=str)
    except Exception:
        return json.dumps({"_unserializable": True, "repr": repr(obj)})


def _iso_to_ms(date_str: str) -> int:
    """Parse an ISO date (or datetime) string to epoch milliseconds (UTC)."""
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    # Last resort: try fromisoformat (handles timezone offsets on 3.11+)
    try:
        dt = datetime.fromisoformat(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return int(dt.timestamp() * 1000)
    except Exception:
        raise ValueError(f"Cannot parse date: {date_str!r}")


def _event_hash(text: str) -> str:
    """Short deterministic hash for dedup."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _today_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# FMP API helper
# ---------------------------------------------------------------------------

_FMP_BASE = "https://financialmodelingprep.com/api/v3"
_FMP_RATE_DELAY = 0.5  # seconds between FMP requests


def _fmp_get(endpoint: str, params: Dict[str, str], api_key: str) -> Optional[List[Dict]]:
    """GET a FMP endpoint, return parsed JSON list or None on failure."""
    try:
        import requests
    except ImportError:
        print("  [WARN] 'requests' not installed -- pip install requests")
        return None

    params["apikey"] = api_key
    url = f"{_FMP_BASE}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and "Error Message" in data:
            print(f"  [WARN] FMP error: {data['Error Message']}")
            return None
        if isinstance(data, list):
            return data
        return None
    except Exception as exc:
        print(f"  [WARN] FMP request failed ({endpoint}): {exc}")
        return None


def _date_chunks(start: str, end: str, days: int = 90) -> List[Tuple[str, str]]:
    """Split a date range into chunks of at most *days* days."""
    s = datetime.strptime(start, "%Y-%m-%d")
    e = datetime.strptime(end, "%Y-%m-%d")
    chunks = []
    while s < e:
        chunk_end = min(s + timedelta(days=days), e)
        chunks.append((s.strftime("%Y-%m-%d"), chunk_end.strftime("%Y-%m-%d")))
        s = chunk_end + timedelta(days=1)
    return chunks


# ===================================================================
# Source 1: FMP Economic Calendar
# ===================================================================

def ingest_economic_calendar(conn, start: str, end: str, api_key: str) -> int:
    """Ingest macro economic events from FMP economic_calendar endpoint."""
    print("\n--- Economic Calendar (FMP) ---")
    if not api_key:
        print("  [SKIP] No FMP_API_KEY provided.")
        return 0

    inserted = 0
    for chunk_start, chunk_end in _date_chunks(start, end):
        data = _fmp_get("economic_calendar", {"from": chunk_start, "to": chunk_end}, api_key)
        if data is None:
            continue
        for row in data:
            date_str = row.get("date", "")
            event_name = row.get("event", "")
            if not date_str:
                continue
            eid = f"fmp_eco:{date_str}:{_event_hash(event_name)}"
            evt = {
                "source": "fmp",
                "event_id": eid,
                "event_type": "economic",
                "title": event_name,
                "country": row.get("country", ""),
                "currency": row.get("currency", ""),
                "impact": row.get("impact", ""),
                "actual": str(row.get("actual", "")) if row.get("actual") is not None else "",
                "forecast": str(row.get("estimate", "")) if row.get("estimate") is not None else "",
                "previous": str(row.get("previous", "")) if row.get("previous") is not None else "",
                "event_ts_ms": _iso_to_ms(date_str),
                "raw_json": _json_safe(row),
            }
            if db.insert_calendar_event(conn, evt):
                inserted += 1
        conn.commit()
        time.sleep(_FMP_RATE_DELAY)

    print(f"  Inserted {inserted} economic calendar events.")
    return inserted


# ===================================================================
# Source 2: FOMC / Central Bank Decisions
# ===================================================================

# Hard-coded FOMC meeting decision dates 2024-2026 (announcement dates).
FOMC_DATES = [
    # 2024
    "2024-01-31", "2024-03-20", "2024-05-01", "2024-06-12",
    "2024-07-31", "2024-09-18", "2024-11-07", "2024-12-18",
    # 2025
    "2025-01-29", "2025-03-19", "2025-05-07", "2025-06-18",
    "2025-07-30", "2025-09-17", "2025-11-05", "2025-12-17",
    # 2026
    "2026-01-28", "2026-03-18", "2026-05-06", "2026-06-17",
    "2026-07-29", "2026-09-16", "2026-11-04", "2026-12-16",
]

# Known major central bank decision dates (non-exhaustive, high-impact only).
CENTRAL_BANK_DATES = [
    # ECB
    ("ECB", "EU", "EUR", "2024-01-25"), ("ECB", "EU", "EUR", "2024-03-07"),
    ("ECB", "EU", "EUR", "2024-04-11"), ("ECB", "EU", "EUR", "2024-06-06"),
    ("ECB", "EU", "EUR", "2024-07-18"), ("ECB", "EU", "EUR", "2024-09-12"),
    ("ECB", "EU", "EUR", "2024-10-17"), ("ECB", "EU", "EUR", "2024-12-12"),
    ("ECB", "EU", "EUR", "2025-01-30"), ("ECB", "EU", "EUR", "2025-03-06"),
    ("ECB", "EU", "EUR", "2025-04-17"), ("ECB", "EU", "EUR", "2025-06-05"),
    # BOE
    ("BOE", "GB", "GBP", "2024-02-01"), ("BOE", "GB", "GBP", "2024-03-21"),
    ("BOE", "GB", "GBP", "2024-05-09"), ("BOE", "GB", "GBP", "2024-06-20"),
    ("BOE", "GB", "GBP", "2024-08-01"), ("BOE", "GB", "GBP", "2024-09-19"),
    ("BOE", "GB", "GBP", "2024-11-07"), ("BOE", "GB", "GBP", "2024-12-19"),
    ("BOE", "GB", "GBP", "2025-02-06"), ("BOE", "GB", "GBP", "2025-03-20"),
    ("BOE", "GB", "GBP", "2025-05-08"), ("BOE", "GB", "GBP", "2025-06-19"),
    # BOJ
    ("BOJ", "JP", "JPY", "2024-01-23"), ("BOJ", "JP", "JPY", "2024-03-19"),
    ("BOJ", "JP", "JPY", "2024-04-26"), ("BOJ", "JP", "JPY", "2024-06-14"),
    ("BOJ", "JP", "JPY", "2024-07-31"), ("BOJ", "JP", "JPY", "2024-09-20"),
    ("BOJ", "JP", "JPY", "2024-10-31"), ("BOJ", "JP", "JPY", "2024-12-19"),
    # RBA
    ("RBA", "AU", "AUD", "2024-02-06"), ("RBA", "AU", "AUD", "2024-03-19"),
    ("RBA", "AU", "AUD", "2024-05-07"), ("RBA", "AU", "AUD", "2024-06-18"),
    ("RBA", "AU", "AUD", "2024-08-06"), ("RBA", "AU", "AUD", "2024-09-24"),
    ("RBA", "AU", "AUD", "2024-11-05"), ("RBA", "AU", "AUD", "2024-12-10"),
    # BOC
    ("BOC", "CA", "CAD", "2024-01-24"), ("BOC", "CA", "CAD", "2024-03-06"),
    ("BOC", "CA", "CAD", "2024-04-10"), ("BOC", "CA", "CAD", "2024-06-05"),
    ("BOC", "CA", "CAD", "2024-07-24"), ("BOC", "CA", "CAD", "2024-09-04"),
    ("BOC", "CA", "CAD", "2024-10-23"), ("BOC", "CA", "CAD", "2024-12-11"),
    # SNB
    ("SNB", "CH", "CHF", "2024-03-21"), ("SNB", "CH", "CHF", "2024-06-20"),
    ("SNB", "CH", "CHF", "2024-09-26"), ("SNB", "CH", "CHF", "2024-12-12"),
]


def ingest_central_bank_decisions(conn, start: str, end: str, api_key: str) -> int:
    """Ingest FOMC + other central bank decision dates."""
    print("\n--- Central Bank Decisions ---")
    inserted = 0
    start_ms = _iso_to_ms(start)
    end_ms = _iso_to_ms(end)

    # FOMC
    for d in FOMC_DATES:
        ts = _iso_to_ms(d)
        if ts < start_ms or ts > end_ms:
            continue
        evt = {
            "source": "hardcoded",
            "event_id": f"fomc:{d}",
            "event_type": "central_bank_decision",
            "title": "FOMC Interest Rate Decision",
            "country": "US",
            "currency": "USD",
            "impact": "high",
            "actual": "",
            "forecast": "",
            "previous": "",
            "event_ts_ms": ts,
            "raw_json": _json_safe({"bank": "FOMC", "date": d}),
        }
        if db.insert_calendar_event(conn, evt):
            inserted += 1

    # Other central banks
    for bank, country, currency, d in CENTRAL_BANK_DATES:
        ts = _iso_to_ms(d)
        if ts < start_ms or ts > end_ms:
            continue
        evt = {
            "source": "hardcoded",
            "event_id": f"cb:{bank.lower()}:{d}",
            "event_type": "central_bank_decision",
            "title": f"{bank} Interest Rate Decision",
            "country": country,
            "currency": currency,
            "impact": "high",
            "actual": "",
            "forecast": "",
            "previous": "",
            "event_ts_ms": ts,
            "raw_json": _json_safe({"bank": bank, "date": d}),
        }
        if db.insert_calendar_event(conn, evt):
            inserted += 1

    conn.commit()

    # Also try FMP for additional central bank data
    if api_key:
        for chunk_start, chunk_end in _date_chunks(start, end):
            data = _fmp_get("economic_calendar", {"from": chunk_start, "to": chunk_end}, api_key)
            if data is None:
                continue
            for row in data:
                event_name = (row.get("event", "") or "").lower()
                if "interest rate" not in event_name and "rate decision" not in event_name:
                    continue
                date_str = row.get("date", "")
                if not date_str:
                    continue
                eid = f"fmp_cb:{date_str}:{_event_hash(event_name)}"
                evt = {
                    "source": "fmp",
                    "event_id": eid,
                    "event_type": "central_bank_decision",
                    "title": row.get("event", ""),
                    "country": row.get("country", ""),
                    "currency": row.get("currency", ""),
                    "impact": row.get("impact", "high"),
                    "actual": str(row.get("actual", "")) if row.get("actual") is not None else "",
                    "forecast": str(row.get("estimate", "")) if row.get("estimate") is not None else "",
                    "previous": str(row.get("previous", "")) if row.get("previous") is not None else "",
                    "event_ts_ms": _iso_to_ms(date_str),
                    "raw_json": _json_safe(row),
                }
                if db.insert_calendar_event(conn, evt):
                    inserted += 1
            conn.commit()
            time.sleep(_FMP_RATE_DELAY)

    print(f"  Inserted {inserted} central bank decision events.")
    return inserted


# ===================================================================
# Source 3: Earnings Calendar (FMP)
# ===================================================================

def ingest_earnings_calendar(conn, start: str, end: str, api_key: str) -> int:
    """Ingest earnings calendar from FMP."""
    print("\n--- Earnings Calendar (FMP) ---")
    if not api_key:
        print("  [SKIP] No FMP_API_KEY provided.")
        return 0

    inserted = 0
    for chunk_start, chunk_end in _date_chunks(start, end):
        data = _fmp_get("earning_calendar", {"from": chunk_start, "to": chunk_end}, api_key)
        if data is None:
            continue
        for row in data:
            date_str = row.get("date", "")
            symbol = row.get("symbol", "")
            if not date_str or not symbol:
                continue
            eid = f"fmp_earn:{symbol}:{date_str}"
            eps_str = str(row.get("eps", "")) if row.get("eps") is not None else ""
            eps_est = str(row.get("epsEstimated", "")) if row.get("epsEstimated") is not None else ""
            rev_str = str(row.get("revenue", "")) if row.get("revenue") is not None else ""
            evt = {
                "source": "fmp",
                "event_id": eid,
                "event_type": "earnings",
                "title": f"{symbol} Earnings Report",
                "country": "",
                "currency": "USD",
                "impact": "medium",
                "actual": eps_str,
                "forecast": eps_est,
                "previous": "",
                "event_ts_ms": _iso_to_ms(date_str),
                "raw_json": _json_safe(row),
            }
            if db.insert_calendar_event(conn, evt):
                inserted += 1
        conn.commit()
        time.sleep(_FMP_RATE_DELAY)

    print(f"  Inserted {inserted} earnings events.")
    return inserted


# ===================================================================
# Source 4: IPO Calendar (FMP)
# ===================================================================

def ingest_ipo_calendar(conn, start: str, end: str, api_key: str) -> int:
    """Ingest IPO calendar from FMP."""
    print("\n--- IPO Calendar (FMP) ---")
    if not api_key:
        print("  [SKIP] No FMP_API_KEY provided.")
        return 0

    inserted = 0
    for chunk_start, chunk_end in _date_chunks(start, end):
        data = _fmp_get("ipo_calendar", {"from": chunk_start, "to": chunk_end}, api_key)
        if data is None:
            continue
        for row in data:
            date_str = row.get("date", "")
            symbol = row.get("symbol", "")
            company = row.get("company", symbol)
            if not date_str:
                continue
            eid = f"fmp_ipo:{symbol or _event_hash(company)}:{date_str}"
            evt = {
                "source": "fmp",
                "event_id": eid,
                "event_type": "ipo",
                "title": f"IPO: {company}" if company else "IPO",
                "country": "",
                "currency": "USD",
                "impact": "medium",
                "actual": str(row.get("price", "")) if row.get("price") is not None else "",
                "forecast": str(row.get("priceRange", "")) if row.get("priceRange") is not None else "",
                "previous": "",
                "event_ts_ms": _iso_to_ms(date_str),
                "raw_json": _json_safe(row),
            }
            if db.insert_calendar_event(conn, evt):
                inserted += 1
        conn.commit()
        time.sleep(_FMP_RATE_DELAY)

    print(f"  Inserted {inserted} IPO events.")
    return inserted


# ===================================================================
# Source 5: Geopolitical Events (hard-coded seed + optional news API)
# ===================================================================

# Major geopolitical / market-moving events 2020-2026 (seed data).
GEOPOLITICAL_SEED_EVENTS = [
    # (date, title, country, keywords/description)
    ("2020-01-03", "US assassination of Qasem Soleimani", "US", "Middle East tensions, Iran, oil spike"),
    ("2020-03-11", "WHO declares COVID-19 pandemic", "GLOBAL", "COVID pandemic, global lockdowns, market crash"),
    ("2020-03-15", "Fed emergency rate cut to near zero", "US", "Emergency monetary policy, COVID response"),
    ("2020-04-20", "WTI crude oil futures go negative", "US", "Oil crash, storage crisis, unprecedented"),
    ("2020-11-09", "Pfizer COVID vaccine announcement", "US", "Vaccine breakthrough, market rally"),
    ("2020-12-31", "Brexit transition period ends", "GB", "Brexit completion, UK-EU trade deal"),
    ("2021-01-06", "US Capitol attack", "US", "Political instability, insurrection"),
    ("2021-01-27", "GameStop short squeeze peaks", "US", "Meme stocks, retail trading, market structure"),
    ("2021-05-19", "China crypto ban announcement", "CN", "Crypto crash, mining ban, capital flight"),
    ("2021-09-20", "Evergrande debt crisis intensifies", "CN", "China real estate, contagion fears"),
    ("2021-11-10", "US CPI hits 6.2% - 30yr high", "US", "Inflation shock, Fed pivot expectations"),
    ("2022-02-24", "Russia invades Ukraine", "RU", "War, sanctions, energy crisis, commodity spike"),
    ("2022-05-09", "Terra/LUNA collapse", "GLOBAL", "Crypto crash, stablecoin failure, contagion"),
    ("2022-06-13", "Celsius Network freezes withdrawals", "US", "Crypto contagion, lending crisis"),
    ("2022-09-22", "Japan Yen intervention (BOJ)", "JP", "Yen intervention, currency markets, BOJ"),
    ("2022-09-23", "UK mini-budget crisis", "GB", "Gilt crash, pension crisis, PM resignation"),
    ("2022-10-07", "US-China chip export controls", "US", "Semiconductor sanctions, tech cold war"),
    ("2022-11-11", "FTX bankruptcy filing", "US", "Crypto fraud, exchange collapse, contagion"),
    ("2023-03-10", "Silicon Valley Bank (SVB) collapse", "US", "Bank run, regional banking crisis, contagion"),
    ("2023-03-19", "Credit Suisse emergency UBS takeover", "CH", "Systemic bank failure, AT1 wipeout"),
    ("2023-05-01", "US debt ceiling crisis peak", "US", "Default risk, government shutdown threat"),
    ("2023-05-01", "First Republic Bank seizure", "US", "Regional bank crisis continues"),
    ("2023-10-07", "Hamas attack on Israel", "IL", "Middle East war, oil risk, safe haven flows"),
    ("2023-11-30", "COP28 climate summit agreement", "AE", "Energy transition, fossil fuel commitments"),
    ("2024-01-10", "SEC approves Bitcoin spot ETFs", "US", "Crypto milestone, institutional adoption"),
    ("2024-03-19", "BOJ ends negative interest rate policy", "JP", "Historic policy shift, Yen dynamics"),
    ("2024-04-19", "Iran-Israel tensions escalate", "GLOBAL", "Middle East escalation, oil risk"),
    ("2024-08-05", "Japan carry trade unwind crash", "JP", "Yen carry trade, global equity sell-off, VIX spike"),
    ("2024-11-05", "US Presidential Election 2024", "US", "Election, policy uncertainty, market volatility"),
    ("2025-01-20", "US Presidential Inauguration 2025", "US", "Administration change, policy shift"),
    ("2025-02-01", "US tariffs on Canada, Mexico, China", "US", "Trade war escalation, tariffs, supply chain"),
    ("2025-04-02", "US Liberation Day reciprocal tariffs", "US", "Broad tariff escalation, global trade shock"),
]

# Geopolitical keywords for news API searches
_GEO_KEYWORDS = [
    "sanctions", "tariff", "trade war", "election", "coup",
    "invasion", "treaty", "embargo", "default", "missile",
    "nuclear", "ceasefire", "annexation", "blockade",
]


def ingest_geopolitical_events(
    conn,
    start: str,
    end: str,
    seed: bool = True,
    news_api_key: str = "",
) -> int:
    """Ingest geopolitical events from hard-coded seed + optional news API."""
    print("\n--- Geopolitical Events ---")
    inserted = 0
    start_ms = _iso_to_ms(start)
    end_ms = _iso_to_ms(end)

    # --- Hard-coded seed events ---
    if seed:
        for date_str, title, country, desc in GEOPOLITICAL_SEED_EVENTS:
            ts = _iso_to_ms(date_str)
            if ts < start_ms or ts > end_ms:
                continue
            eid = f"seed_geo:{date_str}:{_event_hash(title)}"
            evt = {
                "source": "hardcoded",
                "event_id": eid,
                "event_type": "geopolitical",
                "title": title,
                "country": country,
                "currency": "",
                "impact": "high",
                "actual": "",
                "forecast": "",
                "previous": "",
                "event_ts_ms": ts,
                "raw_json": _json_safe({
                    "date": date_str, "title": title,
                    "country": country, "description": desc,
                }),
            }
            if db.insert_calendar_event(conn, evt):
                inserted += 1

            # Also insert into sentiment table for geopolitical events
            sent = {
                "source": "hardcoded",
                "sentiment_id": f"geo_sent:{date_str}:{_event_hash(title)}",
                "sentiment_type": "geopolitical",
                "symbol": "",
                "value": -0.8,  # Major geopolitical events are generally risk-off
                "label": "negative",
                "ts_ms": ts,
                "raw_json": _json_safe({
                    "date": date_str, "title": title, "country": country,
                }),
            }
            db.insert_sentiment(conn, sent)

        conn.commit()
        seed_count = inserted
        print(f"  Loaded {seed_count} hard-coded seed events.")

    # --- World News API (optional) ---
    if news_api_key:
        news_inserted = _ingest_world_news_geopolitical(conn, start, end, news_api_key)
        inserted += news_inserted
    else:
        print("  [SKIP] No WORLD_NEWS_API_KEY -- skipping news API geopolitical search.")

    print(f"  Inserted {inserted} total geopolitical events.")
    return inserted


def _ingest_world_news_geopolitical(
    conn, start: str, end: str, api_key: str,
) -> int:
    """Search World News API for geopolitical events."""
    try:
        import requests
    except ImportError:
        print("  [WARN] 'requests' not installed -- pip install requests")
        return 0

    inserted = 0
    base_url = "https://api.worldnewsapi.com/search-news"

    for keyword in _GEO_KEYWORDS:
        try:
            params = {
                "text": keyword,
                "language": "en",
                "earliest-publish-date": start,
                "latest-publish-date": end,
                "number": 50,
                "sort": "publish-time",
                "sort-direction": "DESC",
                "api-key": api_key,
            }
            resp = requests.get(base_url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            articles = data.get("news", [])

            for article in articles:
                pub_date = article.get("publish_date", "")
                title = article.get("title", "")
                if not pub_date or not title:
                    continue
                try:
                    ts = _iso_to_ms(pub_date[:19])
                except ValueError:
                    continue

                eid = f"wnews_geo:{_event_hash(title + pub_date)}"

                # Simple sentiment scoring based on keyword presence
                text = (title + " " + article.get("text", "")[:500]).lower()
                neg_words = sum(1 for w in ["war", "crash", "crisis", "attack",
                                             "sanctions", "collapse", "default",
                                             "invasion"] if w in text)
                sentiment_val = max(-1.0, -0.3 * neg_words) if neg_words else -0.1
                label = "negative" if sentiment_val < -0.3 else "neutral"

                evt = {
                    "source": "world_news_api",
                    "event_id": eid,
                    "event_type": "geopolitical",
                    "title": title[:500],
                    "country": article.get("source_country", ""),
                    "currency": "",
                    "impact": "high" if neg_words >= 2 else "medium",
                    "actual": "",
                    "forecast": "",
                    "previous": "",
                    "event_ts_ms": ts,
                    "raw_json": _json_safe({
                        "title": title, "url": article.get("url", ""),
                        "source": article.get("source", ""),
                        "publish_date": pub_date, "keyword": keyword,
                    }),
                }
                if db.insert_calendar_event(conn, evt):
                    inserted += 1

                # Sentiment
                sent = {
                    "source": "world_news_api",
                    "sentiment_id": f"wnews_sent:{_event_hash(title + pub_date)}",
                    "sentiment_type": "geopolitical",
                    "symbol": "",
                    "value": sentiment_val,
                    "label": label,
                    "ts_ms": ts,
                    "raw_json": _json_safe({
                        "title": title, "keyword": keyword, "sentiment_val": sentiment_val,
                    }),
                }
                db.insert_sentiment(conn, sent)

            conn.commit()
            time.sleep(0.5)  # rate limit courtesy
        except Exception as exc:
            print(f"  [WARN] World News API search for '{keyword}' failed: {exc}")
            continue

    print(f"  Inserted {inserted} news-sourced geopolitical events.")
    return inserted


# ===================================================================
# Source 6: Dividends Calendar (FMP)
# ===================================================================

def ingest_dividends_calendar(conn, start: str, end: str, api_key: str) -> int:
    """Ingest dividend calendar from FMP."""
    print("\n--- Dividends Calendar (FMP) ---")
    if not api_key:
        print("  [SKIP] No FMP_API_KEY provided.")
        return 0

    inserted = 0
    for chunk_start, chunk_end in _date_chunks(start, end):
        data = _fmp_get("stock_dividend_calendar", {"from": chunk_start, "to": chunk_end}, api_key)
        if data is None:
            continue
        for row in data:
            date_str = row.get("date", "") or row.get("paymentDate", "")
            symbol = row.get("symbol", "")
            if not date_str or not symbol:
                continue
            eid = f"fmp_div:{symbol}:{date_str}"
            div_amt = str(row.get("dividend", "")) if row.get("dividend") is not None else ""
            div_yield = str(row.get("adjDividend", "")) if row.get("adjDividend") is not None else ""
            evt = {
                "source": "fmp",
                "event_id": eid,
                "event_type": "dividend",
                "title": f"{symbol} Dividend",
                "country": "",
                "currency": "USD",
                "impact": "low",
                "actual": div_amt,
                "forecast": div_yield,
                "previous": "",
                "event_ts_ms": _iso_to_ms(date_str),
                "raw_json": _json_safe(row),
            }
            if db.insert_calendar_event(conn, evt):
                inserted += 1
        conn.commit()
        time.sleep(_FMP_RATE_DELAY)

    print(f"  Inserted {inserted} dividend events.")
    return inserted


# ===================================================================
# CLI & Main
# ===================================================================

ALL_SOURCES = ["economic", "earnings", "ipo", "dividends", "central_banks", "geopolitical"]


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ingest economic calendar, earnings, IPOs, geopolitical events "
                    "into Aureon global history DB.",
    )
    p.add_argument("--db", default=None, help="SQLite DB path override")
    p.add_argument("--start", default="2020-01-01", help="ISO start date (default: 2020-01-01)")
    p.add_argument("--end", default=_today_iso(), help="ISO end date (default: today)")
    p.add_argument(
        "--sources", default="all",
        help="Comma-separated: economic,earnings,ipo,dividends,central_banks,geopolitical,all (default: all)",
    )
    p.add_argument("--fmp-key", default=None, help="FMP API key (or env FMP_API_KEY)")
    p.add_argument("--news-key", default=None, help="World News API key (or env WORLD_NEWS_API_KEY)")
    p.add_argument(
        "--seed-events", nargs="?", const="true", default="true",
        help="Include hard-coded geopolitical seed events (default: true)",
    )
    return p.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)

    fmp_key = args.fmp_key or os.getenv("FMP_API_KEY", "")
    news_key = args.news_key or os.getenv("WORLD_NEWS_API_KEY", "")
    seed = args.seed_events.lower() in ("true", "1", "yes")

    sources_raw = args.sources.lower().strip()
    if sources_raw == "all":
        sources = set(ALL_SOURCES)
    else:
        sources = {s.strip() for s in sources_raw.split(",")}

    print(f"Aureon Economic Calendar Ingestion")
    print(f"  DB:      {args.db or '(default)'}")
    print(f"  Range:   {args.start} -> {args.end}")
    print(f"  Sources: {', '.join(sorted(sources))}")
    print(f"  FMP key: {'set' if fmp_key else 'NOT SET'}")
    print(f"  News key: {'set' if news_key else 'NOT SET'}")
    print(f"  Seed:    {seed}")

    conn = db.connect(args.db)
    total = 0

    try:
        if "economic" in sources:
            total += ingest_economic_calendar(conn, args.start, args.end, fmp_key)

        if "central_banks" in sources:
            total += ingest_central_bank_decisions(conn, args.start, args.end, fmp_key)

        if "earnings" in sources:
            total += ingest_earnings_calendar(conn, args.start, args.end, fmp_key)

        if "ipo" in sources:
            total += ingest_ipo_calendar(conn, args.start, args.end, fmp_key)

        if "dividends" in sources:
            total += ingest_dividends_calendar(conn, args.start, args.end, fmp_key)

        if "geopolitical" in sources:
            total += ingest_geopolitical_events(
                conn, args.start, args.end,
                seed=seed, news_api_key=news_key,
            )

        # Update watermark
        db.set_watermark_ms(conn, "calendar_ingest", _now_ms())
        conn.commit()

    finally:
        conn.close()

    print(f"\n=== Done. Total inserted: {total} ===")


if __name__ == "__main__":
    main()
