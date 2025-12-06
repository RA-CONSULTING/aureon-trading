/**
 * All Tickers Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Fetches and manages real-time ticker data from all exchanges
 * with built-in validation and caching
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { validateMarketPacket, type ValidationResult, type MarketPacket } from '@/core/marketDataValidator';

export interface TickerData {
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
  validation?: ValidationResult;
}

export interface UseAllTickersResult {
  tickers: TickerData[];
  tickerMap: Map<string, TickerData>;
  isLoading: boolean;
  isConnected: boolean;
  lastUpdate: number | null;
  stats: {
    totalTickers: number;
    validTickers: number;
    staleCount: number;
    avgVolatility: number;
    topSymbol: string | null;
  };
  error: string | null;
  refresh: () => Promise<void>;
  getTicker: (symbol: string, exchange?: string) => TickerData | undefined;
}

const REFRESH_INTERVAL_MS = 5000; // 5 seconds
const CACHE_TTL_MS = 10000; // 10 seconds

export function useAllTickers(
  symbols?: string[],
  exchanges: string[] = ['binance'],
  limit: number = 100
): UseAllTickersResult {
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [tickerMap, setTickerMap] = useState<Map<string, TickerData>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const cacheRef = useRef<{ data: TickerData[]; timestamp: number } | null>(null);

  const refresh = useCallback(async () => {
    // Check cache first
    if (cacheRef.current && Date.now() - cacheRef.current.timestamp < CACHE_TTL_MS) {
      return;
    }

    try {
      setIsLoading(true);
      setError(null);

      const { data, error: apiError } = await supabase.functions.invoke('fetch-all-tickers', {
        body: { symbols, exchanges, limit }
      });

      if (apiError) {
        throw new Error(apiError.message || 'Failed to fetch tickers');
      }

      if (!data?.success) {
        throw new Error(data?.error || 'Unknown error');
      }

      const fetchedTickers: TickerData[] = (data.tickers || []).map((t: any) => {
        // Create market packet for validation
        const packet: MarketPacket = {
          symbol: t.symbol,
          exchange: t.exchange,
          price: t.price,
          volume: t.volumeUsd,
          volatility: t.volatility,
          momentum: t.momentum,
          timestamp: t.timestamp,
          bidPrice: t.bidPrice,
          askPrice: t.askPrice,
          high24h: t.high24h,
          low24h: t.low24h,
          priceChange24h: t.priceChange24h,
          spread: t.spread,
        };

        // Validate the packet
        const validation = validateMarketPacket(packet);

        return {
          ...t,
          isValidated: validation.isValid,
          validation,
        };
      });

      // Update state
      setTickers(fetchedTickers);
      
      // Update map for O(1) lookups
      const newMap = new Map<string, TickerData>();
      for (const ticker of fetchedTickers) {
        const key = `${ticker.exchange}:${ticker.symbol}`;
        newMap.set(key, ticker);
        // Also store by symbol only (uses first exchange found)
        if (!newMap.has(ticker.symbol)) {
          newMap.set(ticker.symbol, ticker);
        }
      }
      setTickerMap(newMap);
      
      // Update cache
      cacheRef.current = { data: fetchedTickers, timestamp: Date.now() };
      
      setLastUpdate(Date.now());
      setIsConnected(true);

    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      console.error('[useAllTickers] Error:', message);
      setError(message);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  }, [symbols, exchanges, limit]);

  // Initial load and periodic refresh
  useEffect(() => {
    refresh();
    
    const interval = setInterval(refresh, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refresh]);

  // Calculate stats
  const stats = {
    totalTickers: tickers.length,
    validTickers: tickers.filter(t => t.isValidated).length,
    staleCount: tickers.filter(t => t.validation?.freshness === 'stale').length,
    avgVolatility: tickers.length > 0
      ? tickers.reduce((sum, t) => sum + (t.volatility || 0), 0) / tickers.length
      : 0,
    topSymbol: tickers.length > 0 ? tickers[0].symbol : null,
  };

  // Helper to get specific ticker
  const getTicker = useCallback((symbol: string, exchange?: string): TickerData | undefined => {
    if (exchange) {
      return tickerMap.get(`${exchange}:${symbol}`);
    }
    return tickerMap.get(symbol);
  }, [tickerMap]);

  return {
    tickers,
    tickerMap,
    isLoading,
    isConnected,
    lastUpdate,
    stats,
    error,
    refresh,
    getTicker,
  };
}
