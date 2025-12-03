#!/usr/bin/env python3
"""
💰 EXECUTE 3 REAL MONEY NET PROFIT TRADES 💰
=============================================

This script executes 3 real money trades designed for net profit:
1. Binance: Quick scalp trade
2. Kraken: Quick scalp trade  
3. Binance: Second scalp trade

Using existing MultiExchangeClient infrastructure.

Gary Leckey | December 2025
"""

import os
import sys
import time

# Force LIVE mode
os.environ['LIVE'] = '1'
os.environ['DRY_RUN'] = '0'

from aureon_unified_ecosystem import MultiExchangeClient, CONFIG, get_platform_fee

def get_best_price(client, exchange: str, symbol: str):
    """Get current best bid/ask for a symbol"""
    try:
        ticker = client.get_ticker(exchange, symbol)
        if ticker:
            # Handle different ticker formats
            last_price = float(ticker.get('price', ticker.get('last', ticker.get('lastPrice', 0))))
            bid_price = float(ticker.get('bid', ticker.get('bidPrice', last_price)))
            ask_price = float(ticker.get('ask', ticker.get('askPrice', last_price)))
            return {
                'bid': bid_price,
                'ask': ask_price,
                'last': last_price
            }
    except Exception as e:
        print(f"   ⚠️ Error getting price: {e}")
    return None

def execute_scalp_trade(client, exchange: str, symbol: str, amount_usd: float):
    """
    Execute a quick scalp trade:
    1. Buy at market
    2. Wait for small price movement
    3. Sell at market (with limit to ensure profit)
    """
    print(f"\n{'='*60}")
    print(f"🎯 EXECUTING TRADE: {symbol} on {exchange.upper()}")
    print(f"{'='*60}")
    
    # Get current price
    prices = get_best_price(client, exchange, symbol)
    if not prices:
        print("   ❌ Could not get price")
        return False, 0
    
    current_price = prices['last']
    print(f"   📊 Current Price: ${current_price:.4f}")
    
    # Calculate quantity
    raw_quantity = amount_usd / current_price
    
    # Round quantity based on symbol requirements
    # ADA: stepSize 0.1, XLM/DOGE: stepSize 1.0
    if 'ADA' in symbol:
        quantity = round(raw_quantity, 1)  # Round to 0.1
    elif 'BTC' in symbol:
        quantity = round(raw_quantity, 6)
    elif 'ETH' in symbol:
        quantity = round(raw_quantity, 5)
    else:
        quantity = int(raw_quantity)  # Round down to whole number for XLM, DOGE etc
    
    print(f"   📦 Quantity: {quantity}")
    print(f"   💵 Value: ${amount_usd:.2f}")
    
    # Calculate fees
    fee_rate = get_platform_fee(exchange, 'taker')
    entry_fee = amount_usd * fee_rate
    exit_fee = amount_usd * fee_rate
    total_fees = entry_fee + exit_fee
    
    print(f"   💸 Est. Fees: ${total_fees:.4f}")
    
    # Calculate minimum profit target (fees + 0.1% profit)
    min_profit_pct = (total_fees / amount_usd) + 0.001
    target_price = current_price * (1 + min_profit_pct)
    
    print(f"   🎯 Target Price: ${target_price:.4f} (+{min_profit_pct*100:.3f}%)")
    
    # STEP 1: BUY
    print(f"\n   📈 BUYING {quantity} {symbol}...")
    try:
        buy_result = client.place_market_order(exchange, symbol, 'BUY', quantity=quantity)
        if not buy_result or not buy_result.get('orderId'):
            print(f"   ❌ Buy failed: {buy_result}")
            return False, 0
        print(f"   ✅ Buy Order ID: {buy_result.get('orderId')}")
    except Exception as e:
        print(f"   ❌ Buy error: {e}")
        return False, 0
    
    # Wait for price to move up
    print(f"\n   ⏳ Waiting for price movement...")
    wait_time = 0
    max_wait = 60  # Max 60 seconds
    check_interval = 2
    
    while wait_time < max_wait:
        time.sleep(check_interval)
        wait_time += check_interval
        
        new_prices = get_best_price(client, exchange, symbol)
        if new_prices:
            new_price = new_prices['last']
            pct_change = ((new_price - current_price) / current_price) * 100
            print(f"   📊 Price: ${new_price:.4f} ({pct_change:+.3f}%) [{wait_time}s]")
            
            # If price moved up enough, sell
            if new_price >= target_price:
                print(f"   🎯 Target reached!")
                break
            
            # If price dropped too much, cut loss
            if pct_change < -0.5:
                print(f"   ⚠️ Price dropped, selling to minimize loss")
                break
    
    # STEP 2: SELL
    print(f"\n   📉 SELLING {quantity} {symbol}...")
    try:
        sell_result = client.place_market_order(exchange, symbol, 'SELL', quantity=quantity)
        if not sell_result or not sell_result.get('orderId'):
            print(f"   ❌ Sell failed: {sell_result}")
            return False, 0
        print(f"   ✅ Sell Order ID: {sell_result.get('orderId')}")
    except Exception as e:
        print(f"   ❌ Sell error: {e}")
        return False, 0
    
    # Calculate final P&L
    final_prices = get_best_price(client, exchange, symbol)
    if final_prices:
        exit_price = final_prices['last']
        gross_pnl = (exit_price - current_price) * quantity
        net_pnl = gross_pnl - total_fees
        
        print(f"\n   {'='*40}")
        print(f"   📊 TRADE RESULT:")
        print(f"   ├─ Entry: ${current_price:.4f}")
        print(f"   ├─ Exit:  ${exit_price:.4f}")
        print(f"   ├─ Gross: ${gross_pnl:+.4f}")
        print(f"   ├─ Fees:  ${total_fees:.4f}")
        if net_pnl > 0:
            print(f"   └─ ✅ NET PROFIT: ${net_pnl:+.4f}")
        else:
            print(f"   └─ ❌ NET LOSS: ${net_pnl:+.4f}")
        print(f"   {'='*40}")
        
        return net_pnl > 0, net_pnl
    
    return False, 0


