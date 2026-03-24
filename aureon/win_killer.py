#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                          WIN KILLER - BY ANY MEANS                             ║
║                     No Mercy. No Hesitation. Only Wins.                       ║
╚═══════════════════════════════════════════════════════════════════════════════╝

MISSION: Execute winning trades by any means necessary
STRATEGY: Find the hottest momentum, arb, or bounce plays and EXECUTE
MODE: KILL

Author: Aureon Trading System
"""

import os
import sys
import json
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_DOWN

# Windows UTF-8 wrapper
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WinConfig:
    """Configuration for the WIN KILLER"""
    min_win_score: float = 3.0          # Minimum score to consider
    min_volume_usd: float = 1_000_000   # Minimum 24h volume
    max_position_pct: float = 0.10      # Max 10% of portfolio per trade
    stop_loss_pct: float = 0.03         # 3% stop loss
    take_profit_pct: float = 0.05       # 5% take profit
    min_risk_reward: float = 1.5        # Minimum R:R ratio
    scan_interval: int = 10             # Seconds between scans
    dry_run: bool = False               # Set False for LIVE FIRE


@dataclass
class Opportunity:
    """A trading opportunity"""
    symbol: str
    exchange: str
    type: str  # MOMENTUM, ARBITRAGE, BOUNCE, ACCUMULATION
    price: float
    change_24h: float
    volume_24h: float
    score: float
    entry: float
    target: float
    stop: float
    risk_reward: float
    timestamp: str


class KrakenExecutor:
    """Execute trades on Kraken - NO MERCY"""
    
    def __init__(self):
        self.api_key = os.getenv('KRAKEN_API_KEY', '')
        self.api_secret = os.getenv('KRAKEN_API_SECRET', '')
        self.base_url = 'https://api.kraken.com'
        self.wins = []
        self.losses = []
        self.total_pnl = 0.0
        
    def _signature(self, urlpath: str, data: dict) -> str:
        """Generate Kraken API signature"""
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()
        mac = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        return base64.b64encode(mac.digest()).decode()
    
    def _private_request(self, endpoint: str, data: dict = None) -> dict:
        """Make authenticated request to Kraken"""
        if not self.api_key or not self.api_secret:
            return {'error': ['No API credentials']}
        
        url = f'{self.base_url}{endpoint}'
        if data is None:
            data = {}
        data['nonce'] = int(time.time() * 1000)
        
        headers = {
            'API-Key': self.api_key,
            'API-Sign': self._signature(endpoint, data)
        }
        
        try:
            resp = requests.post(url, headers=headers, data=data, timeout=30)
            return resp.json()
        except Exception as e:
            return {'error': [str(e)]}
    
    def get_balance(self) -> Dict[str, float]:
        """Get current balance"""
        result = self._private_request('/0/private/Balance')
        if 'result' in result:
            return {k: float(v) for k, v in result['result'].items() if float(v) > 0}
        return {}
    
    def get_ticker(self, pair: str) -> Optional[Dict]:
        """Get ticker for a pair"""
        try:
            url = f'{self.base_url}/0/public/Ticker'
            resp = requests.get(url, params={'pair': pair}, timeout=10)
            data = resp.json()
            if 'result' in data and data['result']:
                key = list(data['result'].keys())[0]
                t = data['result'][key]
                return {
                    'bid': float(t['b'][0]),
                    'ask': float(t['a'][0]),
                    'last': float(t['c'][0]),
                    'volume': float(t['v'][1])
                }
        except:
            pass
        return None
    
    def execute_market_buy(self, pair: str, volume: float, dry_run: bool = True) -> Dict:
        """Execute market buy order"""
        if dry_run:
            return {
                'dry_run': True,
                'pair': pair,
                'type': 'buy',
                'volume': volume,
                'status': 'WOULD_EXECUTE'
            }
        
        data = {
            'pair': pair,
            'type': 'buy',
            'ordertype': 'market',
            'volume': str(volume)
        }
        
        result = self._private_request('/0/private/AddOrder', data)
        return result
    
    def execute_market_sell(self, pair: str, volume: float, dry_run: bool = True) -> Dict:
        """Execute market sell order"""
        if dry_run:
            return {
                'dry_run': True,
                'pair': pair,
                'type': 'sell',
                'volume': volume,
                'status': 'WOULD_EXECUTE'
            }
        
        data = {
            'pair': pair,
            'type': 'sell',
            'ordertype': 'market',
            'volume': str(volume)
        }
        
        result = self._private_request('/0/private/AddOrder', data)
        return result


class WinScanner:
    """Scan for winning opportunities across exchanges"""
    
    def __init__(self, config: WinConfig):
        self.config = config
        
    def scan_binance(self) -> List[Dict]:
        """Scan Binance for opportunities"""
        opportunities = []
        
        try:
            url = 'https://api.binance.com/api/v3/ticker/24hr'
            resp = requests.get(url, timeout=30)
            tickers = resp.json()
            
            usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
            
            for t in usdt_pairs:
                try:
                    change = float(t.get('priceChangePercent', 0))
                    volume = float(t.get('quoteVolume', 0))
                    price = float(t.get('lastPrice', 0))
                    high = float(t.get('highPrice', 0))
                    low = float(t.get('lowPrice', 0))
                    
                    if volume < self.config.min_volume_usd:
                        continue
                    
                    # Calculate opportunity score
                    score = self._calculate_score(change, volume, price, high, low)
                    
                    if score >= self.config.min_win_score:
                        op_type = self._determine_type(change, price, high, low)
                        entry, target, stop = self._calculate_levels(price, op_type, high, low)
                        rr = (target - entry) / (entry - stop) if entry > stop else 0
                        
                        if rr >= self.config.min_risk_reward:
                            opportunities.append({
                                'symbol': t['symbol'],
                                'exchange': 'binance',
                                'type': op_type,
                                'price': price,
                                'change_24h': change,
                                'volume_24h': volume,
                                'score': score,
                                'entry': entry,
                                'target': target,
                                'stop': stop,
                                'risk_reward': rr
                            })
                except:
                    continue
                    
        except Exception as e:
            print(f'   ❌ Binance scan error: {e}')
        
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)
    
    def scan_kraken(self) -> List[Dict]:
        """Scan Kraken for opportunities"""
        opportunities = []
        
        # Top Kraken pairs
        pairs = ['XBTUSD', 'ETHUSD', 'SOLUSD', 'DOTUSD', 'LINKUSD', 'MATICUSD', 
                 'AVAXUSD', 'ATOMUSD', 'UNIUSD', 'AAVEUSD', 'WLDUSD']
        
        try:
            url = 'https://api.kraken.com/0/public/Ticker'
            resp = requests.get(url, params={'pair': ','.join(pairs)}, timeout=10)
            data = resp.json()
            
            if 'result' in data:
                for pair, t in data['result'].items():
                    try:
                        price = float(t['c'][0])
                        high = float(t['h'][1])  # 24h high
                        low = float(t['l'][1])   # 24h low
                        volume = float(t['v'][1]) * price  # Volume in USD
                        
                        if high > 0 and low > 0:
                            change = ((price - low) / low - (high - price) / high) * 100
                        else:
                            change = 0
                        
                        score = self._calculate_score(change, volume, price, high, low)
                        
                        if score >= self.config.min_win_score * 0.5:  # Lower threshold for Kraken
                            op_type = self._determine_type(change, price, high, low)
                            entry, target, stop = self._calculate_levels(price, op_type, high, low)
                            rr = (target - entry) / (entry - stop) if entry > stop else 0
                            
                            opportunities.append({
                                'symbol': pair,
                                'exchange': 'kraken',
                                'type': op_type,
                                'price': price,
                                'change_24h': change,
                                'volume_24h': volume,
                                'score': score,
                                'entry': entry,
                                'target': target,
                                'stop': stop,
                                'risk_reward': max(rr, 1.0)
                            })
                    except:
                        continue
                        
        except Exception as e:
            print(f'   ❌ Kraken scan error: {e}')
        
        return sorted(opportunities, key=lambda x: x['score'], reverse=True)
    
    def _calculate_score(self, change: float, volume: float, price: float, 
                         high: float, low: float) -> float:
        """Calculate opportunity score"""
        # Momentum score (0-3 points)
        momentum = max(0, change / 7)  # +21% = 3 points
        
        # Volume score (0-2 points)
        vol_score = min(2, volume / 50_000_000)
        
        # Bounce score (0-2 points) - for oversold with recovery
        if change < -10 and price > low * 1.02:
            bounce = (price - low) / (high - low) if high > low else 0
            bounce_score = bounce * 2
        else:
            bounce_score = 0
        
        # Breakout score (0-1 point) - near highs
        if high > 0 and price > high * 0.95:
            breakout_score = 1.0
        else:
            breakout_score = 0
        
        return momentum + vol_score + bounce_score + breakout_score
    
    def _determine_type(self, change: float, price: float, high: float, low: float) -> str:
        """Determine opportunity type"""
        if change > 10:
            return 'MOMENTUM'
        elif change < -10 and price > low * 1.02:
            return 'BOUNCE'
        elif abs(change) < 3:
            return 'ACCUMULATION'
        else:
            return 'SWING'
    
    def _calculate_levels(self, price: float, op_type: str, 
                          high: float, low: float) -> Tuple[float, float, float]:
        """Calculate entry, target, and stop levels"""
        entry = price
        
        if op_type == 'MOMENTUM':
            target = price * 1.05  # 5% target
            stop = price * 0.97    # 3% stop
        elif op_type == 'BOUNCE':
            target = price + (high - price) * 0.5  # 50% retracement
            stop = low * 0.98
        else:
            target = price * 1.03
            stop = price * 0.98
        
        return entry, target, stop


class WinKiller:
    """The main WIN KILLER engine"""
    
    def __init__(self, config: WinConfig = None):
        self.config = config or WinConfig()
        self.scanner = WinScanner(self.config)
        self.executor = KrakenExecutor()
        self.active_positions = []
        self.completed_trades = []
        self.total_pnl = 0.0
        
    def hunt(self) -> List[Opportunity]:
        """Hunt for winning opportunities"""
        all_opportunities = []
        
        # Scan all exchanges
        binance_ops = self.scanner.scan_binance()
        kraken_ops = self.scanner.scan_kraken()
        
        # Combine and sort
        all_opportunities = binance_ops + kraken_ops
        all_opportunities.sort(key=lambda x: x['score'], reverse=True)
        
        # Convert to Opportunity objects
        return [
            Opportunity(
                symbol=op['symbol'],
                exchange=op['exchange'],
                type=op['type'],
                price=op['price'],
                change_24h=op['change_24h'],
                volume_24h=op['volume_24h'],
                score=op['score'],
                entry=op['entry'],
                target=op['target'],
                stop=op['stop'],
                risk_reward=op['risk_reward'],
                timestamp=datetime.now().isoformat()
            )
            for op in all_opportunities[:20]  # Top 20
        ]
    
    def execute(self, opportunity: Opportunity) -> Dict:
        """Execute a winning trade"""
        # Get balance
        balances = self.executor.get_balance()
        
        # Find USD/USDT balance
        usd_balance = balances.get('ZUSD', 0) + balances.get('USD', 0)
        
        if usd_balance < 1:
            return {'error': 'Insufficient USD balance'}
        
        # Calculate position size
        position_usd = min(usd_balance * self.config.max_position_pct, usd_balance)
        volume = position_usd / opportunity.price
        
        # Map symbol to Kraken pair
        if opportunity.exchange == 'binance':
            # Convert BTCUSDT -> XBTUSD
            base = opportunity.symbol.replace('USDT', '')
            if base == 'BTC':
                base = 'XBT'
            kraken_pair = f'{base}USD'
        else:
            kraken_pair = opportunity.symbol
        
        # Execute!
        result = self.executor.execute_market_buy(
            kraken_pair, 
            volume,
            dry_run=self.config.dry_run
        )
        
        return {
            'opportunity': asdict(opportunity),
            'execution': result,
            'position_usd': position_usd,
            'volume': volume
        }
    
    def run_forever(self):
        """Run the WIN KILLER continuously"""
        print()
        print('💀' * 35)
        print('   WIN KILLER ACTIVATED - KILL MODE')
        print('💀' * 35)
        print()
        print(f'   Mode: {"DRY RUN" if self.config.dry_run else "🔥 LIVE FIRE 🔥"}')
        print(f'   Min Score: {self.config.min_score}')
        print(f'   Scan Interval: {self.config.scan_interval}s')
        print()
        
        cycle = 0
        while True:
            cycle += 1
            print(f'━━━ HUNT CYCLE {cycle} ━━━ {datetime.now().strftime("%H:%M:%S")}')
            
            # Hunt for opportunities
            opportunities = self.hunt()
            
            if opportunities:
                best = opportunities[0]
                print(f'   🎯 BEST TARGET: {best.symbol} ({best.exchange})')
                print(f'      Type: {best.type} | Score: {best.score:.2f}')
                print(f'      Price: ${best.price:.6f} | Δ24h: {best.change_24h:+.1f}%')
                print(f'      Target: ${best.target:.6f} | Stop: ${best.stop:.6f}')
                print(f'      R:R: {best.risk_reward:.1f}:1')
                
                # Execute if score is high enough
                if best.score >= 5.0 and best.exchange == 'kraken':
                    print('   ⚡ EXECUTING...')
                    result = self.execute(best)
                    if 'error' not in result:
                        print(f'   ✅ ORDER PLACED: {result}')
                    else:
                        print(f'   ❌ {result["error"]}')
            else:
                print('   ⏳ No opportunities above threshold')
            
            print()
            time.sleep(self.config.scan_interval)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='WIN KILLER - By Any Means Necessary')
    parser.add_argument('--live', action='store_true', help='Enable LIVE trading')
    parser.add_argument('--min-score', type=float, default=3.0, help='Minimum win score')
    parser.add_argument('--interval', type=int, default=10, help='Scan interval (seconds)')
    parser.add_argument('--once', action='store_true', help='Run single scan')
    args = parser.parse_args()
    
    config = WinConfig(
        min_win_score=args.min_score,
        scan_interval=args.interval,
        dry_run=not args.live
    )
    
    killer = WinKiller(config)
    
    if args.once:
        # Single scan
        print()
        print('🔍 Single scan mode...')
        print()
        
        opportunities = killer.hunt()
        
        if opportunities:
            print('🏆 TOP OPPORTUNITIES:')
            print()
            for i, op in enumerate(opportunities[:10], 1):
                print(f'   {i}. {op.symbol:12} | {op.exchange:8} | {op.type:12}')
                print(f'      Score: {op.score:.2f} | Price: ${op.price:.6f}')
                print(f'      Δ24h: {op.change_24h:+.1f}% | Vol: ${op.volume_24h/1e6:.1f}M')
                print(f'      R:R: {op.risk_reward:.1f}:1')
                print()
        else:
            print('   No opportunities found')
    else:
        # Continuous mode
        try:
            killer.run_forever()
        except KeyboardInterrupt:
            print()
            print('👋 WIN KILLER shutdown')


if __name__ == '__main__':
    main()
