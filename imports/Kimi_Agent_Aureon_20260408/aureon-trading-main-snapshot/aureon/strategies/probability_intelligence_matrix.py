#!/usr/bin/env python3
"""
🎯🧠 PROBABILITY INTELLIGENCE MATRIX 🧠🎯
==========================================
STOPS MISTAKES BEFORE THEY HAPPEN

The old probability calculation was:
    P = proximity × momentum × cascade

THE PROBLEM: It ignored WHY ETAs were wrong!
- Dying momentum wasn't penalized
- High volatility wasn't penalized  
- Deceleration wasn't penalized
- Low sample confidence wasn't penalized

THE SOLUTION: Intelligence Matrix
- Integrates improved ETA confidence directly
- Penalizes dangerous patterns BEFORE they cause losses
- Learns from what actually predicts success

"Don't just predict. KNOW when the prediction is garbage."

Gary Leckey | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import time
import math
import json
import os
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field

# =============================================================================
# 📊 PROBABILITY INTELLIGENCE FACTORS
# =============================================================================

@dataclass
class IntelligenceFactor:
    """A factor that affects kill probability."""
    name: str
    weight: float  # How much this factor matters (0-1)
    value: float   # Current value (0-1, where 1 is good)
    reason: str    # Why this value
    
    @property
    def contribution(self) -> float:
        """Weighted contribution to probability."""
        return self.weight * self.value


@dataclass 
class ProbabilityIntelligence:
    """Complete intelligence assessment for probability calculation."""
    # Core metrics
    raw_probability: float = 0.0      # Naive calculation
    adjusted_probability: float = 0.0  # After intelligence adjustments
    confidence: float = 0.0            # How much to trust this probability
    
    # Intelligence factors
    factors: List[IntelligenceFactor] = field(default_factory=list)
    
    # Risk flags
    risk_flags: List[str] = field(default_factory=list)
    
    # Recommendation
    action: str = "HOLD"  # HOLD, WATCH, CAUTION, DANGER
    
    def add_factor(self, name: str, weight: float, value: float, reason: str):
        """Add an intelligence factor."""
        self.factors.append(IntelligenceFactor(name, weight, value, reason))
    
    def add_risk(self, flag: str):
        """Add a risk flag."""
        if flag not in self.risk_flags:
            self.risk_flags.append(flag)
    
    def calculate_adjusted(self):
        """Calculate adjusted probability from all factors."""
        if not self.factors:
            self.adjusted_probability = self.raw_probability
            return
        
        # Weighted product of all factors
        total_weight = sum(f.weight for f in self.factors)
        if total_weight == 0:
            self.adjusted_probability = self.raw_probability
            return
        
        # Each factor contributes proportionally
        adjustment = 0.0
        for f in self.factors:
            adjustment += (f.weight / total_weight) * f.value
        
        # Apply adjustment (0.5 = neutral, <0.5 = penalty, >0.5 = boost)
        if adjustment >= 0.5:
            # Boost: scale from raw to 1.0
            boost_factor = (adjustment - 0.5) * 2  # 0-1
            self.adjusted_probability = self.raw_probability + (1 - self.raw_probability) * boost_factor * 0.3
        else:
            # Penalty: scale from raw down to 0
            penalty_factor = (0.5 - adjustment) * 2  # 0-1
            self.adjusted_probability = self.raw_probability * (1 - penalty_factor * 0.7)
        
        # Clamp
        self.adjusted_probability = max(0, min(1, self.adjusted_probability))
        
        # Risk flags affect action recommendation
        if len(self.risk_flags) >= 3:
            self.action = "DANGER"
        elif len(self.risk_flags) >= 2:
            self.action = "CAUTION"
        elif len(self.risk_flags) >= 1:
            self.action = "WATCH"
        else:
            self.action = "HOLD"


# =============================================================================
# 🧠 PROBABILITY INTELLIGENCE MATRIX
# =============================================================================

class ProbabilityIntelligenceMatrix:
    """
    🧠 PROBABILITY INTELLIGENCE MATRIX 🧠
    
    Integrates ALL intelligence sources to calculate TRUE probability of kill.
    STOPS mistakes before they happen by:
    
    1. Penalizing dying momentum (velocity decay detected)
    2. Penalizing high volatility (unpredictable)
    3. Penalizing deceleration (slowing down)
    4. Penalizing low ETA confidence (unreliable prediction)
    5. Boosting strong patterns (acceleration, steady momentum)
    6. Learning from historical accuracy
    
    "The naive probability lies. The intelligent probability protects."
    """
    
    def __init__(self):
        # Learning state
        self.pattern_accuracy: Dict[str, Dict] = {}  # pattern -> {hits, misses, accuracy}
        self.factor_weights: Dict[str, float] = {
            'proximity': 0.25,           # How close to target
            'momentum': 0.20,            # Current momentum direction
            'eta_confidence': 0.20,      # From improved ETA calculator
            'acceleration': 0.15,        # Speeding up or slowing down
            'volatility': 0.10,          # Price stability
            'sample_quality': 0.10,      # Data quality
        }
        
        # Load learned state
        self._load_state()
        
        # Wire improved ETA calculator
        try:
            from improved_eta_calculator import ImprovedETACalculator
            self.eta_calc = ImprovedETACalculator()
            self.eta_calc_available = True
        except ImportError:
            self.eta_calc = None
            self.eta_calc_available = False
    
    def _load_state(self):
        """Load learned state from file."""
        state_file = "probability_intelligence_state.json"
        try:
            if os.path.exists(state_file):
                with open(state_file, 'r') as f:
                    data = json.load(f)
                    self.pattern_accuracy = data.get('pattern_accuracy', {})
                    saved_weights = data.get('factor_weights', {})
                    # Update weights if saved
                    for k, v in saved_weights.items():
                        if k in self.factor_weights:
                            self.factor_weights[k] = v
        except Exception:
            pass
    
    def _save_state(self):
        """Save learned state to file."""
        state_file = "probability_intelligence_state.json"
        try:
            data = {
                'pattern_accuracy': self.pattern_accuracy,
                'factor_weights': self.factor_weights,
                'last_updated': time.time()
            }
            with open(state_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def calculate_intelligent_probability(
        self,
        current_pnl: float,
        target_pnl: float,
        pnl_history: List[Tuple[float, float]],  # [(timestamp, pnl), ...]
        momentum_score: float = 0.0,
        cascade_factor: float = 1.0,
        kappa_t: float = 1.0,
        lighthouse_gamma: float = 0.5
    ) -> ProbabilityIntelligence:
        """
        🎯 Calculate intelligent probability with all factors.
        
        This is the ENHANCED probability calculation that STOPS mistakes.
        """
        intel = ProbabilityIntelligence()
        
        # ==== 1. PROXIMITY FACTOR ====
        if target_pnl > 0:
            proximity = max(0, min(1, current_pnl / target_pnl))
        else:
            proximity = 0.0
        
        # Proximity is good when high
        intel.add_factor(
            name="proximity",
            weight=self.factor_weights['proximity'],
            value=proximity,
            reason=f"{proximity:.0%} to target"
        )
        
        # ==== 2. MOMENTUM FACTOR ====
        # Convert -1 to +1 score to 0-1 value
        momentum_value = (momentum_score + 1) / 2  # Now 0-1
        
        intel.add_factor(
            name="momentum", 
            weight=self.factor_weights['momentum'],
            value=momentum_value,
            reason=f"Momentum {momentum_score:+.2f}"
        )
        
        if momentum_score < 0:
            intel.add_risk("NEGATIVE_MOMENTUM")
        
        # ==== 3. ETA CONFIDENCE FACTOR (NEW!) ====
        eta_confidence = 0.5  # Default neutral
        eta_limiting_factors = []
        acceleration = 0.0
        volatility_cv = 0.0
        
        if self.eta_calc_available and len(pnl_history) >= 3:
            try:
                eta_result = self.eta_calc.calculate_eta(
                    current_pnl=current_pnl,
                    target_pnl=target_pnl,
                    pnl_history=pnl_history
                )
                
                eta_confidence = eta_result.confidence
                eta_limiting_factors = eta_result.limiting_factors
                acceleration = eta_result.acceleration
                volatility_cv = eta_result.volatility / max(0.0001, abs(eta_result.velocity)) if eta_result.velocity != 0 else 1.0
                
            except Exception:
                pass
        
        intel.add_factor(
            name="eta_confidence",
            weight=self.factor_weights['eta_confidence'],
            value=eta_confidence,
            reason=f"ETA confidence {eta_confidence:.0%}"
        )
        
        if eta_confidence < 0.2:
            intel.add_risk("LOW_ETA_CONFIDENCE")
        
        # ==== 4. ACCELERATION FACTOR (NEW!) ====
        # Positive acceleration is good (speeding up toward target)
        if acceleration > 0.00001:
            accel_value = min(1.0, 0.5 + acceleration * 10000)  # Boost for acceleration
            intel.add_factor(
                name="acceleration",
                weight=self.factor_weights['acceleration'],
                value=accel_value,
                reason=f"Accelerating +${acceleration:.6f}/s²"
            )
        elif acceleration < -0.00001:
            # DECELERATION - Major penalty!
            accel_value = max(0.0, 0.5 + acceleration * 10000)  # Penalty for deceleration
            intel.add_factor(
                name="acceleration",
                weight=self.factor_weights['acceleration'],
                value=accel_value,
                reason=f"DECELERATING ${acceleration:.6f}/s²"
            )
            intel.add_risk("DECELERATING")
        else:
            intel.add_factor(
                name="acceleration",
                weight=self.factor_weights['acceleration'],
                value=0.5,
                reason="Steady velocity"
            )
        
        # ==== 5. VOLATILITY FACTOR (NEW!) ====
        # Low volatility (stable) is good
        if volatility_cv > 0:
            if volatility_cv > 0.8:
                vol_value = 0.2  # High volatility = bad
                intel.add_risk("HIGH_VOLATILITY")
            elif volatility_cv > 0.5:
                vol_value = 0.4
            elif volatility_cv > 0.3:
                vol_value = 0.6
            else:
                vol_value = 0.8  # Low volatility = good
        else:
            vol_value = 0.5  # Unknown
        
        intel.add_factor(
            name="volatility",
            weight=self.factor_weights['volatility'],
            value=vol_value,
            reason=f"Volatility CV={volatility_cv:.2f}"
        )
        
        # ==== 6. SAMPLE QUALITY FACTOR ====
        sample_count = len(pnl_history)
        if sample_count >= 10:
            sample_value = 0.9
        elif sample_count >= 5:
            sample_value = 0.7
        elif sample_count >= 3:
            sample_value = 0.5
        else:
            sample_value = 0.2
            intel.add_risk("LOW_SAMPLES")
        
        intel.add_factor(
            name="sample_quality",
            weight=self.factor_weights['sample_quality'],
            value=sample_value,
            reason=f"{sample_count} samples"
        )
        
        # ==== CALCULATE RAW PROBABILITY (Old method) ====
        if momentum_score > 0:
            intel.raw_probability = proximity * (0.5 + 0.5 * momentum_score)
        else:
            intel.raw_probability = proximity * (0.5 + 0.5 * momentum_score)
        intel.raw_probability = max(0, min(1, intel.raw_probability))
        
        # ==== CASCADE BOOST (existing logic) ====
        cascade_mult = 1.0 + (cascade_factor - 1.0) * 0.3
        kappa_mult = 1.0 + (kappa_t - 1.0) * 0.2
        lighthouse_mult = 1.0
        if lighthouse_gamma >= 0.75:
            lighthouse_mult = 1.0 + (lighthouse_gamma - 0.75) * 0.4
        total_cascade = min(3.0, cascade_mult * kappa_mult * lighthouse_mult)
        
        intel.raw_probability *= total_cascade
        intel.raw_probability = max(0, min(1, intel.raw_probability))
        
        # ==== CALCULATE ADJUSTED PROBABILITY ====
        intel.calculate_adjusted()
        
        # ==== SET OVERALL CONFIDENCE ====
        intel.confidence = eta_confidence
        
        # ==== APPLY RISK FLAG PENALTIES ====
        # Each risk flag reduces probability
        risk_penalty = len(intel.risk_flags) * 0.1
        intel.adjusted_probability *= (1 - risk_penalty)
        intel.adjusted_probability = max(0, min(1, intel.adjusted_probability))
        
        return intel
    
    def record_outcome(
        self,
        intel: ProbabilityIntelligence,
        success: bool,
        symbol: str = ""
    ):
        """
        📚 Record outcome to learn from it.
        
        This allows the matrix to improve its factor weights over time.
        """
        # Create pattern key from factors
        pattern_parts = []
        for f in intel.factors:
            # Bucket factor values
            if f.value < 0.3:
                bucket = "low"
            elif f.value < 0.7:
                bucket = "mid"
            else:
                bucket = "high"
            pattern_parts.append(f"{f.name}:{bucket}")
        
        pattern_key = "|".join(sorted(pattern_parts))
        
        # Update pattern accuracy
        if pattern_key not in self.pattern_accuracy:
            self.pattern_accuracy[pattern_key] = {'hits': 0, 'misses': 0, 'accuracy': 0.5}
        
        if success:
            self.pattern_accuracy[pattern_key]['hits'] += 1
        else:
            self.pattern_accuracy[pattern_key]['misses'] += 1
        
        total = self.pattern_accuracy[pattern_key]['hits'] + self.pattern_accuracy[pattern_key]['misses']
        self.pattern_accuracy[pattern_key]['accuracy'] = self.pattern_accuracy[pattern_key]['hits'] / total
        
        # Adjust factor weights based on which factors were wrong
        if not success and len(intel.risk_flags) > 0:
            # Risk flags were correct - increase their factor weights
            for flag in intel.risk_flags:
                if flag == "NEGATIVE_MOMENTUM":
                    self.factor_weights['momentum'] = min(0.4, self.factor_weights['momentum'] * 1.05)
                elif flag == "LOW_ETA_CONFIDENCE":
                    self.factor_weights['eta_confidence'] = min(0.4, self.factor_weights['eta_confidence'] * 1.05)
                elif flag == "DECELERATING":
                    self.factor_weights['acceleration'] = min(0.3, self.factor_weights['acceleration'] * 1.05)
                elif flag == "HIGH_VOLATILITY":
                    self.factor_weights['volatility'] = min(0.25, self.factor_weights['volatility'] * 1.05)
                elif flag == "LOW_SAMPLES":
                    self.factor_weights['sample_quality'] = min(0.2, self.factor_weights['sample_quality'] * 1.05)
        
        # Normalize weights to sum to 1.0
        total_weight = sum(self.factor_weights.values())
        for k in self.factor_weights:
            self.factor_weights[k] /= total_weight
        
        # Save state
        self._save_state()
    
    def get_pattern_confidence(self, intel: ProbabilityIntelligence) -> float:
        """
        Get historical confidence for a pattern.
        Returns how often this pattern has succeeded historically.
        """
        pattern_parts = []
        for f in intel.factors:
            if f.value < 0.3:
                bucket = "low"
            elif f.value < 0.7:
                bucket = "mid"
            else:
                bucket = "high"
            pattern_parts.append(f"{f.name}:{bucket}")
        
        pattern_key = "|".join(sorted(pattern_parts))
        
        if pattern_key in self.pattern_accuracy:
            return self.pattern_accuracy[pattern_key]['accuracy']
        
        return 0.5  # Unknown pattern
    
    def explain(self, intel: ProbabilityIntelligence) -> str:
        """Generate human-readable explanation of probability."""
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║  🧠 PROBABILITY INTELLIGENCE MATRIX 🧠                        ║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]
        
        lines.append(f"║  Raw Probability:      {intel.raw_probability:.1%}")
        lines.append(f"║  Adjusted Probability: {intel.adjusted_probability:.1%}")
        lines.append(f"║  Confidence:           {intel.confidence:.1%}")
        lines.append(f"║  Action:               {intel.action}")
        lines.append("║  ────────────────────────────────────────────────────────")
        lines.append("║  INTELLIGENCE FACTORS:")
        
        for f in intel.factors:
            value_bar = "█" * int(f.value * 10) + "░" * (10 - int(f.value * 10))
            lines.append(f"║    {f.name:15s} [{value_bar}] {f.value:.0%} ({f.reason})")
        
        if intel.risk_flags:
            lines.append("║  ────────────────────────────────────────────────────────")
            lines.append("║  ⚠️ RISK FLAGS:")
            for flag in intel.risk_flags:
                lines.append(f"║    🚩 {flag}")
        
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        
        return "\n".join(lines)
    
    def get_status_report(self) -> str:
        """Get status report of learned patterns."""
        lines = [
            "\n🧠 PROBABILITY INTELLIGENCE MATRIX - STATUS REPORT",
            "=" * 60,
            "\n📊 CURRENT FACTOR WEIGHTS:",
        ]
        
        for name, weight in sorted(self.factor_weights.items(), key=lambda x: -x[1]):
            bar = "█" * int(weight * 40) + "░" * (40 - int(weight * 40))
            lines.append(f"  {name:15s} [{bar}] {weight:.1%}")
        
        if self.pattern_accuracy:
            lines.append(f"\n📚 LEARNED PATTERNS: {len(self.pattern_accuracy)}")
            
            # Show best and worst patterns
            sorted_patterns = sorted(
                self.pattern_accuracy.items(),
                key=lambda x: x[1]['accuracy'],
                reverse=True
            )
            
            lines.append("\n  🟢 BEST PATTERNS:")
            for pattern, stats in sorted_patterns[:3]:
                total = stats['hits'] + stats['misses']
                lines.append(f"    {stats['accuracy']:.0%} ({stats['hits']}/{total}): {pattern[:50]}...")
            
            lines.append("\n  🔴 WORST PATTERNS:")
            for pattern, stats in sorted_patterns[-3:]:
                total = stats['hits'] + stats['misses']
                lines.append(f"    {stats['accuracy']:.0%} ({stats['hits']}/{total}): {pattern[:50]}...")
        
        return "\n".join(lines)


# =============================================================================
# 🌍 GLOBAL SINGLETON
# =============================================================================

_PROB_MATRIX: Optional[ProbabilityIntelligenceMatrix] = None

def get_probability_matrix() -> ProbabilityIntelligenceMatrix:
    """Get singleton probability intelligence matrix."""
    global _PROB_MATRIX
    if _PROB_MATRIX is None:
        _PROB_MATRIX = ProbabilityIntelligenceMatrix()
    return _PROB_MATRIX


def calculate_intelligent_probability(
    current_pnl: float,
    target_pnl: float,
    pnl_history: List[Tuple[float, float]],
    momentum_score: float = 0.0,
    cascade_factor: float = 1.0,
    kappa_t: float = 1.0,
    lighthouse_gamma: float = 0.5
) -> ProbabilityIntelligence:
    """Convenience function to calculate intelligent probability."""
    matrix = get_probability_matrix()
    return matrix.calculate_intelligent_probability(
        current_pnl, target_pnl, pnl_history,
        momentum_score, cascade_factor, kappa_t, lighthouse_gamma
    )


def record_outcome(intel: ProbabilityIntelligence, success: bool, symbol: str = ""):
    """Convenience function to record outcome."""
    matrix = get_probability_matrix()
    matrix.record_outcome(intel, success, symbol)


# =============================================================================
# 🧪 DEMO / TEST
# =============================================================================

if __name__ == "__main__":
    import random
    
    print("🧠 PROBABILITY INTELLIGENCE MATRIX - DEMO")
    print("=" * 70)
    
    matrix = get_probability_matrix()
    
    # Demo 1: Strong momentum, good conditions
    print("\n📊 SCENARIO 1: Strong Momentum, Good Conditions")
    print("-" * 70)
    
    base_time = time.time() - 10
    pnl_history = []
    pnl = 0.002
    for i, v in enumerate([0.0003, 0.00035, 0.0004, 0.00045, 0.0005]):
        pnl += v
        pnl_history.append((base_time + i * 2, pnl))
    
    intel = matrix.calculate_intelligent_probability(
        current_pnl=pnl,
        target_pnl=0.01,
        pnl_history=pnl_history,
        momentum_score=0.7,
        cascade_factor=2.0
    )
    print(matrix.explain(intel))
    
    # Demo 2: Dying momentum, dangerous
    print("\n📊 SCENARIO 2: Dying Momentum, DANGEROUS")
    print("-" * 70)
    
    pnl_history = []
    pnl = 0.005
    for i, v in enumerate([0.001, 0.0006, 0.0003, 0.00015, 0.00005]):
        pnl += v
        pnl_history.append((base_time + i * 2, pnl))
    
    intel = matrix.calculate_intelligent_probability(
        current_pnl=pnl,
        target_pnl=0.01,
        pnl_history=pnl_history,
        momentum_score=0.2,
        cascade_factor=1.5
    )
    print(matrix.explain(intel))
    
    # Demo 3: High volatility
    print("\n📊 SCENARIO 3: High Volatility, Unpredictable")
    print("-" * 70)
    
    pnl_history = []
    pnl = 0.004
    for i, v in enumerate([0.001, -0.0005, 0.0015, -0.0003, 0.0008]):
        pnl += v
        pnl_history.append((base_time + i * 2, pnl))
    
    intel = matrix.calculate_intelligent_probability(
        current_pnl=pnl,
        target_pnl=0.01,
        pnl_history=pnl_history,
        momentum_score=0.3,
        cascade_factor=1.0
    )
    print(matrix.explain(intel))
    
    print("\n" + matrix.get_status_report())
