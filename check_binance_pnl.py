from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient
from datetime import datetime

client = BinanceClient()

print('📈 RECENT TRADE HISTORY:')
print('=' * 80)

symbols = ['BTCUSDC', 'BANANAUSDC', 'FETUSDC', 'TURBOUSDC', 'FRONTUSDC', 'ALTUSDC']
all_trades = []

for sym in symbols:
    try:
        trades = client.get_my_trades(sym, limit=50)
        for t in trades:
            t['_symbol'] = sym
            all_trades.append(t)
    except Exception as e:
        pass

# Sort by time
all_trades.sort(key=lambda x: x['time'])

# Calculate P&L
total_spent = 0
total_received = 0
total_fees_usdc = 0

print(f"{'TIME':19s} | {'TYPE':4s} | {'SYMBOL':12s} | {'QTY':12s} | {'PRICE':10s} | {'VALUE':10s} | {'FEE':10s}")
print('=' * 80)

for t in all_trades:
    ts = datetime.fromtimestamp(t['time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
    side = 'BUY' if t['isBuyer'] else 'SELL'
    sym = t['_symbol']
    qty = float(t['qty'])
    price = float(t['price'])
    value = qty * price
    fee = float(t['commission'])
    fee_asset = t['commissionAsset']
    
    if t['isBuyer']:
        total_spent += value
        if fee_asset == 'USDC':
            total_fees_usdc += fee
    else:
        total_received += value
        if fee_asset == 'USDC':
            total_fees_usdc += fee
    
    print(f'{ts} | {side:4s} | {sym:12s} | {qty:12.6f} | ${price:9.4f} | ${value:9.4f} | {fee:.6f} {fee_asset}')

print('=' * 80)
print(f'\n💰 TRADING SUMMARY:')
print(f'Total Spent (Buys):     ${total_spent:.4f}')
print(f'Total Received (Sells): ${total_received:.4f}')
print(f'Total Fees (USDC):      ${total_fees_usdc:.6f}')
print(f'Net P&L (Closed):       ${total_received - total_spent:.4f}')
print(f'Net P&L (after fees):   ${total_received - total_spent - total_fees_usdc:.6f}')

# Calculate open position value
print(f'\n📦 OPEN POSITIONS:')
account = client.account()
balances = account['balances']

# Get current prices for held assets
held_assets = {}
for b in balances:
    qty = float(b['free']) + float(b['locked'])
    if qty > 0.001 and b['asset'] not in ['USDC', 'USDT', 'BUSD']:
        held_assets[b['asset']] = qty

open_position_value = 0
for asset, qty in held_assets.items():
    symbol = f'{asset}USDC'
    try:
        ticker = client.get_ticker(symbol)
        price = float(ticker['lastPrice'])
        value = qty * price
        open_position_value += value
        if value > 0.1:  # Only show positions > $0.10
            print(f'{asset:10s}: {qty:12.6f} @ ${price:9.4f} = ${value:9.4f}')
    except:
        pass

print(f'\nTotal Open Positions Value: ${open_position_value:.4f}')
print(f'USDC Balance:               ${79.0928:.4f}')
print(f'Total Account Value:        ${79.0928 + open_position_value:.4f}')
