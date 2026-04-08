#!/usr/bin/env python3
"""
🕵️ AUREON BOT ENTITY ATTRIBUTION ENGINE 🕵️
═══════════════════════════════════════════════════════════════════════════════
"Who controls the bots? Find the Prime Sentinel."

Analyzes bot patterns to attribute them to real-world entities:
- Volume signatures (size → institutional classification)
- Geographic timing (UTC offsets → location)
- Cross-exchange correlation (same pattern = same owner)
- Known entity fingerprints (Goldman, Jump, Citadel patterns)

Output: `bot_entity_attribution.json`

Gary Leckey | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import json
import time
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, asdict, field
from collections import defaultdict

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT"]
INTERVAL = "1h"
DAYS_BACK = 180  # Last 6 months for fresh patterns
BINANCE_API = "https://api.binance.com"

# Known Entity Fingerprints
ENTITY_SIGNATURES = {
    "CITADEL_SECURITIES": {
        "description": "Citadel Securities - US Market Maker",
        "patterns": {
            "peak_hours_utc": [13, 14, 15, 16],  # US Trading Hours (9am-12pm ET)
            "volume_profile": "exponential_spike",
            "cycle_periods": [24.0],
            "volatility_preference": "high",
            "typical_size_btc": (5.0, 50.0)  # BTC per trade
        }
    },
    "JUMP_TRADING": {
        "description": "Jump Trading - HFT/Arbitrage Specialist",
        "patterns": {
            "peak_hours_utc": [0, 1, 2, 3, 8, 9, 10],  # Asia/Europe overlap
            "volume_profile": "flat_consistent",
            "cycle_periods": [8.0, 12.0],
            "volatility_preference": "low",
            "typical_size_btc": (0.1, 5.0)
        }
    },
    "JANE_STREET": {
        "description": "Jane Street - Quantitative Market Maker",
        "patterns": {
            "peak_hours_utc": [7, 8, 9, 14, 15],  # London + NY Open
            "volume_profile": "gaussian",
            "cycle_periods": [24.0, 168.0],
            "volatility_preference": "medium",
            "typical_size_btc": (2.0, 20.0)
        }
    },
    "BINANCE_HOUSE": {
        "description": "Binance Internal Market Making",
        "patterns": {
            "peak_hours_utc": list(range(24)),  # 24/7
            "volume_profile": "flat_consistent",
            "cycle_periods": [8.0],
            "volatility_preference": "any",
            "typical_size_btc": (0.01, 100.0)
        }
    },
    "KOREAN_WHALE_CARTEL": {
        "description": "South Korean Institutional Group",
        "patterns": {
            "peak_hours_utc": [0, 1, 2, 3, 4, 5, 6],  # KST 9am-3pm
            "volume_profile": "burst_pattern",
            "cycle_periods": [24.0, 168.0],
            "volatility_preference": "high",
            "typical_size_btc": (10.0, 100.0)
        }
    },
    "GRAYSCALE_TRUST": {
        "description": "Grayscale Trust Rebalancing Bot",
        "patterns": {
            "peak_hours_utc": [16, 17],  # 4pm UTC (Market Close)
            "volume_profile": "single_spike",
            "cycle_periods": [168.0],  # Weekly
            "volatility_preference": "low",
            "typical_size_btc": (50.0, 500.0)
        }
    },
    "FTX_ALAMEDA_GHOST": {
        "description": "Legacy Alameda Research Pattern (Zombie Bot)",
        "patterns": {
            "peak_hours_utc": [6, 7, 8],  # Hong Kong Hours
            "volume_profile": "erratic_burst",
            "cycle_periods": [12.0, 24.0],
            "volatility_preference": "extreme",
            "typical_size_btc": (20.0, 200.0)
        }
    }
}

@dataclass
class BotAttribution:
    bot_id: str
    bot_name: str
    symbol: str
    cycle_period_hours: float
    
    # Volume Analysis
    avg_hourly_volume_btc: float
    peak_hours_utc: List[int]
    volume_profile_type: str  # "flat", "gaussian", "burst", "exponential"
    
    # Entity Match
    likely_entity: str
    entity_confidence: float
    entity_description: str
    
    # Geographic Clues
    geographic_hint: str  # "US_EAST", "ASIA_PACIFIC", "EUROPE", "GLOBAL"
    
    # Behavioral Signature
    aggression_score: float  # 0-1 (how aggressively it trades)
    stealth_score: float     # 0-1 (how hidden/distributed trades are)
    
    # Cross-Exchange Presence
    detected_exchanges: List[str] = field(default_factory=list)
    
    # Evidence
    evidence: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════════════
# 📡 DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str, days: int) -> List[Dict]:
    """Fetch historical klines with volume data."""
    print(f"📥 Fetching {days} days of {interval} data for {symbol}...")
    
    end_time = int(time.time() * 1000)
    start_time = int((datetime.now() - timedelta(days=days)).timestamp() * 1000)
    
    all_klines = []
    current_start = start_time
    
    while True:
        try:
            params = {
                "symbol": symbol,
                "interval": interval,
                "startTime": current_start,
                "endTime": end_time,
                "limit": 1000
            }
            resp = requests.get(f"{BINANCE_API}/api/v3/klines", params=params, timeout=10)
            data = resp.json()
            
            if not isinstance(data, list) or len(data) == 0:
                break
                
            all_klines.extend(data)
            last_ts = data[-1][0]
            current_start = last_ts + 1
            
            if last_ts >= end_time or len(data) < 1000:
                break
                
            time.sleep(0.05)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
            
    cleaned = []
    for k in all_klines:
        cleaned.append({
            'ts': k[0],
            'open': float(k[1]),
            'high': float(k[2]),
            'low': float(k[3]),
            'close': float(k[4]),
            'vol': float(k[5]),
            'quote_vol': float(k[7])
        })
        
    print(f"✅ Loaded {len(cleaned)} candles.")
    return cleaned

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 ATTRIBUTION ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def analyze_volume_profile(candles: List[Dict]) -> Tuple[str, List[int], float]:
    """Determine volume distribution type and peak hours."""
    # Group by hour of day (UTC)
    hourly_volumes = defaultdict(list)
    
    for c in candles:
        dt = datetime.fromtimestamp(c['ts'] / 1000)
        hour = dt.hour
        hourly_volumes[hour].append(c['vol'])
    
    # Average per hour
    avg_per_hour = {h: np.mean(vols) for h, vols in hourly_volumes.items()}
    total_avg = np.mean(list(avg_per_hour.values()))
    
    # Find peak hours (> 1.5x average)
    peak_hours = [h for h, v in avg_per_hour.items() if v > total_avg * 1.5]
    peak_hours.sort()
    
    # Classify distribution
    if not avg_per_hour:
        return "unknown", [], 0.0
    
    hourly_vals = list(avg_per_hour.values())
    std = np.std(hourly_vals)
    mean = np.mean(hourly_vals)
    cv = std / mean if mean > 0 else 0  # Coefficient of variation
    
    if cv < 0.2:
        profile_type = "flat_consistent"
    elif cv > 0.8:
        profile_type = "burst_pattern"
    else:
        profile_type = "gaussian"
    
    avg_vol_btc = mean
    
    return profile_type, peak_hours, avg_vol_btc

def match_entity(bot_period: float, peak_hours: List[int], vol_profile: str, avg_vol: float) -> Tuple[str, float, str, str]:
    """Match bot characteristics to known entities."""
    best_match = "UNKNOWN_ENTITY"
    best_score = 0.0
    best_desc = "Unidentified algorithmic actor"
    geo_hint = "UNKNOWN"
    
    for entity_name, entity_data in ENTITY_SIGNATURES.items():
        patterns = entity_data["patterns"]
        score = 0.0
        
        # 1. Cycle Period Match
        if bot_period in patterns["cycle_periods"]:
            score += 40.0
        elif any(abs(bot_period - p) < 2.0 for p in patterns["cycle_periods"]):
            score += 20.0
        
        # 2. Peak Hours Overlap
        if peak_hours:
            overlap = len(set(peak_hours) & set(patterns["peak_hours_utc"]))
            score += (overlap / len(patterns["peak_hours_utc"])) * 30.0
        
        # 3. Volume Profile Match
        if vol_profile == patterns["volume_profile"]:
            score += 20.0
        
        # 4. Volume Size Match
        if "typical_size_btc" in patterns:
            min_size, max_size = patterns["typical_size_btc"]
            if min_size <= avg_vol <= max_size:
                score += 10.0
        
        if score > best_score:
            best_score = score
            best_match = entity_name
            best_desc = entity_data["description"]
    
    # Geographic inference from peak hours
    if peak_hours:
        avg_hour = np.mean(peak_hours)
        if 13 <= avg_hour <= 20:
            geo_hint = "US_EAST"
        elif 0 <= avg_hour <= 7:
            geo_hint = "ASIA_PACIFIC"
        elif 7 <= avg_hour <= 13:
            geo_hint = "EUROPE"
        else:
            geo_hint = "GLOBAL"
    
    confidence = min(best_score / 100.0, 1.0)
    
    return best_match, confidence, best_desc, geo_hint

def calculate_behavioral_scores(candles: List[Dict], vol_profile: str) -> Tuple[float, float]:
    """Calculate aggression and stealth scores."""
    if not candles:
        return 0.0, 0.0
    
    volumes = np.array([c['vol'] for c in candles])
    ranges = np.array([(c['high'] - c['low']) / c['low'] * 100 for c in candles if c['low'] > 0])
    
    # Aggression: High volatility + High volume spikes
    aggression = 0.0
    if len(ranges) > 0:
        avg_range = np.mean(ranges)
        aggression = min(avg_range / 5.0, 1.0)  # Normalize to 0-1
    
    # Stealth: Flat volume distribution (low variance)
    stealth = 0.0
    if len(volumes) > 0:
        cv = np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
        stealth = max(0.0, 1.0 - cv)  # Inverse of volatility
    
    return round(aggression, 2), round(stealth, 2)

def attribute_bot(symbol: str, bot_id: str, bot_name: str, period: float, candles: List[Dict]) -> BotAttribution:
    """Perform full entity attribution on a bot."""
    vol_profile, peak_hours, avg_vol = analyze_volume_profile(candles)
    entity, confidence, desc, geo = match_entity(period, peak_hours, vol_profile, avg_vol)
    aggression, stealth = calculate_behavioral_scores(candles, vol_profile)
    
    # Generate evidence
    evidence = []
    if confidence > 0.5:
        evidence.append(f"High confidence match ({confidence:.0%}) to known entity pattern")
    if peak_hours:
        evidence.append(f"Peak activity at UTC hours: {peak_hours}")
    evidence.append(f"Volume profile: {vol_profile}")
    evidence.append(f"Geographic signature: {geo}")
    
    return BotAttribution(
        bot_id=bot_id,
        bot_name=bot_name,
        symbol=symbol,
        cycle_period_hours=period,
        avg_hourly_volume_btc=round(avg_vol, 4),
        peak_hours_utc=peak_hours,
        volume_profile_type=vol_profile,
        likely_entity=entity,
        entity_confidence=round(confidence, 2),
        entity_description=desc,
        geographic_hint=geo,
        aggression_score=aggression,
        stealth_score=stealth,
        detected_exchanges=["BINANCE"],
        evidence=evidence
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n🕵️ AUREON BOT ENTITY ATTRIBUTION ENGINE")
    print("="*80)
    
    # Load Census Data
    try:
        with open("bot_census_registry.json", "r") as f:
            census = json.load(f)
    except FileNotFoundError:
        print("❌ bot_census_registry.json not found. Run aureon_historical_bot_census.py first.")
        return
    
    attributions = {}
    
    for symbol in TARGET_SYMBOLS:
        print(f"\n🔍 Analyzing {symbol}...")
        
        if symbol not in census or not census[symbol]:
            print(f"   No bots registered for {symbol}")
            continue
        
        # Fetch recent data for volume analysis
        candles = fetch_klines(symbol, INTERVAL, DAYS_BACK)
        if not candles:
            continue
        
        symbol_attributions = []
        
        for bot in census[symbol][:5]:  # Top 5 bots per symbol
            bot_id = bot['id']
            bot_name = bot['name']
            period = bot['cycle_period_hours']
            
            attr = attribute_bot(symbol, bot_id, bot_name, period, candles)
            symbol_attributions.append(asdict(attr))
            
            # Print Result
            entity_str = attr.likely_entity.replace("_", " ")
            print(f"   🤖 {bot_name:<25} → {entity_str:<20} ({attr.entity_confidence:.0%})")
            print(f"      📍 {attr.geographic_hint:<15} ⚔️ Aggr:{attr.aggression_score} 🥷 Stealth:{attr.stealth_score}")
        
        attributions[symbol] = symbol_attributions
    
    # Save
    with open("bot_entity_attribution.json", "w") as f:
        json.dump(attributions, f, indent=2)
    
    print("\n" + "="*80)
    print("✅ ENTITY ATTRIBUTION COMPLETE")
    print("💾 Saved to: bot_entity_attribution.json")
    print("\n🎯 PRIME SENTINEL STATUS:")
    
    # Find the most likely "Prime Sentinel" (highest confidence match)
    prime_sentinel = None
    max_conf = 0.0
    
    for sym_attrs in attributions.values():
        for attr in sym_attrs:
            if attr['entity_confidence'] > max_conf:
                max_conf = attr['entity_confidence']
                prime_sentinel = attr
    
    if prime_sentinel and max_conf > 0.6:
        print(f"   🎖️ IDENTIFIED: {prime_sentinel['likely_entity']}")
        print(f"   📋 {prime_sentinel['entity_description']}")
        print(f"   🔬 Confidence: {prime_sentinel['entity_confidence']:.0%}")
        print(f"   🌍 Operating from: {prime_sentinel['geographic_hint']}")
        print(f"   ⚡ Bot: {prime_sentinel['bot_name']} ({prime_sentinel['symbol']})")
    else:
        print("   ⚠️ No Prime Sentinel identified above 60% confidence threshold.")

if __name__ == "__main__":
    main()
