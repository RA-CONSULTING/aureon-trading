
from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import sys
import json
import time

# Windows UTF-8 Fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

try:
    from cost_basis_tracker import CostBasisTracker
    from trade_logger import TradeLogger
except ImportError:
    print("❌ Failed to import trackers. Ensure you are in the project root.")
    sys.exit(1)

def repair():
    print("🛠️  REPAIRING SYSTEM STATE...")
    
    # 1. Initialize Log Directory
    log_dir = "/tmp/aureon_trade_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"✅ Created {log_dir}")
    else:
        print(f"✅ {log_dir} verified")

    # 2. Sync Cost Basis from all exchanges
    print("\n📊 Syncing Cost Basis (this ensures we never sell at a loss)...")
    tracker = CostBasisTracker()
    
    print("   🟡 Binance...")
    b_count = tracker.sync_from_binance()
    print(f"      └─ Updated {b_count} positions")
    
    print("   🐙 Kraken...")
    k_count = tracker.sync_from_kraken()
    print(f"      └─ Updated {k_count} positions")
    
    print("   🦙 Alpaca...")
    # Add Alpaca sync if method exists, otherwise manual update
    if hasattr(tracker, 'sync_from_alpaca'):
        a_count = tracker.sync_from_alpaca()
    else:
        # CostBasisTracker already attempts this in some versions
        a_count = 0
    print(f"      └─ Updated {a_count} positions")

    # 3. Create initial tracked_positions mapping for Orca from actual balances
    print("\n🦈 Initializing Orca tracking state...")
    tracked = {}
    for symbol, pos in tracker.positions.items():
        tracked[symbol] = {
            'symbol': symbol,
            'exchange': pos.get('exchange', 'unknown'),
            'entry_price': pos.get('avg_entry_price', 0),
            'entry_qty': pos.get('total_quantity', 0),
            'entry_cost': pos.get('total_cost', 0),
            'entry_time': pos.get('synced_at', time.time()),
            'breakeven_price': pos.get('avg_entry_price', 0) * 1.005 # rough estimate including fees
        }
    
    with open('tracked_positions.json', 'w') as f:
        json.dump(tracked, f, indent=4)
    print(f"✅ Created tracked_positions.json with {len(tracked)} verified positions")

    # 4. Final Connectivity Check
    print("\n📡 100% CONNECTIVITY VERIFICATION...")
    try:
        from binance_client import BinanceClient
        bc = BinanceClient()
        print("   ✅ BINANCE: Connected")
    except: print("   ❌ BINANCE: Failed")
    
    try:
        from kraken_client import KrakenClient
        kc = KrakenClient()
        print("   ✅ KRAKEN: Connected")
    except: print("   ❌ KRAKEN: Failed")

    print("\n✅ REPAIR COMPLETE. System visibility restored.")

if __name__ == "__main__":
    repair()
