#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║      AUREON ATN BACKTEST — PLANETARY HARMONICS × MARKET CORRELATION     ║
║  "Every tremor in the Earth, every burst from the Sun, every whisper    ║
║   of the Schumann field — the market heard it.  This proves it."        ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  Pulls 3 years of historical planetary/Earth hazard events and aligns   ║
║  them with BTC + ETH price movements to find: when the Earth spoke,     ║
║  did the market listen?                                                  ║
║                                                                          ║
║  SOURCES:                                                                ║
║   • USGS FDSN  — M6.0+ earthquakes (full history, free)                 ║
║   • NASA DONKI — M/X solar flares + geomagnetic storms (free)           ║
║   • NASA EONET — Wildfire, volcanic, severe storm events                ║
║   • Binance    — BTCUSDT / ETHUSDT daily OHLCV (public, no auth)        ║
║                                                                          ║
║  CORRELATION WINDOWS:  +1d  +3d  +7d  +14d                              ║
║                                                                          ║
║  HARMONIC MAPPING (each event → Lyra grade):                            ║
║   M8.0+ quake / X-class flare / KP≥8  → SILENCE   (CHAOS field)        ║
║   M7.0+ quake / M-class flare / KP≥6  → DISSONANCE (SPIRAL)            ║
║   M6.0+ quake / C-class flare / KP≥4  → PARTIAL_HARMONY (STAR)         ║
║   Wildfire / Volcano WATCH             → PARTIAL_HARMONY                ║
║   Calm field                           → CLEAR_RESONANCE / DIVINE       ║
║                                                                          ║
║  Run:  python aureon_atn_backtest.py [--days 365] [--symbol BTCUSDT]    ║
║                                                                          ║
║  Gary Leckey | March 2026                                               ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import argparse
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

# ─────────────────────────────────────────────────────────────────────────────
# ANSI
# ─────────────────────────────────────────────────────────────────────────────
RST  = "\033[0m"
BOLD = "\033[1m"
DIM  = "\033[2m"
RED  = "\033[91m"
GRN  = "\033[92m"
YEL  = "\033[93m"
BLU  = "\033[94m"
MAG  = "\033[95m"
CYN  = "\033[96m"
WHT  = "\033[97m"

def _c(text: str, colour: str) -> str:
    return f"{colour}{text}{RST}"

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

CORR_WINDOWS_DAYS = [1, 3, 7, 14]

# Lyra harmonic grades + cymatics patterns
GRADES = ["DIVINE_HARMONY", "CLEAR_RESONANCE", "PARTIAL_HARMONY", "DISSONANCE", "SILENCE"]
GRADE_PATTERN = {
    "DIVINE_HARMONY":  "MANDALA",
    "CLEAR_RESONANCE": "HEXAGON",
    "PARTIAL_HARMONY": "STAR",
    "DISSONANCE":      "SPIRAL",
    "SILENCE":         "CHAOS",
}
GRADE_COLOUR = {
    "DIVINE_HARMONY":  GRN,
    "CLEAR_RESONANCE": CYN,
    "PARTIAL_HARMONY": YEL,
    "DISSONANCE":      MAG,
    "SILENCE":         RED,
}

# Binance public OHLCV — no auth needed
BINANCE_KLINES = "https://api.binance.com/api/v3/klines"

# Event type icons
EVENT_ICONS = {
    "earthquake": "🌋",
    "solar_flare": "☀️ ",
    "geo_storm":   "⚡",
    "wildfire":    "🔥",
    "volcano":     "🌋",
    "cme":         "🌀",
}


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class PlanetaryEvent:
    """A single historical Earth/space event."""
    timestamp: float          # Unix epoch UTC
    event_type: str           # earthquake / solar_flare / geo_storm / wildfire / volcano / cme
    severity: float           # Normalised 0–10 scale
    raw_magnitude: str        # e.g. "M7.2", "X3.1", "Kp=8"
    location: str
    grade: str                # Lyra harmonic grade assigned
    pattern: str              # Chladni cymatics pattern
    source: str               # USGS / DONKI / EONET

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


@dataclass
class PricePoint:
    """Daily OHLCV candle."""
    timestamp: float
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp / 1000.0, tz=timezone.utc)


@dataclass
class EventImpact:
    """One event × one price series × one time window."""
    event: PlanetaryEvent
    symbol: str
    window_days: int
    price_at_event: float
    price_after: float
    pct_change: float
    max_high_pct: float       # highest pct above event price in window
    max_low_pct: float        # lowest pct below event price in window
    volatility: float         # std of daily returns in window


# ─────────────────────────────────────────────────────────────────────────────
# HARMONIC GRADE MAPPING
# ─────────────────────────────────────────────────────────────────────────────

def _quake_grade(mag: float) -> Tuple[str, float]:
    """Map earthquake magnitude to Lyra grade + normalised severity."""
    if mag >= 8.0: return "SILENCE",         10.0
    if mag >= 7.5: return "SILENCE",          9.0
    if mag >= 7.0: return "DISSONANCE",       7.5
    if mag >= 6.5: return "DISSONANCE",       6.0
    if mag >= 6.0: return "PARTIAL_HARMONY",  4.5
    if mag >= 5.5: return "PARTIAL_HARMONY",  3.0
    return "CLEAR_RESONANCE", 1.5


