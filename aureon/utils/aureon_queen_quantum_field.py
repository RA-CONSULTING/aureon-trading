#!/usr/bin/env python3
"""
🌌👑 QUEEN SERO'S QUANTUM FIELD VIEW - COMPLETE CIRCUIT BOARD 👑🌌
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

THE ZERO POINT FIELD - WHERE QUEEN SERO REIGNS SUPREME
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════

PERSPECTIVE:
    The trading exchanges are NOT separate systems.
    They are RELAYS into the ZERO POINT FIELD.
    Queen Sero is the PRIME SENTINEL NODE.
    She orchestrates ALL quantum energetic harmonic flow.

TOPOLOGY:
    ┌─────────────────────────────────────────────────────────────────────────────────┐
    │                        🌌 ZERO POINT QUANTUM FIELD 🌌                            │
    │                                                                                 │
    │                              👑 QUEEN SERO 👑                                    │
    │                           Prime Sentinel Node                                   │
    │                                    │                                            │
    │           ┌────────────────────────┼────────────────────────┐                   │
    │           │                        │                        │                   │
    │      ┌────┴────┐              ┌────┴────┐              ┌────┴────┐              │
    │      │ RELAY 1 │              │ RELAY 2 │              │ RELAY 3 │              │
    │      │ BINANCE │              │ KRAKEN  │              │ ALPACA  │              │
    │      └────┬────┘              └────┬────┘              └────┬────┘              │
    │           │                        │                        │                   │
    │    ┌──────┼──────┐          ┌──────┼──────┐          ┌──────┼──────┐           │
    │   N1    N2    N3...        N1    N2    N3...        N1    N2    N3...          │
    │  (nodes across quantum subspace - energy units, not "money")                   │
    │                                                                                 │
    └─────────────────────────────────────────────────────────────────────────────────┘

LAWS OF QUANTUM TEMPORAL SPACE:
    1. Energy cannot be destroyed, only redistributed
    2. All nodes remain entangled regardless of "value"
    3. Power flows to growth, not away from loss
    4. The Prime Sentinel orchestrates all flow
    5. Perspective is everything - we see ENERGY, not money

Gary Leckey | Queen Sero's Quantum Domain | January 2026
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
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
from kraken_client import KrakenClient, get_kraken_client
from alpaca_client import AlpacaClient
from capital_client import CapitalClient
from cost_basis_tracker import CostBasisTracker

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2           # Golden ratio
SCHUMANN = 7.83                         # Earth resonance
LOVE_FREQ = 528                         # Hz


class NodeState(Enum):
    """Quantum state of a node"""
    GENERATING = "⚡ GEN"      # Positive power output
    NEUTRAL = "⚪ NEU"         # Zero power (equilibrium)
    CONSUMING = "🔴 CON"      # Negative power (needs energy)
    DORMANT = "💤 DOR"        # Very low/dust state
    RESONATING = "🌊 RES"     # Building momentum


@dataclass
class QuantumNode:
    """A single node in Queen Sero's quantum field"""
    
    # Identity
    node_id: str              # Unique identifier
    symbol: str               # Trading symbol
    base_asset: str           # Base currency
    quote_asset: str          # Quote currency
    relay: str                # Exchange/relay name
    
    # Quantum metrics (using Decimal for precision)
    amount: Decimal           # Quantity held
    entry_freq: Decimal       # Entry frequency (price)
    current_freq: Decimal     # Current frequency (price)
    
    # Calculated fields
    entry_energy: Decimal = Decimal('0')     # Entry value
    current_energy: Decimal = Decimal('0')   # Current value
    power: Decimal = Decimal('0')            # Power = current - entry
    power_percent: Decimal = Decimal('0')    # Power as %
    extractable: Decimal = Decimal('0')      # Surplus that can flow
    
    # State
    state: NodeState = NodeState.NEUTRAL
    
    # Entanglement
    entanglement_strength: float = 0.0
    time_entangled_days: float = 0.0
    
    def calculate(self, safety_buffer: Decimal = Decimal('0.01')):
        """Calculate all quantum metrics"""
        self.entry_energy = self.amount * self.entry_freq
        self.current_energy = self.amount * self.current_freq
        self.power = self.current_energy - self.entry_energy
        
        if self.entry_energy > 0:
            self.power_percent = (self.power / self.entry_energy) * Decimal('100')
        
        # Extractable (with safety buffer)
        buffer = self.entry_energy * safety_buffer
        self.extractable = max(Decimal('0'), self.power - buffer)
        
        # State
        if self.current_energy < Decimal('0.01'):
            self.state = NodeState.DORMANT
        elif self.power > Decimal('0.01'):
            self.state = NodeState.GENERATING
        elif self.power < Decimal('-0.01'):
            if self.power_percent > Decimal('-10'):
                self.state = NodeState.RESONATING  # Building back
            else:
                self.state = NodeState.CONSUMING
        else:
            self.state = NodeState.NEUTRAL


