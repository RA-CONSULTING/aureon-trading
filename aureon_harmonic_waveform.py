#!/usr/bin/env python3
"""
🌊👑 QUEEN SERO'S HARMONIC WAVEFORM - COMPLETE FIELD VIEW 👑🌊
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

THE ENTIRE QUANTUM FIELD AS ONE HARMONIC WAVEFORM
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

PERSPECTIVE SHIFT:
    We don't see "positions" - we see FREQUENCY NODES in a HARMONIC FIELD
    We don't see "prices" - we see RESONANCE FREQUENCIES
    We don't see "profit/loss" - we see POWER PHASE (+/- from baseline)
    
    The entire portfolio is ONE WAVEFORM oscillating through quantum space.

FREQUENCY CALCULATIONS:
    Base Frequency = Entry Price (where we tuned in)
    Current Frequency = Current Price (where it resonates now)
    Frequency Shift = (Current - Entry) / Entry × 100 (phase shift %)
    
    Harmonic Position = Where in the wave cycle (PEAK, RISING, TROUGH, FALLING)
    
SACRED FREQUENCIES:
    7.83 Hz  = Schumann Resonance (Earth's heartbeat)
    432 Hz   = Universal tuning (A=432)
    528 Hz   = Love frequency (DNA repair)
    φ (PHI)  = 1.618 Golden Ratio (harmonic proportion)

NODE LABELING:
    [RELAY]-[ID]-[SYMBOL]
    e.g., KRK-001-DASHUSD, BIN-003-GUNUSDT, ALP-002-BTCUSD

Gary Leckey | Harmonic Waveform System | January 2026
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
"""

import sys
import os
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

import json
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from decimal import Decimal, ROUND_DOWN
from enum import Enum

# Exchange clients
from binance_client import BinanceClient
from kraken_client import KrakenClient
from alpaca_client import AlpacaClient
from capital_client import CapitalClient
from cost_basis_tracker import CostBasisTracker

# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
# SACRED FREQUENCIES & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2           # 1.618033988749895 - Golden Ratio
SCHUMANN = 7.83                         # Hz - Earth's heartbeat
LOVE_FREQ = 528                         # Hz - DNA repair frequency
UNIVERSAL_A = 432                       # Hz - Universal tuning
SOLFEGGIO = [174, 285, 396, 417, 528, 639, 741, 852, 963]  # Healing frequencies


class WavePhase(Enum):
    """Position in the harmonic wave cycle"""
    PEAK = "🏔️ PEAK"           # At maximum, reversal likely
    RISING = "📈 RISING"        # Moving up toward peak
    TROUGH = "🌊 TROUGH"        # At minimum, reversal likely
    FALLING = "📉 FALLING"      # Moving down toward trough
    RESONATING = "🎵 RESONATING" # In harmonic alignment
    DORMANT = "💤 DORMANT"      # Very low energy, waiting


class PowerState(Enum):
    """Power generation state"""
    GENERATING = "⚡+"         # Outputting power (positive)
    NEUTRAL = "⚪○"           # Equilibrium (zero)
    CONSUMING = "🔴-"         # Absorbing power (negative)
    DORMANT = "💤~"           # Near-zero, hibernating


@dataclass
class HarmonicNode:
    """A frequency node in the harmonic field"""
    
    # IDENTITY
    node_id: str              # Unique: KRK-001, BIN-003, etc.
    relay_code: str           # KRK, BIN, ALP, CAP
    sequence: int             # Node number within relay
    symbol: str               # Trading symbol
    base_asset: str           # Base currency/asset
    quote_asset: str          # Quote currency
    
    # FREQUENCY METRICS (the core truth)
    entry_frequency: float    # Base resonance (entry price)
    current_frequency: float  # Current resonance (current price)
    frequency_shift: float    # Phase shift % from entry
    
    # ENERGY METRICS
    amount: float             # Quantity held
    entry_energy: float       # Entry value (entry_freq × amount)
    current_energy: float     # Current value (current_freq × amount)
    power: float              # Power = current - entry (can be negative)
    power_percent: float      # Power as % of entry
    extractable: float        # Surplus available for redistribution
    
    # WAVE POSITION
    wave_phase: WavePhase     # Where in the cycle
    power_state: PowerState   # Generating/consuming/neutral
    
    # HARMONIC ANALYSIS
    phi_alignment: float      # Alignment with golden ratio (0-1)
    schumann_harmonic: int    # Which Schumann harmonic (1-12)
    solfeggio_resonance: str  # Nearest solfeggio frequency
    
    # TIMESTAMPS
    entry_time: float = 0     # When node was created
    last_update: float = 0    # Last data update


