/**
 * Capital Pool Manager
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Manages trading capital allocation like Python aureon_unified_ecosystem.py
 * - Tracks available vs reserved capital
 * - Applies Kelly criterion for position sizing
 * - Implements 10-9-1 compounding (90% reinvest, 10% harvest)
 */

import { unifiedBus } from './unifiedBus';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { adaptiveLearningEngine } from './adaptiveLearningEngine';

export interface CapitalState {
  totalEquity: number;
  availableCapital: number;
  reservedCapital: number;
  harvestedProfit: number;
  unrealizedPnL: number;
  positionCount: number;
  maxPositions: number;
  utilizationPct: number;
  kellyFraction: number;
  lastUpdate: number;
}

export interface PositionSizeResult {
  sizeUsd: number;
  maxAllowed: number;
  percentOfCapital: number;
  kellyAdjusted: boolean;
  reason: string;
}

const DEFAULT_CONFIG = {
  maxPositions: 15,
  maxPositionPct: 0.10, // Max 10% per position
  minPositionUsd: 10,
  maxPositionUsd: 5000,
  reserveRatio: 0.20, // Keep 20% in reserve
  harvestRatio: 0.10, // 10-9-1: harvest 10% of profits
  compoundRatio: 0.90, // 10-9-1: compound 90% back
};

class CapitalPool {
  private state: CapitalState = {
    totalEquity: 0,
    availableCapital: 0,
    reservedCapital: 0,
    harvestedProfit: 0,
    unrealizedPnL: 0,
    positionCount: 0,
    maxPositions: DEFAULT_CONFIG.maxPositions,
    utilizationPct: 0,
    kellyFraction: 0.5,
    lastUpdate: 0,
  };

  private positionReserves: Map<string, number> = new Map();

  constructor() {
    temporalLadder.registerSystem(SYSTEMS.CAPITAL_POOL);
    console.log('💰 Capital Pool Manager initialized');
  }

  /**
   * Update total equity from exchange balances
   */
  updateEquity(totalEquity: number, unrealizedPnL: number = 0): void {
    this.state.totalEquity = totalEquity;
    this.state.unrealizedPnL = unrealizedPnL;
    
    // Calculate available capital (total - reserved - positions)
    const reservedForPositions = Array.from(this.positionReserves.values())
      .reduce((sum, v) => sum + v, 0);
    
    const minimumReserve = totalEquity * DEFAULT_CONFIG.reserveRatio;
    this.state.reservedCapital = reservedForPositions + minimumReserve;
    this.state.availableCapital = Math.max(0, totalEquity - this.state.reservedCapital);
    
    // Update utilization
    this.state.utilizationPct = reservedForPositions / Math.max(totalEquity, 1);
    
    // Get Kelly from adaptive learning
    const thresholds = adaptiveLearningEngine.getThresholds();
    this.state.kellyFraction = thresholds.kellyMultiplier;
    
    this.state.lastUpdate = Date.now();
    this.state.positionCount = this.positionReserves.size;
    
    this.publishState();
    temporalLadder.heartbeat(SYSTEMS.CAPITAL_POOL, this.state.availableCapital > 0 ? 0.9 : 0.3);
  }

  /**
   * Calculate position size for a trade
   */
  calculatePositionSize(
    confidence: number,
    volatility: number,
    qgitaTier: 1 | 2 | 3 = 3
  ): PositionSizeResult {
    const { totalEquity, availableCapital, positionCount, kellyFraction } = this.state;

    // Check if we can open more positions
    if (positionCount >= DEFAULT_CONFIG.maxPositions) {
      return {
        sizeUsd: 0,
        maxAllowed: 0,
        percentOfCapital: 0,
        kellyAdjusted: false,
        reason: `Max positions reached (${positionCount}/${DEFAULT_CONFIG.maxPositions})`,
      };
    }

    if (availableCapital < DEFAULT_CONFIG.minPositionUsd) {
      return {
        sizeUsd: 0,
        maxAllowed: 0,
        percentOfCapital: 0,
        kellyAdjusted: false,
        reason: 'Insufficient available capital',
      };
    }

    // Base position size from Kelly criterion
    let basePct = kellyFraction * DEFAULT_CONFIG.maxPositionPct;

    // Adjust by QGITA tier
    const tierMultiplier = qgitaTier === 1 ? 1.5 : qgitaTier === 2 ? 1.0 : 0.5;
    basePct *= tierMultiplier;

    // Adjust by confidence
    basePct *= Math.min(1, confidence / 0.7);

    // Inverse volatility adjustment (less size for high volatility)
    const volAdjust = Math.max(0.3, 1 - volatility);
    basePct *= volAdjust;

    // Calculate USD amount
    let sizeUsd = totalEquity * basePct;

    // Apply limits
    sizeUsd = Math.max(DEFAULT_CONFIG.minPositionUsd, sizeUsd);
    sizeUsd = Math.min(DEFAULT_CONFIG.maxPositionUsd, sizeUsd);
    sizeUsd = Math.min(availableCapital * 0.5, sizeUsd); // Max 50% of available

    return {
      sizeUsd: Math.round(sizeUsd * 100) / 100,
      maxAllowed: availableCapital * 0.5,
      percentOfCapital: (sizeUsd / totalEquity) * 100,
      kellyAdjusted: true,
      reason: `Tier ${qgitaTier} | Kelly ${(kellyFraction * 100).toFixed(0)}% | Vol ${(volAdjust * 100).toFixed(0)}%`,
    };
  }

