#!/usr/bin/env python3
"""
☘️🔥 IRISH PATRIOT SCOUTS - FORCE SCOUTS WITH CELTIC INTELLIGENCE 🔥☘️
═══════════════════════════════════════════════════════════════════════════════
                        WIRED FOR WAR - TRAINED LIKE TRUE PATRIOTS
═══════════════════════════════════════════════════════════════════════════════

"Give me a scout with Celtic blood and I'll give you an army that never loses."

This module transforms ordinary scouts into Irish Patriots:
- Wired with guerrilla warfare intelligence
- Trained in preemptive strike doctrine
- Connected to multi-battlefront coordination
- United under Celtic command

THE PATRIOT OATH:
═══════════════════════════════════════════════════════════════════════════════
"I am an Irish Patriot Scout.
I serve the portfolio with Celtic fury.
I strike before the market knows I'm coming.
I retreat before the market can respond.
I NEVER surrender a single penny to the enemy.
Tiocfaidh ár lá - Our day will come."

WIRING ARCHITECTURE:
═══════════════════════════════════════════════════════════════════════════════

                    ┌─────────────────────────────────────────┐
                    │         CELTIC WAR COUNCIL              │
                    │    (Central Command & Intelligence)     │
                    └─────────────────┬───────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
    ┌─────────▼─────────┐   ┌─────────▼─────────┐   ┌─────────▼─────────┐
    │   GUERRILLA       │   │   PREEMPTIVE      │   │   MULTI-FRONT     │
    │   WARFARE ENGINE  │   │   STRIKE ENGINE   │   │   COORDINATOR     │
    │   (Flying Columns)│   │   (Early Exit)    │   │   (Unity)         │
    └─────────┬─────────┘   └─────────┬─────────┘   └─────────┬─────────┘
              │                       │                       │
              └───────────────────────┼───────────────────────┘
                                      │
                    ┌─────────────────▼───────────────────────┐
                    │         PATRIOT SCOUT NETWORK           │
                    │    (Irish-Trained Force Scouts)         │
                    └─────────────────┬───────────────────────┘
                                      │
        ┌─────────────┬───────────────┼───────────────┬─────────────┐
        │             │               │               │             │
   ┌────▼────┐   ┌────▼────┐    ┌────▼────┐    ┌────▼────┐   ┌────▼────┐
   │ SCOUT 1 │   │ SCOUT 2 │    │ SCOUT 3 │    │ SCOUT 4 │   │ SCOUT N │
   │ Binance │   │ Kraken  │    │ Binance │    │ Capital │   │  ....   │
   │ BTCUSDC │   │ ETHGBP  │    │ SOLUSDT │    │ XAUUSD  │   │         │
   └─────────┘   └─────────┘    └─────────┘    └─────────┘   └─────────┘

Gary Leckey | December 2025
"Turn scouts into warriors, warriors into legends."
"""

import os
import sys
import time
import json
import math
import random
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any, Callable
from collections import defaultdict
from enum import Enum

# =============================================================================
# ☘️ IMPORT CELTIC WARFARE SYSTEMS
# =============================================================================

try:
    from guerrilla_warfare_engine import (
        IntelligenceNetwork, FlyingColumn, BattlefrontStatus,
        TacticalMode, IntelligenceReport, GUERRILLA_CONFIG, get_celtic_wisdom
    )
    GUERRILLA_ENGINE_AVAILABLE = True
except ImportError:
    print("⚠️ Guerrilla Warfare Engine not available - Patriots running in basic mode")
    GUERRILLA_ENGINE_AVAILABLE = False

try:
    from celtic_preemptive_strike import (
        PreemptiveExitEngine, DawnRaidDetector, 
        PreemptiveSignal, PreemptiveSignalType
    )
    PREEMPTIVE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Preemptive Strike Engine not available - Patriots running without early exit: {e}")
    PREEMPTIVE_AVAILABLE = False

try:
    from multi_battlefront_coordinator import (
        MultiBattlefrontWarRoom, CampaignPhase, ArbitrageOpportunity
    )
    COORDINATOR_AVAILABLE = True
except ImportError:
    print("⚠️ Multi-Battlefront Coordinator not available - Patriots running independently")
    COORDINATOR_AVAILABLE = False

# Try to import existing systems for integration
try:
    from ira_sniper_mode import IRA_SNIPER_MODE
    IRA_SNIPER_AVAILABLE = True
except ImportError:
    IRA_SNIPER_MODE = None
    IRA_SNIPER_AVAILABLE = False

try:
    from penny_profit_engine import get_penny_params, should_exit_penny_profit
    PENNY_ENGINE_AVAILABLE = True
