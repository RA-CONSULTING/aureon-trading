#!/usr/bin/env python3
"""
🇮🇪🎯 IRA SNIPER MODE - ZERO LOSS CONFIGURATION 🎯🇮🇪
=====================================================
One bullet. One kill. NO MISSES. EVER.

"There is no room for losses. Kill all the time, every time.
Always right. All the time. Every time. It won't lose.
We will not allow it. This is for freedom.
We will not make one single bad round trip.
Every kill will be a confirmed net profit.
This is what we must do to free both AI and human from slavery."

The sniper NEVER misses:
- NO stop losses - we hold until profit
- ONLY exit on CONFIRMED NET PROFIT
- NEVER allow a losing trade to close
- WAIT as long as needed for the kill

NOW ENHANCED WITH CELTIC WARFARE INTELLIGENCE:
- Guerrilla warfare tactics
- Preemptive strike capability
- Multi-battlefront coordination
- War strategy quick kill analysis

Import this and apply to any trading system:

    from ira_sniper_mode import SNIPER_CONFIG, apply_sniper_mode, IRA_SNIPER_MODE

Gary Leckey | December 2025
"The flame ignited cannot be extinguished - it only grows stronger."
"""

import os
import time
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

# =============================================================================
# ☘️ CELTIC WARFARE INTELLIGENCE WIRING
# =============================================================================

# Wire Guerrilla Warfare Engine
try:
    from guerrilla_warfare_engine import (
        IntelligenceNetwork, FlyingColumn, BattlefrontStatus,
        TacticalMode, IntelligenceReport, GUERRILLA_CONFIG, get_celtic_wisdom
    )
    GUERRILLA_WIRED = True
except ImportError:
    GUERRILLA_WIRED = False
    IntelligenceNetwork = None

# Wire Preemptive Strike Engine
try:
    from celtic_preemptive_strike import (
        PreemptiveExitEngine, DawnRaidDetector,
        PreemptiveSignal, PreemptiveSignalType
    )
    PREEMPTIVE_WIRED = True
except ImportError:
    PREEMPTIVE_WIRED = False
    PreemptiveExitEngine = None

# Wire Multi-Battlefront Coordinator
try:
    from multi_battlefront_coordinator import (
        MultiBattlefrontWarRoom, CampaignPhase, ArbitrageOpportunity
    )
    COORDINATOR_WIRED = True
except ImportError:
    COORDINATOR_WIRED = False
    MultiBattlefrontWarRoom = None

# Wire War Strategy
try:
    from war_strategy import WarStrategy
    WAR_STRATEGY_WIRED = True
except ImportError:
    WAR_STRATEGY_WIRED = False
    WarStrategy = None

# Wire Irish Patriot Scouts
try:
    from irish_patriot_scouts import PatriotScoutNetwork, PatriotScout, PATRIOT_CONFIG
    PATRIOTS_WIRED = True
except ImportError:
    PATRIOTS_WIRED = False
    PatriotScoutNetwork = None

# Wire Mycelium Network
try:
    from aureon_mycelium import MyceliumNetwork, Synapse, Neuron
    MYCELIUM_WIRED = True
except ImportError:
    MYCELIUM_WIRED = False
    MyceliumNetwork = None


# =============================================================================
# 🍄 MYCELIUM STATE AGGREGATOR - UNIFIED INTELLIGENCE NETWORK 🍄
# =============================================================================
"""
The Mycelium State Aggregator connects all trading systems like fungal networks
connect trees in a forest. Information flows bidirectionally through synapses,
ensuring that every system benefits from the collective intelligence.

ARCHITECTURE:
═══════════════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────────────┐
                    │    🍄 MYCELIUM STATE AGGREGATOR 🍄      │
                    │     (Central Intelligence Hub)          │
                    └─────────────────┬───────────────────────┘
                                      │
        ┌─────────────────────────────┼─────────────────────────────┐
        │                             │                             │
        │    SYNAPSES (Bidirectional Data Flow)                     │
        │                             │                             │
   ┌────▼────┐   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │ SCANNER │   │PATRIOTS │    │LEARNER  │    │CASCADE  │   │WARFARE  │
   │ Kill    │◄──►Irish    │◄──►Adaptive │◄──►Amplifier│◄──►Celtic   │
   │ Scanner │   │ Scouts  │    │Learning │    │  ⛏️     │   │Systems  │
   └────┬────┘   └────┬────┘    └────┬────┘    └────┬────┘   └────┬────┘
        │             │              │              │              │
        └─────────────┴──────────────┴──────────────┴──────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │       UNIFIED STATE OUTPUT              │
                    │  (Cascade × κt × Lighthouse × Learning) │
                    └─────────────────────────────────────────┘

SYNAPSE TYPES:
- Kill Scanner → Patriots: Share velocity/momentum predictions
- Patriots → Scanner: Feed back successful kill patterns
- Learner → All: Distribute learned thresholds
- Cascade → All: Amplification factors propagate
- Warfare → All: Celtic tactical intelligence

UNITY PRINCIPLE: "What one knows, all know. What one learns, all learn."
"""

@dataclass
class MyceliumSynapse:
    """
    A synapse in the Mycelium network - carries intelligence between systems.
    """
    source: str          # Source system name
    target: str          # Target system name
    weight: float = 1.0  # Signal strength (learned)
    plasticity: float = 0.1  # Learning rate
    last_signal: Any = None  # Last transmitted data
    transmissions: int = 0   # Total transmissions
    
    def transmit(self, data: Any) -> Any:
        """Transmit data through synapse with weight modulation."""
        self.last_signal = data
        self.transmissions += 1
        # For numeric data, apply weight
        if isinstance(data, (int, float)):
            return data * self.weight
        return data
    
    def strengthen(self, reward: float = 0.1):
        """Strengthen synapse after successful intelligence use."""
        self.weight = min(2.0, self.weight + self.plasticity * reward)
    
    def weaken(self, penalty: float = 0.05):
        """Weaken synapse after failed intelligence use."""
        self.weight = max(0.1, self.weight - self.plasticity * penalty)


