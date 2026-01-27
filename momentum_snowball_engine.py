#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   🌊⚡ MOMENTUM SNOWBALL ENGINE ⚡🌊                                              ║
║                                                                                   ║
║   THE KEY INSIGHT:                                                                ║
║   • Pure arbitrage above fees is rare (markets are efficient)                    ║
║   • BUT momentum exists - some assets are RISING, others FALLING                 ║
║   • Strategy: Convert FROM falling TO rising                                      ║
║   • Always ride the strongest wave                                                ║
║                                                                                   ║
║   THE MATH:                                                                        ║
║   Asset A: falling 0.5%/minute                                                    ║
║   Asset B: rising 0.8%/minute                                                     ║
║   Net advantage: 1.3%/minute (minus 0.21% fees = +1.09%/minute)                  ║
║                                                                                   ║
║   CONVERT! Ride B's momentum, escape A's decline.                                ║
║                                                                                   ║
║   SPEED + MOMENTUM = EXPONENTIAL GROWTH                                          ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import time
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from dataclasses import dataclass, field
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

CONFIG = {
    # Fees
    'total_fee_rate': 0.0021,      # 0.21% total (maker + slippage)
    
    # Momentum thresholds
    'min_momentum_diff': 0.003,    # 0.3% momentum difference to convert
    'momentum_window_seconds': 60, # Look at 60-second momentum
    
    # Conversion
    'min_trade_usd': 5.0,
    'conversion_cooldown': 1.0,    # 1 second between conversions
    
    # Safety
    'max_conversions_per_minute': 30,
}


class MomentumTracker:
    """
    Tracks price momentum for all assets
    
    Momentum = price change over time window
    Positive = rising
    Negative = falling
    """
    
    def __init__(self, window_seconds: int = 60):
        self.window = window_seconds
        self.price_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.current_prices: Dict[str, float] = {}
        self.momentum: Dict[str, float] = {}  # Asset -> momentum %
        
    def update_price(self, asset: str, price: float):
        """Record a price update"""
        now = time.time()
        self.current_prices[asset] = price
        self.price_history[asset].append((now, price))
        
        # Calculate momentum
        self._calculate_momentum(asset)
        
    def _calculate_momentum(self, asset: str):
        """Calculate momentum for an asset"""
        history = self.price_history[asset]
        if len(history) < 2:
            self.momentum[asset] = 0.0
            return
            
        now = time.time()
        cutoff = now - self.window
        
        # Find oldest price in window
        oldest_price = None
        oldest_time = now
        for t, p in history:
            if t >= cutoff:
                if oldest_price is None or t < oldest_time:
                    oldest_price = p
                    oldest_time = t
                    
        if oldest_price is None or oldest_price <= 0:
            self.momentum[asset] = 0.0
            return
            
        current = self.current_prices.get(asset, 0)
        if current <= 0:
            self.momentum[asset] = 0.0
            return
            
        # Momentum = % change per minute
        time_diff = now - oldest_time
        if time_diff < 5:  # Need at least 5 seconds of data
            self.momentum[asset] = 0.0
            return
            
        price_change = (current - oldest_price) / oldest_price
        minutes = time_diff / 60
        self.momentum[asset] = price_change / minutes if minutes > 0 else 0.0
        
    def get_momentum(self, asset: str) -> float:
        """Get current momentum for asset (% per minute)"""
        return self.momentum.get(asset, 0.0)
        
    def get_strongest_rising(self, exclude: set = None) -> List[Tuple[str, float]]:
        """Get assets sorted by rising momentum"""
        exclude = exclude or set()
        items = [(a, m) for a, m in self.momentum.items() 
                 if a not in exclude and m > 0 and a in self.current_prices]
        return sorted(items, key=lambda x: x[1], reverse=True)
        
    def get_weakest_falling(self, include: set = None) -> List[Tuple[str, float]]:
        """Get assets sorted by falling momentum"""
        include = include or set(self.momentum.keys())
        items = [(a, m) for a, m in self.momentum.items() 
                 if a in include and m < 0]
        return sorted(items, key=lambda x: x[1])  # Most negative first


