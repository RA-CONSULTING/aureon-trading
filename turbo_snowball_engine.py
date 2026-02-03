#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ⚡🔥 TURBO SNOWBALL ENGINE 🔥⚡                                                 ║
║                                                                                   ║
║   MAXIMUM SPEED CONVERSION SYSTEM                                                 ║
║                                                                                   ║
║   • WebSocket streaming for INSTANT price updates                                 ║
║   • Scans 1000+ pairs per second                                                  ║
║   • Converts the MOMENT profit is found                                           ║
║   • Tracks entire chain of conversions                                            ║
║   • Compounds gains automatically                                                 ║
║                                                                                   ║
║   THE MATH:                                                                        ║
║   If we hold A worth $100                                                         ║
║   And B is worth $100.10 (after fees)                                             ║
║   CONVERT! Net gain: $0.10                                                        ║
║   Now we hold B worth $100.10                                                     ║
║   Scan again... repeat forever                                                    ║
║                                                                                   ║
║   SPEED = MONEY                                                                   ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import time
import websockets
import aiohttp
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict
from dataclasses import dataclass, field
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# FEE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

FEES = {
    'kraken_maker': 0.0016,    # 0.16%
    'kraken_taker': 0.0026,    # 0.26%
    'binance_maker': 0.001,    # 0.10%
    'binance_taker': 0.001,    # 0.10%
    'slippage': 0.0003,        # 0.03% average slippage
    'spread_cost': 0.0002,     # 0.02% spread cost
}

# Total cost per conversion (conservative)
TOTAL_CONVERSION_COST = FEES['kraken_maker'] + FEES['slippage'] + FEES['spread_cost']
# = 0.16% + 0.03% + 0.02% = 0.21%

# Minimum gain to make a conversion worthwhile
MIN_GAIN_THRESHOLD = TOTAL_CONVERSION_COST + 0.0001  # 0.22% minimum


@dataclass
class TurboState:
    """Engine state tracking"""
    # Holdings
    holdings: Dict[str, float] = field(default_factory=dict)
    starting_value_usd: float = 0.0
    
    # Chain tracking
    chain: List[Dict] = field(default_factory=list)
    step_count: int = 0
    
    # Stats
    total_gained: float = 0.0
    total_fees: float = 0.0
    scans: int = 0
    conversions: int = 0
    
    def current_value(self, prices: Dict[str, float]) -> float:
        total = 0.0
        for asset, amount in self.holdings.items():
            price = prices.get(asset, 0)
            total += amount * price
        return total
        
    def net_profit(self, prices: Dict[str, float]) -> float:
        return self.current_value(prices) - self.starting_value_usd


