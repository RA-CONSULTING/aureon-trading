"""
BINANCE P&L REALITY CHECK
==========================
This script compares:
1. What the bot THINKS it's doing (simulated trades)
2. What BINANCE actually shows (real account balance)
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
from binance_client import BinanceClient

print("=" * 80)
print("🔍 BINANCE P&L REALITY CHECK")
print("=" * 80)

client = BinanceClient()

print(f"\n📋 CLIENT CONFIGURATION:")
print(f"   Testnet Mode:  {client.use_testnet}")
print(f"   Dry Run Mode:  {client.dry_run}")
print(f"   Base URL:      {client.base}")

# Get account
account = client.account()
balances = account['balances']

print(f"\n💰 REAL BINANCE BALANCES:")
print(f"{'Asset':10s} | {'Balance':15s} | {'Estimated Value (USDC)':25s}")
print("-" * 60)

usdc_balance = 0
total_value_usdc = 0

for b in balances:
    free = float(b['free'])
    locked = float(b['locked'])
    total = free + locked
    
    if b['asset'] == 'USDC':
        usdc_balance = total
        total_value_usdc += total
        print(f"{'USDC':10s} | {f'${total:.4f}':15s} | {'(base currency)':25s}")
    elif total > 0.0001:
        # Try to get USDC price
        symbol = f"{b['asset']}USDC"
        try:
            ticker = client.get_ticker(symbol)
            price = float(ticker['lastPrice'])
            value_usdc = total * price
            total_value_usdc += value_usdc
            if value_usdc > 0.05:  # Only show positions > $0.05
                print(f"{b['asset']:10s} | {total:15.6f} | ${value_usdc:9.4f} @ ${price:.6f}")
        except:
            if total > 1:  # Show tokens with significant quantity
                print(f"{b['asset']:10s} | {total:15.6f} | {'(no USDC pair)':25s}")

print("-" * 60)
print(f"{'TOTAL':10s} | {'':15s} | ${total_value_usdc:.4f}")

# Check recent trades on USDC pairs
print(f"\n📈 RECENT USDC TRADES (Last 24 hours):")
symbols = ['BTCUSDC', 'BANANAUSDC', 'FETUSDC', 'TURBOUSDC', 'FRONTUSDC', 'ALTUSDC']

found_trades = False
for sym in symbols:
    try:
        trades = client.get_my_trades(sym, limit=100)
        if trades:
            found_trades = True
            print(f"\n{sym}:")
            for t in trades[-5:]:  # Show last 5
                side = '🟢 BUY' if t['isBuyer'] else '🔴 SELL'
                qty = float(t['qty'])
                price = float(t['price'])
                value = qty * price
                fee = float(t['commission'])
                print(f"  {side} | {qty:.6f} @ ${price:.4f} = ${value:.4f} | Fee: {fee:.6f} {t['commissionAsset']}")
    except:
        pass

if not found_trades:
    print("   ⚠️ NO USDC TRADES FOUND!")
    print("   This means the bot is NOT executing real trades on Binance.")

print(f"\n" + "=" * 80)
print("💡 ANALYSIS:")
print("=" * 80)

print(f"""
If you see:
  ✅ No USDC trades found + FET balance exists
     → Bot is in SIMULATION mode (not executing real orders)
  
  ✅ USDC trades found + changing balances
     → Bot is LIVE trading (real money!)

Current Status: """)

if not found_trades:
    print("   🔴 SIMULATION MODE - Bot is NOT trading real money on Binance")
    print(f"   Your FET balance ({next((float(b['free']) + float(b['locked']) for b in balances if b['asset'] == 'FET'), 0):.2f}) is from BEFORE this bot session")
else:
    print("   🟢 LIVE TRADING - Bot is executing real trades!")

print("=" * 80)
