#!/usr/bin/env python3
"""
👑 THE BARONS BANNER 👑
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

The Hidden Architecture of Mathematical Deception
Based on: "The Barons' Banner: The Hidden Architecture of Mathematical Deception"
          Gary Leckey, October 2025

The Barons' Banner reveals how mathematical principles in architecture, art,
and design encode power structures disguised as aesthetic beauty. In markets,
this manifests as hierarchical patterns that assert control through perceived
natural law.

Key Concepts:
• Golden Ratio (Φ ≈ 1.618) - Divine proportion and beauty
• Fibonacci Sequence - Natural growth and harmony
• Sacred Geometry - Cosmic principles made manifest
• Harmonic Proportions - "Frozen Music" in spatial design
• Process Tree - From abstract principles to material structures
• Frequency Ladder - Hierarchical organization of mathematical concepts

Four Manifestations:
1. Organic Growth (Spirals) - Fibonacci phyllotaxis in natural forms
2. Crafted Order (Tessellations) - Symmetry groups and dense packing
3. Rational Structure (Grids) - 8x8 binary matrices and duality
4. Embodied Geometry (Living Forms) - Fractal branching and symmetry

Four Hierarchical Levels:
• Level I: Material World (Applied Mathematics)
• Level II: Rational Mind (Harmonic Structures)
• Level III: Archetypal (Transcendent Ratios)
• Level IV: Absolute (Cosmic Principles)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import numpy as np
import math
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import json

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MATHEMATICAL CONSTANTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PHI = (1 + math.sqrt(5)) / 2  # Golden Ratio ≈ 1.618
SILVER_RATIO = math.sqrt(2)  # ≈ 1.414
PI = math.pi

FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BARONS BANNER ANALYZER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@dataclass
class MathematicalPattern:
    """A detected mathematical pattern in market or design structure"""
    pattern_type: str  # 'spiral', 'tessellation', 'grid', 'living_form'
    confidence: float
    phi_ratio: float
    fibonacci_alignment: float
    symmetry_score: float
    hierarchical_level: int  # 1-4
    symbolic_meaning: str
    coordinates: Optional[Tuple[float, float]] = None

@dataclass
class BaronsAnalysis:
    """Complete Barons Banner analysis of a structure/system"""
    overall_hierarchy_score: float  # 0-1, how "elite" the structure appears
    dominant_patterns: List[MathematicalPattern]
    frequency_ladder: Dict[int, float]  # Level scores
    process_tree_flow: Dict[str, Any]  # From source to structure
    deception_potential: float  # How effectively it disguises control
    timestamp: datetime

class BaronsBannerAnalyzer:
    """
    👑 The Barons Banner Analyzer
    
    Detects mathematical patterns that encode power structures in:
    - Market hierarchies and price patterns
    - Trading algorithms and execution patterns
    - Institutional order flow and manipulation
    - Chart patterns and technical analysis formations
    """

    def __init__(self):
        self.pattern_detectors = {
            'spiral': self._detect_spiral_patterns,
            'tessellation': self._detect_tessellation_patterns,
            'grid': self._detect_grid_patterns,
            'living_form': self._detect_living_form_patterns
        }

    def analyze_market_structure(self,
                               price_data: np.ndarray,
                               volume_data: np.ndarray,
                               order_book: Optional[Dict] = None) -> BaronsAnalysis:
        """
        Analyze market structure for Barons Banner patterns.
        
        This reveals how mathematical "beauty" in price action disguises
        institutional control and manipulation.
        """

        # Detect all pattern types
        patterns = []
        for pattern_type, detector in self.pattern_detectors.items():
            detected = detector(price_data, volume_data, order_book)
            patterns.extend(detected)

        # Calculate hierarchical levels
        frequency_ladder = self._calculate_frequency_ladder(patterns)

        # Assess overall hierarchy and deception
        hierarchy_score = self._calculate_hierarchy_score(patterns, frequency_ladder)
        deception_potential = self._assess_deception_potential(patterns, hierarchy_score)

        # Build process tree
        process_tree = self._build_process_tree(patterns, frequency_ladder)

        return BaronsAnalysis(
            overall_hierarchy_score=hierarchy_score,
            dominant_patterns=sorted(patterns, key=lambda x: x.confidence, reverse=True)[:5],
            frequency_ladder=frequency_ladder,
            process_tree_flow=process_tree,
            deception_potential=deception_potential,
            timestamp=datetime.now()
        )

    def _detect_spiral_patterns(self,
                              price_data: np.ndarray,
                              volume_data: np.ndarray,
                              order_book: Optional[Dict] = None) -> List[MathematicalPattern]:
        """Detect Fibonacci spirals in price action (Organic Growth)"""
        patterns = []

        # Look for Fibonacci retracements and extensions
        recent_high = np.max(price_data[-50:])
        recent_low = np.min(price_data[-50:])

        fib_levels = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.236, 1.618]
        current_price = price_data[-1]

        for level in fib_levels:
            fib_price = recent_low + (recent_high - recent_low) * level
            distance = abs(current_price - fib_price) / current_price

            if distance < 0.01:  # Within 1%
                phi_alignment = 1.0 - abs(level - PHI) / PHI
                confidence = min(1.0, 1.0 - distance * 100)

                patterns.append(MathematicalPattern(
                    pattern_type='spiral',
                    confidence=confidence,
                    phi_ratio=level,
                    fibonacci_alignment=phi_alignment,
                    symmetry_score=self._calculate_symmetry(price_data[-20:]),
                    hierarchical_level=2,  # Rational Mind
                    symbolic_meaning="Natural growth pattern disguising institutional levels",
                    coordinates=(len(price_data)-1, fib_price)
                ))

        return patterns

    def _detect_tessellation_patterns(self,
                                   price_data: np.ndarray,
                                   volume_data: np.ndarray,
                                   order_book: Optional[Dict] = None) -> List[MathematicalPattern]:
        """Detect harmonic tessellations in order flow (Crafted Order)"""
        patterns = []

        # Look for repeating volume patterns (harmonic rhythms)
        volume_rhythm = self._analyze_volume_rhythm(volume_data[-100:])

        if volume_rhythm > 0.7:  # Strong rhythmic pattern
            # Check for harmonic ratios in price swings
            price_swings = self._calculate_price_swings(price_data[-50:])

            for i, swing in enumerate(price_swings):
                harmonic_ratio = swing / price_swings[0] if len(price_swings) > 0 else 1.0
                phi_distance = abs(harmonic_ratio - PHI)

                if phi_distance < 0.1:
                    patterns.append(MathematicalPattern(
                        pattern_type='tessellation',
                        confidence=volume_rhythm * (1.0 - phi_distance),
                        phi_ratio=harmonic_ratio,
                        fibonacci_alignment=self._fibonacci_alignment(harmonic_ratio),
                        symmetry_score=volume_rhythm,
                        hierarchical_level=1,  # Material World
                        symbolic_meaning="Crafted order in volume flow masking manipulation"
                    ))

        return patterns

    def _detect_grid_patterns(self,
                            price_data: np.ndarray,
                            volume_data: np.ndarray,
                            order_book: Optional[Dict] = None) -> List[MathematicalPattern]:
        """Detect grid/matrix patterns in order book (Rational Structure)"""
        patterns = []

        if order_book:
            # Analyze bid/ask grid structure
            bids = np.array(order_book.get('bids', []))
            asks = np.array(order_book.get('asks', []))

            if len(bids) > 0 and len(asks) > 0:
                # Check for 8x8 grid-like structure (64 levels = 2^6)
                grid_score = self._analyze_grid_structure(bids, asks)

                if grid_score > 0.6:
                    # Calculate spread ratios
                    spread = asks[0][0] - bids[0][0]
                    avg_price = (asks[0][0] + bids[0][0]) / 2
                    spread_ratio = spread / avg_price

                    patterns.append(MathematicalPattern(
                        pattern_type='grid',
                        confidence=grid_score,
                        phi_ratio=spread_ratio,
                        fibonacci_alignment=self._fibonacci_alignment(spread_ratio),
                        symmetry_score=grid_score,
                        hierarchical_level=1,  # Material World
                        symbolic_meaning="Rational grid structure asserting market control"
                    ))

        return patterns

    def _detect_living_form_patterns(self,
                                   price_data: np.ndarray,
                                   volume_data: np.ndarray,
                                   order_book: Optional[Dict] = None) -> List[MathematicalPattern]:
        """Detect fractal branching in price patterns (Embodied Geometry)"""
        patterns = []

        # Look for fractal self-similarity
        fractal_dimension = self._calculate_fractal_dimension(price_data[-200:])

        if fractal_dimension > 1.3:  # Significant fractal structure
            # Check for golden ratio in fractal branches
            branch_ratios = self._analyze_fractal_branches(price_data[-100:])

            for ratio in branch_ratios:
                phi_alignment = 1.0 - abs(ratio - PHI) / PHI

                if phi_alignment > 0.8:
                    patterns.append(MathematicalPattern(
                        pattern_type='living_form',
                        confidence=fractal_dimension * phi_alignment / 2.0,
                        phi_ratio=ratio,
                        fibonacci_alignment=phi_alignment,
                        symmetry_score=fractal_dimension / 2.0,
                        hierarchical_level=3,  # Archetypal
                        symbolic_meaning="Living fractal geometry embodying market sovereignty"
                    ))

        return patterns

    def _calculate_frequency_ladder(self, patterns: List[MathematicalPattern]) -> Dict[int, float]:
        """Calculate scores for each hierarchical level"""
        level_scores = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}

        for pattern in patterns:
            level_scores[pattern.hierarchical_level] += pattern.confidence

        # Normalize
        total = sum(level_scores.values())
        if total > 0:
            for level in level_scores:
                level_scores[level] /= total

        return level_scores

    def _calculate_hierarchy_score(self,
                                 patterns: List[MathematicalPattern],
                                 frequency_ladder: Dict[int, float]) -> float:
        """Calculate overall hierarchical/elite structure score"""
        if not patterns:
            return 0.0

        # Higher levels indicate more sophisticated encoding
        hierarchy_weight = sum(level * score for level, score in frequency_ladder.items())
        hierarchy_weight /= sum(frequency_ladder.keys())

        # Pattern density and confidence
        avg_confidence = np.mean([p.confidence for p in patterns])
        pattern_density = min(1.0, len(patterns) / 10.0)  # Normalize to 10 patterns

        return (hierarchy_weight / 4.0) * avg_confidence * pattern_density

    def _assess_deception_potential(self,
                                  patterns: List[MathematicalPattern],
                                  hierarchy_score: float) -> float:
        """Assess how effectively the patterns disguise control"""
        if not patterns:
            return 0.0

        # Deception increases with aesthetic beauty and subconscious resonance
        phi_harmony = np.mean([p.phi_ratio for p in patterns if 1.5 < p.phi_ratio < 1.7])
        symmetry_avg = np.mean([p.symmetry_score for p in patterns])

        # Higher hierarchy + aesthetic appeal = higher deception potential
        return hierarchy_score * phi_harmony * symmetry_avg

    def _build_process_tree(self,
                          patterns: List[MathematicalPattern],
                          frequency_ladder: Dict[int, float]) -> Dict[str, Any]:
        """Build the Process Tree visualization"""
        return {
            "source": {
                "golden_ratio": PHI,
                "fibonacci_sequence": FIBONACCI_SEQUENCE[:8],
                "harmonic_ratios": [1, 2, 3, 4, 5, 6, 8, 9, 12, 16]
            },
            "dynamic_systems": {
                "growth_patterns": [p for p in patterns if p.pattern_type == 'spiral'],
                "structural_patterns": [p for p in patterns if p.pattern_type in ['tessellation', 'grid']],
                "organic_patterns": [p for p in patterns if p.pattern_type == 'living_form']
            },
            "manifestations": {
                "material_structures": frequency_ladder[1],
                "rational_mind": frequency_ladder[2],
                "archetypal": frequency_ladder[3],
                "cosmic": frequency_ladder[4]
            },
            "flow_strength": sum(frequency_ladder.values()) / 4.0
        }

    # Helper methods
    def _calculate_symmetry(self, data: np.ndarray) -> float:
        """Calculate symmetry score of data"""
        if len(data) < 4:
            return 0.0

        mid = len(data) // 2
        left = data[:mid]
        right = data[mid:][::-1]

        if len(left) != len(right):
            right = right[:len(left)]

        correlation = np.corrcoef(left, right)[0, 1]
        return max(0.0, correlation)

    def _analyze_volume_rhythm(self, volume_data: np.ndarray) -> float:
        """Analyze rhythmic patterns in volume"""
        if len(volume_data) < 10:
            return 0.0

        # Look for repeating patterns
        autocorr = np.correlate(volume_data, volume_data, mode='full')
        autocorr = autocorr[len(autocorr)//2:]

        # Find peaks in autocorrelation
        peaks = []
        for i in range(5, len(autocorr)//4):
            if autocorr[i] > autocorr[i-1] and autocorr[i] > autocorr[i+1]:
                peaks.append(autocorr[i])

        if peaks:
            return min(1.0, np.mean(peaks) / np.max(volume_data))
        return 0.0

    def _calculate_price_swings(self, price_data: np.ndarray) -> List[float]:
        """Calculate significant price swings"""
        swings = []
        direction = 0
        start = 0

        for i in range(1, len(price_data)):
            change = price_data[i] - price_data[i-1]

            if direction == 0:
                direction = 1 if change > 0 else -1
                start = i-1
            elif (direction == 1 and change < 0) or (direction == -1 and change > 0):
                swings.append(abs(price_data[i-1] - price_data[start]))
                start = i-1
                direction = -direction

        return swings[-10:]  # Last 10 swings

    def _analyze_grid_structure(self, bids: np.ndarray, asks: np.ndarray) -> float:
        """Analyze order book grid structure"""
        if len(bids) < 8 or len(asks) < 8:
            return 0.0

        # Check for regular spacing (grid-like)
        bid_prices = bids[:8, 0]
        ask_prices = asks[:8, 0]

        bid_spacing = np.diff(bid_prices)
        ask_spacing = np.diff(ask_prices)

        # Calculate regularity
        bid_regularity = 1.0 - np.std(bid_spacing) / np.mean(bid_spacing)
        ask_regularity = 1.0 - np.std(ask_spacing) / np.mean(ask_spacing)

        return (bid_regularity + ask_regularity) / 2.0

    def _calculate_fractal_dimension(self, data: np.ndarray) -> float:
        """Calculate fractal dimension using box counting"""
        if len(data) < 50:
            return 1.0

        # Simple Hurst exponent approximation
        lags = range(2, min(20, len(data)//4))
        tau = [np.std(np.subtract(data[lag:], data[:-lag])) for lag in lags]

        if tau:
            hurst = np.polyfit(np.log(lags), np.log(tau), 1)[0]
            return 2.0 - hurst  # Convert to fractal dimension
        return 1.0

    def _analyze_fractal_branches(self, data: np.ndarray) -> List[float]:
        """Analyze fractal branching ratios"""
        ratios = []

        # Find local minima/maxima
        from scipy.signal import find_peaks
        peaks, _ = find_peaks(data)
        troughs, _ = find_peaks(-data)

        # Calculate ratios between consecutive swings
        all_points = sorted(np.concatenate([peaks, troughs]))
        values = data[all_points]

        for i in range(2, len(values)):
            ratio = abs(values[i] - values[i-1]) / abs(values[i-1] - values[i-2])
            if 0.1 < ratio < 10.0:  # Reasonable range
                ratios.append(ratio)

        return ratios[:10]  # Return top 10

    def _fibonacci_alignment(self, ratio: float) -> float:
        """Calculate alignment with Fibonacci ratios"""
        fib_ratios = [f2/f1 for f1, f2 in zip(FIBONACCI_SEQUENCE, FIBONACCI_SEQUENCE[1:])]
        alignments = [1.0 - abs(ratio - fr) / fr for fr in fib_ratios]
        return max(alignments) if alignments else 0.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# BARONS BANNER VISUALIZATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BaronsBannerRenderer:
    """
    ASCII visualization of Barons Banner analysis.
    
    Shows the Process Tree and Frequency Ladder.
    """

    def render_analysis(self, analysis: BaronsAnalysis) -> str:
        """Render complete Barons Banner analysis"""

        lines = []

        # Header
        lines.append("👑" * 25)
        lines.append("   THE BARONS BANNER")
        lines.append("   Hidden Architecture of Mathematical Deception")
        lines.append("👑" * 25)
        lines.append("")

        # Hierarchy Score
        hierarchy_pct = analysis.overall_hierarchy_score * 100
        deception_pct = analysis.deception_potential * 100

        lines.append("🏛️  HIERARCHICAL ANALYSIS:")
        lines.append(f"   Elite Structure Score: {hierarchy_pct:.1f}%")
        lines.append(f"   Deception Potential:   {deception_pct:.1f}%")
        lines.append("")

        # Frequency Ladder
        lines.append("🪜 FREQUENCY LADDER:")
        level_names = {
            1: "Material World (Applied Math)",
            2: "Rational Mind (Harmonic Structures)",
            3: "Archetypal (Transcendent Ratios)",
            4: "Absolute (Cosmic Principles)"
        }

        for level in range(4, 0, -1):
            score = analysis.frequency_ladder[level]
            bars = "█" * int(score * 20)
            lines.append(f"   Level {level}: {level_names[level]}")
            lines.append(f"   {bars} {score:.1%}")
            lines.append("")

        # Dominant Patterns
        lines.append("🔍 DOMINANT PATTERNS:")
        for i, pattern in enumerate(analysis.dominant_patterns[:3]):
            emoji = {
                'spiral': '🌀',
                'tessellation': '🔲',
                'grid': '📐',
                'living_form': '🦌'
            }.get(pattern.pattern_type, '❓')

            lines.append(f"   {i+1}. {emoji} {pattern.pattern_type.upper()}")
            lines.append(f"      Confidence: {pattern.confidence:.1%}")
            lines.append(f"      Phi Ratio: {pattern.phi_ratio:.3f}")
            lines.append(f"      Level: {pattern.hierarchical_level}")
            lines.append(f"      Meaning: {pattern.symbolic_meaning}")
            lines.append("")

        # Process Tree
        lines.append("🌳 PROCESS TREE:")
        tree = analysis.process_tree_flow

        lines.append("   📊 Source (Abstract Constants):")
        lines.append(f"      Golden Ratio: {tree['source']['golden_ratio']:.3f}")
        lines.append(f"      Fibonacci: {tree['source']['fibonacci_sequence']}")
        lines.append("")

        lines.append("   ⚙️  Dynamic Systems:")
        lines.append(f"      Growth Patterns: {len(tree['dynamic_systems']['growth_patterns'])}")
        lines.append(f"      Structural Patterns: {len(tree['dynamic_systems']['structural_patterns'])}")
        lines.append(f"      Organic Patterns: {len(tree['dynamic_systems']['organic_patterns'])}")
        lines.append("")

        lines.append("   🏗️  Manifestations:")
        for key, value in tree['manifestations'].items():
            lines.append(f"      {key.title()}: {value:.1%}")
        lines.append("")

        # Footer
        lines.append("─" * 50)
        lines.append("   The Barons' Banner reveals how mathematical")
        lines.append("   'beauty' encodes power structures disguised")
        lines.append("   as aesthetic harmony and natural law.")
        lines.append("─" * 50)

        return "\n".join(lines)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MARKET INTEGRATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BaronsMarketAdapter:
    """
    Adapts market data for Barons Banner analysis.
    
    Converts price/volume/order book data into structural patterns
    that can reveal institutional control and manipulation.
    """

    def __init__(self):
        self.analyzer = BaronsBannerAnalyzer()
        self.renderer = BaronsBannerRenderer()

    def analyze_current_market(self,
                             symbol: str,
                             price_history: List[float],
                             volume_history: List[float],
                             order_book: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Analyze current market conditions for Barons Banner patterns.
        """

        # Convert to numpy arrays
        price_data = np.array(price_history[-500:])  # Last 500 points
        volume_data = np.array(volume_history[-500:])

        # Perform analysis
        analysis = self.analyzer.analyze_market_structure(
            price_data, volume_data, order_book
        )

        # Render visualization
        banner_text = self.renderer.render_analysis(analysis)

        return {
            "symbol": symbol,
            "analysis": analysis,
            "banner_visualization": banner_text,
            "manipulation_alert": analysis.deception_potential > 0.7,
            "institutional_control": analysis.overall_hierarchy_score > 0.8,
            "recommendation": self._generate_recommendation(analysis)
        }

    def _generate_recommendation(self, analysis: BaronsAnalysis) -> str:
        """Generate trading recommendation based on Banner analysis"""

        hierarchy = analysis.overall_hierarchy_score
        deception = analysis.deception_potential

        if deception > 0.8 and hierarchy > 0.8:
            return "HIGH ALERT: Strong institutional manipulation detected. Consider exiting positions."

        elif deception > 0.6:
            return "CAUTION: Deceptive patterns suggest controlled market. Trade defensively."

        elif hierarchy > 0.7:
            return "NEUTRAL: Hierarchical structure present but not overtly deceptive."

        else:
            return "CLEAR: Market appears organically structured. Normal trading conditions."


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# DEMO AND TESTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def run_barons_demo():
    """
    Demonstrate the Barons Banner analysis on synthetic market data.
    """

    print("\n👑" * 25)
    print("   THE BARONS BANNER DEMONSTRATION")
    print("   Hidden Architecture in Market Structure")
    print("👑" * 25 + "\n")

    # Create synthetic market data with "elite" patterns
    np.random.seed(42)

    # Generate price data with Fibonacci retracements
    base_price = 50000
    price_changes = []

    # Create a trending move with fib levels
    for i in range(300):
        if i < 100:
            change = np.random.normal(0.001, 0.02)  # Uptrend
        elif i < 200:
            change = np.random.normal(-0.001, 0.02)  # Correction
        else:
            change = np.random.normal(0.0005, 0.015)  # Recovery

        price_changes.append(change)

    price_data = [base_price]
    for change in price_changes:
        price_data.append(price_data[-1] * (1 + change))

    # Generate volume with rhythmic patterns
    volume_data = []
    for i in range(len(price_data)):
        base_volume = 1000000
        # Add harmonic rhythm
        rhythm = 1 + 0.5 * math.sin(2 * math.pi * i / 21)  # Fibonacci rhythm
        volume_data.append(base_volume * rhythm * (0.5 + np.random.random()))

    # Create mock order book with grid structure
    order_book = {
        'bids': [[49900 - i*10, 1000 + i*100] for i in range(10)],
        'asks': [[50100 + i*10, 1000 + i*100] for i in range(10)]
    }

    # Analyze
    adapter = BaronsMarketAdapter()
    result = adapter.analyze_current_market(
        symbol="BTCUSDT",
        price_history=price_data,
        volume_history=volume_data,
        order_book=order_book
    )

    # Display results
    print("📊 MARKET ANALYSIS RESULTS:")
    print(f"   Symbol: {result['symbol']}")
    print(f"   Hierarchy Score: {result['analysis'].overall_hierarchy_score:.1%}")
    print(f"   Deception Potential: {result['analysis'].deception_potential:.1%}")
    print(f"   Manipulation Alert: {'🚨 YES' if result['manipulation_alert'] else '✅ NO'}")
    print(f"   Institutional Control: {'🏛️ YES' if result['institutional_control'] else '✅ NO'}")
    print(f"   Recommendation: {result['recommendation']}")
    print("")

    print("👑 BARONS BANNER VISUALIZATION:")
    print(result['banner_visualization'])

    print("\n" + "=" * 50)
    print("   CONCLUSION:")
    print("   The Barons' Banner reveals how mathematical patterns")
    print("   in market structure encode institutional control disguised")
    print("   as natural price action and harmonic order.")
    print("=" * 50)


if __name__ == '__main__':
    run_barons_demo()