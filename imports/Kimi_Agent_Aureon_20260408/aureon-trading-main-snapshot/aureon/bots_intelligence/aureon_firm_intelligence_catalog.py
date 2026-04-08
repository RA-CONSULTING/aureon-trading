#!/usr/bin/env python3
"""
📊 AUREON FIRM INTELLIGENCE CATALOG 📊
=======================================

Real-time intelligence database tracking major trading firms:
- 24-hour movement history
- Pattern recognition (entry/exit behaviors)
- Market correlations
- Probability predictions
- Success rate tracking
- Behavioral fingerprints

This gives us UNFAIR ADVANTAGE by knowing what firms are doing BEFORE they execute.

Gary Leckey | January 2026 | Know Thy Enemy, Beat Thy Enemy
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from collections import deque, defaultdict
from datetime import datetime, timedelta
from enum import Enum

# UTF-8 fix
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'

import logging
logger = logging.getLogger(__name__)

# Sacred constants
PHI = (1 + math.sqrt(5)) / 2


class FirmActivityType(Enum):
    """Types of firm activities we track."""
    BUY = "buy"
    SELL = "sell"
    ACCUMULATION = "accumulation"
    DISTRIBUTION = "distribution"
    MARKET_MAKING = "market_making"
    ARBITRAGE = "arbitrage"
    SPOOFING = "spoofing"
    ICEBERG = "iceberg"
    UNKNOWN = "unknown"


class MarketRegime(Enum):
    """Market regimes firms operate in."""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    VOLATILE = "volatile"
    QUIET = "quiet"


@dataclass
class FirmMovement:
    """A single tracked movement by a firm."""
    firm_id: str
    timestamp: float
    symbol: str
    activity_type: FirmActivityType
    volume_usd: float
    price: float
    side: str  # 'buy' or 'sell'
    confidence: float  # Attribution confidence
    
    # Derived metrics
    market_impact: float = 0.0  # Price change caused (%)
    success_score: float = 0.0  # How profitable was this move?
    pattern_match: Optional[str] = None  # Pattern name if recognized
    
    # Context
    market_regime: MarketRegime = MarketRegime.SIDEWAYS
    time_of_day_hour: int = 0
    day_of_week: int = 0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['activity_type'] = self.activity_type.value
        data['market_regime'] = self.market_regime.value
        return data


@dataclass
class FirmPattern:
    """Recognized behavioral pattern for a firm."""
    pattern_id: str
    firm_id: str
    pattern_name: str
    occurrences: int = 0
    success_rate: float = 0.0
    
# ═══════════════════════════════════════════════════════════════════════════════
# 🤖 BOT CENSUS REGISTRY 🤖
# ═══════════════════════════════════════════════════════════════════════════════
# The "Yellow Pages" of silicon lifeforms.
# Tracks every known bot entity, its spectral signature, and cultural origin.

@dataclass
class BotCensusEntry:
    bot_uuid: str
    firm_id: str             # "CITADEL_SECURITIES", "UNKNOWN_WHALE"
    cultural_origin: str     # "USA_Chicago", "Russia_Moscow"
    primary_spectrum_band: str # "HIGH_FREQ", "INFRA_LOW"
    
    first_seen: float
    last_seen: float
    
    frequency_fingerprint: List[float] # Key frequencies (Hz)
    shape_class: str         # "HFT_SCALPER", "MM_SPOOFER"
    
    manipulation_score: float # 0.0 - 1.0 (How toxic is this bot?)
    status: str              # "ACTIVE", "DORMANT", "BANNED"

class BotCensusRegistry:
    """
    Central Registry for all identified autonomous agents.
    """
    def __init__(self, persistence_file="bot_census_registry.json"):
        self.persistence_file = persistence_file
        self.registry: Dict[str, BotCensusEntry] = {}
        self.load()

    def register_or_update(self, entry: BotCensusEntry):
        """Register a new bot or update existing one."""
        if entry.bot_uuid in self.registry:
            existing = self.registry[entry.bot_uuid]
            # Merge logic (keep oldest first_seen, update last_seen)
            existing.last_seen = time.time()
            existing.frequency_fingerprint = entry.frequency_fingerprint # Update signatures
            existing.manipulation_score = (existing.manipulation_score + entry.manipulation_score) / 2
            existing.status = "ACTIVE"
            self.registry[entry.bot_uuid] = existing
        else:
            self.registry[entry.bot_uuid] = entry
            
        self.save()

    def find_by_firm(self, firm_id: str) -> List[BotCensusEntry]:
        return [b for b in self.registry.values() if b.firm_id == firm_id]

    def find_by_spectrum(self, band: str) -> List[BotCensusEntry]:
        return [b for b in self.registry.values() if b.primary_spectrum_band == band]

    def load(self):
        if os.path.exists(self.persistence_file):
            try:
                with open(self.persistence_file, 'r') as f:
                    data = json.load(f)
                    for k, v in data.items():
                        self.registry[k] = BotCensusEntry(**v)
            except Exception as e:
                logger.error(f"Failed to load Bot Census: {e}")

    def save(self):
        # Rate limit saves in production
        try:
            with open(self.persistence_file, 'w') as f:
                json.dump({k: asdict(v) for k, v in self.registry.items()}, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save Bot Census: {e}")

# Global Registry Instance
_registry_instance = BotCensusRegistry()

def get_bot_census() -> BotCensusRegistry:
    return _registry_instance
    avg_profit_pct: float = 0.0
    
    # Pattern characteristics
    typical_volume_range: Tuple[float, float] = (0, 0)
    typical_duration_seconds: float = 0
    preferred_hours: List[int] = field(default_factory=list)
    preferred_symbols: List[str] = field(default_factory=list)
    market_regimes: List[MarketRegime] = field(default_factory=list)
    
    # Predictive
    next_move_probability: float = 0.5  # Probability of this pattern repeating
    confidence_score: float = 0.5
    
    last_seen: float = 0.0
    
    def to_dict(self) -> Dict:
        data = asdict(self)
        data['market_regimes'] = [r.value for r in self.market_regimes]
        return data


@dataclass
class FirmStatistics:
    """Statistical summary for a firm over 24 hours."""
    firm_id: str
    total_movements: int = 0
    total_volume_usd: float = 0.0
    avg_movement_size: float = 0.0
    
    # Activity breakdown
    buys: int = 0
    sells: int = 0
    volume_bought: float = 0.0
    volume_sold: float = 0.0
    
    # Performance
    successful_moves: int = 0
    failed_moves: int = 0
    success_rate: float = 0.0
    avg_profit_pct: float = 0.0
    total_market_impact: float = 0.0
    
    # Behavioral
    most_active_hours: List[int] = field(default_factory=list)
    most_active_symbols: List[str] = field(default_factory=list)
    dominant_activity_type: FirmActivityType = FirmActivityType.UNKNOWN
    
    # Predictions
    next_24h_activity_probability: float = 0.5
    predicted_direction: str = "neutral"  # 'bullish', 'bearish', 'neutral'
    confidence: float = 0.5


@dataclass
class MarketCorrelation:
    """Correlation between a firm's activity and market movements."""
    firm_id: str
    symbol: str
    correlation_coefficient: float  # -1 to 1
    lag_seconds: float  # How many seconds firm leads/lags market
    predictive_power: float  # 0-1, how well firm predicts market
    
    # Statistics
    sample_size: int = 0
    last_updated: float = 0.0


