#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ❄️🔥 SNOWBALL CONVERSION ENGINE 🔥❄️                                            ║
║                                                                                   ║
║   THE CONCEPT:                                                                    ║
║   • Start with ANY asset (BTC, ETH, SOL, whatever)                               ║
║   • Scan ENTIRE market for better conversions                                     ║
║   • Convert if: new_value > old_value (after fees, slippage, spread)             ║
║   • Remember every step in the chain                                              ║
║   • SPEED IS KEY - faster conversions = quicker compounding                       ║
║                                                                                   ║
║   THE MATH:                                                                        ║
║   • Taker fee: 0.26%                                                              ║
║   • Maker fee: 0.16%                                                              ║
║   • Slippage estimate: 0.05%                                                      ║
║   • If net_gain > 0 (even $0.001) → CONVERT                                       ║
║                                                                                   ║
║   ONE RULE: NEVER LOSE. ALWAYS GROW. SNOWBALL.                                   ║
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
from typing import Dict, List, Optional, Tuple, Any
from collections import deque
from dataclasses import dataclass, field
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

SNOWBALL_CONFIG = {
    # Fees (Kraken)
    'taker_fee': 0.0026,        # 0.26%
    'maker_fee': 0.0016,        # 0.16% - we'll use maker when possible
    'slippage': 0.0005,         # 0.05% estimated slippage
    'spread_buffer': 0.0002,    # 0.02% extra safety buffer
    
    # Minimum profitable conversion
    'min_net_gain_usd': 0.001,  # Even $0.001 profit = CONVERT
    'min_net_gain_pct': 0.0001, # 0.01% minimum gain
    
    # Speed settings
    'scan_interval_ms': 100,    # Scan every 100ms
    'max_conversions_per_min': 60,  # Up to 60 conversions per minute
    
    # Portfolio
    'min_hold_usd': 5.0,        # Minimum USD value to convert
}


@dataclass
class ConversionStep:
    """A single step in the snowball chain"""
    step_num: int
    timestamp: datetime
    from_asset: str
    to_asset: str
    from_amount: float
    to_amount: float
    from_value_usd: float
    to_value_usd: float
    net_gain_usd: float
    net_gain_pct: float
    fees_paid_usd: float
    cumulative_gain_usd: float
    
    def to_dict(self) -> Dict:
        return {
            'step': self.step_num,
            'time': self.timestamp.isoformat(),
            'from': f"{self.from_amount:.8f} {self.from_asset}",
            'to': f"{self.to_amount:.8f} {self.to_asset}",
            'from_usd': self.from_value_usd,
            'to_usd': self.to_value_usd,
            'net_gain': self.net_gain_usd,
            'gain_pct': f"{self.net_gain_pct*100:.4f}%",
            'fees': self.fees_paid_usd,
            'cumulative': self.cumulative_gain_usd
        }


@dataclass
class Portfolio:
    """Current portfolio state"""
    holdings: Dict[str, float] = field(default_factory=dict)
    total_value_usd: float = 0.0
    starting_value_usd: float = 0.0
    conversion_chain: List[ConversionStep] = field(default_factory=list)
    total_fees_paid: float = 0.0
    total_conversions: int = 0
    
    def net_profit(self) -> float:
        return self.total_value_usd - self.starting_value_usd


