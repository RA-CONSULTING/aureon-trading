import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { validateMarketPacket, getDataHealthScore, getExchangeStatuses, type ExchangeValidationStatus } from '@/core/marketDataValidator';

export interface TickerData {
  symbol: string;
  exchange: string;
  price: number;
  bidPrice?: number;
  askPrice?: number;
  volume: number;
  volumeUsd: number;
  high24h?: number;
  low24h?: number;
  priceChange24h?: number;
  volatility?: number;
  momentum?: number;
  spread?: number;
  isValidated: boolean;
  fetchedAt: string;
  staleness: number; // seconds since fetched
}

export interface TickerStreamStats {
  totalTickers: number;
  validTickers: number;
  staleTickers: number;
  avgVolatility: number;
  avgSpread: number;
  exchangeStatus: Record<string, { connected: boolean; tickerCount: number; lastUpdate: Date | null }>;
}

export interface UseTickerStreamResult {
  tickers: TickerData[];
  stats: TickerStreamStats;
  isLoading: boolean;
  isConnected: boolean;
  lastUpdate: Date | null;
  healthScore: { score: number; status: 'healthy' | 'degraded' | 'critical' };
  exchangeStatuses: ExchangeValidationStatus[];
  refreshTickers: () => Promise<void>;
  getTicker: (symbol: string, exchange?: string) => TickerData | undefined;
  getTopByVolume: (limit?: number) => TickerData[];
  getTopByVolatility: (limit?: number) => TickerData[];
}

const REFRESH_INTERVAL = 3000; // 3 seconds
const STALE_THRESHOLD = 30; // 30 seconds

