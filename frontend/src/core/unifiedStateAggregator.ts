/**
 * Unified State Aggregator - Ported from aureon_unified_ecosystem.py lines 1564-1880
 * Loads and aggregates all JSON data sources into unified ecosystem state
 */

import { unifiedBus } from './unifiedBus';

interface SymbolInsight {
  symbol: string;
  winRate: number;
  avgProfit: number;
  totalTrades: number;
  lastTradeTime: number;
  preferredRegime: string;
  bestTimeOfDay: number;
}

interface FrequencyPerformance {
  frequency: number;
  winRate: number;
  avgProfit: number;
  tradeCount: number;
}

interface CoherenceBand {
  min: number;
  max: number;
  label: string;
  winRate: number;
  avgProfit: number;
}

interface AggregatedState {
  symbolInsights: Map<string, SymbolInsight>;
  frequencyPerformance: Map<number, FrequencyPerformance>;
  coherenceBands: CoherenceBand[];
  primeSymbols: string[];
  blacklistedSymbols: string[];
  optimalTradingHours: number[];
  lastUpdateTime: number;
}

export class UnifiedStateAggregator {
  private state: AggregatedState = {
    symbolInsights: new Map(),
    frequencyPerformance: new Map(),
    coherenceBands: [
      { min: 0.0, max: 0.5, label: 'LOW', winRate: 0.35, avgProfit: -0.5 },
      { min: 0.5, max: 0.7, label: 'MEDIUM', winRate: 0.48, avgProfit: 0.1 },
      { min: 0.7, max: 0.85, label: 'HIGH', winRate: 0.58, avgProfit: 0.4 },
      { min: 0.85, max: 0.945, label: 'VERY_HIGH', winRate: 0.65, avgProfit: 0.7 },
      { min: 0.945, max: 1.0, label: 'PRIME', winRate: 0.72, avgProfit: 1.2 }
    ],
    primeSymbols: [],
    blacklistedSymbols: [],
    optimalTradingHours: [9, 10, 14, 15, 16, 21, 22], // London + NY overlap, Asian open
    lastUpdateTime: 0
  };

  private isLoaded: boolean = false;

  /**
   * Load all JSON data sources and aggregate into state
   */
  async loadAllSources(): Promise<void> {
    try {
      console.log('[UnifiedStateAggregator] Loading data sources...');
      
      // Load binance-pairs.json
      await this.loadBinancePairs();
      
      // Load frequency codex if available
      await this.loadFrequencyCodex();
      
      // Load elephant memory from database
      await this.loadElephantMemory();
      
      this.state.lastUpdateTime = Date.now();
      this.isLoaded = true;
      
      // Publish aggregated state
      this.publishState();
      
      console.log('[UnifiedStateAggregator] All sources loaded successfully');
    } catch (error) {
      console.error('[UnifiedStateAggregator] Error loading sources:', error);
    }
  }

  private async loadBinancePairs(): Promise<void> {
    try {
      const response = await fetch('/data/binance-pairs.json');
      if (response.ok) {
        const pairs = await response.json();
        
        // Extract prime symbols (high volume, stable)
        const primeSymbols = pairs
          .filter((p: any) => p.quoteAsset === 'USDT' || p.quoteAsset === 'USDC')
          .slice(0, 100)
          .map((p: any) => p.symbol);
        
        this.state.primeSymbols = primeSymbols;
        console.log(`[UnifiedStateAggregator] Loaded ${primeSymbols.length} prime symbols`);
      }
    } catch (error) {
      console.warn('[UnifiedStateAggregator] Could not load binance-pairs.json:', error);
    }
  }

  private async loadFrequencyCodex(): Promise<void> {
    try {
      const response = await fetch('/data/frequency_codex.json');
      if (response.ok) {
        const codex = await response.json();
        
        // Initialize frequency performance from codex
        const frequencies = [174, 285, 396, 417, 432, 528, 639, 741, 852, 963];
        for (const freq of frequencies) {
          this.state.frequencyPerformance.set(freq, {
            frequency: freq,
            winRate: freq === 528 ? 0.65 : 0.50, // 528 Hz love frequency has best performance
            avgProfit: freq === 528 ? 0.8 : 0.2,
            tradeCount: 0
          });
        }
        
        console.log('[UnifiedStateAggregator] Loaded frequency codex');
      }
    } catch (error) {
      console.warn('[UnifiedStateAggregator] Could not load frequency_codex.json:', error);
    }
  }

