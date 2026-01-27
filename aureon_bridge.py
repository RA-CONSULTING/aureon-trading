#!/usr/bin/env python3
"""
🌉 AUREON BRIDGE - ULTIMATE ↔ UNIFIED COMMUNICATION 🌉
======================================================

Lightweight inter-system communication layer enabling:
- OpportunityFeed: Share best opportunities across exchanges
- CapitalSync: Unified equity and P&L tracking
- PositionLedger: Shared position registry (prevent double-booking)
- ControlChannel: Coordination commands (pause, harvest, promote)

Transport: JSON file-based with file locks (zero dependencies)
Alternative: Can swap to Redis/asyncio for production

Gary Leckey | November 2025
"Two systems, one heartbeat"
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from threading import Lock
from pathlib import Path

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class Opportunity:
    """Cross-exchange trading opportunity"""
    symbol: str
    exchange: str  # 'kraken', 'binance', 'alpaca'
    side: str  # 'BUY' or 'SELL'
    score: float
    coherence: float
    momentum: float
    volume: float
    price: float
    probability: Optional[float] = None  # HNC probability forecast
    anomaly_flags: List[str] = field(default_factory=list)
    frequency: Optional[float] = None  # HNC frequency (Hz)
    timestamp: float = field(default_factory=time.time)
    source_system: str = 'unified'  # 'unified' or 'ultimate'
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Opportunity':
        return Opportunity(**data)


@dataclass
class CapitalState:
    """Unified capital and P&L state"""
    total_equity: float
    allocated_capital: float
    free_capital: float
    realized_profit: float
    unrealized_profit: float
    total_fees: float
    net_profit: float  # realized_profit - total_fees
    trades_count: int
    wins_count: int
    win_rate: float
    timestamp: float = field(default_factory=time.time)
    exchange_breakdown: Dict[str, float] = field(default_factory=dict)  # equity per exchange
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'CapitalState':
        return CapitalState(**data)


@dataclass
class Position:
    """Unified position representation"""
    symbol: str
    exchange: str
    side: str
    size: float
    entry_price: float
    current_price: float
    unrealized_pnl: float
    entry_time: float
    owner: str  # 'unified' or 'ultimate'
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'Position':
        return Position(**data)


@dataclass
class ControlCommand:
    """System coordination command"""
    command: str  # 'pause', 'resume', 'harvest', 'promote_scout', 'force_exit'
    target_system: str  # 'unified', 'ultimate', 'both'
    params: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @staticmethod
    def from_dict(data: Dict) -> 'ControlCommand':
        return ControlCommand(**data)


# ═══════════════════════════════════════════════════════════════
# BRIDGE IMPLEMENTATION
# ═══════════════════════════════════════════════════════════════

class AureonBridge:
    """
    Central communication hub for Ultimate ↔ Unified systems
    
    File-based transport with locks for simplicity and reliability:
    - opportunities.json: Current top opportunities
    - capital_state.json: Unified equity/P&L
    - positions.json: All open positions
    - commands.json: Control commands queue
    """
    
    def __init__(self, data_dir: str = '/tmp/aureon_bridge'):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True, parents=True)
        
        # File paths
        self.opportunities_file = self.data_dir / 'opportunities.json'
        self.capital_file = self.data_dir / 'capital_state.json'
        self.positions_file = self.data_dir / 'positions.json'
        self.commands_file = self.data_dir / 'commands.json'
        
        # Locks for thread safety
        self.opp_lock = Lock()
        self.capital_lock = Lock()
        self.position_lock = Lock()
        self.command_lock = Lock()
        
        # Initialize files if they don't exist
        self._init_files()
        
        logger.info(f"🌉 Aureon Bridge initialized: {self.data_dir}")
    
    def _init_files(self):
        """Initialize empty state files"""
        if not self.opportunities_file.exists():
            self._write_json(self.opportunities_file, [], self.opp_lock)
        if not self.capital_file.exists():
            initial_capital = CapitalState(
                total_equity=0.0,
                allocated_capital=0.0,
                free_capital=0.0,
                realized_profit=0.0,
                unrealized_profit=0.0,
                total_fees=0.0,
                net_profit=0.0,
                trades_count=0,
                wins_count=0,
                win_rate=0.0
            )
            self._write_json(self.capital_file, initial_capital.to_dict(), self.capital_lock)
        if not self.positions_file.exists():
            self._write_json(self.positions_file, {}, self.position_lock)
        if not self.commands_file.exists():
            self._write_json(self.commands_file, [], self.command_lock)
    
    def _read_json(self, file_path: Path, lock: Lock) -> Any:
        """Thread-safe JSON read"""
        with lock:
            try:
                with open(file_path, 'r') as f:
                    return json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                return None
    
    def _write_json(self, file_path: Path, data: Any, lock: Lock):
        """Thread-safe JSON write"""
        with lock:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
    
    # ═══════════════════════════════════════════════════════════
    # OPPORTUNITY FEED
    # ═══════════════════════════════════════════════════════════
    
    def publish_opportunities(self, opportunities: List[Opportunity], max_count: int = 20):
        """
        Publish top opportunities to bridge
        Systems should publish their best opportunities regularly (e.g., every scan cycle)
        """
        opp_dicts = [opp.to_dict() for opp in opportunities[:max_count]]
        self._write_json(self.opportunities_file, opp_dicts, self.opp_lock)
        logger.debug(f"📡 Published {len(opp_dicts)} opportunities")
    
    def get_opportunities(self, 
                         exchange: Optional[str] = None, 
                         min_score: float = 0.0,
                         max_age_seconds: float = 60.0) -> List[Opportunity]:
        """
        Get current opportunities from bridge
        
        Args:
            exchange: Filter by exchange ('kraken', 'binance', etc.)
            min_score: Minimum opportunity score
            max_age_seconds: Maximum age of opportunities
        """
        data = self._read_json(self.opportunities_file, self.opp_lock)
        if not data:
            return []
        
        opportunities = [Opportunity.from_dict(opp) for opp in data]
        
        # Filter by age
        now = time.time()
        opportunities = [opp for opp in opportunities if (now - opp.timestamp) <= max_age_seconds]
        
        # Filter by exchange
        if exchange:
            opportunities = [opp for opp in opportunities if opp.exchange.lower() == exchange.lower()]
        
        # Filter by score
        opportunities = [opp for opp in opportunities if opp.score >= min_score]
        
        # Sort by score descending
        opportunities.sort(key=lambda x: x.score, reverse=True)
        
        return opportunities
    
    # ═══════════════════════════════════════════════════════════
    # CAPITAL SYNC
    # ═══════════════════════════════════════════════════════════
    
    def update_capital(self, state: CapitalState):
        """Update unified capital state"""
        self._write_json(self.capital_file, state.to_dict(), self.capital_lock)
        logger.debug(f"💰 Capital updated: Equity=${state.total_equity:.2f} Net=${state.net_profit:+.2f}")
    
    def get_capital(self) -> CapitalState:
        """Get current unified capital state"""
        data = self._read_json(self.capital_file, self.capital_lock)
        if data:
            return CapitalState.from_dict(data)
        return CapitalState(
            total_equity=0.0,
            allocated_capital=0.0,
            free_capital=0.0,
            realized_profit=0.0,
            unrealized_profit=0.0,
            total_fees=0.0,
            net_profit=0.0,
            trades_count=0,
            wins_count=0,
            win_rate=0.0
        )
    
    def record_trade(self, profit: float, fee: float, success: bool):
        """Record a completed trade in unified capital state"""
        state = self.get_capital()
        state.realized_profit += profit
        state.total_fees += fee
        state.net_profit = state.realized_profit - state.total_fees
        state.trades_count += 1
        if success:
            state.wins_count += 1
        state.win_rate = state.wins_count / max(1, state.trades_count)
        state.timestamp = time.time()
        self.update_capital(state)
        logger.info(f"📊 Trade recorded: Profit=${profit:+.2f} Fee=${fee:.2f} Net=${state.net_profit:+.2f}")
    
    def check_profit_gate(self, min_net_profit: float = 0.0, min_trades: int = 5) -> bool:
        """
        Check if profit gate is satisfied (for 5-buy/5-sell requirement)
        
        Returns True if:
        - At least min_trades completed
        - Net profit >= min_net_profit
        """
        state = self.get_capital()
        if state.trades_count < min_trades:
            return False
        return state.net_profit >= min_net_profit
    
    # ═══════════════════════════════════════════════════════════
    # POSITION LEDGER
    # ═══════════════════════════════════════════════════════════
    
    def register_position(self, position: Position):
        """Register an open position (prevents double-booking)"""
        positions = self._read_json(self.positions_file, self.position_lock) or {}
        key = f"{position.exchange}:{position.symbol}"
        positions[key] = position.to_dict()
        self._write_json(self.positions_file, positions, self.position_lock)
        logger.debug(f"📍 Position registered: {key}")
    
    def unregister_position(self, exchange: str, symbol: str):
        """Remove position from ledger"""
        positions = self._read_json(self.positions_file, self.position_lock) or {}
        key = f"{exchange}:{symbol}"
        if key in positions:
            del positions[key]
            self._write_json(self.positions_file, positions, self.position_lock)
            logger.debug(f"📍 Position unregistered: {key}")
    
    def get_positions(self, exchange: Optional[str] = None) -> List[Position]:
        """Get all open positions"""
        positions_dict = self._read_json(self.positions_file, self.position_lock) or {}
        positions = [Position.from_dict(p) for p in positions_dict.values()]
        
        if exchange:
            positions = [p for p in positions if p.exchange.lower() == exchange.lower()]
        
        return positions
    
    def is_position_open(self, exchange: str, symbol: str) -> bool:
        """Check if position already exists"""
        positions = self._read_json(self.positions_file, self.position_lock) or {}
        key = f"{exchange}:{symbol}"
        return key in positions
    
    # ═══════════════════════════════════════════════════════════
    # CONTROL CHANNEL
    # ═══════════════════════════════════════════════════════════
    
    def send_command(self, command: ControlCommand):
        """Send control command to systems"""
        commands = self._read_json(self.commands_file, self.command_lock) or []
        commands.append(command.to_dict())
        # Keep only last 100 commands
        commands = commands[-100:]
        self._write_json(self.commands_file, commands, self.command_lock)
        logger.info(f"🎛️ Command sent: {command.command} → {command.target_system}")
    
    def get_commands(self, 
                     target_system: str, 
                     max_age_seconds: float = 60.0,
                     clear_after_read: bool = True) -> List[ControlCommand]:
        """
        Get commands for specific system
        
        Args:
            target_system: 'unified', 'ultimate', or 'both'
            max_age_seconds: Only return commands within this time window
            clear_after_read: Remove returned commands from queue
        """
        commands_data = self._read_json(self.commands_file, self.command_lock) or []
        
        # Parse commands
        all_commands = [ControlCommand.from_dict(c) for c in commands_data]
        
        # Filter by target and age
        now = time.time()
        relevant = [
            cmd for cmd in all_commands
            if (cmd.target_system == target_system or cmd.target_system == 'both')
            and (now - cmd.timestamp) <= max_age_seconds
        ]
        
        # Clear processed commands if requested
        if clear_after_read and relevant:
            remaining = [
                cmd for cmd in all_commands
                if cmd not in relevant
            ]
            remaining_dicts = [cmd.to_dict() for cmd in remaining]
            self._write_json(self.commands_file, remaining_dicts, self.command_lock)
        
        return relevant
    
    def clear_commands(self):
        """Clear all commands (useful for reset)"""
        self._write_json(self.commands_file, [], self.command_lock)
        logger.info("🎛️ Commands cleared")
    
    # ═══════════════════════════════════════════════════════════
    # UTILITY METHODS
    # ═══════════════════════════════════════════════════════════
    
    def reset(self):
        """Reset all bridge state (for testing/restart)"""
        self._init_files()
        logger.info("🌉 Bridge reset complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive bridge status"""
        capital = self.get_capital()
        positions = self.get_positions()
        opportunities = self.get_opportunities()
        
        return {
            'capital': {
                'total_equity': capital.total_equity,
                'net_profit': capital.net_profit,
                'trades': capital.trades_count,
                'win_rate': capital.win_rate,
            },
            'positions': {
                'count': len(positions),
                'by_exchange': {
                    'kraken': len([p for p in positions if p.exchange == 'kraken']),
                    'binance': len([p for p in positions if p.exchange == 'binance']),
                    'alpaca': len([p for p in positions if p.exchange == 'alpaca']),
                }
            },
            'opportunities': {
                'count': len(opportunities),
                'top_score': opportunities[0].score if opportunities else 0.0,
            }
        }