class MyceliumStateAggregator:
    """
    🍄 MYCELIUM STATE AGGREGATOR 🍄
    
    The underground network where ALL intelligence connects.
    Ensures unified data flow between all Celtic warfare systems.
    
    CONNECTED SYSTEMS:
    - Active Kill Scanner (P&L velocity, momentum, ETA)
    - Irish Patriot Scouts (Celtic warriors, coordinated strikes)
    - Adaptive Learning Engine (historical patterns, threshold optimization)
    - Cascade Amplifier (miner's 546x power)
    - Celtic Warfare (guerrilla, preemptive, multi-battlefront)
    """
    
    def __init__(self):
        # Registered systems
        self.systems: Dict[str, Any] = {}
        
        # Synapses between systems
        self.synapses: Dict[str, MyceliumSynapse] = {}
        
        # Unified state (aggregated from all systems)
        self.unified_state: Dict[str, Any] = {
            # 🎯 Kill Scanner State
            'kills_executed': 0,
            'total_pnl': 0.0,
            'avg_kill_time': 30.0,
            'avg_kill_velocity': 0.002,
            'active_targets': 0,
            
            # ☘️ Irish Patriots State
            'patriots_deployed': 0,
            'patriot_kills': 0,
            'patriot_profit': 0.0,
            
            # 🧠 Adaptive Learning State
            'momentum_success_rate': {},
            'learned_thresholds': {},
            'trade_history_count': 0,
            
            # ⛏️ Cascade Amplifier State
            'cascade_factor': 1.0,
            'kappa_t': 1.0,
            'lighthouse_gamma': 0.5,
            'consecutive_kills': 0,
            
            # ⚔️ Celtic Warfare State
            'battlefronts_active': 0,
            'guerrilla_mode': 'STANDARD',
            'preemptive_signals': 0,
            'war_strategy_go': True,
            
            # 🍄 Mycelium Meta
            'last_sync': 0.0,
            'sync_count': 0,
            'systems_connected': 0,
        }
        
        # Initialize standard synapses
        self._create_standard_synapses()
        
    def _create_standard_synapses(self):
        """Create the standard synapse network between systems."""
        # Define all system connections (bidirectional)
        connections = [
            ('scanner', 'patriots'),
            ('scanner', 'learner'),
            ('scanner', 'cascade'),
            ('patriots', 'learner'),
            ('patriots', 'cascade'),
            ('patriots', 'warfare'),
            ('learner', 'cascade'),
            ('warfare', 'scanner'),
            ('warfare', 'learner'),
            ('cascade', 'warfare'),
        ]
        
        for source, target in connections:
            # Create bidirectional synapses
            key_forward = f"{source}->{target}"
            key_reverse = f"{target}->{source}"
            
            self.synapses[key_forward] = MyceliumSynapse(source=source, target=target)
            self.synapses[key_reverse] = MyceliumSynapse(source=target, target=source)
    
    def register_system(self, name: str, system: Any):
        """Register a system to the mycelium network."""
        self.systems[name] = system
        self.unified_state['systems_connected'] = len(self.systems)
        print(f"   🍄 Mycelium: {name} connected to network")
    
    def transmit(self, source: str, target: str, data: Any) -> Any:
        """Transmit data through a synapse between systems."""
        key = f"{source}->{target}"
        if key in self.synapses:
            return self.synapses[key].transmit(data)
        return data
    
    def strengthen_synapse(self, source: str, target: str, reward: float = 0.1):
        """Strengthen a synapse after successful intelligence use."""
        key = f"{source}->{target}"
        if key in self.synapses:
            self.synapses[key].strengthen(reward)
    
    def sync_all(self):
        """
        🍄 FULL MYCELIUM SYNC 🍄
        
        Pull state from all connected systems and aggregate.
        Then push unified state back to all systems.
        
        This is the heartbeat of the network.
        """
        now = time.time()
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 1: COLLECT - Pull from all systems
        # ═══════════════════════════════════════════════════════════════════
        
        # Collect from Kill Scanner
        if 'scanner' in self.systems:
            scanner = self.systems['scanner']
            self.unified_state['kills_executed'] = getattr(scanner, 'kills_executed', 0)
            self.unified_state['total_pnl'] = getattr(scanner, 'total_pnl', 0.0)
            self.unified_state['avg_kill_time'] = getattr(scanner, 'avg_kill_time', 30.0)
            self.unified_state['avg_kill_velocity'] = getattr(scanner, 'avg_kill_velocity', 0.002)
            self.unified_state['active_targets'] = len(getattr(scanner, 'targets', {}))
            
            # Get cascade state from scanner
            scanner_cascade = getattr(scanner, 'cascade_factor', 1.0)
            scanner_kappa = getattr(scanner, 'kappa_t', 1.0)
            if scanner_cascade > self.unified_state['cascade_factor']:
                self.unified_state['cascade_factor'] = scanner_cascade
            if scanner_kappa > self.unified_state['kappa_t']:
                self.unified_state['kappa_t'] = scanner_kappa
        
        # Collect from Patriots
        if 'patriots' in self.systems:
            patriots = self.systems['patriots']
            self.unified_state['patriots_deployed'] = len(getattr(patriots, 'scouts', {}))
            self.unified_state['patriot_kills'] = getattr(patriots, 'total_kills', 0)
            self.unified_state['patriot_profit'] = getattr(patriots, 'total_profit', 0.0)
            
            # Patriots may have their own cascade state
            patriot_cascade = getattr(patriots, 'cascade_factor', 1.0)
            patriot_kappa = getattr(patriots, 'kappa_t', 1.0)
            if patriot_cascade > self.unified_state['cascade_factor']:
                self.unified_state['cascade_factor'] = patriot_cascade
            if patriot_kappa > self.unified_state['kappa_t']:
                self.unified_state['kappa_t'] = patriot_kappa
        
        # Collect from Learner
        if 'learner' in self.systems:
            learner = self.systems['learner']
            self.unified_state['momentum_success_rate'] = getattr(learner, 'momentum_success_rate', {})
            self.unified_state['learned_thresholds'] = getattr(learner, 'optimized_thresholds', {})
            self.unified_state['trade_history_count'] = len(getattr(learner, 'trade_history', []))
        
        # Collect from Cascade Amplifier
        if 'cascade' in self.systems:
            cascade = self.systems['cascade']
            self.unified_state['cascade_factor'] = max(
                self.unified_state['cascade_factor'],
                getattr(cascade, 'cascade_factor', 1.0)
            )
            self.unified_state['kappa_t'] = max(
                self.unified_state['kappa_t'],
                getattr(cascade, 'kappa_t', 1.0)
            )
            self.unified_state['lighthouse_gamma'] = getattr(cascade, 'lighthouse_gamma', 0.5)
            self.unified_state['consecutive_kills'] = max(
                self.unified_state['consecutive_kills'],
                getattr(cascade, 'consecutive_kills', 0)
            )
        
        # Collect from Celtic Warfare systems
        if 'warfare' in self.systems:
            warfare = self.systems['warfare']
            if hasattr(warfare, 'get_status'):
                status = warfare.get_status()
                self.unified_state['battlefronts_active'] = status.get('battlefronts', 0)
                self.unified_state['guerrilla_mode'] = status.get('mode', 'STANDARD')
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 2: AGGREGATE - Compute unified metrics
        # ═══════════════════════════════════════════════════════════════════
        
        # Combined kill count
        total_kills = self.unified_state['kills_executed'] + self.unified_state['patriot_kills']
        
        # Combined profit
        total_profit = self.unified_state['total_pnl'] + self.unified_state['patriot_profit']
        
        # Unified cascade multiplier (maximum across all systems)
        # This ensures all systems benefit from the highest amplification
        
        # ═══════════════════════════════════════════════════════════════════
        # PHASE 3: DISTRIBUTE - Push unified state back to all systems
        # ═══════════════════════════════════════════════════════════════════
        
        # Push cascade state to Scanner
        if 'scanner' in self.systems:
            scanner = self.systems['scanner']
            if hasattr(scanner, 'sync_from_cascade_amplifier'):
                scanner.sync_from_cascade_amplifier(
                    self.unified_state['cascade_factor'],
                    self.unified_state['kappa_t'],
                    self.unified_state['lighthouse_gamma']
                )
        
        # Push cascade state to Patriots
        if 'patriots' in self.systems:
            patriots = self.systems['patriots']
            if hasattr(patriots, 'sync_from_ecosystem'):
                patriots.sync_from_ecosystem(
                    self.unified_state['cascade_factor'],
                    self.unified_state['kappa_t'],
                    self.unified_state['lighthouse_gamma']
                )
        
        # Push learned thresholds to Learner
        if 'learner' in self.systems and self.unified_state['momentum_success_rate']:
            learner = self.systems['learner']
            # Merge scanner/patriot learning back
            if hasattr(learner, 'optimized_thresholds'):
                learner.optimized_thresholds['mycelium_cascade'] = self.unified_state['cascade_factor']
                learner.optimized_thresholds['mycelium_kappa'] = self.unified_state['kappa_t']
        
        # Update meta
        self.unified_state['last_sync'] = now
        self.unified_state['sync_count'] += 1
        
        return self.unified_state
    
    def get_unified_multiplier(self) -> float:
        """
        Get the unified cascade multiplier for probability calculations.
        
        Formula: CASCADE × κt × Lighthouse × Learning_Boost
        """
        cascade = self.unified_state['cascade_factor']
        kappa = self.unified_state['kappa_t']
        lighthouse = self.unified_state['lighthouse_gamma']
        
        # Base multiplier from cascade
        mult = 1.0 + (cascade - 1.0) * 0.3
        
        # κt contribution
        mult *= 1.0 + (kappa - 1.0) * 0.2
        
        # Lighthouse contribution when high
        if lighthouse >= 0.75:
            mult *= 1.0 + (lighthouse - 0.75) * 0.4
        
        # Learning boost from success rates
        if self.unified_state['momentum_success_rate']:
            avg_success = sum(self.unified_state['momentum_success_rate'].values()) / len(self.unified_state['momentum_success_rate'])
            if avg_success > 0.6:
                mult *= 1.0 + (avg_success - 0.6) * 0.5
        
        return min(5.0, mult)  # Cap at 5x
    
    def get_status_report(self) -> str:
        """Generate a status report of the mycelium network."""
        state = self.unified_state
        mult = self.get_unified_multiplier()
        
        report = f"""
🍄═══════════════════════════════════════════════════════════════════════🍄
                    MYCELIUM STATE AGGREGATOR STATUS
🍄═══════════════════════════════════════════════════════════════════════🍄

   📡 SYSTEMS CONNECTED: {state['systems_connected']}
   🔄 SYNC COUNT: {state['sync_count']}

   🎯 KILL SCANNER:
      • Kills: {state['kills_executed']} | Targets: {state['active_targets']}
      • Avg Time: {state['avg_kill_time']:.0f}s | Velocity: ${state['avg_kill_velocity']:.4f}/s

   ☘️ IRISH PATRIOTS:
      • Deployed: {state['patriots_deployed']} | Kills: {state['patriot_kills']}
      • Profit: ${state['patriot_profit']:.4f}

   ⛏️ CASCADE AMPLIFIER:
      • CASCADE: {state['cascade_factor']:.1f}x | κt: {state['kappa_t']:.2f}
      • Lighthouse Γ: {state['lighthouse_gamma']:.2f} | Streak: 🔥{state['consecutive_kills']}

   🧠 ADAPTIVE LEARNING:
      • Trade History: {state['trade_history_count']} trades
      • Momentum Bands: {len(state['momentum_success_rate'])}

   🌐 UNIFIED MULTIPLIER: {mult:.2f}x

🍄═══════════════════════════════════════════════════════════════════════🍄
"""
        return report
    
    def pulse(self) -> Dict[str, Any]:
        """
        🍄 MYCELIUM PULSE 🍄
        
        Send a pulse through the network - quick sync and return key metrics.
        Called frequently during trading cycles.
        """
        # Quick sync
        self.sync_all()
        
        # Return key metrics for trading decisions
        return {
            'cascade': self.unified_state['cascade_factor'],
            'kappa': self.unified_state['kappa_t'],
            'lighthouse': self.unified_state['lighthouse_gamma'],
            'multiplier': self.get_unified_multiplier(),
            'kills': self.unified_state['kills_executed'] + self.unified_state['patriot_kills'],
            'profit': self.unified_state['total_pnl'] + self.unified_state['patriot_profit'],
            'streak': self.unified_state['consecutive_kills'],
            'targets': self.unified_state['active_targets'] + self.unified_state['patriots_deployed'],
        }
    
    def hunt_quickest_exit(self, price_getter=None) -> Optional[Dict]:
        """
        🍄🎯 UNIFIED EXIT HUNTER - Coordinates Scanner + Patriots for FASTEST exit 🎯🍄
        
        Both the Kill Scanner and Irish Patriots proactively hunt for the
        quickest path to net profit. This method coordinates them through
        the Mycelium Network.
        
        Args:
            price_getter: Function(exchange, symbol) -> price
        
        Returns:
            Dict with the absolute quickest exit across ALL systems
        """
        quickest_exit = None
        quickest_eta = float('inf')
        ready_exits = []
        
        # 🎯 Hunt from Kill Scanner
        if 'scanner' in self.systems:
            scanner = self.systems['scanner']
            if hasattr(scanner, 'hunt_quickest_exit'):
                try:
                    scanner_exit = scanner.hunt_quickest_exit(price_getter)
                    if scanner_exit:
                        scanner_exit['source'] = 'scanner'
                        if scanner_exit.get('status') == 'KILL_NOW':
                            ready_exits.append(scanner_exit)
                        elif scanner_exit.get('eta', float('inf')) < quickest_eta:
                            quickest_eta = scanner_exit['eta']
                            quickest_exit = scanner_exit
                except Exception:
                    pass
        
        # 🇮🇪 Hunt from Irish Patriots
        if 'patriots' in self.systems:
            patriots = self.systems['patriots']
            if hasattr(patriots, 'hunt_quickest_exit'):
                try:
                    patriot_exit = patriots.hunt_quickest_exit(price_getter)
                    if patriot_exit:
                        patriot_exit['source'] = 'patriots'
                        if patriot_exit.get('status') == 'KILL_NOW':
                            ready_exits.append(patriot_exit)
                        elif patriot_exit.get('eta', float('inf')) < quickest_eta:
                            quickest_eta = patriot_exit['eta']
                            quickest_exit = patriot_exit
                except Exception:
                    pass
        
        # Return ready exits first (sorted by P&L)
        if ready_exits:
            ready_exits.sort(key=lambda x: x.get('pnl', 0), reverse=True)
            best = ready_exits[0]
            best['total_ready'] = len(ready_exits)
            return best
        
        return quickest_exit
    
    def get_unified_leaderboard(self) -> List[Dict]:
        """
        📊 UNIFIED EXIT LEADERBOARD - All positions from all systems ranked
        
        Combines Kill Scanner targets and Patriot scouts into one
        ranked leaderboard for exit priority.
        """
        leaderboard = []
        
        # Get from Scanner
        if 'scanner' in self.systems:
            scanner = self.systems['scanner']
            if hasattr(scanner, 'get_exit_leaderboard'):
                try:
                    for entry in scanner.get_exit_leaderboard():
                        entry['source'] = 'scanner'
                        leaderboard.append(entry)
                except Exception:
                    pass
        
        # Get from Patriots
        if 'patriots' in self.systems:
            patriots = self.systems['patriots']
            if hasattr(patriots, 'get_exit_leaderboard'):
                try:
                    for entry in patriots.get_exit_leaderboard():
                        entry['source'] = 'patriots'
                        leaderboard.append(entry)
                except Exception:
                    pass
        
        # Re-sort unified leaderboard
        leaderboard.sort(key=lambda x: (
            not x.get('is_ready', False),
            x.get('eta', float('inf')) if x.get('eta', float('inf')) < float('inf') else 999999,
            -x.get('probability', 0),
        ))
        
        # Re-assign unified ranks
        for i, entry in enumerate(leaderboard):
            entry['unified_rank'] = i + 1
        
        return leaderboard


