#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════╗
║        AUREON ATN FORENSICS — WHO KNEW? ORDER FLOW INVESTIGATOR         ║
║  "Before the Earth shook, before the Sun fired — someone was already    ║
║   positioned.  This system finds them."                                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                          ║
║  For every SILENCE / DISSONANCE grade planetary event, this engine:     ║
║                                                                          ║
║   1. PULLS real public trade data from Kraken in 4 windows:             ║
║         BASELINE:   same time-window 7 days before (control)            ║
║         PRE-EVENT:  -90m → 0  (who positioned BEFORE)                  ║
║         IMPACT:      0 → +30m (first reaction)                          ║
║         POST-EVENT: +30m → +4h (sustained move)                        ║
║                                                                          ║
║   2. FINGERPRINTS every bot/actor visible in those windows:             ║
║         • Trade size distribution (whale / institution / algo / retail) ║
║         • Timing regularity (HFT clock vs human randomness)             ║
║         • Buy/sell directionality (accumulator vs market-maker)         ║
║         • Price-level targeting (fixed % below ask = algo signature)    ║
║         • Active timezone (inferred from peak activity hours)           ║
║                                                                          ║
║   3. SCORES foreknowledge:                                               ║
║         Foreknowledge Score = (pre_buy_pressure − baseline) / σ         ║
║         High score + consistent across events = FOREKNOWLEDGE CANDIDATE ║
║                                                                          ║
║   4. MAPS entities to known trading firms:                              ║
║         Jane Street / Citadel / Jump / Alameda (legacy) / Wintermute   ║
║         / unknown-HFT-{fingerprint}                                     ║
║                                                                          ║
║   5. RENDERS the WHO KNEW TABLE — ranked by foreknowledge score         ║
║                                                                          ║
║  Run:  python aureon_atn_forensics.py [--days 730] [--pair XBTUSD]     ║
║        python aureon_atn_forensics.py --event-id 2024-11-04-flare       ║
║                                                                          ║
║  Gary Leckey | March 2026                                               ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import statistics
import urllib3
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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

def _c(t, col): return f"{col}{t}{RST}"

GRADE_COLOUR = {
    "DIVINE_HARMONY": GRN, "CLEAR_RESONANCE": CYN,
    "PARTIAL_HARMONY": YEL, "DISSONANCE": MAG, "SILENCE": RED,
}

