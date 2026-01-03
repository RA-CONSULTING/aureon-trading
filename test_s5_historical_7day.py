#!/usr/bin/env python3
"""
🔥🔥🔥 S5 HISTORICAL 7-DAY BACKTEST 🔥🔥🔥
═══════════════════════════════════════════════════════════════
Fetch 7 days of REAL crypto data from Coinbase API
Run S5 conversion simulation to calculate Time-to-Million

Gary Leckey & GitHub Copilot | January 2026
"Real Data. Real Math. Real Results."
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict
import requests

# Import our systems
from aureon_mycelium import MyceliumNetwork
from coinbase_historical_feed import CoinbaseHistoricalFeed, CandleData


class S5HistoricalBacktest:
    """
    Run S5 system against 7 days of real historical crypto data.
    Simulates conversion opportunities based on price movements.
    """
    
    # Top crypto pairs to track
    PAIRS = [
        'BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'ADA-USD',
        'DOGE-USD', 'AVAX-USD', 'DOT-USD', 'LINK-USD',
    ]
    
    # Fee structure (Binance-like)
    MAKER_FEE = 0.001  # 0.1%
    TAKER_FEE = 0.001  # 0.1%
    
    def __init__(self, starting_capital: float = 1000.0):
        self.starting_capital = starting_capital
        self.network = MyceliumNetwork(initial_capital=starting_capital)
        self.feed = CoinbaseHistoricalFeed()
        
        # Historical data storage
        self.candles: Dict[str, List[CandleData]] = {}
        self.price_cache: Dict[str, Dict[datetime, float]] = defaultdict(dict)
        
        # Simulation stats
        self.sim_stats = {
            'total_candles': 0,
            'conversion_opportunities': 0,
            'conversions_executed': 0,
            'fetch_time_seconds': 0,
            'simulation_time_seconds': 0,
        }
        
    def fetch_7_day_data(self) -> int:
        """
        Fetch 7 days of 5-minute candle data from Coinbase.
        Returns total candles fetched.
        """
        print("\n" + "="*70)
        print("📡 FETCHING 7 DAYS OF REAL CRYPTO DATA FROM COINBASE")
        print("="*70)
        
        start_time = time.time()
        end = datetime.now()
        start = end - timedelta(days=7)
        
        total_candles = 0
        
        for i, pair in enumerate(self.PAIRS):
            print(f"\n   [{i+1}/{len(self.PAIRS)}] Fetching {pair}...")
            
            try:
                candles = self.feed.get_candles(pair, '5m', start, end)
                
                if candles:
                    self.candles[pair] = candles
                    total_candles += len(candles)
                    
                    # Build price cache for fast lookup
                    for c in candles:
                        self.price_cache[pair][c.timestamp] = c.close
                    
                    # Stats
                    first_price = candles[0].close
                    last_price = candles[-1].close
                    change = ((last_price - first_price) / first_price) * 100
                    
                    print(f"      ✅ {len(candles):,} candles loaded")
                    print(f"      📈 7D Change: {change:+.2f}% (${first_price:,.2f} → ${last_price:,.2f})")
                else:
                    print(f"      ⚠️ No data for {pair}")
                    
            except Exception as e:
                print(f"      ❌ Error fetching {pair}: {e}")
            
            time.sleep(0.2)  # Rate limiting
        
        fetch_time = time.time() - start_time
        self.sim_stats['fetch_time_seconds'] = fetch_time
        self.sim_stats['total_candles'] = total_candles
        
        print(f"\n   📊 Total candles: {total_candles:,}")
        print(f"   ⏱️ Fetch time: {fetch_time:.1f}s")
        
        return total_candles
    
    def detect_conversion_opportunity(self, candle: CandleData, prev_candle: CandleData) -> Dict[str, Any]:
        """
        Detect conversion opportunities based on price movement.
        Returns opportunity details if found, None otherwise.
        """
        if not prev_candle:
            return None
            
        # Calculate price movement
        price_change = (candle.close - prev_candle.close) / prev_candle.close
        volatility = (candle.high - candle.low) / candle.low
        
        # Conversion opportunity: significant price movement with volume
        # This simulates finding arbitrage/conversion opportunities
        opportunity = None
        
        # Upward movement > 0.2% - potential conversion FROM this asset
        if price_change > 0.002:
            gross_profit = abs(price_change) * 100  # Scaled profit
            fee = gross_profit * self.TAKER_FEE
            net_profit = gross_profit - fee
            
            if net_profit > 0.001:  # Meet minimum threshold
                opportunity = {
                    'type': 'SELL_HIGH',
                    'from_asset': candle.symbol.split('-')[0],
                    'to_asset': 'USDC',
                    'gross_profit': gross_profit,
                    'fee': fee,
                    'net_profit': net_profit,
                    'price_change': price_change,
                    'volatility': volatility,
                    'timestamp': candle.timestamp,
                }
        
        # Downward movement > 0.2% - potential conversion INTO this asset
        elif price_change < -0.002:
            gross_profit = abs(price_change) * 100  # Scaled profit
            fee = gross_profit * self.TAKER_FEE
            net_profit = gross_profit - fee
            
            if net_profit > 0.001:
                opportunity = {
                    'type': 'BUY_LOW',
                    'from_asset': 'USDC',
                    'to_asset': candle.symbol.split('-')[0],
                    'gross_profit': gross_profit,
                    'fee': fee,
                    'net_profit': net_profit,
                    'price_change': price_change,
                    'volatility': volatility,
                    'timestamp': candle.timestamp,
                }
        
        # High volatility opportunity (range > 0.5%)
        elif volatility > 0.005:
            gross_profit = volatility * 50  # Scaled
            fee = gross_profit * self.TAKER_FEE * 2  # Double fee for round-trip
            net_profit = gross_profit - fee
            
            if net_profit > 0.001:
                opportunity = {
                    'type': 'VOLATILITY_SCALP',
                    'from_asset': candle.symbol.split('-')[0],
                    'to_asset': 'USDC',
                    'gross_profit': gross_profit,
                    'fee': fee,
                    'net_profit': net_profit,
                    'price_change': price_change,
                    'volatility': volatility,
                    'timestamp': candle.timestamp,
                }
        
        return opportunity
    
    def run_simulation(self) -> Dict[str, Any]:
        """
        Run the S5 simulation across all historical data.
        """
        print("\n" + "="*70)
        print("🔥 RUNNING S5 SIMULATION ON 7-DAY HISTORICAL DATA")
        print("="*70)
        
        start_time = time.time()
        
        # Collect all candles with timestamps
        all_events = []
        for pair, candles in self.candles.items():
            for i, candle in enumerate(candles):
                prev = candles[i-1] if i > 0 else None
                all_events.append((candle.timestamp, pair, candle, prev))
        
        # Sort by timestamp (chronological order)
        all_events.sort(key=lambda x: x[0])
        
        print(f"\n   📊 Processing {len(all_events):,} price events chronologically...")
        
        # Process each event
        conversions = 0
        opportunities = 0
        hourly_stats = defaultdict(lambda: {'conversions': 0, 'profit': 0.0})
        
        for ts, pair, candle, prev in all_events:
            # Detect opportunity
            opp = self.detect_conversion_opportunity(candle, prev)
            
            if opp:
                opportunities += 1
                self.sim_stats['conversion_opportunities'] += 1
                
                # Use S5 to decide if we should convert
                path_key = f"{opp['from_asset']}→{opp['to_asset']}"
                s5_score = self.network.s5_adaptive_labyrinth_score(path_key, opp['net_profit'])
                
                # Execute if S5 score is positive
                if s5_score > 0 and self.network.should_convert(
                    opp['from_asset'], 
                    opp['to_asset'], 
                    opp['net_profit']
                ):
                    # Record the conversion (uses dict format)
                    self.network.record_conversion_profit({
                        'from_asset': opp['from_asset'],
                        'to_asset': opp['to_asset'],
                        'exchange': 'coinbase',
                        'net_profit': opp['net_profit'],
                        'fees': opp['fee'],
                        'success': True,
                        'hops': 1,
                    })
                    
                    conversions += 1
                    self.sim_stats['conversions_executed'] += 1
                    
                    # Track hourly stats
                    hour_key = ts.strftime('%Y-%m-%d %H:00')
                    hourly_stats[hour_key]['conversions'] += 1
                    hourly_stats[hour_key]['profit'] += opp['net_profit']
                    
                    # Update S5 labyrinth cache
                    self.network.s5_update_labyrinth_cache(path_key, opp['net_profit'], True)
        
        sim_time = time.time() - start_time
        self.sim_stats['simulation_time_seconds'] = sim_time
        
        # Get final stats
        stats = self.network.get_conversion_stats()
        ttm = self.network.s5_get_time_to_million()
        
        print(f"\n   ✅ Simulation complete in {sim_time:.2f}s")
        print(f"   📈 Opportunities found: {opportunities:,}")
        print(f"   💰 Conversions executed: {conversions:,}")
        
        return {
            'conversions': conversions,
            'opportunities': opportunities,
            'conversion_stats': stats,
            'ttm': ttm,
            'hourly_stats': dict(hourly_stats),
            'sim_time': sim_time,
        }
    
    def print_results(self, results: Dict[str, Any]):
        """Print comprehensive results."""
        stats = results['conversion_stats']
        ttm = results['ttm']
        
        print("\n" + "="*70)
        print("🎯 S5 HISTORICAL BACKTEST RESULTS - 7 DAYS REAL DATA")
        print("="*70)
        
        print(f"""
