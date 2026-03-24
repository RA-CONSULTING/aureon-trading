from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import json
import random
import os
import logging
from typing import Dict, List, Any
from unified_exchange_client import MultiExchangeClient
from aureon_market_pulse import MarketPulse

logger = logging.getLogger(__name__)

class WarBand:
    """
    🏹⚔️ THE APACHE WAR BAND ⚔️🏹
    
    Autonomous Scout and Sniper unit that operates independently within the ecosystem.
    
    Components:
    - SCOUT (The Hunter): Finds targets based on metrics and deploys capital.
    - SNIPER (The Killer): Watches positions and executes kills for profit.
    
    🧬 ENHANCED: Consumes Mycelium neural outputs for smarter target selection.
    """
    
    def __init__(self, client: MultiExchangeClient, market_pulse: MarketPulse):
        self.client = client
        self.pulse = market_pulse
        self.state_file = 'aureon_kraken_state.json'
        self.external_intel: Dict[str, Dict[str, Any]] = {}
        # Mycelium reference (set by ecosystem wiring)
        self._mycelium = None
        
        # Configuration
        self.scout_size_usd = 12.0
        self.min_cash_required = 15.0
        self.scan_interval = 45
        self.last_scan_time = 0
        
        # War List (Fallback)
        self.fallback_targets = {
            'kraken': ['SOLUSD', 'ADAUSD', 'DOTUSD', 'LINKUSD', 'XRPUSD', 'XXBTZUSD', 'XETHZUSD', 'MATICUSD', 'DOGEUSD'],
            'binance': ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT', 'XRPUSDT'],
            'alpaca': ['BTC/USD', 'ETH/USD']
        }
        
        print("   🏹 War Band Assembled: Scouts & Snipers Ready")

    def set_mycelium(self, mycelium) -> None:
        """Wire Mycelium reference for neural-guided targeting."""
        self._mycelium = mycelium

    def _neural_target_score(self, symbol: str, exchange: str) -> float:
        """Get neural score for a target (higher = better)."""
        if self._mycelium is None:
            return 1.0
        try:
            mem = self._mycelium.get_symbol_memory(symbol)
            friction = self._mycelium.get_exchange_friction(exchange)
            queen = self._mycelium.get_queen_signal()
            coherence = self._mycelium.get_network_coherence()
            
            wr = float(mem.get('win_rate', 0.5))
            act = float(mem.get('activation', 0.5))
            # Penalize exchanges with high recent rejections
            friction_penalty = 1.0 - min(0.5, friction.get('reject_count', 0) * 0.05)
            # Bullish queen + high coherence = boost
            queen_factor = 1.0 + 0.15 * queen
            coh_factor = 0.6 + 0.4 * coherence
            
            return wr * act * friction_penalty * queen_factor * coh_factor
        except Exception:
            return 1.0

    def ingest_intel(self, symbol: str, exchange: str, eta_seconds: float = None,
                     probability: float = None, confidence: float = None,
                     mycelium_coherence: float = None, queen_signal: float = None):
        """Record external sniper/mycelium intel so the band has situational awareness."""
        key = f"{exchange}:{symbol}"
        self.external_intel[key] = {
            'ts': time.time(),
            'eta_seconds': eta_seconds,
            'probability': probability,
            'confidence': confidence,
            'mycelium_coherence': mycelium_coherence,
            'queen_signal': queen_signal,
        }

    def get_state(self) -> Dict:
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            return {'positions': {}, 'kills': []}
        except:
            return {'positions': {}, 'kills': []}

    def save_state(self, state: Dict):
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def update(self):
        """Main update loop called by the ecosystem"""
        current_time = time.time()
        
        # Run Sniper (Every update)
        self._run_sniper()

        # Light-touch intel decay to keep the cache fresh
        stale = [k for k, v in self.external_intel.items() if current_time - v.get('ts', 0) > 900]
        for k in stale:
            self.external_intel.pop(k, None)
        
        # Run Scout (Interval based)
        if current_time - self.last_scan_time > self.scan_interval:
            self._run_scout()
            self.last_scan_time = current_time

    def _run_sniper(self):
        """The Killer: Checks for profit and executes kills"""
        state = self.get_state()
        positions = state.get('positions', {})
        
        if not positions:
            return

        # Check each position
        for symbol, pos in list(positions.items()):
            try:
                exchange = pos.get('exchange', 'kraken')
                qty = float(pos.get('quantity', 0))
                entry_value = float(pos.get('entry_value', 0))
                
                # Get current price
                ticker = self.client.get_ticker(exchange, symbol)
                if not ticker: continue
                
                current_price = float(ticker.get('price', 0))
                if current_price <= 0: continue
                
                current_value = qty * current_price
                
                # Calculate P&L
                # Fees: 0.26% taker * 2 (entry+exit) + slippage buffer
                fees = entry_value * 0.006 
                gross_pnl = current_value - entry_value
                net_pnl = gross_pnl - fees
                
                # KILL CONDITION: Net Profit >= $0.01
                if net_pnl >= 0.0001:
                    print(f"   🔫 SNIPER: Target Acquired {symbol} (+${net_pnl:.4f})")
                    self._execute_kill(exchange, symbol, qty, entry_value, current_value, net_pnl, state)
                    
            except Exception as e:
                pass

    def _execute_kill(self, exchange, symbol, qty, entry_val, exit_val, pnl, state):
        try:
            print(f"   💥 FIRING: Selling {symbol} on {exchange}...")
            result = self.client.place_market_order(exchange, symbol, 'SELL', quantity=qty)
            
            if result and not result.get('error') and not result.get('rejected'):
                order_id = result.get('txid') or result.get('orderId') or result.get('id')
                print(f"   ✅ KILL CONFIRMED! Order: {order_id} | Profit: ${pnl:.4f}")
                
                # Remove from state
                if symbol in state['positions']:
                    del state['positions'][symbol]
                
                # Record kill
                if 'kills' not in state: state['kills'] = []
                state['kills'].append({
                    'symbol': symbol,
                    'exchange': exchange,
                    'time': time.time(),
                    'net_pnl': pnl,
                    'order_id': order_id
                })
                self.save_state(state)
            else:
                reason = result.get('reason', result.get('error', 'Unknown'))
                if 'cancel_only' in str(reason):
                    print(f"   🔒 Market Locked for {symbol}")
                else:
                    print(f"   ❌ Kill Failed: {reason}")
                    
        except Exception as e:
            print(f"   ❌ Sniper Error: {e}")

    def _run_scout(self):
        """The Hunter: Finds targets and deploys capital"""
        try:
            # 1. Load State
            state = self.get_state()
            current_positions = state.get('positions', {})
            held_symbols = [p.get('symbol') for p in current_positions.values()]
            
            # 2. Analyze Market
            market_data = self.pulse.analyze_market()
            top_gainers = market_data.get('top_gainers', [])
            arb_opps = market_data.get('arbitrage_opportunities', [])
            
            # 3. Check Cash & Deploy
            balances = self.client.get_all_balances()
            
            for exchange in ['kraken', 'binance', 'alpaca']:
                cash = self._get_cash(exchange, balances)
                
                if cash >= self.min_cash_required:
                    target, reason = self._select_target(exchange, held_symbols, top_gainers, arb_opps)

                    # Prefer externally-intel'd targets if available and not held
                    ext_key = None
                    for k in sorted(self.external_intel.keys()):
                        if k.startswith(f"{exchange}:"):
                            sym = k.split(":", 1)[1]
                            if sym not in held_symbols:
                                target = sym
                                intel = self.external_intel[k]
                                reason = f"External intel p={intel.get('probability', 'na')} eta={intel.get('eta_seconds', 'na')}"
                                ext_key = k
                                break
                    
                    if target:
                        self._deploy_scout(exchange, target, reason, state)
                        if ext_key:
                            self.external_intel.pop(ext_key, None)
                    
        except Exception as e:
            print(f"   ⚠️ Scout Patrol Error: {e}")

    def _get_cash(self, exchange, balances):
        if exchange == 'kraken':
            return float(balances.get('kraken', {}).get('ZUSD', {}).get('free', 0) if isinstance(balances.get('kraken', {}).get('ZUSD'), dict) else balances.get('kraken', {}).get('ZUSD', 0))
        elif exchange == 'binance':
            cash = float(balances.get('binance', {}).get('USDC', {}).get('free', 0) if isinstance(balances.get('binance', {}).get('USDC'), dict) else balances.get('binance', {}).get('USDC', 0))
            if cash < self.scout_size_usd:
                usdt = float(balances.get('binance', {}).get('USDT', {}).get('free', 0) if isinstance(balances.get('binance', {}).get('USDT'), dict) else balances.get('binance', {}).get('USDT', 0))
                if usdt > cash: return usdt
            return cash
        elif exchange == 'alpaca':
            return float(balances.get('alpaca', {}).get('USD', {}).get('free', 0) if isinstance(balances.get('alpaca', {}).get('USD'), dict) else balances.get('alpaca', {}).get('USD', 0))
        return 0.0

    def _select_target(self, exchange, held_symbols, top_gainers, arb_opps):
        # 1. Arbitrage (score-weighted if multiple)
        arb_candidates = [arb for arb in arb_opps if arb['buy_at']['source'] == exchange and arb['buy_at']['symbol'] not in held_symbols]
        if arb_candidates:
            # Pick the one with best neural score
            arb_candidates.sort(key=lambda a: self._neural_target_score(a['buy_at']['symbol'], exchange), reverse=True)
            best = arb_candidates[0]
            return best['buy_at']['symbol'], f"Arbitrage (+{best['spread_pct']:.2f}%)"
        
        # 2. Momentum (score-weighted)
        exch_gainers = [t for t in top_gainers if t.get('source') == exchange and t.get('symbol') not in held_symbols]
        if exch_gainers:
            exch_gainers.sort(key=lambda t: self._neural_target_score(t.get('symbol', ''), exchange), reverse=True)
            best = exch_gainers[0]
            return best.get('symbol'), f"Top Gainer (+{best.get('priceChangePercent', 0)}%)"
            
        # 3. Fallback (score-weighted)
        available = [t for t in self.fallback_targets.get(exchange, []) if t not in held_symbols]
        if available:
            available.sort(key=lambda t: self._neural_target_score(t, exchange), reverse=True)
            return available[0], "Neural Patrol"
            
        return None, None

    def _deploy_scout(self, exchange, target, reason, state):
        print(f"   🏹 SCOUT: Deploying to {target} on {exchange} ({reason})")
        
        ticker = self.client.get_ticker(exchange, target)
        price = float(ticker.get('price', 0))
        
        if price > 0:
            qty = self.scout_size_usd / price
            result = self.client.place_market_order(exchange, target, 'BUY', quote_qty=self.scout_size_usd)
            
            if result and not result.get('error') and not result.get('rejected'):
                order_id = result.get('txid') or result.get('orderId') or result.get('id')
                print(f"      ✅ DEPLOYED! Order: {order_id}")
                
                state['positions'][target] = {
                    'symbol': target,
                    'exchange': exchange,
                    'entry_price': price,
                    'quantity': qty,
                    'entry_value': self.scout_size_usd,
                    'entry_time': time.time(),
                    'is_scout': True,
                    'strategy': reason
                }
                self.save_state(state)
            else:
                print(f"      ❌ Failed: {result.get('error')}")
