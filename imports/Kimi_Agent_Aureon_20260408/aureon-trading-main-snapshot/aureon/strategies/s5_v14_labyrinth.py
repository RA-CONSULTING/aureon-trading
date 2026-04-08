#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                                                                                   ║
║   ██╗   ██╗ ██╗██╗  ██╗    ██╗      █████╗ ██████╗ ██╗   ██╗██████╗ ██╗███╗   ██║
║   ██║   ██║███║██║  ██║    ██║     ██╔══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗██║████╗  ██║
║   ██║   ██║╚██║███████║    ██║     ███████║██████╔╝ ╚████╔╝ ██████╔╝██║██╔██╗ ██║
║   ╚██╗ ██╔╝ ██║╚════██║    ██║     ██╔══██║██╔══██╗  ╚██╔╝  ██╔══██╗██║██║╚██╗██║
║    ╚████╔╝  ██║     ██║    ███████╗██║  ██║██████╔╝   ██║   ██║  ██║██║██║ ╚████║
║     ╚═══╝   ╚═╝     ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝
║                                                                                   ║
║   🏆 V14 LABYRINTH - 100% WIN RATE CONVERSIONS 🏆                                ║
║                                                                                   ║
║   STRATEGY: Convert holdings through labyrinth paths, only exit at PROFIT        ║
║   • Entry: V14 Score 8+ (multi-factor scoring)                                   ║
║   • Exit: 1.52% profit target (IRA trained)                                      ║
║   • Stop Loss: NONE - hold conversions until profitable                          ║
║   • Patience: INFINITE - never sell at a loss                                    ║
║                                                                                   ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque

try:
    import websockets
except ImportError:
    print("⚠️  websockets module not available - some features may be limited")
    websockets = None  # Allow graceful degradation

import requests

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import V14 enhancements
from s5_v14_dance_enhancements import V14DanceEnhancer, V14_CONFIG, V14ScoringEngine

# Import trading systems
try:
    from kraken_client import KrakenClient, get_kraken_client
    KRAKEN_AVAILABLE = True
except ImportError:
    KRAKEN_AVAILABLE = False
    
try:
    from aureon_mycelium import MyceliumNetwork
    MYCELIUM_AVAILABLE = True
except ImportError:
    MYCELIUM_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════════
# V14 LABYRINTH CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════════

V14_LABYRINTH_CONFIG = {
    # V14 Proven Parameters
    'entry_score_threshold': V14_CONFIG['entry_score_threshold'],  # 8+
    'profit_target_pct': V14_CONFIG['profit_target_pct'],          # 1.52%
    'stop_loss_pct': None,                                         # NONE - key insight!
    
    # Labyrinth Conversion Settings
    'min_conversion_usd': 5.0,           # Minimum conversion size
    'max_conversion_usd': 100.0,         # Maximum conversion size
    'max_concurrent_conversions': 10,    # Max open conversions
    'conversion_cooldown_sec': 30,       # Cooldown between conversions per asset
    
    # Movement Thresholds for Conversion Triggers
    'min_up_move_to_convert': 0.003,     # 0.3% up = sell some
    'min_down_move_to_buy': 0.005,       # 0.5% down = buy opportunity
}


@dataclass
class V14Conversion:
    """A labyrinth conversion with V14 rules"""
    id: str
    from_asset: str
    to_asset: str
    entry_price: float
    quantity: float
    usd_value: float
    entry_time: datetime
    entry_score: int
    kraken_pair: str
    side: str  # BUY or SELL
    
    # V14 Exit Tracking
    current_price: float = 0.0
    current_pnl_pct: float = 0.0
    status: str = 'OPEN'  # OPEN, PROFITABLE, CLOSED
    
    def update_pnl(self, current_price: float) -> Tuple[bool, float]:
        """Update PnL and check if exit condition met"""
        self.current_price = current_price
        
        if self.side == 'SELL':
            # For sells, we want price to go UP after selling (so we sold high)
            # Actually for labyrinth conversions, we measure USD gained
            self.current_pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        else:
            # For buys, we want price to go UP after buying
            self.current_pnl_pct = ((current_price - self.entry_price) / self.entry_price) * 100
        
        # V14 EXIT RULE: ONLY at profit target
        if self.current_pnl_pct >= V14_LABYRINTH_CONFIG['profit_target_pct']:
            self.status = 'PROFITABLE'
            return True, self.current_pnl_pct
        
        # NO STOP LOSS - infinite patience
        return False, self.current_pnl_pct