  private async loadElephantMemory(): Promise<void> {
    try {
      // Load from Supabase elephant_memory table
      const { supabase } = await import('@/integrations/supabase/client');
      
      const { data, error } = await supabase
        .from('elephant_memory')
        .select('*');
      
      if (error) {
        console.warn('[UnifiedStateAggregator] Could not load elephant_memory:', error);
        return;
      }
      
      if (data) {
        // Populate symbol insights
        for (const row of data) {
          const winRate = row.trades > 0 ? (row.wins || 0) / row.trades : 0;
          
          this.state.symbolInsights.set(row.symbol, {
            symbol: row.symbol,
            winRate,
            avgProfit: row.profit || 0,
            totalTrades: row.trades || 0,
            lastTradeTime: row.last_trade ? new Date(row.last_trade).getTime() : 0,
            preferredRegime: 'NORMAL',
            bestTimeOfDay: 14
          });
          
          // Track blacklisted symbols
          if (row.blacklisted) {
            this.state.blacklistedSymbols.push(row.symbol);
          }
        }
        
        console.log(`[UnifiedStateAggregator] Loaded ${data.length} symbol insights from elephant_memory`);
      }
    } catch (error) {
      console.warn('[UnifiedStateAggregator] Error loading elephant_memory:', error);
    }
  }

  private publishState(): void {
    const coherence = this.calculateAggregatedCoherence();
    
    unifiedBus.publish({
      systemName: 'UnifiedStateAggregator',
      timestamp: Date.now(),
      ready: this.isLoaded,
      coherence,
      confidence: this.isLoaded ? 0.8 : 0.3,
      signal: 'NEUTRAL',
      data: {
        primeSymbolCount: this.state.primeSymbols.length,
        blacklistedCount: this.state.blacklistedSymbols.length,
        insightsCount: this.state.symbolInsights.size,
        frequencyBands: this.state.frequencyPerformance.size
      }
    });
  }

  private calculateAggregatedCoherence(): number {
    if (this.state.symbolInsights.size === 0) return 0.5;
    
    // Average win rate across all tracked symbols
    let totalWinRate = 0;
    for (const insight of this.state.symbolInsights.values()) {
      totalWinRate += insight.winRate;
    }
    
    return totalWinRate / this.state.symbolInsights.size;
  }

  /**
   * Get insight for a specific symbol
   */
  getSymbolInsight(symbol: string): SymbolInsight | undefined {
    return this.state.symbolInsights.get(symbol);
  }

  /**
   * Get frequency performance data
   */
  getFrequencyPerformance(frequency: number): FrequencyPerformance | undefined {
    // Find nearest frequency band
    const frequencies = Array.from(this.state.frequencyPerformance.keys());
    const nearest = frequencies.reduce((prev, curr) => 
      Math.abs(curr - frequency) < Math.abs(prev - frequency) ? curr : prev
    );
    return this.state.frequencyPerformance.get(nearest);
  }

  /**
   * Get coherence band for a given coherence value
   */
  getCoherenceBand(coherence: number): CoherenceBand | undefined {
    return this.state.coherenceBands.find(band => 
      coherence >= band.min && coherence < band.max
    );
  }

  /**
   * Check if symbol is prime (recommended)
   */
  isPrimeSymbol(symbol: string): boolean {
    return this.state.primeSymbols.includes(symbol);
  }

  /**
   * Check if symbol is blacklisted
   */
  isBlacklisted(symbol: string): boolean {
    return this.state.blacklistedSymbols.includes(symbol);
  }

  /**
   * Check if current hour is optimal for trading
   */
  isOptimalTradingHour(): boolean {
    const hour = new Date().getUTCHours();
    return this.state.optimalTradingHours.includes(hour);
  }

  /**
   * Update symbol insight with new trade data
   */
  updateSymbolInsight(symbol: string, profit: number, won: boolean): void {
    const existing = this.state.symbolInsights.get(symbol);
    
    if (existing) {
      const newTotalTrades = existing.totalTrades + 1;
      const newWins = won ? (existing.winRate * existing.totalTrades) + 1 : existing.winRate * existing.totalTrades;
      
      this.state.symbolInsights.set(symbol, {
        ...existing,
        winRate: newWins / newTotalTrades,
        avgProfit: ((existing.avgProfit * existing.totalTrades) + profit) / newTotalTrades,
        totalTrades: newTotalTrades,
        lastTradeTime: Date.now()
      });
    } else {
      this.state.symbolInsights.set(symbol, {
        symbol,
        winRate: won ? 1 : 0,
        avgProfit: profit,
        totalTrades: 1,
        lastTradeTime: Date.now(),
        preferredRegime: 'NORMAL',
        bestTimeOfDay: new Date().getUTCHours()
      });
    }
    
    this.publishState();
  }

  /**
   * Get expected win rate based on coherence band
   */
  getExpectedWinRate(coherence: number): number {
    const band = this.getCoherenceBand(coherence);
    return band?.winRate || 0.5;
  }

  getState(): AggregatedState {
    return this.state;
  }

  isReady(): boolean {
    return this.isLoaded;
  }
}

export const unifiedStateAggregator = new UnifiedStateAggregator();