class TurboPriceStream:
    """
    Ultra-fast price streaming via WebSocket
    Updates prices in real-time for instant conversion decisions
    """
    
    def __init__(self):
        self.prices: Dict[str, float] = {}  # Asset -> USD price
        self.bid_ask: Dict[str, Tuple[float, float]] = {}  # Asset -> (bid, ask)
        self.last_update: Dict[str, float] = {}  # Asset -> timestamp
        self.running = False
        self._ws_task = None
        self._update_callbacks = []
        
    def on_update(self, callback):
        """Register callback for price updates"""
        self._update_callbacks.append(callback)
        
    async def start(self):
        """Start streaming prices"""
        self.running = True
        
        # Start WebSocket streams
        self._ws_task = asyncio.create_task(self._run_streams())
        
        # Initial REST fetch for complete price list
        await self._fetch_all_prices()
        
    async def stop(self):
        """Stop streaming"""
        self.running = False
        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
                
    async def _fetch_all_prices(self):
        """Fetch all prices via REST API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Binance prices
                async with session.get('https://api.binance.com/api/v3/ticker/price', 
                                       timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        tickers = await resp.json()
                        btc_price = 91000
                        eth_price = 3150
                        
                        for t in tickers:
                            symbol = t['symbol']
                            price = float(t['price'])
                            
                            # USD pairs
                            for quote in ['USDT', 'USDC', 'BUSD']:
                                if symbol.endswith(quote):
                                    base = symbol[:-len(quote)]
                                    self.prices[base] = price
                                    if base == 'BTC':
                                        btc_price = price
                                    elif base == 'ETH':
                                        eth_price = price
                                    break
                                    
                        # BTC pairs
                        for t in tickers:
                            symbol = t['symbol']
                            price = float(t['price'])
                            if symbol.endswith('BTC') and not symbol.endswith('USDT'):
                                base = symbol[:-3]
                                if base not in self.prices:
                                    self.prices[base] = price * btc_price
                                    
        except Exception as e:
            logger.debug(f"REST fetch error: {e}")
            
        # Set stablecoin prices
        for stable in ['USD', 'USDT', 'USDC', 'BUSD', 'DAI']:
            self.prices[stable] = 1.0
            
    async def _run_streams(self):
        """Run WebSocket price streams"""
        while self.running:
            try:
                await self._connect_binance_stream()
            except Exception as e:
                logger.debug(f"Stream error: {e}")
                await asyncio.sleep(1)
                
    async def _connect_binance_stream(self):
        """Connect to Binance WebSocket for real-time prices"""
        url = "wss://stream.binance.com:9443/ws/!miniTicker@arr"
        
        async with websockets.connect(url) as ws:
            while self.running:
                try:
                    msg = await asyncio.wait_for(ws.recv(), timeout=5)
                    data = json.loads(msg)
                    
                    btc_price = self.prices.get('BTC', 91000)
                    
                    for ticker in data:
                        symbol = ticker['s']
                        price = float(ticker['c'])  # Close price
                        
                        # Update USD pairs
                        for quote in ['USDT', 'USDC']:
                            if symbol.endswith(quote):
                                base = symbol[:-len(quote)]
                                old_price = self.prices.get(base, 0)
                                self.prices[base] = price
                                self.last_update[base] = time.time()
                                
                                if base == 'BTC':
                                    btc_price = price
                                    
                                # Notify callbacks of significant changes
                                if old_price > 0:
                                    change = abs(price - old_price) / old_price
                                    if change > 0.001:  # 0.1% change
                                        for cb in self._update_callbacks:
                                            try:
                                                cb(base, price, change)
                                            except:
                                                pass
                                break
                                
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    logger.debug(f"WS message error: {e}")
                    break
                    
    def get_price(self, asset: str) -> float:
        """Get current USD price for asset"""
        asset = asset.upper()
        if asset in self.prices:
            return self.prices[asset]
        # Stablecoins
        if asset in ['USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'ZUSD']:
            return 1.0
        return 0.0


class TurboSnowball:
    """
    TURBO SNOWBALL ENGINE
    
    Maximum speed conversion system.
    Scans continuously, converts instantly when profit is found.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.stream = TurboPriceStream()
        self.state = TurboState()
        self.running = False
        
        # Kraken for execution
        self.kraken = None
        if not dry_run:
            try:
                from kraken_client import KrakenClient, get_kraken_client
                self.kraken = get_kraken_client()
            except:
                print("⚠️ Kraken not available - running dry")
                self.dry_run = True
                
        # Target assets (liquid pairs on Kraken)
        self.target_assets = [
            'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'MATIC',
            'AVAX', 'ATOM', 'UNI', 'AAVE', 'LTC', 'BCH', 'ALGO', 'XLM',
            'DOGE', 'SHIB', 'NEAR', 'FTM', 'SAND', 'MANA', 'AXS', 'ENJ'
        ]
        
        # Timing
        self.start_time = None
        self.last_conversion_time = 0
        self.min_conversion_interval = 0.5  # 500ms between conversions
        
    async def initialize(self, starting_holdings: Dict[str, float] = None):
        """Initialize the engine"""
        print("\n" + "="*80)
        print("⚡🔥 TURBO SNOWBALL ENGINE 🔥⚡")
        print("="*80)
        print(f"\nMODE: {'🔵 DRY RUN' if self.dry_run else '🟢 LIVE TRADING'}")
        print(f"FEE ESTIMATE: {TOTAL_CONVERSION_COST*100:.2f}%")
        print(f"MIN GAIN THRESHOLD: {MIN_GAIN_THRESHOLD*100:.2f}%")
        
        # Start price stream
        print("\n📡 Starting real-time price stream...")
        await self.stream.start()
        await asyncio.sleep(2)  # Wait for initial prices
        print(f"   ✅ Streaming {len(self.stream.prices)} assets")
        
        # Set initial holdings
        if starting_holdings:
            self.state.holdings = starting_holdings.copy()
        elif self.dry_run:
            # Simulated portfolio
            self.state.holdings = {
                'BTC': 0.001,
                'ETH': 0.05,
                'SOL': 1.0,
            }
        else:
            # Load real balances
            await self._load_real_balances()
            
        # Calculate starting value
        self.state.starting_value_usd = self.state.current_value(self.stream.prices)
        
        print("\n📦 STARTING PORTFOLIO:")
        for asset, amount in self.state.holdings.items():
            price = self.stream.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f}")
        print(f"\n   💰 TOTAL: ${self.state.starting_value_usd:.2f}")
        print("="*80)
        
    async def _load_real_balances(self):
        """Load real Kraken balances"""
        if self.kraken:
            result = self.kraken.get_balance()
            if result.get('success'):
                for asset, balance in result.get('balance', {}).items():
                    bal = float(balance)
                    if bal > 0:
                        asset = asset.replace('X', '').replace('Z', '').replace('.S', '')
                        self.state.holdings[asset] = bal
                        
    def _find_best_conversion(self) -> Optional[Tuple[str, str, float, float, float]]:
        """
        Find the best profitable conversion RIGHT NOW
        
        Returns: (from_asset, to_asset, from_amount, to_amount, gain_pct) or None
        """
        best = None
        best_gain = MIN_GAIN_THRESHOLD
        
        self.state.scans += 1
        
        for from_asset, from_amount in list(self.state.holdings.items()):
            from_price = self.stream.get_price(from_asset)
            from_value = from_amount * from_price
            
            # Skip tiny holdings
            if from_value < 5.0:
                continue
                
            for to_asset in self.target_assets:
                if to_asset == from_asset:
                    continue
                    
                to_price = self.stream.get_price(to_asset)
                if to_price <= 0:
                    continue
                    
                # Calculate conversion
                # After fees, how much USD value do we have?
                value_after_fees = from_value * (1 - TOTAL_CONVERSION_COST)
                
                # How much of to_asset can we get?
                to_amount = value_after_fees / to_price
                to_value = to_amount * to_price
                
                # Gain percentage
                gain_pct = (to_value - from_value) / from_value if from_value > 0 else 0
                
                # Is this profitable AND better than current best?
                if gain_pct > best_gain:
                    best_gain = gain_pct
                    best = (from_asset, to_asset, from_amount, to_amount, gain_pct)
                    
        return best
        
    async def _execute_conversion(self, from_asset: str, to_asset: str,
                                   from_amount: float, to_amount: float,
                                   gain_pct: float) -> bool:
        """Execute a conversion"""
        from_price = self.stream.get_price(from_asset)
        to_price = self.stream.get_price(to_asset)
        from_value = from_amount * from_price
        to_value = to_amount * to_price
        
        gain_usd = to_value - from_value
        fees_usd = from_value * TOTAL_CONVERSION_COST
        
        self.state.step_count += 1
        step = self.state.step_count
        
        # Record the step
        chain_entry = {
            'step': step,
            'time': datetime.now().isoformat(),
            'from': from_asset,
            'to': to_asset,
            'from_amount': from_amount,
            'to_amount': to_amount,
            'from_value': from_value,
            'to_value': to_value,
            'gain_usd': gain_usd,
            'gain_pct': gain_pct,
            'fees': fees_usd
        }
        
        if self.dry_run:
            # Simulate
            self.state.holdings[from_asset] = self.state.holdings.get(from_asset, 0) - from_amount
            if self.state.holdings.get(from_asset, 0) <= 0:
                self.state.holdings.pop(from_asset, None)
            self.state.holdings[to_asset] = self.state.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   ❄️ STEP {step}: {from_asset} → {to_asset}")
            print(f"      {from_amount:.8f} {from_asset} (${from_value:.4f})")
            print(f"      → {to_amount:.8f} {to_asset} (${to_value:.4f})")
            print(f"      💰 GAIN: ${gain_usd:.6f} ({gain_pct*100:.4f}%)")
            
        else:
            # Real execution
            success = await self._kraken_convert(from_asset, to_asset, from_amount)
            if not success:
                return False
                
            self.state.holdings[from_asset] = self.state.holdings.get(from_asset, 0) - from_amount
            if self.state.holdings.get(from_asset, 0) <= 0:
                self.state.holdings.pop(from_asset, None)
            self.state.holdings[to_asset] = self.state.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🔥 LIVE STEP {step}: {from_asset} → {to_asset} (+${gain_usd:.6f})")
            
        self.state.chain.append(chain_entry)
        self.state.total_gained += gain_usd
        self.state.total_fees += fees_usd
        self.state.conversions += 1
        
        self.last_conversion_time = time.time()
        
        return True
        
    async def _kraken_convert(self, from_asset: str, to_asset: str, amount: float) -> bool:
        """Execute conversion on Kraken"""
        if not self.kraken:
            return False
            
        # Try direct pair first
        for pair in [f"{from_asset}{to_asset}", f"{from_asset}USD", f"{to_asset}USD"]:
            try:
                if 'USD' in pair:
                    # Two-step via USD
                    # Sell from_asset for USD
                    result1 = self.kraken.create_order(
                        pair=f"{from_asset}USD",
                        side='sell',
                        order_type='market',
                        amount=amount
                    )
                    if result1.get('success'):
                        # Buy to_asset with USD
                        from_price = self.stream.get_price(from_asset)
                        usd_amount = amount * from_price * 0.998
                        to_price = self.stream.get_price(to_asset)
                        to_amount = usd_amount / to_price
                        
                        result2 = self.kraken.create_order(
                            pair=f"{to_asset}USD",
                            side='buy',
                            order_type='market',
                            amount=to_amount
                        )
                        return result2.get('success', False)
                else:
                    # Direct conversion
                    result = self.kraken.create_order(
                        pair=pair,
                        side='sell',
                        order_type='market',
                        amount=amount
                    )
                    return result.get('success', False)
            except:
                continue
                
        return False
        
    async def run(self, duration_seconds: int = 300):
        """
        RUN THE TURBO SNOWBALL
        
        Scan continuously, convert when profitable, compound forever.
        """
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n🚀 TURBO SNOWBALL ROLLING! ({duration_seconds}s)")
        print("   Scanning for profitable conversions...")
        print("   Press Ctrl+C to stop\n")
        
        last_status = time.time()
        
        try:
            while self.running and time.time() < end_time:
                # Check for profitable conversion
                opportunity = self._find_best_conversion()
                
                if opportunity:
                    # Check rate limit
                    if time.time() - self.last_conversion_time >= self.min_conversion_interval:
                        from_asset, to_asset, from_amount, to_amount, gain_pct = opportunity
                        await self._execute_conversion(from_asset, to_asset, from_amount, to_amount, gain_pct)
                        
                # Status every 5 seconds
                if time.time() - last_status >= 5:
                    elapsed = int(time.time() - self.start_time)
                    current_value = self.state.current_value(self.stream.prices)
                    profit = current_value - self.state.starting_value_usd
                    
                    mode = "🔵" if self.dry_run else "🟢"
                    print(f"⚡ {mode} | {elapsed}s | Scans: {self.state.scans} | "
                          f"Converts: {self.state.conversions} | "
                          f"Value: ${current_value:.2f} | "
                          f"Profit: ${profit:.4f}")
                    last_status = time.time()
                    
                # Tiny delay to prevent CPU spinning
                await asyncio.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Stopped by user")
            
        self.running = False
        await self.stream.stop()
        self._print_report()
        
    def _print_report(self):
        """Print final report"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        current_value = self.state.current_value(self.stream.prices)
        profit = current_value - self.state.starting_value_usd
        
        print("\n" + "="*80)
        print("⚡🔥 TURBO SNOWBALL REPORT 🔥⚡")
        print("="*80)
        
        print(f"\n⏱️ DURATION: {elapsed:.1f}s")
        print(f"📊 SCANS: {self.state.scans:,}")
        print(f"🔄 CONVERSIONS: {self.state.conversions}")
        
        if elapsed > 0:
            scans_per_sec = self.state.scans / elapsed
            print(f"⚡ SPEED: {scans_per_sec:.0f} scans/sec")
            
        print(f"\n💰 START: ${self.state.starting_value_usd:.2f}")
        print(f"💰 END: ${current_value:.2f}")
        print(f"📈 PROFIT: ${profit:.4f}")
        print(f"💸 FEES: ${self.state.total_fees:.4f}")
        
        if self.state.starting_value_usd > 0:
            roi = (profit / self.state.starting_value_usd) * 100
            print(f"📊 ROI: {roi:.4f}%")
            
        if elapsed > 0:
            hourly = (profit / elapsed) * 3600
            print(f"⏰ $/HOUR: ${hourly:.2f}")
            
        if self.state.chain:
            print(f"\n📜 CHAIN ({len(self.state.chain)} steps):")
            for step in self.state.chain[-10:]:
                print(f"   {step['step']}: {step['from']} → {step['to']} "
                      f"+${step['gain_usd']:.6f} ({step['gain_pct']*100:.4f}%)")
                      
        print("\n📦 HOLDINGS:")
        for asset, amount in sorted(self.state.holdings.items()):
            price = self.stream.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f}")
                
        print("="*80)
        
        # Save chain
        self._save_results()
        
    def _save_results(self):
        """Save results to file"""
        results = {
            'timestamp': datetime.now().isoformat(),
            'duration': time.time() - self.start_time if self.start_time else 0,
            'starting_value': self.state.starting_value_usd,
            'ending_value': self.state.current_value(self.stream.prices),
            'profit': self.state.current_value(self.stream.prices) - self.state.starting_value_usd,
            'fees': self.state.total_fees,
            'conversions': self.state.conversions,
            'scans': self.state.scans,
            'chain': self.state.chain,
            'final_holdings': self.state.holdings
        }
        
        filename = f"turbo_snowball_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n💾 Saved to {filename}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Turbo Snowball Engine')
    parser.add_argument('--live', action='store_true', help='LIVE trading mode')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    args = parser.parse_args()
    
    if args.live:
        print("\n" + "🔴"*40)
        print("⚠️  LIVE TRADING MODE ⚠️")
        print("Real money will be used!")
        print("🔴"*40)
        confirm = input("\nType 'TURBO' to confirm: ")
        if confirm != 'TURBO':
            print("Cancelled.")
            return
            
    engine = TurboSnowball(dry_run=not args.live)
    await engine.initialize()
    await engine.run(duration_seconds=args.duration)


if __name__ == '__main__':
    asyncio.run(main())
