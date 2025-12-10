/**
 * Ticker Cache Manager
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Fetches and caches ALL 800+ pairs from exchanges
 * Provides real-time ticker data for opportunity scanning
 */

import { supabase } from '@/integrations/supabase/client';
import { unifiedBus } from './unifiedBus';
import { temporalLadder, SYSTEMS } from './temporalLadder';

export interface CachedTicker {
  symbol: string;
  exchange: string;
  price: number;
  bidPrice: number;
  askPrice: number;
  volume: number;
  volumeUsd: number;
  high24h: number;
  low24h: number;
  priceChange24h: number;
  volatility: number;
  momentum: number;
  spread: number;
  timestamp: number;
  isValidated: boolean;
  dataSource: 'live' | 'cached' | 'stale';
}

export interface TickerCacheStats {
  totalTickers: number;
  liveTickers: number;
  staleTickers: number;
  lastFullRefresh: number;
  avgVolatility: number;
  topGainers: string[];
  topLosers: string[];
  highVolume: string[];
}

const REFRESH_INTERVAL_MS = 10000; // 10 seconds
const STALE_THRESHOLD_MS = 60000; // 1 minute
const MIN_VOLUME_USD = 100000; // Filter out low volume pairs

class TickerCacheManager {
  private cache: Map<string, CachedTicker> = new Map();
  private lastRefresh: number = 0;
  private isRefreshing: boolean = false;
  private refreshInterval: ReturnType<typeof setInterval> | null = null;
  private listeners: Array<(tickers: CachedTicker[]) => void> = [];
  private isInitialized: boolean = false;

  constructor() {
    console.log('📊 Ticker Cache Manager initializing...');
  }

  /**
   * Initialize and start automatic refresh
   */
  public async initialize(): Promise<void> {
    if (this.isInitialized) return;

    temporalLadder.registerSystem(SYSTEMS.DATA_INGESTION);

    // Initial fetch
    await this.refreshAll();

    // Start periodic refresh
    this.refreshInterval = setInterval(() => {
      this.refreshAll().catch(console.error);
    }, REFRESH_INTERVAL_MS);

    this.isInitialized = true;
    console.log(`📊 Ticker Cache Manager initialized with ${this.cache.size} pairs`);
  }

  /**
   * Refresh all tickers from exchanges
   */
  public async refreshAll(): Promise<void> {
    if (this.isRefreshing) return;
    this.isRefreshing = true;

    const startTime = Date.now();
    try {
      console.log('[TickerCache] Refreshing all tickers...');

      const { data, error } = await supabase.functions.invoke('fetch-all-tickers', {
        body: { 
          exchanges: ['binance', 'kraken'],
          limit: 500 // Top 500 by volume
        }
      });

      if (error) {
        console.error('[TickerCache] API error:', error);
        return;
      }

      if (data?.success && Array.isArray(data.tickers)) {
        const now = Date.now();
        
        // Update cache
        for (const ticker of data.tickers) {
          const key = `${ticker.exchange}:${ticker.symbol}`;
          this.cache.set(key, {
            ...ticker,
            dataSource: 'live',
            timestamp: now,
          });
        }

        this.lastRefresh = now;

        // Mark old entries as stale
        for (const [key, ticker] of this.cache.entries()) {
          if (now - ticker.timestamp > STALE_THRESHOLD_MS) {
            this.cache.set(key, { ...ticker, dataSource: 'stale' });
          }
        }

        const elapsed = Date.now() - startTime;
        console.log(`[TickerCache] ✅ Refreshed ${data.tickers.length} tickers in ${elapsed}ms`);

        // Publish to UnifiedBus
        this.publishToUnifiedBus();

        // Notify listeners
        this.notifyListeners();

        // Heartbeat to Temporal Ladder
        temporalLadder.heartbeat(SYSTEMS.DATA_INGESTION, 0.95);
      }
    } catch (error) {
      console.error('[TickerCache] Refresh error:', error);
      temporalLadder.heartbeat(SYSTEMS.DATA_INGESTION, 0.1);
    } finally {
      this.isRefreshing = false;
    }
  }