class PriceCache:
    """Ultra-fast price cache for all assets"""
    
    def __init__(self):
        self.prices: Dict[str, float] = {}  # Asset -> USD price
        self.pairs: Dict[str, Dict] = {}     # Pair -> {bid, ask, last}
        self.last_update: float = 0
        
    async def update_all_prices(self):
        """Fetch ALL prices from multiple sources"""
        tasks = [
            self._fetch_binance_prices(),
            self._fetch_kraken_prices(),
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        self.last_update = time.time()
        
    async def _fetch_binance_prices(self):
        """Get all Binance prices"""
        try:
            async with aiohttp.ClientSession() as session:
                # Get all tickers
                async with session.get('https://api.binance.com/api/v3/ticker/price', timeout=5) as resp:
                    if resp.status == 200:
                        tickers = await resp.json()
                        for t in tickers:
                            symbol = t['symbol']
                            price = float(t['price'])
                            
                            # Extract base/quote
                            for quote in ['USDT', 'USDC', 'BUSD', 'USD']:
                                if symbol.endswith(quote):
                                    base = symbol[:-len(quote)]
                                    self.prices[base] = price
                                    self.pairs[f"{base}/{quote}"] = {
                                        'bid': price * 0.9999,
                                        'ask': price * 1.0001,
                                        'last': price
                                    }
                                    break
                                    
                # Get BTC price for conversions
                btc_price = self.prices.get('BTC', 91000)
                for t in tickers:
                    symbol = t['symbol']
                    price = float(t['price'])
                    if symbol.endswith('BTC'):
                        base = symbol[:-3]
                        if base not in self.prices:
                            self.prices[base] = price * btc_price
                            
                # Get ETH price for conversions
                eth_price = self.prices.get('ETH', 3150)
                for t in tickers:
                    symbol = t['symbol']
                    price = float(t['price'])
                    if symbol.endswith('ETH'):
                        base = symbol[:-3]
                        if base not in self.prices:
                            self.prices[base] = price * eth_price
                            
        except Exception as e:
            logger.debug(f"Binance fetch error: {e}")
            
    async def _fetch_kraken_prices(self):
        """Get all Kraken prices"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.kraken.com/0/public/Ticker', timeout=5) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('result'):
                            for pair, info in data['result'].items():
                                # Parse Kraken pair format
                                last = float(info['c'][0])
                                bid = float(info['b'][0])
                                ask = float(info['a'][0])
                                
                                # Store pair data
                                self.pairs[pair] = {
                                    'bid': bid,
                                    'ask': ask,
                                    'last': last
                                }
                                
                                # Extract USD prices
                                for quote in ['USD', 'ZUSD', 'USDT']:
                                    if pair.endswith(quote):
                                        base = pair.replace('X', '').replace('Z', '')
                                        base = base[:-len(quote)]
                                        if base:
                                            self.prices[base] = last
                                            
        except Exception as e:
            logger.debug(f"Kraken fetch error: {e}")
            
    def get_price(self, asset: str) -> float:
        """Get USD price for an asset"""
        # Normalize asset name
        asset = asset.upper().replace('X', '').replace('Z', '')
        
        # Direct lookup
        if asset in self.prices:
            return self.prices[asset]
            
        # Try variations
        for var in [asset, f"X{asset}", f"{asset}USD", f"X{asset}ZUSD"]:
            if var in self.prices:
                return self.prices[var]
                
        # Stablecoins
        if asset in ['USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'ZUSD']:
            return 1.0
            
        return 0.0
        
    def get_pair_prices(self, base: str, quote: str) -> Optional[Tuple[float, float]]:
        """Get bid/ask for a trading pair"""
        # Try different pair formats
        for pair in [f"{base}/{quote}", f"{base}{quote}", f"X{base}Z{quote}", f"X{base}{quote}"]:
            if pair in self.pairs:
                p = self.pairs[pair]
                return (p['bid'], p['ask'])
        return None


class SnowballEngine:
    """
    THE SNOWBALL ENGINE
    
    Continuously scans for profitable conversions and executes them.
    Every conversion that nets profit (after fees) = SUCCESS.
    Speed + Compounding = Exponential Growth
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.price_cache = PriceCache()
        self.portfolio = Portfolio()
        self.running = False
        
        # Kraken client for execution
        self.kraken = None
        if not dry_run:
            try:
                from kraken_client import KrakenClient
                self.kraken = KrakenClient()
            except:
                logger.warning("⚠️ Kraken client not available - running in dry mode")
                self.dry_run = True
                
        # Stats
        self.scans_performed = 0
        self.opportunities_found = 0
        self.conversions_executed = 0
        self.start_time = None
        
        # Available trading pairs on Kraken
        self.kraken_pairs = set()
        
    async def initialize(self):
        """Initialize the engine"""
        print("\n" + "="*80)
        print("❄️🔥 SNOWBALL CONVERSION ENGINE INITIALIZING 🔥❄️")
        print("="*80)
        
        # Load Kraken pairs
        await self._load_kraken_pairs()
        
        # Initial price fetch
        print("\n📊 Fetching prices from ALL exchanges...")
        await self.price_cache.update_all_prices()
        print(f"   ✅ {len(self.price_cache.prices)} assets priced")
        print(f"   ✅ {len(self.price_cache.pairs)} trading pairs loaded")
        
        # Load or set portfolio
        if self.dry_run:
            # Simulated starting portfolio
            self.portfolio.holdings = {
                'BTC': 0.001,   # ~$91
                'ETH': 0.05,   # ~$157
                'SOL': 1.0,    # ~$134
            }
            print("\n🔵 DRY RUN MODE - Simulated portfolio:")
        else:
            # Load real balances
            await self._load_real_balances()
            print("\n🟢 LIVE MODE - Real portfolio:")
            
        # Calculate starting value
        self._update_portfolio_value()
        self.portfolio.starting_value_usd = self.portfolio.total_value_usd
        
        for asset, amount in self.portfolio.holdings.items():
            price = self.price_cache.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} (${value:.2f})")
                
        print(f"\n   💰 TOTAL STARTING VALUE: ${self.portfolio.starting_value_usd:.2f}")
        print("="*80)
        
    async def _load_kraken_pairs(self):
        """Load available Kraken trading pairs"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.kraken.com/0/public/AssetPairs', timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get('result'):
                            for pair, info in data['result'].items():
                                if not pair.endswith('.d'):  # Skip dark pools
                                    self.kraken_pairs.add(pair)
                                    # Also add normalized version
                                    base = info.get('base', '')
                                    quote = info.get('quote', '')
                                    self.kraken_pairs.add(f"{base}{quote}")
        except Exception as e:
            logger.debug(f"Error loading Kraken pairs: {e}")
            
        # Add common pairs
        common = ['BTCUSD', 'ETHUSD', 'SOLUSD', 'XRPUSD', 'ADAUSD', 'DOTUSD', 
                  'LINKUSD', 'MATICUSD', 'AVAXUSD', 'ATOMUSD', 'UNIUSD']
        self.kraken_pairs.update(common)
        
    async def _load_real_balances(self):
        """Load real Kraken balances"""
        if self.kraken:
            result = self.kraken.get_balance()
            if result.get('success'):
                for asset, balance in result.get('balance', {}).items():
                    bal = float(balance)
                    if bal > 0:
                        # Normalize asset name
                        asset = asset.replace('X', '').replace('Z', '').replace('.S', '')
                        self.portfolio.holdings[asset] = bal
                        
    def _update_portfolio_value(self):
        """Calculate current portfolio value in USD"""
        total = 0.0
        for asset, amount in self.portfolio.holdings.items():
            price = self.price_cache.get_price(asset)
            total += amount * price
        self.portfolio.total_value_usd = total
        
    def _calculate_conversion_value(self, from_asset: str, from_amount: float, 
                                     to_asset: str) -> Tuple[float, float, float, float]:
        """
        Calculate what we'd get converting from_asset to to_asset
        
        Returns: (to_amount, net_value_usd, fees_usd, net_gain_usd)
        """
        # Get prices
        from_price = self.price_cache.get_price(from_asset)
        to_price = self.price_cache.get_price(to_asset)
        
        if from_price <= 0 or to_price <= 0:
            return (0, 0, 0, -999)
            
        # Current value
        from_value_usd = from_amount * from_price
        
        # Calculate fees
        fee_rate = SNOWBALL_CONFIG['maker_fee']  # Use maker fee
        slippage = SNOWBALL_CONFIG['slippage']
        spread_buffer = SNOWBALL_CONFIG['spread_buffer']
        
        total_cost_rate = fee_rate + slippage + spread_buffer
        
        # Value after fees
        value_after_fees = from_value_usd * (1 - total_cost_rate)
        fees_usd = from_value_usd * total_cost_rate
        
        # How much of to_asset we'd get
        to_amount = value_after_fees / to_price
        
        # Net gain
        net_gain_usd = value_after_fees - from_value_usd
        
        return (to_amount, value_after_fees, fees_usd, net_gain_usd)
        
    async def find_best_conversion(self) -> Optional[Tuple[str, str, float, float, float]]:
        """
        Scan entire market for the best conversion opportunity
        
        Returns: (from_asset, to_asset, from_amount, to_amount, net_gain_usd) or None
        """
        best = None
        best_gain_pct = SNOWBALL_CONFIG['min_net_gain_pct']
        
        # For each asset we hold
        for from_asset, from_amount in list(self.portfolio.holdings.items()):
            from_price = self.price_cache.get_price(from_asset)
            from_value = from_amount * from_price
            
            # Skip if too small
            if from_value < SNOWBALL_CONFIG['min_hold_usd']:
                continue
                
            # Check conversion to every other asset
            for to_asset in self.price_cache.prices.keys():
                if to_asset == from_asset:
                    continue
                    
                # Calculate conversion
                to_amount, net_value, fees, net_gain = self._calculate_conversion_value(
                    from_asset, from_amount, to_asset
                )
                
                if net_gain < SNOWBALL_CONFIG['min_net_gain_usd']:
                    continue
                    
                gain_pct = net_gain / from_value if from_value > 0 else 0
                
                # Is this the best opportunity?
                if gain_pct > best_gain_pct:
                    best_gain_pct = gain_pct
                    best = (from_asset, to_asset, from_amount, to_amount, net_gain)
                    
        self.scans_performed += 1
        if best:
            self.opportunities_found += 1
            
        return best
        
    async def find_profitable_conversions(self) -> List[Tuple[str, str, float, float, float]]:
        """
        Find ALL profitable conversions, sorted by gain percentage
        
        Returns list of: (from_asset, to_asset, from_amount, to_amount, net_gain_usd)
        """
        opportunities = []
        
        # For each asset we hold
        for from_asset, from_amount in list(self.portfolio.holdings.items()):
            from_price = self.price_cache.get_price(from_asset)
            from_value = from_amount * from_price
            
            # Skip if too small
            if from_value < SNOWBALL_CONFIG['min_hold_usd']:
                continue
                
            # Check top potential targets
            targets = ['BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'MATIC', 
                      'AVAX', 'ATOM', 'UNI', 'AAVE', 'SNX', 'COMP', 'MKR', 'SUSHI']
            
            for to_asset in targets:
                if to_asset == from_asset:
                    continue
                    
                to_price = self.price_cache.get_price(to_asset)
                if to_price <= 0:
                    continue
                    
                # Calculate conversion
                to_amount, net_value, fees, net_gain = self._calculate_conversion_value(
                    from_asset, from_amount, to_asset
                )
                
                if net_gain >= SNOWBALL_CONFIG['min_net_gain_usd']:
                    gain_pct = net_gain / from_value if from_value > 0 else 0
                    opportunities.append((from_asset, to_asset, from_amount, to_amount, net_gain, gain_pct))
                    
        # Sort by gain percentage (best first)
        opportunities.sort(key=lambda x: x[5], reverse=True)
        
        self.scans_performed += 1
        self.opportunities_found += len(opportunities)
        
        return [(o[0], o[1], o[2], o[3], o[4]) for o in opportunities]
        
    async def execute_conversion(self, from_asset: str, to_asset: str, 
                                  from_amount: float, to_amount: float, 
                                  net_gain: float) -> bool:
        """Execute a conversion"""
        from_price = self.price_cache.get_price(from_asset)
        to_price = self.price_cache.get_price(to_asset)
        from_value = from_amount * from_price
        to_value = to_amount * to_price
        
        # Calculate fees
        fee_rate = SNOWBALL_CONFIG['maker_fee'] + SNOWBALL_CONFIG['slippage']
        fees_paid = from_value * fee_rate
        
        step_num = len(self.portfolio.conversion_chain) + 1
        cumulative = sum(s.net_gain_usd for s in self.portfolio.conversion_chain) + net_gain
        
        # Create step record
        step = ConversionStep(
            step_num=step_num,
            timestamp=datetime.now(),
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=from_amount,
            to_amount=to_amount,
            from_value_usd=from_value,
            to_value_usd=to_value,
            net_gain_usd=net_gain,
            net_gain_pct=net_gain / from_value if from_value > 0 else 0,
            fees_paid_usd=fees_paid,
            cumulative_gain_usd=cumulative
        )
        
        if self.dry_run:
            # Simulate the conversion
            self.portfolio.holdings[from_asset] = self.portfolio.holdings.get(from_asset, 0) - from_amount
            if self.portfolio.holdings[from_asset] <= 0:
                del self.portfolio.holdings[from_asset]
            self.portfolio.holdings[to_asset] = self.portfolio.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   ❄️ STEP {step_num}: {from_asset} → {to_asset}")
            print(f"      {from_amount:.8f} {from_asset} (${from_value:.4f})")
            print(f"      → {to_amount:.8f} {to_asset} (${to_value:.4f})")
            print(f"      💰 NET GAIN: ${net_gain:.6f} ({step.net_gain_pct*100:.4f}%)")
            print(f"      📈 CUMULATIVE: ${cumulative:.4f}")
            
        else:
            # Real execution via Kraken
            success = await self._execute_kraken_conversion(from_asset, to_asset, from_amount)
            if not success:
                return False
                
            # Update holdings (will be verified on next balance check)
            self.portfolio.holdings[from_asset] = self.portfolio.holdings.get(from_asset, 0) - from_amount
            if self.portfolio.holdings[from_asset] <= 0:
                del self.portfolio.holdings[from_asset]
            self.portfolio.holdings[to_asset] = self.portfolio.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🔥 LIVE STEP {step_num}: {from_asset} → {to_asset}")
            print(f"      {from_amount:.8f} {from_asset} → {to_amount:.8f} {to_asset}")
            print(f"      💰 NET GAIN: ${net_gain:.6f}")
            
        # Record the step
        self.portfolio.conversion_chain.append(step)
        self.portfolio.total_fees_paid += fees_paid
        self.portfolio.total_conversions += 1
        self.conversions_executed += 1
        
        # Update portfolio value
        self._update_portfolio_value()
        
        return True
        
    async def _execute_kraken_conversion(self, from_asset: str, to_asset: str, 
                                          amount: float) -> bool:
        """Execute conversion on Kraken"""
        if not self.kraken:
            return False
            
        # Determine the trading pair and direction
        # Try from_asset/to_asset first
        pair = f"{from_asset}{to_asset}"
        reverse = False
        
        if pair not in self.kraken_pairs:
            # Try reverse
            pair = f"{to_asset}{from_asset}"
            reverse = True
            
        if pair not in self.kraken_pairs:
            # Try with USD intermediate
            # First sell from_asset for USD, then buy to_asset
            return await self._execute_via_usd(from_asset, to_asset, amount)
            
        # Direct conversion
        if reverse:
            # We need to buy to_asset with from_asset
            result = self.kraken.create_order(
                pair=pair,
                side='buy',
                order_type='market',
                amount=amount
            )
        else:
            # We need to sell from_asset for to_asset
            result = self.kraken.create_order(
                pair=pair,
                side='sell',
                order_type='market',
                amount=amount
            )
            
        return result.get('success', False)
        
    async def _execute_via_usd(self, from_asset: str, to_asset: str, amount: float) -> bool:
        """Execute conversion via USD intermediate"""
        # Sell from_asset for USD
        sell_pair = f"{from_asset}USD"
        result1 = self.kraken.create_order(
            pair=sell_pair,
            side='sell',
            order_type='market',
            amount=amount
        )
        
        if not result1.get('success'):
            return False
            
        # Calculate USD received
        from_price = self.price_cache.get_price(from_asset)
        usd_amount = amount * from_price * 0.997  # After fees
        
        # Buy to_asset with USD
        to_price = self.price_cache.get_price(to_asset)
        to_amount = usd_amount / to_price
        
        buy_pair = f"{to_asset}USD"
        result2 = self.kraken.create_order(
            pair=buy_pair,
            side='buy',
            order_type='market',
            amount=to_amount
        )
        
        return result2.get('success', False)
        
    async def run_snowball(self, duration_seconds: int = 300):
        """
        RUN THE SNOWBALL!
        
        Continuously scan and convert for the specified duration.
        """
        await self.initialize()
        
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n🚀 SNOWBALL ROLLING! Duration: {duration_seconds}s")
        print("   Scanning for profitable conversions...")
        print("   Press Ctrl+C to stop\n")
        
        last_status = time.time()
        price_update_interval = 1.0  # Update prices every 1 second
        last_price_update = 0
        
        try:
            while self.running and time.time() < end_time:
                current_time = time.time()
                
                # Update prices periodically
                if current_time - last_price_update >= price_update_interval:
                    await self.price_cache.update_all_prices()
                    last_price_update = current_time
                    self._update_portfolio_value()
                    
                # Find best conversion
                best = await self.find_best_conversion()
                
                if best:
                    from_asset, to_asset, from_amount, to_amount, net_gain = best
                    await self.execute_conversion(from_asset, to_asset, from_amount, to_amount, net_gain)
                    
                # Status update every 5 seconds
                if current_time - last_status >= 5:
                    elapsed = int(current_time - self.start_time)
                    profit = self.portfolio.net_profit()
                    conversions = self.conversions_executed
                    
                    mode = "🔵 DRY" if self.dry_run else "🟢 LIVE"
                    print(f"❄️ {mode} | {elapsed}s | Scans: {self.scans_performed} | "
                          f"Conversions: {conversions} | "
                          f"Value: ${self.portfolio.total_value_usd:.2f} | "
                          f"Profit: ${profit:.4f}")
                    last_status = current_time
                    
                # Small delay to prevent rate limiting
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Snowball stopped by user")
            
        self.running = False
        await self._print_final_report()
        
    async def _print_final_report(self):
        """Print final snowball report"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        profit = self.portfolio.net_profit()
        
        print("\n" + "="*80)
        print("❄️🔥 SNOWBALL FINAL REPORT 🔥❄️")
        print("="*80)
        
        print(f"\n⏱️ DURATION: {elapsed:.1f} seconds")
        print(f"📊 SCANS: {self.scans_performed}")
        print(f"🎯 OPPORTUNITIES: {self.opportunities_found}")
        print(f"🔄 CONVERSIONS: {self.conversions_executed}")
        
        print(f"\n💰 STARTING VALUE: ${self.portfolio.starting_value_usd:.2f}")
        print(f"💰 ENDING VALUE: ${self.portfolio.total_value_usd:.2f}")
        print(f"📈 NET PROFIT: ${profit:.4f}")
        print(f"💸 FEES PAID: ${self.portfolio.total_fees_paid:.4f}")
        
        if self.portfolio.starting_value_usd > 0:
            roi = (profit / self.portfolio.starting_value_usd) * 100
            print(f"📊 ROI: {roi:.4f}%")
            
        if elapsed > 0:
            profit_per_hour = (profit / elapsed) * 3600
            print(f"⚡ PROFIT/HOUR: ${profit_per_hour:.2f}")
            
        if self.conversions_executed > 0:
            print(f"\n📜 CONVERSION CHAIN ({self.conversions_executed} steps):")
            for step in self.portfolio.conversion_chain[-10:]:  # Last 10 steps
                print(f"   Step {step.step_num}: {step.from_asset} → {step.to_asset} "
                      f"(+${step.net_gain_usd:.6f})")
                      
        print("\n📦 FINAL HOLDINGS:")
        for asset, amount in sorted(self.portfolio.holdings.items()):
            price = self.price_cache.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} (${value:.2f})")
                
        print("="*80)
        
        # Save conversion chain
        self._save_chain()
        
    def _save_chain(self):
        """Save the conversion chain to file"""
        chain_data = {
            'start_time': self.start_time,
            'end_time': time.time(),
            'starting_value': self.portfolio.starting_value_usd,
            'ending_value': self.portfolio.total_value_usd,
            'net_profit': self.portfolio.net_profit(),
            'total_fees': self.portfolio.total_fees_paid,
            'conversions': self.conversions_executed,
            'chain': [s.to_dict() for s in self.portfolio.conversion_chain],
            'final_holdings': self.portfolio.holdings
        }
        
        filename = f"snowball_chain_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(chain_data, f, indent=2, default=str)
        print(f"\n💾 Chain saved to {filename}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Snowball Conversion Engine')
    parser.add_argument('--live', action='store_true', help='Run in LIVE mode (real trades)')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    args = parser.parse_args()
    
    dry_run = not args.live
    
    if args.live:
        print("\n" + "🔴"*40)
        print("⚠️  WARNING: LIVE TRADING MODE ⚠️")
        print("This will execute REAL trades on Kraken!")
        print("🔴"*40)
        confirm = input("\nType 'SNOWBALL' to confirm: ")
        if confirm != 'SNOWBALL':
            print("Cancelled.")
            return
            
    engine = SnowballEngine(dry_run=dry_run)
    await engine.run_snowball(duration_seconds=args.duration)


if __name__ == '__main__':
    asyncio.run(main())
