
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
def validate_sell_logic():
    print("🧮 VALIDATING SELL LOGIC & SNIPER AWARENESS")
    print("="*50)
    
    # 1. THE SCENARIO (CHZUSDC)
    entry_price = 0.044810
    quantity = 535.00
    entry_value = entry_price * quantity
    
    # 2. THE TARGET
    target_pct = 0.00953  # +0.953%
    target_price = entry_price * (1 + target_pct)
    exit_value = target_price * quantity
    gross_profit = exit_value - entry_value
    
    print(f"1. Entry:      ${entry_value:.4f} (@ {entry_price:.6f})")
    print(f"2. Target:     ${exit_value:.4f} (@ {target_price:.6f})")
    print(f"3. Gross PnL:  ${gross_profit:.4f}")
    
    # 3. THE COSTS (Counting the Enemy)
    # Fee 0.1% + Slippage 0.2% + Spread 0.1% = 0.4% TOTAL
    total_rate = 0.004 
    entry_fee = entry_value * total_rate
    exit_fee = exit_value * total_rate
    total_costs = entry_fee + exit_fee
    
    print(f"4. Est Costs:  ${total_costs:.4f} (Entry+Exit @ 0.4%)")
    
    # 4. THE NET PROFIT
    net_profit = gross_profit - total_costs
    print(f"5. Net Profit: ${net_profit:.4f}")
    
    # 5. THE SNIPER CHECK
    print("-" * 50)
    print("🎯 SNIPER LOGIC CHECK:")
    if net_profit >= 0.01:
        print("   ✅ NET PROFIT > $0.01")
        print("   ✅ SNIPER WILL AUTHORIZE KILL")
    else:
        print("   ❌ NET PROFIT < $0.01")
        print("   🛡️ SNIPER WILL HOLD")

if __name__ == "__main__":
    validate_sell_logic()
