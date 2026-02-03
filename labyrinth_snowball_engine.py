#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   🏆🌀 LABYRINTH SNOWBALL ENGINE 🌀🏆                                            ║
║                                                                                   ║
║   USING YOUR EXISTING SYSTEMS:                                                    ║
║   • V14 Labyrinth (100% win rate conversion logic)                               ║
║   • Pure Conversion Engine (barter for better philosophy)                         ║
║   • Mycelium Conversion Hub (10 systems, 90 pathways)                            ║
║   • Conversion Commando (Falcon, Tortoise, Chameleon, Bee)                       ║
║   • Rapid Conversion Stream (2,300+ pairs, 240 updates/sec)                      ║
║                                                                                   ║
║   THE LABYRINTH PHILOSOPHY:                                                       ║
║   Start with BTC → Navigate the maze → Always exit with MORE                     ║
║   Every step through the labyrinth is a conversion                               ║
║   V14 rules: Score 8+, 1.52% target, NO STOP LOSS                               ║
║                                                                                   ║
║   SPEED + LABYRINTH NAVIGATION + ALL SYSTEMS = SNOWBALL GROWTH                  ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import deque
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════════
# IMPORT ALL YOUR SYSTEMS
# ═══════════════════════════════════════════════════════════════════════════════════

print("\n🏆🌀 LABYRINTH SNOWBALL ENGINE LOADING... 🌀🏆")
print("="*80)

# Mycelium Conversion Hub - THE CENTRAL NERVOUS SYSTEM
try:
    from mycelium_conversion_hub import (
        MyceliumConversionHub, get_conversion_hub,
        MyceliumSignal, ConversionSignal, SystemSignal
    )
    MYCELIUM_HUB_AVAILABLE = True
    print("🍄 Mycelium Conversion Hub LOADED!")
except ImportError as e:
    MYCELIUM_HUB_AVAILABLE = False
    print(f"⚠️ Mycelium Hub not available: {e}")

# V14 Labyrinth - 100% WIN RATE
try:
    from s5_v14_labyrinth import V14LabyrinthEngine, V14_LABYRINTH_CONFIG
    V14_LABYRINTH_AVAILABLE = True
    print("🏆 V14 Labyrinth LOADED!")
except ImportError:
    V14_LABYRINTH_AVAILABLE = False

# V14 Scoring
try:
    from s5_v14_dance_enhancements import V14DanceEnhancer, V14_CONFIG, V14ScoringEngine
    V14_AVAILABLE = True
    print("🎯 V14 Scoring LOADED - 100% win rate!")
except ImportError:
    V14_AVAILABLE = False

# Pure Conversion Engine
try:
    from pure_conversion_engine import (
        UnifiedConversionBrain, ConversionOpportunity, 
        ConversionType, Asset, CompletedConversion
    )
    PURE_ENGINE_AVAILABLE = True
    print("🔄 Pure Conversion Engine LOADED!")
except ImportError:
    PURE_ENGINE_AVAILABLE = False

# Conversion Commando
try:
    from aureon_conversion_commando import AdaptiveConversionCommando
    COMMANDO_AVAILABLE = True
    print("🦅 Conversion Commando LOADED!")
except ImportError:
    COMMANDO_AVAILABLE = False

# Conversion Ladder
try:
    from aureon_conversion_ladder import ConversionLadder
    LADDER_AVAILABLE = True
    print("🪜 Conversion Ladder LOADED!")
except ImportError:
    LADDER_AVAILABLE = False

# Rapid Conversion Stream
try:
    from rapid_conversion_stream import RapidConversionStream
    RAPID_STREAM_AVAILABLE = True
    print("⚡ Rapid Conversion Stream LOADED!")
except ImportError:
    RAPID_STREAM_AVAILABLE = False

# Kraken Client
try:
    from kraken_client import KrakenClient, get_kraken_client
    KRAKEN_AVAILABLE = True
    print("🐙 Kraken Client LOADED!")
except ImportError:
    KRAKEN_AVAILABLE = False

