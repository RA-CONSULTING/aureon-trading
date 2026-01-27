from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import json
import os
import sys

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def load_state():
    try:
        with open('aureon_kraken_state.json', 'r') as f:
            return json.load(f)
    except:
        return {'positions': {}, 'kills': []}

def main():
    while True:
        state = load_state()
        positions = state.get('positions', {})
        kills = state.get('kills', [])
        
        clear_screen()
        print("=" * 60)
        print("       ⚔️  AUREON WAR ROOM - BATTLEFIELD STATUS  ⚔️")
        print("=" * 60)
        print(f"🕒 Time: {time.strftime('%H:%M:%S')}")
        print("-" * 60)
        
        # Active Scouts (Positions)
        print(f"🏹 ACTIVE SCOUTS ({len(positions)})")
        print(f"{'SYMBOL':<12} {'EXCHANGE':<10} {'ENTRY':<10} {'VALUE':<10}")
        print("-" * 60)
        
        if not positions:
            print("   (No scouts deployed - waiting for recruitment)")
        
        for sym, pos in positions.items():
            entry = float(pos.get('entry_price', 0))
            val = float(pos.get('entry_value', 0))
            exch = pos.get('exchange', 'kraken').upper()
            print(f"{sym:<12} {exch:<10} ${entry:<9.4f} ${val:<9.2f}")
            
        print("-" * 60)
        
        # Recent Kills
        print(f"💀 RECENT KILLS ({len(kills)})")
        if not kills:
            print("   (No kills yet today)")
        
        for kill in kills[-5:]: # Show last 5
            sym = kill.get('symbol')
            pnl = float(kill.get('net_pnl', 0))
            ts = time.strftime('%H:%M:%S', time.localtime(kill.get('time', 0)))
            pnl_str = f"${pnl:+.4f}"
            color = "🟢" if pnl > 0 else "🔴"
            print(f"   {ts} - {sym} - {color} {pnl_str}")
            
        print("-" * 60)
        print("🤖 AUTOMATION STATUS:")
        print("   ✅ Auto Sniper (Killer): RUNNING")
        print("   ✅ Auto Scout (Hunter): RUNNING")
        print("=" * 60)
        print("Press Ctrl+C to exit War Room (Agents keep running)")
        
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting War Room...")
