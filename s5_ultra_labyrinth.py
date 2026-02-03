#!/usr/bin/env python3
"""
S5 LABYRINTH - ULTRA AGGRESSIVE
================================
Trades ANY movement in your holdings.
No waiting for "perfect" setup - just trade!
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import asyncio
import websockets
import signal
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kraken_client import KrakenClient, get_kraken_client
from aureon_mycelium import MyceliumNetwork


class S5UltraLabyrinth:
    """
    ULTRA AGGRESSIVE LABYRINTH
    - Trade on ANY detectable movement
    - Use everything you have
    - Print money from the labyrinth
    """
    
    WS_URL = "wss://stream.binance.com:9443/stream?streams="
    
    # Map holdings to trading pairs - EXPANDED!
    # Add ALL pairs where you could accumulate assets
    ASSET_MAP = {
        'ATOM': {'binance': 'ATOMUSDT', 'kraken': 'ATOMUSD'},
        'DASH': {'binance': 'DASHUSDT', 'kraken': 'DASHUSD'},
        # More pairs to expand into
        'SOL': {'binance': 'SOLUSDT', 'kraken': 'SOLUSD'},
        'DOT': {'binance': 'DOTUSDT', 'kraken': 'DOTUSD'},
        'LINK': {'binance': 'LINKUSDT', 'kraken': 'LINKUSD'},
        'AVAX': {'binance': 'AVAXUSDT', 'kraken': 'AVAXUSD'},
        'UNI': {'binance': 'UNIUSDT', 'kraken': 'UNIUSD'},
        'AAVE': {'binance': 'AAVEUSDT', 'kraken': 'AAVEUSD'},
        'CRV': {'binance': 'CRVUSDT', 'kraken': 'CRVUSD'},
        'SUSHI': {'binance': 'SUSHIUSDT', 'kraken': 'SUSHIUSD'},
        'COMP': {'binance': 'COMPUSDT', 'kraken': 'COMPUSD'},
        'SNX': {'binance': 'SNXUSDT', 'kraken': 'SNXUSD'},
        'YFI': {'binance': 'YFIUSDT', 'kraken': 'YFIUSD'},
        'MKR': {'binance': 'MKRUSDT', 'kraken': 'MKRUSD'},
        'GRT': {'binance': 'GRTUSDT', 'kraken': 'GRTUSD'},
        'FLOW': {'binance': 'FLOWUSDT', 'kraken': 'FLOWUSD'},
        'NEAR': {'binance': 'NEARUSDT', 'kraken': 'NEARUSD'},
        'APT': {'binance': 'APTUSDT', 'kraken': 'APTUSD'},
        'ARB': {'binance': 'ARBUSDT', 'kraken': 'ARBUSD'},
        'OP': {'binance': 'OPUSDT', 'kraken': 'OPUSD'},
        'IMX': {'binance': 'IMXUSDT', 'kraken': 'IMXUSD'},
        'SAND': {'binance': 'SANDUSDT', 'kraken': 'SANDUSD'},
        'MANA': {'binance': 'MANAUSDT', 'kraken': 'MANAUSD'},
        'FTM': {'binance': 'FTMUSDT', 'kraken': 'FTMUSD'},
        'DYDX': {'binance': 'DYDXUSDT', 'kraken': 'DYDXUSD'},
        'LDO': {'binance': 'LDOUSDT', 'kraken': 'LDOUSD'},
        'RPL': {'binance': 'RPLUSDT', 'kraken': 'RPLUSD'},
    }
    
    # ULTRA AGGRESSIVE - trade on ANY movement
    MIN_MOVE_PCT = 0.01  # 0.01% = 1 bp - even smaller movements
    
    def __init__(self):
        self.kraken = get_kraken_client()
        
        # State
        self.holdings = {}
        self.prices = defaultdict(list)
        self.current_prices = {}
        self.running = False
        self.start_time = None
        self.last_trade_time = {}
        
        # Stats
        self.trades_executed = 0
        self.total_profit = 0.0
        self.trade_log = []
        
        signal.signal(signal.SIGINT, self._stop)
        signal.signal(signal.SIGTERM, self._stop)
    
    def _stop(self, *args):
        print("\n🛑 Stopping...")
        self.running = False
    
    def load_holdings(self):
        """Load Kraken balances"""
        print("\n🐙 Loading Kraken holdings...")
        
        try:
            balance = self.kraken.get_account_balance()
            if not balance:
                print("   ❌ No balance")
                return False
            
            for asset, amount in balance.items():
                if amount > 0.0001 and asset in self.ASSET_MAP:
                    self.holdings[asset] = amount
                    print(f"   ✅ {asset}: {amount:.4f}")
            
            if not self.holdings:
                print("   ⚠️ No tradeable holdings (need ATOM, LUNA, or DASH)")
                return False
            
            return True
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return False
    
    async def run(self):
        """Main loop"""
        print("""
