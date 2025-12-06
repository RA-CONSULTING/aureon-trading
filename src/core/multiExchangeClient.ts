/**
 * Multi-Exchange Client
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Aggregates data from all connected exchanges via authenticated get-user-balances
 * Provides unified view of balances, tickers, and positions
 * NOW PUBLISHES TO UNIFIED BUS for ecosystem integration
 */

import { ExchangeType, EXCHANGE_FEES } from './unifiedExchangeClient';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { unifiedBus, type SignalType } from './unifiedBus';
import { supabase } from '@/integrations/supabase/client';

export interface ConsolidatedBalance {
  asset: string;
  balances: Record<string, { free: number; locked: number; total: number }>;
  totalFree: number;
  totalLocked: number;
  grandTotal: number;
  usdValue: number;
}

export interface ExchangeStatus {
  exchange: ExchangeType;
  connected: boolean;
  lastUpdate: number;
  balanceCount: number;
  totalUsdValue: number;
  error?: string;
}

export interface MultiExchangeState {
  exchanges: ExchangeStatus[];
  consolidatedBalances: ConsolidatedBalance[];
  totalEquityUsd: number;
  lastUpdate: number;
}

const SUPPORTED_EXCHANGES: ExchangeType[] = ['binance', 'kraken', 'alpaca', 'capital'];

export class MultiExchangeClient {
  private statusCache: Map<ExchangeType, ExchangeStatus> = new Map();
  private consolidatedBalances: ConsolidatedBalance[] = [];
  private listeners: Array<(state: MultiExchangeState) => void> = [];
  private updateInterval: ReturnType<typeof setInterval> | null = null;
  private isInitialized = false;
  private totalEquityUsd = 0;

  constructor() {
    console.log('🌐 Multi-Exchange Client initializing...');
  }

  /**
   * Initialize all exchange clients
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    // Register with Temporal Ladder
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);

    // Initialize status cache for each supported exchange
    for (const exchange of SUPPORTED_EXCHANGES) {
      this.statusCache.set(exchange, {
        exchange,
        connected: false,
        lastUpdate: 0,
        balanceCount: 0,
        totalUsdValue: 0
      });
    }

    // Start periodic updates
    this.startPeriodicUpdates();
    this.isInitialized = true;

    console.log(`🌐 Multi-Exchange Client initialized`);
  }

  /**
   * Fetch balances from all exchanges using authenticated get-user-balances
   */
  public async fetchAllBalances(): Promise<MultiExchangeState> {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        console.warn('[MultiExchangeClient] No session, returning cached state');
        return this.getState();
      }

      const { data, error } = await supabase.functions.invoke('get-user-balances', {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (error) {
        console.error('[MultiExchangeClient] API error:', error);
        return this.getState();
      }

      if (data?.success) {
        // Update status cache from response
        const balances = data.balances || [];
        
        for (const exchangeData of balances) {
          const exchange = exchangeData.exchange as ExchangeType;
          this.statusCache.set(exchange, {
            exchange,
            connected: exchangeData.connected,
            lastUpdate: Date.now(),
            balanceCount: exchangeData.assets?.length || 0,
            totalUsdValue: exchangeData.totalUsd || 0,
            error: exchangeData.error
          });
        }

        // Build consolidated balances
        const assetMap = new Map<string, ConsolidatedBalance>();
        
        for (const exchangeData of balances) {
          if (!exchangeData.connected) continue;
          
          for (const asset of (exchangeData.assets || [])) {
            const existing = assetMap.get(asset.asset);
            if (existing) {
              existing.totalFree += asset.free;
              existing.totalLocked += asset.locked;
              existing.grandTotal += asset.free + asset.locked;
              existing.usdValue += asset.usdValue;
              existing.balances[exchangeData.exchange] = { 
                free: asset.free, 
                locked: asset.locked, 
                total: asset.free + asset.locked 
              };
            } else {
              assetMap.set(asset.asset, {
                asset: asset.asset,
                totalFree: asset.free,
                totalLocked: asset.locked,
                grandTotal: asset.free + asset.locked,
                usdValue: asset.usdValue,
                balances: { 
                  [exchangeData.exchange]: { 
                    free: asset.free, 
                    locked: asset.locked, 
                    total: asset.free + asset.locked 
                  } 
                }
              });
            }
          }
        }

        this.consolidatedBalances = Array.from(assetMap.values())
          .sort((a, b) => b.usdValue - a.usdValue);
        this.totalEquityUsd = data.totalEquityUsd || 0;
      }

    } catch (error) {
      console.error('[MultiExchangeClient] Fetch error:', error);
    }
    
    const state = this.getState();
    this.notifyListeners(state);
    
    // Send heartbeat to Temporal Ladder
    const activeCount = state.exchanges.filter(e => e.connected).length;
    const healthRatio = state.exchanges.length > 0 ? activeCount / state.exchanges.length : 0;
    temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, healthRatio);
    
    // PUBLISH TO UNIFIED BUS for ecosystem integration
    this.publishToUnifiedBus(state);
    
