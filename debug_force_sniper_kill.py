
import sys
import os
import time
from dataclasses import dataclass
from typing import Dict, Any

# Mock Dr. Auris / Sero Advice
@dataclass
class SeroAdvice:
    recommendation: str
    confidence: float
    reasoning: str

# Mock Client for Capital
class MockCapitalClient:
    def place_market_order(self, symbol, side, quantity):
        print(f"\n[MOCK CAPITAL] 🔫 EXECUTING SNIPER KILL: {side} {quantity} {symbol}")
        print(f"[MOCK CAPITAL] ✅ ORDER ACCEPTED (ID: mock_12345)")
        time.sleep(1) # Sim latency
        return {
            "dealReference": "mock_12345", 
            "status": "ACCEPTED",
            "id": "mock_12345",
            "filled_qty": quantity,
            "filled_avg_price": 101.00 # Mock fill price
        }

# Mock Cost Basis Info
class MockCostBasisTracker:
    def can_sell_profitably(self, symbol, current_price, exchange=None, quantity=None):
        entry_price = 100.00
        print(f"   ✅ [MOCK] Cost basis found: {symbol} -> entry ${entry_price:.2f}")
        return True, {'entry_price': entry_price}

    def update_position(self, *args, **kwargs):
        pass

class MockTradeLogger:
    def log_trade(self, *args, **kwargs):
        print(f"[MOCK LOGGER] Trade logged successfully.")
    
    def log_execution(self, *args, **kwargs):
        print(f"[MOCK LOGGER] Execution logged successfully.")

# Import the specific module (assumes python path is correct)
sys.path.insert(0, os.getcwd())

try:
    from orca_complete_kill_cycle import OrcaKillCycle, QUEEN_MIN_PROFIT_PCT
except ImportError:
    print("❌ Could not import OrcaKillCycle. Run this from repo root.")
    sys.exit(1)

# Subclass to inject mocks
class ValidatedSniperOrca(OrcaKillCycle):
    def __init__(self):
        # Skip full init to avoid loading everything
        self.running = True
        self.positions = {}
        self.clients = {'capital': MockCapitalClient()}
        self.cost_basis_tracker = MockCostBasisTracker()
        self.fee_rates = {'capital': 0.001}
        self.truth_bridge = None # Default
        self.is_real_win = None # Disable external fee check for mock
        self.epsilon_profit_usd = 0.0001
        self.cop_min_action = None
        self.cop_max_action = None
        self.cop_last_action = None
        self.trade_logger = MockTradeLogger()
        self.tracked_positions = {}
        
    def _prediction_window_ready(self, symbol):
        # Force a "NOT READY" to prove the bypass works
        return False, {'reason': 'NO_VALIDATED_PREDICTIONS'}

    def _get_sero_advice_sync(self, symbol, side, context, queen_confidence):
        print(f"\n👑 [QUEEN] Speaking to Dr. Auris Throne about {symbol}...")
        print(f"🤖 [DR AURIS] Analyzing market structure for {symbol}...")
        print(f"🤖 [DR AURIS] VALIDATED: Market conditions support aggressive action.")
        print(f"👑 [QUEEN] APPROVED. Proceed with {side}.")
        return SeroAdvice(recommendation='PROCEED', confidence=0.95, reasoning="Market Structure Supports Sell")

def run_test():
    orca = ValidatedSniperOrca()
    
    symbol = "TSLA"
    exchange = "capital"
    quantity = 1.0
    
    # Scene Setup
    entry_price = 100.00
    # Current price is HIGHER than Target (0.40%)
    # Target = 100.40. Let's make it 101.00 (1% profit)
    current_price = 101.00 
    entry_cost = entry_price * quantity
    
    print("="*60)
    print(f"🧪 TESTING IRA SNIPER LOGIC ON {exchange.upper()} ({symbol})")
    print(f"📉 Entry: ${entry_price:.2f}")
    print(f"📈 Current: ${current_price:.2f}")
    print(f"🎯 Target Growth: {QUEEN_MIN_PROFIT_PCT}%")
    print("="*60)

    # 1. Validating the "Bird in Hand" Logic first (queen_approved_exit)
    print("\n🔍 STEP 1: Queen Validation Check...")
    can_exit, info = orca.queen_approved_exit(
        symbol=symbol,
        exchange=exchange,
        current_price=current_price,
        entry_price=entry_price,
        entry_qty=quantity,
        entry_cost=entry_cost,
        reason="TARGET_HIT"
    )
    
    print("   ...Validation Complete.")
    
    # 2. Executing the Kill (execute_sell_with_logging)
    print("\n🔍 STEP 2: Executing Kill Cycle (simulating real call)...")
    
    # We pass the result of step 1 as context basically
    orca.execute_sell_with_logging(
        client=orca.clients['capital'],
        symbol=symbol,
        quantity=quantity,
        exchange=exchange,
        current_price=current_price,
        entry_cost=entry_cost,
        reason="GROWTH_MODE_TARGET"
    )

    print("\n✅ TEST COMPLETE: Logic verification finished.")

if __name__ == "__main__":
    run_test()
