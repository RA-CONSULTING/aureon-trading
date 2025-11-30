#!/usr/bin/env python3
"""
AUREON PROFIT-NOW TRADER
═══════════════════════════════════════════════════════════════════════════════
"Simple aggressive profits after fees"

Strategy:
  - Use LDUSDC as primary quote (largest holding at $40)
  - BUY on coherence > 0.85 (lower than original 0.938)
  - SELL after 1.5% profit (covers 0.2% fees + 1.3% net)
  - SELL after 60s max hold time
  - $5-10 per trade from LDUSDC balance
  
Features:
  - Position tracking with entry prices
  - Automatic profit-taking
  - Time-based exits

Usage:
  export CONFIRM_LIVE=yes
  python3 aureon_profit_now.py --duration 3600

Author: Aureon System / Gary Leckey
Date: November 28, 2025
"""
import os, sys, json, time, logging, argparse, random
from datetime import datetime
from typing import List, Dict, Any
from binance_client import BinanceClient

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('profit_now.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# 9 AURIS NODES
# ═══════════════════════════════════════════════════════════════════════════════

class AurisNode:
    def __init__(self, name: str, fn, weight: float):
        self.name = name
        self.fn = fn
        self.weight = weight

    def compute(self, data: dict) -> float:
        try:
            return self.fn(data) * self.weight
        except:
            return 0.0

def create_auris_nodes():
    import math
    nodes = {
        'tiger': AurisNode('tiger', 
            lambda d: ((d['high'] - d['low']) / d['price']) * 100 + (0.2 if d['volume'] > 1000000 else 0), 1.2),
        'falcon': AurisNode('falcon',
            lambda d: abs(d['change']) * 0.7 + min(d['volume'] / 10000000, 0.3), 1.1),
        'hummingbird': AurisNode('hummingbird',
            lambda d: 1 / (1 + ((d['high'] - d['low']) / d['price']) * 10), 0.9),
        'dolphin': AurisNode('dolphin',
            lambda d: math.sin(d['change'] * math.pi / 10) * 0.5 + 0.5, 1.0),
        'deer': AurisNode('deer',
            lambda d: (0.6 if d['price'] > d['open'] else 0.4) + (0.2 if d['change'] > 0 else -0.1), 0.8),
        'owl': AurisNode('owl',
            lambda d: math.cos(d['change'] * math.pi / 10) * 0.3 + (0.3 if d['price'] < d['open'] else 0), 0.9),
        'panda': AurisNode('panda',
            lambda d: 0.5 + math.sin(time.time() / 60000) * 0.1, 0.7),
        'cargoship': AurisNode('cargoship',
            lambda d: 0.8 if d['volume'] > 5000000 else (0.5 if d['volume'] > 1000000 else 0.3), 1.0),
        'clownfish': AurisNode('clownfish',
            lambda d: abs(d['price'] - d['open']) / d['price'] * 100, 0.7),
    }
    return nodes

# ═══════════════════════════════════════════════════════════════════════════════
# MASTER EQUATION
# ═══════════════════════════════════════════════════════════════════════════════

class MasterEquation:
    def __init__(self):
        self.auris_nodes = create_auris_nodes()
        self.lambda_history = {}
        self.OBSERVER_WEIGHT = 0.3
        self.ECHO_WEIGHT = 0.2
        self.ENTRY_COHERENCE = 0.50  # VERY LOW for aggressive action
        self.EXIT_COHERENCE = 0.45

    def compute_substrate(self, market_data: dict) -> float:
        total = 0.0
        weight_sum = 0.0
        for node in self.auris_nodes.values():
            val = node.compute(market_data)
            total += val
            weight_sum += node.weight
        return total / weight_sum if weight_sum > 0 else 0.0

    def compute_echo(self, symbol: str) -> float:
        if symbol not in self.lambda_history or len(self.lambda_history[symbol]) == 0:
            return 0.0
        recent = self.lambda_history[symbol][-5:]
        decay = sum(v * (0.9 ** i) for i, v in enumerate(reversed(recent)))
        return decay / len(recent) * self.ECHO_WEIGHT

    def compute_lambda(self, symbol: str, market_data: dict) -> dict:
        if symbol not in self.lambda_history:
            self.lambda_history[symbol] = []
        
        s_t = self.compute_substrate(market_data)
        o_t = self.lambda_history[symbol][-1] * self.OBSERVER_WEIGHT if self.lambda_history[symbol] else 0.0
        e_t = self.compute_echo(symbol)
        lambda_t = s_t + o_t + e_t
        self.lambda_history[symbol].append(lambda_t)
        
        # Coherence Γ
        variance = max(abs(market_data['high'] - market_data['low']) / market_data['price'], 0.001)
        coherence = max(1 - (variance / 10), 0.0)
        
        return {
            'lambda': lambda_t,
            'coherence': coherence,
            'entry_signal': coherence > self.ENTRY_COHERENCE,
            'exit_signal': coherence < self.EXIT_COHERENCE,
        }

# ═══════════════════════════════════════════════════════════════════════════════
# PROFIT TRADER
# ═══════════════════════════════════════════════════════════════════════════════

class ProfitTrader:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = BinanceClient()
        self.master_eq = MasterEquation()
        self.positions = {}  # symbol -> {'entry_price': float, 'quantity': float, 'entry_time': float, 'quote_spent': float}
        self.TARGET_PROFIT_PCT = 0.35  # 0.35% target (0.2% fees + 0.15% net) - MINIMAL BUT POSITIVE
        self.MAX_HOLD_TIME = 120  # 120s max hold - LONGER FOR PROFIT
        self.TRADE_SIZE_BTC = 0.0001  # ~$9 per trade in BTC - LARGER for better fee ratio
        self.MAX_POSITIONS = 3  # Fewer but larger positions
        self.total_profit = 0.0
        
    def get_market_snapshot(self, symbol: str) -> dict:
        try:
            ticker = self.client.session.get(
                f"{self.client.base}/api/v3/ticker/24hr",
                params={'symbol': symbol}
            ).json()
            return {
                'symbol': symbol,
                'price': float(ticker['lastPrice']),
                'volume': float(ticker['volume']),
                'high': float(ticker['highPrice']),
                'low': float(ticker['lowPrice']),
                'open': float(ticker['openPrice']),
                'change': float(ticker['priceChangePercent']),
            }
        except:
            return None

    def get_btc_pairs(self) -> List[str]:
        """Find all BTC pairs."""
        try:
            info = self.client.exchange_info()
            pairs = []
            for s in info.get('symbols', []):
                if s['status'] == 'TRADING' and s['quoteAsset'] == 'BTC':
                    pairs.append(s['symbol'])
            logger.info(f"✅ Found {len(pairs)} BTC pairs")
            return pairs
        except Exception as e:
            logger.error(f"Failed to fetch pairs: {e}")
            return []

    def check_exit_conditions(self):
        """Check all positions for profit targets or time exits."""
        current_time = time.time()
        symbols_to_exit = []
        
        for symbol, pos in self.positions.items():
            try:
                snapshot = self.get_market_snapshot(symbol)
                if not snapshot: continue
                
                current_price = snapshot['price']
                entry_price = pos['entry_price']
                profit_pct = ((current_price - entry_price) / entry_price) * 100
                hold_time = current_time - pos['entry_time']
                
                # Check profit target
                if profit_pct >= self.TARGET_PROFIT_PCT:
                    logger.info(f"💰 {symbol}: Profit target hit! {profit_pct:.2f}% > {self.TARGET_PROFIT_PCT}%")
                    symbols_to_exit.append(symbol)
                    
                # Check max hold time
                elif hold_time >= self.MAX_HOLD_TIME:
                    logger.info(f"⏰ {symbol}: Max hold time reached ({hold_time:.0f}s). Profit: {profit_pct:.2f}%")
                    symbols_to_exit.append(symbol)
                    
            except Exception as e:
                logger.error(f"Error checking {symbol}: {e}")
        
        # Execute exits
        for symbol in symbols_to_exit:
            self.exit_position(symbol)

    def exit_position(self, symbol: str):
        """Sell position."""
        if symbol not in self.positions:
            return
            
        pos = self.positions[symbol]
        try:
            snapshot = self.get_market_snapshot(symbol)
            current_price = snapshot['price'] if snapshot else pos['entry_price']
            
            # Calculate P&L
            quote_value = pos['quantity'] * current_price
            pnl = quote_value - pos['quote_spent']
            pnl_pct = (pnl / pos['quote_spent']) * 100
            self.total_profit += pnl
            
            if self.dry_run:
                logger.info(f"📝 DRY-RUN: SELL {pos['quantity']:.6f} {symbol.replace('LDUSDC', '')} @ {current_price:.6f} | P&L: ${pnl:.4f} ({pnl_pct:.2f}%)")
            else:
                logger.info(f"🚀 LIVE SELL: {pos['quantity']:.6f} {symbol.replace('LDUSDC', '')} @ {current_price:.6f}")
                result = self.client.place_market_order(symbol, 'SELL', quantity=pos['quantity'])
                logger.info(f"💵 P&L: ${pnl:.4f} ({pnl_pct:.2f}%) | Total: ${self.total_profit:.2f}")
                
            del self.positions[symbol]
            
        except Exception as e:
            logger.error(f"❌ Exit failed for {symbol}: {e}")

    def enter_position(self, symbol: str, coherence: float):
        """Enter new position."""
        if len(self.positions) >= self.MAX_POSITIONS:
            return
            
        try:
            snapshot = self.get_market_snapshot(symbol)
            if not snapshot: return
            
            entry_price = snapshot['price']
            quote_to_spend = self.TRADE_SIZE_BTC
            
            if self.dry_run:
                quantity = quote_to_spend / entry_price
                logger.info(f"📝 DRY-RUN: BUY {symbol} with {quote_to_spend:.8f} BTC @ {entry_price:.8f} (Γ={coherence:.4f})")
                self.positions[symbol] = {
                    'entry_price': entry_price,
                    'quantity': quantity,
                    'entry_time': time.time(),
                    'quote_spent': quote_to_spend
                }
            else:
                logger.info(f"🚀 LIVE BUY: {symbol} with {quote_to_spend:.8f} BTC @ {entry_price:.8f} (Γ={coherence:.4f})")
                result = self.client.place_market_order(symbol, 'BUY', quote_qty=quote_to_spend)
                logger.info(f"📋 Order result: {result}")
                
                # Extract actual filled quantity
                filled_qty = float(result.get('executedQty', 0))
                filled_quote = float(result.get('cummulativeQuoteQty', quote_to_spend))
                
                self.positions[symbol] = {
                    'entry_price': filled_quote / filled_qty if filled_qty > 0 else entry_price,
                    'quantity': filled_qty,
                    'entry_time': time.time(),
                    'quote_spent': filled_quote
                }
                
        except Exception as e:
            logger.error(f"❌ Entry failed for {symbol}: {e}")

    def run(self, duration_sec: int = 3600):
        logger.info(f"\n🚀 Starting PROFIT trading for {duration_sec}s...")
        logger.info(f"💡 Strategy: Entry Γ>{self.master_eq.ENTRY_COHERENCE}, Profit>{self.TARGET_PROFIT_PCT}%, MaxHold={self.MAX_HOLD_TIME}s, Size={self.TRADE_SIZE_BTC} BTC")
        
        start_time = time.time()
        cycle = 0
        
        # Get BTC pairs once
        btc_pairs = self.get_btc_pairs()
        if not btc_pairs:
            logger.error("❌ No BTC pairs found!")
            return
        
        while time.time() - start_time < duration_sec:
            cycle += 1
            elapsed = int(time.time() - start_time)
            logger.info(f"\n🔄 Cycle {cycle} ({elapsed}s) | Positions: {len(self.positions)}/{self.MAX_POSITIONS} | Profit: ${self.total_profit:+.2f}")
            
            # Check exits first
            self.check_exit_conditions()
            
            # Look for entries if we have room
            if len(self.positions) < self.MAX_POSITIONS:
                # Randomly check 15 pairs per cycle
                check_pairs = random.sample(btc_pairs, min(15, len(btc_pairs)))
                
                for symbol in check_pairs:
                    if symbol in self.positions: continue
                    
                    snapshot = self.get_market_snapshot(symbol)
                    if not snapshot: continue
                    
                    state = self.master_eq.compute_lambda(symbol, snapshot)
                    
                    if state['entry_signal']:
                        logger.info(f"🎯 {symbol}: BUY Signal (Γ={state['coherence']:.4f})")
                        self.enter_position(symbol, state['coherence'])
                        break  # One entry per cycle
            
            time.sleep(3)
        
        # Exit all remaining positions
        logger.info("\n⏰ Duration ended, closing all positions...")
        for symbol in list(self.positions.keys()):
            self.exit_position(symbol)
        
        logger.info(f"\n🏁 Final Profit: ${self.total_profit:+.2f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--duration', type=int, default=3600)
    args = parser.parse_args()
    
    if not args.dry_run:
        if os.getenv('CONFIRM_LIVE', '').lower() != 'yes':
            logger.error("❌ Set CONFIRM_LIVE=yes for live trading")
            sys.exit(1)
        logger.warning("⚠️  LIVE TRADING MODE - Real capital at risk!")
    
    trader = ProfitTrader(dry_run=args.dry_run)
    trader.run(duration_sec=args.duration)

if __name__ == "__main__":
    main()
