/**
 * Active Symbols Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Manages active trading symbols from binance-pairs.json
 * Provides top symbols by opportunity score for smart order routing
 */

import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';
import binancePairsData from '@/data/binance-pairs.json';

export interface ActiveSymbol {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  price: number;
  volume: number;
  volatility: number;
  change: number;
  opportunityScore: number;
  lastUpdate: number;
  isLive: boolean;
}

export interface UseActiveSymbolsResult {
  symbols: ActiveSymbol[];
  topSymbols: ActiveSymbol[];
  isLoading: boolean;
  lastUpdate: number | null;
  totalAvailable: number;
  refreshSymbols: () => Promise<void>;
  getSymbol: (symbol: string) => ActiveSymbol | undefined;
  getTopByVolume: (limit?: number) => ActiveSymbol[];
  getTopByVolatility: (limit?: number) => ActiveSymbol[];
}

const TOP_SYMBOLS_COUNT = 50;
const REFRESH_INTERVAL_MS = 30000; // 30 seconds

export function useActiveSymbols(): UseActiveSymbolsResult {
  const [symbols, setSymbols] = useState<ActiveSymbol[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);

  // Process binance-pairs.json data
  const processedSymbols = useMemo(() => {
    const pairs = (binancePairsData as any).pairs || [];
    
    return pairs
      .filter((p: any) => p.volume > 100000 && p.price > 0)
      .map((p: any) => {
        const volatility = p.volatility || 0;
        const volumeScore = Math.log10(Math.max(p.volume, 1)) / 10;
        const momentum = (p.change || 0) / 100;
        
        // Calculate opportunity score
        const opportunityScore = 
          (volatility * 0.4) + 
          (volumeScore * 0.3) + 
          (Math.abs(momentum) * 0.3);
        
        return {
          symbol: p.symbol,
          baseAsset: p.base,
          quoteAsset: p.quote,
          price: p.price,
          volume: p.volume,
          volatility,
          change: p.change || 0,
          opportunityScore,
          lastUpdate: Date.now(),
          isLive: false, // Will be updated with live data
        };
      })
      .sort((a: ActiveSymbol, b: ActiveSymbol) => b.opportunityScore - a.opportunityScore);
  }, []);

  // Refresh with live data from edge function
  const refreshSymbols = useCallback(async () => {
    setIsLoading(true);
    
    try {
      // Get top symbol names to fetch
      const topSymbolNames = processedSymbols
        .slice(0, TOP_SYMBOLS_COUNT)
        .map((s: ActiveSymbol) => s.symbol);
      
      // Fetch live data
      const { data, error } = await supabase.functions.invoke('fetch-all-tickers', {
        body: { 
          symbols: topSymbolNames,
          exchanges: ['binance'],
          limit: TOP_SYMBOLS_COUNT 
        }
      });

      if (error) {
        console.warn('[useActiveSymbols] API error, using cached data:', error);
        setSymbols(processedSymbols);
        setLastUpdate(Date.now());
        return;
      }

      if (data?.success && data.tickers?.length > 0) {
        // Merge live data with processed symbols
        const liveDataMap = new Map<string, any>(
          data.tickers.map((t: any) => [t.symbol, t])
        );
        
        const updatedSymbols = processedSymbols.map((s: ActiveSymbol) => {
          const live = liveDataMap.get(s.symbol) as any;
          if (live) {
            return {
              ...s,
              price: live.price ?? s.price,
              volume: live.volumeUsd ?? s.volume,
              volatility: live.volatility ?? s.volatility,
              change: live.priceChange24h ?? s.change,
              lastUpdate: live.timestamp ?? Date.now(),
              isLive: true,
            };
          }
          return s;
        });
        
        // Re-sort by opportunity score with live data
        updatedSymbols.sort((a, b) => b.opportunityScore - a.opportunityScore);
        
        setSymbols(updatedSymbols);
        setLastUpdate(Date.now());
        
        console.log(`[useActiveSymbols] Updated ${data.tickers.length} symbols with live data`);
      } else {
        setSymbols(processedSymbols);
        setLastUpdate(Date.now());
      }
    } catch (error) {
      console.error('[useActiveSymbols] Refresh error:', error);
      setSymbols(processedSymbols);
      setLastUpdate(Date.now());
    } finally {
      setIsLoading(false);
    }
  }, [processedSymbols]);

  // Initial load and periodic refresh
  useEffect(() => {
    refreshSymbols();
    
    const interval = setInterval(refreshSymbols, REFRESH_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [refreshSymbols]);

  // Get top symbols (already sorted by opportunity score)
  const topSymbols = useMemo(() => {
    return symbols.slice(0, TOP_SYMBOLS_COUNT);
  }, [symbols]);

  // Helper functions
  const getSymbol = useCallback((symbol: string) => {
    return symbols.find(s => s.symbol === symbol);
  }, [symbols]);

  const getTopByVolume = useCallback((limit = 10) => {
    return [...symbols]
      .sort((a, b) => b.volume - a.volume)
      .slice(0, limit);
  }, [symbols]);

  const getTopByVolatility = useCallback((limit = 10) => {
    return [...symbols]
      .sort((a, b) => b.volatility - a.volatility)
      .slice(0, limit);
  }, [symbols]);

  return {
    symbols,
    topSymbols,
    isLoading,
    lastUpdate,
    totalAvailable: (binancePairsData as any).totalPairs || 0,
    refreshSymbols,
    getSymbol,
    getTopByVolume,
    getTopByVolatility,
  };
}