╔══════════════════════════════════════════════════════════╗
║   🌀 S5 ULTRA LABYRINTH - USE WHAT YOU HAVE 🌀          ║
║   Trade ANY movement, no perfect start needed            ║
╚══════════════════════════════════════════════════════════╝
""")
        
        if not self.load_holdings():
            return
        
        print("\n⚠️  Type 'GO' to start REAL trading: ", end='')
        confirm = input()
        if confirm.strip().upper() != 'GO':
            print("Aborted.")
            return
        
        print("\n🔥 LABYRINTH ACTIVATED! 🔥\n")
        
        self.running = True
        self.start_time = datetime.now()
        
        await asyncio.gather(
            self._price_feed(),
            self._trader_loop(),
            self._status_display(),
        )
        
        self._report()
    
    async def _price_feed(self):
        """WebSocket price feed"""
        symbols = [self.ASSET_MAP[a]['binance'].lower() for a in self.holdings]
        streams = [f"{s}@ticker" for s in symbols]
        url = self.WS_URL + "/".join(streams)
        
        print(f"📡 Connecting to {len(symbols)} price feeds...")
        
        while self.running:
            try:
                async with websockets.connect(url) as ws:
                    print("   ✅ Connected!")
                    
                    while self.running:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=10)
                            data = json.loads(msg)
                            
                            if 'data' in data:
                                t = data['data']
                                symbol = t.get('s', '')
                                price = float(t.get('c', 0))
                                change = float(t.get('P', 0))  # 24h % change
                                
                                if price > 0:
                                    self.current_prices[symbol] = {
                                        'price': price,
                                        'change_24h': change,
                                        'time': datetime.now()
                                    }
                                    self.prices[symbol].append((datetime.now(), price))
                                    
                                    # Keep 2 minutes of history
                                    cutoff = datetime.now() - timedelta(minutes=2)
                                    self.prices[symbol] = [(t, p) for t, p in self.prices[symbol] if t > cutoff]
                                    
                        except asyncio.TimeoutError:
                            continue
                            
            except Exception as e:
                print(f"\n   ⚠️ WS error: {e}")
                if self.running:
                    await asyncio.sleep(3)
    
    async def _trader_loop(self):
        """Main trading logic"""
        await asyncio.sleep(5)  # Wait for price data
        
        while self.running:
            for asset, amount in self.holdings.items():
                if amount < 0.001:
                    continue
                
                binance_sym = self.ASSET_MAP[asset]['binance']
                
                if binance_sym not in self.prices or len(self.prices[binance_sym]) < 5:
                    continue
                
                # Rate limit: 1 trade per asset per 30 seconds
                if asset in self.last_trade_time:
                    if (datetime.now() - self.last_trade_time[asset]).seconds < 30:
                        continue
                
                # Get recent price movement
                history = self.prices[binance_sym]
                current = history[-1][1]
                oldest = history[0][1]
                
                pct_change = (current - oldest) / oldest * 100
                
                # TRADE ON ANY DETECTABLE MOVEMENT!
                # If price moved more than 0.02% in last 2 min, trade it
                if abs(pct_change) >= self.MIN_MOVE_PCT:
                    await self._execute_trade(asset, current, pct_change)
            
            await asyncio.sleep(2)
    
    async def _execute_trade(self, asset: str, price: float, pct_change: float):
        """Execute a trade"""
        
        amount = self.holdings[asset]
        kraken_pair = self.ASSET_MAP[asset]['kraken']
        
        # Calculate trade size - aim for at least $1 value
        min_trade_value = 1.5  # Slightly above Kraken $1 min
        trade_value = amount * price
        
        if trade_value < min_trade_value:
            # Can't meet minimum, skip
            return
        
        # Use 50% of holdings if total is small, otherwise scale with movement
        if trade_value < 10:
            trade_pct = 0.5  # Use half if small position
        else:
            trade_pct = min(0.25, 0.10 + abs(pct_change) / 5)
        
        trade_amount = amount * trade_pct
        trade_value = trade_amount * price
        
        # Final check
        if trade_value < 1.0:
            return
        
        side = 'sell' if pct_change > 0 else 'buy'
        
        print(f"\n   🌀 {side.upper()} {trade_amount:.4f} {asset} @ ${price:.4f}")
        print(f"      Movement: {pct_change:+.2f}% | Value: ${trade_value:.2f}")
        
        try:
            result = self.kraken.place_market_order(
                symbol=kraken_pair,
                side=side,
                quantity=trade_amount
            )
            
            if result:
                self.trades_executed += 1
                profit_est = trade_value * abs(pct_change) / 100
                self.total_profit += profit_est
                self.last_trade_time[asset] = datetime.now()
                
                # Update holdings
                if side == 'sell':
                    self.holdings[asset] -= trade_amount
                else:
                    self.holdings[asset] += trade_amount
                
                self.trade_log.append({
                    'time': datetime.now().isoformat(),
                    'asset': asset,
                    'side': side,
                    'amount': trade_amount,
                    'price': price,
                    'value': trade_value,
                    'pct_change': pct_change,
                })
                
                print(f"      ✅ DONE! Est profit: ${profit_est:.4f}")
            else:
                print(f"      ⚠️ No response")
                
        except Exception as e:
            print(f"      ❌ Error: {e}")
    
    async def _status_display(self):
        """Show status"""
        while self.running:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            hours = max(0.001, elapsed / 3600)
            velocity = self.total_profit / hours
            
            prices_str = " | ".join([
                f"{a}=${self.current_prices.get(self.ASSET_MAP[a]['binance'], {}).get('price', 0):.4f}"
                for a in self.holdings
            ])
            
            print(f"\r⏱️ {int(elapsed)}s | 💰 {self.trades_executed} | ${self.total_profit:.4f} | "
                  f"⚡${velocity:.2f}/hr | {prices_str}",
                  end='', flush=True)
            
            await asyncio.sleep(5)
    
    def _report(self):
        """Final report"""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print("\n\n" + "="*60)
        print("📊 LABYRINTH SESSION REPORT")
        print("="*60)
        print(f"⏱️ Runtime: {elapsed:.0f}s")
        print(f"💰 Trades: {self.trades_executed}")
        print(f"💵 Est Profit: ${self.total_profit:.4f}")
        if self.trade_log:
            print("\n📝 Trade Log:")
            for t in self.trade_log:
                print(f"   {t['side'].upper()} {t['amount']:.4f} {t['asset']} @ ${t['price']:.4f} ({t['pct_change']:+.2f}%)")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(S5UltraLabyrinth().run())
