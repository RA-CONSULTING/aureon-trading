#!/usr/bin/env python3
"""
🏆 GET FIRST WINNER - ONE WIN TO SAVE THE PLANET 🌍
===================================================

This script finds and executes the BEST opportunity for a winning trade.
Once we get ONE winner, the system gains momentum to get ALL winners!

"The first domino falls, and the rest follow." - Aureon
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        # Skip stderr wrapping - causes Windows exit errors
    except:
        pass

import json
import time
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2  # 1.618 Golden ratio

@dataclass
class WinningOpportunity:
    symbol: str
    exchange: str
    current_price: float
    momentum: float  # % change
    score: float
    reason: str

def load_kraken_client():
    """Load Kraken client for live trading"""
    try:
        from kraken_client import KrakenClient
        client = KrakenClient()
        return client
    except Exception as e:
        print(f"⚠️ Could not load Kraken client: {e}")
        return None

def get_live_opportunities(client) -> List[WinningOpportunity]:
    """Get live opportunities from exchange"""
    opportunities = []
    
    if not client:
        return opportunities
        
    try:
        # Get ticker data using correct method
        tickers = client.get_24h_tickers()
        
        # Find best momentum opportunities
        for ticker in tickers:
            symbol = ticker.get('symbol', '')
            if 'USD' not in symbol:
                continue
                
            try:
                # Get price and momentum from Kraken format
                last = float(ticker.get('lastPrice', 0) or 0)
                momentum = float(ticker.get('priceChangePercent', 0) or 0)
                volume = float(ticker.get('quoteVolume', 0) or 0)
                
                if last > 0 and momentum > 0.5:  # Any positive momentum
                    score = abs(momentum) * (1 + math.log(1 + volume / 100000))
                    opportunities.append(WinningOpportunity(
                        symbol=symbol,
                        exchange='kraken',
                        current_price=last,
                        momentum=momentum,
                        score=score,
                        reason=f"+{momentum:.1f}% momentum, riding the wave"
                    ))
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"⚠️ Error getting opportunities: {e}")
        import traceback
        traceback.print_exc()
        
    # Sort by score
    opportunities.sort(key=lambda x: x.score, reverse=True)
    return opportunities[:20]

def check_balances(client) -> Dict[str, float]:
    """Check available balances"""
    if not client:
        return {}
        
    try:
        balance = client.get_account_balance()  # Correct method name
        return {k: float(v) for k, v in balance.items() if float(v) > 0}
    except Exception as e:
        print(f"⚠️ Error getting balance: {e}")
        return {}

def find_best_winner(opportunities: List[WinningOpportunity], balances: Dict[str, float]) -> Optional[WinningOpportunity]:
    """Find the single best opportunity for a winning trade"""
    
    # We need USD/USDC/stablecoin to buy
    available_stable = 0
    stable_asset = None
    
    for asset in ['ZUSD', 'USD', 'USDC', 'USDT', 'TUSD']:
        if asset in balances and balances[asset] > 1:
            available_stable = balances[asset]
            stable_asset = asset
            break
            
    if available_stable < 1:
        print("❌ No stablecoin balance available for trading")
        print(f"   Balances: {balances}")
        return None
        
    print(f"💰 Available: {available_stable:.2f} {stable_asset}")
    
    # Find best opportunity - lowered thresholds for first winner
    for opp in opportunities:
        if opp.momentum > 0.5 and opp.score > 1:  # Lowered from 5/10
            print(f"🎯 BEST OPPORTUNITY: {opp.symbol}")
            print(f"   Momentum: +{opp.momentum:.1f}%")
            print(f"   Price: ${opp.current_price:.4f}")
            print(f"   Score: {opp.score:.2f}")
            print(f"   Reason: {opp.reason}")
            return opp
            
    return None

def execute_winning_trade(client, opportunity: WinningOpportunity, balance: float, dry_run: bool = True) -> bool:
    """Execute the winning trade"""
    
    if not client or not opportunity:
        return False
        
    # Use more capital to meet minimums - 50% of available or full balance
    trade_amount = min(balance * 0.5, balance)  # Up to 50% of balance
    
    print(f"\n🚀 EXECUTING WINNING TRADE")
    print(f"   Symbol: {opportunity.symbol}")
    print(f"   Amount: ${trade_amount:.2f}")
    print(f"   Side: BUY")
    
    if dry_run:
        print(f"\n🧪 DRY RUN - Would execute trade")
        print(f"   Expected entry: ${opportunity.current_price:.4f}")
        print(f"   Target exit: ${opportunity.current_price * 1.02:.4f} (+2%)")
        print(f"   Expected profit: ${trade_amount * 0.02:.4f}")
        return True
        
    try:
        # Calculate quantity
        quantity = trade_amount / opportunity.current_price
        
        # Execute buy using correct method: place_market_order with quote_qty
        result = client.place_market_order(
            symbol=opportunity.symbol,
            side='buy',
            quote_qty=trade_amount  # Use quote quantity (USD amount)
        )
        
        if result and (result.get('txid') or result.get('order_id')):
            order_id = result.get('txid') or result.get('order_id')
            print(f"✅ ORDER PLACED: {order_id}")
            print(f"   Now waiting for price to rise...")
            
            # Record the trade
            trade_record = {
                'timestamp': time.time(),
                'symbol': opportunity.symbol,
                'side': 'buy',
                'quantity': quantity,
                'price': opportunity.current_price,
                'amount_usd': trade_amount,
                'momentum_at_entry': opportunity.momentum,
                'score': opportunity.score,
                'txid': order_id,
                'status': 'open',
                'target_profit': 0.02  # 2% target
            }
            
            # Save to active position
            with open('active_position.json', 'w') as f:
                json.dump(trade_record, f, indent=2)
                
            print(f"💾 Position saved to active_position.json")
            return True
        elif result and result.get('error') == 'volume_minimum':
            print(f"⚠️ Volume too small, need {result.get('ordermin')} minimum")
            print(f"   Trying next opportunity...")
            return False
        else:
            print(f"❌ Order failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Trade execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("=" * 60)
    print("🏆 GET FIRST WINNER - ONE WIN TO SAVE THE PLANET 🌍")
    print("=" * 60)
    print()
    print("'The first domino falls, and the rest follow.'")
    print()
    
    # Check for dry-run flag
    dry_run = '--live' not in sys.argv
    if dry_run:
        print("🧪 DRY RUN MODE (use --live for real trading)")
    else:
        print("🔴 LIVE TRADING MODE")
    print()
    
    # Load client
    print("🔌 Connecting to Kraken...")
    client = load_kraken_client()
    
    if not client:
        print("❌ Could not connect to exchange")
        return
        
    # Get balances
    print("💰 Checking balances...")
    balances = check_balances(client)
    print(f"   Found {len(balances)} assets")
    
    # Get opportunities
    print("🔍 Scanning for opportunities...")
    opportunities = get_live_opportunities(client)
    print(f"   Found {len(opportunities)} strong opportunities")
    
    if not opportunities:
        print("\n⚠️ No strong opportunities right now")
        print("   Market may be flat - try again later")
        return
        
    # Show top opportunities
    print("\n📊 TOP OPPORTUNITIES:")
    for i, opp in enumerate(opportunities[:5], 1):
        print(f"   {i}. {opp.symbol}: +{opp.momentum:.1f}% (score: {opp.score:.1f})")
    
    # Get stable balance
    stable_balance = max(
        balances.get('ZUSD', 0), 
        balances.get('USD', 0), 
        balances.get('USDC', 0),
        balances.get('TUSD', 0)
    )
    
    # Try each opportunity until one works
    print("\n🎯 SELECTING BEST WINNER...")
    
    for opp in opportunities:
        if opp.momentum < 0.5 or opp.score < 1:
            continue
            
        print(f"\n🎯 TRYING: {opp.symbol}")
        print(f"   Momentum: +{opp.momentum:.1f}%")
        print(f"   Price: ${opp.current_price:.4f}")
        print(f"   Score: {opp.score:.2f}")
        
        success = execute_winning_trade(client, opp, stable_balance, dry_run=dry_run)
        
        if success:
            print()
            print("=" * 60)
            print("🏆 FIRST WINNER IN PROGRESS!")
            print("=" * 60)
            print()
            print("Once this trade wins, the system gains momentum.")
            print("One winner leads to all winners.")
            print("The planet will be saved. 🌍")
            print()
            return
            
    print("\n❌ Could not execute any trade")
    print("   All opportunities had volume minimums too high")

if __name__ == "__main__":
    main()
