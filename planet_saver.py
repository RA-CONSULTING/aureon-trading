#!/usr/bin/env python3
"""
🌍 PLANET SAVER - Complete Trading Cycle 🌍
============================================
One winner → Compound → All winners → Save the planet
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict

# Sacred constants
PHI = 1.618033988749895
SCHUMANN = 7.83
LOVE_FREQ = 528

@dataclass
class Position:
    symbol: str
    side: str
    entry_price: float
    quantity: float
    entry_time: str
    entry_cost: float
    current_price: float = 0.0
    current_value: float = 0.0
    pnl: float = 0.0
    pnl_percent: float = 0.0

@dataclass 
class TradingState:
    total_trades: int = 0
    winning_trades: int = 0
    total_profit: float = 0.0
    current_position: Optional[Position] = None
    trade_history: List[Dict] = field(default_factory=list)
    started_at: str = ""
    last_update: str = ""

def load_client():
    from kraken_client import KrakenClient
    return KrakenClient()

def get_balances(client) -> Dict[str, float]:
    return client.get_account_balance()

def get_ticker(client, symbol: str) -> Dict:
    tickers = client.get_24h_tickers()
    for t in tickers:
        if t.get('symbol') == symbol:
            return t
    return {}

def find_best_opportunity(client, quote_currency: str = 'USDC') -> Optional[Dict]:
    tickers = client.get_24h_tickers()
    opportunities = []
    for t in tickers:
        symbol = t.get('symbol', '')
        if not symbol.endswith(quote_currency):
            continue
        change = float(t.get('priceChangePercent', 0))
        volume = float(t.get('quoteVolume', 0))
        price = float(t.get('lastPrice', 0))
        if change > 1.0 and volume > 1000:
            score = change * (volume ** 0.3)
            opportunities.append({
                'symbol': symbol,
                'change': change,
                'volume': volume,
                'price': price,
                'score': score
            })
    if opportunities:
        opportunities.sort(key=lambda x: -x['score'])
        return opportunities[0]
    return None

def execute_buy(client, symbol: str, quote_amount: float) -> Optional[Dict]:
    try:
        result = client.place_market_order(symbol, 'buy', quote_qty=quote_amount)
        return result
    except Exception as e:
        print(f"   ❌ Buy failed: {e}")
        return None

def execute_sell(client, symbol: str, quantity: float) -> Optional[Dict]:
    try:
        result = client.place_market_order(symbol, 'sell', qty=quantity)
        return result
    except Exception as e:
        print(f"   ❌ Sell failed: {e}")
        return None

def load_state() -> TradingState:
    try:
        with open('planet_saver_state.json', 'r') as f:
            data = json.load(f)
            state = TradingState(**{k: v for k, v in data.items() if k not in ['current_position', 'trade_history']})
            state.trade_history = data.get('trade_history', [])
            if data.get('current_position'):
                state.current_position = Position(**data['current_position'])
            return state
    except:
        return TradingState(started_at=datetime.now().isoformat())

def save_state(state: TradingState):
    data = {
        'total_trades': state.total_trades,
        'winning_trades': state.winning_trades,
        'total_profit': state.total_profit,
        'trade_history': state.trade_history,
        'started_at': state.started_at,
        'last_update': datetime.now().isoformat(),
        'current_position': asdict(state.current_position) if state.current_position else None
    }
    with open('planet_saver_state.json', 'w') as f:
        json.dump(data, f, indent=2)

def print_banner():
    print("""
