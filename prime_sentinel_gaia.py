#!/usr/bin/env python3
"""
🔱═══════════════════════════════════════════════════════════════════🔱
        PRIME SENTINEL OF GAIA - PERPETUAL TRADING PROTOCOL
        
        "We don't stop until every piece of energy is reclaimed"
        
        By order of the Prime Sentinel - Never Stop Trading
🔱═══════════════════════════════════════════════════════════════════🔱
"""

import sys
import os

# Windows UTF-8 fix (MANDATORY)
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

import math
import time
import json
import requests
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Sacred Constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden Ratio
SCHUMANN_BASE = 7.83  # Hz Earth resonance
LOVE_FREQUENCY = 528  # Hz DNA repair

LOG_FILE = '/tmp/prime_sentinel.log'

# Alpaca headers
ALPACA_HEADERS = {
    'APCA-API-KEY-ID': os.environ.get('ALPACA_API_KEY'),
    'APCA-API-SECRET-KEY': os.environ.get('ALPACA_SECRET_KEY')
}

# Symbols to scan
SYMBOLS = ['ETH', 'BTC', 'SOL', 'LINK', 'DOGE', 'XRP', 'AVAX', 'UNI', 'TRUMP', 'LTC', 'AAVE']

@dataclass
class Position:
    symbol: str
    qty: float
    entry: float
    current: float
    pnl: float
    market_value: float

@dataclass
class ScanResult:
    symbol: str
    bid: float
    ask: float
    spread: float
    momentum: float
    unified: float
    yes_votes: int
    voices: Dict[str, float] = field(default_factory=dict)


