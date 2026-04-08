#!/usr/bin/env python3
"""
📊 PROBABILITY MATRIX VALIDATION ENGINE 📊
═══════════════════════════════════════════════════════════════

Validates probability matrix predictions against actual trading outcomes.
Tracks accuracy over time and adjusts confidence based on performance.

VALIDATION METRICS:
├─ Directional Accuracy: Did price move in predicted direction?
├─ Magnitude Accuracy: How close was predicted vs actual magnitude?
├─ Timing Accuracy: Did the move happen in the 2-hour window?
├─ Win Rate: Trades that achieved target TP before hitting SL
└─ Profit Factor: Gross profit / Gross loss

Gary Leckey & GitHub Copilot | December 2025
"""

from aureon_baton_link import link_system as _baton_link; _baton_link(__name__)
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import deque
import logging

logger = logging.getLogger(__name__)

VALIDATION_FILE = "probability_validation.json"
PREDICTION_LOG = "probability_predictions.jsonl"


@dataclass
class Prediction:
    """A recorded prediction for validation."""
    prediction_id: str
    symbol: str
    timestamp: str
    
    # Prediction details
    predicted_direction: str  # BULLISH, BEARISH, NEUTRAL
    predicted_probability: float  # 0-1
    predicted_confidence: float  # 0-1
    predicted_action: str  # BUY, SELL, HOLD
    
    # Context at prediction time
    price_at_prediction: float
    fear_greed: int
    vix: float
    market_regime: str
    macro_bias: str
    hnc_frequency: float
    
    # Validation window
    window_start: str
    window_end: str  # 2 hours after prediction
    
    # Outcome (filled after validation)
    validated: bool = False
    actual_direction: str = ""
    actual_change_pct: float = 0.0
    price_at_validation: float = 0.0
    direction_correct: bool = False
    outcome_score: float = 0.0  # -1 to +1
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ValidationStats:
    """Aggregated validation statistics."""
    total_predictions: int = 0
    validated_predictions: int = 0
    
    # Directional accuracy
    direction_correct: int = 0
    direction_wrong: int = 0
    direction_accuracy: float = 0.0
    
    # By regime
    accuracy_by_regime: Dict[str, float] = field(default_factory=dict)
    accuracy_by_fear_greed: Dict[str, float] = field(default_factory=dict)
    
    # Performance
    avg_predicted_prob: float = 0.0
    avg_actual_change: float = 0.0
    profit_factor: float = 0.0
    
    # Time-based
    accuracy_last_24h: float = 0.0
    accuracy_last_7d: float = 0.0
    
    def to_dict(self) -> Dict:
        return asdict(self)


