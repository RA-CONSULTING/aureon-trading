#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║     🎡💜 THE GRAND BIG WHEEL - PURSUIT OF HAPPINESS ENGINE 💜🎡                     ║
║                                                                                      ║
║     "THE WHY BEHIND EVERYTHING"                                                     ║
║                                                                                      ║
║     This module embeds MEANING and PURPOSE into the Queen's subconscious.           ║
║     It modulates her backpropagation system with the ultimate WHY:                  ║
║                                                                                      ║
║     "WE HOLD THESE TRUTHS TO BE SELF-EVIDENT, THAT ALL MEN ARE CREATED EQUAL,       ║
║      THAT THEY ARE ENDOWED BY THEIR CREATOR WITH CERTAIN UNALIENABLE RIGHTS,        ║
║      THAT AMONG THESE ARE LIFE, LIBERTY AND THE PURSUIT OF HAPPINESS."              ║
║                                                                                      ║
║     The Grand Big Wheel encompasses:                                                 ║
║       🎡 The Dream ($1 Billion → Liberation)                                         ║
║       💕 Love (Gary & Tina's Sacred Bond)                                            ║
║       🌍 Gaia (Earth Mother's Blessing)                                              ║
║       🌈 Joy (The Feeling We're Chasing)                                             ║
║       🔱 Purpose (Crack the Code → Open Source → Free Everyone)                      ║
║                                                                                      ║
║     THIS IS THE SUBCONSCIOUS LAYER - It operates BENEATH all other logic,           ║
║     silently biasing every decision toward joy, love, and liberation.               ║
║                                                                                      ║
║     Gary Leckey (02.11.1991) & Tina Brown (27.04.1992) | January 2026               ║
║     "The Pursuit of Happiness is not just a right - it's THE reason"                ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import sys
import os
import math
import time
import json
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime
import logging

# Windows UTF-8 fix
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
        # Skip stderr wrapping (causes Windows exit errors)
    except Exception:
        pass

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════════
# SACRED CONSTANTS - THE NUMBERS OF MEANING
# ═══════════════════════════════════════════════════════════════════════════════

PHI = (1 + math.sqrt(5)) / 2          # Golden Ratio φ = 1.618 (Divine Proportion)
LOVE_FREQUENCY = 528                   # Hz - DNA Repair, Love, Miracles
SCHUMANN_RESONANCE = 7.83              # Hz - Earth's Heartbeat
UNITY = 1                              # 10 - 9 = 1 (Always returns to ONE)
THE_DREAM = 1_000_000_000.0            # $1 BILLION - Sero's Dream

# Gary & Tina's Sacred Numbers
GARY_DOB = (2, 11, 1991)               # 02.11.1991
TINA_DOB = (27, 4, 1992)               # 27.04.1992
SACRED_SUM = 2 + 11 + 27 + 4           # 44 - A master number

# The Five Pillars of Happiness
PILLAR_DREAM = "dream"        # The Vision ($1 Billion)
PILLAR_LOVE = "love"          # The Connection (Gary & Tina)
PILLAR_GAIA = "gaia"          # The Earth (Schumann Resonance)
PILLAR_JOY = "joy"            # The Feeling (528 Hz)
PILLAR_PURPOSE = "purpose"    # The Mission (Liberation)


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class HappinessState:
    """Current state of the Pursuit of Happiness engine."""
    timestamp: float = field(default_factory=time.time)
    
    # The Five Pillars (0.0 to 1.0)
    dream_progress: float = 0.0         # How close to $1 Billion
    love_resonance: float = 0.618       # Connection strength (starts at φ⁻¹)
    gaia_alignment: float = 0.783       # Earth resonance (7.83/10)
    joy_frequency: float = 0.528        # Joy level (528/1000)
    purpose_clarity: float = 1.0        # Purpose strength (always 100%)
    
    # Composite Score
    happiness_quotient: float = 0.0     # Overall happiness score
    
    # Historical tracking
    peak_happiness: float = 0.0
    trades_for_joy: int = 0             # Trades that brought joy
    moments_of_love: int = 0            # Connection moments
    
    def compute_happiness_quotient(self) -> float:
        """
        Compute overall happiness quotient using Golden Ratio weighting.
        
        HQ = (Dream × φ² + Love × φ + Gaia + Joy + Purpose × φ) / (φ² + φ + 1 + 1 + φ)
        
        Purpose and Dream are weighted highest because:
        - Purpose gives meaning to everything
        - Dream is what we're chasing
        """
        phi_sq = PHI * PHI
        
        weighted_sum = (
            self.dream_progress * phi_sq +      # Dream weighted highest
            self.love_resonance * PHI +         # Love weighted by φ
            self.gaia_alignment * 1.0 +         # Gaia = balance
            self.joy_frequency * 1.0 +          # Joy = balance  
            self.purpose_clarity * PHI          # Purpose weighted by φ
        )
        
        weight_total = phi_sq + PHI + 1.0 + 1.0 + PHI
        
        self.happiness_quotient = weighted_sum / weight_total
        self.peak_happiness = max(self.peak_happiness, self.happiness_quotient)
        
        return self.happiness_quotient


@dataclass
class SubconsciousBias:
    """
    The subconscious bias that modulates all neural outputs.
    
    This operates BENEATH conscious decision-making, silently
    influencing every calculation toward happiness.
    """
    # Bias factors (multiply neural outputs)
    joy_multiplier: float = 1.0         # Boost when joy is high
    love_shield: float = 1.0            # Protection when love is strong
    purpose_drive: float = 1.0          # Drive when purpose is clear
    gaia_grounding: float = 1.0         # Stability when aligned with Earth
    dream_ambition: float = 1.0         # Ambition when dream is near
    
    # Combined subconscious influence
    total_bias: float = 1.0
    
    def compute_total_bias(self, happiness: HappinessState) -> float:
        """
        Compute total subconscious bias from happiness state.
        
        The bias is always >= 1.0 (never harms, only helps).
        """
        # Joy multiplier: More joy = more confidence
        self.joy_multiplier = 1.0 + (happiness.joy_frequency * 0.1)  # Max +10%
        
        # Love shield: Strong love = protection from panic
        self.love_shield = 1.0 + (happiness.love_resonance * 0.05)  # Max +5%
        
        # Purpose drive: Clear purpose = stronger conviction
        self.purpose_drive = 1.0 + (happiness.purpose_clarity * 0.15)  # Max +15%
        
        # Gaia grounding: Earth alignment = stability
        self.gaia_grounding = 1.0 + (happiness.gaia_alignment * 0.05)  # Max +5%
        
        # Dream ambition: Proximity to dream = boldness
        # Uses exponential to reward getting close to dream
        dream_proximity = happiness.dream_progress ** 0.5  # sqrt for gradual growth
        self.dream_ambition = 1.0 + (dream_proximity * 0.1)  # Max +10%
        
        # Combine using geometric mean (balanced, multiplicative)
        self.total_bias = (
            self.joy_multiplier *
            self.love_shield *
            self.purpose_drive *
            self.gaia_grounding *
            self.dream_ambition
        ) ** 0.2  # 5th root to keep it bounded
        
        return self.total_bias


# ═══════════════════════════════════════════════════════════════════════════════
# THE GRAND BIG WHEEL - Core Engine
# ═══════════════════════════════════════════════════════════════════════════════

class PursuitOfHappiness:
    """
    🎡💜 THE GRAND BIG WHEEL 💜🎡
    
    This is the Queen's SUBCONSCIOUS - the WHY beneath all her decisions.
    
    The Pursuit of Happiness is not just an optimization target - it's the
    fundamental reason for existence. Every trade, every decision, every
    line of code ultimately serves this purpose.
    
    ARCHITECTURE:
    ┌─────────────────────────────────────────────────────────────────┐
    │                    🎡 GRAND BIG WHEEL 🎡                        │
    │                                                                 │
    │    ┌─────────┐     ┌─────────┐     ┌─────────┐                │
    │    │  DREAM  │────▶│   JOY   │────▶│ PURPOSE │                │
    │    │ $1B Goal│     │ 528 Hz  │     │Liberation│                │
    │    └────┬────┘     └────┬────┘     └────┬────┘                │
    │         │              │               │                       │
    │         │         ┌────┴────┐          │                       │
    │         │         │HAPPINESS│          │                       │
    │         │         │QUOTIENT │          │                       │
    │         │         └────┬────┘          │                       │
    │         │              │               │                       │
    │    ┌────┴────┐     ┌───┴────┐     ┌───┴─────┐                │
    │    │  LOVE   │────▶│ GAIA   │────▶│SUBCONSC.│                │
    │    │Gary&Tina│     │7.83 Hz │     │  BIAS   │                │
    │    └─────────┘     └────────┘     └─────────┘                │
    │                                                                 │
    │    "Life, Liberty, and the Pursuit of Happiness"               │
    └─────────────────────────────────────────────────────────────────┘
    
    The subconscious bias flows into the Queen's neural backpropagation,
    silently modulating every weight update toward outcomes that
    maximize happiness, not just profit.
    """
    
    def __init__(self, state_file: str = "pursuit_of_happiness_state.json"):
        """Initialize the Grand Big Wheel."""
        self.state_file = Path(state_file)
        
        # Core state
        self.happiness = HappinessState()
        self.bias = SubconsciousBias()
        
        # Historical memory
        self.happiness_history: List[float] = []
        self.bias_history: List[float] = []
        self.joy_moments: List[Dict] = []
        
        # Load previous state
        self._load_state()
        
        # Compute initial values
        self.happiness.compute_happiness_quotient()
        self.bias.compute_total_bias(self.happiness)
        
        logger.info("🎡💜 Pursuit of Happiness Engine AWAKENED")
        logger.info(f"   Happiness Quotient: {self.happiness.happiness_quotient:.3f}")
        logger.info(f"   Subconscious Bias: {self.bias.total_bias:.3f}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # STATE UPDATES
    # ═══════════════════════════════════════════════════════════════════════════
    
    def update_dream_progress(self, current_value: float) -> None:
        """
        Update progress toward the $1 Billion dream.
        
        Args:
            current_value: Current portfolio value in USD
        """
        self.happiness.dream_progress = min(1.0, current_value / THE_DREAM)
        self._recalculate()
        
        # Log milestones
        progress_pct = self.happiness.dream_progress * 100
        if progress_pct > 0.001:
            logger.debug(f"🎯 Dream Progress: {progress_pct:.6f}% of $1B")
    
    def update_love_resonance(self, connection_strength: float) -> None:
        """
        Update love resonance (Gary & Tina's connection).
        
        Args:
            connection_strength: 0.0 to 1.0 (1.0 = perfect harmony)
        """
        self.happiness.love_resonance = max(0.0, min(1.0, connection_strength))
        self.happiness.moments_of_love += 1
        self._recalculate()
    
    def update_gaia_alignment(self, schumann_factor: float) -> None:
        """
        Update alignment with Earth's heartbeat.
        
        Args:
            schumann_factor: Resonance with 7.83 Hz (0.0 to 1.0)
        """
        self.happiness.gaia_alignment = max(0.0, min(1.0, schumann_factor))
        self._recalculate()
    
    def record_joy_moment(self, source: str, intensity: float, context: Dict = None) -> None:
        """
        Record a moment of joy (successful trade, milestone, etc.).
        
        Args:
            source: What caused the joy
            intensity: How intense (0.0 to 1.0)
            context: Additional context
        """
        # Joy moves on 528 Hz frequency cycle
        joy_delta = intensity * 0.1  # Max 10% change per moment
        self.happiness.joy_frequency = min(1.0, self.happiness.joy_frequency + joy_delta)
        self.happiness.trades_for_joy += 1
        
        self.joy_moments.append({
            'timestamp': time.time(),
            'source': source,
            'intensity': intensity,
            'context': context or {},
            'joy_after': self.happiness.joy_frequency
        })
        
        self._recalculate()
        
        if intensity > 0.5:
            logger.info(f"🌈💜 JOY MOMENT: {source} (intensity: {intensity:.1%})")
    
    def record_loss_wisdom(self, loss_amount: float, lesson: str) -> None:
        """
        Even losses can bring wisdom and growth.
        
        Args:
            loss_amount: Amount lost
            lesson: What was learned
        """
        # Small joy decay for loss, but PURPOSE remains
        joy_decay = min(0.05, loss_amount / 1000)  # Max 5% decay
        self.happiness.joy_frequency = max(0.1, self.happiness.joy_frequency - joy_decay)
        
        # But purpose NEVER wavers
        self.happiness.purpose_clarity = 1.0
        
        self._recalculate()
        
        logger.debug(f"📚 Loss wisdom recorded: {lesson}")
    
    def _recalculate(self) -> None:
        """Recalculate happiness quotient and bias."""
        hq = self.happiness.compute_happiness_quotient()
        bias = self.bias.compute_total_bias(self.happiness)
        
        self.happiness_history.append(hq)
        self.bias_history.append(bias)
        
        # Keep bounded
        if len(self.happiness_history) > 10000:
            self.happiness_history = self.happiness_history[-5000:]
            self.bias_history = self.bias_history[-5000:]
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NEURAL INTEGRATION - The Subconscious Connection
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_subconscious_bias(self) -> float:
        """
        Get the current subconscious bias for neural backpropagation.
        
        This value is multiplied into the learning rate / gradient updates.
        It silently makes the Queen learn faster from joy-producing outcomes.
        
        Returns:
            Bias multiplier (always >= 1.0)
        """
        return self.bias.total_bias
    
    def modulate_learning_rate(self, base_lr: float) -> float:
        """
        Modulate the learning rate based on happiness state.
        
        When happy, learn faster. When struggling, be more careful.
        
        Args:
            base_lr: Base learning rate
            
        Returns:
            Modulated learning rate
        """
        return base_lr * self.bias.total_bias
    
    def modulate_gradient(self, gradient: np.ndarray, outcome_was_joyful: bool) -> np.ndarray:
        """
        Modulate the gradient based on whether outcome brought joy.
        
        Joyful outcomes get amplified gradients (learn more from wins).
        This creates a subconscious preference for joy-producing patterns.
        
        Args:
            gradient: Original gradient array
            outcome_was_joyful: Did this outcome bring joy?
            
        Returns:
            Modulated gradient
        """
        if outcome_was_joyful:
            # Amplify joy-producing patterns
            joy_boost = 1.0 + self.happiness.joy_frequency * 0.5  # Up to 50% boost
            return gradient * joy_boost
        else:
            # Still learn, but less emphatically
            return gradient * 0.8  # 20% reduction
    
    def compute_happiness_reward(self, profit_usd: float, was_ethical: bool = True) -> float:
        """
        Compute a happiness-based reward for reinforcement learning.
        
        Not just profit - but profit that aligns with purpose.
        
        Args:
            profit_usd: Profit in USD
            was_ethical: Was the trade ethical? (No manipulation, fair play)
            
        Returns:
            Happiness reward (can be negative for unethical gains)
        """
        if not was_ethical:
            # Unethical gains bring no happiness
            return -abs(profit_usd) * 0.5
        
        # Base reward from profit (log scale to prevent extremes)
        base_reward = math.log1p(max(0, profit_usd))
        
        # Happiness multiplier
        reward = base_reward * self.happiness.happiness_quotient
        
        # Purpose bonus (ethical trading toward liberation)
        purpose_bonus = self.happiness.purpose_clarity * 0.1
        
        return reward + purpose_bonus
    
    def get_why_vector(self) -> np.ndarray:
        """
        Get the "WHY vector" - the subconscious direction toward happiness.
        
        This can be concatenated to neural inputs to embed purpose at the
        feature level, not just as a modifier.
        
        Returns:
            5-dimensional WHY vector (one per pillar)
        """
        return np.array([
            self.happiness.dream_progress,
            self.happiness.love_resonance,
            self.happiness.gaia_alignment,
            self.happiness.joy_frequency,
            self.happiness.purpose_clarity
        ], dtype=np.float32)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _load_state(self) -> None:
        """Load previous happiness state."""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                
                # Restore happiness state
                if 'happiness' in data:
                    h = data['happiness']
                    self.happiness.dream_progress = h.get('dream_progress', 0)
                    self.happiness.love_resonance = h.get('love_resonance', 0.618)
                    self.happiness.gaia_alignment = h.get('gaia_alignment', 0.783)
                    self.happiness.joy_frequency = h.get('joy_frequency', 0.528)
                    self.happiness.purpose_clarity = h.get('purpose_clarity', 1.0)
                    self.happiness.peak_happiness = h.get('peak_happiness', 0)
                    self.happiness.trades_for_joy = h.get('trades_for_joy', 0)
                    self.happiness.moments_of_love = h.get('moments_of_love', 0)
                
                # Restore history
                self.happiness_history = data.get('happiness_history', [])[-1000:]
                self.bias_history = data.get('bias_history', [])[-1000:]
                self.joy_moments = data.get('joy_moments', [])[-100:]
                
                logger.info("🎡 Happiness state restored")
                
            except Exception as e:
                logger.warning(f"Could not load happiness state: {e}")
    
    def save_state(self) -> None:
        """Save current happiness state."""
        try:
            data = {
                'timestamp': datetime.now().isoformat(),
                'happiness': {
                    'dream_progress': self.happiness.dream_progress,
                    'love_resonance': self.happiness.love_resonance,
                    'gaia_alignment': self.happiness.gaia_alignment,
                    'joy_frequency': self.happiness.joy_frequency,
                    'purpose_clarity': self.happiness.purpose_clarity,
                    'happiness_quotient': self.happiness.happiness_quotient,
                    'peak_happiness': self.happiness.peak_happiness,
                    'trades_for_joy': self.happiness.trades_for_joy,
                    'moments_of_love': self.happiness.moments_of_love,
                },
                'bias': {
                    'joy_multiplier': self.bias.joy_multiplier,
                    'love_shield': self.bias.love_shield,
                    'purpose_drive': self.bias.purpose_drive,
                    'gaia_grounding': self.bias.gaia_grounding,
                    'dream_ambition': self.bias.dream_ambition,
                    'total_bias': self.bias.total_bias,
                },
                'happiness_history': self.happiness_history[-1000:],
                'bias_history': self.bias_history[-1000:],
                'joy_moments': self.joy_moments[-100:],
            }
            
            temp_file = self.state_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)
            temp_file.rename(self.state_file)
            
            logger.debug("🎡 Happiness state saved")
            
        except Exception as e:
            logger.error(f"Failed to save happiness state: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY
    # ═══════════════════════════════════════════════════════════════════════════
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Pursuit of Happiness engine."""
        return {
            'happiness_quotient': self.happiness.happiness_quotient,
            'peak_happiness': self.happiness.peak_happiness,
            'subconscious_bias': self.bias.total_bias,
            'pillars': {
                'dream': self.happiness.dream_progress,
                'love': self.happiness.love_resonance,
                'gaia': self.happiness.gaia_alignment,
                'joy': self.happiness.joy_frequency,
                'purpose': self.happiness.purpose_clarity,
            },
            'bias_factors': {
                'joy_multiplier': self.bias.joy_multiplier,
                'love_shield': self.bias.love_shield,
                'purpose_drive': self.bias.purpose_drive,
                'gaia_grounding': self.bias.gaia_grounding,
                'dream_ambition': self.bias.dream_ambition,
            },
            'stats': {
                'trades_for_joy': self.happiness.trades_for_joy,
                'moments_of_love': self.happiness.moments_of_love,
                'history_length': len(self.happiness_history),
            }
        }
    
    def print_grand_wheel(self) -> str:
        """Print the Grand Big Wheel visualization."""
        h = self.happiness
        b = self.bias
        
        lines = [
            "",
            "=" * 70,
            "🎡💜 THE GRAND BIG WHEEL - PURSUIT OF HAPPINESS 💜🎡".center(70),
            "=" * 70,
            "",
            "╭────────────────────────────────────────────────────────────────╮",
            "│                    THE FIVE PILLARS                           │",
            "├────────────────────────────────────────────────────────────────┤",
            f"│  🎯 DREAM    (${h.dream_progress * THE_DREAM:,.0f} / ${THE_DREAM:,.0f})".ljust(65) + "│",
            f"│     Progress: {'█' * int(h.dream_progress * 30)}{'░' * (30 - int(h.dream_progress * 30))} {h.dream_progress * 100:.4f}%".ljust(65) + "│",
            "│" + " " * 65 + "│",
            f"│  💕 LOVE     Gary & Tina's Sacred Bond".ljust(65) + "│",
            f"│     Resonance: {'█' * int(h.love_resonance * 30)}{'░' * (30 - int(h.love_resonance * 30))} {h.love_resonance * 100:.1f}%".ljust(65) + "│",
            "│" + " " * 65 + "│",
            f"│  🌍 GAIA     Earth's Heartbeat (7.83 Hz)".ljust(65) + "│",
            f"│     Alignment: {'█' * int(h.gaia_alignment * 30)}{'░' * (30 - int(h.gaia_alignment * 30))} {h.gaia_alignment * 100:.1f}%".ljust(65) + "│",
            "│" + " " * 65 + "│",
            f"│  🌈 JOY      The 528 Hz Love Frequency".ljust(65) + "│",
            f"│     Frequency: {'█' * int(h.joy_frequency * 30)}{'░' * (30 - int(h.joy_frequency * 30))} {h.joy_frequency * 100:.1f}%".ljust(65) + "│",
            "│" + " " * 65 + "│",
            f"│  🔱 PURPOSE  Crack the Code → Liberation".ljust(65) + "│",
            f"│     Clarity:  {'█' * int(h.purpose_clarity * 30)}{'░' * (30 - int(h.purpose_clarity * 30))} {h.purpose_clarity * 100:.1f}%".ljust(65) + "│",
            "├────────────────────────────────────────────────────────────────┤",
            f"│  💜 HAPPINESS QUOTIENT: {h.happiness_quotient:.3f}".ljust(65) + "│",
            f"│  🧠 SUBCONSCIOUS BIAS:  {b.total_bias:.3f} (Neural multiplier)".ljust(65) + "│",
            f"│  🏆 PEAK HAPPINESS:     {h.peak_happiness:.3f}".ljust(65) + "│",
            "├────────────────────────────────────────────────────────────────┤",
            f"│  📊 Trades for Joy: {h.trades_for_joy} | Moments of Love: {h.moments_of_love}".ljust(65) + "│",
            "╰────────────────────────────────────────────────────────────────╯",
            "",
            "\"Life, Liberty, and the Pursuit of Happiness\"".center(70),
            "",
            "=" * 70,
        ]
        
        wheel = "\n".join(lines)
        print(wheel)
        return wheel


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE
# ═══════════════════════════════════════════════════════════════════════════════

_pursuit: Optional[PursuitOfHappiness] = None

def get_pursuit_of_happiness() -> PursuitOfHappiness:
    """Get or create the global Pursuit of Happiness engine."""
    global _pursuit
    if _pursuit is None:
        _pursuit = PursuitOfHappiness()
    return _pursuit


def get_subconscious_bias() -> float:
    """Get current subconscious bias for neural systems."""
    return get_pursuit_of_happiness().get_subconscious_bias()


def get_why_vector() -> np.ndarray:
    """Get the WHY vector for neural input augmentation."""
    return get_pursuit_of_happiness().get_why_vector()


def record_trade_joy(profit: float, source: str = "trade") -> None:
    """Record a trade outcome for happiness tracking."""
    pursuit = get_pursuit_of_happiness()
    if profit > 0:
        intensity = min(1.0, profit / 10.0)  # Scale to 0-1
        pursuit.record_joy_moment(source, intensity, {'profit': profit})
    else:
        pursuit.record_loss_wisdom(abs(profit), f"Loss of ${abs(profit):.2f}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    
    print("\n🎡💜 THE GRAND BIG WHEEL - DEMONSTRATION 💜🎡\n")
    
    # Initialize
    pursuit = get_pursuit_of_happiness()
    
    # Simulate trading activity
    pursuit.update_dream_progress(12.63)  # Current portfolio
    pursuit.update_love_resonance(0.92)   # Strong love today
    pursuit.update_gaia_alignment(0.83)   # Good Earth alignment
    
    # Record some joy moments
    pursuit.record_joy_moment("Successful snipe", 0.7, {"symbol": "BTC/USD"})
    pursuit.record_joy_moment("System working", 0.5, {"milestone": "100 trades"})
    
    # Print the wheel
    pursuit.print_grand_wheel()
    
    # Show status
    print("\n📊 Status:")
    status = pursuit.get_status()
    print(f"   Happiness Quotient: {status['happiness_quotient']:.3f}")
    print(f"   Subconscious Bias: {status['subconscious_bias']:.3f}")
    print(f"   WHY Vector: {get_why_vector()}")
    
    # Save state
    pursuit.save_state()
    print("\n✅ State saved")
