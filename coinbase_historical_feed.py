#!/usr/bin/env python3
"""
🪙⚡ COINBASE HISTORICAL DATA FEED ⚡🪙
═══════════════════════════════════════════════════════════════

Fetches FULL YEAR of historical trade data from Coinbase for:
- Training the Probability Matrix
- Validating current market conditions against patterns
- Building the ULTIMATE predictive model

DATA SCOPE:
├─ 1 Year of OHLCV candles (hourly + daily)
├─ Volume patterns
├─ Price correlations
├─ Temporal patterns (day-of-week, hour-of-day)
└─ Cross-pair correlations

Gary Leckey & GitHub Copilot | December 2025
"From Historical Patterns to 100% Probability"
"""

import os
import json
import time
import hmac
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class CandleData:
    """OHLCV candle data"""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    symbol: str
    
    @property
    def change_pct(self) -> float:
        return ((self.close - self.open) / self.open) * 100 if self.open > 0 else 0
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open
    
    @property
    def body_size(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def wick_ratio(self) -> float:
        body = self.body_size
        total_range = self.high - self.low
        return body / total_range if total_range > 0 else 0


class CoinbaseHistoricalFeed:
    """
    Fetch historical data from Coinbase Advanced Trade API
    """
    
    # Coinbase public API endpoints (no auth needed for market data)
    PUBLIC_BASE_URL = "https://api.exchange.coinbase.com"
    
    # Major trading pairs to analyze
    TRADING_PAIRS = [
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
        'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'MATIC-USD', 'LINK-USD',
        'BTC-GBP', 'ETH-GBP', 'SOL-GBP',  # GBP pairs for UK
    ]
    
    # Granularity options (in seconds)
    GRANULARITY = {
        '1m': 60,
        '5m': 300,
        '15m': 900,
        '1h': 3600,
        '6h': 21600,
        '1d': 86400,
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AureonTrading/1.0',
            'Accept': 'application/json',
        })
        self.cache = {}
        self.patterns_db = defaultdict(list)
        
    def get_candles(self, product_id: str, granularity: str = '1h', 
                    start: datetime = None, end: datetime = None) -> List[CandleData]:
        """
        Fetch historical candles from Coinbase
        
        Coinbase returns max 300 candles per request
        """
        if start is None:
            start = datetime.now() - timedelta(days=30)
        if end is None:
            end = datetime.now()
            
        granularity_seconds = self.GRANULARITY.get(granularity, 3600)
        
        all_candles = []
        current_start = start
        
        while current_start < end:
            # Calculate end for this batch (max 300 candles)
            batch_end = min(
                current_start + timedelta(seconds=granularity_seconds * 300),
                end
            )
            
            try:
                url = f"{self.PUBLIC_BASE_URL}/products/{product_id}/candles"
                params = {
                    'start': current_start.isoformat(),
                    'end': batch_end.isoformat(),
                    'granularity': granularity_seconds,
                }
                
                response = self.session.get(url, params=params, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for candle in data:
                        # Coinbase format: [time, low, high, open, close, volume]
                        ts = datetime.fromtimestamp(candle[0])
                        all_candles.append(CandleData(
                            timestamp=ts,
                            open=float(candle[3]),
                            high=float(candle[2]),
                            low=float(candle[1]),
                            close=float(candle[4]),
                            volume=float(candle[5]),
                            symbol=product_id,
                        ))
                else:
                    print(f"   ⚠️ Error fetching {product_id}: {response.status_code}")
                    
            except Exception as e:
                print(f"   ⚠️ Exception fetching {product_id}: {e}")
                
            current_start = batch_end
            time.sleep(0.1)  # Rate limiting
            
        # Sort by timestamp
        all_candles.sort(key=lambda x: x.timestamp)
        return all_candles
    
    def fetch_year_of_data(self, pairs: List[str] = None) -> Dict[str, List[CandleData]]:
        """
        Fetch 1 full year of hourly data for all pairs
        """
        if pairs is None:
            pairs = self.TRADING_PAIRS
            
        print("\n" + "="*70)
        print("📊 FETCHING 1 YEAR OF HISTORICAL DATA FROM COINBASE")
        print("="*70)
        
        end = datetime.now()
        start = end - timedelta(days=365)
        
        all_data = {}
        
        for i, pair in enumerate(pairs):
            print(f"\n   [{i+1}/{len(pairs)}] Fetching {pair}...")
            candles = self.get_candles(pair, '1h', start, end)
            
            if candles:
                all_data[pair] = candles
                print(f"      ✅ {len(candles):,} hourly candles loaded")
                
                # Quick stats
                if len(candles) > 0:
                    first_price = candles[0].close
                    last_price = candles[-1].close
                    change = ((last_price - first_price) / first_price) * 100
                    print(f"      📈 1Y Change: {change:+.1f}% (${first_price:,.2f} → ${last_price:,.2f})")
            else:
                print(f"      ❌ No data available")
                
            time.sleep(0.2)  # Rate limiting
            
        return all_data
    
    def analyze_patterns(self, data: Dict[str, List[CandleData]]) -> Dict[str, Any]:
        """
        Analyze patterns in historical data for probability matrix training
        """
        print("\n" + "="*70)
        print("🔬 ANALYZING PATTERNS FOR PROBABILITY MATRIX")
        print("="*70)
        
        patterns = {
            'hour_of_day': defaultdict(lambda: {'bullish': 0, 'bearish': 0, 'total': 0}),
            'day_of_week': defaultdict(lambda: {'bullish': 0, 'bearish': 0, 'total': 0}),
            'month': defaultdict(lambda: {'bullish': 0, 'bearish': 0, 'total': 0}),
            'consecutive_patterns': defaultdict(int),
            'volatility_by_hour': defaultdict(list),
            'volume_patterns': defaultdict(list),
            'momentum_sequences': [],
            'correlation_pairs': {},
        }
        
        # Analyze each pair
        for symbol, candles in data.items():
            print(f"\n   Analyzing {symbol}...")
            
            for candle in candles:
                hour = candle.timestamp.hour
                dow = candle.timestamp.weekday()
                month = candle.timestamp.month
                
                # Hour of day pattern
                patterns['hour_of_day'][hour]['total'] += 1
                if candle.is_bullish:
                    patterns['hour_of_day'][hour]['bullish'] += 1
                else:
                    patterns['hour_of_day'][hour]['bearish'] += 1
                    
                # Day of week pattern
                patterns['day_of_week'][dow]['total'] += 1
                if candle.is_bullish:
                    patterns['day_of_week'][dow]['bullish'] += 1
                else:
                    patterns['day_of_week'][dow]['bearish'] += 1
                    
                # Month pattern
                patterns['month'][month]['total'] += 1
                if candle.is_bullish:
                    patterns['month'][month]['bullish'] += 1
                else:
                    patterns['month'][month]['bearish'] += 1
                    
                # Volatility by hour
                volatility = (candle.high - candle.low) / candle.open * 100 if candle.open > 0 else 0
                patterns['volatility_by_hour'][hour].append(volatility)
                
                # Volume patterns
                patterns['volume_patterns'][hour].append(candle.volume)
        
        # Calculate probabilities
        results = {
            'hourly_probabilities': {},
            'daily_probabilities': {},
            'monthly_probabilities': {},
            'volatility_profile': {},
            'optimal_trading_hours': [],
            'avoid_hours': [],
        }
        
        # Hourly analysis
        print("\n   📊 HOURLY WIN PROBABILITIES:")
        for hour in range(24):
            data = patterns['hour_of_day'][hour]
            if data['total'] > 0:
                prob = data['bullish'] / data['total']
                results['hourly_probabilities'][hour] = {
                    'bullish_prob': prob,
                    'bearish_prob': 1 - prob,
                    'sample_size': data['total'],
                }
                
                emoji = '🟢' if prob > 0.52 else '🔴' if prob < 0.48 else '🟡'
                print(f"      {hour:02d}:00 UTC: {prob*100:.1f}% bullish ({data['total']:,} samples) {emoji}")
                
                if prob > 0.54:
                    results['optimal_trading_hours'].append(hour)
                elif prob < 0.46:
                    results['avoid_hours'].append(hour)
        
        # Daily analysis
        print("\n   📅 DAILY WIN PROBABILITIES:")
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        for dow in range(7):
            data = patterns['day_of_week'][dow]
            if data['total'] > 0:
                prob = data['bullish'] / data['total']
                results['daily_probabilities'][dow] = {
                    'name': days[dow],
                    'bullish_prob': prob,
                    'sample_size': data['total'],
                }
                emoji = '🟢' if prob > 0.52 else '🔴' if prob < 0.48 else '🟡'
                print(f"      {days[dow]}: {prob*100:.1f}% bullish ({data['total']:,} samples) {emoji}")
        
        # Monthly analysis
        print("\n   📆 MONTHLY WIN PROBABILITIES:")
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        for m in range(1, 13):
            data = patterns['month'][m]
            if data['total'] > 0:
                prob = data['bullish'] / data['total']
                results['monthly_probabilities'][m] = {
                    'name': months[m],
                    'bullish_prob': prob,
                    'sample_size': data['total'],
                }
                emoji = '🟢' if prob > 0.52 else '🔴' if prob < 0.48 else '🟡'
                print(f"      {months[m]}: {prob*100:.1f}% bullish ({data['total']:,} samples) {emoji}")
        
        # Volatility profile
        print("\n   📈 VOLATILITY BY HOUR (avg %):")
        for hour in range(24):
            vols = patterns['volatility_by_hour'][hour]
            if vols:
                avg_vol = sum(vols) / len(vols)
                results['volatility_profile'][hour] = avg_vol
                bar = '█' * int(avg_vol * 10)
                print(f"      {hour:02d}:00: {avg_vol:.2f}% {bar}")
        
        return results
    
    def train_probability_matrix(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create trained probability matrix from patterns
        """
        print("\n" + "="*70)
        print("🧠 TRAINING PROBABILITY MATRIX")
        print("="*70)
        
        matrix = {
            'version': '2.0',
            'trained_at': datetime.now().isoformat(),
            'data_source': 'coinbase_historical',
            'lookback_days': 365,
            
            # Hourly edge matrix
            'hourly_edge': {},
            
            # Daily edge matrix
            'daily_edge': {},
            
            # Monthly edge matrix  
            'monthly_edge': {},
            
            # Combined optimal conditions
            'optimal_conditions': {},
            
            # Avoid conditions
            'avoid_conditions': {},
        }
        
        # Calculate edges (deviation from 50%)
        for hour, data in patterns.get('hourly_probabilities', {}).items():
            edge = (data['bullish_prob'] - 0.5) * 100  # Convert to percentage points
            matrix['hourly_edge'][hour] = {
                'edge': edge,
                'confidence': min(data['sample_size'] / 1000, 1.0),  # More samples = more confidence
            }
            
        for dow, data in patterns.get('daily_probabilities', {}).items():
            edge = (data['bullish_prob'] - 0.5) * 100
            matrix['daily_edge'][dow] = {
                'name': data['name'],
                'edge': edge,
                'confidence': min(data['sample_size'] / 10000, 1.0),
            }
            
        for month, data in patterns.get('monthly_probabilities', {}).items():
            edge = (data['bullish_prob'] - 0.5) * 100
            matrix['monthly_edge'][month] = {
                'name': data['name'],
                'edge': edge,
                'confidence': min(data['sample_size'] / 5000, 1.0),
            }
        
        # Find optimal combined conditions
        optimal_hours = patterns.get('optimal_trading_hours', [])
        if optimal_hours:
            matrix['optimal_conditions']['hours'] = optimal_hours
            print(f"\n   ✅ OPTIMAL TRADING HOURS: {optimal_hours}")
            
        avoid_hours = patterns.get('avoid_hours', [])
        if avoid_hours:
            matrix['avoid_conditions']['hours'] = avoid_hours
            print(f"   ❌ AVOID HOURS: {avoid_hours}")
        
        # Best days
        best_days = [d for d, data in patterns.get('daily_probabilities', {}).items() 
                     if data['bullish_prob'] > 0.52]
        worst_days = [d for d, data in patterns.get('daily_probabilities', {}).items() 
                      if data['bullish_prob'] < 0.48]
        
        if best_days:
            matrix['optimal_conditions']['days'] = best_days
            day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
            print(f"   ✅ OPTIMAL DAYS: {[day_names[d] for d in best_days]}")
            
        if worst_days:
            matrix['avoid_conditions']['days'] = worst_days
            print(f"   ❌ AVOID DAYS: {[day_names[d] for d in worst_days]}")
        
        return matrix
    
    def save_trained_matrix(self, matrix: Dict[str, Any], filename: str = 'trained_probability_matrix.json'):
        """Save the trained matrix to file"""
        with open(filename, 'w') as f:
            json.dump(matrix, f, indent=2, default=str)
        print(f"\n   💾 Saved trained matrix to {filename}")
        return filename
    
    def validate_current_market(self, matrix: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate current market conditions against trained patterns
        """
        now = datetime.now()
        current_hour = now.hour
        current_dow = now.weekday()
        current_month = now.month
        
        validation = {
            'timestamp': now.isoformat(),
            'conditions': {},
            'combined_edge': 0,
            'confidence': 0,
            'recommendation': '',
        }
        
        # Check hourly edge
        hourly = matrix.get('hourly_edge', {}).get(current_hour, {})
        hourly_edge = hourly.get('edge', 0)
        validation['conditions']['hour'] = {
            'current': current_hour,
            'edge': hourly_edge,
            'status': '🟢 OPTIMAL' if hourly_edge > 2 else '🔴 AVOID' if hourly_edge < -2 else '🟡 NEUTRAL'
        }
        
        # Check daily edge
        daily = matrix.get('daily_edge', {}).get(current_dow, {})
        daily_edge = daily.get('edge', 0)
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        validation['conditions']['day'] = {
            'current': days[current_dow],
            'edge': daily_edge,
            'status': '🟢 OPTIMAL' if daily_edge > 2 else '🔴 AVOID' if daily_edge < -2 else '🟡 NEUTRAL'
        }
        
        # Check monthly edge
        monthly = matrix.get('monthly_edge', {}).get(current_month, {})
        monthly_edge = monthly.get('edge', 0)
        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        validation['conditions']['month'] = {
            'current': months[current_month],
            'edge': monthly_edge,
            'status': '🟢 OPTIMAL' if monthly_edge > 2 else '🔴 AVOID' if monthly_edge < -2 else '🟡 NEUTRAL'
        }
        
        # Combined edge (weighted average)
        validation['combined_edge'] = (hourly_edge * 0.5 + daily_edge * 0.3 + monthly_edge * 0.2)
        
        # Recommendation
        if validation['combined_edge'] > 3:
            validation['recommendation'] = '🚀 STRONG BUY CONDITIONS'
            validation['confidence'] = 0.75
        elif validation['combined_edge'] > 1:
            validation['recommendation'] = '📈 FAVORABLE CONDITIONS'
            validation['confidence'] = 0.60
        elif validation['combined_edge'] < -3:
            validation['recommendation'] = '🛑 AVOID TRADING'
            validation['confidence'] = 0.70
        elif validation['combined_edge'] < -1:
            validation['recommendation'] = '⚠️ CAUTION - WEAK CONDITIONS'
            validation['confidence'] = 0.55
        else:
            validation['recommendation'] = '⚖️ NEUTRAL - STANDARD CONDITIONS'
            validation['confidence'] = 0.50
            
        return validation


def main():
    """
    Main function to fetch and analyze historical data
    """
    print("\n" + "🪙"*30)
    print("   COINBASE HISTORICAL DATA → PROBABILITY MATRIX TRAINING")
    print("🪙"*30 + "\n")
    
    feed = CoinbaseHistoricalFeed()
    
    # Fetch 1 year of data (this takes a while)
    # For testing, just get 30 days
    print("⏳ Fetching historical data (this may take a few minutes)...")
    
    # Start with just major pairs for speed
    test_pairs = ['BTC-USD', 'ETH-USD', 'SOL-USD']
    
    data = feed.fetch_year_of_data(test_pairs)
    
    if data:
        # Analyze patterns
        patterns = feed.analyze_patterns(data)
        
        # Train probability matrix
        matrix = feed.train_probability_matrix(patterns)
        
        # Save trained matrix
        feed.save_trained_matrix(matrix)
        
        # Validate current market
        print("\n" + "="*70)
        print("🔍 CURRENT MARKET VALIDATION")
        print("="*70)
        
        validation = feed.validate_current_market(matrix)
        
        print(f"\n   ⏰ Current Time: {validation['timestamp']}")
        print(f"\n   📊 CONDITIONS:")
        for key, cond in validation['conditions'].items():
            print(f"      {key.upper()}: {cond['current']} (edge: {cond['edge']:+.1f}%) {cond['status']}")
        
        print(f"\n   🎯 COMBINED EDGE: {validation['combined_edge']:+.2f}%")
        print(f"   📈 RECOMMENDATION: {validation['recommendation']}")
        print(f"   🔮 CONFIDENCE: {validation['confidence']*100:.0f}%")
        
    print("\n" + "="*70)
    print("✅ PROBABILITY MATRIX TRAINING COMPLETE")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