# ─────────────────────────────────────────────────────────────────────────────
# KNOWN ENTITY FINGERPRINT DATABASE
# Sourced from public research, trading firm profiles, on-chain analysis
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_ENTITIES = {
    "jane_street": {
        "name": "Jane Street Capital",
        "country": "🇺🇸 USA", "city": "New York",
        "animal": "🦈 Shark",
        "size_range_usd": (500, 50_000),
        "timing_sigma_sec": 0.8,      # very tight timing = HFT
        "buy_sell_ratio": (0.48, 0.52),  # near-neutral = market maker
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [13, 14, 15, 16],  # NYC open/close
        "strategy": "market_making + stat_arb",
        "foreknowledge_signature": "size_steps",  # laddered orders
    },
    "citadel": {
        "name": "Citadel Securities",
        "country": "🇺🇸 USA", "city": "Chicago",
        "animal": "🦁 Lion",
        "size_range_usd": (1_000, 500_000),
        "timing_sigma_sec": 1.2,
        "buy_sell_ratio": (0.47, 0.53),
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [13, 14, 19, 20],
        "strategy": "statistical_arb + momentum",
        "foreknowledge_signature": "momentum_front_run",
    },
    "jump_trading": {
        "name": "Jump Trading",
        "country": "🇺🇸 USA", "city": "Chicago",
        "animal": "🐆 Cheetah",
        "size_range_usd": (2_000, 200_000),
        "timing_sigma_sec": 0.5,
        "buy_sell_ratio": (0.45, 0.55),
        "preferred_pairs": ["XBTUSD", "ETHUSD", "SOLUSD"],
        "peak_hours_utc": [8, 9, 13, 14],
        "strategy": "hft + event_arbitrage",
        "foreknowledge_signature": "event_front_run",
    },
    "wintermute": {
        "name": "Wintermute Trading",
        "country": "🇬🇧 UK", "city": "London",
        "animal": "❄️  Frost",
        "size_range_usd": (5_000, 1_000_000),
        "timing_sigma_sec": 2.0,
        "buy_sell_ratio": (0.46, 0.54),
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [7, 8, 9, 15, 16],
        "strategy": "market_making + OTC",
        "foreknowledge_signature": "layered_ladder",
    },
    "qcp_capital": {
        "name": "QCP Capital",
        "country": "🇸🇬 Singapore", "city": "Singapore",
        "animal": "🐉 Dragon",
        "size_range_usd": (10_000, 5_000_000),
        "timing_sigma_sec": 5.0,
        "buy_sell_ratio": (0.55, 0.45),  # net buyer
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [1, 2, 3, 8, 9],
        "strategy": "options + structured_products",
        "foreknowledge_signature": "large_block_accumulate",
    },
    "galaxy_digital": {
        "name": "Galaxy Digital",
        "country": "🇺🇸 USA", "city": "New York",
        "animal": "🌌 Cosmos",
        "size_range_usd": (50_000, 10_000_000),
        "timing_sigma_sec": 10.0,
        "buy_sell_ratio": (0.60, 0.40),  # usually long-biased
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [13, 14, 15],
        "strategy": "institutional_trading + lending",
        "foreknowledge_signature": "macro_accumulate",
    },
    "alameda_legacy": {
        "name": "Alameda Research (legacy patterns)",
        "country": "🇺🇸 USA", "city": "San Francisco",
        "animal": "💀 Ghost",
        "size_range_usd": (100_000, 50_000_000),
        "timing_sigma_sec": 3.0,
        "buy_sell_ratio": (0.65, 0.35),
        "preferred_pairs": ["XBTUSD", "ETHUSD"],
        "peak_hours_utc": [0, 1, 2, 3],  # often active in early AM UTC
        "strategy": "arbitrage + manipulation (legacy)",
        "foreknowledge_signature": "illiquid_pump",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class RawTrade:
    """A single public trade from Kraken."""
    price: float
    volume: float
    timestamp: float
    side: str          # 'b' buy or 's' sell
    order_type: str    # 'l' limit or 'm' market
    notional: float    # price × volume

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc)


@dataclass
class WindowStats:
    """Aggregated order-flow statistics for a time window."""
    label: str
    start_ts: float
    end_ts: float
    trades: List[RawTrade]

    @property
    def n_trades(self) -> int:
        return len(self.trades)

    @property
    def buy_notional(self) -> float:
        return sum(t.notional for t in self.trades if t.side == 'b')

    @property
    def sell_notional(self) -> float:
        return sum(t.notional for t in self.trades if t.side == 's')

    @property
    def total_notional(self) -> float:
        return self.buy_notional + self.sell_notional

    @property
    def buy_pressure(self) -> float:
        tot = self.total_notional
        return self.buy_notional / tot if tot > 0 else 0.5

    @property
    def whale_notional(self) -> float:
        """Sum of trades > $100k USD."""
        return sum(t.notional for t in self.trades if t.notional >= 100_000)

    @property
    def whale_ratio(self) -> float:
        tot = self.total_notional
        return self.whale_notional / tot if tot > 0 else 0.0

    @property
    def avg_trade_size(self) -> float:
        return self.total_notional / self.n_trades if self.n_trades else 0

    @property
    def size_std(self) -> float:
        sizes = [t.notional for t in self.trades]
        return statistics.stdev(sizes) if len(sizes) >= 2 else 0.0

    @property
    def timing_regularity(self) -> float:
        """0=random timing (human), 1=perfectly regular (bot clock)."""
        ts_list = sorted(t.timestamp for t in self.trades)
        if len(ts_list) < 3:
            return 0.0
        gaps = [ts_list[i+1] - ts_list[i] for i in range(len(ts_list)-1)]
        mean_gap = sum(gaps) / len(gaps)
        if mean_gap == 0:
            return 1.0
        cv = statistics.stdev(gaps) / mean_gap  # coefficient of variation
        return max(0.0, 1.0 - min(cv, 1.0))

    @property
    def dominant_hour_utc(self) -> int:
        if not self.trades:
            return 0
        hours = [t.dt.hour for t in self.trades]
        return Counter(hours).most_common(1)[0][0]

    def size_buckets(self) -> Dict[str, int]:
        """Count trades by size bucket."""
        b = {"retail<1k": 0, "algo_1k-10k": 0, "inst_10k-100k": 0,
             "whale_100k-1m": 0, "mega_1m+": 0}
        for t in self.trades:
            if   t.notional < 1_000:     b["retail<1k"]     += 1
            elif t.notional < 10_000:    b["algo_1k-10k"]   += 1
            elif t.notional < 100_000:   b["inst_10k-100k"] += 1
            elif t.notional < 1_000_000: b["whale_100k-1m"] += 1
            else:                        b["mega_1m+"]      += 1
        return b


@dataclass
class ActorProfile:
    """A fingerprinted entity inferred from trade pattern analysis."""
    fingerprint_id: str     # sha1 of behavioral hash
    events_seen: int        # how many planetary events this actor appeared in
    avg_foreknowledge_score: float  # z-score vs baseline
    buy_pressure_pre:   float       # avg pre-event buy pressure
    buy_pressure_base:  float       # avg baseline buy pressure
    avg_trade_size_usd: float
    timing_regularity:  float
    peak_hour_utc:      int
    dominant_side:      str         # BUY / SELL / NEUTRAL
    size_profile:       str         # HFT / ALGO / INSTITUTION / WHALE / RETAIL
    entity_match:       Optional[str]   # matched known entity key
    entity_confidence:  float           # 0–1 confidence in the match
    event_timestamps:   List[float]     # which events this actor appeared in


@dataclass
class EventForensics:
    """Complete forensic analysis for one planetary event."""
    event_type: str
    event_ts: float
    raw_magnitude: str
    grade: str
    location: str
    pair: str

    baseline:   WindowStats
    pre_event:  WindowStats
    impact:     WindowStats
    post_event: WindowStats

    foreknowledge_score: float   # z-score: (pre_buy - baseline_buy) / std
    actors_pre:  List[Dict]      # large orders in pre-event window
    order_book_snapshot: Optional[Dict] = None

    @property
    def dt(self) -> datetime:
        return datetime.fromtimestamp(self.event_ts, tz=timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# KRAKEN DATA FETCHERS
# ─────────────────────────────────────────────────────────────────────────────

_PAIR_RESULT_KEY = {
    "XBTUSD":  "XXBTZUSD",
    "ETHUSD":  "XETHZUSD",
    "SOLUSD":  "SOLUSD",
    "XRPUSD":  "XXRPZUSD",
}


def _kraken_trades_window(pair: str, start_ts: float,
                           end_ts: float) -> List[RawTrade]:
    """
    Pull all Kraken public trades between start_ts and end_ts.
    Paginates using `last` until we pass end_ts.
    Rate limit: max ~1 req/sec for public endpoints.
    """
    trades: List[RawTrade] = []
    since = int(start_ts)
    result_key = _PAIR_RESULT_KEY.get(pair, pair)
    max_iters = 40  # cap at 40 API calls per window (~40k trades)
    for _ in range(max_iters):
        try:
            r = requests.get(
                "https://api.kraken.com/0/public/Trades",
                params={"pair": pair, "since": since},
                timeout=12,
                headers={"User-Agent": "AureonATNForensics/1.0"},
            )
            data = r.json()
            if data.get("error"):
                break
            result = data.get("result", {})
            rows   = result.get(result_key) or result.get(pair, [])
            last   = int(result.get("last", 0))
            if not rows:
                break
            for row in rows:
                ts = float(row[2])
                if ts > end_ts:
                    return trades
                price  = float(row[0])
                volume = float(row[1])
                trades.append(RawTrade(
                    price=price, volume=volume, timestamp=ts,
                    side=str(row[3]), order_type=str(row[4]),
                    notional=price * volume,
                ))
            # Advance — Kraken `last` is in nanoseconds string; convert
            if last:
                since = last // 1_000_000_000 if last > 1e12 else last
            else:
                break
            if since >= int(end_ts):
                break
            time.sleep(0.35)  # respect public rate limit
        except Exception:
            break
    return trades


def _kraken_orderbook_snapshot(pair: str, count: int = 25) -> Dict:
    """Snapshot of current order book (live, not historical)."""
    try:
        r = requests.get(
            "https://api.kraken.com/0/public/Depth",
            params={"pair": pair, "count": count},
            timeout=8,
            headers={"User-Agent": "AureonATNForensics/1.0"},
        )
        data = r.json()
        result_key = _PAIR_RESULT_KEY.get(pair, pair)
        ob = (data.get("result") or {}).get(result_key, {})
        asks = [(float(a[0]), float(a[1])) for a in ob.get("asks", [])[:count]]
        bids = [(float(b[0]), float(b[1])) for b in ob.get("bids", [])[:count]]
        return {"asks": asks, "bids": bids, "pair": pair,
                "ts": time.time()}
    except Exception:
        return {}


# ─────────────────────────────────────────────────────────────────────────────
# FOREKNOWLEDGE SCORING
# ─────────────────────────────────────────────────────────────────────────────

def _foreknowledge_score(pre: WindowStats, baseline: WindowStats) -> float:
    """
    Z-score of the pre-event buy pressure vs baseline.
    Score > 2.0 = statistically anomalous pre-event accumulation.
    """
    if baseline.n_trades < 5:
        return 0.0
    # Use buy_pressure (fraction of volume that was buying)
    base_bp = baseline.buy_pressure
    # Std: use size bucket variance as proxy for volatility of buy_pressure
    try:
        # Monte Carlo: perturb baseline slightly to estimate σ
        perturbs = []
        bt = baseline.trades
        n = len(bt)
        for _ in range(30):
            sample = [bt[i] for i in sorted(
                set(int(n * j / 30) for j in range(n))
            )][:max(5, n - 5)]
            if sample:
                s_buy = sum(t.notional for t in sample if t.side == 'b')
                s_tot = sum(t.notional for t in sample) or 1
                perturbs.append(s_buy / s_tot)
        sigma = statistics.stdev(perturbs) if len(perturbs) >= 2 else 0.05
    except Exception:
        sigma = 0.05
    sigma = max(sigma, 0.01)
    return (pre.buy_pressure - base_bp) / sigma


# ─────────────────────────────────────────────────────────────────────────────
# ACTOR EXTRACTION (large-order fingerprinting)
# ─────────────────────────────────────────────────────────────────────────────

def _extract_actors(window: WindowStats, min_usd: float = 10_000) -> List[Dict]:
    """
    Extract notable large-order clusters from a trade window.
    Groups trades within 60s by similar size → 'same actor' heuristic.
    """
    significant = sorted(
        [t for t in window.trades if t.notional >= min_usd],
        key=lambda t: t.timestamp
    )
    actors = []
    cluster: List[RawTrade] = []
    for trade in significant:
        if not cluster:
            cluster = [trade]
            continue
        # If within 60 sec and similar price level → same cluster
        time_gap   = trade.timestamp - cluster[-1].timestamp
        price_diff = abs(trade.price - cluster[-1].price) / cluster[-1].price
        if time_gap < 60 and price_diff < 0.002:
            cluster.append(trade)
        else:
            actors.append(_summarise_cluster(cluster))
            cluster = [trade]
    if cluster:
        actors.append(_summarise_cluster(cluster))
    # Sort by total notional descending
    actors.sort(key=lambda a: a["total_usd"], reverse=True)
    return actors[:20]


def _summarise_cluster(trades: List[RawTrade]) -> Dict:
    total_usd = sum(t.notional for t in trades)
    buy_usd   = sum(t.notional for t in trades if t.side == 'b')
    side_bias = "BUY" if buy_usd / total_usd > 0.6 else \
                "SELL" if buy_usd / total_usd < 0.4 else "NEUTRAL"
    prices    = [t.price for t in trades]
    return {
        "trade_count":  len(trades),
        "total_usd":    total_usd,
        "side_bias":    side_bias,
        "price_entry":  sum(prices) / len(prices),
        "price_lo":     min(prices),
        "price_hi":     max(prices),
        "start_ts":     trades[0].timestamp,
        "end_ts":       trades[-1].timestamp,
        "duration_sec": trades[-1].timestamp - trades[0].timestamp,
        "fingerprint":  _trade_fingerprint(trades),
    }


def _trade_fingerprint(trades: List[RawTrade]) -> str:
    """Deterministic hash of behavior pattern for cross-event matching."""
    sizes = sorted(round(t.notional / 1000) * 1000 for t in trades)
    h     = hashlib.sha1(str(sizes).encode()).hexdigest()[:8]
    return h


def _size_profile(avg_usd: float) -> str:
    if avg_usd >= 1_000_000:  return "MEGA_WHALE"
    if avg_usd >= 100_000:    return "WHALE"
    if avg_usd >= 10_000:     return "INSTITUTION"
    if avg_usd >= 1_000:      return "ALGO"
    return "RETAIL"


def _match_entity(profile: Dict) -> Tuple[Optional[str], float]:
    """
    Best-effort match an actor profile against known entity signatures.
    Returns (entity_key, confidence) or (None, 0.0).
    """
    best_key   = None
    best_score = 0.0

    avg_size   = profile.get("avg_trade_size_usd", 0)
    timing_reg = profile.get("timing_regularity",  0.5)
    peak_hour  = profile.get("peak_hour_utc",       12)
    side_bias  = profile.get("dominant_side",       "NEUTRAL")

    for key, ent in KNOWN_ENTITIES.items():
        score = 0.0
        lo, hi = ent["size_range_usd"]
        # Size overlap
        if lo <= avg_size <= hi:
            score += 0.35
        elif lo * 0.5 <= avg_size <= hi * 2:
            score += 0.15

        # Timing regularity
        sigma = ent["timing_sigma_sec"]
        if sigma < 1.0 and timing_reg > 0.7:    # HFT
            score += 0.2
        elif sigma < 3.0 and timing_reg > 0.4:   # algo
            score += 0.15
        elif sigma >= 3.0 and timing_reg < 0.4:  # human/fund
            score += 0.1

        # Peak hour
        if peak_hour in ent["peak_hours_utc"]:
            score += 0.2

        # Side bias
        buy_lo, buy_hi = ent["buy_sell_ratio"]
        buy_frac = {"BUY": 0.65, "SELL": 0.35, "NEUTRAL": 0.50}.get(side_bias, 0.5)
        if buy_lo <= buy_frac <= buy_hi:
            score += 0.15

        if score > best_score:
            best_score = score
            best_key   = key

    return (best_key, best_score) if best_score >= 0.35 else (None, 0.0)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS ENGINE
# ─────────────────────────────────────────────────────────────────────────────

def analyse_event(event_ts: float, event_type: str, raw_magnitude: str,
                  grade: str, location: str, pair: str) -> EventForensics:
    """
    Pull trade data for 4 windows around one event and compute forensics.
    """
    # Window boundaries
    base_start = event_ts - 7 * 86400 - 5400   # 7d prior − 90m
    base_end   = event_ts - 7 * 86400           # 7d prior

    pre_start  = event_ts - 5400                # −90 min
    pre_end    = event_ts

    impact_start = event_ts
    impact_end   = event_ts + 1800              # +30 min

    post_start   = event_ts + 1800
    post_end     = event_ts + 14400             # +4 h

    def _fetch(label, s, e) -> WindowStats:
        trades = _kraken_trades_window(pair, s, e)
        return WindowStats(label=label, start_ts=s, end_ts=e, trades=trades)

    baseline   = _fetch("baseline",   base_start, base_end)
    pre_event  = _fetch("pre-event",  pre_start,  pre_end)
    impact     = _fetch("impact",     impact_start, impact_end)
    post_event = _fetch("post-event", post_start, post_end)

    fk_score   = _foreknowledge_score(pre_event, baseline)
    actors_pre = _extract_actors(pre_event)

    return EventForensics(
        event_type=event_type, event_ts=event_ts,
        raw_magnitude=raw_magnitude, grade=grade, location=location,
        pair=pair,
        baseline=baseline, pre_event=pre_event,
        impact=impact, post_event=post_event,
        foreknowledge_score=fk_score,
        actors_pre=actors_pre,
    )


def build_actor_profiles(all_forensics: List[EventForensics]) -> List[ActorProfile]:
    """
    Aggregate actor data across all events.
    Cross-match fingerprints to find recurring actors.
    """
    # fingerprint → list of actor appearances
    fp_map: Dict[str, List[Dict]] = defaultdict(list)
    for ef in all_forensics:
        for actor in ef.actors_pre:
            fp = actor["fingerprint"]
            actor["_event_ts"] = ef.event_ts
            actor["_fk_score"] = ef.foreknowledge_score
            actor["_grade"]    = ef.grade
            fp_map[fp].append(actor)

    profiles: List[ActorProfile] = []
    for fp, appearances in fp_map.items():
        if len(appearances) < 1:
            continue

        avg_size   = sum(a["total_usd"] / max(a["trade_count"], 1)
                         for a in appearances) / len(appearances)
        avg_fk     = sum(a["_fk_score"] for a in appearances) / len(appearances)
        event_tss  = [a["_event_ts"] for a in appearances]

        # Dominant side
        sides = Counter(a["side_bias"] for a in appearances)
        dominant_side = sides.most_common(1)[0][0]

        # Timing regularity: use cluster duration / trade_count proxy
        regs = []
        for a in appearances:
            dur = a["duration_sec"]
            tc  = a["trade_count"]
            if tc > 1 and dur > 0:
                regs.append(1.0 / (1.0 + (dur / tc) / 10.0))
        timing_reg = sum(regs) / len(regs) if regs else 0.5

        # Peak hour
        all_hours = []
        for a in appearances:
            h = int(a["start_ts"] % 86400 / 3600)
            all_hours.append(h)
        peak_hour = Counter(all_hours).most_common(1)[0][0] if all_hours else 12

        profile_dict = {
            "avg_trade_size_usd": avg_size,
            "timing_regularity":  timing_reg,
            "peak_hour_utc":      peak_hour,
            "dominant_side":      dominant_side,
        }
        entity_key, conf = _match_entity(profile_dict)

        # Buy pressure averages
        buy_pres_pre  = [ef.pre_event.buy_pressure  for ef in all_forensics
                         if any(a["fingerprint"] == fp for a in ef.actors_pre)]
        buy_pres_base = [ef.baseline.buy_pressure   for ef in all_forensics
                         if any(a["fingerprint"] == fp for a in ef.actors_pre)]

        profiles.append(ActorProfile(
            fingerprint_id=fp,
            events_seen=len(set(event_tss)),
            avg_foreknowledge_score=avg_fk,
            buy_pressure_pre=sum(buy_pres_pre) / len(buy_pres_pre) if buy_pres_pre else 0.5,
            buy_pressure_base=sum(buy_pres_base) / len(buy_pres_base) if buy_pres_base else 0.5,
            avg_trade_size_usd=avg_size,
            timing_regularity=timing_reg,
            peak_hour_utc=peak_hour,
            dominant_side=dominant_side,
            size_profile=_size_profile(avg_size),
            entity_match=entity_key,
            entity_confidence=conf,
            event_timestamps=sorted(set(event_tss)),
        ))

    profiles.sort(key=lambda p: p.avg_foreknowledge_score, reverse=True)
    return profiles


# ─────────────────────────────────────────────────────────────────────────────
# RENDERING
# ─────────────────────────────────────────────────────────────────────────────

def _bar(val: float, lo: float, hi: float, width: int = 16,
         col: str = GRN) -> str:
    frac  = (val - lo) / (hi - lo) if hi != lo else 0
    frac  = max(0.0, min(1.0, frac))
    filled = int(frac * width)
    return f"{col}{'█' * filled}{'░' * (width - filled)}{RST}"


def render_orderbook(ob: Dict, pair: str) -> None:
    """ASCII order book rendering."""
    asks = ob.get("asks", [])[:15]
    bids = ob.get("bids", [])[:15]
    W = 70
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  LIVE ORDER BOOK — {pair}{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")

    max_vol = max(
        [v for _, v in asks + bids] or [1.0]
    )

    print(f"  {RED}{'ASKS (SELL WALL)':^30}{RST}")
    for price, vol in reversed(asks):
        notional = price * vol
        bar_len  = int(vol / max_vol * 25)
        tag = _c(f"${notional:>10,.0f}", RED)
        print(f"  {RED}{price:>12.2f}{RST}  "
              f"{RED}{'█' * bar_len:25s}{RST}  {tag}")

    print(f"  {BOLD}{'─' * W}{RST}")

    print(f"  {GRN}{'BIDS (BUY WALL)':^30}{RST}")
    for price, vol in bids:
        notional = price * vol
        bar_len  = int(vol / max_vol * 25)
        tag = _c(f"${notional:>10,.0f}", GRN)
        print(f"  {GRN}{price:>12.2f}{RST}  "
              f"{GRN}{'█' * bar_len:25s}{RST}  {tag}")

    # Spread
    if asks and bids:
        spread = asks[-1][0] - bids[0][0]
        mid    = (asks[-1][0] + bids[0][0]) / 2
        print(f"\n  Mid: {BOLD}${mid:,.2f}{RST}   Spread: {YEL}${spread:.2f}{RST}")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")


def render_event_forensics(ef: EventForensics) -> None:
    """Full forensics report for one event."""
    W = 78
    gcol = GRADE_COLOUR.get(ef.grade, WHT)
    fk   = ef.foreknowledge_score
    fk_col = RED if fk > 2 else YEL if fk > 1 else GRN

    print(f"\n{BOLD}{CYN}{'┌' + '─' * (W-2) + '┐'}{RST}")
    print(f"{BOLD}{CYN}│{' ' * (W-2)}│{RST}")
    dt_str = ef.dt.strftime("%Y-%m-%d %H:%M UTC")
    hdr = f"  {ef.event_type.upper()}  {ef.raw_magnitude}  — {dt_str}"
    print(f"{BOLD}{CYN}│{hdr:<{W-2}}│{RST}")
    loc = f"  Location: {ef.location[:55]}"
    print(f"{BOLD}{CYN}│{loc:<{W-2}}│{RST}")
    grade_line = f"  Lyra Grade: {gcol}{ef.grade}{RST}"
    print(f"{BOLD}{CYN}│  Lyra Grade: {gcol}{ef.grade:<16}{RST}{' '*(W-30)}│")
    print(f"{BOLD}{CYN}│{' ' * (W-2)}│{RST}")
    print(f"{BOLD}{CYN}{'└' + '─' * (W-2) + '┘'}{RST}")

    # Window comparison table
    windows = [ef.baseline, ef.pre_event, ef.impact, ef.post_event]
    print(f"\n  {'WINDOW':<14} {'N TRADES':>9} {'NOTIONAL':>14} {'BUY%':>7} "
          f"{'WHALE%':>8} {'AVG SIZE':>10} {'TIMING_REG':>12}")
    print(f"  {'─'*14} {'─'*9} {'─'*14} {'─'*7} {'─'*8} {'─'*10} {'─'*12}")

    for w in windows:
        label_col = (fk_col if w.label == "pre-event" and fk > 1
                     else CYN if w.label == "baseline" else WHT)
        bp_col    = (GRN if w.buy_pressure > 0.55 else
                     RED if w.buy_pressure < 0.45 else WHT)
        print(f"  {label_col}{w.label:<14}{RST} "
              f"{w.n_trades:>9,}  "
              f"${w.total_notional:>12,.0f}  "
              f"{bp_col}{w.buy_pressure*100:>5.1f}%{RST}  "
              f"{w.whale_ratio*100:>6.1f}%  "
              f"${w.avg_trade_size:>8,.0f}  "
              f"{w.timing_regularity:>12.3f}")

    # Foreknowledge score
    fk_bar = _bar(min(fk, 5), 0, 5, 20, fk_col)
    print(f"\n  FOREKNOWLEDGE SCORE:  {fk_col}{BOLD}{fk:+.2f}σ{RST}  {fk_bar}")
    if fk > 3:
        print(f"  {RED}{BOLD}  ⚠ EXTREME: Pre-event accumulation >3σ above baseline{RST}")
    elif fk > 2:
        print(f"  {YEL}{BOLD}  ⚑ HIGH:    Statistically anomalous pre-event buying{RST}")
    elif fk > 1:
        print(f"  {YEL}  ↑ ELEVATED: Mild pre-event positioning detected{RST}")
    else:
        print(f"  {GRN}  ✓ CLEAR:    No unusual pre-event accumulation{RST}")

    # Large pre-event actors
    if ef.actors_pre:
        print(f"\n  {BOLD}LARGE PRE-EVENT ACTORS (≥$10k, −90m window):{RST}")
        print(f"  {'#':>3} {'SIDE':<7} {'TOTAL USD':>12} {'TRADES':>7} "
              f"{'AVG PRICE':>12} {'DURATION':>10} {'FP':>10}")
        print(f"  {'─'*3} {'─'*7} {'─'*12} {'─'*7} {'─'*12} {'─'*10} {'─'*10}")
        for i, a in enumerate(ef.actors_pre[:8], 1):
            side_col = GRN if a["side_bias"] == "BUY" else \
                       RED if a["side_bias"] == "SELL" else YEL
            dur = f"{a['duration_sec']:.0f}s"
            print(f"  {i:>3} {side_col}{a['side_bias']:<7}{RST} "
                  f"${a['total_usd']:>10,.0f}  "
                  f"{a['trade_count']:>7}  "
                  f"${a['price_entry']:>10,.2f}  "
                  f"{dur:>10}  "
                  f"{DIM}{a['fingerprint']}{RST}")

    # Size bucket breakdown
    print(f"\n  {BOLD}PRE-EVENT SIZE DISTRIBUTION:{RST}")
    buckets = ef.pre_event.size_buckets()
    total_b = sum(buckets.values()) or 1
    for bname, bcount in buckets.items():
        pct = bcount / total_b * 100
        bar_len = int(pct / 5)
        col = RED if "whale" in bname or "mega" in bname else \
              YEL if "inst" in bname else GRN
        print(f"  {col}{bname:<20}{RST}  {bcount:>5} trades  "
              f"{col}{'█' * bar_len}{RST} {pct:4.1f}%")


def render_who_knew_table(profiles: List[ActorProfile]) -> None:
    """The money shot — ranked 'WHO KNEW?' table."""
    W = 90
    print(f"\n{BOLD}{RED}{'═' * W}{RST}")
    print(f"{BOLD}{RED}  🔍 WHO KNEW?  —  FOREKNOWLEDGE RANKING{RST}")
    print(f"{DIM}  Actors ranked by anomalous pre-event buy pressure across all planetary events{RST}")
    print(f"{BOLD}{RED}{'═' * W}{RST}")
    print(f"  {'RK':>3}  {'ENTITY / FINGERPRINT':<28} {'EVENTS':>7} "
          f"{'FK SCORE':>9} {'BUY PRE':>8} {'BUY BASE':>9} "
          f"{'SIZE':>6} {'PROFILE':<16} {'MATCH'}")
    print(f"  {'─'*3}  {'─'*28} {'─'*7} {'─'*9} {'─'*8} {'─'*9} "
          f"{'─'*6} {'─'*16} {'─'*20}")

    for rank, p in enumerate(profiles[:25], 1):
        fk_col = (RED + BOLD if p.avg_foreknowledge_score > 3 else
                  RED        if p.avg_foreknowledge_score > 2 else
                  YEL        if p.avg_foreknowledge_score > 1 else GRN)

        if p.entity_match:
            ent = KNOWN_ENTITIES[p.entity_match]
            match_str = (f"{ent['country']} {ent['animal']} "
                         f"{ent['name'][:20]}  ({p.entity_confidence:.0%})")
        else:
            match_str = _c(f"Unknown-{p.fingerprint_id}", DIM)

        label = (p.entity_match or f"fp:{p.fingerprint_id}")[:27]
        print(f"  {rank:>3}  {fk_col}{label:<28}{RST} "
              f"{p.events_seen:>7}  "
              f"{fk_col}{p.avg_foreknowledge_score:>+8.2f}σ{RST}  "
              f"{p.buy_pressure_pre*100:>7.1f}%  "
              f"{p.buy_pressure_base*100:>8.1f}%  "
              f"${p.avg_trade_size_usd/1000:>4.0f}k  "
              f"{p.size_profile:<16}  "
              f"{match_str}")

    print(f"{BOLD}{RED}{'─' * W}{RST}")
    print(f"  {DIM}FK SCORE: σ from baseline buy-pressure.  "
          f"{RED}>2σ = HIGH SUSPICION{RST}{DIM},  "
          f">3σ = EXTREME FOREKNOWLEDGE SIGNAL{RST}")

    # Count suspects
    hot = [p for p in profiles if p.avg_foreknowledge_score > 2.0]
    if hot:
        print(f"\n  {RED}{BOLD}⚠  {len(hot)} ACTOR(S) WITH FOREKNOWLEDGE SCORE > 2σ{RST}")
        for p in hot:
            ent_name = KNOWN_ENTITIES[p.entity_match]["name"] \
                if p.entity_match else f"Unknown-{p.fingerprint_id}"
            dates = [datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")
                     for ts in p.event_timestamps[:3]]
            print(f"    → {RED}{ent_name}{RST}  "
                  f"(events: {', '.join(dates)}{'…' if len(p.event_timestamps)>3 else ''})")
    print(f"{BOLD}{RED}{'═' * W}{RST}")


def render_order_flow_timeline(forensics_list: List[EventForensics]) -> None:
    """ASCII heatmap: event date vs buy pressure delta (pre vs baseline)."""
    W = 78
    print(f"\n{BOLD}{CYN}{'═' * W}{RST}")
    print(f"{BOLD}{CYN}  ORDER FLOW DELTA MAP — Pre-event vs Baseline Buy Pressure{RST}")
    print(f"{DIM}  Each row = one planetary event.  Bar = pre−baseline buy pressure delta.{RST}")
    print(f"  {'DATE':<12} {'TYPE':<14} {'GRADE':<18} {'FK':>6}  {'FLOW DELTA':<30}")
    print(f"  {'─'*12} {'─'*14} {'─'*18} {'─'*6}  {'─'*30}")
    for ef in sorted(forensics_list, key=lambda e: e.event_ts):
        delta = ef.pre_event.buy_pressure - ef.baseline.buy_pressure
        bar_width = 20
        pos = int((delta + 0.5) * bar_width)  # delta ∈ [-0.5, +0.5] → 0..20
        pos = max(0, min(bar_width, pos))
        bar = list("·" * bar_width)
        bar[bar_width // 2] = "│"
        if pos > bar_width // 2:
            for i in range(bar_width // 2 + 1, pos + 1):
                if 0 <= i < bar_width:
                    bar[i] = "█"
            bar_str = GRN + "".join(bar) + RST
        else:
            for i in range(pos, bar_width // 2):
                if 0 <= i < bar_width:
                    bar[i] = "█"
            bar_str = RED + "".join(bar) + RST
        dt_s  = ef.dt.strftime("%Y-%m-%d")
        gcol  = GRADE_COLOUR.get(ef.grade, WHT)
        fkcol = RED if ef.foreknowledge_score > 2 else \
                YEL if ef.foreknowledge_score > 1 else GRN
        print(f"  {dt_s:<12} {ef.event_type[:14]:<14} "
              f"{gcol}{ef.grade[:18]:<18}{RST} "
              f"{fkcol}{ef.foreknowledge_score:>+5.1f}σ{RST}  "
              f"{bar_str}  {delta*100:+.1f}%")
    print(f"{BOLD}{CYN}{'═' * W}{RST}")


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="ATN Forensics — who positioned before planetary events?"
    )
    parser.add_argument("--days",  type=int, default=180,
                        help="Lookback days for event selection (default 180)")
    parser.add_argument("--pair",  type=str, default="XBTUSD",
                        help="Kraken pair (default XBTUSD)")
    parser.add_argument("--min-grade", type=str,
                        default="DISSONANCE",
                        choices=["PARTIAL_HARMONY", "DISSONANCE", "SILENCE"],
                        help="Minimum harmonic grade to investigate")
    parser.add_argument("--max-events", type=int, default=10,
                        help="Max events to analyse (each = ~20 API calls)")
    parser.add_argument("--orderbook", action="store_true",
                        help="Show live order book snapshot")
    parser.add_argument("--verbose", action="store_true",
                        help="Full per-event report")
    args = parser.parse_args()

    W = 80
    print(f"\n{BOLD}{RED}{'╔' + '═'*(W-2) + '╗'}{RST}")
    print(f"{BOLD}{RED}║{'  AUREON ATN FORENSICS — WHO KNEW?':^{W-2}}║{RST}")
    print(f"{BOLD}{RED}║{'  Order Flow Intelligence × Planetary Event Correlation':^{W-2}}║{RST}")
    print(f"{BOLD}{RED}{'╚' + '═'*(W-2) + '╝'}{RST}\n")

    # ── Pull planetary events first (reuse backtest fetchers) ─────────────
    print("  Loading planetary event catalogue…")
    end   = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)

    from aureon.atn.aureon_atn_backtest import (
        fetch_earthquakes, fetch_solar_flares,
        fetch_geomagnetic_storms, PlanetaryEvent,
    )
    import urllib3; urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    all_events: List[PlanetaryEvent] = []
    all_events += fetch_earthquakes(start, end, min_mag=6.5)
    all_events += fetch_solar_flares(start, end)
    all_events += fetch_geomagnetic_storms(start, end)
    all_events.sort(key=lambda e: e.timestamp)

    # Filter to min grade
    grade_order = {"DIVINE_HARMONY": 0, "CLEAR_RESONANCE": 1,
                   "PARTIAL_HARMONY": 2, "DISSONANCE": 3, "SILENCE": 4}
    min_rank = grade_order[args.min_grade]
    filtered = [e for e in all_events
                if grade_order.get(e.grade, 0) >= min_rank]
    # Sort by severity descending — investigate the biggest first
    filtered.sort(key=lambda e: e.severity, reverse=True)
    target_events = filtered[:args.max_events]

    print(f"\n  {BOLD}Total events:    {len(all_events)}{RST}")
    print(f"  {BOLD}Eligible events: {len(filtered)} (grade ≥ {args.min_grade}){RST}")
    print(f"  {BOLD}Analysing:       {len(target_events)} most severe{RST}\n")

    if not target_events:
        print(f"  {YEL}No events found matching criteria.{RST}")
        return

    # ── Live order book snapshot ───────────────────────────────────────────
    if args.orderbook:
        ob = _kraken_orderbook_snapshot(args.pair, count=20)
        if ob:
            render_orderbook(ob, args.pair)

    # ── Forensic analysis per event ────────────────────────────────────────
    all_forensics: List[EventForensics] = []
    for i, evt in enumerate(target_events, 1):
        dt_str = datetime.fromtimestamp(evt.timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M")
        gcol   = GRADE_COLOUR.get(evt.grade, WHT)
        print(f"  [{i}/{len(target_events)}] Analysing "
              f"{gcol}{evt.event_type}{RST} "
              f"{evt.raw_magnitude} @ {dt_str} "
              f"({gcol}{evt.grade}{RST}) …", flush=True)

        ef = analyse_event(
            event_ts=evt.timestamp,
            event_type=evt.event_type,
            raw_magnitude=evt.raw_magnitude,
            grade=evt.grade,
            location=evt.location,
            pair=args.pair,
        )
        all_forensics.append(ef)

        if args.verbose:
            render_event_forensics(ef)
        else:
            fk = ef.foreknowledge_score
            fkcol = RED if fk > 2 else YEL if fk > 1 else GRN
            pre_trades = ef.pre_event.n_trades
            base_trades = ef.baseline.n_trades
            print(f"     FK={fkcol}{fk:+.2f}σ{RST}  "
                  f"pre={pre_trades} trades  "
                  f"base={base_trades} trades  "
                  f"pre_buy={ef.pre_event.buy_pressure*100:.1f}%  "
                  f"base_buy={ef.baseline.buy_pressure*100:.1f}%")

    # ── Actor profiles across all events ──────────────────────────────────
    print(f"\n  Building entity profiles across {len(all_forensics)} events …")
    actor_profiles = build_actor_profiles(all_forensics)
    print(f"  {len(actor_profiles)} unique actor fingerprints identified.")

    # ── Render outputs ─────────────────────────────────────────────────────
    render_order_flow_timeline(all_forensics)
    render_who_knew_table(actor_profiles)

    # ── Verbose: show top 3 events in full ────────────────────────────────
    if not args.verbose and all_forensics:
        print(f"\n  {BOLD}Top 3 events (by foreknowledge score) — detailed view:{RST}")
        for ef in sorted(all_forensics,
                         key=lambda e: e.foreknowledge_score, reverse=True)[:3]:
            render_event_forensics(ef)

    print(f"\n{BOLD}{RED}{'═' * W}{RST}")
    print(f"  {BOLD}Investigation complete.{RST}")
    print(f"  {DIM}This data is from public exchange feeds.  "
          f"All analysis is statistical inference,{RST}")
    print(f"  {DIM}not direct identification of any individual or entity.{RST}")
    print(f"{BOLD}{RED}{'═' * W}{RST}\n")


if __name__ == "__main__":
    main()