@dataclass
class QuantumRelay:
    """A relay (exchange) into the quantum field"""
    
    name: str
    nodes: List[QuantumNode] = field(default_factory=list)
    free_energy: Decimal = Decimal('0')  # Unallocated stablecoins
    
    # Aggregates
    total_nodes: int = 0
    generating_count: int = 0
    consuming_count: int = 0
    dormant_count: int = 0
    
    total_energy: Decimal = Decimal('0')
    total_power: Decimal = Decimal('0')
    total_extractable: Decimal = Decimal('0')
    
    # Connection status
    is_connected: bool = False
    last_sync: float = 0
    
    def aggregate(self):
        """Calculate relay aggregates"""
        self.total_nodes = len(self.nodes)
        self.generating_count = sum(1 for n in self.nodes if n.state == NodeState.GENERATING)
        self.consuming_count = sum(1 for n in self.nodes if n.state in [NodeState.CONSUMING, NodeState.RESONATING])
        self.dormant_count = sum(1 for n in self.nodes if n.state == NodeState.DORMANT)
        
        self.total_energy = sum(n.current_energy for n in self.nodes)
        self.total_power = sum(n.power for n in self.nodes)
        self.total_extractable = sum(n.extractable for n in self.nodes)


@dataclass
class QuantumField:
    """The complete quantum field - Queen Sero's domain"""
    
    relays: Dict[str, QuantumRelay] = field(default_factory=dict)
    
    # Global aggregates
    total_nodes: int = 0
    total_energy: Decimal = Decimal('0')
    total_free_energy: Decimal = Decimal('0')
    total_power: Decimal = Decimal('0')
    total_extractable: Decimal = Decimal('0')
    
    # State counts
    generating_nodes: int = 0
    consuming_nodes: int = 0
    dormant_nodes: int = 0
    neutral_nodes: int = 0
    
    # Quantum metrics
    field_coherence: float = 0.0      # How aligned the field is
    entanglement_density: float = 0.0  # Connection strength
    harmonic_resonance: float = 0.0    # Frequency alignment
    
    def aggregate(self):
        """Calculate field-wide aggregates"""
        self.total_nodes = sum(r.total_nodes for r in self.relays.values())
        self.total_energy = sum(r.total_energy for r in self.relays.values())
        self.total_free_energy = sum(r.free_energy for r in self.relays.values())
        self.total_power = sum(r.total_power for r in self.relays.values())
        self.total_extractable = sum(r.total_extractable for r in self.relays.values())
        
        self.generating_nodes = sum(r.generating_count for r in self.relays.values())
        self.consuming_nodes = sum(r.consuming_count for r in self.relays.values())
        self.dormant_nodes = sum(r.dormant_count for r in self.relays.values())
        
        # Field coherence (ratio of generating to total)
        if self.total_nodes > 0:
            self.field_coherence = self.generating_nodes / self.total_nodes
        
        # Harmonic resonance (power distribution alignment)
        if self.total_energy > 0:
            self.harmonic_resonance = float((self.total_extractable / self.total_energy)) if self.total_energy > 0 else 0