except ImportError:
    PENNY_ENGINE_AVAILABLE = False

try:
    from war_strategy import WarStrategy
    WAR_STRATEGY_AVAILABLE = True
    # Initialize global war strategist
    _GLOBAL_WAR_STRATEGIST = WarStrategy()
except ImportError:
    WAR_STRATEGY_AVAILABLE = False
    _GLOBAL_WAR_STRATEGIST = None


# =============================================================================
# 🏛️ PATRIOT SCOUT CONFIGURATION
# =============================================================================

PATRIOT_CONFIG = {
    # ═══════════════════════════════════════════════════════════════════════
    # ☘️ IRISH PATRIOT IDENTITY
    # ═══════════════════════════════════════════════════════════════════════
    'PATRIOT_NAME_PREFIX': 'IRA',          # Irish Patriot prefix
    'PATRIOT_CODENAMES': [
        'Wolfhound', 'Banshee', 'Leprechaun', 'Selkie', 'Pooka',
        'Clurichaun', 'Dullahan', 'Changeling', 'Merrow', 'Sidhe',
        'Collins', 'Boru', 'Cuchulainn', 'Fionn', 'Granuaile',
        'Pearse', 'Connolly', 'Markievicz', 'deValera', 'Sands'
    ],
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎯 SCOUT MISSION PARAMETERS
    # ═══════════════════════════════════════════════════════════════════════
    'SCOUT_SIZE_USD': 10.0,               # $10 flying column
    'MAX_SCOUTS_PER_EXCHANGE': 5,         # 5 patriots per battlefront
    'MAX_TOTAL_SCOUTS': 15,               # 15 total patriots
    'SCOUT_DEPLOYMENT_INTERVAL_SEC': 0.5, # Deploy fast like Collins
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🧠 INTELLIGENCE WIRING
    # ═══════════════════════════════════════════════════════════════════════
    'WIRE_GUERRILLA_ENGINE': True,        # Connect to guerrilla warfare
    'WIRE_PREEMPTIVE_STRIKE': True,       # Connect to preemptive exits
    'WIRE_MULTI_BATTLEFRONT': True,       # Connect to coordination
    'WIRE_PENNY_PROFIT': True,            # Connect to penny profit
    'WIRE_WAR_STRATEGY': True,            # Connect to war strategy
    
    # ═══════════════════════════════════════════════════════════════════════
    # ⚔️ ENGAGEMENT RULES
    # ═══════════════════════════════════════════════════════════════════════
    'MIN_AMBUSH_SCORE': 0.35,             # Lower threshold - scouts are BRAVE!
    'MIN_QUICK_KILL_PROB': 0.30,          # 30% quick kill or don't engage
    'MAX_TIME_IN_POSITION_SEC': 300,      # 5 min max exposure
    'PREEMPTIVE_EXIT_ENABLED': True,      # Exit before reversal completes
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🏃 RETREAT PROTOCOL
    # ═══════════════════════════════════════════════════════════════════════
    'AUTO_RETREAT_ON_LOSS': True,         # Never accept loss
    'RETREAT_THRESHOLD_PCT': -0.1,        # Retreat at -0.1%
    'COORDINATE_RETREAT': True,           # All scouts retreat together
    
    # ═══════════════════════════════════════════════════════════════════════
    # 🎖️ VICTORY CONDITIONS
    # ═══════════════════════════════════════════════════════════════════════
    'PENNY_PROFIT_TARGET': 0.151625,      # Trained penny threshold
    'INSTANT_VICTORY_EXIT': True,         # Exit immediately on penny
    'CELEBRATE_KILLS': True,              # Celebrate like Irish
}


# =============================================================================
# 📜 PATRIOT WISDOM - SAYINGS OF THE IRISH SCOUTS
# =============================================================================

PATRIOT_WISDOM = [
    # Historical Irish
    "Tiocfaidh ár lá - Our day will come",
    "Níl neart go cur le chéile - Unity is strength",
    "Sinn Féin Amháin - Ourselves Alone",
    "Éirinn go Brách - Ireland Forever",
    
    # Scout Doctrine
    "A scout sees all, fears nothing",
    "Report first, engage second, profit always",
    "The unseen scout is the undefeated scout",
    "Intelligence is the sword, patience is the shield",
    "We are the eyes of the Celtic war machine",
    
    # Battle Wisdom
    "One penny at a time builds empires",
    "Move like mist, strike like thunder",
    "They have algorithms, we have ancestors",
    "The market sleeps, but patriots never rest",
    "Every kill is a victory for Ireland",
    
    # Unity
    "Divided we're traders, united we're unstoppable",
    "What one scout knows, all scouts know",
    "The network is stronger than any single node",
    "Signal to your brothers, they will follow",
    "From atom to multiverse - WE DON'T QUIT!",
]