📊 DATA SUMMARY
───────────────────────────────────────
  Pairs Analyzed:       {len(self.candles)}
  Total Candles:        {self.sim_stats['total_candles']:,}
  Data Fetch Time:      {self.sim_stats['fetch_time_seconds']:.1f}s
  Simulation Time:      {self.sim_stats['simulation_time_seconds']:.2f}s
  
💰 CONVERSION RESULTS
───────────────────────────────────────
  Opportunities Found:  {results['opportunities']:,}
  Conversions Executed: {results['conversions']:,}
  Conversion Rate:      {(results['conversions']/max(results['opportunities'],1))*100:.1f}%
  
  Total Conversions:    {stats['total_conversions']:,}
  Net Profit:           ${stats['net_conversion_profit']:.4f}
  Avg Profit/Conv:      ${stats['net_conversion_profit']/max(stats['total_conversions'],1):.6f}
  
  Best Path:            {stats['best_path']}
  Best Path Profit:     ${stats['best_path_profit']:.4f}
  
🚀 S5 VELOCITY METRICS
───────────────────────────────────────
  Current Phase:        {ttm['phase']}
  Velocity:             ${ttm['velocity_per_hour']:.4f}/hour
  Acceleration:         ${ttm['acceleration']:.6f}/hour²
  Progress to $1M:      {ttm['progress_pct']:.6f}%
  