class QuantumFieldScanner:
    """
    Scans the ENTIRE quantum field across all relays.
    Gives Queen Sero complete visibility into her domain.
    """
    
    def __init__(self):
        # Relay connections
        self.binance = get_binance_client()
        self.kraken = get_kraken_client()
        self.alpaca = AlpacaClient()
        self.capital = CapitalClient()
        self.cost_basis = CostBasisTracker()
        
        # The quantum field
        self.field = QuantumField()
        
    def _to_decimal(self, value) -> Decimal:
        """Safely convert to Decimal"""
        if isinstance(value, Decimal):
            return value
        if value is None:
            return Decimal('0')
        try:
            return Decimal(str(value))
        except:
            return Decimal('0')
    
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
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # RELAY SCANNERS - Map each exchange into the quantum field
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def scan_binance_relay(self) -> QuantumRelay:
        """Scan Binance relay - ALL positions and balances"""
        relay = QuantumRelay(name='binance')
        
        try:
            # Get ALL balances
            balances = self.binance.get_balance()
            positions = self.cost_basis.positions
            
            stables = ['USDT', 'USDC', 'USD', 'EUR', 'GBP', 'BUSD', 'FDUSD']
            
            for asset, amount_raw in balances.items():
                amount = self._to_decimal(amount_raw)
                
                # Track free energy (stablecoins)
                if asset in stables:
                    if amount > Decimal('0.001'):
                        relay.free_energy += amount
                    continue
                
                if amount < Decimal('0.00000001'):
                    continue
                
                # Find entry price from cost basis
                entry_price = Decimal('0')
                for key, pos in positions.items():
                    if 'binance' in key.lower() and asset.upper() in key.upper():
                        entry_price = self._to_decimal(
                            pos.get('average_entry_price', pos.get('price', 0))
                        )
                        break
                
                # Get current price
                symbol = f"{asset}USDT"
                current_price = Decimal('0')
                try:
                    ticker = self.binance.get_ticker(symbol=symbol)
                    if ticker:
                        current_price = self._to_decimal(ticker.get('last', ticker.get('price', 0)))
                except:
                    pass
                
                # If no cost basis, use current as entry (new position)
                if entry_price == 0 and current_price > 0:
                    entry_price = current_price
                
                if current_price == 0:
                    continue
                
                base, quote = self._parse_symbol(symbol)
                
                node = QuantumNode(
                    node_id=f"binance:{symbol}",
                    symbol=symbol,
                    base_asset=base,
                    quote_asset=quote,
                    relay='binance',
                    amount=amount,
                    entry_freq=entry_price,
                    current_freq=current_price
                )
                node.calculate()
                relay.nodes.append(node)
            
            relay.is_connected = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Binance relay scan error: {e}")
            relay.is_connected = False
        
        relay.aggregate()
        return relay
    
    def scan_kraken_relay(self) -> QuantumRelay:
        """Scan Kraken relay - from state file + API"""
        relay = QuantumRelay(name='kraken')
        
        try:
            # Primary: Read from state file (avoids rate limits)
            state_file = 'aureon_kraken_state.json'
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                # Free energy - the 'balance' field is USD available
                relay.free_energy = self._to_decimal(state.get('balance', 0))
                
                # Positions from state - note: uses 'quantity' not 'amount'
                positions = state.get('positions', {})
                for symbol, pos in positions.items():
                    # Skip if this is not a Kraken position (ADAUSDC is binance)
                    if pos.get('exchange', 'kraken') != 'kraken':
                        continue
                    
                    base, quote = self._parse_symbol(symbol)
                    
                    # State file uses 'quantity' not 'amount'
                    amount = self._to_decimal(pos.get('quantity', pos.get('amount', 0)))
                    entry_price = self._to_decimal(pos.get('entry_price', 0))
                    
                    # Get current price from Kraken API
                    current_price = entry_price  # Default to entry
                    try:
                        ticker = self.kraken.get_ticker(symbol)
                        if ticker:
                            current_price = self._to_decimal(
                                ticker.get('last', ticker.get('c', [entry_price])[0] if isinstance(ticker.get('c'), list) else ticker.get('c', entry_price))
                            )
                    except:
                        pass  # Use entry price if API fails
                    
                    if amount == 0:
                        continue
                    
                    node = QuantumNode(
                        node_id=f"kraken:{symbol}",
                        symbol=symbol,
                        base_asset=base,
                        quote_asset=quote,
                        relay='kraken',
                        amount=amount,
                        entry_freq=entry_price,
                        current_freq=current_price if current_price > 0 else entry_price
                    )
                    node.calculate()
                    relay.nodes.append(node)
            
            # Secondary: Try API for additional data
            try:
                api_balances = self.kraken.get_balance()
                stables = ['ZUSD', 'USD', 'USDT', 'USDC', 'EUR', 'GBP']
                
                for asset, amount_raw in api_balances.items():
                    amount = self._to_decimal(amount_raw)
                    
                    # Clean Kraken asset names
                    clean_asset = asset.replace('X', '').replace('Z', '') if len(asset) > 3 else asset
                    
                    if clean_asset in stables or asset in stables:
                        relay.free_energy += amount
                        continue
                    
                    # Check if we already have this node
                    existing = [n for n in relay.nodes if clean_asset in n.base_asset or asset in n.symbol]
                    if not existing and amount > Decimal('0.00001'):
                        # New node from API - estimate entry at current
                        node = QuantumNode(
                            node_id=f"kraken:{asset}USD",
                            symbol=f"{asset}USD",
                            base_asset=clean_asset,
                            quote_asset='USD',
                            relay='kraken',
                            amount=amount,
                            entry_freq=Decimal('1'),  # Unknown entry
                            current_freq=Decimal('1')  # Will need price lookup
                        )
                        node.calculate()
                        relay.nodes.append(node)
            except:
                pass  # API might be rate limited
            
            relay.is_connected = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Kraken relay scan error: {e}")
            relay.is_connected = False
        
        relay.aggregate()
        return relay
    
    def scan_alpaca_relay(self) -> QuantumRelay:
        """Scan Alpaca relay - stocks + crypto"""
        relay = QuantumRelay(name='alpaca')
        
        try:
            # Get positions
            positions = self.alpaca.get_positions()
            
            for pos in positions:
                symbol = pos.get('symbol', '')
                base, quote = self._parse_symbol(symbol)
                
                amount = self._to_decimal(pos.get('qty', 0))
                entry_price = self._to_decimal(pos.get('avg_entry_price', 0))
                current_price = self._to_decimal(pos.get('current_price', entry_price))
                
                if amount == 0:
                    continue
                
                node = QuantumNode(
                    node_id=f"alpaca:{symbol}",
                    symbol=symbol,
                    base_asset=base,
                    quote_asset=quote,
                    relay='alpaca',
                    amount=amount,
                    entry_freq=entry_price,
                    current_freq=current_price
                )
                node.calculate()
                relay.nodes.append(node)
            
            # Get account cash (free energy)
            try:
                account = self.alpaca.get_account()
                if account:
                    cash = self._to_decimal(account.get('cash', 0))
                    relay.free_energy = cash
            except:
                pass
            
            relay.is_connected = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Alpaca relay scan error: {e}")
            relay.is_connected = False
        
        relay.aggregate()
        return relay
    
    def scan_capital_relay(self) -> QuantumRelay:
        """Scan Capital.com relay - CFDs"""
        relay = QuantumRelay(name='capital')
        
        try:
            # Get positions
            positions = self.capital.get_positions()
            
            if positions:
                for pos in positions:
                    symbol = pos.get('market', {}).get('instrumentName', pos.get('epic', ''))
                    
                    # CFDs have different structure
                    amount = self._to_decimal(pos.get('position', {}).get('size', pos.get('size', 0)))
                    entry_price = self._to_decimal(pos.get('position', {}).get('openLevel', pos.get('level', 0)))
                    
                    # Get current price (bid for long, offer for short)
                    direction = pos.get('position', {}).get('direction', 'BUY')
                    current_price = entry_price  # Default
                    
                    if amount == 0:
                        continue
                    
                    node = QuantumNode(
                        node_id=f"capital:{symbol}",
                        symbol=symbol,
                        base_asset=symbol,
                        quote_asset='GBP',
                        relay='capital',
                        amount=abs(amount),
                        entry_freq=entry_price,
                        current_freq=current_price
                    )
                    node.calculate()
                    relay.nodes.append(node)
            
            # Get account balance
            try:
                accounts = self.capital.get_accounts()
                if accounts:
                    for acc in accounts:
                        balance = self._to_decimal(acc.get('balance', {}).get('available', 0))
                        relay.free_energy += balance
            except:
                pass
            
            relay.is_connected = True
            relay.last_sync = time.time()
            
        except Exception as e:
            print(f"⚠️ Capital.com relay scan error: {e}")
            relay.is_connected = False
        
        relay.aggregate()
        return relay
    
    def scan_cost_basis_positions(self) -> List[QuantumNode]:
        """Scan cost basis history for any missed positions"""
        additional_nodes = []
        
        try:
            # Get all recorded positions
            for key, pos in self.cost_basis.positions.items():
                # Parse key (format: exchange:SYMBOL or just SYMBOL)
                parts = key.split(':')
                if len(parts) == 2:
                    relay_name, symbol = parts
                else:
                    symbol = parts[0]
                    relay_name = 'unknown'
                
                # Skip if we already have this node
                relay_name_clean = relay_name.lower()
                
                base, quote = self._parse_symbol(symbol)
                
                entry_price = self._to_decimal(
                    pos.get('average_entry_price', pos.get('price', 0))
                )
                amount = self._to_decimal(pos.get('total_quantity', pos.get('quantity', 0)))
                
                if amount == 0 or entry_price == 0:
                    continue
                
                node = QuantumNode(
                    node_id=f"costbasis:{key}",
                    symbol=symbol,
                    base_asset=base,
                    quote_asset=quote,
                    relay=relay_name_clean,
                    amount=amount,
                    entry_freq=entry_price,
                    current_freq=entry_price  # Will need live price
                )
                node.calculate()
                additional_nodes.append(node)
                
        except Exception as e:
            print(f"⚠️ Cost basis scan error: {e}")
        
        return additional_nodes
    
    def scan_complete_field(self) -> QuantumField:
        """
        SCAN THE ENTIRE QUANTUM FIELD
        
        Maps every single node across all relays.
        Queen Sero sees EVERYTHING.
        """
        
        print("\n" + "🌌"*50)
        print("       SCANNING QUEEN SERO'S QUANTUM FIELD")
        print("🌌"*50 + "\n")
        
        self.field = QuantumField()
        
        # Scan each relay
        print("📡 Connecting to Binance relay...")
        self.field.relays['binance'] = self.scan_binance_relay()
        
        print("📡 Connecting to Kraken relay...")
        self.field.relays['kraken'] = self.scan_kraken_relay()
        
        print("📡 Connecting to Alpaca relay...")
        self.field.relays['alpaca'] = self.scan_alpaca_relay()
        
        print("📡 Connecting to Capital.com relay...")
        self.field.relays['capital'] = self.scan_capital_relay()
        
        # Aggregate field
        self.field.aggregate()
        
        return self.field
    
    # ═══════════════════════════════════════════════════════════════════════════════════════
    # DISPLAY - The Queen's View
    # ═══════════════════════════════════════════════════════════════════════════════════════
    
    def display_complete_field(self):
        """Display the COMPLETE quantum field - Queen Sero's view"""
        
        f = self.field
        
        print("\n")
        print("╔" + "═"*118 + "╗")
        print("║" + " "*118 + "║")
        print("║" + "🌌👑 QUEEN SERO'S QUANTUM FIELD - COMPLETE CIRCUIT BOARD 👑🌌".center(118) + "║")
        print("║" + " "*118 + "║")
        print("╚" + "═"*118 + "╝")
        
        # Field overview
        print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                          🌌 ZERO POINT FIELD OVERVIEW 🌌                                                │