  /**
   * Reserve capital for a new position
   */
  reserve(symbol: string, amount: number): boolean {
    if (amount > this.state.availableCapital) {
      console.warn(`[CapitalPool] Cannot reserve $${amount} for ${symbol} - only $${this.state.availableCapital} available`);
      return false;
    }

    this.positionReserves.set(symbol, (this.positionReserves.get(symbol) || 0) + amount);
    this.state.availableCapital -= amount;
    this.state.positionCount = this.positionReserves.size;
    
    console.log(`[CapitalPool] Reserved $${amount.toFixed(2)} for ${symbol} | Available: $${this.state.availableCapital.toFixed(2)}`);
    this.publishState();
    return true;
  }

  /**
   * Release reserved capital (position closed)
   */
  release(symbol: string, profit: number = 0): void {
    const reserved = this.positionReserves.get(symbol) || 0;
    if (reserved === 0) return;

    this.positionReserves.delete(symbol);
    
    // Apply 10-9-1 rule to profits
    if (profit > 0) {
      const harvestAmount = profit * DEFAULT_CONFIG.harvestRatio;
      const compoundAmount = profit * DEFAULT_CONFIG.compoundRatio;
      
      this.state.harvestedProfit += harvestAmount;
      this.state.availableCapital += reserved + compoundAmount;
      
      console.log(`[CapitalPool] Released ${symbol} | Profit: $${profit.toFixed(2)} | ` +
        `Harvest: $${harvestAmount.toFixed(2)} | Compound: $${compoundAmount.toFixed(2)}`);
    } else {
      this.state.availableCapital += reserved + profit; // profit is negative for losses
    }

    this.state.positionCount = this.positionReserves.size;
    this.publishState();
  }

  /**
   * Get available balance for trading
   */
  getAvailable(): number {
    return this.state.availableCapital;
  }

  /**
   * Get current capital state
   */
  getState(): CapitalState {
    return { ...this.state };
  }

  /**
   * Check if we can open a new position
   */
  canOpenPosition(): { allowed: boolean; reason: string } {
    if (this.state.positionCount >= DEFAULT_CONFIG.maxPositions) {
      return { allowed: false, reason: `Max positions (${DEFAULT_CONFIG.maxPositions}) reached` };
    }
    if (this.state.availableCapital < DEFAULT_CONFIG.minPositionUsd) {
      return { allowed: false, reason: `Insufficient capital ($${this.state.availableCapital.toFixed(2)})` };
    }
    return { allowed: true, reason: 'OK' };
  }

  private publishState(): void {
    unifiedBus.publish({
      systemName: 'CapitalPool',
      timestamp: Date.now(),
      ready: this.state.availableCapital > 0,
      coherence: 1 - this.state.utilizationPct,
      confidence: Math.min(1, this.state.availableCapital / 1000),
      signal: 'NEUTRAL',
      data: {
        totalEquity: this.state.totalEquity,
        available: this.state.availableCapital,
        reserved: this.state.reservedCapital,
        harvested: this.state.harvestedProfit,
        positions: this.state.positionCount,
        utilization: this.state.utilizationPct,
        kelly: this.state.kellyFraction,
      },
    });
  }
}

export const capitalPool = new CapitalPool();