class MomentumSnowball:
    """
    MOMENTUM SNOWBALL ENGINE
    
    Strategy:
    1. Track momentum of ALL assets in real-time
    2. When holding a FALLING asset, find a RISING one
    3. If momentum difference > fees, CONVERT
    4. Ride the wave, compound gains
    
    The key: We're not looking for instant arbitrage,
    we're surfing momentum waves.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.tracker = MomentumTracker(window_seconds=CONFIG['momentum_window_seconds'])
        self.running = False
        
        # Portfolio
        self.holdings: Dict[str, float] = {}
        self.starting_value: float = 0.0
        
        # Chain
        self.chain: List[Dict] = []
        self.total_conversions: int = 0
        self.total_fees: float = 0.0
        
        # Stats
        self.scans: int = 0
        self.start_time: float = 0
        self.last_conversion: float = 0
        
        # Target assets (liquid)
        self.targets = [
            'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'MATIC',
            'AVAX', 'ATOM', 'UNI', 'AAVE', 'LTC', 'BCH', 'ALGO', 'XLM',
            'DOGE', 'NEAR', 'FTM', 'SAND', 'MANA', 'CRV', 'SNX', 'COMP'
        ]
        
        # Kraken
        self.kraken = None
        if not dry_run:
            try:
                from kraken_client import KrakenClient
                self.kraken = KrakenClient()
            except:
                print("⚠️ Kraken not available - dry run mode")
                self.dry_run = True
                
    async def fetch_prices(self) -> Dict[str, float]:
        """Fetch current prices from Binance"""
        prices = {}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.binance.com/api/v3/ticker/price',
                                       timeout=aiohttp.ClientTimeout(total=3)) as resp:
                    if resp.status == 200:
                        tickers = await resp.json()
                        for t in tickers:
                            symbol = t['symbol']
                            price = float(t['price'])
                            
                            for quote in ['USDT', 'USDC']:
                                if symbol.endswith(quote):
                                    base = symbol[:-len(quote)]
                                    prices[base] = price
                                    self.tracker.update_price(base, price)
                                    break
        except Exception as e:
            logger.debug(f"Price fetch error: {e}")
            
        # Stablecoins
        for s in ['USD', 'USDT', 'USDC']:
            prices[s] = 1.0
            
        return prices
        
    def current_value(self) -> float:
        """Calculate current portfolio value"""
        total = 0.0
        for asset, amount in self.holdings.items():
            price = self.tracker.current_prices.get(asset, 0)
            total += amount * price
        return total
        
    def find_momentum_opportunity(self) -> Optional[Tuple[str, str, float, float, float]]:
        """
        Find best momentum-based conversion
        
        Logic:
        - For each asset we hold that is FALLING (or neutral)
        - Find an asset that is RISING
        - If momentum difference > fee rate, convert
        
        Returns: (from_asset, to_asset, from_amount, expected_gain_pct, momentum_diff)
        """
        self.scans += 1
        
        best = None
        best_momentum_diff = CONFIG['min_momentum_diff']
        
        for from_asset, from_amount in list(self.holdings.items()):
            from_price = self.tracker.current_prices.get(from_asset, 0)
            from_value = from_amount * from_price
            
            if from_value < CONFIG['min_trade_usd']:
                continue
                
            from_momentum = self.tracker.get_momentum(from_asset)
            
            # Look for rising assets
            for to_asset, to_momentum in self.tracker.get_strongest_rising(exclude={from_asset}):
                if to_asset not in self.targets:
                    continue
                    
                to_price = self.tracker.current_prices.get(to_asset, 0)
                if to_price <= 0:
                    continue
                    
                # Momentum difference
                momentum_diff = to_momentum - from_momentum
                
                # Must exceed fees + minimum threshold
                if momentum_diff > best_momentum_diff:
                    # Calculate expected gain
                    # If we hold for 1 minute, we expect:
                    # from_asset would change by from_momentum
                    # to_asset would change by to_momentum
                    # Net advantage = momentum_diff - fees
                    net_advantage = momentum_diff - CONFIG['total_fee_rate']
                    
                    if net_advantage > 0:
                        best_momentum_diff = momentum_diff
                        best = (from_asset, to_asset, from_amount, net_advantage, momentum_diff)
                        
        return best
        
    async def execute_conversion(self, from_asset: str, to_asset: str, 
                                  from_amount: float, expected_gain: float,
                                  momentum_diff: float) -> bool:
        """Execute a momentum-based conversion"""
        from_price = self.tracker.current_prices.get(from_asset, 0)
        to_price = self.tracker.current_prices.get(to_asset, 0)
        
        from_value = from_amount * from_price
        fees = from_value * CONFIG['total_fee_rate']
        after_fees = from_value - fees
        to_amount = after_fees / to_price if to_price > 0 else 0
        
        from_momentum = self.tracker.get_momentum(from_asset)
        to_momentum = self.tracker.get_momentum(to_asset)
        
        step = len(self.chain) + 1
        
        # Record
        entry = {
            'step': step,
            'time': datetime.now().isoformat(),
            'from_asset': from_asset,
            'to_asset': to_asset,
            'from_amount': from_amount,
            'to_amount': to_amount,
            'from_value': from_value,
            'to_value': after_fees,
            'fees': fees,
            'from_momentum': f"{from_momentum*100:.3f}%/min",
            'to_momentum': f"{to_momentum*100:.3f}%/min",
            'momentum_diff': f"{momentum_diff*100:.3f}%",
            'expected_gain': f"{expected_gain*100:.3f}%/min"
        }
        
        if self.dry_run:
            # Simulate
            self.holdings[from_asset] = self.holdings.get(from_asset, 0) - from_amount
            if self.holdings.get(from_asset, 0) <= 0:
                self.holdings.pop(from_asset, None)
            self.holdings[to_asset] = self.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🌊 STEP {step}: {from_asset} → {to_asset}")
            print(f"      {from_asset} momentum: {from_momentum*100:+.3f}%/min")
            print(f"      {to_asset} momentum: {to_momentum*100:+.3f}%/min")
            print(f"      💫 Riding +{momentum_diff*100:.3f}% momentum wave!")
            print(f"      {from_amount:.8f} {from_asset} → {to_amount:.8f} {to_asset}")
            
        else:
            # Real execution
            success = await self._kraken_convert(from_asset, to_asset, from_amount)
            if not success:
                return False
                
            self.holdings[from_asset] = self.holdings.get(from_asset, 0) - from_amount
            if self.holdings.get(from_asset, 0) <= 0:
                self.holdings.pop(from_asset, None)
            self.holdings[to_asset] = self.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🔥 LIVE STEP {step}: {from_asset} → {to_asset} (riding +{momentum_diff*100:.3f}% wave)")
            
        self.chain.append(entry)
        self.total_conversions += 1
        self.total_fees += fees
        self.last_conversion = time.time()
        
        return True
        
    async def _kraken_convert(self, from_asset: str, to_asset: str, amount: float) -> bool:
        """Execute on Kraken"""
        if not self.kraken:
            return False
            
        # Via USD
        try:
            # Sell from_asset
            result1 = self.kraken.create_order(
                pair=f"{from_asset}USD",
                side='sell',
                order_type='market',
                amount=amount
            )
            if not result1.get('success'):
                return False
                
            # Calculate USD and buy to_asset
            from_price = self.tracker.current_prices.get(from_asset, 0)
            usd = amount * from_price * 0.998
            to_price = self.tracker.current_prices.get(to_asset, 0)
            to_amount = usd / to_price
            
            result2 = self.kraken.create_order(
                pair=f"{to_asset}USD",
                side='buy',
                order_type='market',
                amount=to_amount
            )
            return result2.get('success', False)
        except:
            return False
            
    async def initialize(self, starting_holdings: Dict[str, float] = None):
        """Initialize engine"""
        print("\n" + "="*80)
        print("🌊⚡ MOMENTUM SNOWBALL ENGINE ⚡🌊")
        print("="*80)
        print(f"\nMODE: {'🔵 DRY RUN' if self.dry_run else '🟢 LIVE'}")
        print(f"FEE RATE: {CONFIG['total_fee_rate']*100:.2f}%")
        print(f"MIN MOMENTUM DIFF: {CONFIG['min_momentum_diff']*100:.2f}%")
        print(f"MOMENTUM WINDOW: {CONFIG['momentum_window_seconds']}s")
        
        # Initial price fetch
        print("\n📊 Fetching initial prices...")
        await self.fetch_prices()
        print(f"   ✅ Tracking {len(self.tracker.current_prices)} assets")
        
        # Build momentum baseline
        print("   ⏳ Building momentum baseline (30s)...")
        for i in range(30):
            await self.fetch_prices()
            await asyncio.sleep(1)
            if (i + 1) % 10 == 0:
                print(f"      {i+1}/30...")
                
        # Set holdings
        if starting_holdings:
            self.holdings = starting_holdings.copy()
        elif self.dry_run:
            self.holdings = {
                'BTC': 0.001,
                'ETH': 0.05,
                'SOL': 1.0,
            }
        else:
            await self._load_real_balances()
            
        self.starting_value = self.current_value()
        
        print("\n📦 STARTING PORTFOLIO:")
        for asset, amount in self.holdings.items():
            price = self.tracker.current_prices.get(asset, 0)
            value = amount * price
            momentum = self.tracker.get_momentum(asset)
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f} (momentum: {momentum*100:+.3f}%/min)")
        print(f"\n   💰 TOTAL: ${self.starting_value:.2f}")
        
        # Show current momentum leaders
        print("\n📈 TOP MOMENTUM ASSETS:")
        for asset, mom in self.tracker.get_strongest_rising()[:5]:
            print(f"   {asset}: {mom*100:+.3f}%/min")
            
        print("\n📉 WEAKEST MOMENTUM:")
        for asset, mom in self.tracker.get_weakest_falling()[:5]:
            print(f"   {asset}: {mom*100:+.3f}%/min")
            
        print("="*80)
        
    async def _load_real_balances(self):
        """Load Kraken balances"""
        if self.kraken:
            result = self.kraken.get_balance()
            if result.get('success'):
                for asset, bal in result.get('balance', {}).items():
                    b = float(bal)
                    if b > 0:
                        asset = asset.replace('X', '').replace('Z', '').replace('.S', '')
                        self.holdings[asset] = b
                        
    async def run(self, duration_seconds: int = 300):
        """Run the momentum snowball"""
        await self.initialize()
        
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n🚀 MOMENTUM SNOWBALL ROLLING! ({duration_seconds}s)")
        print("   Surfing momentum waves...")
        print("   Press Ctrl+C to stop\n")
        
        last_status = time.time()
        
        try:
            while self.running and time.time() < end_time:
                # Update prices
                await self.fetch_prices()
                
                # Look for momentum opportunity
                opportunity = self.find_momentum_opportunity()
                
                if opportunity:
                    # Check cooldown
                    if time.time() - self.last_conversion >= CONFIG['conversion_cooldown']:
                        from_asset, to_asset, from_amount, expected_gain, momentum_diff = opportunity
                        await self.execute_conversion(from_asset, to_asset, from_amount, 
                                                      expected_gain, momentum_diff)
                                                      
                # Status every 10 seconds
                if time.time() - last_status >= 10:
                    elapsed = int(time.time() - self.start_time)
                    current = self.current_value()
                    profit = current - self.starting_value
                    
                    mode = "🔵" if self.dry_run else "🟢"
                    print(f"🌊 {mode} | {elapsed}s | Scans: {self.scans} | "
                          f"Converts: {self.total_conversions} | "
                          f"Value: ${current:.2f} | Profit: ${profit:.4f}")
                          
                    # Show current momentum of holdings
                    for asset in list(self.holdings.keys())[:3]:
                        mom = self.tracker.get_momentum(asset)
                        print(f"      {asset}: {mom*100:+.3f}%/min")
                        
                    last_status = time.time()
                    
                await asyncio.sleep(0.5)  # Check every 500ms
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
        self.running = False
        self._print_report()
        
    def _print_report(self):
        """Final report"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current = self.current_value()
        profit = current - self.starting_value
        
        print("\n" + "="*80)
        print("🌊⚡ MOMENTUM SNOWBALL REPORT ⚡🌊")
        print("="*80)
        
        print(f"\n⏱️ DURATION: {elapsed:.1f}s")
        print(f"📊 SCANS: {self.scans:,}")
        print(f"🔄 CONVERSIONS: {self.total_conversions}")
        
        print(f"\n💰 START: ${self.starting_value:.2f}")
        print(f"💰 END: ${current:.2f}")
        print(f"📈 PROFIT: ${profit:.4f}")
        print(f"💸 FEES: ${self.total_fees:.4f}")
        
        if self.starting_value > 0:
            roi = (profit / self.starting_value) * 100
            print(f"📊 ROI: {roi:.4f}%")
            
        if elapsed > 0:
            hourly = (profit / elapsed) * 3600
            print(f"⏰ $/HOUR: ${hourly:.2f}")
            
        if self.chain:
            print(f"\n📜 CONVERSION CHAIN ({len(self.chain)} steps):")
            for step in self.chain[-10:]:
                print(f"   {step['step']}: {step['from_asset']} → {step['to_asset']} "
                      f"(wave: {step['momentum_diff']})")
                      
        print("\n📦 FINAL HOLDINGS:")
        for asset, amount in sorted(self.holdings.items()):
            price = self.tracker.current_prices.get(asset, 0)
            value = amount * price
            mom = self.tracker.get_momentum(asset)
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f} ({mom*100:+.3f}%/min)")
                
        print("="*80)
        
        # Save
        filename = f"momentum_snowball_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'duration': elapsed,
                'starting_value': self.starting_value,
                'ending_value': current,
                'profit': profit,
                'fees': self.total_fees,
                'conversions': self.total_conversions,
                'chain': self.chain,
                'holdings': self.holdings
            }, f, indent=2)
        print(f"\n💾 Saved to {filename}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Momentum Snowball Engine')
    parser.add_argument('--live', action='store_true', help='Live trading')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    args = parser.parse_args()
    
    if args.live:
        print("\n🔴" * 40)
        print("⚠️  LIVE TRADING MODE")
        print("🔴" * 40)
        confirm = input("\nType 'MOMENTUM' to confirm: ")
        if confirm != 'MOMENTUM':
            print("Cancelled.")
            return
            
    engine = MomentumSnowball(dry_run=not args.live)
    await engine.run(duration_seconds=args.duration)


if __name__ == '__main__':
    asyncio.run(main())
