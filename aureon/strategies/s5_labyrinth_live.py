#!/usr/bin/env python3
"""
S5 LABYRINTH LIVE TRADER
========================
Uses what you have and moves it through the labyrinth.
No perfect start - just start with what you've got!

YOUR HOLDINGS → LABYRINTH PATHS → PROFIT → REPEAT
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import websockets
import signal
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict
import threading
import requests

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kraken_client import KrakenClient, get_kraken_client
from aureon_mycelium import MyceliumNetwork


@dataclass
class LabyrinthOpportunity:
    """A path through the labyrinth"""
    asset: str
    side: str  # BUY or SELL
    symbol: str
    kraken_pair: str
    quantity: float
    price: float
    usd_value: float
    reason: str
    price_change_1m: float
    price_change_5m: float
    timestamp: datetime


class S5LabyrinthLive:
    """
    LABYRINTH TRADER
    ================
    - Watches real-time prices
    - When YOUR assets move favorably → SELL to capture profit
    - When prices dip → BUY with USD you gained
    - Repeat through the labyrinth
    """
    
    # Binance WebSocket
    WS_URL = "wss://stream.binance.com:9443/stream?streams="
    
    # Your holdings map to these pairs
    KRAKEN_PAIRS = {
        'ATOM': ('ATOMUSDT', 'ATOMUSD'),
        'LUNA': ('LUNCUSDT', 'LUNAUSD'),  # LUNA Classic
        'DASH': ('DASHUSDT', 'DASHUSD'),
    }
    
    # Also watch major pairs for opportunities
    WATCH_PAIRS = [
        'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT',
        'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'ATOMUSDT', 'LUNCUSDT',
        'DASHUSDT', 'LINKUSDT', 'MATICUSDT',
    ]
    
    # Risk limits
    MAX_POSITION_USD = 50.0
    MIN_TRADE_USD = 1.0  # Kraken minimum is ~$1
    MAX_DAILY_TRADES = 50
    MAX_DAILY_LOSS = 20.0
    
    # VERY aggressive thresholds
    MIN_MOVE_TO_SELL = 0.001  # 0.1% up = sell some
    MIN_DIP_TO_BUY = -0.002   # 0.2% down = buy opportunity
    
    def __init__(self):
        self.kraken = get_kraken_client()
        self.network = MyceliumNetwork(initial_capital=100.0)
        
        # Holdings
        self.holdings: Dict[str, Dict] = {}
        self.usd_balance = 0.0
        
        # Prices
        self.prices: Dict[str, List[tuple]] = defaultdict(list)  # [(time, price), ...]
        self.current_prices: Dict[str, float] = {}
        
        # Stats
        self.running = False
        self.start_time = None
        self.trades_today = 0
        self.daily_pnl = 0.0
        self.total_profit = 0.0
        self.real_trades = []
        
        # Threading
        self.ws_connected = False
        
        # Signal handling
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        print("\n\n🛑 Stopping labyrinth trader...")
        self.running = False
    
    def banner(self):
        print("""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗      █████╗ ██████╗ ██╗   ██╗██████╗ ██╗███╗   ██╗████████╗██╗  ██╗     ║
