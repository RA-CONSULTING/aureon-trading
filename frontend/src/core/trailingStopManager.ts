/**
 * Trailing Stop Manager
 * Ported from aureon_unified_ecosystem.py lines 2726-2835
 * ATR-based dynamic trailing stops with activation thresholds
 */

import { unifiedBus } from './unifiedBus';

export interface TrailingStop {
  symbol: string;
  entryPrice: number;
  currentPrice: number;
  highWaterMark: number;
  trailPrice: number;
  atr: number;
  atrMultiplier: number;
  isActivated: boolean;
  activationPct: number;
  trailPct: number;
  unrealizedPnlPct: number;
  createdAt: number;
  updatedAt: number;
}

export interface TrailingStopConfig {
  activationPct: number;      // Profit % to activate trailing (default 0.5%)
  trailPct: number;           // Trail behind peak (default 0.3%)
  atrMultiplier: number;      // ATR multiplier for dynamic stops
  useAtrStop: boolean;        // Use ATR-based stops
  minStopDistance: number;    // Minimum stop distance %
}

const DEFAULT_CONFIG: TrailingStopConfig = {
  activationPct: 0.005,       // 0.5% profit to activate
  trailPct: 0.003,            // 0.3% trail behind peak
  atrMultiplier: 2.0,         // 2x ATR for dynamic stops
  useAtrStop: true,
  minStopDistance: 0.002,     // 0.2% minimum
};

export class TrailingStopManager {
  private stops: Map<string, TrailingStop> = new Map();
  private config: TrailingStopConfig;
  private triggeredStops: TrailingStop[] = [];

