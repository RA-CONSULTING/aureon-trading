#!/usr/bin/env python3
"""
🎓 BETA GRADUATION RESET
========================
Resets trade statistics to start fresh at v0.9.0-beta.

The losses during development were TRAINING DATA - tuition paid to
reach beta. This script archives the training stats and resets
counters so Kelly criterion starts fresh.

Run: python reset_for_beta.py
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import json
import os
from datetime import datetime

STATE_FILE = 'aureon_kraken_state.json'
LEARNING_FILE = 'adaptive_learning_history.json'

def main():
    print("\n" + "=" * 60)
    print("🎓 AUREON BETA GRADUATION RESET")
    print("=" * 60)
    print("\nThe training losses were tuition to reach v0.9.0-beta.")
    print("Time to start fresh with production-ready code!\n")
    
    # Archive current state
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Reset state file
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            state = json.load(f)
        
        # Archive old stats
        archive_file = f'training_archive_{timestamp}.json'
        training_stats = {
            'archived_at': timestamp,
            'phase': 'pre-beta-training',
            'total_trades': state.get('total_trades', 0),
            'wins': state.get('wins', 0),
            'losses': state.get('losses', 0),
            'net_profit': state.get('net_profit', 0),
            'message': 'These losses were training data for v0.9.0-beta'
        }
        
        with open(archive_file, 'w') as f:
            json.dump(training_stats, f, indent=2)
        print(f"📦 Archived training stats to: {archive_file}")
        print(f"   - Training trades: {training_stats['total_trades']}")
        print(f"   - Training wins: {training_stats['wins']}")
        print(f"   - Training losses: {training_stats['losses']}")
        
        # Reset counters but keep positions
        old_trades = state.get('total_trades', 0)
        old_wins = state.get('wins', 0)
        
        state['total_trades'] = 0
        state['wins'] = 0
        state['losses'] = 0
        state['net_profit'] = 0.0
        state['beta_started'] = timestamp
        state['beta_version'] = '0.9.0-beta'
        
        # Keep initial balance as current equity (fresh start)
        if 'total_equity' in state:
            state['initial_balance'] = state['total_equity']
        
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
        
        print(f"\n✅ Reset {STATE_FILE}:")
        print(f"   - total_trades: {old_trades} → 0")
        print(f"   - wins: {old_wins} → 0")
        print(f"   - losses: → 0")
        print(f"   - Beta started: {timestamp}")
    else:
        print(f"⚠️  {STATE_FILE} not found - will be created on startup")
    
    # Reset adaptive learning history
    if os.path.exists(LEARNING_FILE):
        with open(LEARNING_FILE, 'r') as f:
            learning = json.load(f)
        
        # Archive learning data
        learning_archive = f'learning_archive_{timestamp}.json'
        with open(learning_archive, 'w') as f:
            json.dump(learning, f, indent=2)
        print(f"\n📦 Archived learning history to: {learning_archive}")
        
        # Reset learning metrics (current schema uses 'trades' + 'thresholds')
        learning['trades'] = []
        learning['thresholds'] = {}
        learning['beta_reset'] = timestamp
        learning['updated_at'] = datetime.now().isoformat()
        
        with open(LEARNING_FILE, 'w') as f:
            json.dump(learning, f, indent=2)
        print(f"✅ Reset {LEARNING_FILE}")
    
    print("\n" + "=" * 60)
    print("🚀 BETA GRADUATION COMPLETE!")
    print("=" * 60)
    print("""
What happens now:
1. Kelly criterion will use BASE_POSITION_SIZE (4%) until 10 trades
2. Win rate starts fresh at 0% (no negative history)
3. Training losses are archived, not forgotten
4. System is ready for production-quality trading

Start the system:
    python aureon_unified_ecosystem.py

Good luck, soldier! 🎖️
""")


if __name__ == "__main__":
    main()
