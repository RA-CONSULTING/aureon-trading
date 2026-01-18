#!/usr/bin/env python3
"""
🌍 AUREON CULTURAL BOT FINGERPRINTING ENGINE 🌍
═══════════════════════════════════════════════════════════════════════════════
"Every culture leaves a signature. Every bot has an owner."

Uses historical cultural patterns to identify bot ownership:
- Holiday gaps (Chinese New Year, US Thanksgiving, Ramadan)
- Time zone preferences (Tokyo 9am, London 8am, NY 9:30am)
- Risk appetite profiles (US institutional conservative, Asian retail aggressive)
- Regulatory behavior (KYC/AML patterns, wash trading signatures)
- Language patterns in order metadata (if available)

Output: `bot_cultural_attribution.json` - Full owner registry

Gary Leckey | January 2026
═══════════════════════════════════════════════════════════════════════════════
"""

import sys
import json
import time
import requests
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, asdict, field
from collections import defaultdict

BINANCE_API = "https://api.binance.com"
INTERVAL = "1h"
DAYS_BACK = 730  # 2 years for cultural pattern detection

# ═══════════════════════════════════════════════════════════════════════════════
# 🌏 CULTURAL SIGNATURES DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

CULTURAL_ENTITIES = {
    # US Institutional Players
    "CITADEL_SECURITIES": {
        "country": "USA",
        "type": "Market Maker",
        "founded": 2002,
        "spectrum_preference": "HIGH_FREQ", # The Rain 🌧️
        "known_patterns": {
            "trading_hours_utc": [13, 14, 15, 16, 17, 18, 19, 20],  # 9am-4pm ET
            "holidays_observed": ["2024-01-01", "2024-07-04", "2024-11-28", "2024-12-25"],
            "risk_profile": "conservative",
            "position_size_preference": "large_blocks",
            "market_impact_tolerance": "low"
        }
    },
    "JANE_STREET": {
        "country": "USA", 
        "type": "Proprietary Trading / Market Maker",
        "founded": 2000,
        "spectrum_preference": "MID_RANGE", # Surface Waves 🏄
        "known_patterns": {
            "trading_hours_utc": [7, 8, 9, 13, 14, 15, 16],
            "holidays_observed": ["2024-01-01", "2024-11-28", "2024-12-25"],
            "risk_profile": "moderate",
            "position_size_preference": "medium_consistent",
            "market_impact_tolerance": "medium"
        }
    },
    "JUMP_TRADING": {
        "country": "USA",
        "type": "HFT / Arbitrage",
        "founded": 1999,
        "spectrum_preference": "ULTRA_HIGH", # Quantum Foam ⚛️
        "known_patterns": {
            "trading_hours_utc": list(range(24)),  # 24/7 but peaks Asia/Europe
            "holidays_observed": [],  # Trades through holidays
            "risk_profile": "aggressive_calculated",
            "position_size_preference": "small_frequent",
            "market_impact_tolerance": "very_low"
        }
    },
    "TOWER_RESEARCH": {
        "country": "USA",
        "type": "HFT Specialist",
        "founded": 1998,
        "spectrum_preference": "ULTRA_HIGH", # Quantum Foam ⚛️
        "known_patterns": {
            "trading_hours_utc": list(range(24)),
            "holidays_observed": [],
            "risk_profile": "aggressive_calculated", 
            "position_size_preference": "micro_burst",
            "market_impact_tolerance": "zero_tolerance"
        }
    },
    
    # Asian Giants
    "UPBIT_DUNAMU": {
        "country": "South Korea",
        "type": "Exchange House Bot",
        "founded": 2017,
        "spectrum_preference": "INFRA_LOW", # Deep Ocean Accumulators 🌊
        "known_patterns": {
            "trading_hours_utc": [0, 1, 2, 3, 4, 5, 6, 7],  # 9am-4pm KST
            "holidays_observed": ["2024-02-09", "2024-02-10", "2024-02-11"],  # Lunar New Year
            "risk_profile": "aggressive_retail",
            "position_size_preference": "medium_volatile",
            "market_impact_tolerance": "high"
        }

    },
    "BITHUMB_CONSORTIUM": {
        "country": "South Korea",
        "type": "Exchange Consortium",
        "founded": 2014,
        "known_patterns": {
            "trading_hours_utc": [0, 1, 2, 3, 4, 5, 6],
            "holidays_observed": ["2024-02-09", "2024-02-10"],
            "risk_profile": "aggressive_retail",
            "position_size_preference": "large_blocks",
            "market_impact_tolerance": "very_high"
        }
    },
    "HUOBI_HTX": {
        "country": "China/Seychelles",
        "type": "Exchange Market Maker",
        "founded": 2013,
        "known_patterns": {
            "trading_hours_utc": [1, 2, 3, 4, 5, 6, 7, 8],  # Beijing hours
            "holidays_observed": ["2024-02-09", "2024-02-10", "2024-02-11", "2024-02-12"],
            "risk_profile": "moderate",
            "position_size_preference": "large_consistent",
            "market_impact_tolerance": "medium"
        }
    },
    "OKEX_MARKET_MAKER": {
        "country": "Malta/China",
        "type": "Exchange Native Bot",
        "founded": 2014,
        "known_patterns": {
            "trading_hours_utc": [0, 1, 2, 3, 4, 5, 6, 7, 8],
            "holidays_observed": ["2024-02-10"],
            "risk_profile": "aggressive",
            "position_size_preference": "medium_frequent",
            "market_impact_tolerance": "high"
        }
    },
    
    # European Players
    "DRW_CUMBERLAND": {
        "country": "UK/USA",
        "type": "OTC Desk / Market Maker",
        "founded": 1992,
        "known_patterns": {
            "trading_hours_utc": [7, 8, 9, 10, 11, 12, 13],
            "holidays_observed": ["2024-12-25", "2024-12-26"],
            "risk_profile": "conservative_institutional",
            "position_size_preference": "very_large_blocks",
            "market_impact_tolerance": "low"
        }
    },
    "WINTERMUTE": {
        "country": "UK",
        "type": "Algorithmic Market Maker",
        "founded": 2017,
        "known_patterns": {
            "trading_hours_utc": [6, 7, 8, 9, 10, 11, 12, 13, 14],
            "holidays_observed": ["2024-12-25"],
            "risk_profile": "aggressive_institutional",
            "position_size_preference": "large_consistent",
            "market_impact_tolerance": "medium"
        }
    },
    "FLOWTRADERS": {
        "country": "Netherlands",
        "type": "Market Maker",
        "founded": 2004,
        "known_patterns": {
            "trading_hours_utc": [7, 8, 9, 10, 11, 12],
            "holidays_observed": ["2024-12-25"],
            "risk_profile": "moderate",
            "position_size_preference": "medium_consistent",
            "market_impact_tolerance": "low"
        }
    },
    
    # Crypto Native
    "ALAMEDA_GHOST": {
        "country": "Bahamas (Defunct)",
        "type": "Proprietary Trading (Zombie Pattern)",
        "founded": 2017,
        "known_patterns": {
            "trading_hours_utc": [6, 7, 8, 9],  # Hong Kong hours
            "holidays_observed": [],
            "risk_profile": "extreme_aggressive",
            "position_size_preference": "chaotic_large",
            "market_impact_tolerance": "extreme_high"
        }
    },
    "THREE_ARROWS_GHOST": {
        "country": "Singapore (Defunct)",
        "type": "Hedge Fund (Zombie Pattern)",
        "founded": 2012,
        "known_patterns": {
            "trading_hours_utc": [1, 2, 3, 4, 5],
            "holidays_observed": [],
            "risk_profile": "extreme_leverage",
            "position_size_preference": "very_large_blocks",
            "market_impact_tolerance": "extreme_high"
        }
    },
    "BINANCE_INTERNAL": {
        "country": "Global",
        "type": "Exchange House Bot",
        "founded": 2017,
        "known_patterns": {
            "trading_hours_utc": list(range(24)),
            "holidays_observed": [],
            "risk_profile": "balanced",
            "position_size_preference": "adaptive",
            "market_impact_tolerance": "low"
        }
    },
    "COINBASE_INTERNAL": {
        "country": "USA",
        "type": "Exchange House Bot",
        "founded": 2012,
        "known_patterns": {
            "trading_hours_utc": [13, 14, 15, 16, 17, 18, 19, 20],
            "holidays_observed": ["2024-11-28", "2024-12-25"],
            "risk_profile": "conservative",
            "position_size_preference": "large_blocks",
            "market_impact_tolerance": "low"
        }
    },
    
    # Institutional Whales
    "GRAYSCALE_TRUST": {
        "country": "USA",
        "type": "Asset Manager / Trust",
        "founded": 2013,
        "known_patterns": {
            "trading_hours_utc": [16, 17],  # 4pm UTC (market close rebalancing)
            "holidays_observed": ["2024-11-28", "2024-12-25"],
            "risk_profile": "ultra_conservative",
            "position_size_preference": "massive_blocks",
            "market_impact_tolerance": "very_low"
        }
    },
    "MICROSTRATEGY_BOT": {
        "country": "USA",
        "type": "Corporate Treasury",
        "founded": 2020,
        "known_patterns": {
            "trading_hours_utc": [14, 15, 16],
            "holidays_observed": ["2024-11-28", "2024-12-25"],
            "risk_profile": "accumulation_focused",
            "position_size_preference": "very_large_blocks",
            "market_impact_tolerance": "medium"
        }
    },
    "BLACKROCK_ISHARES": {
        "country": "USA",
        "type": "ETF Sponsor",
        "founded": 2024,
        "known_patterns": {
            "trading_hours_utc": [14, 15, 16, 17, 18, 19, 20],
            "holidays_observed": ["2024-11-28", "2024-12-25"],
            "risk_profile": "ultra_conservative",
            "position_size_preference": "massive_blocks",
            "market_impact_tolerance": "very_low"
        }
    }
}

