/**
 * Cross-Exchange Arbitrage Scanner
 * Ported from aureon_unified_ecosystem.py lines 557-697
 * Detects and executes price discrepancies between exchanges
 */

import { unifiedBus } from './unifiedBus';

export interface ArbitrageOpportunity {
  symbol: string;
  buyExchange: string;
  sellExchange: string;
  buyPrice: number;
  sellPrice: number;
  spreadPct: number;
  netProfitPct: number;
  estimatedProfit: number;
  timestamp: number;
  isViable: boolean;
}

export interface ArbitrageScanResult {
  opportunities: ArbitrageOpportunity[];
  bestOpportunity: ArbitrageOpportunity | null;
  totalScanned: number;
  viableCount: number;
  scanDurationMs: number;
}

// Exchange fee configuration (synced from Python)
const EXCHANGE_FEES: Record<string, number> = {
  binance: 0.001,    // 0.10%
  kraken: 0.0026,    // 0.26%
  alpaca: 0.0,       // 0% for stocks
  capital: 0.0005,   // 0.05% spread
};

// Minimum spread to consider (must exceed fees on both sides)
const MIN_SPREAD_PCT = 0.005; // 0.5%

// Maximum position for arbitrage trades
const MAX_ARBITRAGE_POSITION_USD = 1000;

export class CrossExchangeArbitrageScanner {
  private lastScan: ArbitrageScanResult | null = null;
  private priceCache: Map<string, Map<string, { price: number; timestamp: number }>> = new Map();
  private executedArbitrages: ArbitrageOpportunity[] = [];

  /**
   * Update price cache for a symbol on an exchange
   */
  updatePrice(symbol: string, exchange: string, price: number): void {
    if (!this.priceCache.has(symbol)) {
      this.priceCache.set(symbol, new Map());
    }
    this.priceCache.get(symbol)!.set(exchange, {
      price,
      timestamp: Date.now(),
    });
  }

  /**
   * Get cached price for symbol on exchange
   */
  getPrice(symbol: string, exchange: string): number | null {
    const symbolPrices = this.priceCache.get(symbol);
    if (!symbolPrices) return null;
    
    const cached = symbolPrices.get(exchange);
    if (!cached) return null;
    
    // Price is stale after 10 seconds
    if (Date.now() - cached.timestamp > 10000) return null;
    
    return cached.price;
  }

  /**
   * Calculate net profit after fees
   */
  private calculateNetProfit(
    buyPrice: number,
    sellPrice: number,
    buyExchange: string,
    sellExchange: string,
    positionSize: number
  ): { netProfitPct: number; estimatedProfit: number } {
    const buyFee = EXCHANGE_FEES[buyExchange] || 0.001;
    const sellFee = EXCHANGE_FEES[sellExchange] || 0.001;
    
    const grossSpread = (sellPrice - buyPrice) / buyPrice;
    const totalFees = buyFee + sellFee;
    const netProfitPct = grossSpread - totalFees;
    const estimatedProfit = positionSize * netProfitPct;
    
    return { netProfitPct, estimatedProfit };
  }

  /**
   * Scan for direct arbitrage opportunities
   * Direct arbitrage: Buy on Exchange A, Sell on Exchange B
   */
  scanDirectArbitrage(symbols: string[]): ArbitrageScanResult {
    const startTime = Date.now();
    const opportunities: ArbitrageOpportunity[] = [];
    const exchanges = Object.keys(EXCHANGE_FEES);

    for (const symbol of symbols) {
      const symbolPrices = this.priceCache.get(symbol);
      if (!symbolPrices || symbolPrices.size < 2) continue;

      // Compare all exchange pairs
      for (let i = 0; i < exchanges.length; i++) {
        for (let j = i + 1; j < exchanges.length; j++) {
          const exchangeA = exchanges[i];
          const exchangeB = exchanges[j];
          
          const priceA = this.getPrice(symbol, exchangeA);
          const priceB = this.getPrice(symbol, exchangeB);
          
          if (priceA === null || priceB === null) continue;

          // Check both directions
          this.checkArbitrageDirection(
            symbol, exchangeA, priceA, exchangeB, priceB, opportunities
          );
          this.checkArbitrageDirection(
            symbol, exchangeB, priceB, exchangeA, priceA, opportunities
          );
        }
      }
    }

    // Sort by net profit
    opportunities.sort((a, b) => b.netProfitPct - a.netProfitPct);
    
    const viableOpportunities = opportunities.filter(o => o.isViable);
    
    this.lastScan = {
      opportunities,
      bestOpportunity: viableOpportunities[0] || null,
      totalScanned: symbols.length,
      viableCount: viableOpportunities.length,
      scanDurationMs: Date.now() - startTime,
    };

    // Publish to UnifiedBus
    unifiedBus.publish({
      systemName: 'CrossExchangeArbitrage',
      timestamp: Date.now(),
      ready: true,
      coherence: viableOpportunities.length > 0 ? 0.9 : 0.5,
      confidence: this.lastScan.bestOpportunity?.netProfitPct || 0,
      signal: viableOpportunities.length > 0 ? 'BUY' : 'NEUTRAL',
      data: {
        viableCount: viableOpportunities.length,
        bestSpread: this.lastScan.bestOpportunity?.spreadPct || 0,
        scanDurationMs: this.lastScan.scanDurationMs,
      },
    });
    return this.lastScan;
  }

  /**
   * Check arbitrage in one direction
   */
  private checkArbitrageDirection(
    symbol: string,
    buyExchange: string,
    buyPrice: number,
    sellExchange: string,
    sellPrice: number,
    opportunities: ArbitrageOpportunity[]
  ): void {
    if (sellPrice <= buyPrice) return;
    
    const spreadPct = (sellPrice - buyPrice) / buyPrice;
    if (spreadPct < MIN_SPREAD_PCT) return;

    const { netProfitPct, estimatedProfit } = this.calculateNetProfit(
      buyPrice, sellPrice, buyExchange, sellExchange, MAX_ARBITRAGE_POSITION_USD
    );

    opportunities.push({
      symbol,
      buyExchange,
      sellExchange,
      buyPrice,
      sellPrice,
      spreadPct,
      netProfitPct,
      estimatedProfit,
      timestamp: Date.now(),
      isViable: netProfitPct > 0.001, // Must be > 0.1% net profit
    });
  }

  /**
   * Get the last scan result
   */
  getLastScan(): ArbitrageScanResult | null {
    return this.lastScan;
  }

  /**
   * Record executed arbitrage for tracking
   */
  recordExecution(opportunity: ArbitrageOpportunity): void {
    this.executedArbitrages.push({
      ...opportunity,
      timestamp: Date.now(),
    });
    
    // Keep only last 100 executions
    if (this.executedArbitrages.length > 100) {
      this.executedArbitrages = this.executedArbitrages.slice(-100);
    }
  }

  /**
   * Get execution history
   */
  getExecutionHistory(): ArbitrageOpportunity[] {
    return [...this.executedArbitrages];
  }

  /**
   * Get statistics
   */
  getStats(): {
    totalScans: number;
    totalOpportunities: number;
    executedCount: number;
    totalProfit: number;
  } {
    return {
      totalScans: this.lastScan ? 1 : 0,
      totalOpportunities: this.lastScan?.viableCount || 0,
      executedCount: this.executedArbitrages.length,
      totalProfit: this.executedArbitrages.reduce((sum, a) => sum + a.estimatedProfit, 0),
    };
  }
}

// Singleton instance
export const crossExchangeArbitrageScanner = new CrossExchangeArbitrageScanner();
