/**
 * Position Heat Tracker
 * Ported from aureon_unified_ecosystem.py lines 2459-2556
 * Tracks correlation heat to prevent over-concentration
 */

import { unifiedBus } from './unifiedBus';

export interface PositionHeat {
  symbol: string;
  heatValue: number;        // 0-1 heat contribution
  correlationGroup: string; // BTC, ETH, ALTS, STABLES
  positionSize: number;     // Position size in USD
  entryTime: number;
}

export interface HeatState {
  totalHeat: number;
  btcHeat: number;
  ethHeat: number;
  altHeat: number;
  stableHeat: number;
  canAddPosition: boolean;
  maxHeatReached: boolean;
}

// Correlation groups and their heat multipliers
const CORRELATION_GROUPS: Record<string, string[]> = {
  BTC: ['BTCUSDT', 'BTCUSDC', 'BTCBUSD', 'WBTCUSDT', 'BTCGBP', 'BTCEUR'],
  ETH: ['ETHUSDT', 'ETHUSDC', 'ETHBUSD', 'ETHBTC', 'ETHGBP', 'ETHEUR'],
  ALTS: ['SOLUSDT', 'AVAXUSDT', 'DOTUSDT', 'ADAUSDT', 'MATICUSDT', 'LINKUSDT', 
         'ATOMUSDT', 'NEARUSDT', 'FTMUSDT', 'ALGOUSDT', 'XRPUSDT', 'DOGEUSDT'],
  STABLES: ['USDCUSDT', 'BUSDUSDT', 'DAIUSDT', 'TUSDUSDT'],
};

// Heat multipliers by correlation group (BTC/ETH pairs add more heat)
const HEAT_MULTIPLIERS: Record<string, number> = {
  BTC: 1.0,      // Full heat
  ETH: 0.9,      // 90% heat (slightly correlated with BTC)
  ALTS: 0.7,     // 70% heat (less correlated)
  STABLES: 0.1,  // 10% heat (minimal risk)
};

// Maximum allowed heat (90% = nearly fully invested)
const MAX_TOTAL_HEAT = 0.90;
const MAX_GROUP_HEAT = 0.50; // Max 50% in any single group

export class PositionHeatTracker {
  private positions: Map<string, PositionHeat> = new Map();
  private totalCapital: number = 10000; // Default capital

  constructor(initialCapital: number = 10000) {
    this.totalCapital = initialCapital;
  }

  /**
   * Set total capital for heat calculations
   */
  setCapital(capital: number): void {
    this.totalCapital = capital;
    this.publishState();
  }

  /**
   * Get correlation group for a symbol
   */
  private getCorrelationGroup(symbol: string): string {
    const upperSymbol = symbol.toUpperCase();
    
    for (const [group, symbols] of Object.entries(CORRELATION_GROUPS)) {
      if (symbols.includes(upperSymbol)) {
        return group;
      }
    }
    
    // Default to ALTS for unknown symbols
    return 'ALTS';
  }

  /**
   * Calculate heat value for a position
   */
  private calculateHeat(symbol: string, positionSize: number): number {
    const group = this.getCorrelationGroup(symbol);
    const multiplier = HEAT_MULTIPLIERS[group] || 0.7;
    const baseHeat = positionSize / this.totalCapital;
    return baseHeat * multiplier;
  }

  /**
   * Add a position to heat tracking
   */
  addPosition(symbol: string, positionSize: number): boolean {
    const group = this.getCorrelationGroup(symbol);
    const heatValue = this.calculateHeat(symbol, positionSize);
    
    // Check if adding this position would exceed limits
    const currentState = this.getHeatState();
    const projectedTotalHeat = currentState.totalHeat + heatValue;
    
    if (projectedTotalHeat > MAX_TOTAL_HEAT) {
      console.log(`[PositionHeat] Rejected ${symbol}: Would exceed max heat (${(projectedTotalHeat * 100).toFixed(1)}%)`);
      return false;
    }

    // Check group heat limits
    const groupHeat = this.getGroupHeat(group);
    if (groupHeat + heatValue > MAX_GROUP_HEAT) {
      console.log(`[PositionHeat] Rejected ${symbol}: Would exceed ${group} group limit`);
      return false;
    }

    this.positions.set(symbol, {
      symbol,
      heatValue,
      correlationGroup: group,
      positionSize,
      entryTime: Date.now(),
    });

    this.publishState();
    return true;
  }