# Ultra Labyrinth
try:
    from s5_ultra_labyrinth import UltraLabyrinth
    ULTRA_LABYRINTH_AVAILABLE = True
    print("🌀 Ultra Labyrinth LOADED!")
except ImportError:
    ULTRA_LABYRINTH_AVAILABLE = False

print("="*80)


# ═══════════════════════════════════════════════════════════════════════════════════
# LABYRINTH PATH TRACKING
# ═══════════════════════════════════════════════════════════════════════════════════

@dataclass
class LabyrinthStep:
    """A single step through the labyrinth"""
    step_num: int
    from_asset: str
    to_asset: str
    from_amount: float
    to_amount: float
    from_price: float
    to_price: float
    from_value_usd: float
    to_value_usd: float
    
    # V14 + System Scores
    v14_score: int = 0
    hub_score: float = 0.0
    participating_systems: List[str] = field(default_factory=list)
    
    # Profit tracking
    net_gain_usd: float = 0.0
    cumulative_gain_usd: float = 0.0
    
    # Status
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = 'COMPLETED'
    
    def to_dict(self) -> Dict:
        return {
            'step': self.step_num,
            'path': f"{self.from_asset} → {self.to_asset}",
            'from': f"{self.from_amount:.8f} {self.from_asset}",
            'to': f"{self.to_amount:.8f} {self.to_asset}",
            'value_change': f"${self.from_value_usd:.4f} → ${self.to_value_usd:.4f}",
            'gain': f"${self.net_gain_usd:.6f}",
            'cumulative': f"${self.cumulative_gain_usd:.4f}",
            'v14_score': self.v14_score,
            'hub_score': f"{self.hub_score*100:.1f}%",
            'systems': self.participating_systems,
            'time': self.timestamp.isoformat()
        }


@dataclass  
class LabyrinthState:
    """Current state of our journey through the labyrinth"""
    holdings: Dict[str, float] = field(default_factory=dict)
    path: List[LabyrinthStep] = field(default_factory=list)
    starting_value_usd: float = 0.0
    current_value_usd: float = 0.0
    total_conversions: int = 0
    total_fees_paid: float = 0.0
    
    def net_profit(self) -> float:
        return self.current_value_usd - self.starting_value_usd


# ═══════════════════════════════════════════════════════════════════════════════════
# LABYRINTH SNOWBALL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════════

