import sys
from aureon_kraken_ecosystem import AureonKrakenEcosystem, CONFIG

print("🧮 Verifying PnL Accounting Logic...")

# Initialize Bot in Dry Run
bot = AureonKrakenEcosystem(initial_balance=1000.0, dry_run=True)

# Define Trade Parameters
symbol = "ETHGBP"
entry_price = 2000.0
investment = 100.0  # £100 investment
exit_price = 2040.0 # +2% gain

# 1. Simulate BUY
print(f"\n1. Simulating BUY of {symbol}...")
print(f"   Investment: £{investment:.2f}")
print(f"   Entry Price: £{entry_price:.2f}")

# Calculate expected entry values
entry_fee_rate = CONFIG['KRAKEN_FEE'] # 0.0026
entry_fee = investment * entry_fee_rate
net_investment = investment # In this bot logic, pos_size is the total value, fee is tracked separately usually or deducted. 
# Let's look at open_position logic:
# entry_fee = pos_size * CONFIG['KRAKEN_FEE']
# quantity = pos_size / price
quantity = investment / entry_price

print(f"   Quantity: {quantity:.6f} ETH")
print(f"   Entry Fee ({entry_fee_rate*100}%): £{entry_fee:.4f}")

# Manually inject position into bot
from aureon_kraken_ecosystem import Position
import time

bot.positions[symbol] = Position(
    symbol=symbol,
    entry_price=entry_price,
    quantity=quantity,
    entry_fee=entry_fee,
    entry_value=investment,
    momentum=10.0,
    coherence=0.8,
    entry_time=time.time(),
    dominant_node="TestNode"
)

# 2. Simulate SELL
print(f"\n2. Simulating SELL at £{exit_price:.2f} (+2%)...")

# Calculate expected exit values manually
exit_value = quantity * exit_price
gross_pnl = exit_value - investment
exit_fee_rate = CONFIG['KRAKEN_FEE']
exit_fee = exit_value * exit_fee_rate
slippage_rate = CONFIG['SLIPPAGE_PCT'] # 0.0010
slippage_cost = exit_value * slippage_rate

total_expenses = entry_fee + exit_fee + slippage_cost
net_pnl = gross_pnl - total_expenses

print(f"   Exit Value: £{exit_value:.4f}")
print(f"   Gross PnL: £{gross_pnl:.4f}")
print(f"   Expected Exit Fee ({exit_fee_rate*100}%): £{exit_fee:.4f}")
print(f"   Expected Slippage ({slippage_rate*100}%): £{slippage_cost:.4f}")
print(f"   Total Expenses: £{total_expenses:.4f}")
print(f"   Expected NET PnL: £{net_pnl:.4f}")

# 3. Execute Bot Logic
print("\n3. Executing Bot Close Logic...")
# Capture stdout to see the bot's report
from io import StringIO
old_stdout = sys.stdout
sys.stdout = mystdout = StringIO()

bot.close_position(symbol, "TEST_SELL", 2.0, exit_price)

sys.stdout = old_stdout
bot_output = mystdout.getvalue()
print(bot_output)

# 4. Verify
print("\n4. Verification Results:")
# Parse bot output for Net PnL
import re
match = re.search(r"Net: [£$€]([+\-0-9.]+)", bot_output)
if match:
    bot_net_pnl = float(match.group(1))
    diff = abs(bot_net_pnl - net_pnl)
    
    if diff < 0.01:
        print(f"✅ SUCCESS: Bot PnL (£{bot_net_pnl:.4f}) matches manual calc (£{net_pnl:.4f})")
    else:
        print(f"❌ FAILURE: Mismatch! Bot: {bot_net_pnl}, Manual: {net_pnl}")
else:
    print("❌ Could not parse Bot output.")
