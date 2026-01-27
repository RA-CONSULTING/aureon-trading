#!/usr/bin/env python3
"""
🏷️🐋 AUREON COMPLETE WHALE PROFILER SYSTEM 🐋🏷️
===================================================

BAG, TAG, AND TRACK every detected bot, whale, and firm.

FULL PROFILE INCLUDES:
- Firm Attribution (Robin → Singapore Office → Shark Class)
- Prey/Targets (What they're hunting: ETH, retail movements, etc.)
- 24-Hour Activity (Bought $X, sold $Y, manipulated $Z)
- Current Position (Where are they NOW?)
- Pattern Classification (Accumulation, Spoofing, HFT, etc.)
- Sonar Tracking (Real-time movement monitoring)

Example Profile:
┌─────────────────────────────────────────────────────────┐
│ 🦈 WHALE PROFILE #00237                                 │
├─────────────────────────────────────────────────────────┤
│ Name: "Singapore Shark"                                 │
│ Firm: Jump Trading (Singapore Office)                   │
│ Class: MEGALODON (>$10M positions)                      │
│ Strategy: HFT_ALGO                                      │
│                                                         │
│ 📊 24-Hour Activity:                                    │
│ ├─ Bought: $2,347,892 ETH                              │
│ ├─ Sold: $1,823,445 BTC                                │
│ ├─ Net PnL: +$524,447                                  │
│ └─ Manipulations: 3 spoof attempts detected            │
│                                                         │
│ 🎯 Current Targets:                                     │
│ ├─ Primary: ETHUSDT (accumulating)                     │
│ ├─ Secondary: SOLUSDT (watching)                       │
│ └─ Retail Hunt: Small wallets on Binance               │
│                                                         │
│ 📍 Current Status:                                      │
│ └─ ACTIVE | Last seen: 2 min ago | Confidence: 94%     │
└─────────────────────────────────────────────────────────┘

Gary Leckey | January 2026 | Bag 'Em, Tag 'Em, Track 'Em
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import math
import time
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, deque
from pathlib import Path

# UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    try:
        import io
        def _is_utf8_wrapper(stream):
            return (isinstance(stream, io.TextIOWrapper) and 
                    hasattr(stream, 'encoding') and stream.encoding and
                    stream.encoding.lower().replace('-', '') == 'utf8')
        if hasattr(sys.stdout, 'buffer') and not _is_utf8_wrapper(sys.stdout):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
        if hasattr(sys.stderr, 'buffer') and not _is_utf8_wrapper(sys.stderr):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    except Exception:
        pass

logger = logging.getLogger(__name__)

PHI = (1 + math.sqrt(5)) / 2  # 1.618


# ═══════════════════════════════════════════════════════════════════════════════
# WHALE CLASSIFICATION SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class WhaleClass:
    """Whale size classification based on position size."""
    MINNOW = "MINNOW"           # < $10K
    SHARK = "SHARK"             # $10K - $100K
    WHALE = "WHALE"             # $100K - $1M
    MEGALODON = "MEGALODON"     # $1M - $10M
    LEVIATHAN = "LEVIATHAN"     # > $10M
    
    @staticmethod
    def classify(position_usd: float) -> str:
        """Classify whale by position size."""
        if position_usd < 10_000:
            return WhaleClass.MINNOW
        elif position_usd < 100_000:
            return WhaleClass.SHARK
        elif position_usd < 1_000_000:
            return WhaleClass.WHALE
        elif position_usd < 10_000_000:
            return WhaleClass.MEGALODON
        else:
            return WhaleClass.LEVIATHAN


class StrategyType:
    """Trading strategy classifications."""
    ACCUMULATION = "ACCUMULATION"       # Slow buying
    DISTRIBUTION = "DISTRIBUTION"       # Slow selling
    HFT_ALGO = "HFT_ALGO"              # High-frequency trading
    MM_SPOOF = "MM_SPOOF"              # Market maker spoofing
    WASH_TRADE = "WASH_TRADE"          # Self-trading
    PUMP_DUMP = "PUMP_DUMP"            # Pump and dump
    ARBITRAGE = "ARBITRAGE"            # Cross-exchange arb
    ICEBERG = "ICEBERG"                # Hidden orders
    FRONT_RUN = "FRONT_RUN"            # Front-running
    RETAIL_HUNT = "RETAIL_HUNT"        # Hunting stop losses


# ═══════════════════════════════════════════════════════════════════════════════
# TRADING FIRM DATABASE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class FirmOffice:
    """Trading firm office location."""
    city: str
    country: str
    timezone: str
    active_hours: Tuple[int, int]  # Local trading hours (start, end)
    

@dataclass
class TradingFirm:
    """Complete trading firm profile."""
    name: str
    hq_location: str
    offices: List[FirmOffice]
    typical_strategies: List[str]
    typical_symbols: List[str]
    confidence_threshold: float  # How confident we are in attribution
    

GLOBAL_TRADING_FIRMS = {
    "citadel": TradingFirm(
        name="Citadel Securities",
        hq_location="Chicago, USA",
        offices=[
            FirmOffice("Chicago", "USA", "America/Chicago", (8, 17)),
            FirmOffice("New York", "USA", "America/New_York", (9, 18)),
            FirmOffice("London", "UK", "Europe/London", (8, 17)),
        ],
        typical_strategies=["HFT_ALGO", "MM_SPOOF", "ARBITRAGE"],
        typical_symbols=["BTCUSDT", "ETHUSDT", "BTCUSD"],
        confidence_threshold=0.85
    ),
    "jump_trading": TradingFirm(
        name="Jump Trading",
        hq_location="Chicago, USA",
        offices=[
            FirmOffice("Chicago", "USA", "America/Chicago", (8, 17)),
            FirmOffice("Singapore", "Singapore", "Asia/Singapore", (9, 18)),
            FirmOffice("London", "UK", "Europe/London", (8, 17)),
        ],
        typical_strategies=["HFT_ALGO", "FRONT_RUN"],
        typical_symbols=["ETHUSDT", "SOLUSDT", "BTCUSDT"],
        confidence_threshold=0.82
    ),
    "jane_street": TradingFirm(
        name="Jane Street",
        hq_location="New York, USA",
        offices=[
            FirmOffice("New York", "USA", "America/New_York", (9, 18)),
            FirmOffice("London", "UK", "Europe/London", (8, 17)),
            FirmOffice("Hong Kong", "Hong Kong", "Asia/Hong_Kong", (9, 18)),
        ],
        typical_strategies=["MM_SPOOF", "ARBITRAGE"],
        typical_symbols=["BTCUSDT", "ETHUSDT"],
        confidence_threshold=0.88
    ),
    "wintermute": TradingFirm(
        name="Wintermute",
        hq_location="London, UK",
        offices=[
            FirmOffice("London", "UK", "Europe/London", (8, 17)),
            FirmOffice("Singapore", "Singapore", "Asia/Singapore", (9, 18)),
        ],
        typical_strategies=["MM_SPOOF", "ICEBERG", "RETAIL_HUNT"],
        typical_symbols=["ETHUSDT", "SOLUSDT", "ADAUSDT"],
        confidence_threshold=0.79
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# WHALE ACTIVITY TRACKING
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class Activity24Hour:
    """24-hour activity summary."""
    bought_usd: float = 0.0
    sold_usd: float = 0.0
    net_pnl: float = 0.0
    manipulations_detected: int = 0
    spoofs_detected: int = 0
    retail_hunts: int = 0
    symbols_traded: List[str] = field(default_factory=list)
    

@dataclass
class CurrentTarget:
    """Current trading target."""
    symbol: str
    action: str  # "accumulating", "distributing", "watching", "hunting"
    confidence: float
    volume_usd: float
    

@dataclass
class WhaleProfile:
    """
    🏷️ COMPLETE WHALE PROFILE 🏷️
    
    Everything we know about a specific whale/bot/firm.
    """
    # Identity
    profile_id: str
    nickname: str  # e.g., "Singapore Shark"
    firm: Optional[str] = None
    office_location: Optional[str] = None
    
    # Classification
    whale_class: str = WhaleClass.MINNOW
    strategy: str = StrategyType.ACCUMULATION
    
    # 24-Hour Activity
    activity_24h: Activity24Hour = field(default_factory=Activity24Hour)
    
    # Current Targets
    current_targets: List[CurrentTarget] = field(default_factory=list)
    
    # Tracking
    first_seen: float = field(default_factory=time.time)
    last_seen: float = field(default_factory=time.time)
    total_sightings: int = 0
    confidence: float = 0.0  # How confident are we in this profile?
    
    # Patterns
    typical_frequency: float = 0.0  # Hz
    typical_activity_count: int = 0
    hunt_patterns: List[str] = field(default_factory=list)
    
    # Status
    status: str = "ACTIVE"  # ACTIVE, DORMANT, DISAPPEARED
    

# ═══════════════════════════════════════════════════════════════════════════════
# WHALE PROFILER SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class WhaleProfilerSystem:
    """
    🏷️ BAG, TAG, AND TRACK SYSTEM 🏷️
    
    Maintains complete profiles of all detected whales/bots/firms.
    """
    
    def __init__(self, persistence_file: str = "whale_profiles.json"):
        self.profiles: Dict[str, WhaleProfile] = {}
        self.persistence_file = Path(persistence_file)
        self.next_profile_id = 1
        
        # Load existing profiles
        self.load_profiles()
        
        logger.info(f"🏷️ Whale Profiler System initialized - {len(self.profiles)} profiles loaded")
        
    def create_profile(
        self,
        symbol: str,
        whale_class: str,
        strategy: str,
        frequency: float,
        activities: int,
        firm: Optional[str] = None,
        office: Optional[str] = None
    ) -> WhaleProfile:
        """
        🏷️ CREATE NEW WHALE PROFILE 🏷️
        
        Bag and tag a newly detected whale.
        """
        profile_id = f"WH{self.next_profile_id:05d}"
        self.next_profile_id += 1
        
        # Generate nickname
        nickname = self._generate_nickname(firm, office, whale_class, strategy)
        
        profile = WhaleProfile(
            profile_id=profile_id,
            nickname=nickname,
            firm=firm,
            office_location=office,
            whale_class=whale_class,
            strategy=strategy,
            typical_frequency=frequency,
            typical_activity_count=activities,
            confidence=0.75,  # Initial confidence
            total_sightings=1
        )
        
        # Add initial target
        profile.current_targets.append(CurrentTarget(
            symbol=symbol,
            action="watching",
            confidence=0.75,
            volume_usd=0.0
        ))
        
        self.profiles[profile_id] = profile
        
        logger.info(f"🏷️ NEW PROFILE: {nickname} ({profile_id}) - {strategy} on {symbol}")
        
        return profile
        
    def update_profile(
        self,
        profile_id: str,
        symbol: str,
        action: str,
        volume_usd: float,
        **kwargs
    ) -> None:
        """
        📊 UPDATE EXISTING PROFILE 📊
        
        Track new activity for an existing whale.
        """
        if profile_id not in self.profiles:
            logger.warning(f"Profile {profile_id} not found")
            return
            
        profile = self.profiles[profile_id]
        profile.last_seen = time.time()
        profile.total_sightings += 1
        
        # Update 24-hour activity
        if action == "buy":
            profile.activity_24h.bought_usd += volume_usd
        elif action == "sell":
            profile.activity_24h.sold_usd += volume_usd
            
        profile.activity_24h.net_pnl = (
            profile.activity_24h.sold_usd - profile.activity_24h.bought_usd
        )
        
        # Update symbols traded
        if symbol not in profile.activity_24h.symbols_traded:
            profile.activity_24h.symbols_traded.append(symbol)
            
        # Update current targets
        target_found = False
        for target in profile.current_targets:
            if target.symbol == symbol:
                target.action = action
                target.volume_usd += volume_usd
                target.confidence = min(1.0, target.confidence + 0.05)
                target_found = True
                break
                
        if not target_found:
            profile.current_targets.append(CurrentTarget(
                symbol=symbol,
                action=action,
                confidence=0.7,
                volume_usd=volume_usd
            ))
            
        # Increase confidence
        profile.confidence = min(1.0, profile.confidence + 0.02)
        
    def find_or_create_profile(
        self,
        symbol: str,
        whale_class: str,
        strategy: str,
        frequency: float,
        activities: int,
        firm: Optional[str] = None
    ) -> WhaleProfile:
        """
        🔍 FIND EXISTING OR CREATE NEW PROFILE 🔍
        
        Smart matching to avoid duplicate profiles.
        """
        # Try to find matching profile
        for profile in self.profiles.values():
            if (profile.strategy == strategy and
                abs(profile.typical_frequency - frequency) < 0.5 and
                profile.firm == firm):
                # Found match!
                return profile
                
        # No match found, create new
        return self.create_profile(
            symbol, whale_class, strategy, frequency, activities, firm
        )
        
    def get_active_profiles(self, min_confidence: float = 0.6) -> List[WhaleProfile]:
        """Get all active profiles above confidence threshold."""
        now = time.time()
        active = []
        
        for profile in self.profiles.values():
            # Mark as dormant if not seen in 1 hour
            if now - profile.last_seen > 3600:
                profile.status = "DORMANT"
            elif now - profile.last_seen > 86400:  # 24 hours
                profile.status = "DISAPPEARED"
            else:
                profile.status = "ACTIVE"
                
            if profile.status == "ACTIVE" and profile.confidence >= min_confidence:
                active.append(profile)
                
        return active
        
    def get_profiles_by_firm(self, firm: str) -> List[WhaleProfile]:
        """Get all profiles attributed to a specific firm."""
        return [p for p in self.profiles.values() if p.firm == firm]
        
    def get_profiles_by_symbol(self, symbol: str) -> List[WhaleProfile]:
        """Get all profiles currently trading a symbol."""
        result = []
        for profile in self.profiles.values():
            for target in profile.current_targets:
                if target.symbol == symbol:
                    result.append(profile)
                    break
        return result
        
    def format_profile_display(self, profile: WhaleProfile) -> str:
        """
        📋 FORMAT PROFILE FOR DISPLAY 📋
        
        Beautiful ASCII art profile display.
        """
        lines = []
        lines.append("┌" + "─" * 60 + "┐")
        lines.append(f"│ 🦈 WHALE PROFILE {profile.profile_id:>44} │")
        lines.append("├" + "─" * 60 + "┤")
        lines.append(f"│ Name: {profile.nickname:<52} │")
        
        if profile.firm:
            lines.append(f"│ Firm: {profile.firm:<52} │")
        if profile.office_location:
            lines.append(f"│ Office: {profile.office_location:<50} │")
            
        lines.append(f"│ Class: {profile.whale_class:<51} │")
        lines.append(f"│ Strategy: {profile.strategy:<48} │")
        lines.append("│" + " " * 60 + "│")
        
        # 24-hour activity
        lines.append("│ 📊 24-Hour Activity:" + " " * 39 + "│")
        lines.append(f"│ ├─ Bought: ${profile.activity_24h.bought_usd:,.0f}" + " " * (48 - len(f"{profile.activity_24h.bought_usd:,.0f}")) + "│")
        lines.append(f"│ ├─ Sold: ${profile.activity_24h.sold_usd:,.0f}" + " " * (50 - len(f"{profile.activity_24h.sold_usd:,.0f}")) + "│")
        lines.append(f"│ ├─ Net PnL: ${profile.activity_24h.net_pnl:+,.0f}" + " " * (46 - len(f"{profile.activity_24h.net_pnl:+,.0f}")) + "│")
        
        if profile.activity_24h.manipulations_detected > 0:
            lines.append(f"│ └─ Manipulations: {profile.activity_24h.manipulations_detected} detected" + " " * (32 - len(str(profile.activity_24h.manipulations_detected))) + "│")
        
        lines.append("│" + " " * 60 + "│")
        
        # Current targets
        if profile.current_targets:
            lines.append("│ 🎯 Current Targets:" + " " * 40 + "│")
            for i, target in enumerate(profile.current_targets[:3]):  # Show top 3
                prefix = "├─" if i < len(profile.current_targets) - 1 else "└─"
                lines.append(f"│ {prefix} {target.symbol}: {target.action} (${target.volume_usd:,.0f})" + " " * (47 - len(target.symbol) - len(target.action) - len(f"{target.volume_usd:,.0f}")) + "│")
        
        lines.append("│" + " " * 60 + "│")
        
        # Status
        time_since = int(time.time() - profile.last_seen)
        if time_since < 60:
            time_str = f"{time_since}s ago"
        elif time_since < 3600:
            time_str = f"{time_since//60}m ago"
        else:
            time_str = f"{time_since//3600}h ago"
            
        lines.append(f"│ 📍 Status: {profile.status} | Last seen: {time_str}" + " " * (29 - len(profile.status) - len(time_str)) + "│")
        lines.append(f"│    Confidence: {profile.confidence:.0%} | Sightings: {profile.total_sightings}" + " " * (32 - len(str(profile.total_sightings))) + "│")
        lines.append("└" + "─" * 60 + "┘")
        
        return "\n".join(lines)
        
    def _generate_nickname(
        self,
        firm: Optional[str],
        office: Optional[str],
        whale_class: str,
        strategy: str
    ) -> str:
        """Generate a memorable nickname for the whale."""
        parts = []
        
        if office:
            parts.append(office.split(',')[0])  # City name
        elif firm:
            parts.append(firm.split()[0])  # First word of firm name
            
        if whale_class == WhaleClass.MEGALODON:
            parts.append("Mega")
        elif whale_class == WhaleClass.LEVIATHAN:
            parts.append("Leviathan")
        elif whale_class == WhaleClass.SHARK:
            parts.append("Shark")
        elif whale_class == WhaleClass.WHALE:
            parts.append("Whale")
            
        if strategy == StrategyType.HFT_ALGO:
            parts.append("HFT")
        elif strategy == StrategyType.MM_SPOOF:
            parts.append("Spoofer")
        elif strategy == StrategyType.RETAIL_HUNT:
            parts.append("Hunter")
            
        return " ".join(parts) if parts else "Unknown Whale"
        
    def save_profiles(self) -> None:
        """💾 Save profiles to disk."""
        try:
            data = {
                'profiles': {pid: asdict(p) for pid, p in self.profiles.items()},
                'next_id': self.next_profile_id
            }
            
            with open(self.persistence_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logger.debug(f"💾 Saved {len(self.profiles)} profiles")
        except Exception as e:
            logger.error(f"Failed to save profiles: {e}")
            
    def load_profiles(self) -> None:
        """📂 Load profiles from disk."""
        if not self.persistence_file.exists():
            return
            
        try:
            with open(self.persistence_file) as f:
                data = json.load(f)
                
            for pid, pdata in data.get('profiles', {}).items():
                # Reconstruct dataclasses
                pdata['activity_24h'] = Activity24Hour(**pdata['activity_24h'])
                pdata['current_targets'] = [
                    CurrentTarget(**t) for t in pdata['current_targets']
                ]
                self.profiles[pid] = WhaleProfile(**pdata)
                
            self.next_profile_id = data.get('next_id', 1)
            
            logger.info(f"📂 Loaded {len(self.profiles)} profiles from disk")
        except Exception as e:
            logger.error(f"Failed to load profiles: {e}")


# Singleton instance
_profiler_system = None

def get_whale_profiler() -> WhaleProfilerSystem:
    """Get the singleton whale profiler instance."""
    global _profiler_system
    if _profiler_system is None:
        _profiler_system = WhaleProfilerSystem()
    return _profiler_system


if __name__ == '__main__':
    print("🏷️🐋 WHALE PROFILER SYSTEM - Test Mode 🐋🏷️")
    print("=" * 62)
    
    profiler = get_whale_profiler()
    
    # Create test profiles
    profile1 = profiler.create_profile(
        symbol="ETHUSDT",
        whale_class=WhaleClass.SHARK,
        strategy=StrategyType.HFT_ALGO,
        frequency=4.03,
        activities=393,
        firm="Jump Trading",
        office="Singapore, Singapore"
    )
    
    # Update with activity
    profiler.update_profile(
        profile1.profile_id,
        symbol="ETHUSDT",
        action="buy",
        volume_usd=125_000
    )
    
    profiler.update_profile(
        profile1.profile_id,
        symbol="SOLUSDT",
        action="watching",
        volume_usd=0
    )
    
    # Display profile
    print(profiler.format_profile_display(profile1))
    
    # Show active profiles
    print(f"\n📊 Active Profiles: {len(profiler.get_active_profiles())}")
    
    # Save profiles
    profiler.save_profiles()
    print("\n💾 Profiles saved!")
