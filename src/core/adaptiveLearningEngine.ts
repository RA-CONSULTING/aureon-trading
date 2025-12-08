// AdaptiveLearningEngine - Self-optimizing thresholds from historical performance
// Phase 5B: Closes the Python ecosystem gap for adaptive_learning_engine

import { tradeLogger, type CalibrationData } from './tradeLogger';

export interface LearnedThresholds {
  coherenceMin: number;
  coherenceMax: number;
  confidenceMin: number;
  kellyMultiplier: number;
  optimalHours: number[];
  avoidHours: number[];
  preferredBands: string[];
  avoidBands: string[];
  regimeAdjustments: Record<string, number>;
}

export interface LearningState {
  thresholds: LearnedThresholds;
  calibrationData: CalibrationData | null;
  lastCalibrationTime: number;
  samplesUsed: number;
  confidence: number;
}

const DEFAULT_THRESHOLDS: LearnedThresholds = {
  coherenceMin: 0.70,
  coherenceMax: 1.0,
  confidenceMin: 0.50,
  kellyMultiplier: 0.5, // Half-Kelly default
  optimalHours: [],
  avoidHours: [],
  preferredBands: ['528Hz', '432Hz'],
  avoidBands: ['963Hz'], // Poor historical performer per Python spec
  regimeAdjustments: {
    TRENDING: 1.2,
    VOLATILE: 0.6,
    RANGING: 0.8,
    NORMAL: 1.0,
  },
};

class AdaptiveLearningEngine {
  private state: LearningState = {
    thresholds: { ...DEFAULT_THRESHOLDS },
    calibrationData: null,
    lastCalibrationTime: 0,
    samplesUsed: 0,
    confidence: 0,
  };

  private calibrationIntervalMs = 60 * 60 * 1000; // Re-calibrate every hour

  /**
   * Run calibration from trade history
   */
  calibrate(): LearnedThresholds {
    const calibration = tradeLogger.exportCalibration();
    this.state.calibrationData = calibration;
    this.state.lastCalibrationTime = Date.now();
    this.state.samplesUsed = calibration.totalTrades;

    if (calibration.totalTrades < 10) {
      // Not enough data, use defaults
      this.state.confidence = 0.1;
      console.log('[AdaptiveLearning] Insufficient trades for calibration, using defaults');
      return this.state.thresholds;
    }

    // Learn coherence range from winners
    this.state.thresholds.coherenceMin = Math.max(0.5, calibration.optimalCoherenceRange.min - 0.05);
    this.state.thresholds.coherenceMax = Math.min(1.0, calibration.optimalCoherenceRange.max + 0.05);

    // Learn optimal hours
    this.state.thresholds.optimalHours = calibration.bestHours;
    
    // Learn hours to avoid (low win rate hours)
    const allHours = Array.from({ length: 24 }, (_, i) => i);
    this.state.thresholds.avoidHours = allHours.filter(h => !calibration.bestHours.includes(h));

    // Learn preferred frequency bands (> 55% win rate)
    const goodBands = (Object.entries(calibration.bandPerformance) as [string, { trades: number; winRate: number; avgPnl: number }][])
      .filter(([, v]) => v.trades >= 5 && v.winRate >= 0.55)
      .map(([k]) => k);
    if (goodBands.length > 0) {
      this.state.thresholds.preferredBands = goodBands;
    }

    // Learn bands to avoid (< 45% win rate with sufficient samples)
    const badBands = (Object.entries(calibration.bandPerformance) as [string, { trades: number; winRate: number; avgPnl: number }][])
      .filter(([, v]) => v.trades >= 5 && v.winRate < 0.45)
      .map(([k]) => k);
    if (badBands.length > 0) {
      this.state.thresholds.avoidBands = badBands;
    }

    // Adjust Kelly multiplier based on recent win rate
    // More conservative when losing, more aggressive when winning
    if (calibration.winRate >= 0.60) {
      this.state.thresholds.kellyMultiplier = Math.min(0.7, 0.5 + (calibration.winRate - 0.5) * 0.4);
    } else if (calibration.winRate < 0.45) {
      this.state.thresholds.kellyMultiplier = Math.max(0.25, 0.5 - (0.5 - calibration.winRate) * 0.5);
    } else {
      this.state.thresholds.kellyMultiplier = 0.5;
    }

    // Learn confidence threshold from tier performance
    const tier1Performance = calibration.tierPerformance[1];
    if (tier1Performance.trades >= 5 && tier1Performance.winRate >= 0.6) {
      // Tier 1 trades are reliable, can lower confidence threshold
      this.state.thresholds.confidenceMin = Math.max(0.4, 0.50 - 0.1);
    } else {
      this.state.thresholds.confidenceMin = 0.50;
    }

    // Calculate overall learning confidence
    const sampleConfidence = Math.min(1, calibration.totalTrades / 100);
    const winRateConfidence = calibration.winRate >= 0.51 ? 1 : calibration.winRate / 0.51;
    this.state.confidence = (sampleConfidence + winRateConfidence) / 2;

    console.log(
      `[AdaptiveLearning] 🧠 Calibrated | Trades: ${calibration.totalTrades} | ` +
      `WinRate: ${(calibration.winRate * 100).toFixed(1)}% | ` +
      `Kelly: ${this.state.thresholds.kellyMultiplier.toFixed(2)} | ` +
      `Γ Range: [${this.state.thresholds.coherenceMin.toFixed(2)}, ${this.state.thresholds.coherenceMax.toFixed(2)}] | ` +
      `Confidence: ${(this.state.confidence * 100).toFixed(0)}%`
    );

    return this.state.thresholds;
  }

