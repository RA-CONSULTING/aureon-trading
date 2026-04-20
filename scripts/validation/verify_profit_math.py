
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os

# Fix path to allow importing from current directory
sys.path.append(os.getcwd())

from adaptive_prime_profit_gate import AdaptivePrimeProfitGate, ExchangeFeeProfile

def verify_math():
    print("=" * 60)
    print("🧪 VERIFYING PROFIT GATE MATH")
    print("=" * 60)

    # 1. Setup Test Case
    V = 100.0  # Trade Notional $100
    G = 0.0    # Fixed cost (Gas)
    P = 1.0    # Target Profit $1
    
    # Fees
    maker_fee = 0.001       # 0.1%
    slippage = 0.0005       # 0.05%
    spread = 0.0005         # 0.05%
    
    # Total cost rate 'c'
    c = maker_fee + slippage + spread # 0.002 (0.2%)
    
    print(f"Parameters:")
    print(f"  Notional (V): ${V}")
    print(f"  Target Profit (P): ${P}")
    print(f"  Fixed Cost (G): ${G}")
    print(f"  Cost Rate (c): {c:.6f} (Fee {maker_fee} + Slip {slippage} + Spread {spread})")
    
    # 2. Manual Calculation
    # r = (V + G + P) / [V * (1-c)^2] - 1
    
    numerator = V + G + P
    denominator = V * ((1 - c) ** 2)
    expected_r = (numerator / denominator) - 1
    
    print("-" * 30)
    print(f"MANUAL CALCULATION:")
    print(f"  Numerator (V+G+P): {numerator}")
    print(f"  Denominator (V*(1-c)^2): {denominator:.6f}")
    print(f"  Expected r: {expected_r:.8f}")
    print(f"  Expected Price Increase: {expected_r*100:.6f}%")
    
    # 3. Code Execution
    gate = AdaptivePrimeProfitGate()
    
    # Verify calculated_required_r method
    calculated_r = gate.calculate_required_r(
        trade_value=V,
        target_profit=P,
        fee_rate=maker_fee,
        slippage=slippage,
        spread=spread,
        fixed_costs=G
    )
    
    print("-" * 30)
    print(f"CODE EXECUTION:")
    print(f"  Calculated r: {calculated_r:.8f}")
    
    # 4. Compare
    diff = abs(expected_r - calculated_r)
    print("-" * 30)
    if diff < 1e-9:
        print("✅ MATCH: The code accurately implements the profit formula.")
    else:
        print(f"❌ MISMATCH: Diff is {diff}")
        exit(1)

    # 5. Sanity Check - Break Even
    # If P=0, G=0
    # r_be = V / [V * (1-c)^2] - 1 = 1/(1-c)^2 - 1
    P_be = 0
    expected_r_be = (1 / ((1-c)**2)) - 1
    
    calc_r_be = gate.calculate_required_r(
        trade_value=V,
        target_profit=P_be,
        fee_rate=maker_fee,
        slippage=slippage,
        spread=spread,
        fixed_costs=G
    )
    
    print(f"Break-even check (P=0):")
    print(f"  Expected r_be: {expected_r_be:.8f}")
    print(f"  Calculated r_be: {calc_r_be:.8f}")
    
    if abs(expected_r_be - calc_r_be) < 1e-9:
        print("✅ BE MATCH")
    else:
        print("❌ BE MISMATCH")
        exit(1)

if __name__ == "__main__":
    verify_math()
