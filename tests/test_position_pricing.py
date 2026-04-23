#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test position price fetching logic"""

import asyncio
import aiohttp
import json

async def test_position_pricing():
    """Test the new dynamic price fetching logic"""
    print("🧪 Testing Position Price Fetching Logic\n")
    
    # Simulate portfolio with positions
    portfolio = {
        'positions': [
            {'symbol': 'SHIBUSD', 'quantity': 934990.2293, 'avgCost': 0.000026, 'currentPrice': 0},
            {'symbol': 'TRXUSD', 'quantity': 1500, 'avgCost': 0.15, 'currentPrice': 0},
            {'symbol': 'TUSD', 'quantity': 100, 'avgCost': 1.0, 'currentPrice': 0},
            {'symbol': 'BSXUSD', 'quantity': 500, 'avgCost': 2.5, 'currentPrice': 0},
            {'symbol': 'LPTUSD', 'quantity': 10, 'avgCost': 15.0, 'currentPrice': 0},
        ]
    }
    
    # Build symbol list
    symbols_to_fetch = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']
    for pos in portfolio['positions']:
        symbol = pos['symbol'].upper()
        if symbol and symbol != 'USD':
            if 'USD' in symbol:
                binance_symbol = symbol.replace('USD', 'USDT')
            else:
                binance_symbol = f"{symbol}USDT"
            if binance_symbol not in symbols_to_fetch:
                symbols_to_fetch.append(binance_symbol)
    
    print(f"📊 Symbols to fetch: {len(symbols_to_fetch)}")
    for s in symbols_to_fetch:
        print(f"  - {s}")
    print()
    
    # Fetch prices from Binance
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                'https://api.binance.com/api/v3/ticker/price',
                timeout=aiohttp.ClientTimeout(total=5)
            ) as resp:
                if resp.status == 200:
                    all_prices = await resp.json()
                    price_map = {item['symbol']: float(item['price']) for item in all_prices if item['symbol'] in symbols_to_fetch}
                    
                    print(f"✅ Fetched {len(price_map)} prices:")
                    for sym, price in price_map.items():
                        print(f"  {sym}: ${price:,.8f}")
                    print()
                    
                    # Update positions
                    total_value = 0
                    total_cost = 0
                    print("💰 Position Valuations:")
                    for pos in portfolio['positions']:
                        symbol = pos['symbol'].upper()
                        if symbol and symbol != 'USD':
                            if 'USD' in symbol:
                                binance_symbol = symbol.replace('USD', 'USDT')
                            else:
                                binance_symbol = f"{symbol}USDT"
                            
                            price = price_map.get(binance_symbol, pos.get('currentPrice', 0))
                            if price > 0:
                                pos['currentPrice'] = price
                                pos['currentValue'] = pos['quantity'] * price
                                pos['unrealizedPnl'] = pos['currentValue'] - (pos['avgCost'] * pos['quantity'])
                                pos['pnlPercent'] = (pos['unrealizedPnl'] / (pos['avgCost'] * pos['quantity']) * 100) if pos['avgCost'] > 0 else 0
                                
                                total_value += pos['currentValue']
                                total_cost += pos['avgCost'] * pos['quantity']
                                
                                print(f"  {symbol}: {pos['quantity']:,.4f} @ ${price:,.8f} = ${pos['currentValue']:,.2f} ({pos['pnlPercent']:+.2f}%)")
                    
                    print(f"\n📈 Portfolio Summary:")
                    print(f"  Total Value: ${total_value:,.2f}")
                    print(f"  Cost Basis:  ${total_cost:,.2f}")
                    print(f"  P&L:         ${total_value - total_cost:+,.2f}")
                    
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_position_pricing())