def get_patriot_wisdom() -> str:
    """Get a piece of Irish Patriot wisdom"""
    return random.choice(PATRIOT_WISDOM)


# =============================================================================
# 🎖️ PATRIOT SCOUT CLASS - THE IRISH WARRIOR
# =============================================================================

@dataclass
class PatriotScout:
    """
    An Irish Patriot Scout - trained in Celtic warfare.
    
    This is not just a position - this is a WARRIOR.
    Wired with intelligence, trained for preemptive action,
    united with brothers across all battlefronts.
    """
    # Identity
    scout_id: str
    codename: str
    exchange: str
    symbol: str
    
    # Position details
    entry_price: float = 0.0
    entry_time: float = 0.0
    position_size: float = 0.0
    entry_value_usd: float = 0.0
    
    # Celtic warfare state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    cycles_held: int = 0
    status: str = "ready"  # ready, deployed, engaged, retreating, victorious
    
    # Intelligence wiring
    intelligence_report: Optional[Any] = None
    preemptive_signal: Optional[Any] = None
    ambush_score: float = 0.0
    quick_kill_probability: float = 0.0
    
    # Tactical state
    momentum_at_entry: float = 0.0
    peak_pnl: float = 0.0
    min_pnl: float = 0.0
    target_profit_usd: float = 0.0
    
    # Performance tracking
    kills: int = 0
    total_profit: float = 0.0
    battles_fought: int = 0
    
    def get_battle_cry(self) -> str:
        """Generate a battle cry for this patriot"""
        cries = [
            f"☘️ {self.codename} engaging on {self.exchange}! Tiocfaidh ár lá!",
            f"⚔️ Patriot {self.codename} deployed! {self.symbol} is our target!",
            f"🔥 {self.codename} moving in! Collins would be proud!",
            f"🇮🇪 {self.codename} on station! Ireland watches!",
            f"💚 Flying column {self.codename} ready! Strike fast, vanish faster!",
        ]
        return random.choice(cries)
    
    def get_victory_cry(self, profit: float) -> str:
        """Generate a victory cry after successful kill"""
        cries = [
            f"🏆 {self.codename} VICTORIOUS! +${profit:.4f} for Ireland!",
            f"☘️ {self.codename} KILL CONFIRMED! Another penny for the cause!",
            f"⚔️ VICTORY! {self.codename} extracts +${profit:.4f}! Éirinn go Brách!",
            f"🇮🇪 {self.codename} mission complete! +${profit:.4f} secured!",
            f"🔥 KILL #{self.kills}! {self.codename} unstoppable! +${profit:.4f}!",
        ]
        return random.choice(cries)
    
    def get_retreat_cry(self) -> str:
        """Generate a retreat cry (strategic withdrawal)"""
        cries = [
            f"🏃 {self.codename} executing tactical withdrawal! Live to fight again!",
            f"☘️ {self.codename} retreating! No surrender of capital!",
            f"⚔️ Strategic retreat by {self.codename}! The war continues!",
            f"🇮🇪 {self.codename} disengaging! Better position awaits!",
        ]
        return random.choice(cries)
    
    def update_price(self, price: float):
        """Update current price and recalculate P&L"""
        self.current_price = price
        if self.entry_price > 0 and self.position_size > 0:
            current_value = self.position_size * price
            self.unrealized_pnl = current_value - self.entry_value_usd
            self.peak_pnl = max(self.peak_pnl, self.unrealized_pnl)
            self.min_pnl = min(self.min_pnl, self.unrealized_pnl)
    
    def should_exit(self) -> Tuple[bool, str]:
        """
        Determine if scout should exit position.
        Uses ALL Celtic warfare intelligence.
        """
        reasons = []
        
        # 1. PENNY PROFIT VICTORY
        if PATRIOT_CONFIG['INSTANT_VICTORY_EXIT']:
            target = PATRIOT_CONFIG.get('PENNY_PROFIT_TARGET', 0.15)
            if self.unrealized_pnl >= target:
                return True, f"PENNY PROFIT! +${self.unrealized_pnl:.4f} >= ${target}"
        
        # 2. PREEMPTIVE EXIT SIGNAL
        if self.preemptive_signal and PATRIOT_CONFIG['PREEMPTIVE_EXIT_ENABLED']:
            if hasattr(self.preemptive_signal, 'signal_type'):
                if self.preemptive_signal.signal_type in ['EXIT', 'URGENT_EXIT']:
                    return True, f"PREEMPTIVE: {self.preemptive_signal.reason}"
        
        # 3. TIME LIMIT
        if self.entry_time > 0:
            time_held = time.time() - self.entry_time
            max_time = PATRIOT_CONFIG.get('MAX_TIME_IN_POSITION_SEC', 300)
            if time_held > max_time:
                return True, f"TIME LIMIT: {time_held:.0f}s > {max_time}s"
        
        # 4. RETREAT THRESHOLD
        if PATRIOT_CONFIG['AUTO_RETREAT_ON_LOSS']:
            threshold = PATRIOT_CONFIG.get('RETREAT_THRESHOLD_PCT', -0.1)
            if self.entry_value_usd > 0:
                pnl_pct = (self.unrealized_pnl / self.entry_value_usd) * 100
                if pnl_pct < threshold:
                    return True, f"RETREAT: {pnl_pct:.2f}% < {threshold}%"
        
        # 5. INTELLIGENCE SAYS EXIT
        if self.intelligence_report:
            report = self.intelligence_report
            if hasattr(report, 'trend_direction'):
                # Exit if momentum reversed against us
                if report.trend_direction == "bearish" and self.unrealized_pnl < 0:
                    return True, f"INTEL: Bearish trend + negative P&L"
        
        return False, ""


