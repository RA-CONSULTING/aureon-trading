/**
 * Exchange Learning Tracker - Multi-Exchange Performance Aggregation
 * Tracks win rates, profits, and learning metrics per exchange
 */

import { unifiedBus } from './unifiedBus';
import { supabase } from '@/integrations/supabase/client';

export type ExchangeType = 'binance' | 'kraken' | 'alpaca' | 'capital';

interface ExchangeMetrics {
  exchange: ExchangeType;
  totalTrades: number;
  wins: number;
  losses: number;
  winRate: number;
  totalProfit: number;
  avgProfit: number;
  avgLatency: number;
  failedOrders: number;
  successRate: number;
  bestSymbol: string;
  worstSymbol: string;
  lastTradeTime: number;
}

interface SymbolExchangePerformance {
  symbol: string;
  exchange: ExchangeType;
  trades: number;
  winRate: number;
  avgProfit: number;
  avgSlippage: number;
}

interface LearningState {
  exchangeMetrics: Map<ExchangeType, ExchangeMetrics>;
  symbolPerformance: Map<string, SymbolExchangePerformance[]>;
  preferredExchangeBySymbol: Map<string, ExchangeType>;
  overallWinRate: number;
  totalProfit: number;
  lastUpdateTime: number;
}

const EXCHANGES: ExchangeType[] = ['binance', 'kraken', 'alpaca', 'capital'];

export class ExchangeLearningTracker {
  private state: LearningState = {
    exchangeMetrics: new Map(),
    symbolPerformance: new Map(),
    preferredExchangeBySymbol: new Map(),
    overallWinRate: 0.5,
    totalProfit: 0,
    lastUpdateTime: 0
  };

  constructor() {
    // Initialize empty metrics for all exchanges
    for (const exchange of EXCHANGES) {
      this.state.exchangeMetrics.set(exchange, this.createEmptyMetrics(exchange));
    }
  }

  private createEmptyMetrics(exchange: ExchangeType): ExchangeMetrics {
    return {
      exchange,
      totalTrades: 0,
      wins: 0,
      losses: 0,
      winRate: 0.5,
      totalProfit: 0,
      avgProfit: 0,
      avgLatency: 0,
      failedOrders: 0,
      successRate: 1,
      bestSymbol: '',
      worstSymbol: '',
      lastTradeTime: 0
    };
  }

  /**
   * Load historical performance from database
   */
  async loadFromDatabase(): Promise<void> {
    try {
      console.log('[ExchangeLearningTracker] Loading historical performance...');

      const { data, error } = await supabase
        .from('trading_executions')
        .select('*')
        .order('executed_at', { ascending: false })
        .limit(1000);

      if (error) {
        console.warn('[ExchangeLearningTracker] Error loading executions:', error);
        return;
      }

      if (data && data.length > 0) {
        // Process each execution
        for (const exec of data) {
          // Use routing_exchange column if available, default to 'binance'
          const exchange = ((exec as any).routing_exchange || 'binance') as ExchangeType;
          // Calculate profit from price difference (entry vs executed)
          const profit = (exec as any).profit_loss || 0;
          const won = profit > 0;

          this.recordTradeInternal(
            exchange,
            exec.symbol,
            profit,
            won,
            50, // Default latency
            new Date(exec.executed_at).getTime()
          );
        }

        this.calculateAggregates();
        console.log(`[ExchangeLearningTracker] Loaded ${data.length} historical trades`);
      }

      this.publishState();
    } catch (error) {
      console.error('[ExchangeLearningTracker] Load error:', error);
    }
  }

  /**
   * Record a new trade for learning
   */
  recordTrade(
    exchange: ExchangeType,
    symbol: string,
    profit: number,
    won: boolean,
    latencyMs: number = 50
  ): void {
    this.recordTradeInternal(exchange, symbol, profit, won, latencyMs, Date.now());
    this.calculateAggregates();
    this.publishState();
  }

  private recordTradeInternal(
    exchange: ExchangeType,
    symbol: string,
    profit: number,
    won: boolean,
    latencyMs: number,
    timestamp: number
  ): void {
    // Update exchange metrics
    const metrics = this.state.exchangeMetrics.get(exchange) || this.createEmptyMetrics(exchange);
    
    metrics.totalTrades++;
    if (won) {
      metrics.wins++;
    } else {
      metrics.losses++;
    }
    metrics.winRate = metrics.wins / metrics.totalTrades;
    metrics.totalProfit += profit;
    metrics.avgProfit = metrics.totalProfit / metrics.totalTrades;
    metrics.avgLatency = ((metrics.avgLatency * (metrics.totalTrades - 1)) + latencyMs) / metrics.totalTrades;
    metrics.lastTradeTime = timestamp;
    
    this.state.exchangeMetrics.set(exchange, metrics);

    // Update symbol performance per exchange
    const symbolPerf = this.state.symbolPerformance.get(symbol) || [];
    const existing = symbolPerf.find(p => p.exchange === exchange);
    
    if (existing) {
      existing.trades++;
      existing.winRate = ((existing.winRate * (existing.trades - 1)) + (won ? 1 : 0)) / existing.trades;
      existing.avgProfit = ((existing.avgProfit * (existing.trades - 1)) + profit) / existing.trades;
    } else {
      symbolPerf.push({
        symbol,
        exchange,
        trades: 1,
        winRate: won ? 1 : 0,
        avgProfit: profit,
        avgSlippage: 0.001 // Default 0.1%
      });
    }
    
    this.state.symbolPerformance.set(symbol, symbolPerf);
  }