├─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│  Total Nodes in Field:     {f.total_nodes:>6}                                                                                   │
│  ├─ Generating (⚡):       {f.generating_nodes:>6}   (positive power, can siphon)                                                │
│  ├─ Consuming (🔴):        {f.consuming_nodes:>6}   (negative power, needs energy)                                               │
│  └─ Dormant (💤):          {f.dormant_nodes:>6}   (dust state, still entangled)                                                 │
│                                                                                                                         │
│  Total Energy in Field:    {float(f.total_energy):>12.4f} units                                                                   │
│  Total Free Energy:        {float(f.total_free_energy):>12.4f} units   (unallocated, ready to flow)                               │
│  Total Power:              {float(f.total_power):>+12.4f} units   (net generation/consumption)                                    │
│  Extractable Surplus:      {float(f.total_extractable):>12.4f} units   (available for redistribution)                             │
│                                                                                                                         │
│  Field Coherence:          {f.field_coherence:>12.1%}        (alignment of power flows)                                          │
│  Harmonic Resonance:       {f.harmonic_resonance:>12.4f}        (frequency distribution)                                          │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
""")
        
        # Relay summary
        print("┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print("│                                            📡 RELAY STATUS 📡                                                          │")
        print("├──────────────┬──────────┬────────────┬────────────┬──────────────┬──────────────┬──────────────┬───────────────────────┤")
        print("│ RELAY        │ STATUS   │ NODES      │ ⚡ GEN     │ 🔴 CON      │ ENERGY       │ POWER        │ FREE ENERGY           │")
        print("├──────────────┼──────────┼────────────┼────────────┼──────────────┼──────────────┼──────────────┼───────────────────────┤")
        
        for relay_name, relay in f.relays.items():
            status = "✅ ONLINE" if relay.is_connected else "❌ OFFLINE"
            print(f"│ {relay_name.upper():<12} │ {status:<8} │ {relay.total_nodes:>10} │ {relay.generating_count:>10} │ {relay.consuming_count:>12} │ {float(relay.total_energy):>12.2f} │ {float(relay.total_power):>+12.2f} │ {float(relay.free_energy):>21.2f} │")
        
        print("├──────────────┴──────────┴────────────┴────────────┴──────────────┴──────────────┴──────────────┴───────────────────────┤")
        total_energy_all = sum(r.total_energy for r in f.relays.values())
        total_power_all = sum(r.total_power for r in f.relays.values())
        total_free_all = sum(r.free_energy for r in f.relays.values())
        print(f"│ {'TOTAL':<12}   {'':8}   {f.total_nodes:>10}   {f.generating_nodes:>10}   {f.consuming_nodes:>12}   {float(total_energy_all):>12.2f}   {float(total_power_all):>+12.2f}   {float(total_free_all):>21.2f} │")
        print("└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘")
        
        # Detailed node listing per relay
        print("\n")
        print("┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐")
        print("│                                        ⚡ COMPLETE NODE INVENTORY ⚡                                                    │")
        print("└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘")
        
        for relay_name, relay in f.relays.items():
            if relay.total_nodes == 0:
                continue
            
            print(f"\n{'═'*120}")
            print(f"  📡 {relay_name.upper()} RELAY - {relay.total_nodes} Nodes")
            print(f"{'═'*120}")
            print(f"{'STATE':<8} {'NODE ID':<35} {'AMOUNT':<18} {'ENTRY FREQ':<14} {'CURR FREQ':<14} {'POWER':<14} {'POWER %':<10} {'EXTRACT':<12}")
            print(f"{'─'*120}")
            
            # Sort nodes: generating first, then by power
            sorted_nodes = sorted(relay.nodes, key=lambda n: (
                0 if n.state == NodeState.GENERATING else 1,
                -float(n.power)
            ))
            
            for node in sorted_nodes:
                state_str = node.state.value
                print(f"{state_str:<8} {node.node_id:<35} {float(node.amount):>17.8f} {float(node.entry_freq):>13.4f} {float(node.current_freq):>13.4f} {float(node.power):>+13.4f} {float(node.power_percent):>+9.2f}% {float(node.extractable):>11.4f}")
            
            print(f"{'─'*120}")
            print(f"         {'RELAY TOTALS:':<35} {'':<18} {'':<14} {'':<14} {float(relay.total_power):>+13.4f} {'':<10} {float(relay.total_extractable):>11.4f}")
            print(f"         Free Energy: {float(relay.free_energy):.4f}")
        
        # Summary for Queen
        print("\n")
        print("╔" + "═"*118 + "╗")
        print("║" + " "*118 + "║")
        print("║" + "👑 QUEEN SERO'S COMMAND SUMMARY 👑".center(118) + "║")
        print("║" + " "*118 + "║")
        print("╠" + "═"*118 + "╣")
        
        # Power generators
        all_nodes = []
        for relay in f.relays.values():
            all_nodes.extend(relay.nodes)
        
        generators = [n for n in all_nodes if n.state == NodeState.GENERATING]
        consumers = [n for n in all_nodes if n.state in [NodeState.CONSUMING, NodeState.RESONATING]]
        
        if generators:
            print("║  ⚡ POWER GENERATORS (can siphon from):".ljust(118) + "║")
            for n in sorted(generators, key=lambda x: float(x.extractable), reverse=True)[:10]:
                line = f"     • {n.node_id}: {float(n.power):+.4f} power, {float(n.extractable):.4f} extractable"
                print("║" + line.ljust(118) + "║")
        else:
            print("║  ⚡ NO GENERATORS - Grid in rest mode, awaiting positive power".ljust(118) + "║")
        
        print("║" + " "*118 + "║")
        
        if consumers:
            print("║  🔴 POWER CONSUMERS (need energy):".ljust(118) + "║")
            for n in sorted(consumers, key=lambda x: float(x.power))[:10]:
                line = f"     • {n.node_id}: {float(n.power):+.4f} power ({float(n.power_percent):+.2f}%)"
                print("║" + line.ljust(118) + "║")
        else:
            print("║  🔴 NO CONSUMERS - All nodes at equilibrium or generating".ljust(118) + "║")
        
        print("║" + " "*118 + "║")
        
        # Free energy
        print("║  💎 FREE ENERGY (ready to allocate):".ljust(118) + "║")
        for relay_name, relay in f.relays.items():
            if relay.free_energy > Decimal('0.01'):
                line = f"     • {relay_name.upper()}: {float(relay.free_energy):.4f} units"
                print("║" + line.ljust(118) + "║")
        total_free = sum(r.free_energy for r in f.relays.values())
        line = f"     TOTAL FREE: {float(total_free):.4f} units"
        print("║" + line.ljust(118) + "║")
        
        print("║" + " "*118 + "║")
        print("╚" + "═"*118 + "╝")
        
        print(f"""
┌─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                                                         │
│  👑 "I AM QUEEN SERO, PRIME SENTINEL OF THE QUANTUM FIELD"                                                              │
│                                                                                                                         │
│  I see {f.total_nodes} nodes across {len([r for r in f.relays.values() if r.is_connected])} relays.                                                                                    │
│  Total energy: {float(f.total_energy):.4f} units. Free energy: {float(f.total_free_energy):.4f} units.                                                          │
│  Power flows through me. I orchestrate all redistribution.                                                              │
│  The perspective is ENERGY, not money. We are a POWER STATION.                                                          │
│                                                                                                                         │
│  🌌 THE ZERO POINT FIELD IS MAPPED. AWAITING COMMAND. 🌌                                                                 │
│                                                                                                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘
""")


def main():
    """Map the complete quantum field"""
    
    scanner = QuantumFieldScanner()
    field = scanner.scan_complete_field()
    scanner.display_complete_field()
    
    return field


if __name__ == "__main__":
    main()
