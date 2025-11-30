#!/usr/bin/env python3
"""
AUREON MESH LIVE TRADING ENGINE
═══════════════════════════════════════════════════════════════════════════════
"Trade on Everything" - Dynamic Mesh Trading System

Strategy:
  - Scans wallet for ANY asset with balance > 0
  - Identifies all tradeable pairs for those assets (Base or Quote)
  - Applies Master Equation Λ(t) to each pair
  - High Coherence (Order) -> Move into Base Asset (BUY)
  - Low Coherence (Chaos) -> Move into Quote Asset (SELL)
  - Dynamic position sizing based on available balance

Features:
  - Wallet-aware pair discovery
  - Dynamic "Mesh" execution (Buy/Sell based on what we hold)
  - Real-time P&L tracking
  - Master Equation Coherence Gating (Γ > 0.938 Entry)

Usage:
  export CONFIRM_LIVE=yes
  python3 aureon_mesh_live.py --duration 3600

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
        logging.FileHandler('mesh_trade.log'),
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
        self.ENTRY_COHERENCE = 0.938
        self.EXIT_COHERENCE = 0.934

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
# MESH TRADER
# ═══════════════════════════════════════════════════════════════════════════════

class MeshTrader:
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.client = BinanceClient()
        self.master_eq = MasterEquation()
        self.min_notional = 10.0
        
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

    def discover_tradeable_pairs(self) -> List[Dict[str, Any]]:
        """Find all pairs we can trade based on current wallet balances."""
        logger.info("🔍 Scanning wallet for tradeable assets...")
        try:
            account = self.client.account()
            balances = {b['asset']: float(b['free']) for b in account['balances'] if float(b['free']) > 0}
            
            if not balances:
                logger.warning("⚠️  No assets found in wallet!")
                return []

            logger.info(f"💰 Wallet: {', '.join([f'{k}:{v:.4f}' for k,v in balances.items()])}")

            info = self.client.exchange_info()
            pairs = []
            
            for s in info.get('symbols', []):
                if s['status'] != 'TRADING': continue
                
                base = s['baseAsset']
                quote = s['quoteAsset']
                symbol = s['symbol']
                
                # Check if we can trade this pair
                can_buy = quote in balances and balances[quote] > 0
                can_sell = base in balances and balances[base] > 0
                
                if can_buy or can_sell:
                    pairs.append({
                        'symbol': symbol,
                        'base': base,
                        'quote': quote,
                        'can_buy': can_buy,
                        'can_sell': can_sell,
                        'quote_balance': balances.get(quote, 0.0),
                        'base_balance': balances.get(base, 0.0)
                    })
            
            logger.info(f"✅ Found {len(pairs)} tradeable pairs.")
            return pairs
        except Exception as e:
            logger.error(f"Failed to discover pairs: {e}")
            return []

    def execute_mesh_trade(self, pair: Dict, signal: str, coherence: float) -> dict:
        symbol = pair['symbol']
        try:
            price_data = self.client.best_price(symbol)
            price = float(price_data['price'])
            
            if signal == 'BUY' and pair['can_buy']:
                # Buy Base using Quote
                quote_bal = pair['quote_balance']
                # Use up to $15 worth, or all if small
                trade_amount = min(quote_bal, 15.0) # Assuming quote is roughly $1 (USDT/USDC)
                
                # If quote is NOT stablecoin, we need to be careful. 
                # Simplified: Use 10% of holding
                if pair['quote'] not in ['USDT', 'USDC', 'BUSD', 'DAI']:
                     trade_amount = quote_bal * 0.1
                
                if trade_amount < 0.00001: return {} # Too small

                if self.dry_run:
                    logger.info(f"📝 DRY-RUN: BUY {symbol} with {trade_amount:.4f} {pair['quote']} (Γ={coherence:.4f})")
                    return {'dry_run': True}
                
                logger.info(f"🚀 LIVE: BUY {symbol} with {trade_amount:.4f} {pair['quote']} (Γ={coherence:.4f})")
                return self.client.place_market_order(symbol, 'BUY', quote_qty=trade_amount)

            elif signal == 'SELL' and pair['can_sell']:
                # Sell Base for Quote
                base_bal = pair['base_balance']
                # Sell 20% of holding
                trade_amount = base_bal * 0.2
                
                if trade_amount < 0.00001: return {}

                if self.dry_run:
                    logger.info(f"📝 DRY-RUN: SELL {trade_amount:.4f} {pair['base']} (Γ={coherence:.4f})")
                    return {'dry_run': True}
                    
                logger.info(f"🚀 LIVE: SELL {trade_amount:.4f} {pair['base']} (Γ={coherence:.4f})")
                return self.client.place_market_order(symbol, 'SELL', quantity=trade_amount)
                
        except Exception as e:
            logger.error(f"❌ Trade failed for {symbol}: {e}")
            return {'error': str(e)}
        return {}

    def run(self, duration_sec: int = 3600):
        logger.info(f"\n🚀 Starting MESH trading for {duration_sec}s...")
        start_time = time.time()
        cycle = 0
        
        while time.time() - start_time < duration_sec:
            cycle += 1
            logger.info(f"\n🔄 Cycle {cycle} ({int(time.time() - start_time)}s elapsed)")
            
            pairs = self.discover_tradeable_pairs()
            random.shuffle(pairs)
            
            # Check top 20 pairs to avoid rate limits
            for pair in pairs[:20]:
                symbol = pair['symbol']
                snapshot = self.get_market_snapshot(symbol)
                if not snapshot: continue
                
                state = self.master_eq.compute_lambda(symbol, snapshot)
                coherence = state['coherence']
                
                if state['entry_signal'] and pair['can_buy']:
                    logger.info(f"🎯 {symbol}: BUY Signal (Γ={coherence:.4f})")
                    self.execute_mesh_trade(pair, 'BUY', coherence)
                    
                elif state['exit_signal'] and pair['can_sell']:
                    logger.info(f"🚪 {symbol}: SELL Signal (Γ={coherence:.4f})")
                    self.execute_mesh_trade(pair, 'SELL', coherence)
            
            time.sleep(5)

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
    
    trader = MeshTrader(dry_run=args.dry_run)
    trader.run(duration_sec=args.duration)

if __name__ == "__main__":
    main()