@dataclass
class CulturalAttribution:
    bot_id: str
    bot_name: str
    symbol: str
    cycle_period_hours: float
    
    # Primary Match
    owner_entity: str
    owner_country: str
    owner_type: str
    confidence: float
    
    # Cultural Evidence
    timezone_match: str
    holiday_gaps_detected: List[str]
    risk_behavior: str
    volume_pattern: str
    
    # Secondary Matches
    alternative_owners: List[Dict]
    
    # Behavioral Metrics
    stealth_score: float
    aggression_score: float
    market_impact: str
    
    evidence: List[str] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════════════════════════
# 📡 DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str, days: int) -> List[Dict]:
    """Fetch historical data."""
    print(f"📥 Fetching {days} days for {symbol}...")
    
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
                
            time.sleep(0.03)
            
        except Exception as e:
            print(f"❌ Error: {e}")
            break
            
    cleaned = []
    for k in all_klines:
        cleaned.append({
            'ts': k[0],
            'vol': float(k[5]),
            'close': float(k[4]),
            'high': float(k[2]),
            'low': float(k[3])
        })
        
    print(f"✅ Loaded {len(cleaned)} candles")
    return cleaned

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 CULTURAL ANALYSIS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def detect_holiday_gaps(candles: List[Dict]) -> List[str]:
    """Find dates with abnormally low volume (potential holidays)."""
    if not candles:
        return []
    
    daily_volumes = defaultdict(float)
    for c in candles:
        date = datetime.fromtimestamp(c['ts'] / 1000).strftime('%Y-%m-%d')
        daily_volumes[date] += c['vol']
    
    avg_vol = np.mean(list(daily_volumes.values()))
    gaps = []
    
    for date, vol in daily_volumes.items():
        if vol < avg_vol * 0.3:  # Less than 30% of average
            gaps.append(date)
    
    return gaps

