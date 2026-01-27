#!/usr/bin/env python3
"""
📜 AUREON HISTORICAL BOT CENSUS & EVOLUTION TRACKER 📜
═══════════════════════════════════════════════════════════════════════════════
Scans the last 4 years of market history to identify, label, and TRACK the 
growth of algorithmic actors.

Features:
- Fetches 4 years of 1h candles (Klines) from Binance.
- Performs FFT Spectral Analysis to find dominant cycles.
- "Time-Travels" via sliding windows to see when bots were BORN.
- Tracks "Bot Power" over time to classify growth (Explosive, Steady, Dying).
- Generates `bot_census_registry.json`.

Usage:
    python aureon_historical_bot_census.py

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

# ═══════════════════════════════════════════════════════════════════════════════
# ⚙️ CONFIG & DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

TARGET_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT", "ADAUSDT"]
INTERVAL = "1h" # 1 hour candles for macro structure
DAYS_BACK = 3000 # ~8 Years (Binance Inception)
WINDOW_DAYS = 90 # 3-month sliding window for evolution tracking
STEP_DAYS = 15   # Step size for sliding window
BINANCE_API = "https://api.binance.com"

@dataclass
class HistoricalBot:
    """A registered historical bot entity"""
    id: str                 # Unique ID (e.g., "BOT-BTC-24H")
    name: str               # Human readable name
    symbol: str
    cycle_period_hours: float
    confidence: float
    first_seen: str
    last_seen: str
    birth_date: str         # Date when signal first became significant
    growth_rate: str        # "Explosive", "Steady", "Declining", "Ancient"
    evolution_history: List[Dict] = field(default_factory=list) # Time series of strength {date, strength}
    description: str = ""

# ═══════════════════════════════════════════════════════════════════════════════
# 📡 DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════

def fetch_klines(symbol: str, interval: str, days: int) -> List[Dict]:
    """Fetch historical klines from Binance public API with pagination."""
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
            resp = requests.get(f"{BINANCE_API}/api/v3/klines", params=params)
            data = resp.json()
            
            if not isinstance(data, list) or len(data) == 0:
                break
                
            all_klines.extend(data)
            
            # Update start time to last candle + 1ms
            last_ts = data[-1][0]
            current_start = last_ts + 1
            
            if last_ts >= end_time or len(data) < 1000:
                break
                
            time.sleep(0.05) # Respect rate limits
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            break
            
    # Convert to structured list: [timestamp, open, high, low, close, volume]
    cleaned = []
    for k in all_klines:
        cleaned.append({
            'ts': k[0],
            'vol': float(k[5]),
            'close': float(k[4])
        })
        
    print(f"✅ Loaded {len(cleaned)} candles for {symbol}.")
    return cleaned

# ═══════════════════════════════════════════════════════════════════════════════
# 🧠 SPECTRAL CENSUS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

def get_spectral_strength(volumes: np.array, target_period_hours: float) -> float:
    """Calculate the normalized strength of a specific period in the given volume series."""
    n = len(volumes)
    if n < 24: return 0.0
    
    vol_centered = volumes - np.mean(volumes)
    fft_vals = np.fft.rfft(vol_centered)
    fft_freq = np.fft.rfftfreq(n, d=1.0) # d=1 hour
    
    magnitudes = np.abs(fft_vals)
    max_mag = np.max(magnitudes)
    if max_mag == 0: return 0.0
    
    # Target frequency
    target_freq = 1.0 / target_period_hours
    
    # Find closest frequency bin
    closest_idx = np.argmin(np.abs(fft_freq - target_freq))
    
    # Return normalized strength
    return float(magnitudes[closest_idx] / max_mag)

def track_evolution(symbol: str, full_candles: List[Dict], bots: List[HistoricalBot]):
    """Slide a window across history to see when bots appeared and grew."""
    print(f"   ⏳ Tracking evolution for {len(bots)} bots over {DAYS_BACK} days...")
    
    window_size_candles = WINDOW_DAYS * 24
    step_size_candles = STEP_DAYS * 24
    
    total_candles = len(full_candles)
    
    # Iterate through history
    for i in range(0, total_candles - window_size_candles, step_size_candles):
        window = full_candles[i : i + window_size_candles]
        if not window: continue
        
        window_start_ts = window[0]['ts']
        window_date = datetime.fromtimestamp(window_start_ts/1000).strftime('%Y-%m-%d')
        
        volumes = np.array([c['vol'] for c in window])
        
        # Check each bot in this window
        for bot in bots:
            strength = get_spectral_strength(volumes, bot.cycle_period_hours)
            
            bot.evolution_history.append({
                "date": window_date,
                "strength": round(strength, 3)
            })

    # Post-process evolution: Determine Birth Date and Growth Type
    for bot in bots:
        history = bot.evolution_history
        birth_date = "Ancient"
        
        # Find Birth Date (First time > 0.3 strength)
        for point in history:
            if point['strength'] > 0.3:
                birth_date = point['date']
                break
        
        bot.birth_date = birth_date
        
        # Analyze Trend (Slope of last 10 points or fewer)
        if len(history) > 5:
            recent_points = [p['strength'] for p in history[-10:]]
            # Simple linear fit
            try:
                slope = np.polyfit(range(len(recent_points)), recent_points, 1)[0]
                
                if slope > 0.02: bot.growth_rate = "Explosive 🚀"
                elif slope > 0.005: bot.growth_rate = "Growing 📈"
                elif slope < -0.01: bot.growth_rate = "Declining 📉"
                else: bot.growth_rate = "Steady ⚓"
            except:
                 bot.growth_rate = "Unknown"
        else:
            bot.growth_rate = "New 👶"

def analyze_history(symbol: str, candles: List[Dict]) -> List[HistoricalBot]:
    """Perform FFT on historical volume to find bot cycles."""
    if not candles:
        return []
    
    # 1. Global Scan (Full 4 Year Context)
    volumes = np.array([c['vol'] for c in candles])
    ts_start = candles[0]['ts']
    ts_end = candles[-1]['ts']
    
    vol_centered = volumes - np.mean(volumes)
    fft_vals = np.fft.rfft(vol_centered)
    fft_freq = np.fft.rfftfreq(len(volumes), d=1.0)
    magnitudes = np.abs(fft_vals)
    threshold = np.max(magnitudes) * 0.15 
    
    bots = []
    
    for i in range(1, len(magnitudes)-1):
        mag = magnitudes[i]
        freq_per_hour = fft_freq[i]
        if freq_per_hour == 0: continue
        period_hours = 1.0 / freq_per_hour
        
        if mag > magnitudes[i-1] and mag > magnitudes[i+1] and mag > threshold:
            if period_hours > 24 * 30: continue 
            if period_hours < 2: continue
            
            bot_name, bot_desc = generate_bot_identity(period_hours, symbol)
            bot_id = f"BOT-{symbol}-{int(period_hours)}H"
            
            bots.append(HistoricalBot(
                id=bot_id,
                name=bot_name,
                symbol=symbol,
                cycle_period_hours=round(period_hours, 2),
                confidence=round(float(mag / np.max(magnitudes)), 2),
                first_seen=datetime.fromtimestamp(ts_start/1000).strftime('%Y-%m-%d'),
                last_seen=datetime.fromtimestamp(ts_end/1000).strftime('%Y-%m-%d'),
                birth_date="Unknown",
                growth_rate="Unknown",
                description=bot_desc
            ))
            
    valid_bots = filter_duplicate_signals(bots)
    
    # 2. Evolution Tracking
    if valid_bots:
        track_evolution(symbol, candles, valid_bots)
        
    return valid_bots

def filter_duplicate_signals(bots: List[HistoricalBot]) -> List[HistoricalBot]:
    """Combine bots that are likely the same signal (spectral leakage)."""
    if not bots: return []
    sorted_bots = sorted(bots, key=lambda b: b.confidence, reverse=True)
    unique = []
    for b in sorted_bots:
        is_dupe = False
        for u in unique:
            if abs(b.cycle_period_hours - u.cycle_period_hours) / u.cycle_period_hours < 0.1:
                is_dupe = True
                break
        if not is_dupe:
            unique.append(b)
    return unique[:15] # Keep top 15 only to reduce noise

def generate_bot_identity(period_hours: float, symbol: str) -> Tuple[str, str]:
    """Give the bot a cool name based on its cycle."""
    p = period_hours
    
    if 23.5 <= p <= 24.5:
        name = "The Solar Clock Algorithm"
        desc = "Strict 24h cycle. Daily Settlement."
    elif 7.8 <= p <= 8.2:
        name = "The Funding Rate Farmer"
        desc = "8h Cycle. Times entries with funding rates."
    elif 3.8 <= p <= 4.2:
        name = "The 4H Trend Setter"
        desc = "4h Candle closure bot."
    elif 166 <= p <= 170:
        name = "The Weekend Whale"
        desc = "Weekly cycle (168h). Monday Mover."
    elif 11.8 <= p <= 12.2:
        name = "The Meridian Switcher"
        desc = "12h Cycle."
    elif p > 24 * 6.5 and p < 24 * 7.5:
         name = "The Weekly Pivot"
         desc = "Weekly rebalancing algo."
    elif p < 4:
         name = "High-Freq Macro"
         desc = "Fast intraday rebalancing."
    else:
        suffixes = ["Alpha", "Prime", "Sentinel", "Vector", "Ghost", "Pulse", "Titan"]
        adj = ["Silent", "Heavy", "Rapid", "Deep", "Cyclic", "Harmonic"]
        idx = int(p * 100) % len(suffixes)
        idx2 = int(p * 50) % len(adj)
        name = f"{adj[idx2]} {suffixes[idx]} {int(p)}H"
        desc = f"Unidentified periodic actor ({p:.1f}h)"
    
    return name, desc

# ═══════════════════════════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print(f"\n📜 STARTING AUREON HISTORICAL BOT CENSUS (DEEP SCAN: {DAYS_BACK} DAYS)")
    print("="*80)
    
    registry = {}
    
    for symbol in TARGET_SYMBOLS:
        klines = fetch_klines(symbol, INTERVAL, DAYS_BACK)
        if not klines:
            continue
            
        bots = analyze_history(symbol, klines)
        registry[symbol] = [asdict(b) for b in bots]
        
        print(f"\n>> {symbol} Bot Evolution Report:")
        if not bots:
            print("   No distinct periodic bots found.")
        else:
            print(f"   {'NAME':<25} {'PERIOD':<8} {'BIRTH DATE':<12} {'TREND':<10} {'CONF'}")
            print(f"   {'-'*25} {'-'*8} {'-'*12} {'-'*10} {'-'*5}")
            for b in bots:
                # Truncate trend string for display
                trend_display = b.growth_rate if len(b.growth_rate) < 12 else b.growth_rate[:10]
                print(f"   🤖 {b.name:<25} {b.cycle_period_hours:>6.1f}h  {b.birth_date:<12} {trend_display:<10} {b.confidence:.2f}")

    # Save Registry
    with open("bot_census_registry.json", "w") as f:
        json.dump(registry, f, indent=2)
        
    print("\n" + "="*80)
    print(f"✅ CENSUS COMPLETE.")
    print(f"💾 Registry saved to: bot_census_registry.json")

if __name__ == "__main__":
    main()
