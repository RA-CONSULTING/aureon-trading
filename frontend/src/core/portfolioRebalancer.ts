/**
 * Portfolio Rebalancer - Ported from aureon_unified_ecosystem.py lines 861-1097
 * Maintains target allocations across exchanges by calculating and executing rebalance trades
 */

import { unifiedBus } from './unifiedBus';

interface TargetAllocation {
  asset: string;
  targetPercent: number;
}

interface AssetBalance {
  asset: string;
  exchange: string;
  quantity: number;
  usdValue: number;
}

interface RebalanceTrade {
  asset: string;
  exchange: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  usdValue: number;
  reason: string;
}

interface RebalanceResult {
  needsRebalance: boolean;
  currentAllocations: Map<string, number>;
  targetAllocations: Map<string, number>;
  deviations: Map<string, number>;
  trades: RebalanceTrade[];
  totalPortfolioValue: number;
  maxDeviation: number;
  timestamp: number;
}

export class PortfolioRebalancer {
  private targetAllocations: TargetAllocation[] = [
    { asset: 'BTC', targetPercent: 30 },
    { asset: 'ETH', targetPercent: 25 },
    { asset: 'USDT', targetPercent: 35 },
    { asset: 'USDC', targetPercent: 10 }
  ];
  
  private rebalanceThreshold: number = 5.0; // Trigger rebalance if deviation > 5%
  private minTradeValue: number = 20; // Minimum trade value in USD
  private lastRebalance: number = 0;
  private rebalanceCooldown: number = 3600000; // 1 hour cooldown

  constructor(config?: {
    targetAllocations?: TargetAllocation[];
    rebalanceThreshold?: number;
    minTradeValue?: number;
    rebalanceCooldown?: number;
  }) {
    if (config?.targetAllocations) this.targetAllocations = config.targetAllocations;
    if (config?.rebalanceThreshold) this.rebalanceThreshold = config.rebalanceThreshold;
    if (config?.minTradeValue) this.minTradeValue = config.minTradeValue;
    if (config?.rebalanceCooldown) this.rebalanceCooldown = config.rebalanceCooldown;
  }

  /**
   * Analyze current portfolio and determine if rebalancing is needed
   */
  analyzePortfolio(balances: AssetBalance[]): RebalanceResult {
    const now = Date.now();
    
    // Calculate total portfolio value
    const totalValue = balances.reduce((sum, b) => sum + b.usdValue, 0);
    
    // Calculate current allocations by asset
    const currentAllocations = new Map<string, number>();
    const assetValues = new Map<string, number>();
    
    for (const balance of balances) {
      const current = assetValues.get(balance.asset) || 0;
      assetValues.set(balance.asset, current + balance.usdValue);
    }
    
    for (const [asset, value] of assetValues) {
      currentAllocations.set(asset, totalValue > 0 ? (value / totalValue) * 100 : 0);
    }
    
    // Calculate target allocations map
    const targetAllocationsMap = new Map<string, number>();
    for (const target of this.targetAllocations) {
      targetAllocationsMap.set(target.asset, target.targetPercent);
    }
    
    // Calculate deviations
    const deviations = new Map<string, number>();
    let maxDeviation = 0;
    
    for (const target of this.targetAllocations) {
      const currentPercent = currentAllocations.get(target.asset) || 0;
      const deviation = currentPercent - target.targetPercent;
      deviations.set(target.asset, deviation);
      maxDeviation = Math.max(maxDeviation, Math.abs(deviation));
    }
    
    // Check if rebalance is needed
    const cooldownPassed = now - this.lastRebalance > this.rebalanceCooldown;
    const needsRebalance = maxDeviation > this.rebalanceThreshold && cooldownPassed;
    
    // Generate rebalance trades
    const trades: RebalanceTrade[] = [];
    
    if (needsRebalance) {
      // Sort by deviation: sells first (positive deviation), then buys (negative deviation)
      const sortedDeviations = Array.from(deviations.entries())
        .sort((a, b) => b[1] - a[1]);
      
      for (const [asset, deviation] of sortedDeviations) {
        if (Math.abs(deviation) < 1.0) continue; // Skip small deviations
        
        const tradeValue = Math.abs((deviation / 100) * totalValue);
        if (tradeValue < this.minTradeValue) continue;
        
        // Find best exchange for this asset
        const assetBalances = balances.filter(b => b.asset === asset);
        const bestExchange = assetBalances.length > 0 
          ? assetBalances.reduce((a, b) => a.usdValue > b.usdValue ? a : b).exchange
          : 'binance';
        
        const currentPrice = assetBalances.length > 0 && assetBalances[0].quantity > 0
          ? assetBalances[0].usdValue / assetBalances[0].quantity
          : 1;
        
        trades.push({
          asset,
          exchange: bestExchange,
          side: deviation > 0 ? 'SELL' : 'BUY',
          quantity: currentPrice > 0 ? tradeValue / currentPrice : 0,
          usdValue: tradeValue,
          reason: `${deviation > 0 ? 'Over' : 'Under'}weight by ${Math.abs(deviation).toFixed(1)}%`
        });
      }
    }
    
    // Publish state to UnifiedBus
    unifiedBus.publish({
      systemName: 'PortfolioRebalancer',
      timestamp: now,
      ready: true,
      coherence: 1 - (maxDeviation / 100),
      confidence: needsRebalance ? 0.8 : 0.5,
      signal: 'NEUTRAL',
      data: {
        totalPortfolioValue: totalValue,
        maxDeviation,
        needsRebalance,
        tradesCount: trades.length
      }
    });
    
    return {
      needsRebalance,
      currentAllocations,
      targetAllocations: targetAllocationsMap,
      deviations,
      trades,
      totalPortfolioValue: totalValue,
      maxDeviation,
      timestamp: now
    };
  }

  /**
   * Execute rebalance trades (sells first, then buys)
   */
  async executeRebalance(result: RebalanceResult, executeTradeCallback: (trade: RebalanceTrade) => Promise<boolean>): Promise<{
    executed: RebalanceTrade[];
    failed: RebalanceTrade[];
    success: boolean;
  }> {
    const executed: RebalanceTrade[] = [];
    const failed: RebalanceTrade[] = [];
    
    // Sort trades: SELL first, then BUY
    const sortedTrades = [...result.trades].sort((a, b) => {
      if (a.side === 'SELL' && b.side === 'BUY') return -1;
      if (a.side === 'BUY' && b.side === 'SELL') return 1;
      return b.usdValue - a.usdValue; // Larger trades first within same side
    });
    
    for (const trade of sortedTrades) {
      try {
        const success = await executeTradeCallback(trade);
        if (success) {
          executed.push(trade);
        } else {
          failed.push(trade);
        }
      } catch (error) {
        console.error(`[PortfolioRebalancer] Trade execution failed:`, error);
        failed.push(trade);
      }
    }
    
    if (executed.length > 0) {
      this.lastRebalance = Date.now();
    }
    
    return {
      executed,
      failed,
      success: failed.length === 0 && executed.length > 0
    };
  }

  /**
   * Set new target allocations
   */
  setTargetAllocations(allocations: TargetAllocation[]): void {
    // Validate total is 100%
    const total = allocations.reduce((sum, a) => sum + a.targetPercent, 0);
    if (Math.abs(total - 100) > 0.01) {
      throw new Error(`Target allocations must sum to 100%, got ${total}%`);
    }
    this.targetAllocations = allocations;
  }

  getTargetAllocations(): TargetAllocation[] {
    return [...this.targetAllocations];
  }
}

export const portfolioRebalancer = new PortfolioRebalancer();