║   ██║     ██╔══██╗██╔══██╗╚██╗ ██╔╝██╔══██╗██║████╗  ██║╚══██╔══╝██║  ██║     ║
║   ██║     ███████║██████╔╝ ╚████╔╝ ██████╔╝██║██╔██╗ ██║   ██║   ███████║     ║
║   ██║     ██╔══██║██╔══██╗  ╚██╔╝  ██╔══██╗██║██║╚██╗██║   ██║   ██╔══██║     ║
║   ███████╗██║  ██║██████╔╝   ██║   ██║  ██║██║██║ ╚████║   ██║   ██║  ██║     ║
║   ╚══════╝╚═╝  ╚═╝╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝     ║
║                                                                               ║
║      🌀 USE WHAT YOU HAVE - MOVE THROUGH THE LABYRINTH 🌀                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
""")
    
    def load_holdings(self) -> bool:
        """Load current holdings from Kraken"""
        print("\n   🐙 Loading holdings from Kraken...")
        
        try:
            balance = self.kraken.get_account_balance()
            if not balance:
                print("      ❌ Could not get balance")
                return False
            
            print("      ✅ Connected! Your holdings:")
            
            self.holdings = {}
            total_value = 0.0
            
            for asset, amount in balance.items():
                if amount > 0.0001:
                    usd_value = self._estimate_value(asset, amount)
                    if usd_value >= 0.10:  # At least 10 cents
                        self.holdings[asset] = {
                            'amount': amount,
                            'usd_value': usd_value,
                            'tradeable': asset in ['ATOM', 'LUNA', 'DASH', 'SOL', 'DOT', 'XXBT', 'XETH']
                        }
                        total_value += usd_value
                        
                        status = "💰 TRADEABLE" if self.holdings[asset]['tradeable'] else ""
                        print(f"         {asset}: {amount:.4f} (~${usd_value:.2f}) {status}")
                        
                        if asset in ['USD', 'ZUSD']:
                            self.usd_balance += amount
            
            print(f"\n      💎 Total Portfolio: ~${total_value:.2f}")
            print(f"      💵 USD Available: ${self.usd_balance:.2f}")
            
            return True
            
        except Exception as e:
            print(f"      ❌ Error: {e}")
            return False
    
    def _estimate_value(self, asset: str, amount: float) -> float:
        """Estimate USD value"""
        if asset in ['USD', 'ZUSD', 'USDT', 'USDC', 'TUSD']:
            return amount
        
        # Known prices (approximate)
        prices = {
            'ATOM': 9.0, 'LUNA': 0.0001, 'DASH': 30.0,
            'AIR': 0.01, 'MON': 0.05, 'NIGHT': 0.001,
            'XXBT': 95000, 'XETH': 3400,
        }
        return amount * prices.get(asset, 0.0)
    
    async def run(self):
        """Main run loop"""
        self.banner()
        
        if not self.load_holdings():
            return
        
        tradeable = [a for a, h in self.holdings.items() if h['tradeable']]
        if not tradeable:
            print("\n   ⚠️ No tradeable assets found!")
            print("      Need ATOM, LUNA, DASH, etc. on Kraken")
            return
        
        print(f"\n   🎯 Will trade: {', '.join(tradeable)}")
        
        # Confirmation
        print("\n" + "="*70)
        print("   ⚠️  REAL MONEY TRADING ⚠️")
        print("="*70)
        print(f"   Assets: {', '.join(tradeable)}")
        print(f"   Max per trade: ${self.MAX_POSITION_USD}")
        print(f"   Max daily trades: {self.MAX_DAILY_TRADES}")
        confirm = input("\n   Type 'LABYRINTH' to start: ")
        
        if confirm.strip().upper() != 'LABYRINTH':
            print("   Aborted.")
            return
        
        print("\n   🌀🌀🌀 ENTERING THE LABYRINTH 🌀🌀🌀\n")
        
        self.running = True
        self.start_time = datetime.now()
        
        # Run price feed and display
        await asyncio.gather(
            self._price_feed(),
            self._display_loop(),
            self._opportunity_scanner(),
        )
        
        self._final_report()
    
    async def _price_feed(self):
        """Connect to Binance WebSocket for real-time prices"""
        streams = [f"{p.lower()}@ticker" for p in self.WATCH_PAIRS]
        url = self.WS_URL + "/".join(streams)
        
        while self.running:
            try:
                async with websockets.connect(url, ping_interval=20) as ws:
                    self.ws_connected = True
                    
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=5)
                            data = json.loads(msg)
                            
                            if 'data' in data:
                                ticker = data['data']
                                symbol = ticker.get('s', '')
                                price = float(ticker.get('c', 0))
                                
                                if price > 0:
                                    now = datetime.now()
                                    self.current_prices[symbol] = price
                                    self.prices[symbol].append((now, price))
                                    
                                    # Keep 5 minutes of history
                                    cutoff = now - timedelta(minutes=5)
                                    self.prices[symbol] = [(t, p) for t, p in self.prices[symbol] if t > cutoff]
                        except asyncio.TimeoutError:
                            continue
                        except Exception:
                            pass
                            
            except Exception as e:
                self.ws_connected = False
                if self.running:
                    await asyncio.sleep(5)
    
    async def _opportunity_scanner(self):
        """Scan for opportunities in your holdings"""
        await asyncio.sleep(10)  # Wait for price data
        
        while self.running:
            try:
                # Check each tradeable holding
                for asset, info in self.holdings.items():
                    if not info.get('tradeable', False):
                        continue
                    
                    opp = self._check_asset_opportunity(asset, info)
                    if opp:
                        await self._execute_opportunity(opp)
                
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"\n   ⚠️ Scanner error: {e}")
                await asyncio.sleep(5)
    
    def _check_asset_opportunity(self, asset: str, info: dict) -> Optional[LabyrinthOpportunity]:
        """Check if an asset has an opportunity"""
        
        # Get binance symbol for this asset
        binance_symbol = None
        kraken_pair = None
        
        if asset in self.KRAKEN_PAIRS:
            binance_symbol, kraken_pair = self.KRAKEN_PAIRS[asset]
        elif asset == 'ATOM':
            binance_symbol, kraken_pair = 'ATOMUSDT', 'ATOMUSD'
        elif asset == 'LUNA':
            binance_symbol, kraken_pair = 'LUNCUSDT', 'LUNAUSD'
        elif asset == 'DASH':
            binance_symbol, kraken_pair = 'DASHUSDT', 'DASHUSD'
        else:
            return None
        
        if binance_symbol not in self.prices or len(self.prices[binance_symbol]) < 10:
            return None
        
        history = self.prices[binance_symbol]
        current_price = history[-1][1]
        
        # Calculate price changes over different windows
        now = datetime.now()
        
        # 1 minute change
        one_min_ago = [(t, p) for t, p in history if t > now - timedelta(minutes=1)]
        if one_min_ago:
            price_1m = one_min_ago[0][1]
            change_1m = (current_price - price_1m) / price_1m
        else:
            change_1m = 0
        
        # 5 minute change  
        five_min_ago = [(t, p) for t, p in history if t > now - timedelta(minutes=5)]
        if five_min_ago:
            price_5m = five_min_ago[0][1]
            change_5m = (current_price - price_5m) / price_5m
        else:
            change_5m = 0
        
        # SELL if price going UP (capture profit)
        if change_1m >= self.MIN_MOVE_TO_SELL or change_5m >= self.MIN_MOVE_TO_SELL * 2:
            # Calculate how much to sell (scale with price move)
            sell_pct = min(0.20, 0.05 + abs(change_1m) * 10)
            sell_amount = info['amount'] * sell_pct
            sell_value = sell_amount * current_price
            
            if sell_value >= self.MIN_TRADE_USD:
                return LabyrinthOpportunity(
                    asset=asset,
                    side='SELL',
                    symbol=binance_symbol,
                    kraken_pair=kraken_pair,
                    quantity=sell_amount,
                    price=current_price,
                    usd_value=sell_value,
                    reason=f"Price UP {change_1m*100:.2f}% (1m), {change_5m*100:.2f}% (5m)",
                    price_change_1m=change_1m,
                    price_change_5m=change_5m,
                    timestamp=now
                )
        
        return None
    
    async def _execute_opportunity(self, opp: LabyrinthOpportunity):
        """Execute a labyrinth opportunity"""
        
        # Risk checks
        if self.trades_today >= self.MAX_DAILY_TRADES:
            return
        if self.daily_pnl <= -self.MAX_DAILY_LOSS:
            return
        
        print(f"\n   🌀 LABYRINTH OPPORTUNITY:")
        print(f"      {opp.side} {opp.quantity:.4f} {opp.asset} @ ${opp.price:.4f}")
        print(f"      Value: ${opp.usd_value:.2f}")
        print(f"      Reason: {opp.reason}")
        
        try:
            result = self.kraken.place_market_order(
                pair=opp.kraken_pair,
                side=opp.side.lower(),
                volume=opp.quantity
            )
            
            if result:
                self.trades_today += 1
                estimated_profit = opp.usd_value * abs(opp.price_change_1m)
                self.total_profit += estimated_profit
                self.daily_pnl += estimated_profit
                
                self.real_trades.append({
                    'time': opp.timestamp.isoformat(),
                    'asset': opp.asset,
                    'side': opp.side,
                    'quantity': opp.quantity,
                    'price': opp.price,
                    'value': opp.usd_value,
                    'reason': opp.reason,
                    'result': str(result)[:100]
                })
                
                print(f"      ✅ EXECUTED! Est profit: ${estimated_profit:.4f}")
                
                # Update holdings
                if opp.asset in self.holdings:
                    self.holdings[opp.asset]['amount'] -= opp.quantity
                    self.holdings[opp.asset]['usd_value'] -= opp.usd_value
                
                self.usd_balance += opp.usd_value
                
            else:
                print(f"      ⚠️ Order response empty")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    async def _display_loop(self):
        """Display status"""
        while self.running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            hours = elapsed / 3600
            velocity = self.total_profit / hours if hours > 0 else 0
            
            ws_status = "🟢" if self.ws_connected else "🔴"
            
            print(f"\r   {ws_status} ⏱️ {int(elapsed)}s | 💰 {len(self.real_trades)} trades | "
                  f"💵 ${self.total_profit:.4f} | ⚡ ${velocity:.2f}/hr | 💎 ${self.usd_balance:.2f} USD",
                  end='', flush=True)
            
            await asyncio.sleep(5)
    
    def _final_report(self):
        """Print final report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        hours = elapsed / 3600
        
        print("\n\n" + "="*70)
        print("   📊 LABYRINTH SESSION REPORT")
        print("="*70)
        print(f"   ⏱️ Runtime: {elapsed:.0f}s ({hours:.2f} hours)")
        print(f"   💰 Total Trades: {len(self.real_trades)}")
        print(f"   💵 Estimated Profit: ${self.total_profit:.4f}")
        print(f"   ⚡ Velocity: ${self.total_profit/hours:.2f}/hr" if hours > 0 else "   ⚡ Velocity: N/A")
        
        if self.real_trades:
            print("\n   📝 Trade Log:")
            for t in self.real_trades[-10:]:  # Last 10 trades
                print(f"      {t['time'][:19]} | {t['side']} {t['quantity']:.4f} {t['asset']} | ${t['value']:.2f}")
        
        print("="*70 + "\n")


async def main():
    trader = S5LabyrinthLive()
    await trader.run()


if __name__ == "__main__":
    asyncio.run(main())