  /**
   * Update position size (e.g., after partial close)
   */
  updatePosition(symbol: string, newSize: number): void {
    const existing = this.positions.get(symbol);
    if (existing) {
      existing.positionSize = newSize;
      existing.heatValue = this.calculateHeat(symbol, newSize);
      this.publishState();
    }
  }

  /**
   * Remove a position from heat tracking
   */
  removePosition(symbol: string): boolean {
    const result = this.positions.delete(symbol);
    if (result) {
      this.publishState();
    }
    return result;
  }

  /**
   * Get current heat for a correlation group
   */
  private getGroupHeat(group: string): number {
    let heat = 0;
    for (const position of this.positions.values()) {
      if (position.correlationGroup === group) {
        heat += position.heatValue;
      }
    }
    return heat;
  }

  /**
   * Get complete heat state
   */
  getHeatState(): HeatState {
    const btcHeat = this.getGroupHeat('BTC');
    const ethHeat = this.getGroupHeat('ETH');
    const altHeat = this.getGroupHeat('ALTS');
    const stableHeat = this.getGroupHeat('STABLES');
    const totalHeat = btcHeat + ethHeat + altHeat + stableHeat;

    return {
      totalHeat,
      btcHeat,
      ethHeat,
      altHeat,
      stableHeat,
      canAddPosition: totalHeat < MAX_TOTAL_HEAT,
      maxHeatReached: totalHeat >= MAX_TOTAL_HEAT,
    };
  }

  /**
   * Check if a new position can be added
   */
  canAddPosition(symbol: string, positionSize: number): {
    allowed: boolean;
    reason: string;
    projectedHeat: number;
  } {
    const group = this.getCorrelationGroup(symbol);
    const heatValue = this.calculateHeat(symbol, positionSize);
    const currentState = this.getHeatState();
    const projectedTotalHeat = currentState.totalHeat + heatValue;
    const groupHeat = this.getGroupHeat(group);
    const projectedGroupHeat = groupHeat + heatValue;

    if (projectedTotalHeat > MAX_TOTAL_HEAT) {
      return {
        allowed: false,
        reason: `Total heat would exceed ${(MAX_TOTAL_HEAT * 100).toFixed(0)}% limit`,
        projectedHeat: projectedTotalHeat,
      };
    }

    if (projectedGroupHeat > MAX_GROUP_HEAT) {
      return {
        allowed: false,
        reason: `${group} group heat would exceed ${(MAX_GROUP_HEAT * 100).toFixed(0)}% limit`,
        projectedHeat: projectedGroupHeat,
      };
    }

    return {
      allowed: true,
      reason: 'Position allowed',
      projectedHeat: projectedTotalHeat,
    };
  }

  /**
   * Get all tracked positions
   */
  getAllPositions(): PositionHeat[] {
    return Array.from(this.positions.values());
  }

  /**
   * Publish state to UnifiedBus
   */
  private publishState(): void {
    const state = this.getHeatState();
    
    unifiedBus.publish({
      systemName: 'PositionHeatTracker',
      timestamp: Date.now(),
      ready: true,
      coherence: 1 - state.totalHeat, // Lower heat = higher coherence
      confidence: state.canAddPosition ? 0.8 : 0.2,
      signal: state.maxHeatReached ? 'SELL' : 'NEUTRAL',
      data: {
        totalHeat: state.totalHeat,
        btcHeat: state.btcHeat,
        ethHeat: state.ethHeat,
        altHeat: state.altHeat,
        positionCount: this.positions.size,
        canAddPosition: state.canAddPosition,
      },
    });
  }

  /**
   * Get suggested position size based on available heat
   */
  getSuggestedPositionSize(symbol: string): number {
    const group = this.getCorrelationGroup(symbol);
    const multiplier = HEAT_MULTIPLIERS[group] || 0.7;
    const currentState = this.getHeatState();
    const groupHeat = this.getGroupHeat(group);
    
    // Calculate available heat (minimum of total and group limits)
    const availableTotalHeat = MAX_TOTAL_HEAT - currentState.totalHeat;
    const availableGroupHeat = MAX_GROUP_HEAT - groupHeat;
    const availableHeat = Math.min(availableTotalHeat, availableGroupHeat);
    
    // Convert heat back to position size
    const maxPositionSize = (availableHeat / multiplier) * this.totalCapital;
    
    return Math.max(0, maxPositionSize);
  }
}

// Singleton instance
export const positionHeatTracker = new PositionHeatTracker();
