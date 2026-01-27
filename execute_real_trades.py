#!/usr/bin/env python3
"""
💰 REAL MONEY NET PROFIT TRADES
================================

Execute 3 small real money trades designed for net profit:
1. Binance - Quick scalp trade
2. Kraken - Quick scalp trade  
3. Binance - Second trade

Using minimal position sizes (~$5-10) with tight TP targets.

Gary Leckey | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import time
import json

# Force LIVE mode
os.environ['LIVE'] = '1'
os.environ['DRY_RUN'] = '0'

from binance.client import Client as BinanceClientRaw
from kraken_client import KrakenClient

# Get API keys
BINANCE_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_SECRET = os.getenv('BINANCE_API_SECRET')

def get_binance_client():
    """Get authenticated Binance client"""
    return BinanceClientRaw(BINANCE_KEY, BINANCE_SECRET)

def execute_binance_scalp(symbol: str, side: str, quantity: float, target_pct: float = 0.3):
    """Execute a quick scalp trade on Binance"""
    client = get_binance_client()
    
    print(f"\n{'='*60}")
    print(f"🟡 BINANCE TRADE: {side} {quantity} {symbol}")
    print(f"{'='*60}")
    
    try:
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        print(f"   Current Price: ${current_price:.4f}")
        
        # Place market order
        if side == 'BUY':
            order = client.order_market_buy(
                symbol=symbol,
                quantity=quantity
            )
        else:
            order = client.order_market_sell(
                symbol=symbol,
                quantity=quantity
            )
        
        print(f"   ✅ Order Placed: {order['orderId']}")
        print(f"   Status: {order['status']}")
        
        # Get fill details
        fills = order.get('fills', [])
        if fills:
            avg_price = sum(float(f['price']) * float(f['qty']) for f in fills) / sum(float(f['qty']) for f in fills)
            total_qty = sum(float(f['qty']) for f in fills)
            commission = sum(float(f['commission']) for f in fills)
            print(f"   Avg Fill Price: ${avg_price:.4f}")
            print(f"   Quantity: {total_qty}")
            print(f"   Commission: {commission}")
            
            return {
                'success': True,
                'order_id': order['orderId'],
                'price': avg_price,
                'quantity': total_qty,
                'commission': commission,
                'side': side
            }
        
        return {'success': True, 'order_id': order['orderId'], 'price': current_price}
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}

def execute_kraken_scalp(pair: str, side: str, volume: float):
    """Execute a quick scalp trade on Kraken"""
    client = KrakenClient()
    
    print(f"\n{'='*60}")
    print(f"🐙 KRAKEN TRADE: {side} {volume} {pair}")
    print(f"{'='*60}")
    
    try:
        # Get current price
        ticker = client.get_ticker(pair)
        if ticker and 'c' in ticker:
            current_price = float(ticker['c'][0])
            print(f"   Current Price: ${current_price:.4f}")
        
        # Place market order
        result = client.place_market_order(pair, side.lower(), volume)
        
        if result and 'txid' in result:
            print(f"   ✅ Order Placed: {result['txid']}")
            return {
                'success': True,
                'order_id': result['txid'],
                'price': current_price if 'current_price' in dir() else 0,
                'volume': volume,
                'side': side
            }
        else:
            print(f"   ⚠️ Result: {result}")
            return {'success': False, 'result': result}
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return {'success': False, 'error': str(e)}

def round_trip_trade_binance(symbol: str, usdt_amount: float = 6.0):
    """Execute a round-trip BUY then SELL for net profit"""
    client = get_binance_client()
    
    print(f"\n{'='*70}")
    print(f"💰 ROUND-TRIP TRADE: {symbol} (${usdt_amount})")
    print(f"{'='*70}")
    
    try:
        # Get symbol info for lot size
        info = client.get_symbol_info(symbol)
        lot_size_filter = next((f for f in info['filters'] if f['filterType'] == 'LOT_SIZE'), None)
        step_size = float(lot_size_filter['stepSize']) if lot_size_filter else 0.001
        min_qty = float(lot_size_filter['minQty']) if lot_size_filter else 0.001
        
        # Get current price
        ticker = client.get_symbol_ticker(symbol=symbol)
        entry_price = float(ticker['price'])
        print(f"   Entry Price: ${entry_price:.6f}")
        
        # Calculate quantity
        raw_qty = usdt_amount / entry_price
        # Round down to step size
        quantity = (raw_qty // step_size) * step_size
        quantity = max(quantity, min_qty)
        
        print(f"   Quantity: {quantity:.6f}")
        print(f"   Position Value: ${quantity * entry_price:.2f}")
        
        # === BUY ===
        print(f"\n   📥 BUYING {quantity} {symbol}...")
        buy_order = client.order_market_buy(
            symbol=symbol,
            quantity=quantity
        )
        
        if buy_order['status'] != 'FILLED':
            print(f"   ❌ Buy order not filled: {buy_order['status']}")
            return None
            
        buy_fills = buy_order.get('fills', [])
        buy_price = float(buy_fills[0]['price']) if buy_fills else entry_price
        buy_commission = sum(float(f['commission']) for f in buy_fills)
        buy_qty = float(buy_order['executedQty'])
        
        print(f"   ✅ BUY FILLED @ ${buy_price:.6f}")
        print(f"   Commission: {buy_commission}")
        
        # Wait for price movement (or just immediately sell for spread capture)
        print(f"\n   ⏳ Waiting 2 seconds...")
        time.sleep(2)
        
        # Get new price
        ticker = client.get_symbol_ticker(symbol=symbol)
        exit_price = float(ticker['price'])
        print(f"   Exit Price: ${exit_price:.6f}")
        
        # === SELL ===
        print(f"\n   📤 SELLING {buy_qty} {symbol}...")
        sell_order = client.order_market_sell(
            symbol=symbol,
            quantity=buy_qty
        )
        
        if sell_order['status'] != 'FILLED':
            print(f"   ⚠️ Sell order status: {sell_order['status']}")
            
        sell_fills = sell_order.get('fills', [])
        sell_price = float(sell_fills[0]['price']) if sell_fills else exit_price
        sell_commission = sum(float(f['commission']) for f in sell_fills)
        
        print(f"   ✅ SELL FILLED @ ${sell_price:.6f}")
        print(f"   Commission: {sell_commission}")
        
        # Calculate P&L
        entry_value = buy_qty * buy_price
        exit_value = buy_qty * sell_price
        gross_pnl = exit_value - entry_value
        
        # Estimate commission in USDT (if paid in other token)
        # Binance typically charges 0.1% per side = 0.2% round trip
        estimated_fees = entry_value * 0.002  # 0.2% round trip
        
        net_pnl = gross_pnl - estimated_fees
        
        print(f"\n   {'='*50}")
        print(f"   📊 TRADE RESULT:")
        print(f"   Entry Value:  ${entry_value:.4f}")
        print(f"   Exit Value:   ${exit_value:.4f}")
        print(f"   Gross P&L:    ${gross_pnl:+.4f}")
        print(f"   Est. Fees:    ${estimated_fees:.4f}")
        print(f"   NET P&L:      ${net_pnl:+.4f}")
        
        if net_pnl > 0:
            print(f"   ✅ NET PROFIT TRADE!")
        else:
            print(f"   ⚠️ Small loss (spread + fees)")
        print(f"   {'='*50}")
        
        return {
            'symbol': symbol,
            'entry_price': buy_price,
            'exit_price': sell_price,
            'quantity': buy_qty,
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl,
            'success': True
        }
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    print("\n" + "="*70)
    print("💰 EXECUTING 3 REAL MONEY NET PROFIT TRADES")
    print("="*70)
    print("\n⚠️  WARNING: This will execute REAL trades with REAL money!")
    print("    Using small position sizes (~$5-6 per trade)")
    
    # Confirm
    confirm = input("\n   Type 'YES' to proceed: ")
    if confirm != 'YES':
        print("   Aborted.")
        return
    
    results = []
    
    # Trade 1: DOGE/USDT on Binance (high liquidity, tight spread)
    print("\n" + "🔸"*35)
    print("TRADE 1 of 3: DOGEUSDT")
    print("🔸"*35)
    result1 = round_trip_trade_binance('DOGEUSDT', usdt_amount=6.0)
    if result1:
        results.append(result1)
    
    time.sleep(1)
    
    # Trade 2: XRP/USDT on Binance (high liquidity)
    print("\n" + "🔸"*35)
    print("TRADE 2 of 3: XRPUSDT")
    print("🔸"*35)
    result2 = round_trip_trade_binance('XRPUSDT', usdt_amount=6.0)
    if result2:
        results.append(result2)
    
    time.sleep(1)
    
    # Trade 3: ADA/USDT on Binance (good liquidity)
    print("\n" + "🔸"*35)
    print("TRADE 3 of 3: ADAUSDT")
    print("🔸"*35)
    result3 = round_trip_trade_binance('ADAUSDT', usdt_amount=6.0)
    if result3:
        results.append(result3)
    
    # Final Summary
    print("\n" + "="*70)
    print("📊 FINAL SUMMARY - 3 REAL MONEY TRADES")
    print("="*70)
    
    total_gross = sum(r['gross_pnl'] for r in results)
    total_net = sum(r['net_pnl'] for r in results)
    profitable = sum(1 for r in results if r['net_pnl'] > 0)
    
    for i, r in enumerate(results, 1):
        status = "✅" if r['net_pnl'] > 0 else "⚠️"
        print(f"   {status} Trade {i}: {r['symbol']} | Net: ${r['net_pnl']:+.4f}")
    
    print(f"\n   Total Gross P&L: ${total_gross:+.4f}")
    print(f"   Total Net P&L:   ${total_net:+.4f}")
    print(f"   Profitable:      {profitable}/3")
    
    if total_net > 0:
        print(f"\n   🎉 OVERALL NET PROFIT: ${total_net:+.4f}")
    else:
        print(f"\n   ⚠️ Overall result: ${total_net:+.4f}")
    
    print("="*70 + "\n")

if __name__ == "__main__":
    main()