    return state;
  }

  /**
   * Publish exchange state to UnifiedBus for ecosystem-wide visibility
   */
  private publishToUnifiedBus(state: MultiExchangeState): void {
    const connectedCount = state.exchanges.filter(e => e.connected).length;
    const totalExchanges = state.exchanges.length;
    const healthRatio = totalExchanges > 0 ? connectedCount / totalExchanges : 0;
    
    // Derive signal from balance health
    let signal: SignalType = 'NEUTRAL';
    if (state.totalEquityUsd > 1000 && healthRatio >= 0.5) {
      signal = 'BUY'; // Sufficient capital available
    } else if (state.totalEquityUsd < 100 || healthRatio < 0.25) {
      signal = 'SELL'; // Low capital or poor exchange connectivity
    }
    
    unifiedBus.publish({
      systemName: 'MultiExchange',
      timestamp: Date.now(),
      ready: connectedCount > 0,
      coherence: healthRatio,
      confidence: Math.min(healthRatio + 0.2, 1),
      signal,
      data: {
        totalEquityUsd: state.totalEquityUsd,
        connectedExchanges: connectedCount,
        totalExchanges,
        exchanges: state.exchanges.map(e => ({
          name: e.exchange,
          connected: e.connected,
          usdValue: e.totalUsdValue
        })),
        topAssets: state.consolidatedBalances.slice(0, 5).map(b => ({
          asset: b.asset,
          total: b.grandTotal,
          usdValue: b.usdValue
        }))
      }
    });
  }


  /**
   * Get available balance for position sizing
   */
  public getAvailableBalanceForTrading(quoteAsset: string = 'USDT'): number {
    const consolidated = this.getConsolidatedBalances();
    const quoteBalance = consolidated.find(b => b.asset === quoteAsset);
    return quoteBalance?.totalFree || 0;
  }

  /**
   * Calculate position size based on available equity and risk percentage
   */
  public calculatePositionSize(
    riskPercentage: number = 0.02,
    quoteAsset: string = 'USDT'
  ): { positionSizeUsd: number; availableBalance: number; riskAmount: number } {
    const availableBalance = this.getAvailableBalanceForTrading(quoteAsset);
    const totalEquity = this.getTotalEquityUsd();
    const riskAmount = totalEquity * riskPercentage;
    const positionSizeUsd = Math.min(riskAmount, availableBalance * 0.95); // Leave 5% buffer
    
    return {
      positionSizeUsd: Math.max(0, positionSizeUsd),
      availableBalance,
      riskAmount
    };
  }

  /**
   * Get consolidated balances across all exchanges
   */
  public getConsolidatedBalances(): ConsolidatedBalance[] {
    return this.consolidatedBalances;
  }

  /**
   * Get total equity in USD
   */
  public getTotalEquityUsd(): number {
    return this.totalEquityUsd;
  }

  /**
   * Get current state
   */
  public getState(): MultiExchangeState {
    return {
      exchanges: Array.from(this.statusCache.values()),
      consolidatedBalances: this.consolidatedBalances,
      totalEquityUsd: this.totalEquityUsd,
      lastUpdate: Date.now()
    };
  }

  /**
   * Get best exchange for a symbol based on fees
   */
  public getBestExchangeForSymbol(symbol: string): ExchangeType {
    // Return exchange with lowest taker fee from connected exchanges
    let bestExchange: ExchangeType = 'binance';
    let lowestFee = Infinity;

    for (const status of this.statusCache.values()) {
      if (status.connected) {
        const fees = EXCHANGE_FEES[status.exchange];
        if (fees.taker < lowestFee) {
          lowestFee = fees.taker;
          bestExchange = status.exchange;
        }
      }
    }

    return bestExchange;
  }

  /**
   * Get ticker from connected exchanges (stub for compatibility)
   * Returns simulated ticker data based on available balance info
   */
  public async getTickersFromAllExchanges(symbol: string): Promise<Map<ExchangeType, { symbol: string; price: number; bidPrice: number; askPrice: number; volume: number } | null>> {
    const results = new Map<ExchangeType, { symbol: string; price: number; bidPrice: number; askPrice: number; volume: number } | null>();
    
    // Get current BTC price from public API for realistic simulation
    try {
      const response = await fetch('https://api.binance.com/api/v3/ticker/bookTicker?symbol=' + symbol);
      const data = await response.json();
      const bidPrice = parseFloat(data.bidPrice);
      const askPrice = parseFloat(data.askPrice);
      const midPrice = (bidPrice + askPrice) / 2;

      for (const status of this.statusCache.values()) {
        if (status.connected) {
          // Add slight variation per exchange
          const variation = (Math.random() - 0.5) * 0.0002;
          results.set(status.exchange, {
            symbol,
            price: midPrice * (1 + variation),
            bidPrice: bidPrice * (1 + variation),
            askPrice: askPrice * (1 + variation),
            volume: 1000000
          });
        } else {
          results.set(status.exchange, null);
        }
      }
    } catch {
      // Return null for all if API fails
      for (const status of this.statusCache.values()) {
        results.set(status.exchange, null);
      }
    }
    
    return results;
  }

  /**
   * Subscribe to state updates
   */
  public subscribe(listener: (state: MultiExchangeState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(state: MultiExchangeState): void {
    this.listeners.forEach(listener => {
      try {
        listener(state);
      } catch (error) {
        console.error('Multi-exchange listener error:', error);
      }
    });
  }

  private startPeriodicUpdates(): void {
    if (this.updateInterval) return;

    // Update every 30 seconds
    this.updateInterval = setInterval(() => {
      this.fetchAllBalances().catch(console.error);
    }, 30000);

    // Initial fetch
    this.fetchAllBalances().catch(console.error);
  }

  /**
   * Cleanup resources
   */
  public destroy(): void {
    if (this.updateInterval) {
      clearInterval(this.updateInterval);
      this.updateInterval = null;
    }
    this.listeners = [];
    this.statusCache.clear();
    this.consolidatedBalances = [];
    this.isInitialized = false;
  }
}

// Singleton instance
export const multiExchangeClient = new MultiExchangeClient();