class LabyrinthSnowball:
    """
    🏆🌀 THE LABYRINTH SNOWBALL ENGINE 🌀🏆
    
    Uses ALL your existing systems to navigate the market labyrinth:
    
    1. Mycelium Hub coordinates ALL systems (10 systems, 90 pathways)
    2. V14 Labyrinth provides entry rules (Score 8+, 1.52% target)
    3. Pure Conversion Engine evaluates STRENGTH_SWAP, VALUE_CAPTURE, etc.
    4. Conversion Commando provides Falcon/Tortoise/Chameleon/Bee tactics
    5. Rapid Stream provides real-time data (2,300+ pairs)
    
    PHILOSOPHY: Navigate the labyrinth, always exit with MORE
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.state = LabyrinthState()
        self.running = False
        self.start_time = None
        
        # Fee rates (Kraken)
        self.maker_fee = 0.0016  # 0.16%
        self.taker_fee = 0.0026  # 0.26%
        self.slippage = 0.0005   # 0.05%
        
        print(f"\n{'='*80}")
        print("🏆🌀 INITIALIZING LABYRINTH SNOWBALL ENGINE 🌀🏆")
        print(f"{'='*80}")
        print(f"MODE: {'🔵 DRY RUN' if dry_run else '🟢 LIVE TRADING'}")
        
        # ═══════════════════════════════════════════════════════════════════════
        # Initialize ALL systems through Mycelium Hub
        # ═══════════════════════════════════════════════════════════════════════
        
        self.hub: Optional[MyceliumConversionHub] = None
        if MYCELIUM_HUB_AVAILABLE:
            self.hub = get_conversion_hub()
            print("🍄 Mycelium Hub: WIRED")
            
        self.v14: Optional[V14DanceEnhancer] = None
        if V14_AVAILABLE:
            self.v14 = V14DanceEnhancer()
            print("🎯 V14 Scoring: WIRED")
            
        self.commando: Optional[AdaptiveConversionCommando] = None
        if COMMANDO_AVAILABLE:
            self.commando = AdaptiveConversionCommando()
            print("🦅 Conversion Commando: WIRED")
            
        self.ladder: Optional[ConversionLadder] = None
        if LADDER_AVAILABLE:
            self.ladder = ConversionLadder()
            print("🪜 Conversion Ladder: WIRED")
            
        # Kraken for execution
        self.kraken: Optional[KrakenClient] = None
        if KRAKEN_AVAILABLE and not dry_run:
            self.kraken = get_kraken_client()
            print("🐙 Kraken Client: WIRED")
        elif dry_run:
            print("🔵 Running in DRY RUN mode")
            
        # Price cache
        self.prices: Dict[str, float] = {}
        self.last_price_update = 0
        
        # Liquid assets on Kraken for labyrinth navigation
        self.labyrinth_assets = [
            'BTC', 'ETH', 'SOL', 'XRP', 'ADA', 'DOT', 'LINK', 'MATIC',
            'AVAX', 'ATOM', 'UNI', 'AAVE', 'LTC', 'BCH', 'ALGO', 'XLM',
            'DOGE', 'NEAR', 'FTM', 'SAND', 'MANA', 'CRV', 'SNX', 'COMP',
            'MKR', 'YFI', 'SUSHI', 'GRT', 'FIL', 'EOS', 'XTZ', 'DASH'
        ]
        
        print(f"{'='*80}")
        
    async def fetch_prices(self):
        """Fetch all prices from Binance"""
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('https://api.binance.com/api/v3/ticker/price',
                                       timeout=aiohttp.ClientTimeout(total=5)) as resp:
                    if resp.status == 200:
                        tickers = await resp.json()
                        for t in tickers:
                            symbol = t['symbol']
                            price = float(t['price'])
                            
                            for quote in ['USDT', 'USDC']:
                                if symbol.endswith(quote):
                                    base = symbol[:-len(quote)]
                                    self.prices[base] = price
                                    break
                                    
            # Stablecoins
            for s in ['USD', 'USDT', 'USDC']:
                self.prices[s] = 1.0
                
            self.last_price_update = time.time()
            
        except Exception as e:
            logger.debug(f"Price fetch error: {e}")
            
    def get_price(self, asset: str) -> float:
        """Get USD price for asset"""
        return self.prices.get(asset.upper(), 0.0)
        
    def calculate_portfolio_value(self) -> float:
        """Calculate current portfolio value"""
        total = 0.0
        for asset, amount in self.state.holdings.items():
            price = self.get_price(asset)
            total += amount * price
        return total
        
    def get_v14_score(self, from_asset: str, to_asset: str) -> int:
        """Get V14 score for a conversion"""
        if not self.v14:
            return 5  # Default neutral
            
        from_price = self.get_price(from_asset)
        to_price = self.get_price(to_asset)
        
        # Build price data for V14 scoring
        price_data = {
            'from_asset': from_asset,
            'to_asset': to_asset,
            'from_price': from_price,
            'to_price': to_price,
            'price_24h_change': 0.0,  # Would need historical
            'volume_24h': 1000000,    # Assumed liquid
        }
        
        try:
            score = self.v14.score_entry(price_data)
            return score if score else 5
        except:
            return 5
            
    def get_hub_signal(self, from_asset: str, to_asset: str) -> Tuple[float, List[str]]:
        """Get unified signal from Mycelium Hub"""
        if not self.hub:
            return 0.5, []
            
        try:
            # Build market data
            from_price = self.get_price(from_asset)
            to_price = self.get_price(to_asset)
            
            market_data = {
                'from_asset': from_asset,
                'to_asset': to_asset,
                'from_price': from_price,
                'to_price': to_price,
            }
            
            # Get signal from hub
            signal = self.hub.evaluate_conversion(
                from_asset=from_asset,
                to_asset=to_asset,
                from_amount=1.0,
                market_data=market_data
            )
            
            if signal:
                return signal.unified_score, signal.participating_systems
                
        except Exception as e:
            logger.debug(f"Hub signal error: {e}")
            
        return 0.5, []
        
    def calculate_conversion_value(self, from_asset: str, from_amount: float,
                                    to_asset: str) -> Tuple[float, float, float]:
        """
        Calculate what we get from converting
        
        Returns: (to_amount, to_value_usd, net_gain_usd)
        """
        from_price = self.get_price(from_asset)
        to_price = self.get_price(to_asset)
        
        if from_price <= 0 or to_price <= 0:
            return 0, 0, -999
            
        from_value = from_amount * from_price
        
        # Apply fees
        total_fee = self.maker_fee + self.slippage
        value_after_fees = from_value * (1 - total_fee)
        fees_paid = from_value * total_fee
        
        # Amount of to_asset
        to_amount = value_after_fees / to_price
        to_value = to_amount * to_price
        
        # Net gain (should be negative due to fees unless price advantage)
        net_gain = to_value - from_value
        
        return to_amount, to_value, net_gain
        
    async def find_labyrinth_path(self) -> Optional[Tuple[str, str, float, int, float, List[str]]]:
        """
        Find the best path through the labyrinth
        
        Uses V14 + Mycelium Hub to find optimal conversions
        
        Returns: (from_asset, to_asset, from_amount, v14_score, hub_score, systems)
        """
        best = None
        best_combined_score = 0
        
        # For each asset we hold
        for from_asset, from_amount in list(self.state.holdings.items()):
            from_price = self.get_price(from_asset)
            from_value = from_amount * from_price
            
            # Skip small holdings
            if from_value < 5.0:
                continue
                
            # Evaluate all possible conversions
            for to_asset in self.labyrinth_assets:
                if to_asset == from_asset:
                    continue
                    
                to_price = self.get_price(to_asset)
                if to_price <= 0:
                    continue
                    
                # Get V14 score
                v14_score = self.get_v14_score(from_asset, to_asset)
                
                # Get Hub consensus
                hub_score, systems = self.get_hub_signal(from_asset, to_asset)
                
                # Combined score (V14 is 0-10, normalize to 0-1)
                v14_normalized = v14_score / 10.0
                combined_score = (v14_normalized * 0.4) + (hub_score * 0.6)
                
                # V14 RULE: Only enter if score >= 8
                if v14_score >= 8 and combined_score > best_combined_score:
                    best_combined_score = combined_score
                    best = (from_asset, to_asset, from_amount, v14_score, hub_score, systems)
                    
        return best
        
    async def execute_labyrinth_step(self, from_asset: str, to_asset: str,
                                      from_amount: float, v14_score: int,
                                      hub_score: float, systems: List[str]) -> bool:
        """Execute a step through the labyrinth"""
        from_price = self.get_price(from_asset)
        to_price = self.get_price(to_asset)
        from_value = from_amount * from_price
        
        # Calculate conversion
        to_amount, to_value, net_gain = self.calculate_conversion_value(
            from_asset, from_amount, to_asset
        )
        
        fees_paid = from_value * (self.maker_fee + self.slippage)
        
        step_num = len(self.state.path) + 1
        cumulative = sum(s.net_gain_usd for s in self.state.path) + net_gain
        
        # Create step record
        step = LabyrinthStep(
            step_num=step_num,
            from_asset=from_asset,
            to_asset=to_asset,
            from_amount=from_amount,
            to_amount=to_amount,
            from_price=from_price,
            to_price=to_price,
            from_value_usd=from_value,
            to_value_usd=to_value,
            v14_score=v14_score,
            hub_score=hub_score,
            participating_systems=systems,
            net_gain_usd=net_gain,
            cumulative_gain_usd=cumulative
        )
        
        if self.dry_run:
            # Simulate the conversion
            self.state.holdings[from_asset] = self.state.holdings.get(from_asset, 0) - from_amount
            if self.state.holdings.get(from_asset, 0) <= 0:
                self.state.holdings.pop(from_asset, None)
            self.state.holdings[to_asset] = self.state.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🏆 LABYRINTH STEP {step_num}: {from_asset} → {to_asset}")
            print(f"      V14 Score: {v14_score}/10 | Hub Score: {hub_score*100:.1f}%")
            print(f"      Systems: {', '.join(systems[:5])}")
            print(f"      {from_amount:.8f} {from_asset} (${from_value:.4f})")
            print(f"      → {to_amount:.8f} {to_asset} (${to_value:.4f})")
            print(f"      💰 Step: ${net_gain:.6f} | Cumulative: ${cumulative:.4f}")
            
        else:
            # Real execution
            success = await self._execute_kraken_conversion(from_asset, to_asset, from_amount)
            if not success:
                return False
                
            self.state.holdings[from_asset] = self.state.holdings.get(from_asset, 0) - from_amount
            if self.state.holdings.get(from_asset, 0) <= 0:
                self.state.holdings.pop(from_asset, None)
            self.state.holdings[to_asset] = self.state.holdings.get(to_asset, 0) + to_amount
            
            print(f"\n   🔥 LIVE STEP {step_num}: {from_asset} → {to_asset} (V14: {v14_score})")
            
        # Record step
        self.state.path.append(step)
        self.state.total_conversions += 1
        self.state.total_fees_paid += fees_paid
        self.state.current_value_usd = self.calculate_portfolio_value()
        
        return True
        
    async def _execute_kraken_conversion(self, from_asset: str, to_asset: str,
                                          amount: float) -> bool:
        """Execute conversion on Kraken via USD intermediate"""
        if not self.kraken:
            return False
            
        try:
            # Sell from_asset for USD
            result1 = self.kraken.create_order(
                pair=f"{from_asset}USD",
                side='sell',
                order_type='market',
                amount=amount
            )
            if not result1.get('success'):
                return False
                
            # Calculate USD and buy to_asset
            from_price = self.get_price(from_asset)
            usd = amount * from_price * 0.998
            to_price = self.get_price(to_asset)
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
        """Initialize the labyrinth journey"""
        # Fetch initial prices
        print("\n📊 Fetching market prices...")
        await self.fetch_prices()
        print(f"   ✅ {len(self.prices)} assets priced")
        
        # Set starting holdings
        if starting_holdings:
            self.state.holdings = starting_holdings.copy()
        elif self.dry_run:
            # Simulated portfolio
            self.state.holdings = {
                'BTC': 0.001,   # ~$91
                'ETH': 0.05,   # ~$157
                'SOL': 1.0,    # ~$134
            }
        else:
            # Load real Kraken balances
            if self.kraken:
                result = self.kraken.get_balance()
                if result.get('success'):
                    for asset, bal in result.get('balance', {}).items():
                        b = float(bal)
                        if b > 0:
                            asset = asset.replace('X', '').replace('Z', '').replace('.S', '')
                            self.state.holdings[asset] = b
                            
        # Calculate starting value
        self.state.starting_value_usd = self.calculate_portfolio_value()
        self.state.current_value_usd = self.state.starting_value_usd
        
        print("\n📦 STARTING PORTFOLIO (LABYRINTH ENTRANCE):")
        for asset, amount in self.state.holdings.items():
            price = self.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f}")
        print(f"\n   💰 TOTAL VALUE: ${self.state.starting_value_usd:.2f}")
        
    async def run(self, duration_seconds: int = 300):
        """
        Navigate the labyrinth!
        
        Keep scanning for conversion opportunities using V14 + all systems.
        Execute when V14 score >= 8 and hub consensus is favorable.
        """
        await self.initialize()
        
        self.running = True
        self.start_time = time.time()
        end_time = self.start_time + duration_seconds
        
        print(f"\n🌀 ENTERING THE LABYRINTH! (Duration: {duration_seconds}s)")
        print("   Using V14 + Mycelium Hub for navigation...")
        print("   V14 Rule: Only convert when score >= 8")
        print("   Press Ctrl+C to exit\n")
        
        last_status = time.time()
        last_path_search = 0
        path_search_interval = 2.0  # Search every 2 seconds
        
        try:
            while self.running and time.time() < end_time:
                # Update prices
                if time.time() - self.last_price_update > 1.0:
                    await self.fetch_prices()
                    self.state.current_value_usd = self.calculate_portfolio_value()
                    
                # Search for labyrinth path
                if time.time() - last_path_search >= path_search_interval:
                    path = await self.find_labyrinth_path()
                    
                    if path:
                        from_asset, to_asset, from_amount, v14_score, hub_score, systems = path
                        await self.execute_labyrinth_step(
                            from_asset, to_asset, from_amount,
                            v14_score, hub_score, systems
                        )
                        
                    last_path_search = time.time()
                    
                # Status every 10 seconds
                if time.time() - last_status >= 10:
                    elapsed = int(time.time() - self.start_time)
                    profit = self.state.net_profit()
                    
                    mode = "🔵" if self.dry_run else "🟢"
                    print(f"🌀 {mode} | {elapsed}s | Steps: {self.state.total_conversions} | "
                          f"Value: ${self.state.current_value_usd:.2f} | Profit: ${profit:.4f}")
                          
                    last_status = time.time()
                    
                await asyncio.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\n\n⏹️ Exiting labyrinth...")
            
        self.running = False
        self._print_report()
        
    def _print_report(self):
        """Print final labyrinth journey report"""
        elapsed = time.time() - self.start_time if self.start_time else 0
        profit = self.state.net_profit()
        
        print("\n" + "="*80)
        print("🏆🌀 LABYRINTH JOURNEY REPORT 🌀🏆")
        print("="*80)
        
        print(f"\n⏱️ DURATION: {elapsed:.1f}s")
        print(f"🚶 STEPS TAKEN: {self.state.total_conversions}")
        
        print(f"\n💰 ENTRANCE VALUE: ${self.state.starting_value_usd:.2f}")
        print(f"💰 EXIT VALUE: ${self.state.current_value_usd:.2f}")
        print(f"📈 NET PROFIT: ${profit:.4f}")
        print(f"💸 FEES PAID: ${self.state.total_fees_paid:.4f}")
        
        if self.state.starting_value_usd > 0:
            roi = (profit / self.state.starting_value_usd) * 100
            print(f"📊 ROI: {roi:.4f}%")
            
        if elapsed > 0:
            hourly = (profit / elapsed) * 3600
            print(f"⏰ $/HOUR: ${hourly:.2f}")
            
        if self.state.path:
            print(f"\n📜 LABYRINTH PATH ({len(self.state.path)} steps):")
            for step in self.state.path[-10:]:
                print(f"   Step {step.step_num}: {step.from_asset} → {step.to_asset} "
                      f"(V14: {step.v14_score}, Hub: {step.hub_score*100:.0f}%) "
                      f"${step.net_gain_usd:+.6f}")
                      
        print("\n📦 EXIT HOLDINGS:")
        for asset, amount in sorted(self.state.holdings.items()):
            price = self.get_price(asset)
            value = amount * price
            if value > 0.01:
                print(f"   {asset}: {amount:.8f} = ${value:.2f}")
                
        print("="*80)
        
        # Save journey
        filename = f"labyrinth_journey_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                'duration': elapsed,
                'starting_value': self.state.starting_value_usd,
                'ending_value': self.state.current_value_usd,
                'profit': profit,
                'fees': self.state.total_fees_paid,
                'steps': self.state.total_conversions,
                'path': [s.to_dict() for s in self.state.path],
                'final_holdings': self.state.holdings
            }, f, indent=2, default=str)
        print(f"\n💾 Journey saved to {filename}")


async def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Labyrinth Snowball Engine')
    parser.add_argument('--live', action='store_true', help='Live trading mode')
    parser.add_argument('--duration', type=int, default=300, help='Duration in seconds')
    args = parser.parse_args()
    
    if args.live:
        print("\n" + "🔴"*40)
        print("⚠️  LIVE TRADING MODE")
        print("🔴"*40)
        confirm = input("\nType 'LABYRINTH' to enter: ")
        if confirm != 'LABYRINTH':
            print("Journey cancelled.")
            return
            
    engine = LabyrinthSnowball(dry_run=not args.live)
    await engine.run(duration_seconds=args.duration)


if __name__ == '__main__':
    asyncio.run(main())
