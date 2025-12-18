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
