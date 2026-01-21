/**
 * Adaptive Filter Thresholds - Ported from aureon_unified_ecosystem.py lines 2563-2719
 * Detects market regime and auto-adjusts trading thresholds based on conditions
 */

import { unifiedBus } from './unifiedBus';

type MarketRegime = 'TRENDING' | 'VOLATILE' | 'RANGING' | 'NORMAL';

interface ThresholdConfig {
  minMomentum: number;
  minVolume: number;
  minCoherence: number;
  maxPositions: number;
  takeProfitPct: number;
  stopLossPct: number;
}

interface RegimeDetectionResult {
  regime: MarketRegime;
  confidence: number;
  volatility: number;
  trendStrength: number;
  rangeWidth: number;
  timestamp: number;
}

interface TradeHistory {
  symbol: string;
  profit: number;
  coherenceAtEntry: number;
  momentumAtEntry: number;
  volumeAtEntry: number;
  regime: MarketRegime;
  timestamp: number;
}

// Regime-specific threshold presets
const REGIME_PRESETS: Record<MarketRegime, ThresholdConfig> = {
  TRENDING: {
    minMomentum: 0.005,    // Lower momentum threshold - ride the trend
    minVolume: 500000,
    minCoherence: 0.6,     // Lower coherence OK in strong trends
    maxPositions: 8,
    takeProfitPct: 2.0,    // Wider take profit
    stopLossPct: 1.0
  },
  VOLATILE: {
    minMomentum: 0.02,     // Higher momentum required
    minVolume: 1000000,    // Higher volume required
    minCoherence: 0.8,     // Higher coherence required
    maxPositions: 4,       // Fewer positions
    takeProfitPct: 1.5,
    stopLossPct: 0.8       // Tighter stops
  },
  RANGING: {
    minMomentum: 0.001,    // Low momentum OK
    minVolume: 300000,
    minCoherence: 0.7,
    maxPositions: 6,
    takeProfitPct: 0.8,    // Tighter targets
    stopLossPct: 0.5
  },
  NORMAL: {
    minMomentum: 0.01,
    minVolume: 500000,
    minCoherence: 0.7,
    maxPositions: 6,
    takeProfitPct: 1.2,
    stopLossPct: 0.8
  }
};

export class AdaptiveFilterThresholds {
  private currentRegime: MarketRegime = 'NORMAL';
  private currentThresholds: ThresholdConfig = { ...REGIME_PRESETS.NORMAL };
  private tradeHistory: TradeHistory[] = [];
  private maxHistorySize: number = 500;
  private volatilityWindow: number[] = [];
  private priceWindow: number[] = [];
  private windowSize: number = 20;

  // Learning parameters
  private learningRate: number = 0.1;
  private learnedAdjustments: Map<MarketRegime, Partial<ThresholdConfig>> = new Map();

  /**
   * Detect current market regime from price/volume data
   */
  detectRegime(prices: number[], volumes: number[]): RegimeDetectionResult {
    const now = Date.now();
    
    if (prices.length < 10) {
      return {
        regime: 'NORMAL',
        confidence: 0.5,
        volatility: 0,
        trendStrength: 0,
        rangeWidth: 0,
        timestamp: now
      };
    }
    
    // Calculate volatility (standard deviation of returns)
    const returns: number[] = [];
    for (let i = 1; i < prices.length; i++) {
      returns.push((prices[i] - prices[i - 1]) / prices[i - 1]);
    }
    const avgReturn = returns.reduce((a, b) => a + b, 0) / returns.length;
    const volatility = Math.sqrt(
      returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length
    );
    
    // Calculate trend strength (linear regression slope)
    const n = prices.length;
    const xMean = (n - 1) / 2;
    const yMean = prices.reduce((a, b) => a + b, 0) / n;
    let numerator = 0;
    let denominator = 0;
    for (let i = 0; i < n; i++) {
      numerator += (i - xMean) * (prices[i] - yMean);
      denominator += Math.pow(i - xMean, 2);
    }
    const slope = denominator !== 0 ? numerator / denominator : 0;
    const trendStrength = Math.abs(slope / yMean) * 100;
    
    // Calculate range width
    const high = Math.max(...prices);
    const low = Math.min(...prices);
    const rangeWidth = ((high - low) / low) * 100;
    
    // Determine regime
    let regime: MarketRegime = 'NORMAL';
    let confidence = 0.5;
    
    if (volatility > 0.03 && rangeWidth > 5) {
      regime = 'VOLATILE';
      confidence = Math.min(0.9, volatility * 20);
    } else if (trendStrength > 0.5 && volatility < 0.02) {
      regime = 'TRENDING';
      confidence = Math.min(0.9, trendStrength);
    } else if (rangeWidth < 2 && volatility < 0.01) {
      regime = 'RANGING';
      confidence = Math.min(0.9, (2 - rangeWidth) / 2);
    } else {
      regime = 'NORMAL';
      confidence = 0.6;
    }
    
    // Update current regime if confident enough
    if (confidence > 0.6 && regime !== this.currentRegime) {
      this.currentRegime = regime;
      this.updateThresholds(regime);
    }
    
    // Publish to UnifiedBus
    unifiedBus.publish({
      systemName: 'AdaptiveFilterThresholds',
      timestamp: now,
      ready: true,
      coherence: confidence,
      confidence,
      signal: 'NEUTRAL',
      data: {
        regime,
        volatility,
        trendStrength,
        rangeWidth,
        thresholds: this.currentThresholds
      }
    });
    
    return {
      regime,
      confidence,
      volatility,
      trendStrength,
      rangeWidth,
      timestamp: now
    };
  }