  /**
   * Get current learned thresholds, auto-recalibrating if needed
   */
  getThresholds(): LearnedThresholds {
    const timeSinceCalibration = Date.now() - this.state.lastCalibrationTime;
    if (timeSinceCalibration > this.calibrationIntervalMs) {
      this.calibrate();
    }
    return this.state.thresholds;
  }

  /**
   * Check if a trade should be taken based on learned thresholds
   */
  shouldTrade(params: {
    coherence: number;
    confidence: number;
    frequencyBand: string;
    regime: string;
    hour?: number;
  }): { allowed: boolean; reason: string; modifier: number } {
    const t = this.getThresholds();
    const hour = params.hour ?? new Date().getHours();

    // Check coherence range
    if (params.coherence < t.coherenceMin) {
      return { allowed: false, reason: `Coherence ${params.coherence.toFixed(3)} below learned min ${t.coherenceMin.toFixed(3)}`, modifier: 1 };
    }

    // Check confidence
    if (params.confidence < t.confidenceMin) {
      return { allowed: false, reason: `Confidence ${params.confidence.toFixed(3)} below learned min ${t.confidenceMin.toFixed(3)}`, modifier: 1 };
    }

    // Check avoid bands
    if (t.avoidBands.includes(params.frequencyBand)) {
      return { allowed: false, reason: `Frequency band ${params.frequencyBand} historically underperforms`, modifier: 1 };
    }

    // Check avoid hours (soft block - reduce size instead of blocking)
    let modifier = 1.0;
    if (t.avoidHours.includes(hour) && t.avoidHours.length < 18) {
      modifier *= 0.5;
    }

    // Apply regime adjustment
    const regimeModifier = t.regimeAdjustments[params.regime] ?? 1.0;
    modifier *= regimeModifier;

    // Boost for optimal hours
    if (t.optimalHours.includes(hour)) {
      modifier *= 1.2;
    }

    // Boost for preferred bands
    if (t.preferredBands.includes(params.frequencyBand)) {
      modifier *= 1.15;
    }

    return { allowed: true, reason: 'Passed adaptive thresholds', modifier };
  }

  /**
   * Get Kelly-adjusted position size
   */
  adjustPositionSize(baseSize: number): number {
    return baseSize * this.state.thresholds.kellyMultiplier;
  }

  /**
   * Get current learning state
   */
  getState(): LearningState {
    return { ...this.state };
  }

  /**
   * Force immediate recalibration
   */
  forceCalibrate(): LearnedThresholds {
    return this.calibrate();
  }

  /**
   * Reset to default thresholds
   */
  reset(): void {
    this.state = {
      thresholds: { ...DEFAULT_THRESHOLDS },
      calibrationData: null,
      lastCalibrationTime: 0,
      samplesUsed: 0,
      confidence: 0,
    };
    console.log('[AdaptiveLearning] Reset to defaults');
  }
}

export const adaptiveLearningEngine = new AdaptiveLearningEngine();
