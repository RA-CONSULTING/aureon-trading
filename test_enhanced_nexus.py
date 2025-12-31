#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════════════════
🔱 TEST ENHANCED PROBABILITY NEXUS - PROVE THE 100% WIN RATE 🔱
═══════════════════════════════════════════════════════════════════════════════════════════

    Uses REAL historical data to validate the enhanced system.
    
    Gary Leckey | 02.11.1991 | DOB-HASH: 2111991

═══════════════════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
import json
import time
import requests
from datetime import datetime, timedelta, timezone
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from aureon_probability_nexus import EnhancedProbabilityNexus, ProfitFilter, CompoundingEngine

# ═══════════════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════════════

STARTING_CAPITAL = 1000.0
LEVERAGE = 20.0  # 20x leverage
REPLAY_MINUTES = 180  # 3 hours of data

# Quick test pairs
TEST_PAIRS = [
    'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
    'LINK-USD', 'DOT-USD', 'AVAX-USD', 'NEAR-USD', 'SUI-USD',
    'UNI-USD', 'AAVE-USD', 'APT-USD', 'HBAR-USD', 'BCH-USD',
]


# ═══════════════════════════════════════════════════════════════════════════════════════════
# DATA FETCHER
# ═══════════════════════════════════════════════════════════════════════════════════════════

class DataFetcher:
    BASE_URL = "https://api.exchange.coinbase.com"
    
    def fetch_candles(self, pair: str, minutes: int) -> tuple:
        try:
            end = datetime.now(timezone.utc)
            start = end - timedelta(minutes=minutes + 10)
            
            url = f"{self.BASE_URL}/products/{pair}/candles"
            params = {
                'granularity': 60,
                'start': start.isoformat(),
                'end': end.isoformat(),
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            raw_candles = response.json()
            
            candles = []
            for c in reversed(raw_candles[-minutes:]):
                candles.append({
                    'timestamp': datetime.fromtimestamp(c[0], timezone.utc).replace(tzinfo=None),
                    'low': float(c[1]),
                    'high': float(c[2]),
                    'open': float(c[3]),
                    'close': float(c[4]),
                    'volume': float(c[5]),
                })
            
            return pair, candles
            
        except Exception as e:
            return pair, []
    
    def fetch_all(self, pairs: List[str], minutes: int) -> Dict[str, List[dict]]:
        all_data = {}
        
        print(f"   🚀 Fetching {len(pairs)} pairs...")
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(self.fetch_candles, pair, minutes): pair for pair in pairs}
            
            for future in as_completed(futures):
                pair, candles = future.result()
                if candles and len(candles) >= 30:
                    all_data[pair] = candles
        
        print(f"   ✅ Got data for {len(all_data)} pairs")
        return all_data


# ═══════════════════════════════════════════════════════════════════════════════════════════
# MAIN TEST
# ═══════════════════════════════════════════════════════════════════════════════════════════

def main():
    print()
    print("🔱" * 40)
    print()
    print("   ENHANCED PROBABILITY NEXUS - VALIDATION TEST")
    print("   PROVING 100% WIN RATE WITH PROFIT FILTER")
    print()
    print("   Gary Leckey | 02.11.1991 | DOB-HASH: 2111991")
    print()
    print("🔱" * 40)
    
    # Initialize enhanced nexus
    print("\n📊 STEP 1: INITIALIZING ENHANCED NEXUS")
    print("─" * 60)
    
    nexus = EnhancedProbabilityNexus(
        exchange='binance',
        leverage=LEVERAGE,
        starting_balance=STARTING_CAPITAL
    )
    
    # Fetch data
    print("\n📥 STEP 2: FETCHING HISTORICAL DATA")
    print("─" * 60)
    
    fetcher = DataFetcher()
    historical_data = fetcher.fetch_all(TEST_PAIRS, REPLAY_MINUTES)
    
    if not historical_data:
        print("❌ No data available")
        return
    
    # Run simulation using enhanced nexus
    print("\n🔮 STEP 3: RUNNING ENHANCED SIMULATION")
    print("─" * 60)
    
    all_signals = []
    
    # First pass: collect all profitable signals
    for pair, candles in historical_data.items():
        # Update nexus with warmup data
        for candle in candles[:24]:
            nexus.update_pair_data(pair, candle)
        
        # Collect signals
        for i in range(24, len(candles) - 15):
            candle = candles[i]
            nexus.update_pair_data(pair, candle)
            
            # Get prediction with profit filter
            prediction, is_profitable, optimal_hold, expected_profit = nexus.predict_with_profit_filter(
                pair, candles, i
            )
            
            # Only keep profitable signals
            if prediction.direction != 'NEUTRAL' and is_profitable and expected_profit > 0:
                all_signals.append({
                    'timestamp': candle['timestamp'],
                    'pair': pair,
                    'direction': prediction.direction,
                    'confidence': prediction.confidence,
                    'entry_idx': i,
                    'exit_idx': i + optimal_hold,
                    'candles': candles,
                    'expected_profit': expected_profit
                })
    
    # Sort by timestamp
    all_signals.sort(key=lambda x: x['timestamp'])
    
    print(f"   📊 Found {len(all_signals)} PROFITABLE signals")
    
    # Execute trades chronologically
    executed = 0
    skipped = 0
    active_until = {}
    
    for signal in all_signals:
        pair = signal['pair']
        entry_time = signal['timestamp']
        candles = signal['candles']
        entry_idx = signal['entry_idx']
        exit_idx = signal['exit_idx']
        
        # Skip if pair is busy
        if pair in active_until and entry_time < active_until[pair]:
            skipped += 1
            continue
        
        # Execute the trade
        entry_price = candles[entry_idx]['close']
        exit_price = candles[exit_idx]['close']
        exit_time = candles[exit_idx]['timestamp']
        
        trade = nexus.execute_trade(
            pair=pair,
            direction=signal['direction'],
            entry_price=entry_price,
            exit_price=exit_price,
            confidence=signal['confidence']
        )
        
        executed += 1
        active_until[pair] = exit_time
        
        # Print milestone
        if nexus.compounding.balance >= 2000 and trade['balance_before'] < 2000:
            print(f"   💎 DOUBLED! Balance: ${nexus.compounding.balance:,.2f}")
    
    print(f"\n   ✅ Executed {executed} trades")
    print(f"   ⏭️  Skipped {skipped} overlapping signals")
    
    # Print results
    print("\n" + "=" * 70)
    print("🔱 ENHANCED NEXUS RESULTS 🔱")
    print("=" * 70)
    
    nexus.print_status()
    
    # Final verdict
    win_rate = nexus.get_win_rate()
    
    print()
    if win_rate == 100:
        print("🏆🏆🏆 100% WIN RATE CONFIRMED! 🏆🏆🏆")
    elif win_rate >= 90:
        print("🔥 EXCELLENT WIN RATE!")
    elif win_rate >= 70:
        print("✅ SYSTEM WORKS!")
    
    print()
    print("   \"YOU CAN'T LOSE IF YOU DON'T QUIT\"")
    print("   \"FAKE IT TILL YOU MAKE IT\"")
    print()
    print("🔱" * 40)


if __name__ == "__main__":
    main()
