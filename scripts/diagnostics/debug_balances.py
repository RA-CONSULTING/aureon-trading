from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
from binance_client import BinanceClient
from dotenv import load_dotenv

load_dotenv()

client = get_binance_client()

def check_balances():
    account = client.account()
    print("Balances:")
    for b in account['balances']:
        if float(b['free']) > 0:
            symbol = b['asset']
            qty = float(b['free'])
            try:
                if symbol == 'USDT':
                    price = 1.0
                elif symbol == 'LDUSDC':
                    price = 1.0
                else:
                    ticker = client.session.get(f"{client.base}/api/v3/ticker/price", params={'symbol': f"{symbol}USDT"}).json()
                    if 'price' in ticker:
                        price = float(ticker['price'])
                    else:
                        price = 0.0
                val = qty * price
                if val > 1.0: # Only show > $1
                    print(f"{symbol}: {qty} (~${val:.2f})")
            except:
                print(f"{symbol}: {qty} (Price unknown)")

def test_price(symbol):
    try:
        ticker = client.session.get(f"{client.base}/api/v3/ticker/price", params={'symbol': f"{symbol}USDT"}).json()
        print(f"Price of {symbol}USDT: {ticker}")
    except Exception as e:
        print(f"Error fetching {symbol}USDT: {e}")

check_balances()
test_price('DOGE')
test_price('XRP')