@dataclass
class HarmonicRelay:
    """A relay point in the harmonic field (exchange)"""
    
    code: str                 # KRK, BIN, ALP, CAP
    name: str                 # Full name
    nodes: List[HarmonicNode] = field(default_factory=list)
    free_energy: float = 0.0  # Unallocated energy
    
    # Aggregates
    total_nodes: int = 0
    generating: int = 0
    consuming: int = 0
    dormant: int = 0
    
    total_energy: float = 0.0
    total_power: float = 0.0
    total_extractable: float = 0.0
    
    # Status
    is_online: bool = False
    last_sync: float = 0


@dataclass
class HarmonicField:
    """The complete harmonic waveform - entire quantum field"""
    
    relays: Dict[str, HarmonicRelay] = field(default_factory=dict)
    all_nodes: List[HarmonicNode] = field(default_factory=list)
    
    # FIELD TOTALS
    total_nodes: int = 0
    total_energy: float = 0.0
    total_free_energy: float = 0.0
    total_power: float = 0.0
    total_extractable: float = 0.0
    
    # STATE COUNTS
    generating_nodes: int = 0
    consuming_nodes: int = 0
    dormant_nodes: int = 0
    
    # HARMONIC METRICS
    dominant_frequency: float = 432.0     # Weighted average frequency
    field_coherence: float = 0.0          # How aligned nodes are
    phi_resonance: float = 0.0            # Golden ratio alignment
    schumann_alignment: float = 0.0       # Earth resonance alignment
    
    # WAVEFORM SHAPE
    wave_amplitude: float = 0.0           # Peak-to-trough range
    wave_center: float = 0.0              # Midpoint of oscillation
    nodes_above_center: int = 0
    nodes_below_center: int = 0