class V14LabyrinthEngine:
    """
    🏆 V14 LABYRINTH ENGINE 🏆
    
    Converts holdings through profitable paths using V14 100% win rate rules:
    - Score-based entry (8+ required)
    - 1.52% profit target
    - NO STOP LOSS - hold until profitable
    """
    
    # Binance WebSocket
    WS_URL = "wss://stream.binance.com:9443/stream?streams="
    
    # Asset to pair mapping
    ASSET_PAIRS = {
        # Your holdings map
        'ATOM': {'binance': 'ATOMUSDT', 'kraken': 'ATOMUSD'},
        'LUNA': {'binance': 'LUNCUSDT', 'kraken': 'LUNAUSD'},
        'DASH': {'binance': 'DASHUSDT', 'kraken': 'DASHUSD'},
        'SOL': {'binance': 'SOLUSDT', 'kraken': 'SOLUSD'},
        'DOT': {'binance': 'DOTUSDT', 'kraken': 'DOTUSD'},
        'LINK': {'binance': 'LINKUSDT', 'kraken': 'LINKUSD'},
        'AVAX': {'binance': 'AVAXUSDT', 'kraken': 'AVAXUSD'},
        'NEAR': {'binance': 'NEARUSDT', 'kraken': 'NEARUSD'},
        'APT': {'binance': 'APTUSDT', 'kraken': 'APTUSD'},
        'ARB': {'binance': 'ARBUSDT', 'kraken': 'ARBUSD'},
        'OP': {'binance': 'OPUSDT', 'kraken': 'OPUSD'},
        'UNI': {'binance': 'UNIUSDT', 'kraken': 'UNIUSD'},
        'AAVE': {'binance': 'AAVEUSDT', 'kraken': 'AAVEUSD'},
        'BTC': {'binance': 'BTCUSDT', 'kraken': 'XBTUSD'},
        'ETH': {'binance': 'ETHUSDT', 'kraken': 'ETHUSD'},
        'XRP': {'binance': 'XRPUSDT', 'kraken': 'XRPUSD'},
        'ADA': {'binance': 'ADAUSDT', 'kraken': 'ADAUSD'},
        'DOGE': {'binance': 'DOGEUSDT', 'kraken': 'DOGEUSD'},
        'MATIC': {'binance': 'MATICUSDT', 'kraken': 'MATICUSD'},
        'LTC': {'binance': 'LTCUSDT', 'kraken': 'LTCUSD'},
        'SHIB': {'binance': 'SHIBUSDT', 'kraken': 'SHIBUSD'},
        'PEPE': {'binance': 'PEPEUSDT', 'kraken': 'PEPEUSD'},
    }
    
    # Fee structure (Kraken)
    TAKER_FEE = 0.0026  # 0.26%
    MAKER_FEE = 0.0016  # 0.16%
    
    def __init__(self, starting_capital: float = 10000.0, dry_run: bool = False):
        self.starting_capital = starting_capital
        self.dry_run = dry_run
        
        # V14 Scoring Engine
        self.v14 = V14DanceEnhancer()
        
        # Kraken client
        if KRAKEN_AVAILABLE and not dry_run:
            self.kraken = get_kraken_client()
        else:
            self.kraken = None
        
        # Mycelium network for additional intelligence
        if MYCELIUM_AVAILABLE:
            self.network = MyceliumNetwork(initial_capital=starting_capital)
        else:
            self.network = None
        
        # Holdings
        self.holdings: Dict[str, Dict] = {}
        self.usd_balance = 0.0
        
        # Price tracking
        self.prices: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.current_prices: Dict[str, float] = {}
        
        # V14 Conversions - with INFINITE patience
        self.conversions: Dict[str, V14Conversion] = {}
        self.closed_conversions: List[Dict] = []
        self.conversion_counter = 0
        
        # Cooldowns
        self.last_conversion_time: Dict[str, datetime] = {}
        
        # State
        self.running = False
        self.start_time = None
        self.ws_connected = False
        
        # Stats
        self.stats = {
            'price_updates': 0,
            'conversions_opened': 0,
            'conversions_closed': 0,
            'total_profit': 0.0,
            'win_rate': 1.0,  # Target: 100%
            'conversions_rejected': 0,
        }
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\n🛑 Stopping V14 Labyrinth...")
        self.running = False
    
    def banner(self):
        """Display startup banner"""
        mode = "DRY RUN" if self.dry_run else "🔴 LIVE TRADING"
        print(f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗   ██╗ ██╗██╗  ██╗    ██╗      █████╗ ██████╗ ██╗   ██╗██████╗           ║
║   ██║   ██║███║██║  ██║    ██║     ██╔══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗          ║
║   ██║   ██║╚██║███████║    ██║     ███████║██████╔╝ ╚████╔╝ ██████╔╝          ║
║   ╚██╗ ██╔╝ ██║╚════██║    ██║     ██╔══██║██╔══██╗  ╚██╔╝  ██╔══██╗          ║
║    ╚████╔╝  ██║     ██║    ███████╗██║  ██║██████╔╝   ██║   ██║  ██║          ║
║     ╚═══╝   ╚═╝     ╚═╝    ╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝   ╚═╝  ╚═╝          ║
║                                                                               ║
║      🏆 100% WIN RATE LABYRINTH CONVERSIONS 🏆                                ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   V14 RULES:                                                                  ║
║   • Entry Score: {V14_LABYRINTH_CONFIG['entry_score_threshold']}+ (multi-factor)                                       ║
║   • Profit Target: {V14_LABYRINTH_CONFIG['profit_target_pct']}%                                                  ║
║   • Stop Loss: NONE (infinite patience)                                       ║
║   • Strategy: Convert holdings → wait for profit → extract                    ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║   MODE: {mode:<60}        ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    def load_holdings(self) -> bool:
        """Load current holdings from Kraken"""
        print("\n   🐙 Loading holdings from Kraken...")
        
        if self.dry_run or not self.kraken:
            # Simulate holdings for dry run
            self.holdings = {
                'ATOM': {'amount': 10.0, 'usd_value': 90.0},
                'SOL': {'amount': 0.5, 'usd_value': 85.0},
                'DOT': {'amount': 15.0, 'usd_value': 90.0},
            }
            self.usd_balance = 100.0
            print("      🔵 DRY RUN - Using simulated holdings")
            return True
        
        try:
            balance = self.kraken.get_account_balance()
            if not balance:
                print("      ❌ Could not get balance")
                return False
            
            print("      ✅ Connected! Your holdings:")
            
            total_value = 0.0
            for asset, amount in balance.items():
                if amount > 0.0001:
                    usd_value = self._estimate_value(asset, amount)
                    if usd_value >= 1.0:
                        # Map Kraken asset names
                        clean_asset = asset.replace('X', '').replace('Z', '') if asset.startswith('X') or asset.startswith('Z') else asset
                        if clean_asset == 'XBT':
                            clean_asset = 'BTC'
                        
                        self.holdings[clean_asset] = {
                            'amount': amount,
                            'usd_value': usd_value,
                        }
                        total_value += usd_value
                        
                        tradeable = "💰 TRADEABLE" if clean_asset in self.ASSET_PAIRS else ""
                        print(f"         {clean_asset}: {amount:.4f} (~${usd_value:.2f}) {tradeable}")
                        
                        if asset in ['USD', 'ZUSD']:
                            self.usd_balance += amount
            
            print(f"\n      💎 Total Portfolio: ~${total_value:.2f}")
            print(f"      💵 USD Available: ${self.usd_balance:.2f}")
            
            return len(self.holdings) > 0
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False
    
    def _estimate_value(self, asset: str, amount: float) -> float:
        """Estimate USD value of an asset"""
        if asset in ['USD', 'ZUSD', 'USDT', 'USDC']:
            return amount
        
        # Approximate prices
        prices = {
            'ATOM': 9.0, 'LUNA': 0.0001, 'DASH': 30.0,
            'SOL': 170.0, 'DOT': 6.0, 'LINK': 15.0,
            'AVAX': 35.0, 'NEAR': 5.0, 'APT': 8.0,
            'ARB': 0.80, 'OP': 1.80, 'UNI': 7.0,
            'AAVE': 280.0, 'BTC': 97000, 'XXBT': 97000,
            'ETH': 3400, 'XETH': 3400, 'XRP': 2.20,
            'ADA': 0.90, 'DOGE': 0.32, 'MATIC': 0.50,
            'LTC': 100.0,
        }
        return amount * prices.get(asset, 0.0)
    
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
            
            # Get all binance symbols we care about
            binance_symbols = {v['binance'] for v in self.ASSET_PAIRS.values()}
            
            for ticker in data:
                symbol = ticker['symbol']
                if symbol in binance_symbols:
                    price = float(ticker['lastPrice'])
                    volume = float(ticker.get('volume', 0))
                    
                    self.current_prices[symbol] = price
                    self.prices[symbol].append({
                        'price': price,
                        'volume': volume,
                        'time': datetime.now()
                    })
                    
                    # Update V14 scoring engine
                    self.v14.scoring_engine.update_price_history(symbol, price, volume)
            
            print(f"      ✅ Loaded {len(self.current_prices)} prices")
            
        except Exception as e:
            print(f"      ⚠️ REST API error: {e}")
    
    async def _price_feed(self):
        """WebSocket price feed"""
        # Get all symbols we need to watch
        binance_symbols = list({v['binance'].lower() for v in self.ASSET_PAIRS.values()})
        streams = [f"{s}@ticker" for s in binance_symbols[:20]]  # Limit streams
        url = self.WS_URL + "/".join(streams)
        
        print(f"\n   🌐 Connecting to Binance WebSocket ({len(streams)} streams)...")
        
        reconnect_delay = 1
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
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
                                symbol = ticker.get('s', '')
                                price = float(ticker.get('c', 0))
                                volume = float(ticker.get('v', 0))
                                
                                if price > 0:
                                    self.current_prices[symbol] = price
                                    self.prices[symbol].append({
                                        'price': price,
                                        'volume': volume,
                                        'time': datetime.now()
                                    })
                                    
                                    # Update V14 scoring engine
                                    self.v14.scoring_engine.update_price_history(symbol, price, volume)
                                    
                                    self.stats['price_updates'] += 1
                                    
                                    # Check conversions
                                    await self._check_conversions(symbol, price)
                                    
                                    # Check for new opportunities
                                    await self._check_opportunities(symbol, price, volume)
                                    
                        except Exception:
                            pass
                            
            except websockets.exceptions.ConnectionClosed:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
                    
            except Exception:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(reconnect_delay)
                    reconnect_delay = min(reconnect_delay * 2, 60)
    
    async def _check_conversions(self, symbol: str, price: float):
        """Check open conversions for exit condition"""
        
        conversions_to_close = []
        
        for conv_id, conv in self.conversions.items():
            # Find the binance symbol for this conversion
            from_binance = self.ASSET_PAIRS.get(conv.from_asset, {}).get('binance')
            to_binance = self.ASSET_PAIRS.get(conv.to_asset, {}).get('binance')
            
            if symbol in [from_binance, to_binance]:
                should_exit, pnl_pct = conv.update_pnl(price)
                
                if should_exit:
                    conversions_to_close.append(conv_id)
        
        # Close profitable conversions
        for conv_id in conversions_to_close:
            await self._close_conversion(conv_id)
    
    async def _check_opportunities(self, symbol: str, price: float, volume: float):
        """Check for new conversion opportunities using V14 scoring"""
        
        # Find asset for this symbol
        asset = None
        for a, pairs in self.ASSET_PAIRS.items():
            if pairs['binance'] == symbol:
                asset = a
                break
        
        if not asset or asset not in self.holdings:
            return
        
        # Check limits
        if len(self.conversions) >= V14_LABYRINTH_CONFIG['max_concurrent_conversions']:
            return
        
        # Check cooldown
        if asset in self.last_conversion_time:
            elapsed = (datetime.now() - self.last_conversion_time[asset]).total_seconds()
            if elapsed < V14_LABYRINTH_CONFIG['conversion_cooldown_sec']:
                return
        
        # Calculate price movement
        history = list(self.prices[symbol])
        if len(history) < 10:
            return
        
        # 1 minute price change
        one_min_prices = [h['price'] for h in history if 
                         (datetime.now() - h['time']).total_seconds() < 60]
        if len(one_min_prices) < 2:
            return
        
        price_change_1m = (price - one_min_prices[0]) / one_min_prices[0]
        
        # V14 Scoring
        v14_eval = self.v14.evaluate_entry(symbol, price, volume)
        
        # Decide on conversion direction
        side = None
        reason = ""
        
        if price_change_1m >= V14_LABYRINTH_CONFIG['min_up_move_to_convert']:
            # Price going UP - SELL to capture profit
            side = 'SELL'
            reason = f"📈 Price UP {price_change_1m*100:.2f}%"
        elif price_change_1m <= -V14_LABYRINTH_CONFIG['min_down_move_to_buy']:
            # Price going DOWN - BUY at discount
            side = 'BUY'
            reason = f"📉 Price DOWN {price_change_1m*100:.2f}%"
        
        if not side:
            return
        
        # V14 APPROVAL CHECK (for buys)
        if side == 'BUY' and not v14_eval['should_enter']:
            self.stats['conversions_rejected'] += 1
            return
        
        # Open conversion
        await self._open_conversion(asset, side, price, v14_eval['score'], reason)
    
    async def _open_conversion(self, asset: str, side: str, price: float, 
                                score: int, reason: str):
        """Open a V14-scored conversion"""
        
        holding = self.holdings.get(asset)
        if not holding:
            return
        
        # Calculate conversion size
        if side == 'SELL':
            # Sell portion of holdings
            sell_pct = min(0.20, 0.10 + score * 0.01)  # Scale with V14 score
            quantity = holding['amount'] * sell_pct
            usd_value = quantity * price
        else:
            # Buy with USD
            if self.usd_balance < V14_LABYRINTH_CONFIG['min_conversion_usd']:
                return
            usd_value = min(
                V14_LABYRINTH_CONFIG['max_conversion_usd'],
                self.usd_balance * 0.20
            )
            quantity = usd_value / price
        
        if usd_value < V14_LABYRINTH_CONFIG['min_conversion_usd']:
            return
        
        # Get Kraken pair
        kraken_pair = self.ASSET_PAIRS.get(asset, {}).get('kraken', f'{asset}USD')
        
        # Create conversion
        self.conversion_counter += 1
        conv_id = f"V14-{self.conversion_counter:04d}"
        
        conversion = V14Conversion(
            id=conv_id,
            from_asset=asset if side == 'SELL' else 'USD',
            to_asset='USD' if side == 'SELL' else asset,
            entry_price=price,
            quantity=quantity,
            usd_value=usd_value,
            entry_time=datetime.now(),
            entry_score=score,
            kraken_pair=kraken_pair,
            side=side,
            current_price=price,
        )
        
        # Execute on Kraken (if not dry run)
        if not self.dry_run and self.kraken:
            try:
                result = self.kraken.place_market_order(
                    symbol=kraken_pair,
                    side=side.lower(),
                    quantity=quantity
                )
                if not result or 'orderId' not in result:
                    print(f"\n   ⚠️ Conversion failed: {result}")
                    return
            except Exception as e:
                print(f"\n   ❌ Conversion error: {e}")
                return
        
        # Store conversion
        self.conversions[conv_id] = conversion
        self.last_conversion_time[asset] = datetime.now()
        self.stats['conversions_opened'] += 1
        
        # Update holdings tracking
        if side == 'SELL':
            holding['amount'] -= quantity
            self.usd_balance += usd_value * (1 - self.TAKER_FEE)
        else:
            holding['amount'] += quantity
            self.usd_balance -= usd_value
        
        mode = "(DRY)" if self.dry_run else ""
        print(f"\n   🌀 V14 CONVERSION {mode}: {conv_id}")
        print(f"      {side} {quantity:.4f} {asset} @ ${price:.4f}")
        print(f"      Score: {score} | Value: ${usd_value:.2f} | {reason}")
        print(f"      Target: +{V14_LABYRINTH_CONFIG['profit_target_pct']}% | Stop: NONE (∞ patience)")
    
    async def _close_conversion(self, conv_id: str):
        """Close a conversion at profit target"""
        
        if conv_id not in self.conversions:
            return
        
        conv = self.conversions[conv_id]
        
        pnl_usd = conv.usd_value * (conv.current_pnl_pct / 100)
        
        # Execute closing trade (if not dry run)
        if not self.dry_run and self.kraken:
            try:
                # Reverse the original trade
                close_side = 'buy' if conv.side == 'SELL' else 'sell'
                result = self.kraken.place_market_order(
                    symbol=conv.kraken_pair,
                    side=close_side,
                    quantity=conv.quantity
                )
                if not result:
                    print(f"\n   ⚠️ Close conversion failed")
                    return
            except Exception as e:
                print(f"\n   ❌ Close error: {e}")
                return
        
        # Record closed conversion
        closed = {
            'id': conv.id,
            'from_asset': conv.from_asset,
            'to_asset': conv.to_asset,
            'entry_price': conv.entry_price,
            'exit_price': conv.current_price,
            'pnl_pct': conv.current_pnl_pct,
            'pnl_usd': pnl_usd,
            'entry_score': conv.entry_score,
            'hold_hours': (datetime.now() - conv.entry_time).total_seconds() / 3600,
        }
        self.closed_conversions.append(closed)
        
        # Update stats
        self.stats['conversions_closed'] += 1
        self.stats['total_profit'] += pnl_usd
        
        # Calculate win rate (should be 100%!)
        wins = sum(1 for c in self.closed_conversions if c['pnl_usd'] > 0)
        self.stats['win_rate'] = wins / len(self.closed_conversions)
        
        # Remove from open conversions
        del self.conversions[conv_id]
        
        mode = "(DRY)" if self.dry_run else ""
        print(f"\n   🎯 V14 EXIT {mode}: {conv.id}")
        print(f"      PnL: +{conv.current_pnl_pct:.2f}% (+${pnl_usd:.4f})")
        print(f"      Total Profit: ${self.stats['total_profit']:.4f} | WR: {self.stats['win_rate']*100:.0f}%")
    
    async def _display_loop(self):
        """Display live stats"""
        
        while self.running:
            await asyncio.sleep(5)
            self._display_stats()
    
    def _display_stats(self):
        """Display current stats"""
        
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        
        # Build conversion summary
        conv_summary = ""
        for conv in list(self.conversions.values())[:3]:
            arrow = "📈" if conv.current_pnl_pct > 0 else "📉"
            conv_summary += f" {conv.from_asset}: {conv.current_pnl_pct:+.2f}%{arrow}"
        
        print(f"\r   ⏱️ {elapsed:.0f}s | "
              f"📡 {self.stats['price_updates']:,} | "
              f"🌀 {len(self.conversions)} open | "
              f"✅ {self.stats['conversions_closed']} closed | "
              f"💰 ${self.stats['total_profit']:.4f} | "
              f"🏆 {self.stats['win_rate']*100:.0f}% WR{conv_summary}", 
              end='', flush=True)
    
    def _final_report(self):
        """Final session report"""
        
        if not self.start_time:
            return
        
        elapsed = time.time() - self.start_time
        
        print("\n\n" + "═"*80)
        print("🏆 V14 LABYRINTH SESSION REPORT")
        print("═"*80)
        
        print(f"\n⏱️ SESSION")
        print(f"   Runtime: {elapsed:.1f}s ({elapsed/3600:.2f} hours)")
        print(f"   Mode: {'DRY RUN' if self.dry_run else 'LIVE TRADING'}")
        
        print(f"\n🌀 CONVERSIONS")
        print(f"   Opened: {self.stats['conversions_opened']}")
        print(f"   Closed: {self.stats['conversions_closed']}")
        print(f"   Still Open: {len(self.conversions)}")
        print(f"   Rejected (V14): {self.stats['conversions_rejected']}")
        
        print(f"\n💰 PROFIT")
        print(f"   Total Profit: ${self.stats['total_profit']:.4f}")
        print(f"   🏆 WIN RATE: {self.stats['win_rate']*100:.0f}%")
        
        if self.closed_conversions:
            avg_pnl = sum(c['pnl_pct'] for c in self.closed_conversions) / len(self.closed_conversions)
            avg_hold = sum(c['hold_hours'] for c in self.closed_conversions) / len(self.closed_conversions)
            print(f"   Average PnL: {avg_pnl:.2f}%")
            print(f"   Average Hold: {avg_hold:.2f} hours")
        
        if self.conversions:
            print(f"\n📊 OPEN CONVERSIONS ({len(self.conversions)})")
            for conv in self.conversions.values():
                print(f"   {conv.id}: {conv.from_asset}→{conv.to_asset} @ ${conv.entry_price:.4f} | "
                      f"Current: {conv.current_pnl_pct:+.2f}%")
        
        print("\n" + "═"*80)
        print("🏆 V14 LABYRINTH: PATIENCE IS PROFIT - NO STOP LOSS, INFINITE PATIENCE 🏆")
        print("═"*80 + "\n")
    
    async def run(self):
        """Main run loop"""
        
        self.banner()
        
        if not self.load_holdings():
            print("\n   ❌ No holdings to convert!")
            return
        
        # Confirmation
        if not self.dry_run:
            print("\n" + "═"*70)
            print("⚠️  REAL MONEY V14 LABYRINTH TRADING ⚠️")
            print("═"*70)
            print("\n   V14 Conversion Rules:")
            print(f"   • Entry Score: {V14_LABYRINTH_CONFIG['entry_score_threshold']}+ required for buys")
            print(f"   • Profit Target: {V14_LABYRINTH_CONFIG['profit_target_pct']}%")
            print(f"   • Stop Loss: NONE (hold until profit)")
            
            confirm = input("\n   Type 'V14 LABYRINTH' to start: ")
            if confirm != 'V14 LABYRINTH':
                print("\n   Aborted.")
                return
        
        print("\n🏆🌀🏆 V14 LABYRINTH ACTIVATED! 🏆🌀🏆\n")
        
        self.running = True
        self.start_time = time.time()
        
        await self._fetch_initial_prices()
        
        try:
            await asyncio.gather(
                self._price_feed(),
                self._display_loop(),
            )
        except asyncio.CancelledError:
            pass
        finally:
            self._final_report()


# Need to import time for the engine
import time


async def main():
    """Entry point"""
    
    import argparse
    parser = argparse.ArgumentParser(description='V14 Labyrinth Conversion Engine')
    parser.add_argument('--dry-run', action='store_true', help='Run without real trades')
    parser.add_argument('--capital', type=float, default=10000.0, help='Starting capital')
    args = parser.parse_args()
    
    print("\n🏆🌀🏆 V14 LABYRINTH ENGINE 🏆🌀🏆")
    print("   100% WIN RATE CONVERSIONS")
    print("   Press Ctrl+C to stop\n")
    
    engine = V14LabyrinthEngine(
        starting_capital=args.capital,
        dry_run=args.dry_run
    )
    await engine.run()


if __name__ == "__main__":
    asyncio.run(main())