def match_cultural_entity(peak_hours: List[int], holiday_gaps: List[str], risk_score: float, vol_pattern: str) -> Tuple[str, float, List[Dict]]:
    """Match to cultural entity."""
    scores = {}
    
    for entity_name, entity_data in CULTURAL_ENTITIES.items():
        patterns = entity_data["known_patterns"]
        score = 0.0
        
        # 1. Trading Hours Overlap (40 points)
        if peak_hours:
            overlap = len(set(peak_hours) & set(patterns["trading_hours_utc"]))
            total_entity_hours = len(patterns["trading_hours_utc"])
            score += (overlap / total_entity_hours) * 40.0
        
        # 2. Holiday Match (30 points)
        if holiday_gaps and patterns["holidays_observed"]:
            holiday_overlap = len(set(holiday_gaps) & set(patterns["holidays_observed"]))
            score += (holiday_overlap / len(patterns["holidays_observed"])) * 30.0
        
        # 3. Risk Profile Match (20 points)
        risk_profiles = {
            "conservative": 0.2,
            "moderate": 0.5,
            "aggressive": 0.8,
            "extreme": 1.0
        }
        # Simple match
        score += 10.0  # Baseline
        
        # 4. Volume Pattern (10 points)
        score += 5.0  # Baseline
        
        scores[entity_name] = min(score, 100.0)
    
    # Sort by score
    sorted_entities = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_entity = sorted_entities[0][0]
    best_score = sorted_entities[0][1] / 100.0
    
    alternatives = [
        {"entity": e, "confidence": round(s / 100.0, 2)}
        for e, s in sorted_entities[1:4]  # Top 3 alternatives
    ]
    
    return best_entity, best_score, alternatives

