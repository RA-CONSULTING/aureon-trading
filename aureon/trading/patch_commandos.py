#!/usr/bin/env python3
"""Patch to add Commandos initialization to s5_intelligent_dance.py"""

from aureon.core.aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
with open('s5_intelligent_dance.py', 'r') as f:
    content = f.read()

# Find the target line and insert after it
target = 'self.dream_simulator = DreamRunSimulator(min_validation_trades=3, min_accuracy=0.6)'
insert_after = '''
        
        # 🦆⚔️ INITIALIZE QUACK COMMANDOS - Animal Warfare Intelligence!
        self.commandos = None
        if COMMANDOS_AVAILABLE and self.binance:
            try:
                self.commandos = QuackCommandos(self.binance, config={
                    'LION_SLOTS': 3,
                    'WOLF_SLOTS': 2,
                    'ANTS_SLOTS': 1,
                    'HUMMINGBIRD_SLOTS': 1,
                    'ALLOW_SLOT_BORROWING': True
                })
                print("🦆⚔️ Quack Commandos deployed!")
                print(f"      └─ 🦁 Lion: 3 slots | 🐺 Wolf: 2 slots")
                print(f"      └─ 🐜 Ants: 1 slot  | 🐝 Hummingbird: 1 slot")
            except Exception as e:
                print(f"   ⚠️ Commandos init failed: {e}")'''

if target in content and 'QUACK COMMANDOS' not in content:
    content = content.replace(target, target + insert_after)
    with open('s5_intelligent_dance.py', 'w') as f:
        f.write(content)
    print("✅ Commandos initialization added!")
elif 'QUACK COMMANDOS' in content:
    print("⚠️ Commandos already initialized in file")
else:
    print("❌ Could not find target line")
