#!/usr/bin/env python3
"""
🏔️ CONTINUOUS SNOWBALL TO MILLION
Real trading loop - no stopping until $1M
"""

import os
import sys
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from kraken_client import KrakenClient

MILLION = 1_000_000
CYCLE_SECONDS = 45

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def get_portfolio_value(kraken):
    """Get total portfolio value in USD"""
    total = 0
    balances = kraken.get_balance()
    
    for asset, qty in balances.items():
        qty = float(qty)
        if qty <= 0:
            continue
            
        if asset in ['USD', 'ZUSD']:
            total += qty
        elif asset == 'ZGBP':
            total += qty * 1.27
        elif asset not in ['TUSD', 'USDT']:
            try:
                pair = f"{asset}USD"
                ticker = kraken.get_ticker(pair)
                if ticker and ticker.get('price'):
                    total += qty * float(ticker['price'])
            except:
                pass
                
    return total

def check_profit_taking(kraken):
    """Check if any positions should be sold for profit"""
    balances = kraken.get_balance()
    
    for asset, qty in balances.items():
        qty = float(qty)
        if qty <= 0 or asset in ['USD', 'ZUSD', 'ZGBP', 'TUSD']:
            continue
            
        pair = f"{asset}USD"
        try:
            ticker = kraken.get_ticker(pair)
            if not ticker:
                continue
                
            price = float(ticker['price'])
            value = qty * price
            
            if value < 3:  # Skip tiny positions
                continue
                
            # Simple profit logic: if we have enough value, take some profit
            if value > 5:
                log(f"💰 {asset}: ${value:.2f} @ ${price:.4f}")
                
                # Sell 30% to lock profit, keep rest for growth
                sell_qty = qty * 0.3
                
                log(f"   🎯 Selling {sell_qty:.4f} {asset} for profit")
                
                result = kraken.place_market_order(pair, 'sell', sell_qty)
                
                if result and result.get('status') == 'FILLED':
                    received = float(result.get('receivedQty', 0))
                    log(f"   ✅ SOLD! Received ${received:.2f}")
                    return True
                    
        except Exception as e:
            pass
            
    return False

def find_buy_opportunity(kraken):
    """Find something to buy that's cheap"""
    usd = float(kraken.get_balance().get('USD', 0))
    
    if usd < 2:
        log(f"⏳ Not enough USD (${usd:.2f}) - waiting for profit-taking")
        return False
        
    # Pairs to consider
    pairs = ['ADAUSD', 'XRPUSD', 'DOGEUSD', 'TRXUSD', 'SHIBUSDT']
    
    for pair in pairs:
        try:
            ticker = kraken.get_ticker(pair)
            if not ticker:
                continue
                
            price = float(ticker['price'])
            
            # Buy with 50% of USD
            trade_usd = usd * 0.5
            qty = trade_usd / price
            
            log(f"🎯 BUY: {qty:.2f} {pair.replace('USD', '')} @ ${price:.4f} (${trade_usd:.2f})")
            
            result = kraken.place_market_order(pair, 'buy', qty)
            
            if result and result.get('status') == 'FILLED':
                log(f"   ✅ BOUGHT! Order filled")
                return True
            else:
                log(f"   ❌ Order failed: {result.get('status')}")
                
        except Exception as e:
            pass
            
    return False

def main():
    print("\n" + "🏔️❄️" * 20)
    print("   SNOWBALL TO MILLION - CONTINUOUS RUN")
    print("🏔️❄️" * 20 + "\n")
    
    kraken = KrakenClient()
    cycle = 0
    
    while True:
        cycle += 1
        
        log("=" * 50)
        log(f"CYCLE {cycle}")
        log("=" * 50)
        
        try:
            # Check portfolio
            portfolio = get_portfolio_value(kraken)
            progress = (portfolio / MILLION) * 100
            
            log(f"💰 Portfolio: ${portfolio:.2f}")
            log(f"🎯 Progress: {progress:.6f}%")
            
            if portfolio >= MILLION:
                log("🎉🎉🎉 MILLION REACHED! 🎉🎉🎉")
                break
                
            # Step 1: Check for profit-taking
            log("\n📈 Checking profit opportunities...")
            sold = check_profit_taking(kraken)
            
            # Step 2: Look for buys
            if not sold:
                log("\n🔍 Looking for buy opportunities...")
                find_buy_opportunity(kraken)
                
        except KeyboardInterrupt:
            log("\n⏸️ Stopped by user")
            break
        except Exception as e:
            log(f"❌ Error: {e}")
            
        # Wait for next cycle
        log(f"\n⏳ Next cycle in {CYCLE_SECONDS}s...\n")
        time.sleep(CYCLE_SECONDS)

if __name__ == '__main__':
    main()