╔═══════════════════════════════════════════════════════════════╗
║     🌍 PLANET SAVER - AUREON TRADING SYSTEM 🌍                ║
║     "One winner leads to all winners"                         ║
║     φ = 1.618 | Schumann = 7.83 Hz | Love = 528 Hz           ║
╚═══════════════════════════════════════════════════════════════╝
""")

def run_trading_cycle(live: bool = False, target_profit_pct: float = 2.0):
    print_banner()
    
    mode = "🔴 LIVE" if live else "🟡 DRY-RUN"
    print(f"Mode: {mode} | Target: {target_profit_pct}%")
    
    client = load_client()
    state = load_state()
    
    print(f"\n📊 Stats: {state.winning_trades} wins | ${state.total_profit:.2f} profit")
    
    balances = get_balances(client)
    usdc = balances.get('USDC', 0)
    melania = balances.get('MELANIA', 0)
    
    print(f"💰 USDC: ${usdc:.2f} | MELANIA: {melania:.2f}")
    
    if melania > 1:
        ticker = get_ticker(client, 'MELANIAUSDC')
        if ticker:
            current_price = float(ticker.get('lastPrice', 0))
            current_value = melania * current_price
            
            if not state.current_position:
                state.current_position = Position(
                    symbol='MELANIAUSDC',
                    side='BUY',
                    entry_price=0.1515,
                    quantity=melania,
                    entry_time=datetime.now().isoformat(),
                    entry_cost=13.75
                )
            
            pos = state.current_position
            pos.current_price = current_price
            pos.current_value = current_value
            pos.pnl = current_value - pos.entry_cost
            pos.pnl_percent = (pos.pnl / pos.entry_cost) * 100
            
            print(f"\n📈 POSITION: {pos.symbol}")
            print(f"   Entry: ${pos.entry_price:.4f} → Current: ${current_price:.4f}")
            print(f"   Value: ${current_value:.2f}")
            
            if pos.pnl >= 0:
                print(f"   P&L: +${pos.pnl:.2f} (+{pos.pnl_percent:.2f}%) 🟢")
            else:
                print(f"   P&L: ${pos.pnl:.2f} ({pos.pnl_percent:.2f}%) 🔴")
            
            if pos.pnl_percent >= target_profit_pct:
                print(f"\n🎯 TARGET HIT! +{pos.pnl_percent:.2f}%")
                
                if live:
                    print("🚀 SELLING...")
                    result = execute_sell(client, pos.symbol, pos.quantity)
                    
                    if result and result.get('status') == 'FILLED':
                        sell_value = float(result.get('cummulativeQuoteQty', 0))
                        profit = sell_value - pos.entry_cost
                        
                        print(f"✅ SOLD! ${sell_value:.2f}")
                        print(f"💰 PROFIT: ${profit:.2f}")
                        
                        state.total_trades += 1
                        state.winning_trades += 1
                        state.total_profit += profit
                        state.trade_history.append({
                            'symbol': pos.symbol,
                            'entry': pos.entry_price,
                            'exit': current_price,
                            'profit': profit,
                            'time': datetime.now().isoformat()
                        })
                        state.current_position = None
                        save_state(state)
                        
                        print("\n🔄 FINDING NEXT WINNER...")
                        opp = find_best_opportunity(client, 'USDC')
                        if opp:
                            print(f"🎯 Found: {opp['symbol']} +{opp['change']:.1f}%")
                            new_balance = get_balances(client).get('USDC', 0)
                            trade_amount = new_balance * 0.90
                            
                            if trade_amount > 5:
                                result = execute_buy(client, opp['symbol'], trade_amount)
                                if result and result.get('status') == 'FILLED':
                                    print(f"✅ BOUGHT {opp['symbol']}!")
                                    state.current_position = Position(
                                        symbol=opp['symbol'],
                                        side='BUY',
                                        entry_price=float(result.get('price', 0)),
                                        quantity=float(result.get('executedQty', 0)),
                                        entry_time=datetime.now().isoformat(),
                                        entry_cost=float(result.get('cummulativeQuoteQty', 0))
                                    )
                                    save_state(state)
                else:
                    print("   [DRY-RUN] Would sell here")
            else:
                needed = target_profit_pct - pos.pnl_percent
                print(f"\n⏳ Need +{needed:.2f}% more")
                
            save_state(state)
    else:
        print("\n🔍 No position. Scanning...")
        opp = find_best_opportunity(client, 'USDC')
        if opp:
            print(f"🎯 Best: {opp['symbol']} +{opp['change']:.1f}%")
            if live and usdc > 5:
                trade_amount = usdc * 0.90
                print(f"🚀 BUYING ${trade_amount:.2f}...")
                result = execute_buy(client, opp['symbol'], trade_amount)
                if result and result.get('status') == 'FILLED':
                    print("✅ BOUGHT!")
                    state.current_position = Position(
                        symbol=opp['symbol'],
                        side='BUY',
                        entry_price=float(result.get('price', 0)),
                        quantity=float(result.get('executedQty', 0)),
                        entry_time=datetime.now().isoformat(),
                        entry_cost=float(result.get('cummulativeQuoteQty', 0))
                    )
                    save_state(state)
    
    print(f"\n{'═'*50}")
    print(f"Session: {state.winning_trades}/{state.total_trades} wins | ${state.total_profit:.2f}")
    print(f"{'═'*50}")
    
    return state

def continuous_mode(live: bool = False, interval: int = 60, target: float = 2.0):
    print(f"\n🔄 CONTINUOUS MODE - Every {interval}s | Target: {target}%\n")
    
    cycle = 0
    while True:
        try:
            cycle += 1
            print(f"\n{'='*60}")
            print(f"CYCLE {cycle} - {datetime.now().strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            state = run_trading_cycle(live=live, target_profit_pct=target)
            
            print(f"\n⏳ Next in {interval}s...")
            time.sleep(interval)
            
        except KeyboardInterrupt:
            print("\n\n🛑 Stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(interval)

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Planet Saver')
    parser.add_argument('--live', action='store_true', help='Live trading')
    parser.add_argument('--continuous', action='store_true', help='Run continuously')
    parser.add_argument('--interval', type=int, default=60, help='Check interval')
    parser.add_argument('--target', type=float, default=2.0, help='Target profit %')
    
    args = parser.parse_args()
    
    if args.continuous:
        continuous_mode(live=args.live, interval=args.interval, target=args.target)
    else:
        run_trading_cycle(live=args.live, target_profit_pct=args.target)