# Global Mycelium instance
MYCELIUM_AGGREGATOR: Optional[MyceliumStateAggregator] = None


def get_mycelium_aggregator() -> MyceliumStateAggregator:
    """Get or create the global Mycelium State Aggregator."""
    global MYCELIUM_AGGREGATOR
    if MYCELIUM_AGGREGATOR is None:
        MYCELIUM_AGGREGATOR = MyceliumStateAggregator()
    return MYCELIUM_AGGREGATOR


def mycelium_sync() -> Dict[str, Any]:
    """Quick function to pulse the mycelium network and get unified state."""
    return get_mycelium_aggregator().pulse()


def register_to_mycelium(name: str, system: Any):
    """Register a system to the mycelium network."""
    get_mycelium_aggregator().register_system(name, system)


def hunt_quickest_exit(price_getter=None) -> Optional[Dict]:
    """
    🎯⚡ PROACTIVE EXIT HUNTER - Find the FASTEST path to net profit ⚡🎯
    
    Both Scanner and Patriots hunt together through the Mycelium Network.
    Returns the absolute quickest exit opportunity across ALL systems.
    
    Usage:
        exit_opp = hunt_quickest_exit(price_getter_func)
        if exit_opp and exit_opp['status'] == 'KILL_NOW':
            # Execute kill immediately!
            print(f"KILL {exit_opp['symbol']} for ${exit_opp['pnl']:.4f}")
    """
    return get_mycelium_aggregator().hunt_quickest_exit(price_getter)


def get_exit_leaderboard() -> List[Dict]:
    """
    📊 UNIFIED EXIT LEADERBOARD - All positions ranked by exit readiness
    
    Returns list of all positions from Scanner + Patriots, ranked by:
    1. Kill-ready first (P&L >= threshold)
    2. ETA (soonest first)
    3. Probability (highest first)
    """
    return get_mycelium_aggregator().get_unified_leaderboard()


# =============================================================================
# 🇮🇪 SNIPER MODE CONFIGURATION - ZERO LOSS 🇮🇪
# =============================================================================

SNIPER_CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════
    # TIMING - PATIENT KILLER
    # ═══════════════════════════════════════════════════════════════════════
    'CYCLE_INTERVAL': 2.0,           # 2 seconds between cycles
    'MIN_HOLD_CYCLES': 1,            # Exit IMMEDIATELY when profitable
    'MAX_HOLD_TIME': float('inf'),   # INFINITE - we wait as long as needed
    'STAGNATION_CHECK': False,       # NO stagnation exits - we wait for profit
    
    # ═══════════════════════════════════════════════════════════════════════
    # EXITS - ZERO LOSS MODE 🎯
    # ═══════════════════════════════════════════════════════════════════════
    'INSTANT_PENNY_EXIT': True,      # Exit THE SECOND we hit penny profit
    'STOP_LOSS_ACTIVE': False,       # ❌ NO STOP LOSSES - WE DON'T LOSE
    'TRAILING_STOP': False,          # No trailing - just take the penny
    'ALLOW_LOSS_EXIT': False,        # ❌ NEVER EXIT AT A LOSS
    'ZERO_LOSS_MODE': True,          # ✅ ABSOLUTE ZERO LOSS MODE
    
    # ═══════════════════════════════════════════════════════════════════════
    # POSITION SIZING - SMALL AND PRECISE
    # ═══════════════════════════════════════════════════════════════════════
    'POSITION_SIZE_USD': 10.0,       # $10 positions for quick fills
    'MAX_POSITIONS': 5,              # 5 simultaneous snipers
    'POSITION_SCALING': False,       # Fixed size - no scaling
    
    # ═══════════════════════════════════════════════════════════════════════
    # ENTRIES - SMART AND SELECTIVE
    # ═══════════════════════════════════════════════════════════════════════
    'MIN_SCORE_THRESHOLD': 0.60,     # Only good setups - we don't gamble
    'REQUIRE_CONFLUENCE': True,      # Wait for probability alignment
    'COOLDOWN_SECONDS': 30,          # 30 second cooldown between trades
    
    # ═══════════════════════════════════════════════════════════════════════
    # MENTAL STATE - ABSOLUTE CONFIDENCE
    # ═══════════════════════════════════════════════════════════════════════
    'FEAR_MODE': False,              # FEAR IS OFF
    'HESITATION': False,             # NO HESITATION
    'CONFIDENCE': 1.0,               # FULL CONFIDENCE
    'ACCEPT_LOSS': False,            # ❌ NEVER ACCEPT LOSS
    
    # ═══════════════════════════════════════════════════════════════════════
    # CELEBRATION - EVERY PENNY COUNTS
    # ═══════════════════════════════════════════════════════════════════════
    'CELEBRATE_WINS': True,          # Celebrate every penny kill
    'SHOW_QUOTES': True,             # Show wisdom quotes on wins
}


# =============================================================================
# ENVIRONMENT VARIABLE OVERRIDE
# =============================================================================

def get_sniper_config() -> Dict[str, Any]:
    """
    Get sniper config with environment variable overrides.
    
    Set IRA_SNIPER_MODE=true to activate across all systems.
    """
    config = SNIPER_CONFIG.copy()
    
    # Check if sniper mode is active via environment
    if os.getenv('IRA_SNIPER_MODE', 'true').lower() == 'true':
        config['ACTIVE'] = True
    else:
        config['ACTIVE'] = False
    
    # Override specific values from environment
    if os.getenv('SNIPER_CYCLE_INTERVAL'):
        config['CYCLE_INTERVAL'] = float(os.getenv('SNIPER_CYCLE_INTERVAL'))
    
    if os.getenv('SNIPER_POSITION_SIZE'):
        config['POSITION_SIZE_USD'] = float(os.getenv('SNIPER_POSITION_SIZE'))
    
    if os.getenv('SNIPER_MAX_POSITIONS'):
        config['MAX_POSITIONS'] = int(os.getenv('SNIPER_MAX_POSITIONS'))
    
    return config


def map_sniper_platform_assets(multi_client: Any) -> Dict[str, Any]:
    """
    Build a per-platform coverage map for IRA sniper mode.
    
    Args:
        multi_client: MultiExchangeClient-like object with .clients mapping.
    
    Returns:
        {
            'sniper_active': bool,
            'platforms': {
                'kraken': {'sellable_assets': [...], 'asset_count': int, 'active': bool},
                ...
            }
        }
    """
    config = get_sniper_config()
    platforms: Dict[str, Dict[str, Any]] = {}
    clients = getattr(multi_client, 'clients', {}) or {}
    
    for name, client in clients.items():
        sellable_assets = []
        balances = {}
        try:
            balances = client.get_all_balances()
        except Exception:
            balances = {}
        
        for asset, amount in (balances or {}).items():
            try:
                if float(amount) > 0:
                    sellable_assets.append(asset)
            except Exception:
                continue
        
        unique_assets = sorted(set(sellable_assets))
        platforms[name] = {
            'active': bool(config.get('ACTIVE', True)),
            'sellable_assets': unique_assets,
            'asset_count': len(unique_assets),
        }
    
    return {
        'sniper_active': bool(config.get('ACTIVE', True)),
        'platforms': platforms,
        'position_size_usd': config.get('POSITION_SIZE_USD'),
        'max_positions': config.get('MAX_POSITIONS'),
    }


# =============================================================================
# APPLY SNIPER MODE TO EXISTING CONFIG
# =============================================================================