  /**
   * Update thresholds based on detected regime
   */
  private updateThresholds(regime: MarketRegime): void {
    // Start with preset
    this.currentThresholds = { ...REGIME_PRESETS[regime] };
    
    // Apply learned adjustments if available
    const learned = this.learnedAdjustments.get(regime);
    if (learned) {
      this.currentThresholds = {
        ...this.currentThresholds,
        ...learned
      };
    }
    
    console.log(`[AdaptiveFilterThresholds] Regime changed to ${regime}:`, this.currentThresholds);
  }

  /**
   * Record trade result for learning
   */
  recordTrade(trade: TradeHistory): void {
    this.tradeHistory.push(trade);
    
    // Trim history
    if (this.tradeHistory.length > this.maxHistorySize) {
      this.tradeHistory = this.tradeHistory.slice(-this.maxHistorySize);
    }
    
    // Trigger learning every 50 trades
    if (this.tradeHistory.length % 50 === 0) {
      this.learnFromHistory();
    }
  }

  /**
   * Learn optimal thresholds from trade history
   */
  private learnFromHistory(): void {
    // Group trades by regime
    const regimeGroups = new Map<MarketRegime, TradeHistory[]>();
    
    for (const trade of this.tradeHistory) {
      const existing = regimeGroups.get(trade.regime) || [];
      existing.push(trade);
      regimeGroups.set(trade.regime, existing);
    }
    
    // For each regime, find optimal thresholds
    for (const [regime, trades] of regimeGroups) {
      if (trades.length < 20) continue;
      
      // Find winning trades
      const winningTrades = trades.filter(t => t.profit > 0);
      if (winningTrades.length === 0) continue;
      
      // Calculate average thresholds of winning trades
      const avgCoherence = winningTrades.reduce((s, t) => s + t.coherenceAtEntry, 0) / winningTrades.length;
      const avgMomentum = winningTrades.reduce((s, t) => s + t.momentumAtEntry, 0) / winningTrades.length;
      const avgVolume = winningTrades.reduce((s, t) => s + t.volumeAtEntry, 0) / winningTrades.length;
      
      // Apply learning rate to adjust
      const current = this.learnedAdjustments.get(regime) || {};
      this.learnedAdjustments.set(regime, {
        ...current,
        minCoherence: this.lerp(REGIME_PRESETS[regime].minCoherence, avgCoherence, this.learningRate),
        minMomentum: this.lerp(REGIME_PRESETS[regime].minMomentum, avgMomentum, this.learningRate),
        minVolume: this.lerp(REGIME_PRESETS[regime].minVolume, avgVolume, this.learningRate)
      });
    }
    
    console.log('[AdaptiveFilterThresholds] Learning updated adjustments:', 
      Object.fromEntries(this.learnedAdjustments));
  }

  private lerp(a: number, b: number, t: number): number {
    return a + (b - a) * t;
  }

  /**
   * Check if trade passes current adaptive thresholds
   */
  passesThresholds(coherence: number, momentum: number, volume: number): boolean {
    return (
      coherence >= this.currentThresholds.minCoherence &&
      Math.abs(momentum) >= this.currentThresholds.minMomentum &&
      volume >= this.currentThresholds.minVolume
    );
  }

  getCurrentRegime(): MarketRegime {
    return this.currentRegime;
  }

  getCurrentThresholds(): ThresholdConfig {
    return { ...this.currentThresholds };
  }

  getMaxPositions(): number {
    return this.currentThresholds.maxPositions;
  }

  getTakeProfitPct(): number {
    return this.currentThresholds.takeProfitPct;
  }

  getStopLossPct(): number {
    return this.currentThresholds.stopLossPct;
  }
}

export const adaptiveFilterThresholds = new AdaptiveFilterThresholds();
