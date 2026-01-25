#!/usr/bin/env python3
"""
Queen Power Dashboard - Integrated View
Shows Queen's power redistribution + live power monitoring in one interface.

Real-time display of:
- Queen's redistribution decisions
- Energy flow across relays
- Net energy gained vs drains avoided
- Power station output
- Scanning system metrics
"""

import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        def _is_buffer_valid(stream):
            if not hasattr(stream, 'buffer'):
                return False
            try:
                return stream.buffer is not None and not stream.buffer.closed
            except (ValueError, AttributeError):
                return False
        if _is_buffer_valid(sys.stdout) and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if _is_buffer_valid(sys.stderr) and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, Optional


def load_json_safe(filepath: str, default=None) -> Dict:
    """Load JSON file safely with fallback."""
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}


def format_usd(value: float) -> str:
    """Format USD value with color."""
    if value > 0:
        return f"\033[92m${value:.2f}\033[0m"  # Green
    elif value < 0:
        return f"\033[91m${value:.2f}\033[0m"  # Red
    else:
        return f"${value:.2f}"


def format_pct(value: float) -> str:
    """Format percentage with color."""
    if value > 0:
        return f"\033[92m+{value:.2f}%\033[0m"  # Green
    elif value < 0:
        return f"\033[91m{value:.2f}%\033[0m"  # Red
    else:
        return f"{value:.2f}%"