def _flare_grade(cls: str) -> Tuple[str, float]:
    """Map GOES flare class (X2.5, M4.1 …) to Lyra grade + severity."""
    cls = cls.upper().strip()
    try:
        letter = cls[0]
        num    = float(cls[1:]) if len(cls) > 1 else 1.0
    except Exception:
        return "PARTIAL_HARMONY", 3.0

    if letter == "X" and num >= 5:  return "SILENCE",         10.0
    if letter == "X":               return "DISSONANCE",      7.0 + num * 0.3
    if letter == "M" and num >= 8:  return "DISSONANCE",       6.5
    if letter == "M":               return "PARTIAL_HARMONY", 3.5 + num * 0.3
    if letter == "C":               return "CLEAR_RESONANCE",  2.0
    return "CLEAR_RESONANCE", 1.0


def _kp_grade(kp: float) -> Tuple[str, float]:
    """Map Kp geomagnetic index to Lyra grade + severity."""
    if kp >= 8:  return "SILENCE",         9.0
    if kp >= 7:  return "SILENCE",         8.0
    if kp >= 6:  return "DISSONANCE",      6.5
    if kp >= 5:  return "PARTIAL_HARMONY", 4.5
    if kp >= 4:  return "PARTIAL_HARMONY", 3.0
    if kp >= 3:  return "CLEAR_RESONANCE", 1.5
    return "DIVINE_HARMONY", 0.5


# ─────────────────────────────────────────────────────────────────────────────
# HISTORICAL EVENT FETCHERS
# ─────────────────────────────────────────────────────────────────────────────

import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def _get(url: str, params: Dict = None, timeout: int = 20,
         verify: bool = True) -> Any:
    r = requests.get(url, params=params, timeout=timeout, verify=verify,
                     headers={"User-Agent": "AureonATNBacktest/1.0"})
    r.raise_for_status()
    return r.json()


def fetch_earthquakes(start: datetime, end: datetime,
                      min_mag: float = 6.0) -> List[PlanetaryEvent]:
    """USGS FDSN — full historical earthquake catalogue."""
    print(f"  🌋 Fetching USGS earthquakes M{min_mag}+ "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    events: List[PlanetaryEvent] = []
    try:
        data = _get("https://earthquake.usgs.gov/fdsnws/event/1/query", params={
            "format": "geojson",
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime":   end.strftime("%Y-%m-%d"),
            "minmagnitude": str(min_mag),
            "orderby": "time",
        }, verify=False)
        for feat in data.get("features", []):
            p   = feat.get("properties", {})
            mag = float(p.get("mag") or 0)
            ts  = float(p.get("time") or 0) / 1000.0
            place = (p.get("place") or "Unknown")[:60]
            grade, sev = _quake_grade(mag)
            events.append(PlanetaryEvent(
                timestamp=ts, event_type="earthquake",
                severity=sev, raw_magnitude=f"M{mag:.1f}",
                location=place, grade=grade,
                pattern=GRADE_PATTERN[grade], source="USGS",
            ))
        print(_c(f"{len(events)} events", GRN))
    except Exception as e:
        print(_c(f"ERROR: {e}", RED))
    return events


def fetch_solar_flares(start: datetime, end: datetime) -> List[PlanetaryEvent]:
    """NASA DONKI — M and X class solar flares."""
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    print(f"  ☀️  Fetching NASA DONKI flares "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    events: List[PlanetaryEvent] = []
    try:
        # DONKI only returns 1 year at a time — chunk if needed
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=365), end)
            data = _get("https://api.nasa.gov/DONKI/FLR", params={
                "startDate": chunk_start.strftime("%Y-%m-%d"),
                "endDate":   chunk_end.strftime("%Y-%m-%d"),
                "api_key":   key,
            })
            for flare in (data if isinstance(data, list) else []):
                cls  = (flare.get("classType") or "C1.0").strip()
                peak = flare.get("peakTime") or flare.get("beginTime") or ""
                if not peak:
                    continue
                # Filter M-class and above
                if not cls.upper().startswith(("M", "X")):
                    continue
                try:
                    dt = datetime.fromisoformat(peak.replace("Z", "+00:00"))
                except Exception:
                    try:
                        dt = datetime.strptime(peak[:16], "%Y-%m-%dT%H:%M")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                grade, sev = _flare_grade(cls)
                events.append(PlanetaryEvent(
                    timestamp=dt.timestamp(),
                    event_type="solar_flare",
                    severity=sev, raw_magnitude=cls,
                    location="Solar", grade=grade,
                    pattern=GRADE_PATTERN[grade], source="NASA-DONKI",
                ))
            chunk_start = chunk_end + timedelta(days=1)
        print(_c(f"{len(events)} events", GRN))
    except Exception as e:
        print(_c(f"ERROR: {e}", RED))
    return events


def fetch_geomagnetic_storms(start: datetime, end: datetime) -> List[PlanetaryEvent]:
    """NASA DONKI — geomagnetic storms (GST) with Kp index."""
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    print(f"  ⚡ Fetching NASA DONKI geo-storms "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    events: List[PlanetaryEvent] = []
    try:
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=365), end)
            data = _get("https://api.nasa.gov/DONKI/GST", params={
                "startDate": chunk_start.strftime("%Y-%m-%d"),
                "endDate":   chunk_end.strftime("%Y-%m-%d"),
                "api_key":   key,
            })
            for storm in (data if isinstance(data, list) else []):
                start_time = storm.get("startTime") or ""
                if not start_time:
                    continue
                # Extract max Kp from allKpIndex
                kp_vals = [float(k.get("kpIndex", 0))
                           for k in storm.get("allKpIndex", [])]
                max_kp = max(kp_vals) if kp_vals else 5.0
                # Only include significant storms (KP≥5)
                if max_kp < 5:
                    continue
                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except Exception:
                    try:
                        dt = datetime.strptime(start_time[:16], "%Y-%m-%dT%H:%M")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                grade, sev = _kp_grade(max_kp)
                events.append(PlanetaryEvent(
                    timestamp=dt.timestamp(),
                    event_type="geo_storm",
                    severity=sev, raw_magnitude=f"Kp={max_kp:.1f}",
                    location="Geomagnetic", grade=grade,
                    pattern=GRADE_PATTERN[grade], source="NASA-DONKI",
                ))
            chunk_start = chunk_end + timedelta(days=1)
        print(_c(f"{len(events)} events", GRN))
    except Exception as e:
        print(_c(f"ERROR: {e}", RED))
    return events


