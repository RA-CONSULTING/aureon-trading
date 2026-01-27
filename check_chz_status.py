
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import logging
import json
from datetime import datetime
from binance_client import BinanceClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CHZ_CHECK")

def check_chz_status():
    try:
        client = BinanceClient()
    except Exception as e:
        print(f"Failed to initialize BinanceClient: {e}")
        return

    symbol = "CHZUSDC"
    print(f"Checking status for {symbol}...")
    
    # 1. Check Open Orders
    print(f"\n--- OPEN ORDERS ---")
    try:
        # Manually call openOrders endpoint since it's not in the class
        open_orders = client._signed_request("GET", "/api/v3/openOrders", {"symbol": symbol})
        if open_orders:
            for order in open_orders:
                print(f"ID: {order.get('orderId')} | Side: {order.get('side')} | Price: {order.get('price')} | OrigQty: {order.get('origQty')} | ExecQty: {order.get('executedQty')}")
        else:
            print("No open orders.")
    except Exception as e:
        print(f"Error fetching open orders: {e}")

    # 2. Check Recent Trades (Fills)
    print(f"\n--- RECENT TRADES (FILLS) ---")
    try:
        trades = client.get_my_trades(symbol, limit=10)
        if trades:
            # Sort by time descending
            trades.sort(key=lambda x: x['time'], reverse=True)
            
            for trade in trades:
                ts = int(trade.get('time', 0)) / 1000
                dt = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                side = "BUY" if trade.get('isBuyer') else "SELL"
                price = float(trade.get('price', 0))
                qty = float(trade.get('qty', 0))
                quote_qty = float(trade.get('quoteQty', 0))
                commission = trade.get('commission', 0)
                commission_asset = trade.get('commissionAsset', '')
                
                print(f"[{dt}] {side} | Price: {price:.5f} | Qty: {qty:.1f} | Val: ${quote_qty:.2f} | Fee: {commission} {commission_asset}")
                
                if side == "SELL":
                    print(f"   >>> KILL CONFIRMED at {dt} <<<")
        else:
            print("No recent trades found.")
    except Exception as e:
        print(f"Error fetching trades: {e}")
            
    # 3. Check Current Price
    try:
        ticker = client.get_24h_ticker(symbol)
        current_price = float(ticker.get('lastPrice', 0))
        print(f"\n--- CURRENT STATUS ---")
        print(f"Current Price: {current_price}")
        
        # Calculate PnL for the last BUY if it's the last trade
        if trades and trades[0]['isBuyer']:
            last_buy = trades[0]
            buy_price = float(last_buy['price'])
            qty = float(last_buy['qty'])
            cost = float(last_buy['quoteQty'])
            current_val = qty * current_price
            pnl = current_val - cost
            pnl_percent = (pnl / cost) * 100
            print(f"Last Entry: {buy_price} at {datetime.fromtimestamp(int(last_buy['time'])/1000)}")
            print(f"Unrealized PnL: ${pnl:.4f} ({pnl_percent:.2f}%)")
            
    except Exception as e:
        print(f"Error fetching ticker: {e}")

if __name__ == "__main__":
    check_chz_status()