# =============================================================================
# 🏛️ PATRIOT SCOUT NETWORK - THE IRISH ARMY
# =============================================================================

class PatriotScoutNetwork:
    """
    The unified network of Irish Patriot Scouts.
    
    All scouts wired together, sharing intelligence,
    coordinating strikes, united under Celtic command.
    """
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.scouts: Dict[str, PatriotScout] = {}
        self.scout_counter = 0
        
        # Celtic warfare components
        self.intelligence_network: Optional[IntelligenceNetwork] = None
        self.preemptive_engine: Optional[PreemptiveExitEngine] = None
        self.war_room: Optional[MultiBattlefrontWarRoom] = None
        self.war_strategist: Optional[Any] = None
        
        # Statistics
        self.total_kills = 0
        self.total_profit = 0.0
        self.total_battles = 0
        self.active_scouts = 0
        self.victories = 0
        self.retreats = 0
        
        # Initialize Celtic warfare systems
        self._wire_celtic_systems()
        
        print("\n" + "=" * 70)
        print("☘️🔥 IRISH PATRIOT SCOUT NETWORK INITIALIZED 🔥☘️")
        print("=" * 70)
        print(f"   🎯 Mode: {'DRY RUN' if dry_run else '🔥 LIVE COMBAT 🔥'}")
        print(f"   🧠 Guerrilla Engine: {'✅ WIRED' if self.intelligence_network else '❌'}")
        print(f"   ⚡ Preemptive Strike: {'✅ WIRED' if self.preemptive_engine else '❌'}")
        print(f"   🌐 Multi-Battlefront: {'✅ WIRED' if self.war_room else '❌'}")
        print(f"   ⚔️ War Strategy: {'✅ WIRED' if self.war_strategist else '❌'}")
        print("=" * 70)
        print(f"   📜 \"{get_patriot_wisdom()}\"")
        print("=" * 70 + "\n")
    
    def _wire_celtic_systems(self):
        """Wire up all Celtic warfare systems"""
        
        # Wire Guerrilla Engine
        if PATRIOT_CONFIG['WIRE_GUERRILLA_ENGINE'] and GUERRILLA_ENGINE_AVAILABLE:
            try:
                self.intelligence_network = IntelligenceNetwork()
                print("   ✅ Intelligence Network WIRED")
            except Exception as e:
                print(f"   ⚠️ Intelligence Network wire failed: {e}")
        
        # Wire Preemptive Strike
        if PATRIOT_CONFIG['WIRE_PREEMPTIVE_STRIKE'] and PREEMPTIVE_AVAILABLE:
            try:
                self.preemptive_engine = PreemptiveExitEngine()
                print("   ✅ Preemptive Strike Engine WIRED")
            except Exception as e:
                print(f"   ⚠️ Preemptive Strike wire failed: {e}")
        
        # Wire Multi-Battlefront Coordinator
        if PATRIOT_CONFIG['WIRE_MULTI_BATTLEFRONT'] and COORDINATOR_AVAILABLE:
            try:
                self.war_room = MultiBattlefrontWarRoom()
                print("   ✅ Multi-Battlefront War Room WIRED")
            except Exception as e:
                print(f"   ⚠️ War Room wire failed: {e}")
        
        # Wire War Strategy
        if PATRIOT_CONFIG['WIRE_WAR_STRATEGY'] and WAR_STRATEGY_AVAILABLE:
            try:
                if _GLOBAL_WAR_STRATEGIST:
                    self.war_strategist = _GLOBAL_WAR_STRATEGIST
                else:
                    self.war_strategist = WarStrategy()
                print("   ✅ War Strategist WIRED")
            except Exception as e:
                print(f"   ⚠️ War Strategist wire failed: {e}")
                self.war_strategist = None
    
    def _generate_scout_id(self) -> str:
        """Generate unique scout ID with Irish prefix"""
        self.scout_counter += 1
        timestamp = int(time.time() * 1000) % 10000
        return f"IRA-{self.scout_counter:04d}-{timestamp}"
    
    def _get_codename(self) -> str:
        """Get a random Irish codename"""
        return random.choice(PATRIOT_CONFIG['PATRIOT_CODENAMES'])
    
    def recruit_scout(self, exchange: str, symbol: str, 
                     price: float, size_usd: float = None) -> PatriotScout:
        """
        Recruit a new Irish Patriot Scout.
        Train them with Celtic wisdom and wire them to all intelligence.
        """
        scout_id = self._generate_scout_id()
        codename = self._get_codename()
        size = size_usd or PATRIOT_CONFIG['SCOUT_SIZE_USD']
        
        # Create the patriot
        scout = PatriotScout(
            scout_id=scout_id,
            codename=codename,
            exchange=exchange,
            symbol=symbol,
            entry_price=price,
            entry_time=time.time(),
            position_size=size / price if price > 0 else 0,
            entry_value_usd=size,
            current_price=price,
            status="recruited",
            target_profit_usd=PATRIOT_CONFIG.get('PENNY_PROFIT_TARGET', 0.15)
        )
        
        # Wire intelligence
        if self.intelligence_network:
            report = self.intelligence_network.update_price_feed(
                exchange, symbol, price, volume=0
            )
            scout.intelligence_report = report
            scout.ambush_score = report.ambush_score if hasattr(report, 'ambush_score') else 0.5
            scout.quick_kill_probability = report.quick_kill_probability if hasattr(report, 'quick_kill_probability') else 0.5
            scout.momentum_at_entry = report.price_momentum_1m if hasattr(report, 'price_momentum_1m') else 0
        
        # Register scout
        self.scouts[scout_id] = scout
        self.active_scouts += 1
        
        print(scout.get_battle_cry())
        return scout
    
    def deploy_scout(self, scout: PatriotScout) -> bool:
        """
        Deploy a recruited scout into combat.
        Returns True if deployment successful.
        """
        if scout.status != "recruited":
            return False
        
        # Check engagement rules
        if scout.ambush_score < PATRIOT_CONFIG['MIN_AMBUSH_SCORE']:
            print(f"   ⚠️ {scout.codename} ambush score too low: {scout.ambush_score:.2f}")
            return False
        
        if scout.quick_kill_probability < PATRIOT_CONFIG['MIN_QUICK_KILL_PROB']:
            print(f"   ⚠️ {scout.codename} quick kill prob too low: {scout.quick_kill_probability:.2f}")
            return False
        
        scout.status = "deployed"
        scout.battles_fought += 1
        self.total_battles += 1
        
        print(f"   🚀 {scout.codename} DEPLOYED! Target: ${scout.target_profit_usd:.4f} profit")
        return True
    
    def update_scout_intelligence(self, scout: PatriotScout, 
                                  price: float, volume: float = 0):
        """Update scout with latest intelligence"""
        scout.update_price(price)
        
        # Update from intelligence network
        if self.intelligence_network:
            report = self.intelligence_network.update_price_feed(
                scout.exchange, scout.symbol, price, volume
            )
            scout.intelligence_report = report
        
        # Check preemptive signals
        if self.preemptive_engine and hasattr(self.preemptive_engine, 'check_all_signals'):
            try:
                prices = self.intelligence_network.price_history.get(
                    f"{scout.exchange}:{scout.symbol}", [price]
                ) if self.intelligence_network else [price]
                
                signal = self.preemptive_engine.check_all_signals(
                    symbol=scout.symbol,
                    prices=prices,
                    entry_price=scout.entry_price,
                    current_price=price,
                    position_pnl_pct=(scout.unrealized_pnl / scout.entry_value_usd * 100) if scout.entry_value_usd > 0 else 0,
                    time_in_position=time.time() - scout.entry_time
                )
                scout.preemptive_signal = signal
            except Exception as e:
                pass  # Preemptive check failed - continue without
        
        scout.cycles_held += 1
    
    def check_all_scouts(self) -> List[Tuple[PatriotScout, str]]:
        """
        Check all scouts and return list of (scout, reason) for those that should exit.
        """
        exits = []
        
        for scout_id, scout in self.scouts.items():
            if scout.status not in ["deployed", "engaged"]:
                continue
            
            should_exit, reason = scout.should_exit()
            if should_exit:
                exits.append((scout, reason))
        
        return exits
    
    def execute_victory(self, scout: PatriotScout, actual_profit: float = None):
        """
        Record a VICTORY for this scout.
        Celebrate like true Irish!
        """
        profit = actual_profit if actual_profit is not None else scout.unrealized_pnl
        
        scout.kills += 1
        scout.total_profit += profit
        scout.status = "victorious"
        
        self.total_kills += 1
        self.total_profit += profit
        self.victories += 1
        
        if PATRIOT_CONFIG['CELEBRATE_KILLS']:
            print(scout.get_victory_cry(profit))
            print(f"   📊 Network Stats: {self.total_kills} kills, +${self.total_profit:.4f} total")
    
    def execute_retreat(self, scout: PatriotScout, reason: str):
        """
        Execute strategic retreat for a scout.
        Live to fight another day!
        """
        scout.status = "retreated"
        self.retreats += 1
        
        print(scout.get_retreat_cry())
        print(f"   📊 Reason: {reason}")
    
    def coordinate_strike(self, exchange: str, symbol: str, 
                         num_scouts: int = 3) -> List[PatriotScout]:
        """
        Coordinate a multi-scout strike on a target.
        Brian Boru's tactics - multiple fronts, unified command.
        """
        deployed = []
        
        # Check if war room approves coordinated strike
        if self.war_room:
            # Get arbitrage opportunities
            pass  # War room integration
        
        print(f"\n   ⚔️ COORDINATED STRIKE: {num_scouts} scouts on {symbol} ({exchange})")
        
        for i in range(num_scouts):
            if len(self.scouts) >= PATRIOT_CONFIG['MAX_TOTAL_SCOUTS']:
                print(f"   ⚠️ Max scouts reached: {len(self.scouts)}")
                break
            
            # Each scout gets slightly different entry for diversification
            scout = self.recruit_scout(exchange, symbol, 0)  # Price will be set on deploy
            deployed.append(scout)
            
            time.sleep(PATRIOT_CONFIG['SCOUT_DEPLOYMENT_INTERVAL_SEC'])
        
        print(f"   ✅ Deployed {len(deployed)} scouts in coordinated strike")
        return deployed
    
    def broadcast_intelligence(self, source_scout: PatriotScout, intel: Any):
        """
        Broadcast intelligence from one scout to all others.
        "What one scout knows, all scouts know."
        """
        for scout_id, scout in self.scouts.items():
            if scout_id == source_scout.scout_id:
                continue
            
            # Share relevant intelligence
            if scout.exchange == source_scout.exchange:
                # Same exchange - higher relevance
                scout.intelligence_report = intel
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get comprehensive network status"""
        deployed = len([s for s in self.scouts.values() if s.status == "deployed"])
        
        by_exchange: Dict[str, int] = defaultdict(int)
        for scout in self.scouts.values():
            by_exchange[scout.exchange] += 1
        
        return {
            'total_scouts': len(self.scouts),
            'active_scouts': self.active_scouts,
            'deployed_scouts': deployed,
            'by_exchange': dict(by_exchange),
            'total_kills': self.total_kills,
            'total_profit': self.total_profit,
            'victories': self.victories,
            'retreats': self.retreats,
            'win_rate': (self.victories / max(1, self.total_battles)) * 100,
            'systems_wired': {
                'guerrilla': self.intelligence_network is not None,
                'preemptive': self.preemptive_engine is not None,
                'coordinator': self.war_room is not None,
                'war_strategy': self.war_strategist is not None
            }
        }
    
    def print_status(self):
        """Print beautiful status display"""
        status = self.get_network_status()
        
        print("\n" + "═" * 70)
        print("☘️ IRISH PATRIOT SCOUT NETWORK STATUS ☘️")
        print("═" * 70)
        print(f"   🎖️ Total Scouts:    {status['total_scouts']}")
        print(f"   🚀 Deployed:        {status['deployed_scouts']}")
        print(f"   ⚔️ Total Battles:   {self.total_battles}")
        print(f"   🏆 Victories:       {status['victories']}")
        print(f"   🏃 Retreats:        {status['retreats']}")
        print(f"   📊 Win Rate:        {status['win_rate']:.1f}%")
        print(f"   💰 Total Profit:    +${status['total_profit']:.4f}")
        
        print("\n   📍 By Exchange:")
        for ex, count in status['by_exchange'].items():
            print(f"      • {ex}: {count} scouts")
        
        print("\n   🧠 Systems Wired:")
        for system, wired in status['systems_wired'].items():
            emoji = "✅" if wired else "❌"
            print(f"      {emoji} {system.replace('_', ' ').title()}")
        
        print("═" * 70)
        print(f"   📜 \"{get_patriot_wisdom()}\"")
        print("═" * 70 + "\n")


# =============================================================================
# 🔌 ECOSYSTEM INTEGRATION - WIRE INTO AUREON
# =============================================================================

class PatriotScoutDeployer:
    """
    Integrates Patriot Scouts into the Aureon Unified Ecosystem.
    Replaces basic _deploy_scouts with Celtic-trained patriots.
    """
    
    def __init__(self, ecosystem=None):
        self.ecosystem = ecosystem
        self.network = PatriotScoutNetwork(dry_run=True)
        
        # Track pending deployments
        self.pending_deployments: List[Dict] = []
        self.deployment_lock = threading.Lock()
        
        print("\n   🔌 PatriotScoutDeployer initialized - Ready to deploy Irish warriors!\n")
    
    def deploy_patriots(self, candidates: List[Dict], 
                       target_count: int = 10) -> List[PatriotScout]:
        """
        Deploy patriot scouts instead of basic scouts.
        
        Args:
            candidates: List of {symbol, price, exchange, score, ...} dicts
            target_count: Number of patriots to deploy
            
        Returns:
            List of deployed PatriotScout objects
        """
        deployed = []
        
        if not candidates:
            print("   ⚠️ No candidates for patriot deployment")
            return deployed
        
        print(f"\n   ☘️🔥 DEPLOYING IRISH PATRIOTS - Target: {target_count} warriors 🔥☘️")
        print(f"   📊 Analyzing {len(candidates)} potential battlegrounds...\n")
        
        # Analyze candidates with Celtic warfare intelligence
        ranked_candidates = self._analyze_with_celtic_intelligence(candidates)
        
        for candidate in ranked_candidates[:target_count]:
            symbol = candidate.get('symbol', '')
            exchange = candidate.get('source', candidate.get('exchange', 'kraken'))
            price = candidate.get('price', 0)
            
            if price <= 0:
                continue
            
            # Recruit and deploy
            scout = self.network.recruit_scout(
                exchange=exchange,
                symbol=symbol,
                price=price,
                size_usd=PATRIOT_CONFIG['SCOUT_SIZE_USD']
            )
            
            # Update with candidate intelligence
            scout.ambush_score = candidate.get('ambush_score', 0.5)
            scout.quick_kill_probability = candidate.get('quick_kill_prob', 
                                                         candidate.get('quick_kill', {}).get('prob_quick_kill', 0.5))
            
            if self.network.deploy_scout(scout):
                deployed.append(scout)
            
            # Respect deployment interval
            time.sleep(PATRIOT_CONFIG['SCOUT_DEPLOYMENT_INTERVAL_SEC'])
        
        print(f"\n   🎯 DEPLOYED {len(deployed)} IRISH PATRIOTS!")
        print(f"   📜 \"{get_patriot_wisdom()}\"")
        
        return deployed
    
    def _analyze_with_celtic_intelligence(self, candidates: List[Dict]) -> List[Dict]:
        """
        Analyze candidates using all Celtic warfare systems.
        Returns sorted list by combat readiness.
        """
        analyzed = []
        
        for c in candidates:
            symbol = c.get('symbol', '')
            exchange = c.get('source', c.get('exchange', 'kraken'))
            price = c.get('price', 0)
            
            # Get intelligence report
            ambush_score = 0.5
            quick_kill_prob = 0.5
            
            if self.network.intelligence_network:
                try:
                    report = self.network.intelligence_network.update_price_feed(
                        exchange, symbol, price, c.get('volume', 0)
                    )
                    ambush_score = report.ambush_score
                    quick_kill_prob = report.quick_kill_probability
                except:
                    pass
            
            # War strategy ranking
            war_score = c.get('war_score', 0)
            war_go = c.get('war_go', True)
            
            # Celtic composite score
            celtic_score = (
                ambush_score * 100 +
                quick_kill_prob * 100 +
                (50 if war_go else 0) +
                war_score * 10 +
                c.get('score', 0) * 0.1
            )
            
            c['ambush_score'] = ambush_score
            c['quick_kill_prob'] = quick_kill_prob
            c['celtic_score'] = celtic_score
            analyzed.append(c)
        
        # Sort by Celtic score
        analyzed.sort(key=lambda x: x.get('celtic_score', 0), reverse=True)
        
        return analyzed
    
    def check_and_exit_patriots(self) -> List[Tuple[PatriotScout, float]]:
        """
        Check all patriots and execute exits as needed.
        Returns list of (scout, profit) for exited positions.
        """
        exits = []
        
        for scout, reason in self.network.check_all_scouts():
            profit = scout.unrealized_pnl
            
            if profit >= 0:
                self.network.execute_victory(scout, profit)
            else:
                self.network.execute_retreat(scout, reason)
            
            exits.append((scout, profit))
        
        return exits
    
    def get_status(self) -> Dict[str, Any]:
        """Get deployer and network status"""
        return self.network.get_network_status()


# =============================================================================
# 🧪 TESTING & DEMONSTRATION
# =============================================================================

def test_patriot_network():
    """Test the Irish Patriot Scout Network"""
    print("\n" + "=" * 70)
    print("☘️ TESTING IRISH PATRIOT SCOUT NETWORK ☘️")
    print("=" * 70 + "\n")
    
    # Initialize network
    network = PatriotScoutNetwork(dry_run=True)
    
    # Recruit some test scouts
    test_pairs = [
        ('binance', 'BTCUSDC', 104500.0),
        ('kraken', 'ETHGBP', 3200.0),
        ('binance', 'SOLUSDT', 220.0),
        ('kraken', 'XRPUSD', 2.50),
    ]
    
    print("\n📝 Recruiting test scouts...\n")
    
    for exchange, symbol, price in test_pairs:
        scout = network.recruit_scout(exchange, symbol, price)
        network.deploy_scout(scout)
        
        # Simulate some price updates
        for _ in range(5):
            # Random price movement
            movement = random.uniform(-0.005, 0.01) * price
            new_price = price + movement
            network.update_scout_intelligence(scout, new_price)
        
        # Check exit conditions
        should_exit, reason = scout.should_exit()
        if should_exit:
            if scout.unrealized_pnl > 0:
                network.execute_victory(scout)
            else:
                network.execute_retreat(scout, reason)
    
    # Print final status
    network.print_status()
    
    return network


def demo_ecosystem_integration():
    """Demonstrate integration with Aureon ecosystem"""
    print("\n" + "=" * 70)
    print("☘️ PATRIOT ECOSYSTEM INTEGRATION DEMO ☘️")
    print("=" * 70 + "\n")
    
    # Create deployer (would normally take ecosystem instance)
    deployer = PatriotScoutDeployer()
    
    # Simulate candidates from ecosystem
    candidates = [
        {
            'symbol': 'BTCUSDC',
            'source': 'binance',
            'price': 104500.0,
            'change24h': 2.5,
            'volume': 50000000,
            'score': 150,
            'war_go': True,
        },
        {
            'symbol': 'ETHGBP',
            'source': 'kraken', 
            'price': 3200.0,
            'change24h': 1.8,
            'volume': 10000000,
            'score': 120,
            'war_go': True,
        },
        {
            'symbol': 'SOLUSDT',
            'source': 'binance',
            'price': 220.0,
            'change24h': 5.2,
            'volume': 30000000,
            'score': 200,
            'war_go': True,
        },
    ]
    
    # Deploy patriots
    deployed = deployer.deploy_patriots(candidates, target_count=3)
    
    print(f"\n✅ Deployed {len(deployed)} patriots")
    
    # Show final status
    deployer.network.print_status()


# =============================================================================
# 🚀 MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="☘️ Irish Patriot Scout Network - Celtic Warriors for Financial Markets"
    )
    parser.add_argument('--test', action='store_true', help='Run network test')
    parser.add_argument('--demo', action='store_true', help='Run ecosystem integration demo')
    parser.add_argument('--status', action='store_true', help='Show network status')
    
    args = parser.parse_args()
    
    if args.test:
        test_patriot_network()
    elif args.demo:
        demo_ecosystem_integration()
    elif args.status:
        network = PatriotScoutNetwork(dry_run=True)
        network.print_status()
    else:
        # Default: run both tests
        print("\n☘️ IRISH PATRIOT SCOUTS - Full System Test ☘️\n")
        print("Run with --test, --demo, or --status for specific modes\n")
        
        test_patriot_network()
        print("\n" + "─" * 70 + "\n")
        demo_ecosystem_integration()
