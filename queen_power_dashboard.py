#!/usr/bin/env python3
"""
⚡ AUREON POWER STATION - MAIN ENERGY INTERFACE ⚡

Everything is Energy. This is the primary dashboard for all system activity.

Real-time Energy Visualization:
- Total System Energy (all balances)
- Energy Flow (in/out per relay)
- Energy Generation (profits/gains)
- Energy Consumption (fees/drains)
- Energy Reserves (idle capital)
- Energy Deployment (active positions)
- Queen's Energy Decisions
- System Power Output

All trading activity, balances, profits, and losses shown as ENERGY.
Port: 8080 (Primary Interface)
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

from aiohttp import web

# Global reference to dashboard for web handlers
_dashboard_instance = None


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
    ⚡ PRIMARY ENERGY INTERFACE ⚡
    Everything displayed as energy flows and reserves.
    """
    
    def __init__(self):
        self.last_update = 0
        self.update_interval = 3  # seconds
        self.cycle_count = 0
        self.start_time = time.time()
        self.total_energy_at_start = 0.0
        self._cached_nodes = []
        self._cache_time = 0
        self._cache_ttl = 30  # Refresh every 30 seconds
        
        # Initialize the redistribution scanner for LIVE data
        self.scanner = None
        self._init_scanner()
        
        # Calculate baseline energy
        self._calculate_baseline_energy()
    
    def _init_scanner(self):
        """Initialize the Queen Power Redistribution scanner for live data."""
        try:
            from queen_power_redistribution import QueenPowerRedistribution
            self.scanner = QueenPowerRedistribution(dry_run=True)
            print("✅ Queen Power Scanner initialized - LIVE data enabled")
        except Exception as e:
            print(f"⚠️ Scanner init failed: {e} - using fallback state files")
            self.scanner = None
    
    def _get_live_nodes(self):
        """Get live energy nodes from scanner (cached)."""
        now = time.time()
        if now - self._cache_time > self._cache_ttl:
            if self.scanner:
                try:
                    self._cached_nodes = self.scanner.scan_all_energy_nodes()
                    self._cache_time = now
                    print(f"📊 Scanned {len(self._cached_nodes)} live nodes")
                except Exception as e:
                    print(f"⚠️ Scan failed: {e}")
        return self._cached_nodes
    
    def _calculate_baseline_energy(self):
        """Calculate total system energy at startup."""
        total = 0.0
        for relay in ['BIN', 'KRK', 'ALP', 'CAP']:
            energy = self.get_relay_energy(relay)
            total += energy['total']
        self.total_energy_at_start = total
    
    def get_total_system_energy(self) -> Dict:
        """Get comprehensive system energy metrics."""
        relays = ['BIN', 'KRK', 'ALP', 'CAP']
        
        total_energy = 0.0
        total_reserves = 0.0
        total_deployed = 0.0
        relay_breakdown = {}
        
        for relay in relays:
            energy = self.get_relay_energy(relay)
            total_energy += energy['total']
            total_reserves += energy['idle']
            total_deployed += energy['positions']
            relay_breakdown[relay] = energy
        
        # Get Queen's energy metrics
        queen_state = self.get_queen_redistribution_state()
        net_gained = queen_state.get('total_net_energy_gained', 0.0)
        drains_avoided = queen_state.get('total_blocked_drains_avoided', 0.0)
        
        # Calculate system growth
        energy_growth = total_energy - self.total_energy_at_start
        
        return {
            'total_energy': total_energy,
            'total_reserves': total_reserves,
            'total_deployed': total_deployed,
            'reserve_percentage': (total_reserves / total_energy * 100) if total_energy > 0 else 0,
            'deployed_percentage': (total_deployed / total_energy * 100) if total_energy > 0 else 0,
            'net_energy_gained': net_gained,
            'energy_conserved': drains_avoided,
            'energy_growth': energy_growth,
            'growth_percentage': (energy_growth / self.total_energy_at_start * 100) if self.total_energy_at_start > 0 else 0,
            'relay_breakdown': relay_breakdown
        }
    
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
        """Get energy status for a relay using LIVE scanner data."""
        # Map relay codes
        relay_map = {'BIN': 'BIN', 'KRK': 'KRK', 'ALP': 'ALP', 'CAP': 'CAP'}
        relay_code = relay_map.get(relay, relay)
        
        # Get live nodes from scanner
        nodes = self._get_live_nodes()
        
        # Filter nodes for this relay
        relay_nodes = [n for n in nodes if n.relay == relay_code]
        
        if relay_nodes:
            total = sum(n.position_value_usd for n in relay_nodes)
            # Idle = positive energy (profitable positions available to redistribute)
            idle = sum(n.energy_available_to_redistribute for n in relay_nodes)
            positions_count = len(relay_nodes)
            return {
                'total': total,
                'idle': idle,
                'positions': total,  # All deployed
                'positions_count': positions_count,
                'idle_pct': (idle / total * 100) if total > 0 else 0
            }
        
        # Fallback: Try state files
        if relay == 'BIN':
            state = load_json_safe('binance_truth_tracker_state.json', {})
            total = state.get('total_balance_usd', 0.0)
            free_usdt = state.get('balances', {}).get('USDT', {}).get('free', 0.0)
            positions = total - free_usdt
            return {
                'total': total,
                'idle': free_usdt,
                'positions': positions,
                'positions_count': 0,
                'idle_pct': (free_usdt / total * 100) if total > 0 else 0
            }
        
        elif relay == 'KRK':
            state = load_json_safe('aureon_kraken_state.json', {})
            free_usd = state.get('balances', {}).get('ZUSD', 0.0)
            total = free_usd
            positions_value = 0.0
            for asset, bal in state.get('balances', {}).items():
                if asset != 'ZUSD' and isinstance(bal, (int, float)) and bal > 0:
                    positions_value += bal
            total += positions_value
            return {
                'total': total,
                'idle': free_usd,
                'positions': positions_value,
                'positions_count': 0,
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
                'positions_count': 0,
                'idle_pct': (cash / equity * 100) if equity > 0 else 0
            }
        
        elif relay == 'CAP':
            # Capital.com: Try to get from global financial state
            state = load_json_safe('global_financial_state.json', {})
            cap_balance = state.get('capital_balance', 92.66)
            return {
                'total': cap_balance,
                'idle': cap_balance,
                'positions': 0.0,
                'positions_count': 0,
                'idle_pct': 100.0
            }
        
        return {'total': 0.0, 'idle': 0.0, 'positions': 0.0, 'positions_count': 0, 'idle_pct': 0.0}
    
    def display_header(self):
        """Display dashboard header with total system energy."""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        runtime = time.time() - self.start_time
        runtime_str = f"{int(runtime//60)}m {int(runtime%60)}s"
        
        # Get total system energy
        energy_data = self.get_total_system_energy()
        total_energy = energy_data['total_energy']
        energy_growth = energy_data['energy_growth']
        growth_pct = energy_data['growth_percentage']
        
        # Energy growth indicator
        if energy_growth > 0:
            growth_icon = "⚡📈"
            growth_color = '\033[92m'  # Green
        elif energy_growth < 0:
            growth_icon = "⚠️📉"
            growth_color = '\033[91m'  # Red
        else:
            growth_icon = "⚡━"
            growth_color = '\033[93m'  # Yellow
        
        print("\033[2J\033[H")  # Clear screen
        print("\n")
        print("╔" + "═" * 78 + "╗")
        print(f"║  ⚡ AUREON POWER STATION - PRIMARY ENERGY INTERFACE{' ' * 26}║")
        print("╠" + "═" * 78 + "╣")
        print(f"║  📅 {now}  ⏱️  Runtime: {runtime_str:<10} 🔄 Cycle: #{self.cycle_count:<6}║")
        print("╠" + "─" * 78 + "╣")
        print(f"║  💎 Total System Energy: {format_usd(total_energy):<15} {growth_icon} Growth: {growth_color}{format_usd(energy_growth):>10}\033[0m ({growth_pct:+.2f}%)  ║")
        print("╚" + "═" * 78 + "╝")
        print()
    
    def display_queen_intelligence(self):
        """Display Queen's energy generation intelligence."""
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
        
        # Calculate Queen efficiency (energy generated per decision)
        if decisions > 0:
            efficiency = (net_gained + drains_avoided) / decisions
        else:
            efficiency = 0.0
        
        print("╔" + "═" * 78 + "╗")
        print("║  🐝 QUEEN ENERGY GENERATION INTELLIGENCE" + " " * 36 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print(f"  ⚡ Engine Status:       {heartbeat} {status_msg}")
        print()
        print(f"  📊 Energy Generation Summary:")
        print(f"     ├─ ⚡ Energy Generated:      {format_usd(net_gained):<15} (Net positive moves)")
        print(f"     ├─ 🛡️  Energy Conserved:      {format_usd(drains_avoided):<15} (Blocked drains)")
        print(f"     └─ 💎 Total Energy Impact:   {format_usd(net_gained + drains_avoided)}")
        print()
        print(f"  🎯 Queen Performance:")
        print(f"     ├─ Decisions Analyzed:      {decisions} opportunities")
        print(f"     ├─ Energy Moves Executed:   {executions} redistributions")
        print(f"     └─ Efficiency:              {format_usd(efficiency)} per decision")
        
        # Show recent decisions
        recent = state.get('recent_decisions', [])
        if recent:
            print()
            print("  📊 Recent Energy Decisions:")
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
                print(f"{prefix} {decision_icon} {decision_color}{decision:<8}\033[0m │ {relay} → {target:<12} │ {format_usd(net_gain):<12} │ {conf_bar}")
        else:
            print()
            print("  📊 \033[90m🔍 Scanning for profitable opportunities...\033[0m")
        print()
    
    def display_power_station(self):
        """Display power station energy flow."""
        state = self.get_power_station_state()
        
        status = state.get('status', 'UNKNOWN')
        cycles = state.get('cycles_run', 0)
        total_energy = state.get('total_energy_now', 0.0)
        deployed = state.get('energy_deployed', 0.0)
        net_flow = state.get('net_flow', 0.0)
        efficiency = state.get('efficiency', 0.0)
        
        status_icon = "🟢" if status == 'RUNNING' else "🟡"
        status_color = '\033[92m' if status == 'RUNNING' else '\033[93m'
        
        print("╔" + "═" * 78 + "╗")
        print("║  ⚡ ENERGY RESERVES & FLOW" + " " * 50 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print(f"  {status_icon} Power Station Status:  {status_color}{status}\033[0m  \033[90m({cycles} energy cycles)\033[0m")
        print()
        print("  💎 System Energy Status:")
        print(f"     ├─ Total Energy Reserves:    {format_usd(total_energy)}")
        print(f"     ├─ Energy in Positions:      {format_usd(deployed)}")
        print(f"     └─ Net Energy Flow (24h):    {format_usd(net_flow)}")
        print()
        efficiency_bar = "█" * int(efficiency / 10) + "░" * (10 - int(efficiency / 10))
        print(f"  📊 Energy Efficiency:         {efficiency:.1f}% [{efficiency_bar}]")
        print()
    
    def display_relay_status(self):
        """Display energy distribution across relays."""
        print("╔" + "═" * 78 + "╗")
        print("║  🔌 ENERGY DISTRIBUTION BY RELAY" + " " * 44 + "║")
        print("╚" + "═" * 78 + "╝")
        print()
        print("  \033[90m(Each relay operates independently with internal energy isolation)\033[0m")
        print()
        
        relays = ['BIN', 'KRK', 'ALP', 'CAP']
        relay_names = {'BIN': 'Binance', 'KRK': 'Kraken', 'ALP': 'Alpaca', 'CAP': 'Capital'}
        total_system_energy = 0.0
        total_idle_energy = 0.0
        
        print(f"  {'RELAY':<10} {'TOTAL':<12} {'IDLE':<12} {'DEPLOYED':<12} {'MOBILITY':<20}")
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
        """Display energy conservation and generation metrics."""
        queen_state = self.get_queen_redistribution_state()
        net_gained = queen_state.get('total_net_energy_gained', 0.0)
        drains_avoided = queen_state.get('total_blocked_drains_avoided', 0.0)
        
        total_conserved = net_gained + drains_avoided
        
        print("╔" + "═" * 78 + "╗")
        print("║  🌿 ENERGY CONSERVATION & GENERATION" + " " * 40 + "║")
        print("╚" + "═" * 78 + "╝")
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
    
    def get_dashboard_data(self) -> Dict:
        """Get dashboard data as dict for web API."""
        energy = self.get_total_system_energy()
        queen_state = self.get_queen_redistribution_state()
        
        # Get relay breakdown
        relays = {}
        for relay_code in ['BIN', 'KRK', 'ALP', 'CAP']:
            relay_energy = self.get_relay_energy(relay_code)
            relays[relay_code] = {
                'total': relay_energy.get('total', 0),
                'idle': relay_energy.get('idle', 0),
                'positions': relay_energy.get('positions', 0),
                'positions_count': relay_energy.get('positions_count', 0),
            }
        
        return {
            'timestamp': time.time(),
            'cycle': self.cycle_count,
            'uptime_seconds': time.time() - self.start_time,
            'total_energy': energy.get('total_energy', 0),
            'total_reserves': energy.get('total_reserves', 0),
            'total_deployed': energy.get('total_deployed', 0),
            'net_energy_gained': energy.get('net_energy_gained', 0),
            'energy_conserved': energy.get('energy_conserved', 0),
            'energy_growth': energy.get('energy_growth', 0),
            'growth_percentage': energy.get('growth_percentage', 0),
            'relays': relays,
            'queen': {
                'decisions_count': queen_state.get('decisions_count', 0),
                'net_gained': queen_state.get('total_net_energy_gained', 0),
                'drains_avoided': queen_state.get('total_blocked_drains_avoided', 0),
            }
        }
    
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


# ═══════════════════════════════════════════════════════════════════════════════
# WEB SERVER - Health Check & API for DigitalOcean
# ═══════════════════════════════════════════════════════════════════════════════

async def handle_health(request):
    """Health check endpoint for DigitalOcean."""
    global _dashboard_instance
    
    health_data = {
        'status': 'healthy',
        'service': 'queen-power-dashboard',
        'timestamp': datetime.utcnow().isoformat(),
        'uptime_seconds': time.time() - _dashboard_instance.start_time if _dashboard_instance else 0,
        'cycle_count': _dashboard_instance.cycle_count if _dashboard_instance else 0,
    }
    
    return web.json_response(health_data)


async def handle_api_status(request):
    """Get full dashboard status as JSON."""
    global _dashboard_instance
    
    if not _dashboard_instance:
        return web.json_response({'error': 'Dashboard not initialized'}, status=503)
    
    data = _dashboard_instance.get_dashboard_data()
    return web.json_response(data)


async def handle_root(request):
    """Serve HTML dashboard."""
    html = """<!DOCTYPE html>
<html>
<head>
    <title>⚡ Queen Power Station</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <style>
        body { 
            background: #0a0a0a; 
            color: #00ff88; 
            font-family: 'Courier New', monospace;
            padding: 20px;
            margin: 0;
        }
        .header { 
            text-align: center; 
            border: 2px solid #00ff88;
            padding: 20px;
            margin-bottom: 20px;
        }
        .relay-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        .relay-card {
            background: #111;
            border: 1px solid #333;
            padding: 15px;
            border-radius: 5px;
        }
        .relay-card h3 { margin: 0 0 10px 0; }
        .value { font-size: 1.5em; font-weight: bold; }
        .positive { color: #00ff88; }
        .negative { color: #ff4444; }
        .neutral { color: #888; }
        .stats { margin-top: 20px; }
        .stat-row { 
            display: flex; 
            justify-content: space-between;
            padding: 5px 0;
            border-bottom: 1px solid #222;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>⚡ QUEEN POWER STATION ⚡</h1>
        <p>Energy-Based Trading Dashboard</p>
    </div>
    
    <div id="status">Loading...</div>
    
    <script>
        async function updateStatus() {
            try {
                const resp = await fetch('/api/status');
                const data = await resp.json();
                
                const growth = data.growth_percentage || 0;
                const growthClass = growth > 0 ? 'positive' : growth < 0 ? 'negative' : 'neutral';
                
                let html = `
                    <div class="relay-grid">
                        <div class="relay-card">
                            <h3>💰 Total Energy</h3>
                            <div class="value">$${(data.total_energy || 0).toFixed(2)}</div>
                        </div>
                        <div class="relay-card">
                            <h3>⚡ Reserves</h3>
                            <div class="value">$${(data.total_reserves || 0).toFixed(2)}</div>
                        </div>
                        <div class="relay-card">
                            <h3>🎯 Deployed</h3>
                            <div class="value">$${(data.total_deployed || 0).toFixed(2)}</div>
                        </div>
                        <div class="relay-card">
                            <h3>📈 Growth</h3>
                            <div class="value ${growthClass}">${growth >= 0 ? '+' : ''}${growth.toFixed(2)}%</div>
                        </div>
                    </div>
                    
                    <h2>🔌 Relay Status</h2>
                    <div class="relay-grid">
                `;
                
                const relayNames = {BIN: '🟡 Binance', KRK: '🔵 Kraken', ALP: '🟢 Alpaca', CAP: '🏛️ Capital'};
                for (const [code, name] of Object.entries(relayNames)) {
                    const relay = data.relays?.[code] || {};
                    html += `
                        <div class="relay-card">
                            <h3>${name}</h3>
                            <div class="stat-row"><span>Total:</span><span>$${(relay.total || 0).toFixed(2)}</span></div>
                            <div class="stat-row"><span>Idle:</span><span>$${(relay.idle || 0).toFixed(2)}</span></div>
                            <div class="stat-row"><span>Positions:</span><span>${relay.positions_count || 0}</span></div>
                        </div>
                    `;
                }
                
                html += `</div>
                    <div class="stats">
                        <h2>🐝 Queen Intelligence</h2>
                        <div class="stat-row"><span>Decisions Made:</span><span>${data.queen?.decisions_count || 0}</span></div>
                        <div class="stat-row"><span>Net Energy Gained:</span><span class="positive">$${(data.queen?.net_gained || 0).toFixed(2)}</span></div>
                        <div class="stat-row"><span>Drains Avoided:</span><span class="positive">$${(data.queen?.drains_avoided || 0).toFixed(2)}</span></div>
                    </div>
                    
                    <p style="color: #666; margin-top: 20px;">
                        Cycle: ${data.cycle || 0} | 
                        Uptime: ${Math.floor((data.uptime_seconds || 0) / 60)}m | 
                        Last Update: ${new Date(data.timestamp * 1000).toLocaleTimeString()}
                    </p>
                `;
                
                document.getElementById('status').innerHTML = html;
            } catch (err) {
                document.getElementById('status').innerHTML = '<p class="negative">Error loading status: ' + err + '</p>';
            }
        }
        
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>"""
    return web.Response(text=html, content_type='text/html')


async def start_web_server(dashboard, port):
    """Start aiohttp web server."""
    app = web.Application()
    app.router.add_get('/', handle_root)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/api/status', handle_api_status)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    print(f"🌐 Web server started on http://0.0.0.0:{port}")
    print(f"   💚 Health: http://localhost:{port}/health")
    print(f"   📊 Status: http://localhost:{port}/api/status")
    
    return runner


async def main():
    global _dashboard_instance
    
    import argparse
    parser = argparse.ArgumentParser(description="Queen Power Dashboard")
    parser.add_argument('--interval', type=int, default=3, help='Update interval in seconds (default: 3)')
    parser.add_argument('--port', type=int, default=8080, help='Web server port (default: 8080)')
    parser.add_argument('--no-console', action='store_true', help='Disable console output')
    args = parser.parse_args()
    
    port = int(os.environ.get('PORT', args.port))
    
    dashboard = QueenPowerDashboard()
    dashboard.update_interval = args.interval
    _dashboard_instance = dashboard
    
    # Start web server
    runner = await start_web_server(dashboard, port)
    
    try:
        if args.no_console:
            # Just keep updating cycle count for health checks
            print("🐝 Queen Power Dashboard running (console disabled)")
            while True:
                dashboard.cycle_count += 1
                await asyncio.sleep(dashboard.update_interval)
        else:
            # Run console dashboard
            await dashboard.run()
    finally:
        await runner.cleanup()


if __name__ == '__main__':
    asyncio.run(main())
