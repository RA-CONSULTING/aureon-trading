/**
 * Multi-Exchange Client
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Aggregates data from all connected exchanges
 * Provides unified view of balances, tickers, and positions
 */

import { UnifiedExchangeClient, ExchangeBalance, ExchangeTicker, ExchangeType, EXCHANGE_FEES } from './unifiedExchangeClient';
import { temporalLadder, SYSTEMS } from './temporalLadder';

export interface ConsolidatedBalance {
  asset: string;
  balances: Record<ExchangeType, { free: number; locked: number; total: number }>;
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
  private clients: Map<ExchangeType, UnifiedExchangeClient> = new Map();
  private balanceCache: Map<ExchangeType, ExchangeBalance[]> = new Map();
  private statusCache: Map<ExchangeType, ExchangeStatus> = new Map();
  private listeners: Array<(state: MultiExchangeState) => void> = [];
  private updateInterval: number | null = null;
  private isInitialized = false;

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

    // Initialize clients for each supported exchange
    for (const exchange of SUPPORTED_EXCHANGES) {
      const client = new UnifiedExchangeClient({ exchange });
      this.clients.set(exchange, client);
      
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

    console.log(`🌐 Multi-Exchange Client initialized with ${this.clients.size} exchanges`);
  }

  /**
   * Fetch balances from all exchanges
   */
  public async fetchAllBalances(): Promise<MultiExchangeState> {
    const promises = Array.from(this.clients.entries()).map(
      async ([exchange, client]) => {
        try {
          const balances = await client.getBalances();
          this.balanceCache.set(exchange, balances);

          const totalUsdValue = balances.reduce(
            (sum, b) => sum + (b.usdValue || 0),
            0
          );

          this.statusCache.set(exchange, {
            exchange,
            connected: true,
            lastUpdate: Date.now(),
            balanceCount: balances.length,
            totalUsdValue
          });

          return { exchange, balances, success: true };
        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error';
          
          this.statusCache.set(exchange, {
            exchange,
            connected: false,
            lastUpdate: Date.now(),
            balanceCount: 0,
            totalUsdValue: 0,
            error: errorMessage
          });

          return { exchange, balances: [], success: false };
        }
      }
    );

    await Promise.all(promises);
    
    const state = this.getState();
    this.notifyListeners(state);
    
    // Send heartbeat to Temporal Ladder
    const activeCount = state.exchanges.filter(e => e.connected).length;
    temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, activeCount / state.exchanges.length);
    
    return state;
  }

  /**
   * Get consolidated balances across all exchanges
   */
  public getConsolidatedBalances(): ConsolidatedBalance[] {
    const assetMap = new Map<string, ConsolidatedBalance>();

    for (const [exchange, balances] of this.balanceCache.entries()) {
      for (const balance of balances) {
        if (!assetMap.has(balance.asset)) {
          assetMap.set(balance.asset, {
            asset: balance.asset,
            balances: {} as Record<ExchangeType, { free: number; locked: number; total: number }>,
            totalFree: 0,
            totalLocked: 0,
            grandTotal: 0,
            usdValue: 0
          });
        }

        const consolidated = assetMap.get(balance.asset)!;
        consolidated.balances[exchange] = {
          free: balance.free,
          locked: balance.locked,
          total: balance.total
        };
        consolidated.totalFree += balance.free;
        consolidated.totalLocked += balance.locked;
        consolidated.grandTotal += balance.total;
        consolidated.usdValue += balance.usdValue || 0;
      }
    }

    return Array.from(assetMap.values())
      .filter(b => b.grandTotal > 0)
      .sort((a, b) => b.usdValue - a.usdValue);
  }

  /**
   * Get total equity in USD
   */
  public getTotalEquityUsd(): number {
    let total = 0;
    for (const status of this.statusCache.values()) {
      total += status.totalUsdValue;
    }
    return total;
  }

  /**
   * Get current state
   */
  public getState(): MultiExchangeState {
    return {
      exchanges: Array.from(this.statusCache.values()),
      consolidatedBalances: this.getConsolidatedBalances(),
      totalEquityUsd: this.getTotalEquityUsd(),
      lastUpdate: Date.now()
    };
  }

  /**
   * Get best exchange for a symbol based on fees
   */
  public getBestExchangeForSymbol(symbol: string): ExchangeType {
    // For now, return exchange with lowest taker fee
    let bestExchange: ExchangeType = 'binance';
    let lowestFee = Infinity;

    for (const [exchange] of this.clients.entries()) {
      const fees = EXCHANGE_FEES[exchange];
      if (fees.taker < lowestFee) {
        lowestFee = fees.taker;
        bestExchange = exchange;
      }
    }

    return bestExchange;
  }

  /**
   * Get ticker from all exchanges
   */
  public async getTickersFromAllExchanges(symbol: string): Promise<Map<ExchangeType, ExchangeTicker | null>> {
    const results = new Map<ExchangeType, ExchangeTicker | null>();

    const promises = Array.from(this.clients.entries()).map(
      async ([exchange, client]) => {
        try {
          const ticker = await client.getTicker(symbol);
          results.set(exchange, ticker);
        } catch {
          results.set(exchange, null);
        }
      }
    );

    await Promise.all(promises);
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
    this.updateInterval = window.setInterval(() => {
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
    this.clients.clear();
    this.balanceCache.clear();
    this.statusCache.clear();
    this.isInitialized = false;
  }
}

// Singleton instance
export const multiExchangeClient = new MultiExchangeClient();
