#!/usr/bin/env python3
"""
⚡ AUREON POWER MONITOR - LIVE ENERGY REDISTRIBUTION ⚡

Real-time monitoring of ALL energy streams across ALL exchanges.
Pulls metrics from scanning systems and power station.
Shows EXACTLY what's happening before ANY action.
"""
import sys, os
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        if hasattr(sys.stdout, 'buffer') and sys.stdout.buffer:
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and sys.stderr.buffer:
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except:
        pass

import json
import time
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path

# Exchange clients
try:
    from binance_client import BinanceClient
    BIN_AVAILABLE = True
except:
    BIN_AVAILABLE = False

try:
    from kraken_client import KrakenClient
    KRK_AVAILABLE = True
except:
    KRK_AVAILABLE = False

try:
    from alpaca_client import AlpacaClient
    ALP_AVAILABLE = True
except:
    ALP_AVAILABLE = False

try:
    from capital_client import CapitalClient
    CAP_AVAILABLE = True
except:
    CAP_AVAILABLE = False


@dataclass
class EnergyStream:
    """Real-time energy flow for one relay"""
    name: str
    connected: bool
    balance_usd: float
    positions_value: float
    total_energy: float
    idle_energy: float  # Not deployed
    deployed_energy: float
    positions: List[Dict]
    last_update: float
    update_latency_ms: float


@dataclass
class ScannerMetrics:
    """Metrics from scanning systems"""
    opportunities_found: int
    validated_branches: int
    coherence_avg: float
    pip_targets: List[float]
    last_scan: float


@dataclass
class PowerStationMetrics:
    """Power station output metrics"""
    total_system_energy: float
    energy_in_motion: float
    energy_idle: float
    drain_rate_per_hour: float
    net_flow_24h: float
    cycles_run: int
    blocked_operations: int


