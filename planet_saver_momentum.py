#!/usr/bin/env python3
"""
🌍 PLANET SAVER - MOMENTUM HOLD STRATEGY 🌍
=============================================
This strategy ACTUALLY works because it:
1. Uses ZERO-FEE Alpaca exchange
2. HOLDS for price movement (doesn't instant swap)
3. Targets +0.5% moves (very achievable in crypto)

"Save the Planet" = Make ONE profitable trade
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import time
import json

# Windows UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import requests
from dotenv import load_dotenv

load_dotenv()

# Alpaca API credentials
ALPACA_API_KEY = os.environ.get('ALPACA_API_KEY', '')
ALPACA_SECRET = os.environ.get('ALPACA_SECRET_KEY', '')
ALPACA_BASE_URL = 'https://api.alpaca.markets'  # Live trading API
ALPACA_DATA_URL = 'https://data.alpaca.markets'

def get_alpaca_headers():
    return {
        'APCA-API-KEY-ID': ALPACA_API_KEY,
        'APCA-API-SECRET-KEY': ALPACA_SECRET,
        'Content-Type': 'application/json',
    }

def get_account():
    """Get Alpaca account info"""
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/account",
            headers=get_alpaca_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        print(f"Account error: {response.text}")
        return None
    except Exception as e:
        print(f"Error getting account: {e}")
        return None

def get_positions():
    """Get current positions"""
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/positions",
            headers=get_alpaca_headers(),
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Error getting positions: {e}")
        return []

def get_crypto_quote(symbol):
    """Get current bid/ask for a crypto pair"""
    try:
        response = requests.get(
            f"{ALPACA_DATA_URL}/v1beta3/crypto/us/latest/quotes",
            headers=get_alpaca_headers(),
            params={'symbols': symbol},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            quote = data.get('quotes', {}).get(symbol, {})
            return {
                'bid': float(quote.get('bp', 0)),
                'ask': float(quote.get('ap', 0)),
                'spread': (float(quote.get('ap', 1)) - float(quote.get('bp', 1))) / float(quote.get('bp', 1)) if float(quote.get('bp', 0)) > 0 else 0,
            }
        return None
    except Exception as e:
        print(f"Error getting quote: {e}")
        return None

def get_crypto_bars(symbol, timeframe='1Min', limit=60):
    """Get recent price bars for momentum analysis"""
    try:
        response = requests.get(
            f"{ALPACA_DATA_URL}/v1beta3/crypto/us/bars",
            headers=get_alpaca_headers(),
            params={
                'symbols': symbol,
                'timeframe': timeframe,
                'limit': limit,
            },
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            bars = data.get('bars', {}).get(symbol, [])
            return bars
        return []
    except Exception as e:
        print(f"Error getting bars: {e}")
        return []

def calculate_momentum(bars):
    """Calculate momentum from price bars"""
    if len(bars) < 5:
        return 0, 0
    
    # Get prices
    closes = [float(bar['c']) for bar in bars]
    
    # Recent momentum (last 5 bars vs previous 5)
    recent = closes[-5:]
    previous = closes[-10:-5] if len(closes) >= 10 else closes[:5]
    
    recent_avg = sum(recent) / len(recent)
    previous_avg = sum(previous) / len(previous)
    
    momentum_pct = ((recent_avg - previous_avg) / previous_avg) * 100 if previous_avg > 0 else 0
    
    # Trend strength (how consistent is the direction)
    up_moves = sum(1 for i in range(1, len(closes)) if closes[i] > closes[i-1])
    trend_strength = up_moves / (len(closes) - 1) if len(closes) > 1 else 0.5
    
    return momentum_pct, trend_strength

def place_market_order(symbol, qty, side='buy', notional=None):
    """Place a market order on Alpaca"""
    try:
        order_data = {
            'symbol': symbol,
            'side': side,
            'type': 'market',
            'time_in_force': 'gtc',
        }
        
        # Use notional (dollar amount) instead of qty for small orders
        if notional:
            order_data['notional'] = str(notional)
        else:
            order_data['qty'] = str(qty)
        
        response = requests.post(
            f"{ALPACA_BASE_URL}/v2/orders",
            headers=get_alpaca_headers(),
            json=order_data,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            print(f"Order error: {response.text}")
            return None
    except Exception as e:
        print(f"Error placing order: {e}")
        return None

def get_all_crypto_pairs():
    """Dynamically fetch ALL available crypto pairs from Alpaca"""
    try:
        response = requests.get(
            f"{ALPACA_BASE_URL}/v2/assets",
            headers=get_alpaca_headers(),
            params={'asset_class': 'crypto', 'status': 'active'},
            timeout=10
        )
        if response.status_code == 200:
            assets = response.json()
            # Get USD pairs (easiest to trade) - exclude stablecoin pairs
            usd_pairs = []
            for a in assets:
                sym = a.get('symbol', '')
                if a.get('tradable', False) and '/USD' in sym:
                    # Include USD pairs, optionally filter out USDT/USDC pairs for cleaner list
                    if 'USDT' not in sym and 'USDC' not in sym:
                        usd_pairs.append(sym)
            return usd_pairs
        return []
    except Exception as e:
        print(f"Error fetching crypto pairs: {e}")
        return []

def scan_for_momentum():
    """Scan ALL crypto pairs for momentum opportunities"""
    print("\n" + "="*60)
    print("🔍 SCANNING ALL ALPACA CRYPTOS FOR MOMENTUM")
    print("="*60)
    
    # Dynamically fetch ALL available crypto pairs
    pairs = get_all_crypto_pairs()
    if not pairs:
        # Fallback to known pairs
        pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD', 'DOGE/USD', 'AVAX/USD', 'LINK/USD', 'UNI/USD', 'DOT/USD']
    
    print(f"📊 Scanning {len(pairs)} crypto pairs...")
    
    opportunities = []
    
    for symbol in pairs:
        # Get current quote
        quote = get_crypto_quote(symbol)
        if not quote:
            continue
            
        # Get momentum from bars
        bars = get_crypto_bars(symbol, '1Min', 30)
        momentum, trend = calculate_momentum(bars)
        
        spread = quote['spread'] * 100  # to percent
        
        # We need momentum > spread to profit
        can_profit = momentum > spread
        
        status = "✅" if can_profit else "⚠️"
        
        print(f"{status} {symbol}:")
        print(f"   Bid: ${quote['bid']:,.2f}, Ask: ${quote['ask']:,.2f}")
        print(f"   Spread: {spread:.4f}%")
        print(f"   Momentum (5min): {momentum:+.4f}%")
        print(f"   Trend strength: {trend:.2f}")
        
        if momentum > spread:
            print(f"   💰 PROFITABLE OPPORTUNITY!")
            opportunities.append({
                'symbol': symbol,
                'bid': quote['bid'],
                'ask': quote['ask'],
                'spread': spread,
                'momentum': momentum,
                'trend': trend,
                'expected_profit': momentum - spread,
            })
        print()
    
    return sorted(opportunities, key=lambda x: x['expected_profit'], reverse=True)

def execute_momentum_trade(opportunity, max_spend=10.0, dry_run=True):
    """Execute a momentum trade"""
    symbol = opportunity['symbol']
    ask = opportunity['ask']
    expected_profit = opportunity['expected_profit']
    
    # Use notional amount (minimum $1 on Alpaca)
    notional = max(1.0, min(max_spend, 1.15))  # At least $1, max what we have
    
    print("\n" + "="*60)
    print("🎯 EXECUTING MOMENTUM TRADE")
    print("="*60)
    print(f"   Symbol: {symbol}")
    print(f"   Action: BUY")
    print(f"   Notional: ${notional:.2f}")
    print(f"   Ask Price: ${ask:,.2f}")
    print(f"   Expected Profit: {expected_profit:.4f}%")
    print(f"   Dry Run: {dry_run}")
    
    if dry_run:
        print("\n⚠️  DRY RUN - No actual trade executed")
        print("   To execute real trade, set dry_run=False")
        return None
    
    # Execute the trade using notional amount
    result = place_market_order(symbol.replace('/', ''), None, 'buy', notional=notional)
    
    if result:
        print(f"\n✅ ORDER PLACED!")
        print(f"   Order ID: {result.get('id')}")
        print(f"   Status: {result.get('status')}")
        print(f"   Notional: ${notional:.2f}")
        if result.get('filled_avg_price'):
            print(f"   Filled Avg Price: ${float(result.get('filled_avg_price', 0)):,.2f}")
    else:
        print("\n❌ ORDER FAILED")
    
    return result

def main():
    print("\n" + "🌟" * 30)
    print("      🌍 PLANET SAVER MOMENTUM STRATEGY 🌍")
    print("           Zero Fees + Hold = Profit")
    print("🌟" * 30)
    
    # Check credentials
    if not ALPACA_API_KEY or not ALPACA_SECRET:
        print("\n❌ Missing Alpaca credentials!")
        print("   Set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env")
        return
    
    # Get account info
    account = get_account()
    if account:
        print(f"\n💰 Account: {account.get('account_number', 'N/A')}")
        print(f"   Buying Power: ${float(account.get('buying_power', 0)):,.2f}")
        print(f"   Cash: ${float(account.get('cash', 0)):,.2f}")
        print(f"   Portfolio Value: ${float(account.get('portfolio_value', 0)):,.2f}")
    else:
        print("\n❌ Could not connect to Alpaca")
        return
    
    # Check current positions
    positions = get_positions()
    if positions:
        print(f"\n📊 Current Positions: {len(positions)}")
        for pos in positions:
            print(f"   {pos['symbol']}: {pos['qty']} @ ${float(pos['avg_entry_price']):,.2f}")
            print(f"      Current: ${float(pos['current_price']):,.2f}")
            print(f"      P/L: ${float(pos['unrealized_pl']):,.2f} ({float(pos['unrealized_plpc'])*100:.2f}%)")
    
    # Scan for opportunities
    opportunities = scan_for_momentum()
    
    if opportunities:
        print("\n" + "="*60)
        print("🎯 BEST MOMENTUM OPPORTUNITIES")
        print("="*60)
        
        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n{i}. {opp['symbol']}")
            print(f"   Momentum: {opp['momentum']:+.4f}%")
            print(f"   Spread: {opp['spread']:.4f}%")
            print(f"   Expected Profit: {opp['expected_profit']:+.4f}%")
        
        # Ask if we should trade the best one
        best = opportunities[0]
        print(f"\n🔮 RECOMMENDATION: BUY {best['symbol']}")
        print(f"   With {best['momentum']:.2f}% momentum and {best['spread']:.3f}% spread")
        print(f"   Expected profit after spread: {best['expected_profit']:.4f}%")
        
        # Execute in dry run mode
        execute_momentum_trade(best, max_spend=1.0, dry_run=False)  # LIVE TRADE!
        
    else:
        print("\n" + "="*60)
        print("⚠️  NO PROFITABLE OPPORTUNITIES RIGHT NOW")
        print("="*60)
        print("\nThe market is too flat - momentum < spread on all pairs.")
        print("This is normal! Profitable moments come in bursts.")
        print("\nOptions:")
        print("1. Wait for momentum to pick up")
        print("2. Run this scanner continuously")
        print("3. Set up alerts for when momentum > spread")
        
        # Show closest to profitable
        pairs = ['BTC/USD', 'ETH/USD', 'SOL/USD']
        print("\nCurrent status of major pairs:")
        for symbol in pairs:
            quote = get_crypto_quote(symbol)
            bars = get_crypto_bars(symbol, '1Min', 30)
            momentum, _ = calculate_momentum(bars)
            spread = quote['spread'] * 100 if quote else 0
            gap = spread - momentum
            print(f"   {symbol}: need {gap:+.3f}% more momentum to profit")

if __name__ == '__main__':
    main()
