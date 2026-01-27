#!/usr/bin/env python3
"""
💰 MOMENTUM PROFIT TRADES - Wait for Uptrend Then Trade 💰
==========================================================

Strategy:
1. Monitor prices for upward momentum
2. Buy when momentum is positive
3. Sell when profit target hit OR momentum reverses

Gary Leckey | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import time
import sys

os.environ['LIVE'] = '1'

from binance_client import BinanceClient

def get_price(client, symbol):
    """Get current price"""
    ticker = client.best_price(symbol)
    return float(ticker.get('price', ticker.get('last', 0)))

def detect_momentum(client, symbol, samples=5, interval=1):
    """Detect if there's upward momentum"""
    prices = []
    for _ in range(samples):
        prices.append(get_price(client, symbol))
        time.sleep(interval)
    
    # Calculate momentum
    if prices[-1] > prices[0]:
        momentum = ((prices[-1] - prices[0]) / prices[0]) * 100
        return momentum, prices[-1]
    return 0, prices[-1]

def execute_momentum_trade(client, symbol, amount_usd):
    """Execute trade when momentum is positive"""
    print(f"\n{'='*60}")
    print(f"🎯 MOMENTUM TRADE: {symbol}")
    print(f"{'='*60}")
    
    # Get lot size info
    filters = client.get_symbol_filters(symbol)
    step_size = filters.get('step_size', 1)
    min_qty = filters.get('min_qty', 1)
    
    # Wait for positive momentum
    print(f"   ⏳ Waiting for upward momentum...")
    max_wait = 120  # 2 minutes max wait
    start = time.time()
    
    while time.time() - start < max_wait:
        momentum, current_price = detect_momentum(client, symbol, samples=3, interval=1)
        
        if momentum > 0.05:  # 0.05% upward momentum
            print(f"   📈 MOMENTUM DETECTED: +{momentum:.3f}% at ${current_price:.5f}")
            break
        else:
            elapsed = int(time.time() - start)
            print(f"   📊 Price: ${current_price:.5f} | Momentum: {momentum:+.3f}% [{elapsed}s]")
            time.sleep(2)
    else:
        print(f"   ⏰ No momentum detected in {max_wait}s - proceeding anyway")
        current_price = get_price(client, symbol)
    
    # Calculate quantity
    raw_qty = amount_usd / current_price
    
    # Round to step size
    if step_size >= 1:
        quantity = int(raw_qty)
    elif step_size >= 0.1:
        quantity = round(raw_qty, 1)
    else:
        quantity = round(raw_qty, 2)
    
    quantity = max(quantity, min_qty)
    entry_value = quantity * current_price
    
    print(f"\n   📦 Quantity: {quantity}")
    print(f"   💵 Entry Value: ${entry_value:.2f}")
    
    # BUY
    print(f"\n   📈 BUYING {quantity} {symbol}...")
    try:
        buy_result = client.place_market_order(symbol, 'BUY', quantity=quantity)
        if buy_result.get('rejected') or buy_result.get('uk_restricted'):
            print(f"   ❌ Buy rejected: {buy_result.get('reason')}")
            return False, 0
        if not buy_result.get('orderId'):
            print(f"   ❌ Buy failed: {buy_result}")
            return False, 0
        
        # Get actual fill price
        fills = buy_result.get('fills', [])
        if fills:
            entry_price = float(fills[0].get('price', current_price))
        else:
            entry_price = current_price
        print(f"   ✅ Bought at ${entry_price:.5f}")
    except Exception as e:
        print(f"   ❌ Buy error: {e}")
        return False, 0
    
    # Hold and monitor - sell on profit or stop loss
    print(f"\n   ⏳ Monitoring for profit target (+0.3%) or stop loss (-0.2%)...")
    
    target_pct = 0.003  # 0.3% profit target
    stop_pct = -0.002   # 0.2% stop loss
    
    for i in range(60):  # Max 2 minutes hold
        time.sleep(2)
        current = get_price(client, symbol)
        pct_change = (current - entry_price) / entry_price
        
        print(f"   📊 ${current:.5f} ({pct_change*100:+.3f}%) [{(i+1)*2}s]")
        
        if pct_change >= target_pct:
            print(f"   🎯 TARGET HIT!")
            break
        elif pct_change <= stop_pct:
            print(f"   🛑 STOP LOSS HIT!")
            break
    
    # SELL
    print(f"\n   📉 SELLING {quantity} {symbol}...")
    try:
        sell_result = client.place_market_order(symbol, 'SELL', quantity=quantity)
        if not sell_result.get('orderId'):
            print(f"   ❌ Sell failed: {sell_result}")
            return False, 0
        
        # Get actual fill price
        fills = sell_result.get('fills', [])
        if fills:
            exit_price = float(fills[0].get('price', current))
        else:
            exit_price = current
        print(f"   ✅ Sold at ${exit_price:.5f}")
    except Exception as e:
        print(f"   ❌ Sell error: {e}")
        return False, 0
    
    # Calculate P&L
    gross_pnl = (exit_price - entry_price) * quantity
    fees = entry_value * 0.001 * 2  # Estimate 0.1% each way
    net_pnl = gross_pnl - fees
    
    print(f"\n   {'='*40}")
    print(f"   📊 TRADE RESULT:")
    print(f"   ├─ Entry: ${entry_price:.5f}")
    print(f"   ├─ Exit:  ${exit_price:.5f}")
    print(f"   ├─ Gross: ${gross_pnl:+.4f}")
    print(f"   ├─ Fees:  ${fees:.4f}")
    if net_pnl > 0:
        print(f"   └─ ✅ NET PROFIT: ${net_pnl:+.4f}")
    else:
        print(f"   └─ ❌ NET LOSS: ${net_pnl:+.4f}")
    print(f"   {'='*40}")
    
    return net_pnl > 0, net_pnl


def main():
    print("\n" + "="*70)
    print("💰 MOMENTUM PROFIT TRADES 💰")
    print("="*70)
    
    print("\n⚠️  This will execute REAL trades with REAL money!")
    print("    Strategy: Wait for upward momentum, ride the wave")
    
    confirm = input("\n   Type 'GO' to proceed: ")
    if confirm != 'GO':
        print("\n   ❌ Cancelled.")
        return
    
    client = BinanceClient()
    print(f"\n🔌 BinanceClient ready")
    
    # Check UK restrictions
    symbols = ['DOGEUSDC', 'ADAUSDC', 'XLMUSDC']
    for sym in symbols:
        can, reason = client.can_trade_symbol(sym)
        if not can:
            print(f"   ❌ {sym}: {reason}")
            return
        print(f"   ✅ {sym}: OK")
    
    # Execute trades
    results = []
    total_pnl = 0
    
    for symbol in symbols:
        success, pnl = execute_momentum_trade(client, symbol, 6.0)
        results.append((symbol, success, pnl))
        total_pnl += pnl
        
        if symbol != symbols[-1]:
            print("\n   ⏳ Next trade in 3 seconds...")
            time.sleep(3)
    
    # Summary
    print("\n" + "="*70)
    print("📊 FINAL RESULTS")
    print("="*70)
    
    wins = sum(1 for _, s, _ in results if s)
    for symbol, success, pnl in results:
        icon = "✅" if success else "❌"
        print(f"   {icon} {symbol}: ${pnl:+.4f}")
    
    print(f"\n   Trades: {len(results)} | Wins: {wins} | Win Rate: {wins/len(results)*100:.0f}%")
    print(f"   Total Net P&L: ${total_pnl:+.4f}")
    
    if total_pnl > 0:
        print("\n   🎉 OVERALL NET PROFIT! 🎉")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