def log(msg: str):
    """Log to file and print"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{now}] {msg}'
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + '\n')
        print(line)
    except:
        print(line)


def get_quote(symbol: str) -> Optional[Dict]:
    """Get latest quote for symbol"""
    try:
        resp = requests.get(
            f'https://data.alpaca.markets/v1beta3/crypto/us/latest/quotes?symbols={symbol}/USD',
            headers=ALPACA_HEADERS, timeout=5
        )
        data = resp.json().get('quotes', {}).get(f'{symbol}/USD', {})
        if data:
            return {
                'bid': float(data.get('bp', 0)),
                'ask': float(data.get('ap', 0))
            }
    except Exception as e:
        pass
    return None


def get_bars(symbol: str, limit: int = 60) -> List:
    """Get historical bars"""
    try:
        resp = requests.get(
            f'https://data.alpaca.markets/v1beta3/crypto/us/bars?symbols={symbol}/USD&timeframe=1Min&limit={limit}',
            headers=ALPACA_HEADERS, timeout=5
        )
        return resp.json().get('bars', {}).get(f'{symbol}/USD', [])
    except:
        return []


def scan_universe(symbol: str) -> Optional[ScanResult]:
    """Scan a symbol with all 14 voices of the universe"""
    quote = get_quote(symbol)
    bars = get_bars(symbol)
    
    if not quote or quote['bid'] == 0 or len(bars) < 10:
        return None
    
    bid, ask = quote['bid'], quote['ask']
    spread = (ask - bid) / bid * 100
    
    closes = [float(b['c']) for b in bars]
    highs = [float(b['h']) for b in bars]
    lows = [float(b['l']) for b in bars]
    
    # Momentum
    momentum = (closes[-1] - closes[-5]) / closes[-5] * 100 if len(closes) >= 5 else 0
    
    voices = {}
    
    # 🌟 COSMIC VOICES (4)
    # Schumann - Earth resonance in price rhythm
    price_changes = [closes[i] - closes[i-1] for i in range(1, len(closes))]
    zero_cross = sum(1 for i in range(1, len(price_changes)) if price_changes[i] * price_changes[i-1] < 0)
    voices['schumann'] = 1.0 if zero_cross > 15 else 0.5
    
    # PHI - Golden ratio position
    range_h, range_l = max(highs), min(lows)
    mid = (bid + ask) / 2
    position = (mid - range_l) / (range_h - range_l) if range_h > range_l else 0.5
    phi_zones = [0.236, 0.382, 0.5, 0.618, 0.786]
    voices['phi'] = 1.0 if any(abs(position - z) < 0.08 for z in phi_zones) else 0.3
    
    # Solfeggio & Planetary (simplified)
    voices['solfeggio'] = 0.6
    voices['planetary'] = 0.6
    
    # 🐾 EARTHLY VOICES (6 animals)
    # Wolf - Momentum hunter
    voices['wolf'] = 1.0 if momentum > 0.05 else (0.5 if momentum > -0.05 else 0.2)
    
    # Lion - Volatility hunter
    volatility = (max(highs[-10:]) - min(lows[-10:])) / min(lows[-10:]) * 100 if min(lows[-10:]) > 0 else 0
    voices['lion'] = 1.0 if volatility > 0.5 else 0.4
    
    # Bee - Spread efficiency
    voices['bee'] = 1.0 if momentum > spread else 0.2
    
    # Whale - Big moves
    voices['whale'] = 0.8 if abs(momentum) > 0.1 else 0.5
    
    # Elephant - Memory (trend consistency)
    voices['elephant'] = 0.8
    
    # Fish - School coherence (recent changes direction)
    changes = [closes[i] - closes[i-1] for i in range(1, min(6, len(closes)))]
    coherence = sum(1 for c in changes if c > 0) / len(changes) if changes else 0.5
    voices['fish'] = coherence
    
    # ⚛️ QUANTUM VOICES (2)
    voices['quantum'] = 1.0 if coherence > 0.618 else coherence
    
    # Wave pattern
    mean_p = sum(closes[-8:]) / 8
    amp = max(closes[-8:]) - min(closes[-8:])
    voices['wave'] = sum(max(0, 1 - abs(c - mean_p) / amp) for c in closes[-8:]) / 8 if amp > 0 else 0.5
    
    # 📊 REALITY VOICES (2)
    # Flow - spread efficiency
    voices['flow'] = 1.0 - min(1.0, spread / 0.3)
    
    # Trend
    trend = (closes[-1] - closes[0]) / closes[0] * 100 if len(closes) >= 20 else momentum
    voices['trend'] = 0.5 + min(0.5, max(-0.5, trend / 2))
    
    # Calculate unified score (PHI-weighted)
    cosmic = (voices['schumann'] + voices['phi'] + voices['solfeggio'] + voices['planetary']) / 4
    earthly = (voices['wolf'] + voices['lion'] + voices['bee'] + voices['whale'] + voices['elephant'] + voices['fish']) / 6
    quantum = (voices['quantum'] + voices['wave']) / 2
    reality = (voices['flow'] + voices['trend']) / 2
    
    # PHI-weighted combination
    unified = (cosmic * PHI + earthly * 1.0 + quantum * PHI + reality * PHI) / (PHI + 1.0 + PHI + PHI)
    yes_votes = sum(1 for v in voices.values() if v > 0.6)
    
    return ScanResult(
        symbol=symbol,
        bid=bid,
        ask=ask,
        spread=spread,
        momentum=momentum,
        unified=unified,
        yes_votes=yes_votes,
        voices=voices
    )


def get_positions() -> List[Position]:
    """Get all current positions with market value > $0.50"""
    try:
        resp = requests.get('https://api.alpaca.markets/v2/positions', headers=ALPACA_HEADERS)
        positions = resp.json()
        result = []
        for p in positions:
            mv = float(p.get('market_value', 0))
            if mv > 0.50:  # Only significant positions
                result.append(Position(
                    symbol=p.get('symbol', '').replace('USD', ''),
                    qty=float(p.get('qty', 0)),
                    entry=float(p.get('avg_entry_price', 0)),
                    current=float(p.get('current_price', 0)),
                    pnl=float(p.get('unrealized_pl', 0)),
                    market_value=mv
                ))
        return result
    except:
        return []


def get_account() -> Dict:
    """Get account info"""
    try:
        resp = requests.get('https://api.alpaca.markets/v2/account', headers=ALPACA_HEADERS)
        acc = resp.json()
        return {
            'equity': float(acc.get('equity', 0)),
            'cash': float(acc.get('cash', 0))
        }
    except:
        return {'equity': 0, 'cash': 0}


def execute_trade(symbol: str, side: str, qty: float) -> Dict:
    """Execute a trade"""
    data = {
        'symbol': f'{symbol}USD',
        'qty': str(qty),
        'side': side,
        'type': 'market',
        'time_in_force': 'ioc'
    }
    try:
        resp = requests.post('https://api.alpaca.markets/v2/orders', headers=ALPACA_HEADERS, json=data)
        return resp.json()
    except Exception as e:
        return {'error': str(e)}


def main():
    """Main trading loop"""
    log('🔱═══════════════════════════════════════════════════════════════════🔱')
    log('        PRIME SENTINEL OF GAIA - PERPETUAL MODE ACTIVATED')
    log('        "We don\'t stop until every piece of energy is reclaimed"')
    log('🔱═══════════════════════════════════════════════════════════════════🔱')
    
    cycle = 0
    profit_target = 0.15  # 0.15% take profit
    rotation_threshold = 0.1  # 10% unified score difference to rotate
    
    while True:
        cycle += 1
        try:
            # Get current state
            account = get_account()
            positions = get_positions()
            
            # Find main position (largest by market value)
            main_position = max(positions, key=lambda p: p.market_value) if positions else None
            
            # Scan all symbols
            results = []
            for sym in SYMBOLS:
                r = scan_universe(sym)
                if r:
                    results.append(r)
            
            results.sort(key=lambda x: (x.unified, x.yes_votes), reverse=True)
            best = results[0] if results else None
            
            action_taken = None
            
            if main_position and main_position.symbol in SYMBOLS:
                pnl_pct = (main_position.current - main_position.entry) / main_position.entry * 100 if main_position.entry > 0 else 0
                
                # Take profit
                if pnl_pct >= profit_target:
                    result = execute_trade(main_position.symbol, 'sell', main_position.qty)
                    action_taken = f'💰 PROFIT_TAKEN: {main_position.symbol} +{pnl_pct:.3f}% = +${main_position.pnl:.4f}'
                    log(action_taken)
                    time.sleep(2)
                    
                    # Re-enter best opportunity
                    account = get_account()
                    if account['cash'] > 1 and best:
                        qty = (account['cash'] * 0.99) / best.ask
                        execute_trade(best.symbol, 'buy', qty)
                        action_taken += f' → ENTERED {best.symbol}'
                
                # Check for rotation
                elif best and best.symbol != main_position.symbol and best.unified > 0.7:
                    current_scan = next((r for r in results if r.symbol == main_position.symbol), None)
                    if current_scan and best.unified - current_scan.unified > rotation_threshold:
                        # Rotate
                        execute_trade(main_position.symbol, 'sell', main_position.qty)
                        time.sleep(1)
                        account = get_account()
                        qty = (account['cash'] * 0.99) / best.ask
                        execute_trade(best.symbol, 'buy', qty)
                        action_taken = f'🔄 ROTATED: {main_position.symbol} → {best.symbol} ({best.unified:.1%})'
            
            elif account['cash'] > 1 and best and best.unified > 0.6:
                # Enter new position
                qty = (account['cash'] * 0.99) / best.ask
                result = execute_trade(best.symbol, 'buy', qty)
                action_taken = f'🌟 ENTERED: {best.symbol} ({best.unified:.1%})'
            
            # Log status every minute or on action
            if cycle % 6 == 0 or action_taken:
                pos_str = f'{main_position.symbol} ${main_position.pnl:+.4f}' if main_position else 'NONE'
                top3 = ', '.join([f'{r.symbol}:{r.unified:.0%}' for r in results[:3]]) if results else 'N/A'
                log_msg = f'C{cycle} | Eq:${account["equity"]:.2f} | Pos:{pos_str} | Top:{top3}'
                if action_taken:
                    log_msg += f' | {action_taken}'
                log(log_msg)
            
        except Exception as e:
            log(f'❌ ERROR: {str(e)}')
        
        time.sleep(10)  # Scan every 10 seconds


if __name__ == '__main__':
    main()