  /**
   * Record failed order for learning
   */
  recordFailedOrder(exchange: ExchangeType): void {
    const metrics = this.state.exchangeMetrics.get(exchange);
    if (metrics) {
      metrics.failedOrders++;
      metrics.successRate = (metrics.totalTrades) / (metrics.totalTrades + metrics.failedOrders);
      this.state.exchangeMetrics.set(exchange, metrics);
      this.publishState();
    }
  }

  private calculateAggregates(): void {
    let totalWins = 0;
    let totalTrades = 0;
    let totalProfit = 0;

    // Aggregate across exchanges
    for (const metrics of this.state.exchangeMetrics.values()) {
      totalWins += metrics.wins;
      totalTrades += metrics.totalTrades;
      totalProfit += metrics.totalProfit;

      // Find best/worst symbols for this exchange
      this.updateBestWorstSymbols(metrics);
    }

    this.state.overallWinRate = totalTrades > 0 ? totalWins / totalTrades : 0.5;
    this.state.totalProfit = totalProfit;
    this.state.lastUpdateTime = Date.now();

    // Calculate preferred exchange per symbol
    this.calculatePreferredExchanges();
  }

  private updateBestWorstSymbols(metrics: ExchangeMetrics): void {
    let bestProfit = -Infinity;
    let worstProfit = Infinity;
    
    for (const [symbol, perfs] of this.state.symbolPerformance.entries()) {
      const perf = perfs.find(p => p.exchange === metrics.exchange);
      if (perf && perf.trades >= 3) {
        if (perf.avgProfit > bestProfit) {
          bestProfit = perf.avgProfit;
          metrics.bestSymbol = symbol;
        }
        if (perf.avgProfit < worstProfit) {
          worstProfit = perf.avgProfit;
          metrics.worstSymbol = symbol;
        }
      }
    }
  }

  private calculatePreferredExchanges(): void {
    for (const [symbol, perfs] of this.state.symbolPerformance.entries()) {
      if (perfs.length === 0) continue;
      
      // Score = winRate * 0.5 + (1 - avgSlippage) * 0.3 + successRate * 0.2
      let bestExchange: ExchangeType = 'binance';
      let bestScore = -1;
      
      for (const perf of perfs) {
        const exchangeMetrics = this.state.exchangeMetrics.get(perf.exchange);
        const successRate = exchangeMetrics?.successRate || 1;
        const score = perf.winRate * 0.5 + (1 - perf.avgSlippage) * 0.3 + successRate * 0.2;
        
        if (score > bestScore) {
          bestScore = score;
          bestExchange = perf.exchange;
        }
      }
      
      this.state.preferredExchangeBySymbol.set(symbol, bestExchange);
    }
  }

  private publishState(): void {
    const coherence = this.state.overallWinRate;
    
    unifiedBus.publish({
      systemName: 'ExchangeLearningTracker',
      timestamp: Date.now(),
      ready: true,
      coherence,
      confidence: Math.min(0.95, 0.5 + (this.getTotalTrades() / 1000)),
      signal: coherence > 0.55 ? 'BUY' : coherence < 0.45 ? 'SELL' : 'NEUTRAL',
      data: {
        overallWinRate: this.state.overallWinRate,
        totalProfit: this.state.totalProfit,
        totalTrades: this.getTotalTrades(),
        exchangeCount: this.state.exchangeMetrics.size
      }
    });
  }

  /**
   * Get preferred exchange for a symbol based on historical performance
   */
  getPreferredExchange(symbol: string): ExchangeType {
    return this.state.preferredExchangeBySymbol.get(symbol) || 'binance';
  }

  /**
   * Get metrics for a specific exchange
   */
  getExchangeMetrics(exchange: ExchangeType): ExchangeMetrics | undefined {
    return this.state.exchangeMetrics.get(exchange);
  }

  /**
   * Get all exchange metrics
   */
  getAllExchangeMetrics(): ExchangeMetrics[] {
    return Array.from(this.state.exchangeMetrics.values());
  }

  /**
   * Get symbol performance across exchanges
   */
  getSymbolPerformance(symbol: string): SymbolExchangePerformance[] {
    return this.state.symbolPerformance.get(symbol) || [];
  }

  /**
   * Get total trades across all exchanges
   */
  getTotalTrades(): number {
    let total = 0;
    for (const metrics of this.state.exchangeMetrics.values()) {
      total += metrics.totalTrades;
    }
    return total;
  }

  /**
   * Get overall win rate
   */
  getOverallWinRate(): number {
    return this.state.overallWinRate;
  }

  /**
   * Get learning confidence (increases with more data)
   */
  getLearningConfidence(): number {
    const trades = this.getTotalTrades();
    // Sigmoid-like growth: 50% at 0 trades, 90% at 500 trades
    return 0.5 + 0.45 * (1 - Math.exp(-trades / 200));
  }

  getState(): LearningState {
    return this.state;
  }
}

export const exchangeLearningTracker = new ExchangeLearningTracker();