class FirmIntelligenceCatalog:
    """
    📊 REAL-TIME FIRM INTELLIGENCE DATABASE
    
    Tracks everything major firms do in real-time:
    - All movements (buys, sells, spoofs, etc.)
    - Pattern recognition (repeating behaviors)
    - Market correlations (who leads, who follows)
    - Probability predictions (what they'll do next)
    - Success tracking (how often they win)
    
    This is our UNFAIR ADVANTAGE.
    """
    
    def __init__(self, lookback_hours: int = 24):
        self.lookback_hours = lookback_hours
        self.lookback_seconds = lookback_hours * 3600
        
        # Movement storage: firm_id → deque of movements
        self.movements: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Pattern library: firm_id → list of patterns
        self.patterns: Dict[str, List[FirmPattern]] = defaultdict(list)
        
        # Statistics cache: firm_id → stats
        self.statistics: Dict[str, FirmStatistics] = {}
        
        # Market correlations: (firm_id, symbol) → correlation
        self.correlations: Dict[Tuple[str, str], MarketCorrelation] = {}
        
        # Real-time tracking
        self.active_firms: set = set()
        self.last_activity: Dict[str, float] = {}
        
        # Persistence
        self.state_file = Path("firm_intelligence_catalog_state.json")
        self._load_state()
        
        logger.info("📊 Firm Intelligence Catalog initialized")
        logger.info(f"   Lookback: {lookback_hours} hours")
        logger.info(f"   Tracking: {len(self.movements)} firms")
    
    def _load_state(self):
        """Load persisted state."""
        try:
            if self.state_file.exists():
                data = json.loads(self.state_file.read_text())
                
                # Load movements
                for firm_id, movements_list in data.get('movements', {}).items():
                    for mov_data in movements_list:
                        mov = FirmMovement(**{
                            **mov_data,
                            'activity_type': FirmActivityType(mov_data['activity_type']),
                            'market_regime': MarketRegime(mov_data['market_regime'])
                        })
                        self.movements[firm_id].append(mov)
                
                # Load patterns
                for firm_id, patterns_list in data.get('patterns', {}).items():
                    for pat_data in patterns_list:
                        pat = FirmPattern(**{
                            **pat_data,
                            'market_regimes': [MarketRegime(r) for r in pat_data['market_regimes']]
                        })
                        self.patterns[firm_id].append(pat)
                
                logger.info(f"📊 Loaded catalog state: {len(self.movements)} firms, {sum(len(p) for p in self.patterns.values())} patterns")
        except Exception as e:
            logger.debug(f"Could not load catalog state: {e}")
    
    def _save_state(self):
        """Persist state."""
        try:
            # Only save recent movements (last 24h)
            now = time.time()
            cutoff = now - self.lookback_seconds
            
            movements_dict = {}
            for firm_id, movements in self.movements.items():
                recent = [m.to_dict() for m in movements if m.timestamp >= cutoff]
                if recent:
                    movements_dict[firm_id] = recent
            
            patterns_dict = {}
            for firm_id, patterns in self.patterns.items():
                patterns_dict[firm_id] = [p.to_dict() for p in patterns]
            
            data = {
                'movements': movements_dict,
                'patterns': patterns_dict,
                'last_update': now
            }
            
            tmp = self.state_file.with_suffix('.json.tmp')
            tmp.write_text(json.dumps(data, indent=2))
            tmp.rename(self.state_file)
        except Exception as e:
            logger.debug(f"Could not save catalog state: {e}")
    
    def record_movement(self, firm_id: str, symbol: str, side: str, volume_usd: float,
                       price: float, confidence: float = 0.8, 
                       activity_type: Optional[FirmActivityType] = None) -> FirmMovement:
        """
        Record a firm movement.
        
        Args:
            firm_id: Firm identifier
            symbol: Trading pair
            side: 'buy' or 'sell'
            volume_usd: Trade volume in USD
            price: Execution price
            confidence: Attribution confidence
            activity_type: Type of activity (auto-detected if None)
            
        Returns:
            FirmMovement object
        """
        now = time.time()
        dt = datetime.fromtimestamp(now)
        
        # Auto-detect activity type if not provided
        if activity_type is None:
            activity_type = self._detect_activity_type(firm_id, symbol, side, volume_usd)
        
        # Detect market regime
        market_regime = self._detect_market_regime(symbol)
        
        movement = FirmMovement(
            firm_id=firm_id,
            timestamp=now,
            symbol=symbol,
            activity_type=activity_type,
            volume_usd=volume_usd,
            price=price,
            side=side,
            confidence=confidence,
            market_regime=market_regime,
            time_of_day_hour=dt.hour,
            day_of_week=dt.weekday()
        )
        
        # Store movement
        self.movements[firm_id].append(movement)
        self.active_firms.add(firm_id)
        self.last_activity[firm_id] = now
        
        # Check for pattern matches
        self._check_pattern_match(movement)
        
        # Update correlations
        self._update_correlation(firm_id, symbol, side, price, now)
        
        logger.debug(f"📊 Recorded: {firm_id} {side.upper()} {symbol} ${volume_usd:,.0f}")
        
        return movement
    
    def _detect_activity_type(self, firm_id: str, symbol: str, side: str, volume: float) -> FirmActivityType:
        """Auto-detect activity type based on context."""
        # Get recent movements for context
        recent = self._get_recent_movements(firm_id, window_seconds=300)
        
        if len(recent) < 2:
            return FirmActivityType.BUY if side == 'buy' else FirmActivityType.SELL
        
        # Check for accumulation (multiple buys)
        if side == 'buy':
            recent_buys = [m for m in recent if m.side == 'buy' and m.symbol == symbol]
            if len(recent_buys) >= 3:
                return FirmActivityType.ACCUMULATION
        
        # Check for distribution (multiple sells)
        if side == 'sell':
            recent_sells = [m for m in recent if m.side == 'sell' and m.symbol == symbol]
            if len(recent_sells) >= 3:
                return FirmActivityType.DISTRIBUTION
        
        # Check for market making (buy and sell)
        buys = sum(1 for m in recent if m.side == 'buy' and m.symbol == symbol)
        sells = sum(1 for m in recent if m.side == 'sell' and m.symbol == symbol)
        if buys > 0 and sells > 0:
            return FirmActivityType.MARKET_MAKING
        
        # Check for arbitrage (quick turnaround)
        if len(recent) >= 2:
            last = recent[-1]
            if last.symbol == symbol and last.side != side:
                time_diff = time.time() - last.timestamp
                if time_diff < 60:  # Less than 1 minute
                    return FirmActivityType.ARBITRAGE
        
        # Check for large volume (possible spoof or iceberg)
        if volume > 1_000_000:  # $1M+
            return FirmActivityType.ICEBERG
        
        return FirmActivityType.BUY if side == 'buy' else FirmActivityType.SELL
    
    def _detect_market_regime(self, symbol: str) -> MarketRegime:
        """Detect current market regime (would integrate with market data)."""
        # Placeholder - would analyze actual market data
        # For now, return sideways as default
        return MarketRegime.SIDEWAYS
    
    def _get_recent_movements(self, firm_id: str, window_seconds: float = None) -> List[FirmMovement]:
        """Get recent movements for a firm."""
        if window_seconds is None:
            window_seconds = self.lookback_seconds
        
        now = time.time()
        cutoff = now - window_seconds
        
        if firm_id not in self.movements:
            return []
        
        return [m for m in self.movements[firm_id] if m.timestamp >= cutoff]
    
    def _check_pattern_match(self, movement: FirmMovement):
        """Check if movement matches known patterns."""
        firm_patterns = self.patterns.get(movement.firm_id, [])
        
        for pattern in firm_patterns:
            # Check if movement fits pattern characteristics
            if movement.symbol in pattern.preferred_symbols:
                if movement.time_of_day_hour in pattern.preferred_hours:
                    if movement.market_regime in pattern.market_regimes:
                        movement.pattern_match = pattern.pattern_name
                        pattern.last_seen = movement.timestamp
                        logger.info(f"📊 Pattern match: {movement.firm_id} → {pattern.pattern_name}")
                        break
    
    def _update_correlation(self, firm_id: str, symbol: str, side: str, price: float, timestamp: float):
        """Update market correlation data."""
        # Placeholder for correlation tracking
        # Would analyze how firm's moves correlate with subsequent market movements
        pass
    
    def compute_statistics(self, firm_id: str) -> FirmStatistics:
        """
        Compute comprehensive statistics for a firm over lookback period.
        
        Returns:
            FirmStatistics object with all metrics
        """
        recent = self._get_recent_movements(firm_id)
        
        if not recent:
            return FirmStatistics(firm_id=firm_id)
        
        stats = FirmStatistics(firm_id=firm_id)
        stats.total_movements = len(recent)
        
        # Volume statistics
        stats.total_volume_usd = sum(m.volume_usd for m in recent)
        stats.avg_movement_size = stats.total_volume_usd / len(recent) if recent else 0
        
        # Activity breakdown
        stats.buys = sum(1 for m in recent if m.side == 'buy')
        stats.sells = sum(1 for m in recent if m.side == 'sell')
        stats.volume_bought = sum(m.volume_usd for m in recent if m.side == 'buy')
        stats.volume_sold = sum(m.volume_usd for m in recent if m.side == 'sell')
        
        # Performance
        stats.successful_moves = sum(1 for m in recent if m.success_score > 0)
        stats.failed_moves = sum(1 for m in recent if m.success_score < 0)
        stats.success_rate = stats.successful_moves / len(recent) if recent else 0
        stats.avg_profit_pct = sum(m.success_score for m in recent) / len(recent) if recent else 0
        stats.total_market_impact = sum(abs(m.market_impact) for m in recent)
        
        # Behavioral analysis
        hour_counts = defaultdict(int)
        symbol_counts = defaultdict(int)
        activity_counts = defaultdict(int)
        
        for m in recent:
            hour_counts[m.time_of_day_hour] += 1
            symbol_counts[m.symbol] += 1
            activity_counts[m.activity_type] += 1
        
        stats.most_active_hours = sorted(hour_counts.keys(), key=lambda h: hour_counts[h], reverse=True)[:3]
        stats.most_active_symbols = sorted(symbol_counts.keys(), key=lambda s: symbol_counts[s], reverse=True)[:5]
        stats.dominant_activity_type = max(activity_counts.keys(), key=lambda k: activity_counts[k]) if activity_counts else FirmActivityType.UNKNOWN
        
        # Predictions
        stats.next_24h_activity_probability = self._predict_activity_probability(firm_id, recent)
        stats.predicted_direction = self._predict_direction(firm_id, recent)
        stats.confidence = self._calculate_prediction_confidence(firm_id, recent)
        
        # Cache statistics
        self.statistics[firm_id] = stats
        
        return stats
    
    def _predict_activity_probability(self, firm_id: str, recent: List[FirmMovement]) -> float:
        """Predict probability of activity in next 24 hours."""
        if not recent:
            return 0.5
        
        # Calculate activity frequency
        if len(recent) < 2:
            return 0.5
        
        # Time between movements
        time_diffs = []
        for i in range(1, len(recent)):
            time_diffs.append(recent[i].timestamp - recent[i-1].timestamp)
        
        if not time_diffs:
            return 0.5
        
        avg_interval = sum(time_diffs) / len(time_diffs)
        hours_since_last = (time.time() - recent[-1].timestamp) / 3600
        
        # If average interval is short and recent activity, high probability
        if avg_interval < 3600 and hours_since_last < 6:  # < 1 hour intervals, < 6 hours ago
            return 0.85
        elif avg_interval < 7200 and hours_since_last < 12:  # < 2 hour intervals, < 12 hours ago
            return 0.65
        else:
            return 0.45
    
    def _predict_direction(self, firm_id: str, recent: List[FirmMovement]) -> str:
        """Predict next likely direction."""
        if not recent:
            return "neutral"
        
        # Analyze recent bias
        recent_5 = recent[-5:] if len(recent) >= 5 else recent
        
        buy_volume = sum(m.volume_usd for m in recent_5 if m.side == 'buy')
        sell_volume = sum(m.volume_usd for m in recent_5 if m.side == 'sell')
        
        if buy_volume > sell_volume * 1.5:
            return "bullish"
        elif sell_volume > buy_volume * 1.5:
            return "bearish"
        else:
            return "neutral"
    
    def _calculate_prediction_confidence(self, firm_id: str, recent: List[FirmMovement]) -> float:
        """Calculate confidence in predictions."""
        if len(recent) < 5:
            return 0.3  # Low confidence with little data
        
        # Base confidence on pattern consistency
        if len(recent) >= 10:
            # Check if recent behavior is consistent
            recent_10 = recent[-10:]
            activity_types = [m.activity_type for m in recent_10]
            most_common = max(set(activity_types), key=activity_types.count)
            consistency = activity_types.count(most_common) / len(activity_types)
            
            return 0.5 + (consistency * 0.5)  # 0.5 to 1.0 range
        
        return 0.5
    
    def recognize_patterns(self, firm_id: str, min_occurrences: int = 3) -> List[FirmPattern]:
        """
        Recognize behavioral patterns for a firm.
        
        Args:
            firm_id: Firm to analyze
            min_occurrences: Minimum times pattern must repeat
            
        Returns:
            List of recognized patterns
        """
        movements = self._get_recent_movements(firm_id)
        
        if len(movements) < min_occurrences * 2:
            return []
        
        patterns = []
        
        # Pattern 1: Time-of-day patterns
        hour_activity = defaultdict(list)
        for m in movements:
            hour_activity[m.time_of_day_hour].append(m)
        
        for hour, movs in hour_activity.items():
            if len(movs) >= min_occurrences:
                pattern = FirmPattern(
                    pattern_id=f"{firm_id}_hour_{hour}",
                    firm_id=firm_id,
                    pattern_name=f"Active at {hour:02d}:00",
                    occurrences=len(movs),
                    preferred_hours=[hour],
                    preferred_symbols=list(set(m.symbol for m in movs)),
                    last_seen=max(m.timestamp for m in movs)
                )
                patterns.append(pattern)
        
        # Pattern 2: Symbol-specific patterns
        symbol_activity = defaultdict(list)
        for m in movements:
            symbol_activity[m.symbol].append(m)
        
        for symbol, movs in symbol_activity.items():
            if len(movs) >= min_occurrences:
                buys = sum(1 for m in movs if m.side == 'buy')
                sells = sum(1 for m in movs if m.side == 'sell')
                
                if buys > sells * 2:
                    direction = "accumulation"
                elif sells > buys * 2:
                    direction = "distribution"
                else:
                    direction = "balanced"
                
                pattern = FirmPattern(
                    pattern_id=f"{firm_id}_symbol_{symbol}_{direction}",
                    firm_id=firm_id,
                    pattern_name=f"{symbol} {direction}",
                    occurrences=len(movs),
                    preferred_symbols=[symbol],
                    last_seen=max(m.timestamp for m in movs)
                )
                patterns.append(pattern)
        
        # Store patterns
        self.patterns[firm_id] = patterns
        
        logger.info(f"📊 Recognized {len(patterns)} patterns for {firm_id}")
        
        return patterns
    
    def get_firm_summary(self, firm_id: str) -> Dict[str, Any]:
        """
        Get comprehensive summary for a firm.
        
        Returns:
            {
                'firm_id': str,
                'statistics': FirmStatistics,
                'patterns': List[FirmPattern],
                'recent_movements': List[FirmMovement],
                'correlations': List[MarketCorrelation],
                'prediction': {
                    'next_24h_probability': float,
                    'predicted_direction': str,
                    'confidence': float,
                    'reasoning': str
                }
            }
        """
        stats = self.compute_statistics(firm_id)
        patterns = self.recognize_patterns(firm_id)
        recent = self._get_recent_movements(firm_id, window_seconds=3600)  # Last hour
        
        # Get correlations for this firm
        firm_correlations = [
            corr for (fid, sym), corr in self.correlations.items()
            if fid == firm_id
        ]
        
        # Generate prediction reasoning
        reasoning_parts = []
        if stats.next_24h_activity_probability > 0.7:
            reasoning_parts.append(f"High activity probability ({stats.next_24h_activity_probability:.0%})")
        if stats.predicted_direction != "neutral":
            reasoning_parts.append(f"Bias: {stats.predicted_direction}")
        if patterns:
            reasoning_parts.append(f"{len(patterns)} patterns recognized")
        if stats.most_active_symbols:
            reasoning_parts.append(f"Focus on: {', '.join(stats.most_active_symbols[:2])}")
        
        reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Insufficient data"
        
        return {
            'firm_id': firm_id,
            'statistics': asdict(stats),
            'patterns': [asdict(p) for p in patterns],
            'recent_movements': [m.to_dict() for m in recent[-10:]],  # Last 10
            'correlations': [asdict(c) for c in firm_correlations],
            'prediction': {
                'next_24h_probability': stats.next_24h_activity_probability,
                'predicted_direction': stats.predicted_direction,
                'confidence': stats.confidence,
                'reasoning': reasoning
            },
            'last_activity': self.last_activity.get(firm_id, 0),
            'hours_since_activity': (time.time() - self.last_activity.get(firm_id, time.time())) / 3600
        }
    
    def get_all_active_firms(self) -> List[str]:
        """Get list of all firms with recent activity."""
        now = time.time()
        cutoff = now - self.lookback_seconds
        
        active = []
        for firm_id, last_time in self.last_activity.items():
            if last_time >= cutoff:
                active.append(firm_id)
        
        return sorted(active)
    
    def get_market_leaders(self, symbol: str, top_n: int = 5) -> List[Tuple[str, float]]:
        """
        Get top firms by activity in a specific market.
        
        Returns:
            List of (firm_id, total_volume) tuples
        """
        firm_volumes = defaultdict(float)
        
        for firm_id, movements in self.movements.items():
            symbol_movs = [m for m in movements if m.symbol == symbol]
            total_vol = sum(m.volume_usd for m in symbol_movs)
            if total_vol > 0:
                firm_volumes[firm_id] = total_vol
        
        sorted_firms = sorted(firm_volumes.items(), key=lambda x: x[1], reverse=True)
        return sorted_firms[:top_n]
    
    def get_status(self) -> Dict:
        """Get catalog status."""
        return {
            'total_firms_tracked': len(self.movements),
            'active_firms_24h': len(self.get_all_active_firms()),
            'total_movements_24h': sum(len(self._get_recent_movements(f)) for f in self.active_firms),
            'total_patterns': sum(len(p) for p in self.patterns.values()),
            'lookback_hours': self.lookback_hours
        }