export function useTickerStream(
  symbols?: string[],
  exchanges: string[] = ['binance', 'kraken']
): UseTickerStreamResult {
  const [tickers, setTickers] = useState<TickerData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const tickerMapRef = useRef<Map<string, TickerData>>(new Map());
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch tickers from edge function
  const refreshTickers = useCallback(async () => {
    try {
      const { data, error } = await supabase.functions.invoke('fetch-all-tickers', {
        body: {
          symbols,
          exchanges,
          limit: symbols?.length || 200,
        },
      });

      if (error) {
        console.error('[useTickerStream] Fetch error:', error);
        setIsConnected(false);
        return;
      }

      if (!data?.tickers) {
        console.warn('[useTickerStream] No tickers in response');
        return;
      }

      const now = new Date();
      const validatedTickers: TickerData[] = [];

      for (const ticker of data.tickers) {
        // Validate each ticker
        const validation = validateMarketPacket({
          symbol: ticker.symbol,
          exchange: ticker.exchange,
          price: ticker.price,
          volume: ticker.volume,
          timestamp: ticker.fetchedAt || now.toISOString(),
          bidPrice: ticker.bidPrice,
          askPrice: ticker.askPrice,
        });

        const staleness = ticker.fetchedAt 
          ? Math.floor((now.getTime() - new Date(ticker.fetchedAt).getTime()) / 1000)
          : 0;

        const tickerData: TickerData = {
          symbol: ticker.symbol,
          exchange: ticker.exchange,
          price: ticker.price,
          bidPrice: ticker.bidPrice,
          askPrice: ticker.askPrice,
          volume: ticker.volume,
          volumeUsd: ticker.volumeUsd,
          high24h: ticker.high24h,
          low24h: ticker.low24h,
          priceChange24h: ticker.priceChange24h,
          volatility: ticker.volatility,
          momentum: ticker.momentum,
          spread: ticker.spread,
          isValidated: validation.isValid,
          fetchedAt: ticker.fetchedAt || now.toISOString(),
          staleness,
        };

        validatedTickers.push(tickerData);
        tickerMapRef.current.set(`${ticker.exchange}:${ticker.symbol}`, tickerData);
      }

      setTickers(validatedTickers);
      setLastUpdate(now);
      setIsConnected(true);
      setIsLoading(false);

      // Persist snapshots to database (fire and forget)
      if (validatedTickers.length > 0) {
        supabase.functions.invoke('ingest-ticker-snapshot', {
          body: {
            temporal_id: `stream-${now.getTime()}`,
            tickers: validatedTickers.slice(0, 50).map(t => ({
              symbol: t.symbol,
              exchange: t.exchange,
              price: t.price,
              bidPrice: t.bidPrice,
              askPrice: t.askPrice,
              volume: t.volume,
              volumeUsd: t.volumeUsd,
              high24h: t.high24h,
              low24h: t.low24h,
              priceChange24h: t.priceChange24h,
              volatility: t.volatility,
              momentum: t.momentum,
              spread: t.spread,
              isValidated: t.isValidated,
              dataSource: 'live',
            })),
          },
        }).catch(err => console.warn('[useTickerStream] Snapshot persist error:', err));
      }
    } catch (error) {
      console.error('[useTickerStream] Error:', error);
      setIsConnected(false);
    }
  }, [symbols, exchanges]);

  // Start polling on mount
  useEffect(() => {
    refreshTickers();
    
    intervalRef.current = setInterval(refreshTickers, REFRESH_INTERVAL);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [refreshTickers]);

  // Calculate stats
  const stats: TickerStreamStats = useMemo(() => {
    const validTickers = tickers.filter(t => t.isValidated);
    const staleTickers = tickers.filter(t => t.staleness > STALE_THRESHOLD);
    
    const avgVolatility = validTickers.length > 0
      ? validTickers.reduce((sum, t) => sum + (t.volatility || 0), 0) / validTickers.length
      : 0;
    
    const avgSpread = validTickers.length > 0
      ? validTickers.reduce((sum, t) => sum + (t.spread || 0), 0) / validTickers.length
      : 0;

    // Group by exchange
    const exchangeStatus: Record<string, { connected: boolean; tickerCount: number; lastUpdate: Date | null }> = {};
    for (const exchange of exchanges) {
      const exchangeTickers = tickers.filter(t => t.exchange === exchange);
      const nonStaleTickers = exchangeTickers.filter(t => t.staleness <= STALE_THRESHOLD);
      exchangeStatus[exchange] = {
        connected: nonStaleTickers.length > 0,
        tickerCount: exchangeTickers.length,
        lastUpdate: exchangeTickers.length > 0 
          ? new Date(Math.max(...exchangeTickers.map(t => new Date(t.fetchedAt).getTime())))
          : null,
      };
    }

    return {
      totalTickers: tickers.length,
      validTickers: validTickers.length,
      staleTickers: staleTickers.length,
      avgVolatility,
      avgSpread,
      exchangeStatus,
    };
  }, [tickers, exchanges]);

  // Get health score
  const healthScore = useMemo(() => getDataHealthScore(), [tickers]);
  
  // Get exchange statuses
  const exchangeStatuses = useMemo(() => getExchangeStatuses(), [tickers]);

  // Helper functions
  const getTicker = useCallback((symbol: string, exchange?: string): TickerData | undefined => {
    if (exchange) {
      return tickerMapRef.current.get(`${exchange}:${symbol}`);
    }
    // Return first matching symbol from any exchange
    for (const ticker of tickers) {
      if (ticker.symbol === symbol) return ticker;
    }
    return undefined;
  }, [tickers]);

  const getTopByVolume = useCallback((limit: number = 20): TickerData[] => {
    return [...tickers]
      .filter(t => t.isValidated)
      .sort((a, b) => (b.volumeUsd || 0) - (a.volumeUsd || 0))
      .slice(0, limit);
  }, [tickers]);

  const getTopByVolatility = useCallback((limit: number = 20): TickerData[] => {
    return [...tickers]
      .filter(t => t.isValidated)
      .sort((a, b) => (b.volatility || 0) - (a.volatility || 0))
      .slice(0, limit);
  }, [tickers]);

  return {
    tickers,
    stats,
    isLoading,
    isConnected,
    lastUpdate,
    healthScore,
    exchangeStatuses,
    refreshTickers,
    getTicker,
    getTopByVolume,
    getTopByVolatility,
  };
}