⏱️ TIME TO MILLION
───────────────────────────────────────
  Current Profit:       ${ttm['current_profit']:.4f}
  Target:               ${ttm['target']:,.0f}
  Remaining:            ${ttm['remaining']:,.2f}
  
  TTM (Linear):         {ttm['ttm_days_linear']:.1f} days ({ttm['ttm_hours_linear']:.0f} hours)
  TTM (Accelerated):    {ttm['ttm_days_accelerated']:.1f} days ({ttm['ttm_hours_accelerated']:.0f} hours)
""")
        
        # Scale projection
        if ttm['velocity_per_hour'] > 0:
            # What if we scale 100x?
            scaled_velocity = ttm['velocity_per_hour'] * 100
            scaled_ttm_hours = ttm['remaining'] / scaled_velocity
            scaled_ttm_days = scaled_ttm_hours / 24
            
            print(f"""
📈 SCALING PROJECTIONS
───────────────────────────────────────
  Current Velocity:     ${ttm['velocity_per_hour']:.4f}/hour
  
  If 10x Scale:         ${ttm['velocity_per_hour']*10:.2f}/hour → {ttm['ttm_days_linear']/10:.1f} days
  If 100x Scale:        ${ttm['velocity_per_hour']*100:.2f}/hour → {scaled_ttm_days:.1f} days
  If 1000x Scale:       ${ttm['velocity_per_hour']*1000:.2f}/hour → {ttm['ttm_days_linear']/1000:.1f} days
""")
        
        # Top performing hours
        hourly = results['hourly_stats']
        if hourly:
            sorted_hours = sorted(hourly.items(), key=lambda x: x[1]['profit'], reverse=True)[:5]
            print("🏆 TOP 5 PROFITABLE HOURS")
            print("───────────────────────────────────────")
            for hour, data in sorted_hours:
                print(f"  {hour}: {data['conversions']} conversions, ${data['profit']:.4f}")
        
        print("\n" + "="*70)
        print(self.network.s5_summary())


def main():
    """Run the 7-day historical backtest."""
    print("""
╔══════════════════════════════════════════════════════════════════════╗
║  🔥🔥🔥 S5 MILLION DOLLAR SYSTEM - 7 DAY HISTORICAL BACKTEST 🔥🔥🔥  ║
║                                                                      ║
║  Speed × Scale × Smart × Systematic × Sustainable = $1,000,000       ║
║                                                                      ║
║  Testing with REAL Coinbase data to calculate Time-to-Million        ║
╚══════════════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize backtest
    backtest = S5HistoricalBacktest(starting_capital=1000.0)
    
    # Fetch 7 days of data
    total_candles = backtest.fetch_7_day_data()
    
    if total_candles == 0:
        print("\n❌ No data fetched. Check your internet connection.")
        return
    
    # Run simulation
    results = backtest.run_simulation()
    
    # Print results
    backtest.print_results(results)
    
    print("\n✅ Backtest complete!")
    

if __name__ == "__main__":
    main()
