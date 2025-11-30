#!/usr/bin/env python3
"""Check recent trade history from Binance"""

from binance_client import BinanceClient
from datetime import datetime

client = BinanceClient()

# Get all recent trades from last hour
print("\n📊 RECENT BINANCE ORDERS (Last 60 minutes):\n")

# Get account to find symbols with recent activity
account = client.account()
symbols_traded = []

# Check recent orders for BTC pairs
import requests
import time
import hmac
import hashlib

timestamp = int(time.time() * 1000)
recv_window = 60000

# Get all orders from last hour
params = {
    'timestamp': timestamp,
    'recvWindow': recv_window
}

# Sign the request
query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
signature = hmac.new(
    client.api_secret.encode('utf-8'),
    query_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()
params['signature'] = signature

# Get recent trades
try:
    # Try to get trades for specific symbols we know were traded
    test_symbols = ['JSTBTC', 'GLMBTC', 'DIABTC', 'WIFBTC', 'YFIBTC', 'HEIBTC', 'MINABTC', 'WLDBTC']
    
    all_trades = []
    for symbol in test_symbols:
        try:
            params_sym = {
                'symbol': symbol,
                'timestamp': int(time.time() * 1000),
                'recvWindow': recv_window
            }
            query = '&'.join([f"{k}={v}" for k, v in params_sym.items()])
            sig = hmac.new(client.api_secret.encode('utf-8'), query.encode('utf-8'), hashlib.sha256).hexdigest()
            params_sym['signature'] = sig
            
            response = client.session.get(
                f"{client.base}/api/v3/myTrades",
                params=params_sym
            )
            
            if response.status_code == 200:
                trades = response.json()
                if trades:
                    for trade in trades[-5:]:  # Last 5 trades per symbol
                        trade_time = datetime.fromtimestamp(trade['time'] / 1000)
                        all_trades.append({
                            'symbol': symbol,
                            'time': trade_time,
                            'side': 'BUY' if trade['isBuyer'] else 'SELL',
                            'qty': float(trade['qty']),
                            'price': float(trade['price']),
                            'quoteQty': float(trade['quoteQty']),
                            'commission': float(trade['commission']),
                            'commissionAsset': trade['commissionAsset']
                        })
        except Exception as e:
            pass
    
    if all_trades:
        # Sort by time
        all_trades.sort(key=lambda x: x['time'], reverse=True)
        
        print(f"✅ Found {len(all_trades)} recent trades:\n")
        for t in all_trades[:20]:  # Show last 20
            print(f"  {t['time'].strftime('%H:%M:%S')} | {t['side']:4} {t['symbol']:12} | "
                  f"Qty: {t['qty']:.8f} @ {t['price']:.8f} | "
                  f"Value: {t['quoteQty']:.8f} BTC | "
                  f"Fee: {t['commission']:.8f} {t['commissionAsset']}")
    else:
        print("❌ No recent trades found in the last period")
        print("\nChecking if dry_run mode is active...")
        print(f"Client dry_run setting: {client.dry_run}")
        print(f"Client testnet setting: {client.use_testnet}")
        
except Exception as e:
    print(f"❌ Error fetching trades: {e}")
    import traceback
    traceback.print_exc()

print(f"\n🔍 API Mode Check:")
print(f"  Base URL: {client.base}")
print(f"  Dry Run: {client.dry_run}")
print(f"  Testnet: {client.use_testnet}")