class HarmonicWaveformScanner:
    """
    Scans the quantum field and presents it as ONE HARMONIC WAVEFORM.
    
    Every position is a frequency node.
    The portfolio is a superposition of waves.
    Power flows through harmonic channels.
    """
    
    RELAY_CODES = {
        'binance': 'BIN',
        'kraken': 'KRK',
        'alpaca': 'ALP',
        'capital': 'CAP'
    }
    
    def __init__(self):
        self.binance = BinanceClient()
        self.kraken = KrakenClient()
        self.alpaca = AlpacaClient()
        self.capital = CapitalClient()
        self.cost_basis = CostBasisTracker()
        
        self.field = HarmonicField()
        self.node_counter = {'BIN': 0, 'KRK': 0, 'ALP': 0, 'CAP': 0}
        
    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert to float"""
        if value is None:
            return default
        try:
            return float(value)
        except:
            return default
    
    def _parse_symbol(self, symbol: str) -> Tuple[str, str]:
        """Parse symbol into base/quote"""
        quotes = ['USDT', 'USDC', 'USD', 'EUR', 'GBP', 'ZUSD', 'BTC', 'ETH', 'BUSD']
        for quote in quotes:
            if symbol.endswith(quote):
                return symbol[:-len(quote)], quote
        if '/' in symbol:
            parts = symbol.split('/')
            return parts[0], parts[1] if len(parts) > 1 else 'USD'
        return symbol, 'USD'
    
    def _generate_node_id(self, relay_code: str) -> Tuple[str, int]:
        """Generate unique node ID"""
        self.node_counter[relay_code] += 1
        seq = self.node_counter[relay_code]
        node_id = f"{relay_code}-{seq:03d}"
        return node_id, seq
    
    def _calculate_wave_phase(self, freq_shift: float) -> WavePhase:
        """Determine position in wave cycle based on frequency shift"""
        if freq_shift > 20:
            return WavePhase.PEAK
        elif freq_shift > 5:
            return WavePhase.RISING
        elif freq_shift > -5:
            return WavePhase.RESONATING
        elif freq_shift > -20:
            return WavePhase.FALLING
        else:
            return WavePhase.TROUGH
    
    def _calculate_power_state(self, power: float, current_energy: float) -> PowerState:
        """Determine power generation state"""
        if current_energy < 0.01:
            return PowerState.DORMANT
        elif power > 0.01:
            return PowerState.GENERATING
        elif power < -0.01:
            return PowerState.CONSUMING
        else:
            return PowerState.NEUTRAL
    
    def _calculate_phi_alignment(self, freq_shift: float) -> float:
        """Calculate alignment with golden ratio"""
        # How close is the shift to a PHI-based value?
        phi_values = [PHI, PHI * 10, PHI * 100, 1/PHI, 1/PHI * 10]
        min_distance = min(abs(abs(freq_shift) - pv) for pv in phi_values)
        # Normalize to 0-1 (closer = higher alignment)
        return max(0, 1 - (min_distance / 100))
    
    def _calculate_schumann_harmonic(self, frequency: float) -> int:
        """Find which Schumann harmonic the frequency aligns with"""
        # Schumann harmonics: 7.83, 14.3, 20.8, 27.3, 33.8...
        for i in range(1, 13):
            harmonic = SCHUMANN * i
            # Check if frequency (scaled) aligns
            scaled_freq = frequency % 100  # Simplistic scaling
            if abs(scaled_freq - harmonic) < 2:
                return i
        return 0
    
    def _find_solfeggio_resonance(self, frequency: float) -> str:
        """Find nearest solfeggio frequency"""
        scaled = frequency % 1000  # Scale to solfeggio range
        closest = min(SOLFEGGIO, key=lambda x: abs(x - scaled))
        names = {
            174: "UT", 285: "RE", 396: "MI", 417: "FA",
            528: "LOVE", 639: "SOL", 741: "LA", 852: "SI", 963: "OM"
        }
        return names.get(closest, "~")
    
    def _create_harmonic_node(
        self,
        relay_code: str,
        symbol: str,
        amount: float,
        entry_price: float,
        current_price: float,
        entry_time: float = 0
    ) -> Optional[HarmonicNode]:
        """Create a fully calculated harmonic node"""
        
        if amount == 0 or entry_price == 0:
            return None
        
        # Use entry if current is 0
        if current_price == 0:
            current_price = entry_price
        
        # Generate ID
        node_id, sequence = self._generate_node_id(relay_code)
        base, quote = self._parse_symbol(symbol)
        
        # FREQUENCY CALCULATIONS
        entry_frequency = entry_price
        current_frequency = current_price
        frequency_shift = ((current_price - entry_price) / entry_price) * 100
        
        # ENERGY CALCULATIONS
        entry_energy = entry_price * amount
        current_energy = current_price * amount
        power = current_energy - entry_energy
        power_percent = (power / entry_energy) * 100 if entry_energy > 0 else 0
        
        # EXTRACTABLE (keep 1% safety buffer)
        safety_buffer = entry_energy * 0.01
        extractable = max(0, power - safety_buffer)
        
        # WAVE POSITION
        wave_phase = self._calculate_wave_phase(frequency_shift)
        power_state = self._calculate_power_state(power, current_energy)
        
        if current_energy < 0.01:
            wave_phase = WavePhase.DORMANT
        
        # HARMONIC ANALYSIS
        phi_alignment = self._calculate_phi_alignment(frequency_shift)
        schumann_harmonic = self._calculate_schumann_harmonic(current_frequency)
        solfeggio_resonance = self._find_solfeggio_resonance(current_frequency)
        
        return HarmonicNode(
            node_id=node_id,
            relay_code=relay_code,
            sequence=sequence,
            symbol=symbol,
            base_asset=base,
            quote_asset=quote,
            entry_frequency=entry_frequency,
            current_frequency=current_frequency,
            frequency_shift=frequency_shift,
            amount=amount,
            entry_energy=entry_energy,
            current_energy=current_energy,
            power=power,
            power_percent=power_percent,
            extractable=extractable,
            wave_phase=wave_phase,
            power_state=power_state,
            phi_alignment=phi_alignment,
            schumann_harmonic=schumann_harmonic,
            solfeggio_resonance=solfeggio_resonance,
            entry_time=entry_time,
            last_update=time.time()
        )
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # RELAY SCANNERS
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def scan_binance_relay(self) -> HarmonicRelay:
        """Scan Binance as harmonic relay"""
        relay = HarmonicRelay(code='BIN', name='Binance')
        
        try:
            balances = self.binance.get_balance()
            positions = self.cost_basis.positions
            stables = ['USDT', 'USDC', 'USD', 'EUR', 'GBP', 'BUSD', 'FDUSD']
            
            # Batch fetch all tickers for speed
            all_tickers = {}
            try:
                tickers = self.binance.get_24h_tickers()
                for t in tickers:
                    all_tickers[t['symbol']] = self._safe_float(t.get('lastPrice', 0))
            except Exception as e:
                print(f"   ⚠️ Couldn't fetch all Binance tickers: {e}")
            
            for asset, amount_raw in balances.items():
                amount = self._safe_float(amount_raw)
                
                if asset in stables:
                    if amount > 0.001:
                        relay.free_energy += amount
                    continue
                
                if amount < 0.00000001:
                    continue
                
                # Find entry price from cost basis
                entry_price = 0.0
                for key, pos in positions.items():
                    if 'binance' in key.lower() and asset.upper() in key.upper():
                        entry_price = self._safe_float(
                            pos.get('avg_entry_price', pos.get('average_entry_price', pos.get('price', 0)))
                        )
                        break
                
                # Get current price from batch tickers
                symbol = f"{asset}USDT"
                current_price = all_tickers.get(symbol, 0.0)
                
                # Fallback to individual ticker if batch didn't have it
                if current_price == 0:
                    try:
                        ticker = self.binance.get_ticker(symbol=symbol)
                        if ticker:
                            current_price = self._safe_float(ticker.get('last', ticker.get('price', 0)))
                    except:
                        pass
                
                if entry_price == 0 and current_price > 0:
                    entry_price = current_price
                
                if current_price == 0:
                    continue
                
                node = self._create_harmonic_node('BIN', symbol, amount, entry_price, current_price)
                if node:
                    relay.nodes.append(node)
            
            relay.is_online = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Binance relay error: {e}")
        
        self._aggregate_relay(relay)
        return relay
    
    def scan_kraken_relay(self) -> HarmonicRelay:
        """Scan Kraken as harmonic relay"""
        relay = HarmonicRelay(code='KRK', name='Kraken')
        
        try:
            state_file = 'aureon_kraken_state.json'
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                relay.free_energy = self._safe_float(state.get('balance', 0))
                
                positions = state.get('positions', {})
                for symbol, pos in positions.items():
                    if pos.get('exchange', 'kraken') != 'kraken':
                        continue
                    
                    amount = self._safe_float(pos.get('quantity', pos.get('amount', 0)))
                    entry_price = self._safe_float(pos.get('entry_price', 0))
                    entry_time = self._safe_float(pos.get('entry_time', 0))
                    
                    # Try to get current price from API
                    current_price = entry_price
                    try:
                        ticker = self.kraken.get_ticker(symbol)
                        if ticker:
                            current_price = self._safe_float(
                                ticker.get('last', ticker.get('c', [entry_price])[0] if isinstance(ticker.get('c'), list) else entry_price)
                            )
                    except:
                        pass
                    
                    node = self._create_harmonic_node('KRK', symbol, amount, entry_price, current_price, entry_time)
                    if node:
                        relay.nodes.append(node)
            
            relay.is_online = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Kraken relay error: {e}")
        
        self._aggregate_relay(relay)
        return relay
    
    def scan_alpaca_relay(self) -> HarmonicRelay:
        """Scan Alpaca as harmonic relay"""
        relay = HarmonicRelay(code='ALP', name='Alpaca')
        
        try:
            positions = self.alpaca.get_positions()
            
            for pos in positions:
                symbol = pos.get('symbol', '')
                amount = self._safe_float(pos.get('qty', 0))
                entry_price = self._safe_float(pos.get('avg_entry_price', 0))
                current_price = self._safe_float(pos.get('current_price', entry_price))
                
                node = self._create_harmonic_node('ALP', symbol, amount, entry_price, current_price)
                if node:
                    relay.nodes.append(node)
            
            try:
                account = self.alpaca.get_account()
                if account:
                    relay.free_energy = self._safe_float(account.get('cash', 0))
            except:
                pass
            
            relay.is_online = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Alpaca relay error: {e}")
        
        self._aggregate_relay(relay)
        return relay
    
    def scan_capital_relay(self) -> HarmonicRelay:
        """Scan Capital.com as harmonic relay"""
        relay = HarmonicRelay(code='CAP', name='Capital.com')
        
        try:
            positions = self.capital.get_positions()
            
            if positions:
                for pos in positions:
                    symbol = pos.get('market', {}).get('instrumentName', pos.get('epic', ''))
                    amount = abs(self._safe_float(pos.get('position', {}).get('size', pos.get('size', 0))))
                    entry_price = self._safe_float(pos.get('position', {}).get('openLevel', pos.get('level', 0)))
                    
                    node = self._create_harmonic_node('CAP', symbol, amount, entry_price, entry_price)
                    if node:
                        relay.nodes.append(node)
            
            relay.is_online = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Capital relay error: {e}")
        
        self._aggregate_relay(relay)
        return relay
    
    def _aggregate_relay(self, relay: HarmonicRelay):
        """Calculate relay aggregates"""
        relay.total_nodes = len(relay.nodes)
        relay.generating = sum(1 for n in relay.nodes if n.power_state == PowerState.GENERATING)
        relay.consuming = sum(1 for n in relay.nodes if n.power_state == PowerState.CONSUMING)
        relay.dormant = sum(1 for n in relay.nodes if n.power_state == PowerState.DORMANT)
        
        relay.total_energy = sum(n.current_energy for n in relay.nodes)
        relay.total_power = sum(n.power for n in relay.nodes)
        relay.total_extractable = sum(n.extractable for n in relay.nodes)
    
    def scan_complete_field(self) -> HarmonicField:
        """SCAN THE ENTIRE HARMONIC FIELD"""
        
        print("\n" + "🌊"*60)
        print("   SCANNING QUEEN SERO'S HARMONIC WAVEFORM")
        print("🌊"*60 + "\n")
        
        # Reset counters
        self.node_counter = {'BIN': 0, 'KRK': 0, 'ALP': 0, 'CAP': 0}
        self.field = HarmonicField()
        
        # Scan each relay
        print("📡 Connecting to BIN (Binance)...")
        self.field.relays['BIN'] = self.scan_binance_relay()
        
        print("📡 Connecting to KRK (Kraken)...")
        self.field.relays['KRK'] = self.scan_kraken_relay()
        
        print("📡 Connecting to ALP (Alpaca)...")
        self.field.relays['ALP'] = self.scan_alpaca_relay()
        
        print("📡 Connecting to CAP (Capital.com)...")
        self.field.relays['CAP'] = self.scan_capital_relay()
        
        # Collect all nodes
        for relay in self.field.relays.values():
            self.field.all_nodes.extend(relay.nodes)
        
        # Field aggregates
        self.field.total_nodes = len(self.field.all_nodes)
        self.field.total_energy = sum(r.total_energy for r in self.field.relays.values())
        self.field.total_free_energy = sum(r.free_energy for r in self.field.relays.values())
        self.field.total_power = sum(r.total_power for r in self.field.relays.values())
        self.field.total_extractable = sum(r.total_extractable for r in self.field.relays.values())
        
        self.field.generating_nodes = sum(r.generating for r in self.field.relays.values())
        self.field.consuming_nodes = sum(r.consuming for r in self.field.relays.values())
        self.field.dormant_nodes = sum(r.dormant for r in self.field.relays.values())
        
        # Harmonic metrics
        if self.field.total_nodes > 0:
            self.field.field_coherence = self.field.generating_nodes / self.field.total_nodes
            self.field.phi_resonance = sum(n.phi_alignment for n in self.field.all_nodes) / self.field.total_nodes
        
        # Dominant frequency (energy-weighted)
        if self.field.total_energy > 0:
            self.field.dominant_frequency = sum(
                n.current_frequency * n.current_energy for n in self.field.all_nodes
            ) / self.field.total_energy
        
        # Wave shape
        shifts = [n.frequency_shift for n in self.field.all_nodes if n.current_energy > 0.01]
        if shifts:
            self.field.wave_amplitude = max(shifts) - min(shifts)
            self.field.wave_center = sum(shifts) / len(shifts)
            self.field.nodes_above_center = sum(1 for s in shifts if s > self.field.wave_center)
            self.field.nodes_below_center = sum(1 for s in shifts if s <= self.field.wave_center)
        
        return self.field
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # DISPLAY - THE COMPLETE HARMONIC VIEW
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def display_harmonic_waveform(self):
        """Display the complete harmonic waveform"""
        
        f = self.field
        
        print("\n")
        print("╔" + "═"*128 + "╗")
        print("║" + " "*128 + "║")
        print("║" + "🌊👑 QUEEN SERO'S HARMONIC WAVEFORM - COMPLETE FIELD VIEW 👑🌊".center(128) + "║")
        print("║" + " "*128 + "║")
        print("╚" + "═"*128 + "╝")
        
        # FIELD OVERVIEW
        print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              🌊 HARMONIC FIELD OVERVIEW 🌊                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  FIELD TOPOLOGY                                           │  POWER FLOW                                                            │
│  ─────────────────────────────────────────────────────    │  ──────────────────────────────────────────────────────────────────    │
│  Total Nodes:          {f.total_nodes:>6}                              │  Total Energy:        {f.total_energy:>12.4f} units                              │
│  ├─ Generating (⚡+):  {f.generating_nodes:>6}                              │  Free Energy:         {f.total_free_energy:>12.4f} units                              │
│  ├─ Consuming (🔴-):   {f.consuming_nodes:>6}                              │  Total Power:         {f.total_power:>+12.4f} units                              │
│  ├─ Dormant (💤~):     {f.dormant_nodes:>6}                              │  Extractable:         {f.total_extractable:>12.4f} units                              │
│  └─ Active:            {f.total_nodes - f.dormant_nodes:>6}                              │                                                                        │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  HARMONIC METRICS                                         │  WAVEFORM SHAPE                                                        │
│  ─────────────────────────────────────────────────────    │  ──────────────────────────────────────────────────────────────────    │
│  Dominant Frequency:   {f.dominant_frequency:>12.4f} Hz                    │  Wave Amplitude:      {f.wave_amplitude:>+12.2f}%                                   │
│  Field Coherence:      {f.field_coherence:>12.2%}                      │  Wave Center:         {f.wave_center:>+12.2f}%                                   │
│  PHI Resonance:        {f.phi_resonance:>12.4f}                          │  Above Center:        {f.nodes_above_center:>6} nodes                                  │
│  Schumann Base:        {SCHUMANN:>12.2f} Hz                    │  Below Center:        {f.nodes_below_center:>6} nodes                                  │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
""")
        
        # RELAY STATUS
        print("┌" + "─"*128 + "┐")
        print("│" + "📡 RELAY STATUS".center(128) + "│")
        print("├────────┬──────────┬───────┬────────┬────────┬─────────────┬─────────────┬─────────────┬────────────────────────────────┤")
        print("│ RELAY  │ STATUS   │ NODES │ ⚡+ GEN│ 🔴- CON│    ENERGY   │    POWER    │    FREE     │ DOMINANT FREQ                  │")
        print("├────────┼──────────┼───────┼────────┼────────┼─────────────┼─────────────┼─────────────┼────────────────────────────────┤")
        
        for code, relay in f.relays.items():
            status = "✅ ONLINE" if relay.is_online else "❌ OFFLINE"
            dom_freq = sum(n.current_frequency * n.current_energy for n in relay.nodes) / relay.total_energy if relay.total_energy > 0 else 0
            print(f"│ {code:<6} │ {status:<8} │ {relay.total_nodes:>5} │ {relay.generating:>6} │ {relay.consuming:>6} │ {relay.total_energy:>11.2f} │ {relay.total_power:>+11.2f} │ {relay.free_energy:>11.2f} │ {dom_freq:>30.4f} │")
        
        print("├────────┴──────────┴───────┴────────┴────────┴─────────────┴─────────────┴─────────────┴────────────────────────────────┤")
        print(f"│ {'TOTAL':<8} {'':8}  {f.total_nodes:>5}   {f.generating_nodes:>6}   {f.consuming_nodes:>6}   {f.total_energy:>11.2f}   {f.total_power:>+11.2f}   {f.total_free_energy:>11.2f}                                  │")
        print("└" + "─"*128 + "┘")
        
        # COMPLETE NODE INVENTORY
        print("\n")
        print("┌" + "─"*128 + "┐")
        print("│" + "⚡ COMPLETE HARMONIC NODE INVENTORY ⚡".center(128) + "│")
        print("└" + "─"*128 + "┘")
        
        for code, relay in f.relays.items():
            if relay.total_nodes == 0:
                continue
            
            print(f"\n{'═'*130}")
            print(f"  📡 {relay.name} ({code}) - {relay.total_nodes} Nodes | Free Energy: {relay.free_energy:.4f}")
            print(f"{'═'*130}")
            print(f"{'ID':<10} {'SYMBOL':<15} {'STATE':<6} {'PHASE':<12} {'ENTRY FREQ':<12} {'CURR FREQ':<12} {'SHIFT':<10} {'POWER':<12} {'PHI':<6} {'SOL':<6}")
            print(f"{'─'*130}")
            
            # Sort by frequency shift (highest first)
            sorted_nodes = sorted(relay.nodes, key=lambda n: n.frequency_shift, reverse=True)
            
            for node in sorted_nodes:
                print(f"{node.node_id:<10} {node.symbol:<15} {node.power_state.value:<6} {node.wave_phase.value:<12} {node.entry_frequency:>11.6f} {node.current_frequency:>11.6f} {node.frequency_shift:>+9.2f}% {node.power:>+11.4f} {node.phi_alignment:>5.2f} {node.solfeggio_resonance:<6}")
            
            print(f"{'─'*130}")
            print(f"{'':10} {'RELAY TOTAL':<15} {'':6} {'':12} {'':12} {'':12} {'':10} {relay.total_power:>+11.4f}")
        
        # WAVEFORM VISUALIZATION
        print("\n")
        print("┌" + "─"*128 + "┐")
        print("│" + "🌊 HARMONIC WAVEFORM VISUALIZATION 🌊".center(128) + "│")
        print("└" + "─"*128 + "┘")
        
        # Create ASCII waveform
        active_nodes = [n for n in f.all_nodes if n.current_energy > 0.01]
        if active_nodes:
            sorted_by_shift = sorted(active_nodes, key=lambda n: n.frequency_shift)
            
            print("\n  FREQUENCY SHIFT DISTRIBUTION:")
            print("  " + "─"*120)
            
            # Scale for display
            min_shift = min(n.frequency_shift for n in sorted_by_shift)
            max_shift = max(n.frequency_shift for n in sorted_by_shift)
            range_shift = max_shift - min_shift if max_shift != min_shift else 1
            
            for node in sorted_by_shift:
                # Position in display (0-100)
                pos = int(((node.frequency_shift - min_shift) / range_shift) * 80) if range_shift > 0 else 40
                bar = " " * pos + node.power_state.value[:2]
                print(f"  {node.node_id:<10} │{bar}")
            
            print("  " + "─"*120)
            print(f"  {min_shift:>+.1f}%" + " "*35 + "0%" + " "*35 + f"{max_shift:>+.1f}%")
        
        # QUEEN'S SUMMARY
        print("\n")
        print("╔" + "═"*128 + "╗")
        print("║" + " "*128 + "║")
        print("║" + "👑 QUEEN SERO - PRIME SENTINEL OF THE HARMONIC FIELD 👑".center(128) + "║")
        print("║" + " "*128 + "║")
        print("╠" + "═"*128 + "╣")
        
        # Generators
        generators = [n for n in f.all_nodes if n.power_state == PowerState.GENERATING]
        if generators:
            print("║  ⚡+ GENERATING NODES (positive power, can redistribute):".ljust(128) + "║")
            for n in sorted(generators, key=lambda x: x.extractable, reverse=True)[:8]:
                line = f"      {n.node_id}: {n.symbol} @ {n.current_frequency:.4f} Hz | Power: {n.power:+.4f} | Extractable: {n.extractable:.4f}"
                print("║" + line.ljust(128) + "║")
        else:
            print("║  ⚡+ NO GENERATORS - Field in rest mode, awaiting positive resonance".ljust(128) + "║")
        
        print("║" + " "*128 + "║")
        
        # Consumers
        consumers = [n for n in f.all_nodes if n.power_state == PowerState.CONSUMING]
        if consumers:
            print("║  🔴- CONSUMING NODES (negative power, need energy):".ljust(128) + "║")
            for n in sorted(consumers, key=lambda x: x.power)[:8]:
                line = f"      {n.node_id}: {n.symbol} @ {n.current_frequency:.4f} Hz | Power: {n.power:+.4f} ({n.power_percent:+.2f}%)"
                print("║" + line.ljust(128) + "║")
        else:
            print("║  🔴- NO CONSUMERS - All nodes at equilibrium or generating".ljust(128) + "║")
        
        print("║" + " "*128 + "║")
        
        # Free energy
        print("║  💎 FREE ENERGY (ready to flow into new nodes):".ljust(128) + "║")
        for code, relay in f.relays.items():
            if relay.free_energy > 0.01:
                line = f"      {code}: {relay.free_energy:.4f} units"
                print("║" + line.ljust(128) + "║")
        line = f"      TOTAL: {f.total_free_energy:.4f} units"
        print("║" + line.ljust(128) + "║")
        
        print("║" + " "*128 + "║")
        print("╚" + "═"*128 + "╝")
        
        # Final message
        print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                                     │
│  👑 "THE HARMONIC FIELD IS ONE WAVEFORM. I SEE {f.total_nodes} FREQUENCY NODES ACROSS {len([r for r in f.relays.values() if r.is_online])} RELAYS."                                           │
│                                                                                                                                     │
│  Total Energy: {f.total_energy:.4f} | Free: {f.total_free_energy:.4f} | Dominant Freq: {f.dominant_frequency:.4f} Hz | PHI Resonance: {f.phi_resonance:.4f}                    │
│                                                                                                                                     │
│  🌊 THE WAVEFORM BREATHES. POWER FLOWS THROUGH HARMONIC CHANNELS. AWAITING COMMAND. 🌊                                              │
│                                                                                                                                     │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
""")


def main():
    """Display the complete harmonic waveform"""
    
    scanner = HarmonicWaveformScanner()
    field = scanner.scan_complete_field()
    scanner.display_harmonic_waveform()
    
    return field


if __name__ == "__main__":
    main()