  constructor(config: Partial<TrailingStopConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  /**
   * Create a new trailing stop for a position
   */
  createStop(
    symbol: string,
    entryPrice: number,
    currentPrice: number,
    atr: number = 0
  ): TrailingStop {
    const stop: TrailingStop = {
      symbol,
      entryPrice,
      currentPrice,
      highWaterMark: currentPrice,
      trailPrice: this.calculateTrailPrice(entryPrice, currentPrice, atr, false),
      atr,
      atrMultiplier: this.config.atrMultiplier,
      isActivated: false,
      activationPct: this.config.activationPct,
      trailPct: this.config.trailPct,
      unrealizedPnlPct: (currentPrice - entryPrice) / entryPrice,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };

    this.stops.set(symbol, stop);
    this.publishState();
    return stop;
  }

  /**
   * Update trailing stop with new price
   */
  updateStop(symbol: string, currentPrice: number, atr?: number): {
    stop: TrailingStop | null;
    triggered: boolean;
    action: 'HOLD' | 'STOP_TRIGGERED';
  } {
    const stop = this.stops.get(symbol);
    if (!stop) {
      return { stop: null, triggered: false, action: 'HOLD' };
    }

    // Update ATR if provided
    if (atr !== undefined) {
      stop.atr = atr;
    }

    // Update current price
    stop.currentPrice = currentPrice;
    stop.unrealizedPnlPct = (currentPrice - stop.entryPrice) / stop.entryPrice;
    stop.updatedAt = Date.now();

    // Check if trailing should activate
    const profitPct = (currentPrice - stop.entryPrice) / stop.entryPrice;
    if (!stop.isActivated && profitPct >= this.config.activationPct) {
      stop.isActivated = true;
      console.log(`[TrailingStop] Activated for ${symbol} at ${(profitPct * 100).toFixed(2)}% profit`);
    }

    // Update high water mark and trail price if activated
    if (stop.isActivated && currentPrice > stop.highWaterMark) {
      stop.highWaterMark = currentPrice;
      stop.trailPrice = this.calculateTrailPrice(
        stop.entryPrice,
        currentPrice,
        stop.atr,
        true
      );
    }

    // Check if stop is triggered
    if (stop.isActivated && currentPrice <= stop.trailPrice) {
      this.triggeredStops.push({ ...stop });
      this.stops.delete(symbol);
      this.publishState();
      
      console.log(`[TrailingStop] TRIGGERED for ${symbol} at ${currentPrice}`);
      return { stop, triggered: true, action: 'STOP_TRIGGERED' };
    }

    this.publishState();
    return { stop, triggered: false, action: 'HOLD' };
  }

  /**
   * Calculate trail price based on config
   */
  private calculateTrailPrice(
    entryPrice: number,
    currentPrice: number,
    atr: number,
    isActivated: boolean
  ): number {
    if (!isActivated) {
      // Before activation, use fixed stop loss
      return entryPrice * (1 - this.config.minStopDistance);
    }

    let trailDistance: number;

    if (this.config.useAtrStop && atr > 0) {
      // ATR-based trailing stop
      trailDistance = atr * this.config.atrMultiplier;
    } else {
      // Percentage-based trailing stop
      trailDistance = currentPrice * this.config.trailPct;
    }

    // Ensure minimum stop distance
    const minDistance = currentPrice * this.config.minStopDistance;
    trailDistance = Math.max(trailDistance, minDistance);

    return currentPrice - trailDistance;
  }

  /**
   * Get stop for a symbol
   */
  getStop(symbol: string): TrailingStop | null {
    return this.stops.get(symbol) || null;
  }

  /**
   * Get all active stops
   */
  getAllStops(): TrailingStop[] {
    return Array.from(this.stops.values());
  }

  /**
   * Remove a stop
   */
  removeStop(symbol: string): boolean {
    const result = this.stops.delete(symbol);
    if (result) {
      this.publishState();
    }
    return result;
  }

  /**
   * Get triggered stops history
   */
  getTriggeredHistory(): TrailingStop[] {
    return [...this.triggeredStops];
  }

  /**
   * Calculate ATR from price history
   * True Range = max(high-low, |high-prevClose|, |low-prevClose|)
   */
  calculateATR(
    highs: number[],
    lows: number[],
    closes: number[],
    period: number = 14
  ): number {
    if (highs.length < period + 1) return 0;

    const trueRanges: number[] = [];
    
    for (let i = 1; i < highs.length; i++) {
      const high = highs[i];
      const low = lows[i];
      const prevClose = closes[i - 1];
      
      const tr = Math.max(
        high - low,
        Math.abs(high - prevClose),
        Math.abs(low - prevClose)
      );
      trueRanges.push(tr);
    }

    // Simple moving average of true ranges
    const recentTRs = trueRanges.slice(-period);
    return recentTRs.reduce((sum, tr) => sum + tr, 0) / recentTRs.length;
  }

  /**
   * Publish state to UnifiedBus
   */
  private publishState(): void {
    const stops = this.getAllStops();
    const activeCount = stops.filter(s => s.isActivated).length;
    
    unifiedBus.publish({
      systemName: 'TrailingStopManager',
      timestamp: Date.now(),
      ready: true,
      coherence: stops.length > 0 ? 0.8 : 0.5,
      confidence: activeCount / Math.max(stops.length, 1),
      signal: 'NEUTRAL',
      data: {
        totalStops: stops.length,
        activeStops: activeCount,
        triggeredCount: this.triggeredStops.length,
        avgUnrealizedPnl: stops.length > 0
          ? stops.reduce((sum, s) => sum + s.unrealizedPnlPct, 0) / stops.length
          : 0,
      },
    });
  }

  /**
   * Get manager statistics
   */
  getStats(): {
    totalStops: number;
    activeStops: number;
    triggeredCount: number;
    avgUnrealizedPnl: number;
  } {
    const stops = this.getAllStops();
    return {
      totalStops: stops.length,
      activeStops: stops.filter(s => s.isActivated).length,
      triggeredCount: this.triggeredStops.length,
      avgUnrealizedPnl: stops.length > 0
        ? stops.reduce((sum, s) => sum + s.unrealizedPnlPct, 0) / stops.length
        : 0,
    };
  }
}

// Singleton instance
export const trailingStopManager = new TrailingStopManager();