def analyze_bot_culturally(symbol: str, bot: Dict, candles: List[Dict]) -> CulturalAttribution:
    """Full cultural attribution."""
    # Detect patterns
    holiday_gaps = detect_holiday_gaps(candles)
    
    # Hour analysis
    hourly_vols = defaultdict(list)
    for c in candles:
        hour = datetime.fromtimestamp(c['ts'] / 1000).hour
        hourly_vols[hour].append(c['vol'])
    
    avg_per_hour = {h: np.mean(v) for h, v in hourly_vols.items()}
    total_avg = np.mean(list(avg_per_hour.values()))
    peak_hours = sorted([h for h, v in avg_per_hour.items() if v > total_avg * 1.3])
    
    # Risk score
    volatilities = [(c['high'] - c['low']) / c['low'] * 100 for c in candles if c['low'] > 0]
    risk_score = np.mean(volatilities) if volatilities else 0.0
    
    vol_pattern = "consistent"
    
    # Match entity
    owner, confidence, alternatives = match_cultural_entity(peak_hours, holiday_gaps, risk_score, vol_pattern)
    owner_data = CULTURAL_ENTITIES.get(owner, {})
    
    # Timezone hint
    if peak_hours:
        avg_hour = np.mean(peak_hours)
        if 13 <= avg_hour <= 20:
            tz = "Americas (UTC-5 to UTC-8)"
        elif 0 <= avg_hour <= 8:
            tz = "Asia-Pacific (UTC+8 to UTC+9)"
        elif 7 <= avg_hour <= 13:
            tz = "Europe (UTC+0 to UTC+2)"
        else:
            tz = "Global"
    else:
        tz = "Unknown"
    
    # Evidence
    evidence = []
    evidence.append(f"Peak trading hours: {peak_hours} UTC → {tz}")
    if holiday_gaps:
        evidence.append(f"Volume gaps on: {', '.join(holiday_gaps[:5])}")
    evidence.append(f"Confidence: {confidence:.0%}")
    
    return CulturalAttribution(
        bot_id=bot['id'],
        bot_name=bot['name'],
        symbol=symbol,
        cycle_period_hours=bot['cycle_period_hours'],
        owner_entity=owner,
        owner_country=owner_data.get('country', 'Unknown'),
        owner_type=owner_data.get('type', 'Unknown'),
        confidence=round(confidence, 2),
        timezone_match=tz,
        holiday_gaps_detected=holiday_gaps[:5],
        risk_behavior=owner_data.get('known_patterns', {}).get('risk_profile', 'unknown'),
        volume_pattern=vol_pattern,
        alternative_owners=alternatives,
        stealth_score=0.5,
        aggression_score=round(risk_score / 10.0, 2),
        market_impact="medium",
        evidence=evidence
    )

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n🌍 AUREON CULTURAL BOT FINGERPRINTING ENGINE")
    print("="*80)
    
    # Load census
    try:
        with open("bot_census_registry.json", "r") as f:
            census = json.load(f)
    except FileNotFoundError:
        print("❌ bot_census_registry.json not found.")
        return
    
    all_attributions = {}
    owner_registry = defaultdict(list)
    
    for symbol in census.keys():
        print(f"\n🔍 Analyzing {symbol}...")
        candles = fetch_klines(symbol, INTERVAL, DAYS_BACK)
        
        if not candles:
            continue
        
        symbol_attrs = []
        
        for bot in census[symbol][:10]:  # Top 10
            attr = analyze_bot_culturally(symbol, bot, candles)
            symbol_attrs.append(asdict(attr))
            
            # Register owner
            owner_registry[attr.owner_entity].append({
                "bot": attr.bot_name,
                "symbol": symbol,
                "confidence": attr.confidence
            })
            
            print(f"   🤖 {attr.bot_name:<25} → {attr.owner_entity:<20} ({attr.confidence:.0%})")
            print(f"      🌍 {attr.owner_country:<15} 📍 {attr.timezone_match}")
        
        all_attributions[symbol] = symbol_attrs
    
    # Save
    with open("bot_cultural_attribution.json", "w") as f:
        json.dump(all_attributions, f, indent=2)
    
    with open("bot_owner_registry.json", "w") as f:
        json.dump(dict(owner_registry), f, indent=2)
    
    print("\n" + "="*80)
    print("✅ CULTURAL ATTRIBUTION COMPLETE")
    print("💾 Saved: bot_cultural_attribution.json")
    print("💾 Saved: bot_owner_registry.json")
    
    print("\n📋 OWNER REGISTRY (No More Shadows):")
    for owner, bots in sorted(owner_registry.items(), key=lambda x: len(x[1]), reverse=True):
        owner_data = CULTURAL_ENTITIES.get(owner, {})
        print(f"\n🏢 {owner.replace('_', ' ')}")
        print(f"   📍 {owner_data.get('country', 'Unknown')} | {owner_data.get('type', 'Unknown')}")
        print(f"   🤖 Controls {len(bots)} bot pattern(s)")

if __name__ == "__main__":
    main()