  /**
   * Get all tickers from cache
   */
  public getAllTickers(): CachedTicker[] {
    return Array.from(this.cache.values());
  }

  /**
   * Get tickers filtered by volume
   */
  public getHighVolumeTickers(minVolumeUsd: number = MIN_VOLUME_USD): CachedTicker[] {
    return this.getAllTickers()
      .filter(t => t.volumeUsd >= minVolumeUsd)
      .sort((a, b) => b.volumeUsd - a.volumeUsd);
  }

  /**
   * Get ticker for specific symbol
   */
  public getTicker(symbol: string, exchange: string = 'binance'): CachedTicker | undefined {
    return this.cache.get(`${exchange}:${symbol}`);
  }

  /**
   * Get tickers sorted by volatility (best opportunities)
   */
  public getVolatileTickers(minVolatility: number = 0.02): CachedTicker[] {
    return this.getAllTickers()
      .filter(t => t.volatility >= minVolatility && t.volumeUsd >= MIN_VOLUME_USD)
      .sort((a, b) => b.volatility - a.volatility);
  }

  /**
   * Get top gainers
   */
  public getTopGainers(limit: number = 20): CachedTicker[] {
    return this.getAllTickers()
      .filter(t => t.volumeUsd >= MIN_VOLUME_USD)
      .sort((a, b) => b.priceChange24h - a.priceChange24h)
      .slice(0, limit);
  }

  /**
   * Get top losers
   */
  public getTopLosers(limit: number = 20): CachedTicker[] {
    return this.getAllTickers()
      .filter(t => t.volumeUsd >= MIN_VOLUME_USD)
      .sort((a, b) => a.priceChange24h - b.priceChange24h)
      .slice(0, limit);
  }

  /**
   * Get cache statistics
   */
  public getStats(): TickerCacheStats {
    const tickers = this.getAllTickers();
    const now = Date.now();
    
    const liveTickers = tickers.filter(t => t.dataSource === 'live').length;
    const staleTickers = tickers.filter(t => now - t.timestamp > STALE_THRESHOLD_MS).length;
    
    const avgVolatility = tickers.length > 0 
      ? tickers.reduce((sum, t) => sum + t.volatility, 0) / tickers.length 
      : 0;

    return {
      totalTickers: tickers.length,
      liveTickers,
      staleTickers,
      lastFullRefresh: this.lastRefresh,
      avgVolatility,
      topGainers: this.getTopGainers(5).map(t => t.symbol),
      topLosers: this.getTopLosers(5).map(t => t.symbol),
      highVolume: this.getHighVolumeTickers(1000000).slice(0, 10).map(t => t.symbol),
    };
  }

  /**
   * Check if cache is fresh
   */
  public isFresh(): boolean {
    return Date.now() - this.lastRefresh < STALE_THRESHOLD_MS;
  }

  /**
   * Subscribe to ticker updates
   */
  public subscribe(listener: (tickers: CachedTicker[]) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(): void {
    const tickers = this.getAllTickers();
    for (const listener of this.listeners) {
      try {
        listener(tickers);
      } catch (error) {
        console.error('[TickerCache] Listener error:', error);
      }
    }
  }

  private publishToUnifiedBus(): void {
    const stats = this.getStats();
    
    unifiedBus.publish({
      systemName: 'TickerCache',
      timestamp: Date.now(),
      ready: stats.totalTickers > 0,
      coherence: stats.liveTickers / Math.max(stats.totalTickers, 1),
      confidence: this.isFresh() ? 0.95 : 0.5,
      signal: 'NEUTRAL',
      data: {
        totalTickers: stats.totalTickers,
        liveTickers: stats.liveTickers,
        staleTickers: stats.staleTickers,
        avgVolatility: stats.avgVolatility,
        topGainers: stats.topGainers,
        topLosers: stats.topLosers,
        highVolume: stats.highVolume,
        lastRefresh: this.lastRefresh,
      },
    });
  }

  /**
   * Cleanup
   */
  public destroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
    this.cache.clear();
    this.listeners = [];
    this.isInitialized = false;
  }
}

export const tickerCacheManager = new TickerCacheManager();