class QueenPowerDashboard:
    """
    Integrated dashboard showing Queen's intelligence in action.
    """
    
    def __init__(self):
        self.last_update = 0
        self.update_interval = 3  # seconds
        self.cycle_count = 0
        self.start_time = time.time()
    
    def get_queen_redistribution_state(self) -> Dict:
        """Get Queen's redistribution state."""
        state = load_json_safe('queen_redistribution_state.json', {
            'last_update': 0.0,
            'total_net_energy_gained': 0.0,
            'total_blocked_drains_avoided': 0.0,
            'decisions_count': 0,
            'executions_count': 0,
            'recent_decisions': [],
            'recent_executions': []
        })
        
        # Calculate time since last update (heartbeat)
        last_update = state.get('last_update', 0.0)
        if last_update > 0:
            state['seconds_since_update'] = time.time() - last_update
            state['is_alive'] = state['seconds_since_update'] < 60  # Active if updated in last minute
        else:
            state['seconds_since_update'] = 999999
            state['is_alive'] = False
        
        return state
    
    def get_power_station_state(self) -> Dict:
        """Get power station state."""
        return load_json_safe('power_station_state.json', {
            'status': 'UNKNOWN',
            'cycles_run': 0,
            'total_energy_now': 0.0,
            'energy_deployed': 0.0,
            'net_flow': 0.0,
            'efficiency': 0.0
        })
    
    def get_relay_energy(self, relay: str) -> Dict:
        """Get energy status for a relay."""
        if relay == 'BIN':
            state = load_json_safe('binance_truth_tracker_state.json', {})
            total = state.get('total_balance_usd', 0.0)
            free_usdt = state.get('balances', {}).get('USDT', {}).get('free', 0.0)
            positions = total - free_usdt
            return {
                'total': total,
                'idle': free_usdt,
                'positions': positions,
                'idle_pct': (free_usdt / total * 100) if total > 0 else 0
            }
        
        elif relay == 'KRK':
            state = load_json_safe('aureon_kraken_state.json', {})
            free_usd = state.get('balances', {}).get('ZUSD', 0.0)
            # Calculate total from all positions
            total = free_usd
            positions_value = 0.0
            for asset, bal in state.get('balances', {}).items():
                if asset != 'ZUSD' and isinstance(bal, (int, float)) and bal > 0:
                    # Approximate USD value (simplified)
                    positions_value += bal
            total += positions_value
            return {
                'total': total,
                'idle': free_usd,
                'positions': positions_value,
                'idle_pct': (free_usd / total * 100) if total > 0 else 0
            }
        
        elif relay == 'ALP':
            state = load_json_safe('alpaca_truth_tracker_state.json', {})
            cash = state.get('cash', 0.0)
            equity = state.get('equity', 0.0)
            positions = equity - cash
            return {
                'total': equity,
                'idle': cash,
                'positions': positions,
                'idle_pct': (cash / equity * 100) if equity > 0 else 0
            }
        
        elif relay == 'CAP':
            # Capital.com: simplified (no state file yet)
            return {
                'total': 92.66,
                'idle': 92.66,
                'positions': 0.0,
                'idle_pct': 100.0
            }
        
        return {'total': 0.0, 'idle': 0.0, 'positions': 0.0, 'idle_pct': 0.0}
    
    def display_header(self):
        """Display dashboard header."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        runtime = time.time() - self.start_time
        runtime_str = f"{int(runtime//60)}m {int(runtime%60)}s"
        
        print("\033[2J\033[H")  # Clear screen
        print("\n")
        print("┏" + "━" * 78 + "┓")
        print(f"┃  🐝 QUEEN POWER DASHBOARD{' ' * 51}┃")
        print("┠" + "─" * 78 + "┨")
        print(f"┃  📅 {now}  ⏱️  Runtime: {runtime_str:<10} 🔄 Cycle: #{self.cycle_count:<6}┃")
        print("┗" + "━" * 78 + "┛")
        print()
    
    def display_queen_intelligence(self):
        """Display Queen's redistribution intelligence."""
        state = self.get_queen_redistribution_state()
        
        net_gained = state.get('total_net_energy_gained', 0.0)
        drains_avoided = state.get('total_blocked_drains_avoided', 0.0)
        decisions = state.get('decisions_count', 0)
        executions = state.get('executions_count', 0)
        seconds_since = state.get('seconds_since_update', 999999)
        is_alive = state.get('is_alive', False)
        
        # Heartbeat indicator
        if is_alive:
            heartbeat = "\033[92m💚 ACTIVE\033[0m"
            status_msg = f"\033[90m(updated {seconds_since:.0f}s ago)\033[0m"
        else:
            heartbeat = "\033[91m💔 IDLE\033[0m"
            status_msg = "\033[90m(no recent activity)\033[0m"
        
        print("┏" + "━" * 78 + "┓")
        print("┃  🐝 QUEEN'S REDISTRIBUTION ENGINE" + " " * 43 + "┃")
        print("┗" + "━" * 78 + "┛")
        print()
        print(f"  ⚡ Engine Status:       {heartbeat} {status_msg}")
        print()
        print("  💰 Financial Performance:")
        print(f"     ├─ Net Energy Gained:        {format_usd(net_gained)}")
        print(f"     ├─ Drains Blocked:           {format_usd(drains_avoided)}")
        print(f"     └─ Total Conserved:          {format_usd(net_gained + drains_avoided)}")
        print()
        print("  📈 Decision Metrics:")
        print(f"     ├─ Total Decisions:          {decisions}")
        print(f"     ├─ Executed Orders:          {executions}")
        print(f"     └─ Execution Rate:           {(executions/decisions*100 if decisions > 0 else 0):.1f}%")
        
        # Show efficiency (gained vs total conserved)
        total_conserved = net_gained + drains_avoided
        if total_conserved > 0:
            efficiency = (net_gained / total_conserved * 100)
            efficiency_bar = "█" * int(efficiency / 10) + "░" * (10 - int(efficiency / 10))
            print()
            print(f"  🎯 Queen Efficiency:     {efficiency:.1f}% [{efficiency_bar}]")
        
        # Show recent decisions
        recent = state.get('recent_decisions', [])
        if recent:
            print()
            print("  📊 Recent Decisions:")
            for i, dec in enumerate(recent[-3:], 1):
                opp = dec.get('opportunity', {})
                decision = dec.get('decision', 'UNKNOWN')
                relay = opp.get('relay', '???')
                target = opp.get('target_asset', '???')
                net_gain = opp.get('net_energy_gain', 0.0)
                confidence = dec.get('queen_confidence', 0.0)
                
                decision_icon = "✅" if decision == 'EXECUTE' else "🚫"
                decision_color = '\033[92m' if decision == 'EXECUTE' else '\033[91m'
                conf_bar = "●" * int(confidence * 5) + "○" * (5 - int(confidence * 5))
                
                prefix = "     └─" if i == len(recent[-3:]) else "     ├─"
                print(f"{prefix} {decision_icon} {decision_color}{decision:<8}\033[0m │ {relay} → {target:<12} │ {format_usd(net_gain):<12} │ Confidence: {conf_bar}")
        else:
            print()
            print("  📊 \033[90m🔍 Scanning for profitable opportunities...\033[0m")
        print()
    
    def display_power_station(self):
        """Display power station output."""
        state = self.get_power_station_state()
        
        status = state.get('status', 'UNKNOWN')
        cycles = state.get('cycles_run', 0)
        total_energy = state.get('total_energy_now', 0.0)
        deployed = state.get('energy_deployed', 0.0)
        net_flow = state.get('net_flow', 0.0)
        efficiency = state.get('efficiency', 0.0)
        
        status_icon = "🟢" if status == 'RUNNING' else "🟡"
        status_color = '\033[92m' if status == 'RUNNING' else '\033[93m'
        
        print("┏" + "━" * 78 + "┓")
        print("┃  ⚡ POWER STATION" + " " * 59 + "┃")
        print("┗" + "━" * 78 + "┛")
        print()
        print(f"  {status_icon} Station Status:      {status_color}{status}\033[0m  \033[90m({cycles} cycles completed)\033[0m")
        print()
        print("  💎 Energy Reserves:")
        print(f"     ├─ Total Energy:             {format_usd(total_energy)}")
        print(f"     ├─ Currently Deployed:       {format_usd(deployed)}")
        print(f"     └─ Net Flow (24h):           {format_usd(net_flow)}")
        print()
        efficiency_bar = "█" * int(efficiency / 10) + "░" * (10 - int(efficiency / 10))
        print(f"  📊 Efficiency:           {efficiency:.1f}% [{efficiency_bar}]")
        print()
    
    def display_relay_status(self):
        """Display status of all relays."""
        print("┏" + "━" * 78 + "┓")
        print("┃  🔌 RELAY ENERGY STATUS" + " " * 52 + "┃")
        print("┗" + "━" * 78 + "┛")
        print()
        print("  \033[90m(Internal isolation: Energy moves within relay only)\033[0m")
        print()
        
        relays = ['BIN', 'KRK', 'ALP', 'CAP']
        relay_names = {'BIN': 'Binance', 'KRK': 'Kraken', 'ALP': 'Alpaca', 'CAP': 'Capital'}
        total_system_energy = 0.0
        total_idle_energy = 0.0
        
        print(f"  {'RELAY':<10} {'TOTAL':<12} {'IDLE':<12} {'POSITIONS':<12} {'MOBILITY':<20}")
        print("  " + "─" * 74)
        
        for relay in relays:
            energy = self.get_relay_energy(relay)
            total = energy['total']
            idle = energy['idle']
            positions = energy['positions']
            idle_pct = energy['idle_pct']
            
            total_system_energy += total
            total_idle_energy += idle
            
            # Mobility indicator
            if idle_pct > 50:
                mobility = "\033[92m🟢 HIGH\033[0m"
                mobility_bar = "█" * 5
            elif idle_pct > 10:
                mobility = "\033[93m🟡 MED\033[0m"
                mobility_bar = "█" * 3 + "░" * 2
            else:
                mobility = "\033[91m🔴 LOW\033[0m"
                mobility_bar = "█" + "░" * 4
            
            total_str = f"${total:.2f}"
            idle_str = f"${idle:.2f}"
            pos_str = f"${positions:.2f}"
            
            print(f"  {relay:<10} {total_str:<12} {idle_str:<12} {pos_str:<12} {mobility} [{mobility_bar}] {idle_pct:.0f}%")
        
        print("  " + "─" * 74)
        total_idle_pct = (total_idle_energy/total_system_energy*100 if total_system_energy > 0 else 0)
        print(f"  {'TOTAL':<10} ${total_system_energy:<11.2f} ${total_idle_energy:<11.2f} ${total_system_energy-total_idle_energy:<11.2f} \033[96m⚡ System: {total_idle_pct:.0f}% idle\033[0m")
        print()
    
    def display_energy_conservation(self):
        """Display energy conservation metrics."""
        queen_state = self.get_queen_redistribution_state()
        net_gained = queen_state.get('total_net_energy_gained', 0.0)
        drains_avoided = queen_state.get('total_blocked_drains_avoided', 0.0)
        
        total_conserved = net_gained + drains_avoided
        
        print("┏" + "━" * 78 + "┓")
        print("┃  🌿 ENERGY CONSERVATION" + " " * 52 + "┃")
        print("┗" + "━" * 78 + "┛")
        print()
        
        if total_conserved > 0:
            efficiency = (net_gained / total_conserved * 100)
            print(f"  💎 Net Energy Gained:        {format_usd(net_gained)}")
            print(f"  🛡️  Drains Blocked:           {format_usd(drains_avoided)}")
            print(f"  ✨ Total Conserved:           {format_usd(total_conserved)}")
            print()
            efficiency_bar = "█" * int(efficiency / 10) + "░" * (10 - int(efficiency / 10))
            print(f"  📊 Conservation Rate:        {efficiency:.1f}% [{efficiency_bar}]")
            print(f"     \033[90m(Net gained / Total conserved)\033[0m")
        else:
            print(f"  💎 Net Energy Gained:        {format_usd(net_gained)}")
            print(f"  🛡️  Drains Blocked:           {format_usd(drains_avoided)}")
            print(f"  ✨ Total Conserved:           {format_usd(total_conserved)}")
            print()
            print("  \033[90m📈 Begin trading to track conservation metrics\033[0m")
        print()
    
    async def run(self):
        """Run continuous dashboard updates."""
        print("🐝 Queen Power Dashboard starting...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                self.cycle_count += 1
                
                self.display_header()
                self.display_queen_intelligence()
                self.display_power_station()
                self.display_relay_status()
                self.display_energy_conservation()
                
                print("┏" + "━" * 78 + "┓")
                print(f"┃  ⏳ Next update in {self.update_interval}s" + " " * 33 + "\033[90mPress Ctrl+C to stop\033[0m" + " " * 3 + "┃")
                print("┗" + "━" * 78 + "┛")
                print()
                
                await asyncio.sleep(self.update_interval)
        
        except KeyboardInterrupt:
            print("\n\n🛑 Dashboard stopped by user")


async def main():
    import argparse
    parser = argparse.ArgumentParser(description="Queen Power Dashboard")
    parser.add_argument('--interval', type=int, default=3, help='Update interval in seconds (default: 3)')
    args = parser.parse_args()
    
    dashboard = QueenPowerDashboard()
    dashboard.update_interval = args.interval
    
    await dashboard.run()


if __name__ == '__main__':
    asyncio.run(main())
