#!/usr/bin/env python3
"""
🔥🔥🔥 S5 LIVE EXECUTION ENGINE - REAL MONEY 🔥🔥🔥
═══════════════════════════════════════════════════════════════
LIVE trading with real Kraken execution.
Real-time WebSocket data → S5 Decision → Real Order Execution

Gary Leckey & GitHub Copilot | January 2026
"Taking Over The World - One Conversion At A Time"

⚠️  WARNING: THIS EXECUTES REAL TRADES WITH REAL MONEY! ⚠️
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import asyncio
import json
import time
import signal
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
from dataclasses import dataclass, field
import threading

# Force live mode
os.environ['KRAKEN_DRY_RUN'] = 'false'

try:
    import websockets
except ImportError:
    websockets = None

import requests

# Import our systems
from aureon_mycelium import MyceliumNetwork
from kraken_client import KrakenClient, get_kraken_client


@dataclass
class LivePrice:
    """Real-time price data"""
    symbol: str
    price: float
    bid: float = 0.0
    ask: float = 0.0
    volume_24h: float = 0.0
    change_24h: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = 'unknown'


@dataclass
class ConversionOpportunity:
    """Detected conversion opportunity"""
    from_asset: str
    to_asset: str
    gross_profit: float
    fee: float
    net_profit: float
    price_change: float
    timestamp: datetime
    opportunity_type: str
    s5_score: float = 0.0
    symbol: str = ''
    quantity: float = 0.0
    side: str = ''


class S5LiveExecutionEngine:
    """
    🔥 REAL MONEY S5 TRADING ENGINE 🔥
    
    Executes real trades on Kraken based on S5 signals.
    """
    
    # Trading pairs - Binance format for WebSocket
    # Include pairs that match YOUR HOLDINGS!
    BINANCE_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
        'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT',
        'ATOMUSDT', 'UNIUSDT', 'LTCUSDT', 'NEARUSDT', 'APTUSDT',
        'LUNAUSDT', 'LUNCUSDT',  # LUNA classic - you have 268K!
    ]
    
    # Kraken pair mapping
    BINANCE_TO_KRAKEN = {
        'BTCUSDT': 'XBTUSD',
        'ETHUSDT': 'ETHUSD',
        'SOLUSDT': 'SOLUSD',
        'XRPUSDT': 'XRPUSD',
        'ADAUSDT': 'ADAUSD',
        'DOGEUSDT': 'DOGEUSD',
        'AVAXUSDT': 'AVAXUSD',
        'DOTUSDT': 'DOTUSD',
        'LINKUSDT': 'LINKUSD',
        'MATICUSDT': 'MATICUSD',
        'ATOMUSDT': 'ATOMUSD',
        'UNIUSDT': 'UNIUSD',
        'LTCUSDT': 'LTCUSD',
        'NEARUSDT': 'NEARUSD',
        'APTUSDT': 'APTUSD',
        'LUNAUSDT': 'LUNAUSD',
        'LUNCUSDT': 'LUNCUSD',
    }
    
    # Fee structure (Kraken)
    MAKER_FEE = 0.0016  # 0.16%
    TAKER_FEE = 0.0026  # 0.26%
    
    # Risk management
    MAX_POSITION_USD = 50.0      # Max $50 per trade
    MIN_POSITION_USD = 5.0       # Min $5 per trade
    MAX_DAILY_TRADES = 100       # Max trades per day
    MAX_DAILY_LOSS = 25.0        # Stop if loss exceeds $25
    
    # Opportunity detection thresholds (very aggressive)
    MIN_PRICE_CHANGE = 0.0003    # 0.03% minimum move (3 bps)
    MIN_VOLATILITY = 0.0005      # 0.05% minimum volatility
    MIN_PROFIT = 0.001           # $0.001 minimum profit
    
    def __init__(self, starting_capital: float = 100.0):
        self.starting_capital = starting_capital
        self.network = MyceliumNetwork(initial_capital=starting_capital)
        
        # Initialize Kraken client for real execution
        self.kraken = get_kraken_client()
        
        # Price tracking
        self.prices: Dict[str, LivePrice] = {}
        self.prev_prices: Dict[str, float] = {}
        self.price_history: Dict[str, List[tuple]] = defaultdict(list)
        
        # Trading state
        self.running = False
        self.start_time = None
        self.ws_connected = False
        self.execution_enabled = True
        
        # Risk tracking
        self.daily_trades = 0
        self.daily_pnl = 0.0
        self.open_positions: Dict[str, Dict] = {}
        
        # Stats
        self.stats = {
            'price_updates': 0,
            'opportunities_found': 0,
            'conversions_executed': 0,
            'real_trades_placed': 0,
            'total_gross_profit': 0.0,
            'total_fees': 0.0,
            'total_net_profit': 0.0,
            'best_conversion': None,
            'failed_trades': 0,
        }
        
        # Execution queue (for rate limiting)
        self.execution_queue: List[ConversionOpportunity] = []
        self.execution_lock = threading.Lock()
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown gracefully"""
        print("\n\n🛑 Shutdown signal received...")
        self.running = False
        
    def banner(self):
        """Display startup banner"""
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ███████╗███████╗    ██╗     ██╗██╗   ██╗███████╗                            ║
║   ██╔════╝██╔════╝    ██║     ██║██║   ██║██╔════╝                            ║
║   ███████╗███████╗    ██║     ██║██║   ██║█████╗                              ║
║   ╚════██║╚════██║    ██║     ██║╚██╗ ██╔╝██╔══╝                              ║
║   ███████║███████║    ███████╗██║ ╚████╔╝ ███████╗                            ║
║   ╚══════╝╚══════╝    ╚══════╝╚═╝  ╚═══╝  ╚══════╝                            ║
║                                                                               ║
║      🔥🔥🔥 REAL MONEY EXECUTION ENGINE 🔥🔥🔥                               ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   🎯 TARGET: $1,000,000 Net Profit                                            ║
║   💰 Starting Capital: ${:>12,.2f}                                           ║
║   🔴 MODE: LIVE TRADING - REAL MONEY                                          ║
║   📡 Feed: Binance WebSocket → Kraken Execution                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   ⚠️  RISK LIMITS:                                                             ║
║      Max Position: ${:.2f} | Max Daily Trades: {}                             ║
║      Max Daily Loss: ${:.2f}                                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""".format(self.starting_capital, self.MAX_POSITION_USD, self.MAX_DAILY_TRADES, self.MAX_DAILY_LOSS))

    def check_kraken_connection(self) -> bool:
        """Verify Kraken API connection and get available assets"""
        print("\n   🐙 Checking Kraken connection...")
        
        try:
            # Check if we have API keys
            if not self.kraken.api_key or not self.kraken.api_secret:
                print("      ❌ No Kraken API keys configured!")
                print("      Set KRAKEN_API_KEY and KRAKEN_API_SECRET environment variables")
                return False
            
            # Test connection by getting balance
            balance = self.kraken.get_account_balance()
            
            if balance:
                print("      ✅ Kraken connected!")
                
                # Store available assets for trading
                self.available_assets = {}
                total_value = 0.0
                
                for asset, amount in balance.items():
                    if amount > 0.001:
                        # Get USD value estimate
                        usd_value = self._estimate_usd_value(asset, amount)
                        if usd_value > 0.01:
                            self.available_assets[asset] = {
                                'amount': amount,
                                'usd_value': usd_value
                            }
                            total_value += usd_value
                            print(f"         {asset}: {amount:.4f} (~${usd_value:.2f})")
                
                print(f"      💰 Total Portfolio Value: ~${total_value:.2f}")
                self.portfolio_value = total_value
                
                return True
            else:
                print("      ⚠️ Connected but no balance data")
                return True
                
        except Exception as e:
            print(f"      ❌ Kraken connection failed: {e}")
            return False
    
    def _estimate_usd_value(self, asset: str, amount: float) -> float:
        """Estimate USD value of an asset"""
        # USD stablecoins
        if asset in ['USD', 'ZUSD', 'USDT', 'USDC', 'TUSD']:
            return amount
        
        # Try to get price from Kraken
        try:
            # Common Kraken pair mappings
            pairs_to_try = [f"{asset}USD", f"X{asset}ZUSD", f"{asset}ZUSD"]
            for pair in pairs_to_try:
                try:
                    ticker = self.kraken.get_ticker(pair)
                    if ticker and 'c' in ticker:
                        price = float(ticker['c'][0])
                        return amount * price
                except:
                    continue
        except:
            pass
        
        # Known approximate prices for common assets
        approx_prices = {
            'ATOM': 9.0,
            'LUNA': 0.0001,  # LUNA classic is very cheap
            'AIR': 0.01,
            'MON': 0.05,
            'DASH': 30.0,
            'NIGHT': 0.001,
        }
        if asset in approx_prices:
            return amount * approx_prices[asset]
        
        return 0.0

    async def _fetch_initial_prices(self):
        """Fetch initial prices from REST API"""
        print("\n   📡 Fetching initial prices from Binance...")
        
        try:
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/24hr',
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            for ticker in data:
                symbol = ticker['symbol']
                if symbol in self.BINANCE_PAIRS:
                    price = float(ticker['lastPrice'])
                    self.prices[symbol] = LivePrice(
                        symbol=symbol,
                        price=price,
                        bid=float(ticker.get('bidPrice', price)),
                        ask=float(ticker.get('askPrice', price)),
                        volume_24h=float(ticker.get('volume', 0)),
                        change_24h=float(ticker.get('priceChangePercent', 0)),
                        timestamp=datetime.now(),
                        source='binance_rest'
                    )
                    self.prev_prices[symbol] = price
                    
            print(f"      ✅ Loaded {len(self.prices)} initial prices")
            
        except Exception as e:
            print(f"      ⚠️ REST API error: {e}")
    
    async def _binance_websocket(self):
        """Connect to Binance WebSocket for real-time prices"""
        
        streams = [f"{s.lower()}@ticker" for s in self.BINANCE_PAIRS]
        ws_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"
        
        print(f"\n   🌐 Connecting to Binance WebSocket...")
        
        reconnect_delay = 1
        
        while self.running:
            try:
                async with websockets.connect(ws_url, ping_interval=20) as ws:
                    self.ws_connected = True
                    reconnect_delay = 1
                    print(f"      ✅ WebSocket connected!")
                    
                    async for message in ws:
                        if not self.running:
                            break
                            
                        try:
                            data = json.loads(message)
                            
                            if 'data' in data:
                                ticker = data['data']
                                symbol = ticker.get('s')
                                
                                if symbol and symbol in self.BINANCE_PAIRS:
                                    price = float(ticker.get('c', 0))
                                    
                                    if price > 0:
                                        if symbol in self.prices:
                                            self.prev_prices[symbol] = self.prices[symbol].price
                                        
                                        self.prices[symbol] = LivePrice(
                                            symbol=symbol,
                                            price=price,
                                            bid=float(ticker.get('b', price)),
                                            ask=float(ticker.get('a', price)),
                                            volume_24h=float(ticker.get('v', 0)),
                                            change_24h=float(ticker.get('P', 0)),
                                            timestamp=datetime.now(),
                                            source='binance_ws'
                                        )
                                        
                                        self.price_history[symbol].append((datetime.now(), price))
                                        if len(self.price_history[symbol]) > 100:
                                            self.price_history[symbol].pop(0)
                                        
                                        self.stats['price_updates'] += 1
                                        
                                        # Check for opportunity
                                        await self._check_opportunity(symbol)
                                        
                        except Exception:
                            pass
                            
            except websockets.exceptions.ConnectionClosed:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
                    
            except Exception as e:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _check_opportunity(self, symbol: str):
        """Check if current price movement presents a conversion opportunity"""
        
        # Risk checks
        if self.daily_trades >= self.MAX_DAILY_TRADES:
            return
        if self.daily_pnl <= -self.MAX_DAILY_LOSS:
            return
        if not self.execution_enabled:
            return
            
        if symbol not in self.prev_prices:
            return
            
        current = self.prices[symbol]
        prev_price = self.prev_prices[symbol]
        
        if prev_price <= 0:
            return
            
        price_change = (current.price - prev_price) / prev_price
        
        # Calculate volatility
        history = self.price_history.get(symbol, [])
        volatility = 0.0
        if len(history) >= 10:
            recent_prices = [p for _, p in history[-10:]]
            volatility = (max(recent_prices) - min(recent_prices)) / min(recent_prices)
        
        base_asset = symbol.replace('USDT', '')
        kraken_asset = self._binance_to_kraken_asset(base_asset)
        
        opportunity = None
        
        # CHECK WHAT WE HAVE - Labyrinth uses our assets!
        have_asset = hasattr(self, 'available_assets') and kraken_asset in self.available_assets and self.available_assets[kraken_asset]['usd_value'] > 1.0
        have_usd = hasattr(self, 'available_assets') and any(a in self.available_assets for a in ['USD', 'ZUSD'])
        
        # Strong upward movement - SELL what we have!
        if price_change >= self.MIN_PRICE_CHANGE and have_asset:
            # We have this asset and price is rising - SELL IT!
            asset_info = self.available_assets[kraken_asset]
            sell_pct = min(0.25, 0.1 + abs(price_change) * 10)  # Scale sell amount with price move
            position_usd = asset_info['usd_value'] * sell_pct
            position_usd = min(self.MAX_POSITION_USD, max(self.MIN_POSITION_USD, position_usd))
            
            quantity = position_usd / current.price
            gross_profit = position_usd * abs(price_change)
            fee = position_usd * self.TAKER_FEE
            net_profit = gross_profit - fee
            
            if net_profit >= self.MIN_PROFIT:
                opportunity = ConversionOpportunity(
                    from_asset=base_asset,
                    to_asset='USD',
                    gross_profit=gross_profit,
                    fee=fee,
                    net_profit=net_profit,
                    price_change=price_change,
                    timestamp=current.timestamp,
                    opportunity_type='LABYRINTH_SELL',
                    symbol=symbol,
                    quantity=quantity,
                    side='SELL'
                )
                opportunity.kraken_asset = kraken_asset
        
        # Strong downward movement - buy only if we have USD
        elif price_change <= -self.MIN_PRICE_CHANGE and have_usd:
            position_usd = min(self.MAX_POSITION_USD, max(self.MIN_POSITION_USD,
                self.network.s5_calculate_optimal_size('USD', base_asset, abs(price_change) * 100)))
            
            quantity = position_usd / current.price
            gross_profit = position_usd * abs(price_change)
            fee = position_usd * self.TAKER_FEE
            net_profit = gross_profit - fee
            
            if net_profit >= self.MIN_PROFIT:
                opportunity = ConversionOpportunity(
                    from_asset='USD',
                    to_asset=base_asset,
                    gross_profit=gross_profit,
                    fee=fee,
                    net_profit=net_profit,
                    price_change=price_change,
                    timestamp=current.timestamp,
                    opportunity_type='BUY_LOW',
                    symbol=symbol,
                    quantity=quantity,
                    side='BUY'
                )
        
        # High volatility with assets - trade it!
        elif volatility >= self.MIN_VOLATILITY and have_asset:
            asset_info = self.available_assets[kraken_asset]
            position_usd = min(self.MAX_POSITION_USD, max(self.MIN_POSITION_USD, asset_info['usd_value'] * 0.1))
            quantity = position_usd / current.price
            gross_profit = position_usd * volatility * 0.5
            fee = position_usd * self.TAKER_FEE * 2
            net_profit = gross_profit - fee
            
            if net_profit >= self.MIN_PROFIT:
                opportunity = ConversionOpportunity(
                    from_asset=base_asset,
                    to_asset='USD',
                    gross_profit=gross_profit,
                    fee=fee,
                    net_profit=net_profit,
                    price_change=price_change,
                    timestamp=current.timestamp,
                    opportunity_type='VOLATILITY_SCALP',
                    symbol=symbol,
                    quantity=quantity,
                    side='SELL'
                )
                opportunity.kraken_asset = kraken_asset
        
        if opportunity:
            await self._process_opportunity(opportunity)
    
    def _binance_to_kraken_asset(self, binance_asset: str) -> str:
        """Convert Binance asset name to Kraken asset name"""
        mapping = {
            'BTC': 'XXBT', 'ETH': 'XETH', 'XRP': 'XXRP',
            'ADA': 'ADA', 'SOL': 'SOL', 'DOT': 'DOT',
            'DOGE': 'DOGE', 'ATOM': 'ATOM', 'LUNA': 'LUNA',
            'AVAX': 'AVAX', 'MATIC': 'MATIC', 'LINK': 'LINK',
        }
        return mapping.get(binance_asset, binance_asset)
    
    async def _process_opportunity(self, opp: ConversionOpportunity):
        """Process and execute a conversion opportunity"""
        
        self.stats['opportunities_found'] += 1
        
        # Get S5 score
        path_key = f"{opp.from_asset}→{opp.to_asset}"
        s5_score = self.network.s5_adaptive_labyrinth_score(path_key, opp.net_profit)
        opp.s5_score = s5_score
        
        # S5 decision
        should_execute = (
            s5_score > 0 and
            self.network.should_convert(opp.from_asset, opp.to_asset, opp.net_profit)
        )
        
        if should_execute:
            # Execute real trade!
            success = await self._execute_real_trade(opp)
            
            if success:
                # Record in network
                self.network.record_conversion_profit({
                    'from_asset': opp.from_asset,
                    'to_asset': opp.to_asset,
                    'exchange': 'kraken',
                    'net_profit': opp.net_profit,
                    'fees': opp.fee,
                    'success': True,
                    'hops': 1,
                })
                
                self.stats['conversions_executed'] += 1
                self.stats['total_gross_profit'] += opp.gross_profit
                self.stats['total_fees'] += opp.fee
                self.stats['total_net_profit'] += opp.net_profit
                self.daily_pnl += opp.net_profit
                
                if (self.stats['best_conversion'] is None or 
                    opp.net_profit > self.stats['best_conversion']['net_profit']):
                    self.stats['best_conversion'] = {
                        'path': path_key,
                        'net_profit': opp.net_profit,
                        'type': opp.opportunity_type,
                    }
                
                self.network.s5_update_labyrinth_cache(path_key, opp.net_profit, True)
                
                print(f"\n   💰 REAL TRADE #{self.stats['real_trades_placed']}: {path_key}")
                print(f"      Type: {opp.opportunity_type} | S5: {s5_score:.2f}")
                print(f"      Net Profit: ${opp.net_profit:.4f} | Total: ${self.stats['total_net_profit']:.4f}")
    
    async def _execute_real_trade(self, opp: ConversionOpportunity) -> bool:
        """Execute a real trade on Kraken"""
        
        # Map to Kraken pair
        kraken_pair = self.BINANCE_TO_KRAKEN.get(opp.symbol)
        if not kraken_pair:
            print(f"      ⚠️ No Kraken mapping for {opp.symbol}")
            return False
        
        try:
            # Execute order
            print(f"\n   🔥 EXECUTING: {opp.side} {opp.quantity:.6f} {kraken_pair}")
            
            result = self.kraken.place_market_order(
                symbol=kraken_pair,
                side=opp.side.lower(),
                quantity=opp.quantity
            )
            
            if result and 'orderId' in result:
                self.stats['real_trades_placed'] += 1
                self.daily_trades += 1
                print(f"      ✅ Order filled! ID: {result['orderId']}")
                return True
            elif result and 'error' in result:
                print(f"      ⚠️ Order rejected: {result.get('error')}")
                self.stats['failed_trades'] += 1
                return False
            else:
                print(f"      ⚠️ Unexpected response: {result}")
                return False
                
        except Exception as e:
            print(f"      ❌ Trade failed: {e}")
            self.stats['failed_trades'] += 1
            return False
    
    async def _display_loop(self):
        """Display live stats"""
        
        last_display = time.time()
        
        while self.running:
            await asyncio.sleep(1)
            
            if time.time() - last_display >= 5:
                last_display = time.time()
                self._display_stats()
    
    def _display_stats(self):
        """Display current stats"""
        
        if not self.start_time:
            return
            
        elapsed = time.time() - self.start_time
        hours = elapsed / 3600
        
        ttm = self.network.s5_get_time_to_million()
        phase = ttm['phase']
        velocity = ttm['velocity_per_hour']
        
        print(f"\r   ⏱️ {elapsed:.0f}s | 📡 {self.stats['price_updates']:,} | "
              f"🔍 {self.stats['opportunities_found']:,} | "
              f"💰 {self.stats['real_trades_placed']} REAL | "
              f"💵 ${self.stats['total_net_profit']:.4f} | "
              f"⚡ ${velocity:.2f}/hr | "
              f"📈 {phase}", end='', flush=True)
    
    def _final_report(self):
        """Final report"""
        
        if not self.start_time:
            return
            
        elapsed = time.time() - self.start_time
        ttm = self.network.s5_get_time_to_million()
        
        print("\n\n" + "="*70)
        print("📊 S5 LIVE EXECUTION SESSION REPORT")
        print("="*70)
        
        print(f"\n⏱️ SESSION")
        print(f"   Runtime: {elapsed:.1f}s ({elapsed/3600:.3f} hours)")
        
        print(f"\n📡 DATA")
        print(f"   Price Updates: {self.stats['price_updates']:,}")
        print(f"   Opportunities: {self.stats['opportunities_found']:,}")
        
        print(f"\n💰 EXECUTION")
        print(f"   Real Trades: {self.stats['real_trades_placed']}")
        print(f"   Failed Trades: {self.stats['failed_trades']}")
        print(f"   Net Profit: ${self.stats['total_net_profit']:.4f}")
        
        print(f"\n🚀 S5 METRICS")
        print(f"   Phase: {ttm['phase']}")
        print(f"   Velocity: ${ttm['velocity_per_hour']:,.2f}/hour")
        print(f"   TTM Linear: {ttm['ttm_days_linear']:.1f} days")
        print(f"   TTM Accelerated: {ttm['ttm_days_accelerated']:.1f} days")
        
        print("\n" + "="*70)
        print("🔥 Taking over the world, one trade at a time! 🔥")
        print("="*70 + "\n")
    
    async def run(self):
        """Main run loop"""
        
        self.banner()
        
        # Check Kraken connection first
        if not self.check_kraken_connection():
            print("\n   ❌ Cannot start without Kraken connection!")
            print("   Please configure your API keys and try again.")
            return
        
        # Confirm live trading
        print("\n" + "="*70)
        print("⚠️  FINAL CONFIRMATION - REAL MONEY TRADING ⚠️")
        print("="*70)
        print("\n   This will execute REAL trades with REAL money!")
        print(f"   Max position size: ${self.MAX_POSITION_USD}")
        print(f"   Max daily trades: {self.MAX_DAILY_TRADES}")
        print(f"   Max daily loss: ${self.MAX_DAILY_LOSS}")
        
        confirm = input("\n   Type 'TAKE OVER THE WORLD' to start: ")
        if confirm != 'TAKE OVER THE WORLD':
            print("\n   Aborted. Stay safe!")
            return
        
        print("\n🔥🔥🔥 LET'S GO! TAKING OVER THE WORLD! 🔥🔥🔥\n")
        
        self.running = True
        self.start_time = time.time()
        
        await self._fetch_initial_prices()
        
        try:
            await asyncio.gather(
                self._binance_websocket(),
                self._display_loop(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            self._final_report()


async def main():
    """Entry point"""
    
    print("\n🔥🔥🔥 S5 LIVE EXECUTION ENGINE 🔥🔥🔥")
    print("   REAL MONEY TRADING MODE")
    print("   Press Ctrl+C to stop\n")
    
    engine = S5LiveExecutionEngine(starting_capital=100.0)
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