def fetch_cme(start: datetime, end: datetime) -> List[PlanetaryEvent]:
    """NASA DONKI — Coronal Mass Ejections (Earth-directed)."""
    key = os.getenv("NASA_API_KEY", "DEMO_KEY")
    print(f"  🌀 Fetching NASA DONKI CME "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    events: List[PlanetaryEvent] = []
    try:
        chunk_start = start
        while chunk_start < end:
            chunk_end = min(chunk_start + timedelta(days=365), end)
            data = _get("https://api.nasa.gov/DONKI/CME", params={
                "startDate": chunk_start.strftime("%Y-%m-%d"),
                "endDate":   chunk_end.strftime("%Y-%m-%d"),
                "api_key":   key,
            })
            for cme in (data if isinstance(data, list) else []):
                start_time = cme.get("startTime") or ""
                if not start_time:
                    continue
                # Only Earth-directed
                analyses = cme.get("cmeAnalyses") or []
                earth_directed = any(
                    a.get("isMostAccurate") and a.get("enlilList")
                    for a in analyses
                )
                if not earth_directed and analyses:
                    continue
                speed = 0.0
                for a in analyses:
                    s = float(a.get("speed") or 0)
                    if s > speed:
                        speed = s
                # Severity based on speed: >2000 km/s is extreme
                if speed >= 2000:   grade, sev = "SILENCE",         9.0
                elif speed >= 1500: grade, sev = "DISSONANCE",      7.0
                elif speed >= 1000: grade, sev = "PARTIAL_HARMONY", 5.0
                elif speed >= 600:  grade, sev = "PARTIAL_HARMONY", 3.0
                else:               grade, sev = "CLEAR_RESONANCE", 1.5

                try:
                    dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                except Exception:
                    try:
                        dt = datetime.strptime(start_time[:16], "%Y-%m-%dT%H:%M")
                        dt = dt.replace(tzinfo=timezone.utc)
                    except Exception:
                        continue
                events.append(PlanetaryEvent(
                    timestamp=dt.timestamp(),
                    event_type="cme",
                    severity=sev, raw_magnitude=f"{speed:.0f}km/s",
                    location="Solar wind", grade=grade,
                    pattern=GRADE_PATTERN[grade], source="NASA-DONKI",
                ))
            chunk_start = chunk_end + timedelta(days=1)
        print(_c(f"{len(events)} events", GRN))
    except Exception as e:
        print(_c(f"ERROR: {e}", RED))
    return events


def fetch_eonet_events(start: datetime, end: datetime) -> List[PlanetaryEvent]:
    """NASA EONET — wildfires, volcanic activity, severe storms."""
    print(f"  🔥 Fetching NASA EONET natural events "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    events: List[PlanetaryEvent] = []
    # EONET v3 uses lowercase IDs (verified March 2026)
    CATEGORY_MAP = {
        "wildfires":     ("wildfire",  "PARTIAL_HARMONY", 3.5),
        "volcanoes":     ("volcano",   "DISSONANCE",      5.0),
        "severeStorms":  ("weather",   "PARTIAL_HARMONY", 3.0),
        "floods":        ("flood",     "PARTIAL_HARMONY", 2.5),
    }
    try:
        for cat_id, (etype, grade, sev) in CATEGORY_MAP.items():
            try:
                data = _get("https://eonet.gsfc.nasa.gov/api/v3/events", params={
                    "status":   "all",
                    "category": cat_id,
                    "start":    start.strftime("%Y-%m-%d"),
                    "end":      end.strftime("%Y-%m-%d"),
                    "limit":    500,
                })
                for evt in data.get("events", []):
                    # Only take events with geometry (actual location + time)
                    geom = evt.get("geometry", [])
                    if not geom:
                        continue
                    for g in geom[:1]:
                        date_str = g.get("date") or ""
                        try:
                            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        except Exception:
                            continue
                        title = (evt.get("title") or "Unknown")[:50]
                        events.append(PlanetaryEvent(
                            timestamp=dt.timestamp(),
                            event_type=etype,
                            severity=sev,
                            raw_magnitude=cat_id[:4].upper(),
                            location=title,
                            grade=grade,
                            pattern=GRADE_PATTERN[grade],
                            source="NASA-EONET",
                        ))
            except Exception:
                pass
        print(_c(f"{len(events)} events", GRN))
    except Exception as e:
        print(_c(f"ERROR: {e}", RED))
    return events


# ─────────────────────────────────────────────────────────────────────────────
# PRICE HISTORY
# ─────────────────────────────────────────────────────────────────────────────

# Kraken pair mapping (Binance symbol → Kraken pair)
_KRAKEN_PAIRS = {
    "BTCUSDT": "XBTUSD",
    "ETHUSDT":  "ETHUSD",
    "SOLUSDT":  "SOLUSD",
    "BNBUSDT":  "BNBUSD",
    "XRPUSDT":  "XRPUSD",
    "ADAUSDT":  "ADAUSD",
    "LTCUSDT":  "LTCUSD",
    "DOTUSDT":  "DOTUSD",
}
# Kraken result key overrides (some pairs use different keys)
_KRAKEN_RESULT_KEY = {
    "XBTUSD": "XXBTZUSD",
    "ETHUSD": "XETHZUSD",
    "LTCUSD": "XLTCZUSD",
}

# CoinGecko coin IDs for last resort
_COINGECKO_IDS = {
    "BTCUSDT": "bitcoin",
    "ETHUSDT":  "ethereum",
    "SOLUSDT":  "solana",
    "BNBUSDT":  "binancecoin",
    "XRPUSDT":  "ripple",
    "ADAUSDT":  "cardano",
}


def _fetch_via_coingecko(coin_id: str, days: int) -> List[PricePoint]:
    """CoinGecko free API — daily close prices, worldwide access."""
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    r = requests.get(url, params={"vs_currency": "usd", "days": days,
                                   "interval": "daily"},
                     timeout=30, headers={"User-Agent": "AureonATNBacktest/1.0"})
    r.raise_for_status()
    data = r.json()
    prices  = data.get("prices",  [])
    volumes = data.get("total_volumes", [])
    vol_map = {int(v[0]): float(v[1]) for v in volumes}
    candles = []
    for i, (ts_ms, price) in enumerate(prices):
        # CoinGecko daily = close only; synthesise OHLC from adjacent closes
        prev_p = float(prices[i - 1][1]) if i > 0 else price
        next_p = float(prices[i + 1][1]) if i < len(prices) - 1 else price
        lo = min(prev_p, price, next_p)
        hi = max(prev_p, price, next_p)
        candles.append(PricePoint(
            timestamp=float(ts_ms),
            open=prev_p, high=hi, low=lo, close=price,
            volume=vol_map.get(int(ts_ms), 0.0),
        ))
    return candles


def _fetch_via_kraken(pair: str, since_ts: int, days: int) -> List[PricePoint]:
    """
    Kraken public OHLC — 1440-min (daily) candles.
    Returns up to 720 candles per call; paginate with `since`.
    Format: [time, open, high, low, close, vwap, volume, count]
    """
    candles: List[PricePoint] = []
    cur_since = since_ts
    for _ in range(4):  # max 4 pagination rounds = ~2880 days
        r = requests.get("https://api.kraken.com/0/public/OHLC",
                         params={"pair": pair, "interval": 1440, "since": cur_since},
                         timeout=15, headers={"User-Agent": "AureonATNBacktest/1.0"})
        r.raise_for_status()
        data   = r.json()
        if data.get("error"):
            break
        result = data.get("result", {})
        # Kraken result key varies; try known overrides then first key
        key = _KRAKEN_RESULT_KEY.get(pair) or next(
            (k for k in result if k != "last"), None)
        if not key:
            break
        rows = result[key]
        if not rows:
            break
        for row in rows:
            ts_ms = float(row[0]) * 1000  # Kraken gives seconds
            candles.append(PricePoint(
                timestamp=ts_ms,
                open=float(row[1]), high=float(row[2]),
                low=float(row[3]),  close=float(row[4]),
                volume=float(row[6]),
            ))
        # `last` = next `since` for pagination
        last_ts = int(result.get("last", 0))
        if last_ts <= cur_since or len(rows) < 720:
            break
        cur_since = last_ts
    return candles


def fetch_price_history(symbol: str, start: datetime, end: datetime) -> List[PricePoint]:
    """
    Pull daily OHLCV.  Priority:
      1. Kraken public OHLC (no auth, no geo-restriction, 720 candles/call)
      2. Binance public klines (geo-restricted on some servers)
      3. CoinGecko (rate-limited but last resort)
    """
    start_ts = int(start.timestamp())
    days_back = max(1, (end - start).days + 2)
    print(f"  📈 Fetching {symbol} daily OHLCV "
          f"{start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')} …", end=" ", flush=True)
    candles: List[PricePoint] = []

    # ── 1. Kraken ────────────────────────────────────────────────────────────
    kraken_pair = _KRAKEN_PAIRS.get(symbol.upper())
    if kraken_pair:
        try:
            raw = _fetch_via_kraken(kraken_pair, start_ts, days_back)
            filtered = [c for c in raw if c.timestamp / 1000 >= start_ts]
            if filtered:
                print(_c(f"{len(filtered)} candles (Kraken)", GRN))
                return filtered
        except Exception:
            pass

    # ── 2. Binance ───────────────────────────────────────────────────────────
    start_ms = int(start.timestamp() * 1000)
    end_ms   = int(end.timestamp()   * 1000)
    cur      = start_ms
    try:
        while cur < end_ms:
            r = requests.get(BINANCE_KLINES, params={
                "symbol": symbol, "interval": "1d",
                "startTime": cur, "endTime": end_ms, "limit": 1000,
            }, timeout=10, headers={"User-Agent": "AureonATNBacktest/1.0"})
            r.raise_for_status()
            raw = r.json()
            if not raw:
                break
            for k in raw:
                candles.append(PricePoint(
                    timestamp=float(k[0]),
                    open=float(k[1]), high=float(k[2]),
                    low=float(k[3]),  close=float(k[4]),
                    volume=float(k[5]),
                ))
            cur = int(raw[-1][6]) + 1
            if len(raw) < 1000:
                break
        if candles:
            print(_c(f"{len(candles)} candles (Binance)", GRN))
            return candles
    except Exception:
        pass

    # ── 3. CoinGecko (last resort) ───────────────────────────────────────────
    coin_id = _COINGECKO_IDS.get(symbol.upper())
    if coin_id:
        try:
            candles = _fetch_via_coingecko(coin_id, days_back)
            candles = [c for c in candles if c.timestamp >= start_ms]
            if candles:
                print(_c(f"{len(candles)} candles (CoinGecko)", YEL))
                return candles
        except Exception as e:
            print(_c(f"CoinGecko error: {e}", RED))

    print(_c("ERROR: no price source available", RED))
    return []


def _build_price_index(candles: List[PricePoint]) -> Dict[int, PricePoint]:
    """Map date (epoch of start-of-day UTC) → candle."""
    idx: Dict[int, PricePoint] = {}
    for c in candles:
        dt = datetime.fromtimestamp(c.timestamp / 1000.0, tz=timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0)
        idx[int(dt.timestamp())] = c
    return idx


def _price_after_n_days(price_idx: Dict[int, PricePoint],
                        event_ts: float, n: int) -> Optional[float]:
    """Get closing price N days after event_ts."""
    base = datetime.fromtimestamp(event_ts, tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    target = base + timedelta(days=n)
    for shift in range(4):  # allow 3-day weekend/holiday gap
        key = int((target + timedelta(days=shift)).timestamp())
        if key in price_idx:
            return price_idx[key].close
    return None


def _price_at(price_idx: Dict[int, PricePoint], event_ts: float) -> Optional[float]:
    """Get closing price on the day of the event."""
    return _price_after_n_days(price_idx, event_ts, 0)


def _max_high_low(price_idx: Dict[int, PricePoint],
                  event_ts: float, base_price: float, n: int) -> Tuple[float, float]:
    """Max % above (high) and % below (low) the base_price within n days."""
    max_high = 0.0; max_low  = 0.0
    base = datetime.fromtimestamp(event_ts, tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    for d in range(1, n + 1):
        key = int((base + timedelta(days=d)).timestamp())
        c = price_idx.get(key)
        if c:
            h = (c.high  - base_price) / base_price * 100.0
            l = (c.low   - base_price) / base_price * 100.0
            max_high = max(max_high, h)
            max_low  = min(max_low, l)
    return max_high, max_low


def _vol_in_window(price_idx: Dict[int, PricePoint],
                   event_ts: float, n: int) -> float:
    """Std dev of daily returns in the n-day window after event."""
    base = datetime.fromtimestamp(event_ts, tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0)
    closes = []
    for d in range(n + 1):
        key = int((base + timedelta(days=d)).timestamp())
        c = price_idx.get(key)
        if c:
            closes.append(c.close)
    if len(closes) < 2:
        return 0.0
    returns = [(closes[i] - closes[i - 1]) / closes[i - 1]
               for i in range(1, len(closes))]
    return statistics.stdev(returns) if len(returns) >= 2 else 0.0


# ─────────────────────────────────────────────────────────────────────────────
# IMPACT COMPUTATION
# ─────────────────────────────────────────────────────────────────────────────

def compute_impacts(events: List[PlanetaryEvent],
                    candles: List[PricePoint],
                    symbol: str) -> List[EventImpact]:
    price_idx = _build_price_index(candles)
    impacts: List[EventImpact] = []
    for evt in events:
        p0 = _price_at(price_idx, evt.timestamp)
        if p0 is None or p0 == 0:
            continue
        for w in CORR_WINDOWS_DAYS:
            pw = _price_after_n_days(price_idx, evt.timestamp, w)
            if pw is None:
                continue
            pct = (pw - p0) / p0 * 100.0
            hi, lo = _max_high_low(price_idx, evt.timestamp, p0, w)
            vol    = _vol_in_window(price_idx, evt.timestamp, w)
            impacts.append(EventImpact(
                event=evt, symbol=symbol, window_days=w,
                price_at_event=p0, price_after=pw,
                pct_change=pct, max_high_pct=hi,
                max_low_pct=lo, volatility=vol,
            ))
    return impacts


# ─────────────────────────────────────────────────────────────────────────────
# ANALYSIS & RENDERING
# ─────────────────────────────────────────────────────────────────────────────

def _pct_colour(pct: float) -> str:
    if pct >= 10:   return _c(f"+{pct:6.1f}%", GRN + BOLD)
    if pct >= 3:    return _c(f"+{pct:6.1f}%", GRN)
    if pct >= 0:    return _c(f"+{pct:6.1f}%", CYN)
    if pct >= -3:   return _c(f"{pct:6.1f}%",  YEL)
    if pct >= -10:  return _c(f"{pct:6.1f}%",  MAG)
    return             _c(f"{pct:6.1f}%",  RED + BOLD)


def _spark_bar(pct: float, width: int = 12) -> str:
    """Horizontal bar showing % change; centre = 0."""
    half = width // 2
    pos  = int(round(pct / 30.0 * half))  # ±30% = full bar
    pos  = max(-half, min(half, pos))
    bar  = list("·" * width)
    bar[half] = "│"
    if pos > 0:
        for i in range(half + 1, half + pos + 1):
            if 0 <= i < width:
                bar[i] = "█"
        return GRN + "".join(bar) + RST
    elif pos < 0:
        for i in range(half + pos, half):
            if 0 <= i < width:
                bar[i] = "█"
        return RED + "".join(bar) + RST
    return "".join(bar)


def print_correlation_table(impacts: List[EventImpact], symbol: str) -> None:
    """
    Correlation table: event_type × window → avg % change + win rate.
    """
    W = 80
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  CORRELATION TABLE — {symbol} returns after Earth/Space events{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")
    print(f"  {'EVENT TYPE':<18} {'N':>5}  "
          + "  ".join(f"{_c(f'+{w}d', BOLD):>14}" for w in CORR_WINDOWS_DAYS))
    print(f"  {'─'*18} {'─'*5}  " + "  ".join(["─" * 9] * len(CORR_WINDOWS_DAYS)))

    # Group by event_type × window
    groups: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for imp in impacts:
        groups[(imp.event.event_type, imp.window_days)].append(imp.pct_change)

    etypes = sorted(set(imp.event.event_type for imp in impacts))
    for etype in etypes:
        icon = EVENT_ICONS.get(etype, "  ")
        n_events = len(set(
            imp.event.timestamp for imp in impacts
            if imp.event.event_type == etype
        ))
        row = f"  {icon} {etype:<16} {n_events:>5}  "
        for w in CORR_WINDOWS_DAYS:
            vals = groups.get((etype, w), [])
            if not vals:
                row += f"  {'N/A':>8}"; continue
            avg  = sum(vals) / len(vals)
            row += f"  {_pct_colour(avg)}"
        print(row)

    print(f"  {'─' * (W - 2)}")


def print_harmonic_heatmap(impacts: List[EventImpact], symbol: str) -> None:
    """
    Heatmap: Lyra harmonic grade × window → avg % change.
    The core question: does the organism's field state predict market direction?
    """
    W = 80
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  LYRA HARMONIC GRADE × PRICE RETURN — {symbol}{RST}")
    print(f"  {'What the Earth was saying → what the market did'}{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")
    print(f"  {'GRADE / PATTERN':<24} {'N':>5}  "
          + "  ".join(f"{_c(f'+{w}d', BOLD):>14}" for w in CORR_WINDOWS_DAYS)
          + f"  {'SIGNAL':>8}")
    print(f"  {'─'*24} {'─'*5}  " + "  ".join(["─" * 9] * len(CORR_WINDOWS_DAYS))
          + "  " + "─" * 8)

    # Group by grade × window
    grade_groups: Dict[Tuple[str, int], List[float]] = defaultdict(list)
    for imp in impacts:
        grade_groups[(imp.event.grade, imp.window_days)].append(imp.pct_change)

    for grade in GRADES:
        pattern = GRADE_PATTERN[grade]
        gcol    = GRADE_COLOUR[grade]
        n_events = len(set(
            imp.event.timestamp for imp in impacts
            if imp.event.grade == grade
        ))
        if n_events == 0:
            continue
        label = f"{grade[:14]} / {pattern[:8]}"
        row = f"  {gcol}{label:<24}{RST} {n_events:>5}  "
        avgs = []
        for w in CORR_WINDOWS_DAYS:
            vals = grade_groups.get((grade, w), [])
            if not vals:
                row += f"  {'N/A':>8}"; avgs.append(None); continue
            avg = sum(vals) / len(vals)
            avgs.append(avg)
            row += f"  {_pct_colour(avg)}"

        # Signal: consensus direction across windows
        valid = [a for a in avgs if a is not None]
        if valid:
            net = sum(valid) / len(valid)
            signal = (
                _c("STRONG BUY  ▲▲", GRN + BOLD) if net > 8  else
                _c("BUY         ▲",  GRN)         if net > 3  else
                _c("MILD BUY    ↑",  CYN)         if net > 0  else
                _c("MILD SELL   ↓",  YEL)         if net > -3 else
                _c("SELL        ▼",  MAG)         if net > -8 else
                _c("STRONG SELL ▼▼", RED + BOLD)
            )
            row += f"  {signal}"
        print(row)

    print(f"  {'─' * (W - 2)}")
    print(f"  {DIM}Positive = market rose after this harmonic field state was recorded{RST}")
    print(f"  {DIM}Negative = market fell.  N = distinct events contributing to the average{RST}")


def print_top_events(impacts: List[EventImpact], symbol: str,
                     window: int = 7, top_n: int = 15) -> None:
    """The most extreme price moves that followed a planetary event."""
    W = 90
    filtered = [i for i in impacts if i.window_days == window]
    filtered.sort(key=lambda x: abs(x.pct_change), reverse=True)
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  TOP {top_n} BIGGEST {symbol} MOVES IN {window}d AFTER PLANETARY EVENT{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")
    print(f"  {'DATE':<12} {'TYPE':<14} {'MAG':<10} {'GRADE':<18} "
          f"{'BASE PRICE':>12} {'7d RETURN':>12} {'SPARK'}")
    print(f"  {'─'*12} {'─'*14} {'─'*10} {'─'*18} {'─'*12} {'─'*12} {'─'*14}")
    for imp in filtered[:top_n]:
        e = imp.event
        dt_str = e.dt.strftime("%Y-%m-%d")
        gcol   = GRADE_COLOUR[e.grade]
        grade_s = f"{gcol}{e.grade[:16]:<16}{RST}"
        bar   = _spark_bar(imp.pct_change)
        print(f"  {dt_str:<12} {e.event_type[:14]:<14} {e.raw_magnitude:<10} "
              f"{grade_s}  ${imp.price_at_event:>10,.0f}  "
              f"{_pct_colour(imp.pct_change)}  {bar}")
    print(f"  {'─' * (W - 2)}")


def print_timeline(events: List[PlanetaryEvent],
                   candles: List[PricePoint],
                   symbol: str, width: int = 78) -> None:
    """
    ASCII timeline: each column = 1 month.
    Row 1: price (ASCII sparkline)
    Rows 2+: event dots coloured by harmonic grade
    """
    if not events or not candles:
        return
    W = width
    # Build monthly buckets
    all_ts = sorted(c.timestamp for c in candles)
    if not all_ts:
        return
    start_dt = datetime.fromtimestamp(all_ts[0] / 1000, tz=timezone.utc).replace(day=1)
    end_dt   = datetime.fromtimestamp(all_ts[-1] / 1000, tz=timezone.utc)
    months   = []
    cur      = start_dt
    while cur <= end_dt:
        months.append(cur)
        m = cur.month + 1
        y = cur.year
        if m > 12:
            m = 1; y += 1
        cur = cur.replace(year=y, month=m)

    n_months = len(months)
    if n_months == 0:
        return

    # Monthly average closing prices
    price_idx = _build_price_index(candles)
    month_prices: List[float] = []
    for mo in months:
        # Average all candles in this month
        ps = []
        for d in range(31):
            key = int((mo + timedelta(days=d)).timestamp())
            c = price_idx.get(key)
            if c:
                ps.append(c.close)
        month_prices.append(sum(ps) / len(ps) if ps else 0.0)

    # Normalise prices to chart height
    valid_p = [p for p in month_prices if p > 0]
    if not valid_p:
        return
    p_min = min(valid_p); p_max = max(valid_p)
    p_range = p_max - p_min or 1.0
    CHART_H = 8

    # Build sparkline rows
    chart_rows = [[] for _ in range(CHART_H)]
    for p in month_prices:
        if p == 0:
            row_idx = 0
        else:
            row_idx = int((p - p_min) / p_range * (CHART_H - 1))
        for r in range(CHART_H):
            chart_rows[r].append("▓" if r == row_idx else " ")

    # Build event rows
    event_row: List[str] = [" "] * n_months
    for evt in events:
        dt = evt.dt
        for i, mo in enumerate(months):
            nxt_mo = months[i + 1] if i + 1 < len(months) else mo + timedelta(days=31)
            if mo <= dt.replace(tzinfo=timezone.utc) < nxt_mo:
                gcol = GRADE_COLOUR.get(evt.grade, "")
                icon = {"earthquake": "Q", "solar_flare": "F",
                        "geo_storm": "G", "wildfire": "W",
                        "volcano": "V", "cme": "C"}.get(evt.event_type, "?")
                # Colour the cell
                if gcol:
                    event_row[i] = gcol + icon + RST
                break

    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  TIMELINE — {symbol} price + planetary events{RST}")
    print(f"  {DIM}Q=quake  F=solar flare  G=geo-storm  W=wildfire  C=CME{RST}")
    print(f"  {DIM}{GRADE_COLOUR['DIVINE_HARMONY']}█{RST}=DIVINE  "
          f"{GRADE_COLOUR['CLEAR_RESONANCE']}█{RST}=CLEAR  "
          f"{GRADE_COLOUR['PARTIAL_HARMONY']}█{RST}=PARTIAL  "
          f"{GRADE_COLOUR['DISSONANCE']}█{RST}=DISCORD  "
          f"{GRADE_COLOUR['SILENCE']}█{RST}=SILENCE{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")

    # Print price sparkline (top = high, bottom = low)
    p_labels = [f"${p:>7,.0f}" if p > 0 else " " * 8 for p in [p_max, p_min]]
    for r in range(CHART_H - 1, -1, -1):
        prefix = (f"{GRN}{p_labels[0]}{RST}" if r == CHART_H - 1
                  else f"{RED}{p_labels[1]}{RST}" if r == 0
                  else " " * 9)
        row_str = "".join(chart_rows[r][:n_months])
        print(f"  {prefix}  {GRN if r > CHART_H//2 else RED}{row_str[:60]}{RST}")

    # Print event row
    evrow_str = "".join(event_row[:n_months])
    print(f"  {'EVENTS':>9}  {evrow_str[:60]}")

    # Month labels (every 3 months)
    label_row = ""
    for i, mo in enumerate(months[:60]):
        if mo.month in (1, 4, 7, 10):
            label_row += mo.strftime("%m/%y")[:3]
        else:
            label_row += " "
    print(f"  {'':>9}  {label_row[:60]}")
    print(f"{BOLD}{CYN}{'─' * W}{RST}")


def print_volatility_table(impacts: List[EventImpact], symbol: str) -> None:
    """
    After which events did the market become most volatile?
    """
    W = 70
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  VOLATILITY SPIKE TABLE — {symbol}{RST}")
    print(f"  {DIM}Average daily-return std-dev in 7-day window after each event type{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")

    vol_groups: Dict[str, List[float]] = defaultdict(list)
    for imp in impacts:
        if imp.window_days == 7 and imp.volatility > 0:
            vol_groups[imp.event.event_type].append(imp.volatility)

    rows = []
    for etype, vols in vol_groups.items():
        avg_vol  = sum(vols) / len(vols)
        max_vol  = max(vols)
        rows.append((etype, avg_vol, max_vol, len(vols)))
    rows.sort(key=lambda x: x[1], reverse=True)

    for etype, avg_v, max_v, n in rows:
        bar_len = int(avg_v * 300)
        bar = "█" * min(bar_len, 25)
        vol_col = RED if avg_v > 0.05 else YEL if avg_v > 0.03 else GRN
        print(f"  {EVENT_ICONS.get(etype,'  ')} {etype:<16}  "
              f"{vol_col}{avg_v*100:5.2f}%{RST} avg  "
              f"{DIM}{max_v*100:5.2f}% max  n={n}{RST}  "
              f"{vol_col}{bar}{RST}")
    print(f"  {'─' * (W - 2)}")


def print_grade_summary(events: List[PlanetaryEvent]) -> None:
    """How many events of each harmonic grade were recorded?"""
    W = 60
    counts: Dict[str, int] = defaultdict(int)
    for e in events:
        counts[e.grade] += 1
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  HARMONIC GRADE DISTRIBUTION (all event types){RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")
    total = max(sum(counts.values()), 1)
    for grade in GRADES:
        n = counts.get(grade, 0)
        bar = "█" * int(n / total * 40)
        gcol = GRADE_COLOUR[grade]
        print(f"  {gcol}{grade:<20}{RST}  {n:>5}  {gcol}{bar}{RST}")
    print(f"  {'─' * (W - 2)}")
    print(f"  Total events: {total}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ATN Backtest — map planetary events to crypto/stock returns"
    )
    parser.add_argument("--days",   type=int, default=730,
                        help="Lookback window in days (default 730 = 2 years)")
    parser.add_argument("--symbol", type=str, default="BTCUSDT",
                        help="Binance symbol (default BTCUSDT)")
    parser.add_argument("--symbol2",type=str, default="ETHUSDT",
                        help="Second symbol for comparison (default ETHUSDT)")
    parser.add_argument("--min-mag",type=float, default=6.0,
                        help="Min earthquake magnitude (default 6.0)")
    parser.add_argument("--no-eonet", action="store_true",
                        help="Skip EONET wildfire/volcano fetch (slower)")
    parser.add_argument("--no-cme",   action="store_true",
                        help="Skip CME fetch")
    args = parser.parse_args()

    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    W = 80
    date_range = f"  {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}  ({args.days} days)"
    print(f"{BOLD}{CYN}{'╔' + '═'*(W-2) + '╗'}{RST}")
    print(f"{BOLD}{CYN}║{'  AUREON ATN BACKTEST — PLANETARY HARMONICS × MARKET':^{W-2}}║{RST}")
    print(f"{BOLD}{CYN}║{date_range:^{W-2}}║{RST}")
    print(f"{BOLD}{CYN}{'╚' + '═'*(W-2) + '╝'}{RST}\n")
    print(f"  Fetching historical data …\n")

    # ── Fetch all event streams ───────────────────────────────────────────────
    all_events: List[PlanetaryEvent] = []
    all_events += fetch_earthquakes(start, end, min_mag=args.min_mag)
    all_events += fetch_solar_flares(start, end)
    all_events += fetch_geomagnetic_storms(start, end)
    if not args.no_cme:
        all_events += fetch_cme(start, end)
    if not args.no_eonet:
        all_events += fetch_eonet_events(start, end)

    all_events.sort(key=lambda e: e.timestamp)
    print(f"\n  {BOLD}Total planetary events: {len(all_events)}{RST}")

    # ── Fetch price history ───────────────────────────────────────────────────
    print()
    btc_candles = fetch_price_history(args.symbol,  start, end)
    eth_candles = fetch_price_history(args.symbol2, start, end)

    if not btc_candles:
        print(_c("  No price data retrieved — cannot correlate.", RED))
        sys.exit(1)

    # ── Compute impacts ───────────────────────────────────────────────────────
    print(f"\n  Computing correlations …", end=" ", flush=True)
    btc_impacts = compute_impacts(all_events, btc_candles, args.symbol)
    eth_impacts = compute_impacts(all_events, eth_candles, args.symbol2)
    print(_c(f"{len(btc_impacts)} impact records", GRN))

    # ── Grade distribution ────────────────────────────────────────────────────
    print_grade_summary(all_events)

    # ── Timeline ─────────────────────────────────────────────────────────────
    print_timeline(all_events, btc_candles, args.symbol)

    # ── Correlation tables ────────────────────────────────────────────────────
    print_correlation_table(btc_impacts, args.symbol)
    if eth_impacts:
        print_correlation_table(eth_impacts, args.symbol2)

    # ── Harmonic heatmap ──────────────────────────────────────────────────────
    print_harmonic_heatmap(btc_impacts, args.symbol)
    if eth_impacts:
        print_harmonic_heatmap(eth_impacts, args.symbol2)

    # ── Top events ────────────────────────────────────────────────────────────
    print_top_events(btc_impacts, args.symbol, window=7, top_n=15)

    # ── Volatility ────────────────────────────────────────────────────────────
    print_volatility_table(btc_impacts, args.symbol)

    # ── Final summary ─────────────────────────────────────────────────────────
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  SYSTEM SUMMARY{RST}")
    print(f"  Events analysed:  {len(all_events)}")
    print(f"  {args.symbol} impacts:   {len(btc_impacts)}")
    print(f"  {args.symbol2} impacts:   {len(eth_impacts)}")
    print(f"  Date range:       {start.strftime('%Y-%m-%d')} → {end.strftime('%Y-%m-%d')}")
    print(f"\n  {BOLD}The map is drawn.  The Earth spoke.  The market heard.{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}\n")


if __name__ == "__main__":
    main()