# Global instance
_catalog_instance: Optional[FirmIntelligenceCatalog] = None

def get_firm_catalog() -> FirmIntelligenceCatalog:
    """Get global firm intelligence catalog."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = FirmIntelligenceCatalog()
    return _catalog_instance


# CLI interface
if __name__ == '__main__':
    print("📊 FIRM INTELLIGENCE CATALOG TEST 📊")
    print("=" * 60)
    
    catalog = get_firm_catalog()
    
    # Simulate some movements
    catalog.record_movement('citadel', 'BTC/USD', 'buy', 2_500_000, 95000)
    time.sleep(0.1)
    catalog.record_movement('citadel', 'BTC/USD', 'buy', 1_800_000, 95100)
    time.sleep(0.1)
    catalog.record_movement('jane_street', 'ETH/USD', 'sell', 1_200_000, 3200)
    time.sleep(0.1)
    catalog.record_movement('citadel', 'BTC/USD', 'buy', 3_000_000, 95200)
    
    # Get statistics
    stats = catalog.compute_statistics('citadel')
    print(f"\n📊 Citadel Statistics:")
    print(f"   Movements: {stats.total_movements}")
    print(f"   Volume: ${stats.total_volume_usd:,.0f}")
    print(f"   Buy/Sell: {stats.buys}/{stats.sells}")
    print(f"   Predicted: {stats.predicted_direction} ({stats.next_24h_activity_probability:.0%} probability)")
    
    # Get summary
    summary = catalog.get_firm_summary('citadel')
    print(f"\n📊 Citadel Summary:")
    print(f"   Patterns: {len(summary['patterns'])}")
    print(f"   Recent movements: {len(summary['recent_movements'])}")
    print(f"   Prediction: {summary['prediction']['reasoning']}")
    
    # Get market leaders
    leaders = catalog.get_market_leaders('BTC/USD')
    print(f"\n📊 BTC/USD Market Leaders:")
    for firm_id, volume in leaders:
        print(f"   {firm_id}: ${volume:,.0f}")
    
    print("\n" + "=" * 60)
    print("✅ Firm Intelligence Catalog ready")
