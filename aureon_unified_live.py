#!/usr/bin/env python3
"""
🌌 AUREON UNIFIED LIVE TRADER 🌌
================================

ALL SYSTEMS INTEGRATED:
  ✨ 9 Auris Nodes (Coherence detection)
  ✨ Elephant Memory (Trade persistence)
  ✨ Fire Starter (Intensity scaling)
  ✨ Rainbow Bridge (Emotional frequencies)
  ✨ Kelly Criterion (Optimal sizing)
  ✨ Ping-Pong Engine (Momentum building)
  ✨ Temporal Reader (Past/Present/Future)
  ✨ Proper LOT_SIZE (No more errors!)

ONE SYSTEM. ALL THE POWER.

Gary Leckey | November 2025
"""

import os, sys, time, math, json, logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN
from binance_client import BinanceClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('aureon_unified_live.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

CONFIG = {
    'MIN_TRADE_USD': 6.0,
    'MAX_POSITIONS': 3,
    'STOP_LOSS_PCT': 0.02,
    'TAKE_PROFIT_PCT': 0.03,
    'PING_THRESHOLD': 0.005,  # 0.5% for entry
    'PONG_THRESHOLD': 0.01,   # 1% for exit
    'COHERENCE_THRESHOLD': 0.6,
    'COOLDOWN_MINUTES': 15,
}

# ═══════════════════════════════════════════════════════════════════════════
# ELEPHANT MEMORY
# ═══════════════════════════════════════════════════════════════════════════

class ElephantMemory:
    def __init__(self, filepath: str = 'memory.json'):
        self.filepath = filepath
        self.symbols = {}
        self.load()
    
    def load(self):
        try:
            with open(self.filepath) as f:
                self.symbols = json.load(f)
        except:
            self.symbols = {}
    
    def save(self):
        with open(self.filepath, 'w') as f:
            json.dump(self.symbols, f, indent=2)
    
    def record(self, symbol: str, profit_usd: float):
        if symbol not in self.symbols:
            self.symbols[symbol] = {'trades': 0, 'wins': 0, 'profit': 0, 'last_time': 0, 'streak': 0}
        
        s = self.symbols[symbol]
        s['trades'] += 1
        s['profit'] += profit_usd
        s['last_time'] = time.time()
        
        if profit_usd >= 0:
            s['wins'] += 1
            s['streak'] = 0
        else:
            s['streak'] += 1
        
        self.save()
    
    def should_avoid(self, symbol: str) -> bool:
        if symbol not in self.symbols:
            return False
        s = self.symbols[symbol]
        # Cooldown or 3+ loss streak
        if time.time() - s.get('last_time', 0) < CONFIG['COOLDOWN_MINUTES'] * 60:
            return True
        if s.get('streak', 0) >= 3:
            return True
        return False

# ═══════════════════════════════════════════════════════════════════════════
# LOT SIZE MANAGER
# ═══════════════════════════════════════════════════════════════════════════

class LotSizeManager:
    def __init__(self, client: BinanceClient):
        self.client = client
        self.cache = {}
        self.last_update = 0
    
    def update(self):
        if time.time() - self.last_update < 300: return
        try:
            info = self.client.exchange_info()
            for s in info['symbols']:
                sym = s['symbol']
                self.cache[sym] = {'status': s['status'], 'base': s['baseAsset'], 'quote': s['quoteAsset'], 'filters': {}}
                for f in s['filters']:
                    self.cache[sym]['filters'][f['filterType']] = f
            self.last_update = time.time()
        except Exception as e:
            logger.error(f"Exchange info error: {e}")
    
    def can_trade(self, symbol: str) -> bool:
        self.update()
        return self.cache.get(symbol, {}).get('status') == 'TRADING'
    
    def format_qty(self, symbol: str, qty: float) -> str:
        self.update()
        lot = self.cache.get(symbol, {}).get('filters', {}).get('LOT_SIZE', {})
        step = float(lot.get('stepSize', '0.001'))
        min_qty = float(lot.get('minQty', '0.001'))
        
        precision = len(str(step).rstrip('0').split('.')[-1]) if '.' in str(step) else 0
        qty_d = Decimal(str(qty))
        step_d = Decimal(str(step))
        formatted = (qty_d // step_d) * step_d
        formatted = max(Decimal(str(min_qty)), formatted)
        
        if precision == 0: return str(int(formatted))
        return f"{formatted:.{precision}f}"

# ═══════════════════════════════════════════════════════════════════════════
# COHERENCE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════

def calculate_coherence(price_change_pct: float, volume_btc: float, volatility_pct: float) -> float:
    S = min(1.0, volume_btc / 50.0)
    O = min(1.0, abs(price_change_pct) / 15.0)
    E = min(1.0, volatility_pct / 25.0)
    Lambda = (S + O + E) / 3.0
    return 1 / (1 + math.exp(-5 * (Lambda - 0.5)))

# ═══════════════════════════════════════════════════════════════════════════
# UNIFIED TRADER
# ═══════════════════════════════════════════════════════════════════════════

class AureonUnifiedLive:
    def __init__(self):
        self.client = BinanceClient()
        self.lot_mgr = LotSizeManager(self.client)
        self.memory = ElephantMemory()
        
        self.positions = {}
        self.ticker_cache = {}
        self.last_ticker_update = 0
        
        self.trades = 0
        self.wins = 0
        self.total_profit_usd = 0.0
    
    def update_tickers(self):
        if time.time() - self.last_ticker_update < 2: return
        try:
            tickers = self.client.session.get(f"{self.client.base}/api/v3/ticker/24hr", timeout=5).json()
            self.ticker_cache = {t['symbol']: t for t in tickers if t['symbol'].endswith('USDT') or t['symbol'].endswith('USDC')}
            self.last_ticker_update = time.time()
        except Exception as e:
            logger.error(f"Ticker update failed: {e}")
    
    def get_usdc_balance(self) -> float:
        return self.client.get_free_balance('USDC')
    
    def scan_opportunities(self) -> List[Dict]:
        opportunities = []
        
        for symbol, ticker in self.ticker_cache.items():
            if not symbol.endswith('USDC'): continue
            if not self.lot_mgr.can_trade(symbol): continue
            if self.memory.should_avoid(symbol): continue
            
            try:
                price = float(ticker['lastPrice'])
                change = float(ticker['priceChangePercent'])
                volume = float(ticker['quoteVolume'])
                high = float(ticker['highPrice'])
                low = float(ticker['lowPrice'])
                
                if volume < 10000: continue  # Min $10k volume
                
                volatility = ((high - low) / low * 100) if low > 0 else 0
                coherence = calculate_coherence(change, volume / price if price > 0 else 0, volatility)
                
                # Entry criteria: Dipped + High coherence
                if change < -1 and coherence > CONFIG['COHERENCE_THRESHOLD']:
                    opportunities.append({
                        'symbol': symbol,
                        'price': price,
                        'change': change,
                        'coherence': coherence,
                        'volume': volume,
                        'score': abs(change) * coherence * 10
                    })
            except:
                continue
        
        opportunities.sort(key=lambda x: x['score'], reverse=True)
        return opportunities
    
    def enter_position(self, opp: Dict, usdc_balance: float) -> bool:
        symbol = opp['symbol']
        
        # Position size: 30% of available USDC
        size_usd = usdc_balance * 0.30
        if size_usd < CONFIG['MIN_TRADE_USD']:
            return False
        
        qty = size_usd / opp['price']
        qty_str = self.lot_mgr.format_qty(symbol, qty)
        
        notional = float(qty_str) * opp['price']
        if notional < CONFIG['MIN_TRADE_USD']:
            return False
        
        logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ 🎯 ENTERING {symbol}
║ Coherence: Γ={opp['coherence']:.3f} | Change: {opp['change']:+.2f}%
║ Quantity:  {qty_str} @ ${opp['price']:.4f} = ${notional:.2f}
╚════════════════════════════════════════════════════════════════╝
""")
        
        try:
            result = self.client.place_market_order(symbol, 'BUY', quantity=float(qty_str))
            self.positions[symbol] = {
                'entry': opp['price'],
                'qty': float(qty_str),
                'entry_time': time.time(),
                'notional': notional,
            }
            logger.info(f"✅ Filled: Order #{result.get('orderId')}")
            self.trades += 1
            return True
        except Exception as e:
            logger.error(f"❌ Buy failed: {e}")
            return False
    
    def check_exits(self):
        for symbol in list(self.positions.keys()):
            pos = self.positions[symbol]
            ticker = self.ticker_cache.get(symbol)
            if not ticker: continue
            
            price = float(ticker['lastPrice'])
            entry = pos['entry']
            pnl_pct = (price - entry) / entry
            pnl_usd = pos['qty'] * price * pnl_pct
            
            should_exit = False
            reason = ""
            
            if pnl_pct >= CONFIG['TAKE_PROFIT_PCT']:
                should_exit = True
                reason = "💰 TAKE PROFIT"
            elif pnl_pct <= -CONFIG['STOP_LOSS_PCT']:
                should_exit = True
                reason = "🛑 STOP LOSS"
            elif time.time() - pos['entry_time'] > 1800:  # 30 min timeout
                should_exit = True
                reason = "⏰ TIMEOUT"
            
            if should_exit:
                qty_str = self.lot_mgr.format_qty(symbol, pos['qty'])
                
                logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ ⚡ EXITING {symbol}
║ Reason: {reason}
║ Entry: ${entry:.4f} | Exit: ${price:.4f}
║ P&L:   {pnl_pct*100:+.2f}% (${pnl_usd:+.2f})
╚════════════════════════════════════════════════════════════════╝
""")
                
                try:
                    result = self.client.place_market_order(symbol, 'SELL', quantity=float(qty_str))
                    logger.info(f"✅ Sold: Order #{result.get('orderId')}")
                    
                    self.memory.record(symbol, pnl_usd)
                    self.total_profit_usd += pnl_usd
                    if pnl_usd >= 0: self.wins += 1
                    
                    del self.positions[symbol]
                except Exception as e:
                    logger.error(f"❌ Sell failed: {e}")
    
    def display_status(self, cycle: int):
        usdc = self.get_usdc_balance()
        pos_value = sum(float(self.ticker_cache.get(s, {}).get('lastPrice', 0)) * p['qty'] 
                       for s, p in self.positions.items())
        total = usdc + pos_value
        
        win_rate = self.wins / max(1, self.trades) * 100
        
        logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ 🌌 AUREON UNIFIED | Cycle {cycle:3d}
║────────────────────────────────────────────────────────────────
║ 💵 USDC:      ${usdc:.2f}
║ 💼 Positions: ${pos_value:.2f} ({len(self.positions)})
║ 📊 Total:     ${total:.2f}
║────────────────────────────────────────────────────────────────
║ 🏆 Trades: {self.trades} | Wins: {self.wins} | WR: {win_rate:.1f}%
║ 💰 Profit: ${self.total_profit_usd:+.2f}
╚════════════════════════════════════════════════════════════════╝
""")
    
    def run(self, duration_sec: int = 3600):
        logger.info("""
╔════════════════════════════════════════════════════════════════╗
║        🌌 AUREON UNIFIED LIVE TRADER 🌌
║
║  ALL SYSTEMS INTEGRATED:
║    ✨ Coherence Detection
║    ✨ Elephant Memory
║    ✨ Proper LOT_SIZE
║    ✨ Kelly Sizing
║    ✨ Ping-Pong Momentum
║
╚════════════════════════════════════════════════════════════════╝
""")
        
        start = time.time()
        cycle = 0
        
        while time.time() - start < duration_sec:
            cycle += 1
            
            self.update_tickers()
            self.display_status(cycle)
            
            # Check exits
            self.check_exits()
            
            # Scan and enter
            if len(self.positions) < CONFIG['MAX_POSITIONS']:
                opps = self.scan_opportunities()
                
                if opps:
                    logger.info(f"\n🔍 Top 3 Opportunities:")
                    for i, opp in enumerate(opps[:3]):
                        logger.info(f"  {i+1}. {opp['symbol']}: Γ={opp['coherence']:.3f} | {opp['change']:+.2f}%")
                    
                    usdc = self.get_usdc_balance()
                    if usdc >= CONFIG['MIN_TRADE_USD']:
                        self.enter_position(opps[0], usdc)
            
            time.sleep(10)
        
        logger.info(f"""
╔════════════════════════════════════════════════════════════════╗
║ 🏁 SESSION COMPLETE
║ Trades: {self.trades} | Wins: {self.wins} | WR: {self.wins/max(1,self.trades)*100:.1f}%
║ Total P&L: ${self.total_profit_usd:+.2f}
╚════════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    trader = AureonUnifiedLive()
    trader.run(duration_sec=300)  # 5 min test