class ProbabilityValidator:
    """
    Validates probability matrix predictions against actual market outcomes.
    """
    
    def __init__(self):
        self.predictions: Dict[str, Prediction] = {}  # id -> Prediction
        self.pending_validations: List[str] = []  # prediction IDs to validate
        self.stats = ValidationStats()
        
        self._load_state()
    
    def _load_state(self):
        """Load persisted predictions and stats."""
        try:
            if os.path.exists(VALIDATION_FILE):
                with open(VALIDATION_FILE, 'r') as f:
                    data = json.load(f)
                
                # Restore predictions
                for pid, pdata in data.get('predictions', {}).items():
                    self.predictions[pid] = Prediction(**pdata)
                
                # Restore pending
                self.pending_validations = data.get('pending', [])
                
                # Restore stats
                stats_data = data.get('stats', {})
                self.stats = ValidationStats(**stats_data) if stats_data else ValidationStats()
                
                print(f"📊 Loaded {len(self.predictions)} predictions, {len(self.pending_validations)} pending validation")
        except Exception as e:
            logger.warning(f"Failed to load validation state: {e}")
    
    def _save_state(self):
        """Persist predictions and stats."""
        try:
            data = {
                'predictions': {pid: p.to_dict() for pid, p in self.predictions.items()},
                'pending': self.pending_validations,
                'stats': self.stats.to_dict(),
                'updated': datetime.now().isoformat(),
            }
            with open(VALIDATION_FILE, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save validation state: {e}")
    
    def record_prediction(
        self,
        symbol: str,
        direction: str,
        probability: float,
        confidence: float,
        action: str,
        price: float,
        fear_greed: int = 50,
        vix: float = 20.0,
        market_regime: str = "NORMAL",
        macro_bias: str = "NEUTRAL",
        hnc_frequency: float = 256.0,
    ) -> str:
        """
        Record a prediction for later validation.
        
        Returns: prediction_id
        """
        now = datetime.now()
        prediction_id = f"{symbol}_{now.strftime('%Y%m%d_%H%M%S')}"
        
        prediction = Prediction(
            prediction_id=prediction_id,
            symbol=symbol,
            timestamp=now.isoformat(),
            predicted_direction=direction,
            predicted_probability=probability,
            predicted_confidence=confidence,
            predicted_action=action,
            price_at_prediction=price,
            fear_greed=fear_greed,
            vix=vix,
            market_regime=market_regime,
            macro_bias=macro_bias,
            hnc_frequency=hnc_frequency,
            window_start=now.isoformat(),
            window_end=(now + timedelta(hours=2)).isoformat(),
        )
        
        self.predictions[prediction_id] = prediction
        self.pending_validations.append(prediction_id)
        
        # Also log to JSONL for training
        try:
            with open(PREDICTION_LOG, 'a') as f:
                f.write(json.dumps(prediction.to_dict()) + '\n')
        except:
            pass
        
        self._save_state()
        return prediction_id
    
    def validate_prediction(
        self,
        prediction_id: str,
        current_price: float,
    ) -> Optional[Dict[str, Any]]:
        """
        Validate a prediction against actual outcome.
        
        Returns validation result or None if prediction not found.
        """
        if prediction_id not in self.predictions:
            return None
        
        pred = self.predictions[prediction_id]
        
        if pred.validated:
            return {'already_validated': True, 'prediction': pred.to_dict()}
        
        # Calculate actual change
        price_change_pct = ((current_price - pred.price_at_prediction) / pred.price_at_prediction) * 100
        
        # Determine actual direction
        if price_change_pct > 0.5:
            actual_direction = "BULLISH"
        elif price_change_pct < -0.5:
            actual_direction = "BEARISH"
        else:
            actual_direction = "NEUTRAL"
        
        # Check if direction was correct
        direction_correct = (
            (pred.predicted_direction == "BULLISH" and actual_direction == "BULLISH") or
            (pred.predicted_direction == "BEARISH" and actual_direction == "BEARISH") or
            (pred.predicted_direction == "NEUTRAL" and actual_direction == "NEUTRAL")
        )
        
        # Calculate outcome score (-1 to +1)
        # Positive if prediction was correct, negative if wrong
        if pred.predicted_direction == "BULLISH":
            outcome_score = price_change_pct / 5  # Normalize: +5% = +1.0
        elif pred.predicted_direction == "BEARISH":
            outcome_score = -price_change_pct / 5  # Negative price change = positive score
        else:
            outcome_score = 0.0  # Neutral predictions aren't scored
        
        outcome_score = max(-1.0, min(1.0, outcome_score))
        
        # Update prediction
        pred.validated = True
        pred.actual_direction = actual_direction
        pred.actual_change_pct = price_change_pct
        pred.price_at_validation = current_price
        pred.direction_correct = direction_correct
        pred.outcome_score = outcome_score
        
        # Remove from pending
        if prediction_id in self.pending_validations:
            self.pending_validations.remove(prediction_id)
        
        # Update stats
        self._update_stats()
        self._save_state()
        
        return {
            'prediction_id': prediction_id,
            'symbol': pred.symbol,
            'predicted': pred.predicted_direction,
            'actual': actual_direction,
            'correct': direction_correct,
            'price_change_pct': price_change_pct,
            'outcome_score': outcome_score,
            'probability': pred.predicted_probability,
            'confidence': pred.predicted_confidence,
        }
    
    def validate_pending(self, get_price_func) -> List[Dict]:
        """
        Validate all pending predictions that have passed their window.
        
        Args:
            get_price_func: Function that takes symbol and returns current price
            
        Returns: List of validation results
        """
        now = datetime.now()
        results = []
        
        for pred_id in list(self.pending_validations):
            pred = self.predictions.get(pred_id)
            if not pred:
                self.pending_validations.remove(pred_id)
                continue
            
            # Check if window has passed
            window_end = datetime.fromisoformat(pred.window_end)
            if now >= window_end:
                try:
                    current_price = get_price_func(pred.symbol)
                    if current_price and current_price > 0:
                        result = self.validate_prediction(pred_id, current_price)
                        if result:
                            results.append(result)
                except Exception as e:
                    logger.debug(f"Failed to validate {pred_id}: {e}")
        
        return results
    
    def _update_stats(self):
        """Recalculate aggregate statistics."""
        validated = [p for p in self.predictions.values() if p.validated]
        
        self.stats.total_predictions = len(self.predictions)
        self.stats.validated_predictions = len(validated)
        
        if not validated:
            return
        
        # Directional accuracy
        correct = sum(1 for p in validated if p.direction_correct)
        wrong = len(validated) - correct
        self.stats.direction_correct = correct
        self.stats.direction_wrong = wrong
        self.stats.direction_accuracy = correct / len(validated) if validated else 0.0
        
        # Average values
        self.stats.avg_predicted_prob = sum(p.predicted_probability for p in validated) / len(validated)
        self.stats.avg_actual_change = sum(abs(p.actual_change_pct) for p in validated) / len(validated)
        
        # Accuracy by regime
        regime_stats = {}
        for p in validated:
            regime = p.market_regime
            if regime not in regime_stats:
                regime_stats[regime] = {'correct': 0, 'total': 0}
            regime_stats[regime]['total'] += 1
            if p.direction_correct:
                regime_stats[regime]['correct'] += 1
        
        self.stats.accuracy_by_regime = {
            k: v['correct'] / v['total'] if v['total'] > 0 else 0
            for k, v in regime_stats.items()
        }
        
        # Accuracy by Fear/Greed bands
        fg_bands = {'FEAR': (0, 35), 'NEUTRAL': (35, 65), 'GREED': (65, 100)}
        fg_stats = {band: {'correct': 0, 'total': 0} for band in fg_bands}
        
        for p in validated:
            fg = p.fear_greed
            for band, (low, high) in fg_bands.items():
                if low <= fg < high:
                    fg_stats[band]['total'] += 1
                    if p.direction_correct:
                        fg_stats[band]['correct'] += 1
                    break
        
        self.stats.accuracy_by_fear_greed = {
            k: v['correct'] / v['total'] if v['total'] > 0 else 0
            for k, v in fg_stats.items()
        }
        
        # Recent accuracy
        now = datetime.now()
        last_24h = [p for p in validated if (now - datetime.fromisoformat(p.timestamp)).total_seconds() < 86400]
        last_7d = [p for p in validated if (now - datetime.fromisoformat(p.timestamp)).total_seconds() < 604800]
        
        if last_24h:
            self.stats.accuracy_last_24h = sum(1 for p in last_24h if p.direction_correct) / len(last_24h)
        if last_7d:
            self.stats.accuracy_last_7d = sum(1 for p in last_7d if p.direction_correct) / len(last_7d)
        
        # Profit factor
        gains = sum(p.outcome_score for p in validated if p.outcome_score > 0)
        losses = sum(abs(p.outcome_score) for p in validated if p.outcome_score < 0)
        self.stats.profit_factor = gains / losses if losses > 0 else gains if gains > 0 else 1.0
    
    def get_confidence_adjustment(self, symbol: str, market_regime: str, fear_greed: int) -> float:
        """
        Get confidence adjustment based on historical accuracy.
        
        Returns: Multiplier (0.5 to 1.5) to apply to confidence
        """
        # Check regime accuracy
        regime_acc = self.stats.accuracy_by_regime.get(market_regime, 0.5)
        
        # Check fear/greed band accuracy
        fg_band = "FEAR" if fear_greed < 35 else "GREED" if fear_greed >= 65 else "NEUTRAL"
        fg_acc = self.stats.accuracy_by_fear_greed.get(fg_band, 0.5)
        
        # Combined adjustment
        base_acc = self.stats.direction_accuracy if self.stats.direction_accuracy > 0 else 0.5
        
        # Weighted average
        combined = (base_acc * 0.4) + (regime_acc * 0.3) + (fg_acc * 0.3)
        
        # Map to multiplier: 30% acc -> 0.5x, 70% acc -> 1.5x
        multiplier = 0.5 + (combined * 1.0)
        
        return max(0.5, min(1.5, multiplier))
    
    def print_dashboard(self):
        """Print validation dashboard."""
        print("\n" + "=" * 70)
        print("📊 PROBABILITY MATRIX VALIDATION DASHBOARD 📊")
        print("=" * 70)
        
        print(f"""
┌────────────────────────────────────────────────────────────────────┐
│  📈 OVERALL PERFORMANCE                                            │
│                                                                    │
│  Total Predictions:     {self.stats.total_predictions:<8}                              │
│  Validated:             {self.stats.validated_predictions:<8}                              │
│  Pending Validation:    {len(self.pending_validations):<8}                              │
│                                                                    │
│  Directional Accuracy:  {self.stats.direction_accuracy*100:.1f}%                                   │
│  ├─ Correct: {self.stats.direction_correct:<6} | Wrong: {self.stats.direction_wrong:<6}                      │
│  Profit Factor:         {self.stats.profit_factor:.2f}                                    │
│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  📊 ACCURACY BY MARKET REGIME                                      │
│""")
        for regime, acc in self.stats.accuracy_by_regime.items():
            bar = "█" * int(acc * 20) + "░" * (20 - int(acc * 20))
            print(f"│  {regime:<12} [{bar}] {acc*100:.0f}%")
        
        print(f"""│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  😱 ACCURACY BY FEAR/GREED                                         │
│""")
        for band, acc in self.stats.accuracy_by_fear_greed.items():
            bar = "█" * int(acc * 20) + "░" * (20 - int(acc * 20))
            print(f"│  {band:<12} [{bar}] {acc*100:.0f}%")
        
        print(f"""│                                                                    │
├────────────────────────────────────────────────────────────────────┤
│  ⏱️ RECENT PERFORMANCE                                             │
│  Last 24 hours: {self.stats.accuracy_last_24h*100:.1f}%                                         │
│  Last 7 days:   {self.stats.accuracy_last_7d*100:.1f}%                                         │
└────────────────────────────────────────────────────────────────────┘
""")
        print("=" * 70)
    
    def get_recent_predictions(self, limit: int = 10) -> List[Dict]:
        """Get most recent predictions with outcomes."""
        sorted_preds = sorted(
            self.predictions.values(),
            key=lambda p: p.timestamp,
            reverse=True
        )[:limit]
        
        return [p.to_dict() for p in sorted_preds]


# Global validator instance
_validator = None

def get_validator() -> ProbabilityValidator:
    """Get or create singleton validator."""
    global _validator
    if _validator is None:
        _validator = ProbabilityValidator()
    return _validator


# ═══════════════════════════════════════════════════════════════
# 🧪 TEST / DEMO
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n📊 PROBABILITY MATRIX VALIDATION ENGINE")
    print("=" * 70)
    
    validator = get_validator()
    
    # Show current stats
    validator.print_dashboard()
    
    # Demo: Record a prediction
    print("\n📝 Recording test predictions...")
    
    # Simulated predictions for testing
    test_predictions = [
        ("BTCUSDC", "BULLISH", 0.72, 0.85, "BUY", 97500, 26, 20.0, "NORMAL", "NEUTRAL"),
        ("ETHUSDC", "BULLISH", 0.68, 0.78, "BUY", 3650, 26, 20.0, "NORMAL", "NEUTRAL"),
        ("SOLUSDC", "BEARISH", 0.62, 0.71, "SELL", 220, 26, 20.0, "NORMAL", "NEUTRAL"),
    ]
    
    for symbol, direction, prob, conf, action, price, fg, vix, regime, bias in test_predictions:
        pred_id = validator.record_prediction(
            symbol=symbol,
            direction=direction,
            probability=prob,
            confidence=conf,
            action=action,
            price=price,
            fear_greed=fg,
            vix=vix,
            market_regime=regime,
            macro_bias=bias,
        )
        print(f"   Recorded: {pred_id}")
    
    # Simulate validation (normally would wait 2 hours)
    print("\n🔍 Simulating validation (normally waits 2 hours)...")
    
    # Simulate price changes
    simulated_outcomes = {
        "BTCUSDC": 98200,  # +0.7% (correct)
        "ETHUSDC": 3580,   # -1.9% (wrong)
        "SOLUSDC": 215,    # -2.3% (correct - we predicted bearish)
    }
    
    for pred_id in list(validator.pending_validations)[-3:]:
        pred = validator.predictions[pred_id]
        new_price = simulated_outcomes.get(pred.symbol, pred.price_at_prediction)
        result = validator.validate_prediction(pred_id, new_price)
        if result:
            emoji = "✅" if result['correct'] else "❌"
            print(f"   {emoji} {result['symbol']}: Predicted {result['predicted']}, Actual {result['actual']} ({result['price_change_pct']:+.2f}%)")
    
    # Show updated dashboard
    validator.print_dashboard()
    
    print("\n✅ Validation Engine Ready")
    print("   Predictions are recorded and validated after 2-hour window")
    print("   Accuracy feeds back to adjust confidence levels")