class LivePowerMonitor:
    """
    Real-time energy redistribution monitor.
    Shows ALL energy streams across ALL relays.
    """
    
    def __init__(self):
        self.streams: Dict[str, EnergyStream] = {}
        self.scanner_metrics: Optional[ScannerMetrics] = None
        self.power_metrics: Optional[PowerStationMetrics] = None
        self.clients: Dict[str, any] = {}
        self.running = False
        
        # State files for scanners
        self.state_files = {
            'kraken': Path('aureon_kraken_state.json'),
            'pending': Path('7day_pending_validations.json'),
            'coherence': Path('coherence_history.json'),
            'power_station': Path('power_station_state.json'),
        }
        
        self._init_clients()
    
    def _init_clients(self):
        """Initialize all exchange clients"""
        if BIN_AVAILABLE:
            try:
                self.clients['BIN'] = BinanceClient()
            except:
                pass
        
        if KRK_AVAILABLE:
            try:
                self.clients['KRK'] = KrakenClient()
            except:
                pass
        
        if ALP_AVAILABLE:
            try:
                self.clients['ALP'] = AlpacaClient()
            except:
                pass
        
        if CAP_AVAILABLE:
            try:
                self.clients['CAP'] = CapitalClient()
            except:
                pass
    
    def get_binance_stream(self) -> EnergyStream:
        """Get real-time Binance energy stream"""
        start = time.time()
        
        try:
            client = self.clients.get('BIN')
            if not client:
                return EnergyStream('BIN', False, 0, 0, 0, 0, 0, [], time.time(), 0)
            
            balance = client.get_balance()
            
            total_usd = 0
            positions = []
            usdt_balance = 0
            
            for asset, amount in balance.items():
                if amount > 0.001:
                    if asset in ['USDT', 'USD', 'BUSD', 'USDC']:
                        usd_val = amount
                        usdt_balance += amount
                    else:
                        try:
                            ticker = client.get_ticker(f'{asset}USDT')
                            price = float(ticker.get('last', 0))
                            usd_val = amount * price
                            if usd_val > 0.10:
                                positions.append({
                                    'symbol': asset,
                                    'amount': amount,
                                    'value_usd': usd_val,
                                    'price': price,
                                })
                        except:
                            usd_val = 0
                    total_usd += usd_val
            
            positions_value = sum(p['value_usd'] for p in positions)
            latency = (time.time() - start) * 1000
            
            return EnergyStream(
                name='BIN',
                connected=True,
                balance_usd=usdt_balance,
                positions_value=positions_value,
                total_energy=total_usd,
                idle_energy=usdt_balance,
                deployed_energy=positions_value,
                positions=positions,
                last_update=time.time(),
                update_latency_ms=latency,
            )
        
        except Exception as e:
            return EnergyStream('BIN', False, 0, 0, 0, 0, 0, [], time.time(), 0)
    
    def get_kraken_stream(self) -> EnergyStream:
        """Get Kraken energy from state file (API rate limited)"""
        start = time.time()
        
        try:
            if not self.state_files['kraken'].exists():
                return EnergyStream('KRK', False, 0, 0, 0, 0, 0, [], time.time(), 0)
            
            with open(self.state_files['kraken']) as f:
                state = json.load(f)
            
            balance = state.get('balance', 0)
            positions = []
            positions_value = 0
            
            for sym, pos in state.get('positions', {}).items():
                if pos.get('exchange') == 'kraken':
                    val = pos.get('entry_value', 0)
                    positions_value += val
                    positions.append({
                        'symbol': sym,
                        'value_usd': val,
                        'size': pos.get('size', 0),
                    })
            
            total = balance + positions_value
            latency = (time.time() - start) * 1000
            
            return EnergyStream(
                name='KRK',
                connected=True,
                balance_usd=balance,
                positions_value=positions_value,
                total_energy=total,
                idle_energy=balance,
                deployed_energy=positions_value,
                positions=positions,
                last_update=time.time(),
                update_latency_ms=latency,
            )
        
        except:
            return EnergyStream('KRK', False, 0, 0, 0, 0, 0, [], time.time(), 0)
    
    def get_alpaca_stream(self) -> EnergyStream:
        """Get real-time Alpaca energy stream"""
        start = time.time()
        
        try:
            client = self.clients.get('ALP')
            if not client:
                return EnergyStream('ALP', False, 0, 0, 0, 0, 0, [], time.time(), 0)
            
            account = client.get_account()
            equity = float(account.get('equity', 0))
            cash = float(account.get('cash', 0))
            
            # Get positions
            try:
                positions_raw = client.get_positions()
                positions = []
                positions_value = 0
                
                for pos in positions_raw:
                    val = float(pos.get('market_value', 0))
                    positions_value += abs(val)
                    positions.append({
                        'symbol': pos.get('symbol'),
                        'value_usd': val,
                        'qty': float(pos.get('qty', 0)),
                    })
            except:
                positions = []
                positions_value = 0
            
            latency = (time.time() - start) * 1000
            
            return EnergyStream(
                name='ALP',
                connected=True,
                balance_usd=cash,
                positions_value=positions_value,
                total_energy=equity,
                idle_energy=cash,
                deployed_energy=positions_value,
                positions=positions,
                last_update=time.time(),
                update_latency_ms=latency,
            )
        
        except:
            return EnergyStream('ALP', False, 0, 0, 0, 0, 0, [], time.time(), 0)
    
    def get_capital_stream(self) -> EnergyStream:
        """Get real-time Capital.com energy stream"""
        start = time.time()
        
        try:
            client = self.clients.get('CAP')
            if not client:
                return EnergyStream('CAP', False, 0, 0, 0, 0, 0, [], time.time(), 0)
            
            accounts = client.get_accounts()
            balance_gbp = 0
            
            for acc in (accounts if isinstance(accounts, list) else [accounts]):
                balance_gbp += float(acc.get('balance', 0))
            
            balance_usd = balance_gbp * 1.25  # GBP to USD
            
            # Get positions
            try:
                positions_raw = client.get_positions()
                positions = []
                positions_value = 0
                
                for pos in positions_raw:
                    # TODO: Calculate position value
                    pass
            except:
                positions = []
                positions_value = 0
            
            latency = (time.time() - start) * 1000
            
            return EnergyStream(
                name='CAP',
                connected=True,
                balance_usd=balance_usd,
                positions_value=positions_value,
                total_energy=balance_usd,
                idle_energy=balance_usd,
                deployed_energy=positions_value,
                positions=positions,
                last_update=time.time(),
                update_latency_ms=latency,
            )
        
        except:
            return EnergyStream('CAP', False, 0, 0, 0, 0, 0, [], time.time(), 0)
    
    def get_scanner_metrics(self) -> ScannerMetrics:
        """Get metrics from scanning systems"""
        try:
            # Check pending validations
            opportunities = 0
            validated = 0
            coherence_vals = []
            pip_targets = []
            
            if self.state_files['pending'].exists():
                with open(self.state_files['pending']) as f:
                    pending = json.load(f)
                    opportunities = len(pending)
                    for branch_id, data in pending.items():
                        if data.get('validation_passes', 0) >= 3:
                            validated += 1
                        if 'coherence' in data:
                            coherence_vals.append(data['coherence'])
                        if 'pip_score' in data:
                            pip_targets.append(data['pip_score'])
            
            coherence_avg = sum(coherence_vals) / len(coherence_vals) if coherence_vals else 0
            
            return ScannerMetrics(
                opportunities_found=opportunities,
                validated_branches=validated,
                coherence_avg=coherence_avg,
                pip_targets=pip_targets,
                last_scan=time.time(),
            )
        
        except:
            return ScannerMetrics(0, 0, 0, [], time.time())
    
    def get_power_station_metrics(self) -> PowerStationMetrics:
        """Get power station metrics"""
        try:
            if not self.state_files['power_station'].exists():
                # Calculate from streams
                total = sum(s.total_energy for s in self.streams.values())
                idle = sum(s.idle_energy for s in self.streams.values())
                deployed = sum(s.deployed_energy for s in self.streams.values())
                
                return PowerStationMetrics(
                    total_system_energy=total,
                    energy_in_motion=deployed,
                    energy_idle=idle,
                    drain_rate_per_hour=0,
                    net_flow_24h=0,
                    cycles_run=0,
                    blocked_operations=0,
                )
            
            with open(self.state_files['power_station']) as f:
                state = json.load(f)
            
            return PowerStationMetrics(
                total_system_energy=state.get('total_energy_now', 0),
                energy_in_motion=state.get('total_energy_now', 0),
                energy_idle=0,
                drain_rate_per_hour=0,
                net_flow_24h=state.get('net_flow', 0),
                cycles_run=state.get('cycles_run', 0),
                blocked_operations=state.get('blocked_operations', 0),
            )
        
        except:
            total = sum(s.total_energy for s in self.streams.values())
            idle = sum(s.idle_energy for s in self.streams.values())
            deployed = sum(s.deployed_energy for s in self.streams.values())
            
            return PowerStationMetrics(
                total_system_energy=total,
                energy_in_motion=deployed,
                energy_idle=idle,
                drain_rate_per_hour=0,
                net_flow_24h=0,
                cycles_run=0,
                blocked_operations=0,
            )
    
    def update_all_streams(self):
        """Update all energy streams"""
        self.streams['BIN'] = self.get_binance_stream()
        self.streams['KRK'] = self.get_kraken_stream()
        self.streams['ALP'] = self.get_alpaca_stream()
        self.streams['CAP'] = self.get_capital_stream()
        
        self.scanner_metrics = self.get_scanner_metrics()
        self.power_metrics = self.get_power_station_metrics()
    
    def display_live(self):
        """Display live power monitor"""
        # Clear screen
        print("\033[2J\033[H", end="")
        
        print("=" * 90)
        print("⚡🔋 LIVE POWER MONITOR - ENERGY REDISTRIBUTION 🔋⚡")
        print("=" * 90)
        print(f"  Updated: {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        # System totals
        total = sum(s.total_energy for s in self.streams.values())
        idle = sum(s.idle_energy for s in self.streams.values())
        deployed = sum(s.deployed_energy for s in self.streams.values())
        
        print("📊 SYSTEM ENERGY")
        print("─" * 90)
        print(f"  TOTAL:    ${total:>12.2f}")
        print(f"  IDLE:     ${idle:>12.2f}  ({idle/total*100 if total > 0 else 0:>5.1f}%)")
        print(f"  DEPLOYED: ${deployed:>12.2f}  ({deployed/total*100 if total > 0 else 0:>5.1f}%)")
        print()
        
        # Per-relay streams - INTERNAL ENERGY ONLY
        print("🔌 RELAY ENERGY STREAMS (INTERNAL REDISTRIBUTION)")
        print("─" * 90)
        print("  ⚠️  Each relay is ISOLATED - energy moves WITHIN relay only")
        print()
        
        for name in ['BIN', 'KRK', 'ALP', 'CAP']:
            stream = self.streams.get(name)
            if not stream or not stream.connected:
                print(f"  🔴 {name}: OFFLINE")
                continue
            
            conn = "🟢"
            pct_deployed = (stream.deployed_energy / stream.total_energy * 100) if stream.total_energy > 0 else 0
            pct_idle = (stream.idle_energy / stream.total_energy * 100) if stream.total_energy > 0 else 0
            
            # Energy mobility status
            if stream.idle_energy < 1:
                mobility = "⚠️ LOCKED (no USDT/USD to move)"
            elif pct_idle > 50:
                mobility = "✅ HIGH MOBILITY"
            elif pct_idle > 20:
                mobility = "🟡 MODERATE"
            else:
                mobility = "🔴 LOW"
            
            print(f"  {conn} {name}: ${stream.total_energy:>10.2f} | Idle: ${stream.idle_energy:>8.2f} ({pct_idle:.0f}%) | Deployed: ${stream.deployed_energy:>8.2f} ({pct_deployed:.0f}%) | {mobility}")
            
            # Show top positions - these can be CONVERTED internally
            for pos in stream.positions[:3]:
                sym = pos.get('symbol', '???')[:8]
                val = pos.get('value_usd', 0)
                print(f"      ↳ {sym:8} ${val:>8.2f}  [can convert to other assets on {name}]")
        
        print()
        
        # Scanner metrics
        if self.scanner_metrics:
            print("🔍 SCANNING SYSTEMS")
            print("─" * 90)
            print(f"  Opportunities Found: {self.scanner_metrics.opportunities_found}")
            print(f"  Validated Branches:  {self.scanner_metrics.validated_branches}")
            print(f"  Avg Coherence:       {self.scanner_metrics.coherence_avg:.3f}")
            if self.scanner_metrics.pip_targets:
                print(f"  PIP Targets:         {min(self.scanner_metrics.pip_targets):.4f} - {max(self.scanner_metrics.pip_targets):.4f}")
            print()
        
        # Power station
        if self.power_metrics:
            print("⚡ POWER STATION OUTPUT")
            print("─" * 90)
            print(f"  Cycles Run:          {self.power_metrics.cycles_run}")
            print(f"  Blocked Operations:  {self.power_metrics.blocked_operations}")
            print(f"  Net Flow (24h):      ${self.power_metrics.net_flow_24h:>+10.2f}")
            print()
        
        # Internal conversion opportunities
        print("🔄 INTERNAL RELAY OPPORTUNITIES")
        print("─" * 90)
        for name in ['BIN', 'KRK', 'ALP', 'CAP']:
            stream = self.streams.get(name)
            if not stream or not stream.connected:
                continue
            
            if stream.idle_energy < 1:
                print(f"  {name}: ⚠️  Need to SELL positions to get USDT for conversions")
            elif len(stream.positions) == 0:
                print(f"  {name}: ✅ ${stream.idle_energy:.2f} ready to BUY assets")
            else:
                print(f"  {name}: 🔄 Can convert {len(stream.positions)} positions to other assets")
        
        print()
        
        print("=" * 90)
        print("  Press Ctrl+C to stop")
    
    async def run_live(self, interval: float = 2.0):
        """Run live monitoring loop"""
        self.running = True
        
        print("\n⚡ STARTING LIVE POWER MONITOR ⚡")
        print(f"  Update interval: {interval}s")
        print()
        
        try:
            while self.running:
                self.update_all_streams()
                self.display_live()
                await asyncio.sleep(interval)
        
        except KeyboardInterrupt:
            print("\n\n⚡ MONITOR STOPPED ⚡")
            self.running = False


async def main():
    """Run live monitor"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Live Power Monitor")
    parser.add_argument("--interval", type=float, default=2.0, help="Update interval in seconds")
    args = parser.parse_args()
    
    monitor = LivePowerMonitor()
    await monitor.run_live(interval=args.interval)


if __name__ == "__main__":
    asyncio.run(main())
