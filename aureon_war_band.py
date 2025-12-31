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
    """
    
    def __init__(self, client: MultiExchangeClient, market_pulse: MarketPulse):
        self.client = client
        self.pulse = market_pulse
        self.state_file = 'aureon_kraken_state.json'
        
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
                if net_pnl >= 0.01:
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
                    
                    if target:
                        self._deploy_scout(exchange, target, reason, state)
                    
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
        # 1. Arbitrage
        for arb in arb_opps:
            if arb['buy_at']['source'] == exchange and arb['buy_at']['symbol'] not in held_symbols:
                return arb['buy_at']['symbol'], f"Arbitrage (+{arb['spread_pct']:.2f}%)"
        
        # 2. Momentum
        exch_gainers = [t for t in top_gainers if t.get('source') == exchange and t.get('symbol') not in held_symbols]
        if exch_gainers:
            best = exch_gainers[0]
            return best.get('symbol'), f"Top Gainer (+{best.get('priceChangePercent', 0)}%)"
            
        # 3. Fallback
        available = [t for t in self.fallback_targets.get(exchange, []) if t not in held_symbols]
        if available:
            return random.choice(available), "Standard Patrol"
            
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