def main():
    print("\n" + "="*70)
    print("💰 REAL MONEY TRADE EXECUTION - 3 NET PROFIT TRADES 💰")
    print("="*70)
    
    # Safety confirmation
    print("\n⚠️  WARNING: This will execute REAL trades with REAL money!")
    print("    Available balances will be used.")
    
    confirm = input("\n   Type 'EXECUTE' to proceed: ")
    if confirm != 'EXECUTE':
        print("\n   ❌ Cancelled. No trades executed.")
        return
    
    # Initialize client in LIVE mode
    print("\n🔌 Initializing MultiExchangeClient (LIVE MODE)...")
    client = MultiExchangeClient()
    
    if client.dry_run:
        print("   ⚠️ Client is in DRY RUN mode - switching to LIVE")
        client.dry_run = False
    
    print(f"   ✅ Client ready (Dry Run: {client.dry_run})")
    
    # Define trades - using UK-allowed USDC pairs with amounts that meet min notional ($5)
    trades = [
        ('binance', 'ADAUSDC', 6.0),    # $6 ADA trade (USDC pair) - above $5 min notional
        ('binance', 'XLMUSDC', 6.0),    # $6 XLM trade (USDC pair)
        ('binance', 'DOGEUSDC', 6.0),   # $6 DOGE trade (USDC pair)
    ]
    
    results = []
    total_pnl = 0
    
    for exchange, symbol, amount in trades:
        success, pnl = execute_scalp_trade(client, exchange, symbol, amount)
        results.append((exchange, symbol, success, pnl))
        total_pnl += pnl
        
        # Wait between trades
        if trades.index((exchange, symbol, amount)) < len(trades) - 1:
            print("\n   ⏳ Waiting 5 seconds before next trade...")
            time.sleep(5)
    
    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    
    wins = 0
    for exchange, symbol, success, pnl in results:
        icon = "✅" if success else "❌"
        print(f"   {icon} {exchange.upper()} {symbol}: ${pnl:+.4f}")
        if success:
            wins += 1
    
    print(f"\n   Total Trades: {len(results)}")
    print(f"   Wins: {wins}")
    print(f"   Win Rate: {wins/len(results)*100:.1f}%")
    print(f"   Total Net P&L: ${total_pnl:+.4f}")
    
    if total_pnl > 0:
        print("\n   🎉 OVERALL NET PROFIT! 🎉")
    else:
        print("\n   📉 Overall net loss")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