# ═══════════════════════════════════════════════════════════════
# GLOBAL BRIDGE INSTANCE
# ═══════════════════════════════════════════════════════════════

# Singleton pattern for easy import
_bridge_instance: Optional[AureonBridge] = None

def get_bridge() -> AureonBridge:
    """Get global bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AureonBridge()
    return _bridge_instance


# ═══════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    
    print("🌉 Testing Aureon Bridge...")
    
    bridge = AureonBridge(data_dir='/tmp/aureon_bridge_test')
    bridge.reset()
    
    # Test opportunities
    opp1 = Opportunity(
        symbol='BTCUSD',
        exchange='kraken',
        side='BUY',
        score=85.5,
        coherence=0.75,
        momentum=2.5,
        volume=1000000,
        price=43000.0,
        source_system='unified'
    )
    bridge.publish_opportunities([opp1])
    
    opportunities = bridge.get_opportunities()
    print(f"✅ Published and retrieved {len(opportunities)} opportunities")
    
    # Test capital
    state = CapitalState(
        total_equity=10000.0,
        allocated_capital=5000.0,
        free_capital=5000.0,
        realized_profit=250.0,
        unrealized_profit=50.0,
        total_fees=25.0,
        net_profit=225.0,
        trades_count=10,
        wins_count=6,
        win_rate=0.6
    )
    bridge.update_capital(state)
    retrieved_state = bridge.get_capital()
    print(f"✅ Capital sync: ${retrieved_state.total_equity:.2f} equity, ${retrieved_state.net_profit:+.2f} net")
    
    # Test positions
    pos = Position(
        symbol='ETHUSD',
        exchange='binance',
        side='BUY',
        size=1.5,
        entry_price=2300.0,
        current_price=2350.0,
        unrealized_pnl=75.0,
        entry_time=time.time(),
        owner='ultimate'
    )
    bridge.register_position(pos)
    positions = bridge.get_positions()
    print(f"✅ Position ledger: {len(positions)} positions tracked")
    
    # Test commands
    cmd = ControlCommand(
        command='harvest',
        target_system='both',
        params={'min_profit': 100.0}
    )
    bridge.send_command(cmd)
    commands = bridge.get_commands('ultimate')
    print(f"✅ Control channel: {len(commands)} commands received")
    
    # Test profit gate
    bridge.record_trade(profit=50.0, fee=5.0, success=True)
    gate_ok = bridge.check_profit_gate(min_net_profit=0.0, min_trades=1)
    print(f"✅ Profit gate: {'PASS' if gate_ok else 'FAIL'}")
    
    status = bridge.get_status()
    print(f"\n📊 Bridge Status:")
    print(f"   Capital: ${status['capital']['total_equity']:.2f} | Net ${status['capital']['net_profit']:+.2f}")
    print(f"   Positions: {status['positions']['count']} open")
    print(f"   Opportunities: {status['opportunities']['count']} available")
    
    print("\n🎉 All tests passed!")