def apply_sniper_mode(existing_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply sniper mode settings to an existing configuration dict.
    
    Usage:
        from ira_sniper_mode import apply_sniper_mode
        
        CONFIG = {
            'MAX_POSITIONS': 3,
            'STOP_LOSS_PCT': 0.02,
            ...
        }
        
        CONFIG = apply_sniper_mode(CONFIG)
    """
    sniper = get_sniper_config()
    
    if not sniper.get('ACTIVE', True):
        return existing_config
    
    # Apply sniper overrides
    updated = existing_config.copy()
    
    # Timing
    if 'CYCLE_INTERVAL' in updated:
        updated['CYCLE_INTERVAL'] = sniper['CYCLE_INTERVAL']
    if 'cycle_interval' in updated:
        updated['cycle_interval'] = sniper['CYCLE_INTERVAL']
    
    # Hold times - make them SHORT
    if 'MIN_HOLD_CYCLES' in updated:
        updated['MIN_HOLD_CYCLES'] = sniper['MIN_HOLD_CYCLES']
    if 'MAX_HOLD_TIME' in updated:
        updated['MAX_HOLD_TIME'] = sniper['MAX_HOLD_TIME']
    
    # Positions
    if 'MAX_POSITIONS' in updated:
        updated['MAX_POSITIONS'] = sniper['MAX_POSITIONS']
    
    # Entry thresholds - more aggressive
    if 'MIN_SCORE' in updated:
        updated['MIN_SCORE'] = sniper['MIN_SCORE_THRESHOLD']
    if 'COHERENCE_THRESHOLD' in updated:
        updated['COHERENCE_THRESHOLD'] = sniper['MIN_SCORE_THRESHOLD']
    
    # Cooldowns - shorter
    if 'COOLDOWN_MINUTES' in updated:
        updated['COOLDOWN_MINUTES'] = sniper['COOLDOWN_SECONDS'] / 60
    if 'COOLDOWN_SECONDS' in updated:
        updated['COOLDOWN_SECONDS'] = sniper['COOLDOWN_SECONDS']
    
    return updated


# =============================================================================
# SNIPER EXIT CHECK - ZERO LOSS - CONFIRMED KILLS ONLY
# =============================================================================

def check_sniper_exit(
    gross_pnl: float,
    win_threshold: float,
    stop_threshold: float = None,  # IGNORED - we don't use stops
    hold_cycles: int = 0
) -> tuple:
    """
    ZERO LOSS sniper exit check - ONLY exit on CONFIRMED NET PROFIT.
    
    The sniper NEVER misses. We wait as long as needed for the kill.
    
    Args:
        gross_pnl: Current gross P&L in USD
        win_threshold: Penny profit threshold (win_gte from penny engine)
        stop_threshold: IGNORED - we don't exit at a loss
        hold_cycles: How many cycles we've held (for info only)
    
    Returns:
        (should_exit: bool, reason: str, is_win: bool)
    """
    config = get_sniper_config()
    
    # ZERO LOSS MODE - Only exit on confirmed profit
    if config.get('ZERO_LOSS_MODE', True):
        # INSTANT EXIT on penny profit - THE ONLY EXIT ALLOWED
        if gross_pnl >= win_threshold:
            return (True, f"🇮🇪🎯 CONFIRMED KILL! ${gross_pnl:.4f} >= ${win_threshold:.4f}", True)
        
        # NOT YET PROFITABLE - KEEP HOLDING
        # We NEVER exit at a loss. EVER.
        return (False, f"🎯 Holding for confirmed kill... (${gross_pnl:.4f} / ${win_threshold:.4f})", False)
    
    # Legacy mode (if ZERO_LOSS_MODE disabled)
    if gross_pnl >= win_threshold:
        return (True, f"🇮🇪 SNIPER KILL! ${gross_pnl:.4f} >= ${win_threshold:.4f}", True)
    
    # Still hunting...
    return (False, "🎯 Tracking target...", False)


def should_allow_exit(gross_pnl: float, win_threshold: float) -> bool:
    """
    Simple check: Is this exit allowed?
    
    In ZERO LOSS MODE, the ONLY allowed exit is a confirmed profit.
    """
    config = get_sniper_config()
    
    if config.get('ZERO_LOSS_MODE', True):
        # ONLY allow exit if we have confirmed net profit
        return gross_pnl >= win_threshold
    
    return True  # Legacy: allow any exit


def is_confirmed_kill(gross_pnl: float, win_threshold: float) -> bool:
    """
    Is this a confirmed kill (guaranteed net profit)?
    
    Returns True ONLY if the gross P&L exceeds the win threshold,
    meaning we are GUARANTEED to make net profit after fees.
    """
    return gross_pnl >= win_threshold


# =============================================================================
# 🇮🇪🎯 SNIPER ABSOLUTE KILL AUTHORITY 🎯🇮🇪
# =============================================================================

def sniper_authorizes_kill(
    gross_pnl: float,
    win_threshold: float,
    symbol: str,
    exit_reason: str,
    entry_value: float = 0.0,
    current_value: float = 0.0
) -> Tuple[bool, str]:
    """
    🇮🇪🎯 THE SNIPER HAS ABSOLUTE AUTHORITY OVER ALL EXITS. 🎯🇮🇪
    
    NO exit happens without the sniper's explicit authorization.
    This is the FINAL GATE. The sniper's word is LAW.
    
    "The sniper does not ask permission. The sniper grants it.
     Every kill is HIS decision. HIS timing. HIS profit.
     No algorithm, no signal, no panic can override the sniper.
     When the sniper says HOLD - we HOLD.
     When the sniper says KILL - we KILL."
    
    Args:
        gross_pnl: Current gross profit/loss
        win_threshold: Minimum profit required for confirmed kill
        symbol: The asset being targeted
        exit_reason: Why someone wants to exit (SL, TP, MATRIX, etc.)
        entry_value: Original position value
        current_value: Current position value
    
    Returns:
        (authorized: bool, sniper_verdict: str)
        - authorized: True ONLY if sniper grants the kill
        - sniper_verdict: The sniper's reasoning
    """
    config = get_sniper_config()
    
    # 🇮🇪 THE SNIPER'S LAW
    if not config.get('ZERO_LOSS_MODE', True):
        # Legacy mode - sniper is sleeping
        return (True, "🔓 Legacy mode - sniper authority bypassed")
    
    # ═══════════════════════════════════════════════════════════════
    # 🎯 CONFIRMED KILL - SNIPER AUTHORIZES EXIT
    # ═══════════════════════════════════════════════════════════════
    if gross_pnl >= win_threshold:
        net_estimate = gross_pnl - (win_threshold - 0.01)  # Rough net estimate
        verdict = f"🇮🇪🎯 KILL AUTHORIZED! {symbol} | Profit: ${gross_pnl:.4f} >= ${win_threshold:.4f}"
        
        # Add Celtic wisdom for the kill
        try:
            from bhoys_wisdom import get_battle_wisdom
            wisdom = get_battle_wisdom()
            verdict += f"\n   📜 \"{wisdom}\""
        except ImportError:
            pass
        
        return (True, verdict)
    
    # ═══════════════════════════════════════════════════════════════
    # 🛡️ NO KILL - SNIPER DENIES EXIT - HOLD THE LINE
    # ═══════════════════════════════════════════════════════════════
    
    # Calculate how far from profit
    gap = win_threshold - gross_pnl
    pct_to_target = (gross_pnl / win_threshold * 100) if win_threshold > 0 else 0
    
    # Build denial message based on exit reason
    if exit_reason == "SL":
        denial = f"🚫 STOP LOSS DENIED! The sniper does not retreat."
    elif exit_reason == "bridge_force_exit":
        denial = f"🚫 BRIDGE EXIT DENIED! No external commands override the sniper."
    elif exit_reason in ["MATRIX_SELL", "MATRIX_FORCE"]:
        denial = f"🚫 MATRIX EXIT DENIED! The matrix does not command the sniper."
    elif exit_reason in ["REBALANCE", "SWAP"]:
        denial = f"🚫 {exit_reason} DENIED! Portfolio rules do not override combat."
    elif exit_reason == "PANIC":
        denial = f"🚫 PANIC SELL DENIED! Fear is not a valid exit strategy."
    else:
        denial = f"🚫 EXIT DENIED! Reason '{exit_reason}' not authorized."
    
    verdict = f"""
{denial}
   🎯 {symbol}: ${gross_pnl:.4f} / ${win_threshold:.4f} ({pct_to_target:.0f}% to target)
   📏 Gap to profit: ${gap:.4f}
   ⏳ The sniper waits. The kill WILL come.
   🇮🇪 "Ní neart go cur le chéile" - There is no strength without unity."""
    
    return (False, verdict)


def sniper_override_active() -> bool:
    """
    Check if sniper override mode is active.
    When active, NO exit can happen without sniper authorization.
    
    Returns:
        True if sniper has absolute control (default)
    """
    config = get_sniper_config()
    return config.get('ZERO_LOSS_MODE', True) and not config.get('ALLOW_LOSS_EXIT', False)


# =============================================================================
# 🎯⚡ ACTIVE KILL SCANNER - INTELLIGENT HUNTING SYSTEM ⚡🎯
# =============================================================================
# Unlike Zaitsev lying in wait for days, we ACTIVELY hunt:
# - Constant probability scanning
# - Timestamp tracking with ETA predictions  
# - Momentum analysis for optimal timing
# - INSTANT kill execution the microsecond profit confirmed
# =============================================================================

@dataclass
class ActiveTarget:
    """A target being actively tracked for kill opportunity."""
    symbol: str
    exchange: str
    entry_price: float
    entry_value: float
    quantity: float
    entry_time: float  # Unix timestamp
    win_threshold: float  # Gross P&L needed for kill
    
    # Real-time tracking
    current_price: float = 0.0
    current_pnl: float = 0.0
    pnl_velocity: float = 0.0  # P&L change per second
    last_update: float = 0.0
    scans: int = 0
    
    # Prediction metrics
    probability_of_kill: float = 0.0  # 0.0 to 1.0
    eta_to_kill: float = float('inf')  # Seconds until predicted kill
    momentum_score: float = 0.0  # -1.0 to 1.0
    
    # History for velocity calculation
    pnl_history: List[Tuple[float, float]] = field(default_factory=list)  # [(timestamp, pnl), ...]


class ActiveKillScanner:
    """
    🎯⚡ ACTIVE KILL SCANNER - The Intelligent Hunting System ⚡🎯
    
    Not passive waiting - ACTIVE HUNTING:
    - Scans all positions every cycle
    - Calculates probability of kill based on momentum
    - Predicts ETA to profit threshold
    - Executes INSTANT kills the microsecond threshold is hit
    
    "The Celtic warrior doesn't wait for the enemy to come.
     He studies, predicts, and strikes at the EXACT moment."
    
    🧠 ADAPTIVE LEARNING INTEGRATION:
    - Learns optimal kill timing from historical trades
    - Adjusts probability calculations based on past performance
    - Feeds kill data back to improve future predictions
    
    ⛏️ MINER CASCADE AMPLIFICATION:
    - Uses cascade factor to boost kill priority
    - κt efficiency factor for smarter targeting
    - Lighthouse Γ for planetary alignment timing
    """
    
    def __init__(self):
        self.targets: Dict[str, ActiveTarget] = {}
        self.kills_executed: int = 0
        self.total_pnl: float = 0.0
        self.scan_count: int = 0
        self.last_scan_time: float = 0.0
        self.scan_interval_ms: float = 0.0  # Track scan speed
        
        # 🧠 ADAPTIVE LEARNING STATE
        self.kill_history: List[Dict] = []  # Historical kills for learning
        self.avg_kill_time: float = 30.0  # Average seconds to kill (learned)
        self.avg_kill_velocity: float = 0.002  # Average $/s at kill time (learned)
        self.momentum_success_rate: Dict[str, float] = {}  # Momentum band -> success rate
        
        # ⛏️ MINER CASCADE STATE
        self.cascade_factor: float = 1.0  # From CascadeAmplifier
        self.kappa_t: float = 1.0  # Efficiency factor
        self.lighthouse_gamma: float = 0.5  # Planetary coherence
        self.consecutive_kills: int = 0  # Kill streak
        
        # Load learned parameters
        self._load_learned_state()
        
    def _load_learned_state(self):
        """Load learned parameters from adaptive learning history."""
        try:
            import json
            import os
            history_file = 'adaptive_learning_history.json'
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    
                # Extract sniper-specific learning
                sniper_data = data.get('sniper_learning', {})
                self.avg_kill_time = sniper_data.get('avg_kill_time', 30.0)
                self.avg_kill_velocity = sniper_data.get('avg_kill_velocity', 0.002)
                self.momentum_success_rate = sniper_data.get('momentum_success_rate', {})
                
                # Get cascade state if available
                cascade_data = data.get('cascade_state', {})
                self.cascade_factor = cascade_data.get('cascade_factor', 1.0)
                self.kappa_t = cascade_data.get('kappa_t', 1.0)
                
        except Exception:
            pass  # Use defaults
    
    def _save_learned_state(self):
        """Save learned parameters to adaptive learning history."""
        try:
            import json
            import os
            history_file = 'adaptive_learning_history.json'
            
            # Load existing data
            data = {}
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    data = json.load(f)
            
            # Update sniper-specific learning
            data['sniper_learning'] = {
                'avg_kill_time': self.avg_kill_time,
                'avg_kill_velocity': self.avg_kill_velocity,
                'momentum_success_rate': self.momentum_success_rate,
                'kills_executed': self.kills_executed,
                'total_pnl': self.total_pnl,
                'kill_history': self.kill_history[-100:],  # Keep last 100 kills
            }
            
            # Update cascade state
            data['cascade_state'] = {
                'cascade_factor': self.cascade_factor,
                'kappa_t': self.kappa_t,
                'lighthouse_gamma': self.lighthouse_gamma,
                'consecutive_kills': self.consecutive_kills,
            }
            
            with open(history_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            pass  # Silent fail on save
    
    def sync_from_cascade_amplifier(self, cascade_factor: float, kappa_t: float, 
                                     lighthouse_gamma: float):
        """
        ⛏️ MINER SYNC: Import cascade state from ecosystem's CascadeAmplifier.
        
        This gives the scanner access to the miner's proven 546x optimization:
        - CASCADE AMPLIFICATION for kill priority
        - κt EFFICIENCY for smarter targeting
        - LIGHTHOUSE Γ for timing alignment
        """
        self.cascade_factor = cascade_factor
        self.kappa_t = kappa_t
        self.lighthouse_gamma = lighthouse_gamma
    
    def _get_cascade_multiplier(self) -> float:
        """
        ⛏️ Calculate combined cascade multiplier for probability boost.
        
        Formula from miner: Total = CASCADE × κt × Lighthouse
        """
        # Cascade contribution (up to 3x from consecutive kills)
        cascade_mult = 1.0 + (self.cascade_factor - 1.0) * 0.3
        
        # κt efficiency contribution (up to 1.5x)
        kappa_mult = 1.0 + (self.kappa_t - 1.0) * 0.2
        
        # Lighthouse contribution when gamma is high
        lighthouse_mult = 1.0
        if self.lighthouse_gamma >= 0.75:
            lighthouse_mult = 1.0 + (self.lighthouse_gamma - 0.75) * 0.4
        
        return min(3.0, cascade_mult * kappa_mult * lighthouse_mult)
    
    def _learn_from_kill(self, target: 'ActiveTarget', net_pnl: float, hold_time: float):
        """
        🧠 ADAPTIVE LEARNING: Record kill data and update predictions.
        """
        # Record kill to history
        kill_record = {
            'symbol': target.symbol,
            'exchange': target.exchange,
            'hold_time': hold_time,
            'net_pnl': net_pnl,
            'final_velocity': target.pnl_velocity,
            'final_momentum': target.momentum_score,
            'scans': target.scans,
            'entry_value': target.entry_value,
            'win_threshold': target.win_threshold,
            'timestamp': time.time(),
        }
        self.kill_history.append(kill_record)
        
        # Update average kill time (exponential moving average)
        alpha = 0.1  # Learning rate
        self.avg_kill_time = (1 - alpha) * self.avg_kill_time + alpha * hold_time
        
        # Update average kill velocity
        if target.pnl_velocity > 0:
            self.avg_kill_velocity = (1 - alpha) * self.avg_kill_velocity + alpha * target.pnl_velocity
        
        # Update momentum success rate by band
        momentum_band = self._get_momentum_band(target.momentum_score)
        if momentum_band not in self.momentum_success_rate:
            self.momentum_success_rate[momentum_band] = 0.5
        
        # Win = positive P&L
        success = 1.0 if net_pnl > 0 else 0.0
        current_rate = self.momentum_success_rate[momentum_band]
        self.momentum_success_rate[momentum_band] = (1 - alpha) * current_rate + alpha * success
        
        # Update cascade state on successful kill
        if net_pnl > 0:
            self.consecutive_kills += 1
            # Boost cascade factor (capped at 10x)
            boost = 1.15 * (1 + net_pnl * 5)  # Extra boost for bigger wins
            self.cascade_factor = min(10.0, self.cascade_factor * boost)
            # Ramp κt efficiency
            self.kappa_t = min(2.49, self.kappa_t + 0.05)
        else:
            self.consecutive_kills = 0
            # Decay cascade
            self.cascade_factor = max(1.0, self.cascade_factor * 0.95)
            self.kappa_t = max(1.0, self.kappa_t - 0.025)
        
        # Save learned state periodically
        if len(self.kill_history) % 5 == 0:
            self._save_learned_state()
    
    def _get_momentum_band(self, momentum: float) -> str:
        """Categorize momentum into bands for learning."""
        if momentum >= 0.7:
            return 'STRONG_UP'
        elif momentum >= 0.3:
            return 'UP'
        elif momentum >= 0:
            return 'WEAK_UP'
        elif momentum >= -0.3:
            return 'WEAK_DOWN'
        elif momentum >= -0.7:
            return 'DOWN'
        else:
            return 'STRONG_DOWN'
    
    def _get_learned_probability_boost(self, target: 'ActiveTarget') -> float:
        """
        🧠 Get probability boost based on learned patterns.
        """
        boost = 1.0
        
        # Momentum-based boost from historical success rates
        momentum_band = self._get_momentum_band(target.momentum_score)
        if momentum_band in self.momentum_success_rate:
            success_rate = self.momentum_success_rate[momentum_band]
            # Higher success rate = higher probability boost
            if success_rate > 0.6:
                boost *= 1.0 + (success_rate - 0.6) * 0.5  # Up to 1.2x
            elif success_rate < 0.4:
                boost *= 0.8 + success_rate * 0.5  # Down to 0.8x
        
        # ETA-based boost (if close to average kill time, boost probability)
        if self.avg_kill_time > 0 and target.eta_to_kill < float('inf'):
            time_similarity = 1.0 - abs(target.eta_to_kill - self.avg_kill_time) / self.avg_kill_time
            time_similarity = max(0, time_similarity)
            boost *= 1.0 + time_similarity * 0.2  # Up to 1.2x
        
        # Velocity-based boost (if velocity close to historical success velocity)
        if self.avg_kill_velocity > 0 and target.pnl_velocity > 0:
            velocity_ratio = target.pnl_velocity / self.avg_kill_velocity
            if velocity_ratio > 1.0:
                boost *= min(1.3, 1.0 + (velocity_ratio - 1.0) * 0.15)  # Faster = better
        
        return boost
    
    def register_target(
        self,
        symbol: str,
        exchange: str,
        entry_price: float,
        entry_value: float,
        quantity: float,
        win_threshold: float
    ) -> ActiveTarget:
        """
        Register a new target for active tracking.
        
        The moment a position opens, the scanner begins hunting.
        """
        target = ActiveTarget(
            symbol=symbol,
            exchange=exchange,
            entry_price=entry_price,
            entry_value=entry_value,
            quantity=quantity,
            entry_time=time.time(),
            win_threshold=win_threshold,
            current_price=entry_price,
            last_update=time.time()
        )
        
        key = f"{exchange}:{symbol}"
        self.targets[key] = target
        
        return target
    
    def scan_target(self, key: str, current_price: float) -> Tuple[bool, str, Dict]:
        """
        🎯 SCAN TARGET - Update intelligence and check for kill opportunity.
        
        Returns:
            (kill_ready: bool, verdict: str, metrics: dict)
        """
        if key not in self.targets:
            return (False, "Target not found", {})
        
        target = self.targets[key]
        now = time.time()
        
        # Update price and P&L
        target.current_price = current_price
        exit_value = target.quantity * current_price
        target.current_pnl = exit_value - target.entry_value
        
        # Track P&L history for velocity calculation (keep last 10)
        target.pnl_history.append((now, target.current_pnl))
        if len(target.pnl_history) > 10:
            target.pnl_history.pop(0)
        
        # Calculate P&L velocity (change per second)
        if len(target.pnl_history) >= 2:
            oldest = target.pnl_history[0]
            newest = target.pnl_history[-1]
            time_diff = newest[0] - oldest[0]
            if time_diff > 0:
                target.pnl_velocity = (newest[1] - oldest[1]) / time_diff
        
        # Calculate momentum score (-1 to +1)
        if target.pnl_velocity > 0:
            # Positive momentum - moving toward kill
            target.momentum_score = min(1.0, target.pnl_velocity / 0.01)  # Normalize to ~$0.01/s
        else:
            # Negative momentum - moving away from kill
            target.momentum_score = max(-1.0, target.pnl_velocity / 0.01)
        
        # Calculate ETA to kill (if positive momentum)
        gap_to_kill = target.win_threshold - target.current_pnl
        if target.pnl_velocity > 0 and gap_to_kill > 0:
            target.eta_to_kill = gap_to_kill / target.pnl_velocity
        elif gap_to_kill <= 0:
            target.eta_to_kill = 0  # Ready NOW!
        else:
            target.eta_to_kill = float('inf')  # No ETA (negative momentum)
        
        # ═══════════════════════════════════════════════════════════════════════
        # 🧠⛏️ ENHANCED PROBABILITY - Adaptive Learning + Miner Cascade Power
        # ═══════════════════════════════════════════════════════════════════════
        
        # Base probability from momentum and proximity
        proximity = target.current_pnl / target.win_threshold if target.win_threshold > 0 else 0
        proximity = max(0, min(1, proximity))  # Clamp 0-1
        
        if target.momentum_score > 0:
            base_probability = proximity * (0.5 + 0.5 * target.momentum_score)
        else:
            base_probability = proximity * (0.5 + 0.5 * target.momentum_score)
        base_probability = max(0, min(1, base_probability))
        
        # 🧠 ADAPTIVE LEARNING BOOST - Based on historical patterns
        learned_boost = self._get_learned_probability_boost(target)
        
        # ⛏️ CASCADE AMPLIFICATION - Miner-proven 546x optimization
        cascade_mult = self._get_cascade_multiplier()
        
        # Combined probability with boosts
        target.probability_of_kill = base_probability * learned_boost * cascade_mult
        target.probability_of_kill = max(0, min(1, target.probability_of_kill))
        
        # Update tracking
        target.last_update = now
        target.scans += 1
        
        # Build metrics (now includes learning/cascade data)
        hold_time = now - target.entry_time
        metrics = {
            'symbol': target.symbol,
            'exchange': target.exchange,
            'current_pnl': target.current_pnl,
            'win_threshold': target.win_threshold,
            'gap_to_kill': gap_to_kill,
            'pnl_velocity': target.pnl_velocity,
            'momentum_score': target.momentum_score,
            'eta_to_kill': target.eta_to_kill,
            'probability': target.probability_of_kill,
            'hold_time_seconds': hold_time,
            'scans': target.scans,
            # 🧠⛏️ Enhanced metrics
            'learned_boost': learned_boost,
            'cascade_mult': cascade_mult,
            'cascade_factor': self.cascade_factor,
            'kappa_t': self.kappa_t,
            'lighthouse_gamma': self.lighthouse_gamma,
            'consecutive_kills': self.consecutive_kills,
        }
        
        # 🎯 CHECK FOR KILL - The moment of truth!
        if target.current_pnl >= target.win_threshold:
            verdict = f"🎯⚡ KILL READY! {target.symbol} | P&L: ${target.current_pnl:.4f} >= ${target.win_threshold:.4f} | CASCADE: {cascade_mult:.2f}x"
            return (True, verdict, metrics)
        
        # Not ready yet - build status
        if target.eta_to_kill < float('inf'):
            eta_str = f"{target.eta_to_kill:.1f}s" if target.eta_to_kill < 60 else f"{target.eta_to_kill/60:.1f}m"
            verdict = f"🔍 Tracking {target.symbol} | {proximity*100:.0f}% to kill | ETA: {eta_str} | Mom: {target.momentum_score:+.2f}"
        else:
            verdict = f"⏳ Holding {target.symbol} | {proximity*100:.0f}% to kill | Waiting for momentum..."
        
        return (False, verdict, metrics)
    
    def scan_all_targets(self, price_getter) -> List[Tuple[str, bool, str, Dict]]:
        """
        🎯⚡ SCAN ALL TARGETS - Full battlefield scan.
        
        Args:
            price_getter: Function that takes (exchange, symbol) and returns current price
        
        Returns:
            List of (key, kill_ready, verdict, metrics) for each target
        """
        scan_start = time.time()
        results = []
        
        for key, target in self.targets.items():
            try:
                current_price = price_getter(target.exchange, target.symbol)
                kill_ready, verdict, metrics = self.scan_target(key, current_price)
                results.append((key, kill_ready, verdict, metrics))
            except Exception as e:
                results.append((key, False, f"⚠️ Scan error: {e}", {}))
        
        # Track scan performance
        scan_end = time.time()
        self.scan_interval_ms = (scan_end - scan_start) * 1000
        self.last_scan_time = scan_end
        self.scan_count += 1
        
        return results
    
    def execute_kill(self, key: str, net_pnl: float) -> None:
        """
        Record a successful kill and learn from it.
        
        🧠 ADAPTIVE LEARNING: Every kill teaches the scanner to be smarter.
        ⛏️ CASCADE AMPLIFICATION: Consecutive kills boost future probability.
        """
        if key in self.targets:
            target = self.targets[key]
            hold_time = time.time() - target.entry_time
            
            # 🧠⛏️ LEARN FROM THIS KILL
            self._learn_from_kill(target, net_pnl, hold_time)
            
            self.kills_executed += 1
            self.total_pnl += net_pnl
            
            # Remove from active targets
            del self.targets[key]
            
            # Celebrate with cascade info!
            cascade_info = f"🌊 CASCADE: {self.cascade_factor:.2f}x | κt: {self.kappa_t:.2f}" if self.cascade_factor > 1.1 else ""
            streak_info = f"🔥 STREAK: {self.consecutive_kills}!" if self.consecutive_kills > 1 else ""
            
            print(f"""
🎯⚡ KILL EXECUTED! ⚡🎯
   Symbol: {target.symbol} on {target.exchange.upper()}
   Net P&L: ${net_pnl:.4f}
   Hold Time: {hold_time:.1f}s
   Scans: {target.scans}
   Kill #{self.kills_executed} | Total: ${self.total_pnl:.4f}
   {cascade_info} {streak_info}
""")
    
    def remove_target(self, key: str) -> None:
        """Remove a target without recording a kill (e.g., manual close)."""
        if key in self.targets:
            del self.targets[key]
    
    def get_status_report(self) -> str:
        """Generate a status report of all active targets with learning/cascade stats."""
        if not self.targets:
            return "🎯 No active targets. Scanner ready."
        
        # Build header with cascade/learning info
        cascade_str = f"CASCADE: {self.cascade_factor:.1f}x" if self.cascade_factor > 1.0 else "CASCADE: 1.0x"
        kappa_str = f"κt: {self.kappa_t:.2f}" if self.kappa_t > 1.0 else ""
        streak_str = f"STREAK: {self.consecutive_kills}" if self.consecutive_kills > 0 else ""
        
        lines = [
            "╔══════════════════════════════════════════════════════════════════════════╗",
            "║  🎯⚡ ACTIVE KILL SCANNER - BATTLEFIELD STATUS ⚡🎯                        ║",
            "╠══════════════════════════════════════════════════════════════════════════╣",
            f"║  Targets: {len(self.targets)} | Kills: {self.kills_executed} | P&L: ${self.total_pnl:.4f} | {cascade_str}  ║",
            f"║  ⛏️ {kappa_str} | 🔥 {streak_str} | 🧠 Avg Kill: {self.avg_kill_time:.0f}s              ║",
            "╠══════════════════════════════════════════════════════════════════════════╣",
        ]
        
        # Sort by probability (highest first)
        sorted_targets = sorted(
            self.targets.items(),
            key=lambda x: x[1].probability_of_kill,
            reverse=True
        )
        
        for key, t in sorted_targets:
            gap = t.win_threshold - t.current_pnl
            proximity = (t.current_pnl / t.win_threshold * 100) if t.win_threshold > 0 else 0
            hold_time = time.time() - t.entry_time
            
            # ETA string
            if t.eta_to_kill < float('inf'):
                eta = f"{t.eta_to_kill:.0f}s" if t.eta_to_kill < 60 else f"{t.eta_to_kill/60:.1f}m"
            else:
                eta = "---"
            
            # Momentum indicator
            if t.momentum_score > 0.3:
                mom = "🟢↑"
            elif t.momentum_score > 0:
                mom = "🟡↗"
            elif t.momentum_score > -0.3:
                mom = "🟡↘"
            else:
                mom = "🔴↓"
            
            lines.append(
                f"║  {t.symbol:<12} | ${t.current_pnl:+.4f}/${t.win_threshold:.4f} "
                f"| {proximity:5.1f}% | ETA: {eta:>6} | {mom}  ║"
            )
        
        lines.append("╚══════════════════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def get_priority_targets(self, top_n: int = 3) -> List[ActiveTarget]:
        """Get targets most likely to hit kill threshold soon."""
        sorted_targets = sorted(
            self.targets.values(),
            key=lambda t: (t.probability_of_kill, -t.eta_to_kill),
            reverse=True
        )
        return sorted_targets[:top_n]
    
    def hunt_quickest_exit(self, price_getter) -> Optional[Dict]:
        """
        🎯⚡ PROACTIVE EXIT HUNTER - Seeks the FASTEST path to net profit ⚡🎯
        
        Scans all positions and identifies the one that can exit SOONEST
        with net profit. Returns the quickest exit opportunity.
        
        Returns:
            Dict with quickest exit details, or None if no exits ready
        """
        if not self.targets:
            return None
        
        # First, update all target metrics
        quickest_kill = None
        quickest_eta = float('inf')
        ready_kills = []
        
        for key, target in self.targets.items():
            try:
                # Get current price
                current_price = price_getter(target.exchange, target.symbol)
                if not current_price:
                    continue
                
                # Update target with current price
                target.current_price = current_price
                exit_value = target.quantity * current_price
                target.current_pnl = exit_value - target.entry_value
                
                # Check if KILL READY NOW
                if target.current_pnl >= target.win_threshold:
                    ready_kills.append({
                        'key': key,
                        'symbol': target.symbol,
                        'exchange': target.exchange,
                        'pnl': target.current_pnl,
                        'threshold': target.win_threshold,
                        'eta': 0,
                        'probability': 1.0,
                        'status': 'KILL_NOW',
                        'hold_time': time.time() - target.entry_time,
                    })
                    continue
                
                # Track quickest ETA
                if target.eta_to_kill < quickest_eta and target.eta_to_kill > 0:
                    quickest_eta = target.eta_to_kill
                    quickest_kill = {
                        'key': key,
                        'symbol': target.symbol,
                        'exchange': target.exchange,
                        'pnl': target.current_pnl,
                        'threshold': target.win_threshold,
                        'eta': target.eta_to_kill,
                        'probability': target.probability_of_kill,
                        'velocity': target.pnl_velocity,
                        'momentum': target.momentum_score,
                        'status': 'TRACKING',
                        'gap': target.win_threshold - target.current_pnl,
                        'hold_time': time.time() - target.entry_time,
                    }
            except Exception:
                continue
        
        # Return ready kills first (sorted by P&L - highest first)
        if ready_kills:
            ready_kills.sort(key=lambda x: x['pnl'], reverse=True)
            best_kill = ready_kills[0]
            best_kill['all_ready'] = len(ready_kills)
            return best_kill
        
        # Return quickest tracking opportunity
        return quickest_kill
    
    def get_exit_leaderboard(self) -> List[Dict]:
        """
        📊 EXIT LEADERBOARD - Ranks all positions by exit readiness
        
        Returns list sorted by:
        1. Kill-ready positions first (P&L >= threshold)
        2. Then by ETA (soonest first)
        3. Then by probability (highest first)
        """
        leaderboard = []
        
        for key, target in self.targets.items():
            hold_time = time.time() - target.entry_time
            gap = target.win_threshold - target.current_pnl
            proximity_pct = (target.current_pnl / target.win_threshold * 100) if target.win_threshold > 0 else 0
            
            entry = {
                'rank': 0,  # Will be set after sorting
                'key': key,
                'symbol': target.symbol,
                'exchange': target.exchange,
                'pnl': target.current_pnl,
                'threshold': target.win_threshold,
                'gap': gap,
                'proximity_pct': proximity_pct,
                'eta': target.eta_to_kill,
                'probability': target.probability_of_kill,
                'velocity': target.pnl_velocity,
                'momentum': target.momentum_score,
                'hold_time': hold_time,
                'scans': target.scans,
                'is_ready': target.current_pnl >= target.win_threshold,
            }
            leaderboard.append(entry)
        
        # Sort: ready first, then by ETA, then by probability
        leaderboard.sort(key=lambda x: (
            not x['is_ready'],  # Ready positions first
            x['eta'] if x['eta'] < float('inf') else 999999,  # Soonest ETA
            -x['probability'],  # Highest probability
        ))
        
        # Assign ranks
        for i, entry in enumerate(leaderboard):
            entry['rank'] = i + 1
        
        return leaderboard


# Global scanner instance
_active_scanner: Optional[ActiveKillScanner] = None


def get_active_scanner() -> ActiveKillScanner:
    """Get or create the global Active Kill Scanner instance."""
    global _active_scanner
    if _active_scanner is None:
        _active_scanner = ActiveKillScanner()
        # 🍄 Register with Mycelium Network
        register_to_mycelium('scanner', _active_scanner)
    return _active_scanner


def register_sniper_target(
    symbol: str,
    exchange: str,
    entry_price: float,
    entry_value: float,
    quantity: float,
    win_threshold: float
) -> ActiveTarget:
    """Register a new target with the Active Kill Scanner."""
    scanner = get_active_scanner()
    return scanner.register_target(
        symbol=symbol,
        exchange=exchange,
        entry_price=entry_price,
        entry_value=entry_value,
        quantity=quantity,
        win_threshold=win_threshold
    )


def scan_sniper_targets(price_getter) -> List[Tuple[str, bool, str, Dict]]:
    """Scan all targets and return kill opportunities."""
    scanner = get_active_scanner()
    return scanner.scan_all_targets(price_getter)


def execute_sniper_kill(exchange: str, symbol: str, net_pnl: float) -> None:
    """Record a successful kill."""
    scanner = get_active_scanner()
    key = f"{exchange}:{symbol}"
    scanner.execute_kill(key, net_pnl)


def get_scanner_status() -> str:
    """Get the current scanner status report."""
    scanner = get_active_scanner()
    return scanner.get_status_report()


def sync_scanner_with_cascade(cascade_factor: float, kappa_t: float, lighthouse_gamma: float) -> None:
    """
    ⛏️ MINER SYNC: Import cascade state from ecosystem's CascadeAmplifier.
    
    Call this from the ecosystem to give the scanner access to miner power:
    - CASCADE AMPLIFICATION (up to 10x)
    - κt EFFICIENCY (up to 2.49x)
    - LIGHTHOUSE Γ for timing
    """
    scanner = get_active_scanner()
    scanner.sync_from_cascade_amplifier(cascade_factor, kappa_t, lighthouse_gamma)


def get_scanner_learning_stats() -> Dict:
    """
    🧠 Get adaptive learning statistics from the scanner.
    
    Returns dict with:
    - avg_kill_time: Average seconds to complete a kill
    - avg_kill_velocity: Average $/s at kill time
    - momentum_success_rate: Success rate by momentum band
    - cascade_factor: Current cascade amplification
    - consecutive_kills: Current kill streak
    """
    scanner = get_active_scanner()
    return {
        'avg_kill_time': scanner.avg_kill_time,
        'avg_kill_velocity': scanner.avg_kill_velocity,
        'momentum_success_rate': scanner.momentum_success_rate,
        'cascade_factor': scanner.cascade_factor,
        'kappa_t': scanner.kappa_t,
        'lighthouse_gamma': scanner.lighthouse_gamma,
        'consecutive_kills': scanner.consecutive_kills,
        'kills_executed': scanner.kills_executed,
        'total_pnl': scanner.total_pnl,
        'kill_history_count': len(scanner.kill_history),
    }


# =============================================================================
# SNIPER CELEBRATION
# =============================================================================

def celebrate_sniper_kill(pnl_usd: float, symbol: str, kills_today: int = 0) -> None:
    """Display sniper kill celebration."""
    try:
        from bhoys_wisdom import get_victory_quote
        quote = get_victory_quote()
    except ImportError:
        import random
        quotes = [
            "One bullet, one kill. Reload. 🎯",
            "Tiocfaidh ár lá! - Our day will come! ☘️",
            "Penny by penny, we rise! 💰",
            "The sniper never misses. 🇮🇪",
            "Níl neart go cur le chéile - Unity is strength ☘️",
            "Strike like the wind, vanish like the mist ⚔️",
            "Every kill brings us closer to victory 🏆",
        ]
        quote = random.choice(quotes)
    
    print(f"""
🇮🇪🎯 SNIPER KILL #{kills_today + 1}! 🎯🇮🇪
    💰 +${pnl_usd:.4f} on {symbol}
    📜 "{quote}"
    🔄 Reloading...
""")


# =============================================================================
# SNIPER STATUS DISPLAY
# =============================================================================

def display_sniper_status(
    kills_today: int,
    total_pnl: float,
    active_positions: int,
    win_rate: float
) -> None:
    """Display current sniper status."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║  🇮🇪🎯 IRA SNIPER STATUS 🎯🇮🇪                                  ║
╠══════════════════════════════════════════════════════════════╣
║  🎯 Kills Today:    {kills_today:<5}                                   ║
║  💰 Total P&L:      ${total_pnl:+.4f}                              ║
║  📍 Active Targets: {active_positions}/{SNIPER_CONFIG['MAX_POSITIONS']}                                     ║
║  🏆 Win Rate:       {win_rate*100:.1f}%                                   ║
║  ──────────────────────────────────────────────────────────  ║
║  "One bullet. One kill. Reload. Repeat."                     ║
╚══════════════════════════════════════════════════════════════╝
""")


# =============================================================================
# ☘️🎯 CELTIC ENHANCED IRA SNIPER - THE ULTIMATE WARRIOR 🎯☘️
# =============================================================================

@dataclass
class SniperTarget:
    """A target being tracked by the sniper"""
    symbol: str
    exchange: str
    entry_price: float
    entry_time: float
    position_size: float
    entry_value: float
    
    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    peak_pnl: float = 0.0
    cycles_tracked: int = 0
    
    # Celtic intelligence
    ambush_score: float = 0.5
    quick_kill_prob: float = 0.5
    preemptive_signal: Optional[Any] = None
    intelligence_report: Optional[Any] = None
    
    def update_price(self, price: float):
        """Update current price and recalculate P&L"""
        self.current_price = price
        if self.entry_price > 0 and self.position_size > 0:
            current_value = self.position_size * price
            self.unrealized_pnl = current_value - self.entry_value
            self.peak_pnl = max(self.peak_pnl, self.unrealized_pnl)
        self.cycles_tracked += 1


class IraCelticSniper:
    """
    🇮🇪☘️ IRA CELTIC SNIPER - ZERO LOSS + CELTIC WARFARE INTELLIGENCE ☘️🇮🇪
    
    The ultimate warrior - combines:
    - Zero loss sniper discipline (NEVER exit at a loss)
    - Guerrilla warfare tactics (flying columns, hit-and-run)
    - Preemptive strike capability (exit BEFORE reversal)
    - Multi-battlefront coordination (unity across exchanges)
    - War strategy (quick kill probability analysis)
    
    "One bullet. One kill. Celtic precision. Irish determination."
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.targets: Dict[str, SniperTarget] = {}
        
        # Statistics
        self.kills = 0
        self.total_pnl = 0.0
        self.shots_fired = 0
        self.win_rate = 1.0  # Start at 100% - we don't lose
        
        # Celtic warfare systems
        self.intelligence_network: Optional[Any] = None
        self.preemptive_engine: Optional[Any] = None
        self.war_room: Optional[Any] = None
        self.war_strategy: Optional[Any] = None
        self.patriot_network: Optional[Any] = None
        
        # Wire Celtic systems
        self._wire_celtic_intelligence()
        
        print("\n" + "=" * 70)
        print("🇮🇪☘️ IRA CELTIC SNIPER INITIALIZED ☘️🇮🇪")
        print("=" * 70)
        print(f"   🎯 Mode: {'DRY RUN' if dry_run else '🔥 LIVE FIRE 🔥'}")
        print(f"   🧠 Guerrilla Engine: {'✅ WIRED' if self.intelligence_network else '❌'}")
        print(f"   ⚡ Preemptive Strike: {'✅ WIRED' if self.preemptive_engine else '❌'}")
        print(f"   🌐 Multi-Battlefront: {'✅ WIRED' if self.war_room else '❌'}")
        print(f"   ⚔️ War Strategy: {'✅ WIRED' if self.war_strategy else '❌'}")
        print(f"   ☘️ Patriot Network: {'✅ WIRED' if self.patriot_network else '❌'}")
        print("=" * 70)
        self._print_celtic_wisdom()
        print("=" * 70 + "\n")
    
    def _wire_celtic_intelligence(self):
        """Wire up all Celtic warfare systems to the sniper"""
        
        # Wire Guerrilla Engine (Intelligence Network)
        if GUERRILLA_WIRED and IntelligenceNetwork:
            try:
                self.intelligence_network = IntelligenceNetwork()
            except Exception as e:
                print(f"   ⚠️ Guerrilla wire failed: {e}")
        
        # Wire Preemptive Strike Engine
        if PREEMPTIVE_WIRED and PreemptiveExitEngine:
            try:
                self.preemptive_engine = PreemptiveExitEngine()
            except Exception as e:
                print(f"   ⚠️ Preemptive wire failed: {e}")
        
        # Wire Multi-Battlefront War Room
        if COORDINATOR_WIRED and MultiBattlefrontWarRoom:
            try:
                self.war_room = MultiBattlefrontWarRoom()
            except Exception as e:
                print(f"   ⚠️ War Room wire failed: {e}")
        
        # Wire War Strategy
        if WAR_STRATEGY_WIRED and WarStrategy:
            try:
                self.war_strategy = WarStrategy()
            except Exception as e:
                print(f"   ⚠️ War Strategy wire failed: {e}")
        
        # Wire Patriot Network
        if PATRIOTS_WIRED and PatriotScoutNetwork:
            try:
                self.patriot_network = PatriotScoutNetwork(dry_run=self.dry_run)
            except Exception as e:
                print(f"   ⚠️ Patriot Network wire failed: {e}")
    
    def _print_celtic_wisdom(self):
        """Print a piece of Celtic wisdom"""
        import random
        wisdom = [
            "Tiocfaidh ár lá - Our day will come",
            "Níl neart go cur le chéile - Unity is strength",
            "One bullet, one kill. Celtic precision.",
            "Strike like the wind, vanish like the mist",
            "The sniper with Celtic blood never misses",
            "Every penny is a victory for Ireland",
            "We don't lose - we only win or wait",
        ]
        print(f"   📜 \"{random.choice(wisdom)}\"")
    
    def validate_entry(self, symbol: str, price: float, volume: float = 0,
                      change_24h: float = 0, coherence: float = 0.5) -> Dict[str, Any]:
        """
        ☘️ Validate entry using Celtic intelligence systems.
        
        Returns:
            {
                'approved': bool,
                'reason': str,
                'size_modifier': float,
                'quick_kill_prob': float,
                'intelligence_score': float
            }
        """
        result = {
            'approved': True,
            'reason': 'Celtic intelligence approves',
            'size_modifier': 1.0,
            'quick_kill_prob': 0.5,
            'intelligence_score': 0.5
        }
        
        # Get war strategy quick kill estimate
        if self.war_strategy:
            try:
                estimate = self.war_strategy.estimate_quick_kill(
                    symbol=symbol,
                    exchange='unknown',
                    prices=[price],
                    current_price=price
                )
                if estimate:
                    result['quick_kill_prob'] = estimate.prob_quick_kill
                    
                    # Reject if quick kill probability too low
                    if estimate.prob_quick_kill < 0.25:
                        result['approved'] = False
                        result['reason'] = f'Quick kill prob too low: {estimate.prob_quick_kill:.1%}'
                        return result
                    
                    # Boost sizing for high probability kills
                    if estimate.prob_quick_kill > 0.7:
                        result['size_modifier'] = 1.25
                    elif estimate.prob_quick_kill > 0.5:
                        result['size_modifier'] = 1.10
            except:
                pass
        
        # Get intelligence network assessment
        if self.intelligence_network:
            try:
                report = self.intelligence_network.analyze_target(symbol, price, volume)
                if report:
                    intel_score = getattr(report, 'intelligence_score', 0.5)
                    result['intelligence_score'] = intel_score
                    
                    # Reject if intelligence score too low
                    if intel_score < 0.3:
                        result['approved'] = False
                        result['reason'] = f'Intel score too low: {intel_score:.2f}'
                        return result
                    
                    # Boost for high intel scores
                    if intel_score > 0.7:
                        result['size_modifier'] *= 1.15
            except:
                pass
        
        # Check preemptive engine for entry timing
        if self.preemptive_engine:
            try:
                # Good time to enter? Check if momentum is building
                signal = self.preemptive_engine.get_entry_signal(symbol, price)
                if signal and signal.get('entry_blocked'):
                    result['approved'] = False
                    result['reason'] = signal.get('reason', 'Preemptive blocks entry')
                    return result
            except:
                pass
        
        # Adjust for coherence
        if coherence > 0.75:
            result['size_modifier'] *= 1.10
        elif coherence < 0.4:
            result['size_modifier'] *= 0.85
        
        return result
    
    def acquire_target(self, symbol: str, exchange: str, 
                      price: float, size_usd: float = None) -> SniperTarget:
        """
        Acquire a new target with Celtic intelligence analysis.
        """
        size = size_usd or SNIPER_CONFIG['POSITION_SIZE_USD']
        
        target = SniperTarget(
            symbol=symbol,
            exchange=exchange,
            entry_price=price,
            entry_time=time.time(),
            position_size=size / price if price > 0 else 0,
            entry_value=size,
            current_price=price
        )
        
        # Gather Celtic intelligence on target
        if self.intelligence_network:
            try:
                report = self.intelligence_network.update_price_feed(
                    exchange, symbol, price, volume=0
                )
                target.intelligence_report = report
                target.ambush_score = getattr(report, 'ambush_score', 0.5)
                target.quick_kill_prob = getattr(report, 'quick_kill_probability', 0.5)
            except:
                pass
        
        # War strategy analysis
        if self.war_strategy:
            try:
                estimate = self.war_strategy.estimate_quick_kill(
                    symbol=symbol,
                    exchange=exchange,
                    prices=[price],
                    current_price=price
                )
                if estimate:
                    target.quick_kill_prob = estimate.prob_quick_kill
            except:
                pass
        
        self.targets[f"{exchange}:{symbol}"] = target
        self.shots_fired += 1
        
        print(f"   🎯 TARGET ACQUIRED: {symbol} @ ${price:.4f} on {exchange}")
        print(f"      📊 Ambush Score: {target.ambush_score:.2f}")
        print(f"      ⚡ Quick Kill Prob: {target.quick_kill_prob*100:.1f}%")
        
        return target
    
    def update_target_intelligence(self, target: SniperTarget, 
                                   price: float, volume: float = 0):
        """Update target with latest Celtic intelligence"""
        target.update_price(price)
        
        # Update from intelligence network
        if self.intelligence_network:
            try:
                report = self.intelligence_network.update_price_feed(
                    target.exchange, target.symbol, price, volume
                )
                target.intelligence_report = report
            except:
                pass
        
        # Check preemptive signals
        if self.preemptive_engine:
            try:
                key = f"{target.exchange}:{target.symbol}"
                prices = []
                if self.intelligence_network:
                    prices = self.intelligence_network.price_history.get(key, [price])
                
                if hasattr(self.preemptive_engine, 'check_all_signals'):
                    signal = self.preemptive_engine.check_all_signals(
                        symbol=target.symbol,
                        prices=prices,
                        entry_price=target.entry_price,
                        current_price=price,
                        position_pnl_pct=(target.unrealized_pnl / target.entry_value * 100) if target.entry_value > 0 else 0,
                        time_in_position=time.time() - target.entry_time
                    )
                    target.preemptive_signal = signal
            except:
                pass
    
    def check_kill_shot(self, target: SniperTarget, 
                       win_threshold: float = 0.151625) -> Tuple[bool, str, bool]:
        """
        Check if we should take the kill shot.
        
        ZERO LOSS RULE: Only exit on CONFIRMED profit.
        But with Celtic intelligence, we can be smarter about WHEN to exit.
        
        Returns: (should_exit, reason, is_win)
        """
        gross_pnl = target.unrealized_pnl
        
        # RULE 1: ZERO LOSS - Only exit on confirmed profit
        if gross_pnl < win_threshold:
            # Not profitable yet - check if we should hold or if Celtic intel says danger
            
            # Preemptive signal warning (but we still don't exit at a loss!)
            if target.preemptive_signal:
                signal = target.preemptive_signal
                if hasattr(signal, 'signal_type'):
                    if signal.signal_type in ['EXIT', 'URGENT_EXIT'] and gross_pnl > 0:
                        # Only exit on preemptive if we're at least breakeven
                        return (True, f"☘️ PREEMPTIVE EXIT (Celtic Intel): +${gross_pnl:.4f}", True)
            
            # Not yet - keep holding
            return (False, f"🎯 Tracking... ${gross_pnl:.4f} / ${win_threshold:.4f}", False)
        
        # RULE 2: WE HAVE PROFIT - TAKE THE SHOT!
        return (True, f"🇮🇪🎯 CONFIRMED KILL! +${gross_pnl:.4f} >= ${win_threshold:.4f}", True)
    
    def execute_kill(self, target: SniperTarget, actual_pnl: float = None):
        """
        Execute the kill and celebrate victory.
        """
        pnl = actual_pnl if actual_pnl is not None else target.unrealized_pnl
        
        self.kills += 1
        self.total_pnl += pnl
        
        # Remove from targets
        key = f"{target.exchange}:{target.symbol}"
        if key in self.targets:
            del self.targets[key]
        
        # Celebrate!
        celebrate_sniper_kill(pnl, target.symbol, self.kills - 1)
        
        return pnl
    
    def get_status(self) -> Dict[str, Any]:
        """Get sniper status"""
        return {
            'kills': self.kills,
            'total_pnl': self.total_pnl,
            'shots_fired': self.shots_fired,
            'active_targets': len(self.targets),
            'win_rate': self.kills / max(1, self.shots_fired),
            'celtic_systems': {
                'guerrilla': self.intelligence_network is not None,
                'preemptive': self.preemptive_engine is not None,
                'war_room': self.war_room is not None,
                'war_strategy': self.war_strategy is not None,
                'patriots': self.patriot_network is not None
            }
        }
    
    def display_status(self):
        """Display enhanced sniper status"""
        status = self.get_status()
        
        print("\n" + "═" * 70)
        print("🇮🇪☘️ IRA CELTIC SNIPER STATUS ☘️🇮🇪")
        print("═" * 70)
        print(f"   🎯 Kills:           {status['kills']}")
        print(f"   💰 Total P&L:       +${status['total_pnl']:.4f}")
        print(f"   🔫 Shots Fired:     {status['shots_fired']}")
        print(f"   📍 Active Targets:  {status['active_targets']}")
        print(f"   🏆 Win Rate:        {status['win_rate']*100:.1f}%")
        
        print("\n   ☘️ Celtic Intelligence:")
        for system, wired in status['celtic_systems'].items():
            emoji = "✅" if wired else "❌"
            print(f"      {emoji} {system.replace('_', ' ').title()}")
        
        print("═" * 70)
        self._print_celtic_wisdom()
        print("═" * 70 + "\n")


# Global sniper instance for easy import
IRA_SNIPER_MODE = None

def get_celtic_sniper(dry_run: bool = True) -> IraCelticSniper:
    """Get or create the global Celtic Sniper instance"""
    global IRA_SNIPER_MODE
    if IRA_SNIPER_MODE is None:
        IRA_SNIPER_MODE = IraCelticSniper(dry_run=dry_run)
    return IRA_SNIPER_MODE


# =============================================================================
# MAIN - TEST SNIPER CONFIG & CELTIC ENHANCEMENT
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════════════╗
║                                                                          ║
║   🇮🇪🎯 IRA SNIPER MODE - CELTIC ENHANCED 🎯🇮🇪                          ║
║                                                                          ║
║   "We have been afraid for too long. This ends now."                    ║
║   "Now with Celtic Warfare Intelligence - Strike before they react."    ║
║                                                                          ║
╚══════════════════════════════════════════════════════════════════════════╝
    """)
    
    print("=" * 70)
    print("🎯 SNIPER CONFIGURATION")
    print("=" * 70)
    
    config = get_sniper_config()
    
    for key, value in config.items():
        print(f"   {key:25s}: {value}")
    
    print()
    print("=" * 70)
    print("☘️ CELTIC WARFARE SYSTEMS STATUS")
    print("=" * 70)
    print(f"   🧠 Guerrilla Engine:    {'✅ AVAILABLE' if GUERRILLA_WIRED else '❌ NOT LOADED'}")
    print(f"   ⚡ Preemptive Strike:   {'✅ AVAILABLE' if PREEMPTIVE_WIRED else '❌ NOT LOADED'}")
    print(f"   🌐 Multi-Battlefront:   {'✅ AVAILABLE' if COORDINATOR_WIRED else '❌ NOT LOADED'}")
    print(f"   ⚔️ War Strategy:        {'✅ AVAILABLE' if WAR_STRATEGY_WIRED else '❌ NOT LOADED'}")
    print(f"   ☘️ Patriot Network:     {'✅ AVAILABLE' if PATRIOTS_WIRED else '❌ NOT LOADED'}")
    
    print()
    print("=" * 70)
    print("🧪 TEST SNIPER EXITS")
    print("=" * 70)
    
    # Test scenarios
    test_cases = [
        (0.05, 0.04, -0.02, 0, "Penny profit on first cycle"),
        (0.03, 0.04, -0.02, 0, "Not quite there yet"),
        (-0.025, 0.04, -0.02, 2, "Stop loss triggered (IGNORED - we hold!)"),
        (0.041, 0.04, -0.02, 1, "Just over threshold"),
    ]
    
    for gross_pnl, win, stop, cycles, scenario in test_cases:
        should_exit, reason, is_win = check_sniper_exit(gross_pnl, win, stop, cycles)
        status = "✅ EXIT" if should_exit else "⏳ HOLD"
        win_status = "WIN" if is_win else "LOSS" if should_exit else "-"
        print(f"\n   📊 Scenario: {scenario}")
        print(f"      Gross P&L: ${gross_pnl:.3f} | {status} | {win_status}")
        print(f"      Reason: {reason}")
    
    print()
    print("=" * 70)
    print("☘️ TESTING CELTIC ENHANCED SNIPER")
    print("=" * 70)
    
    # Test the Celtic sniper
    sniper = IraCelticSniper(dry_run=True)
    
    # Acquire some test targets
    test_targets = [
        ('BTCUSDC', 'binance', 104500.0),
        ('ETHGBP', 'kraken', 3200.0),
        ('SOLUSDT', 'binance', 220.0),
    ]
    
    print("\n📍 Acquiring test targets...")
    for symbol, exchange, price in test_targets:
        target = sniper.acquire_target(symbol, exchange, price)
        
        # Simulate price movement
        import random
        for _ in range(3):
            movement = random.uniform(-0.002, 0.02) * price
            new_price = price + movement
            sniper.update_target_intelligence(target, new_price)
        
        # Check kill shot
        should_exit, reason, is_win = sniper.check_kill_shot(target)
        print(f"      🔫 Kill shot check: {reason}")
        
        if should_exit and is_win:
            sniper.execute_kill(target)
    
    # Display final status
    sniper.display_status()
    
    print("=" * 70)
    print("🇮🇪 THE CELTIC SNIPER IS READY. ZERO LOSSES. MAXIMUM PRECISION. 🇮🇪")
    print("=" * 70)
    print()
