import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';
import binancePairs from '@/data/binance-pairs.json';

export interface AssetPrice {
  symbol: string;
  base: string;
  quote: string;
  price: number;
  volume: number;
  change: number;
  volatility: number;
  exchange: 'binance' | 'kraken' | 'alpaca' | 'capital';
  dataSource: 'LIVE' | 'CACHED' | 'STALE' | 'NO_DATA';
  lastUpdate: number;
  priceVariance?: number; // Cross-exchange variance
}

export interface AssetPriceListStats {
  totalAssets: number;
  liveAssets: number;
  cachedAssets: number;
  staleAssets: number;
  noDataAssets: number;
  avgVolatility: number;
  topGainer: AssetPrice | null;
  topLoser: AssetPrice | null;
  topVolume: AssetPrice | null;
  dataFreshness: number; // 0-100%
}

export interface UseAssetPriceListResult {
  assets: AssetPrice[];
  stats: AssetPriceListStats;
  isLoading: boolean;
  lastRefresh: Date | null;
  refresh: () => Promise<void>;
  getAsset: (symbol: string) => AssetPrice | undefined;
  searchAssets: (query: string) => AssetPrice[];
  sortAssets: (by: 'symbol' | 'price' | 'change' | 'volume' | 'volatility') => AssetPrice[];
}

const STALE_THRESHOLD_MS = 30000; // 30 seconds
const CACHE_THRESHOLD_MS = 10000; // 10 seconds

export const useAssetPriceList = (): UseAssetPriceListResult => {
  const [assets, setAssets] = useState<AssetPrice[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);

  // Initialize from static binance-pairs.json
  const initialAssets = useMemo<AssetPrice[]>(() => {
    return binancePairs.pairs.map((pair: any) => ({
      symbol: pair.symbol,
      base: pair.base,
      quote: pair.quote,
      price: pair.price || 0,
      volume: pair.volume || 0,
      change: pair.change || 0,
      volatility: pair.volatility || 0,
      exchange: 'binance' as const,
      dataSource: 'CACHED' as const,
      lastUpdate: new Date(binancePairs.timestamp).getTime(),
    }));
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      // Fetch live tickers from edge function
      const { data, error } = await supabase.functions.invoke('fetch-all-tickers', {
        body: { 
          exchanges: ['binance'],
          limit: 200 // Top 200 by volume
        }
      });

      if (error) {
        console.error('[useAssetPriceList] Error fetching tickers:', error);
        // Fall back to initial cached data
        setAssets(initialAssets);
        return;
      }

      const now = Date.now();
      const liveTickerMap = new Map<string, any>();
      
      if (data?.tickers) {
        data.tickers.forEach((ticker: any) => {
          liveTickerMap.set(ticker.symbol, ticker);
        });
      }

      // Merge live data with static pairs
      const mergedAssets: AssetPrice[] = initialAssets.map(asset => {
        const liveTicker = liveTickerMap.get(asset.symbol);
        
        if (liveTicker) {
          const tickerTime = liveTicker.timestamp || now;
          const age = now - tickerTime;
          
          let dataSource: AssetPrice['dataSource'] = 'LIVE';
          if (age > STALE_THRESHOLD_MS) {
            dataSource = 'STALE';
          } else if (age > CACHE_THRESHOLD_MS) {
            dataSource = 'CACHED';
          }

          return {
            ...asset,
            price: liveTicker.price || asset.price,
            volume: liveTicker.volume || asset.volume,
            change: liveTicker.priceChangePercent || asset.change,
            volatility: liveTicker.volatility || asset.volatility,
            dataSource,
            lastUpdate: tickerTime,
          };
        }
        
        return {
          ...asset,
          dataSource: 'NO_DATA' as const,
        };
      });

      // Sort by volume (highest first)
      mergedAssets.sort((a, b) => b.volume - a.volume);
      
      setAssets(mergedAssets);
      setLastRefresh(new Date());
    } catch (error) {
      console.error('[useAssetPriceList] Exception:', error);
      setAssets(initialAssets);
    } finally {
      setIsLoading(false);
    }
  }, [initialAssets]);

  // Initial load and periodic refresh
  useEffect(() => {
    // Set initial cached data immediately
    setAssets(initialAssets);
    
    // Then fetch live data
    refresh();
    
    // Refresh every 30 seconds
    const interval = setInterval(refresh, 30000);
    return () => clearInterval(interval);
  }, [initialAssets, refresh]);

  // Calculate stats
  const stats = useMemo<AssetPriceListStats>(() => {
    const liveAssets = assets.filter(a => a.dataSource === 'LIVE').length;
    const cachedAssets = assets.filter(a => a.dataSource === 'CACHED').length;
    const staleAssets = assets.filter(a => a.dataSource === 'STALE').length;
    const noDataAssets = assets.filter(a => a.dataSource === 'NO_DATA').length;
    
    const avgVolatility = assets.length > 0
      ? assets.reduce((sum, a) => sum + a.volatility, 0) / assets.length
      : 0;

    const sortedByChange = [...assets].sort((a, b) => b.change - a.change);
    const sortedByVolume = [...assets].sort((a, b) => b.volume - a.volume);

    const dataFreshness = assets.length > 0
      ? ((liveAssets + cachedAssets) / assets.length) * 100
      : 0;

    return {
      totalAssets: assets.length,
      liveAssets,
      cachedAssets,
      staleAssets,
      noDataAssets,
      avgVolatility,
      topGainer: sortedByChange[0] || null,
      topLoser: sortedByChange[sortedByChange.length - 1] || null,
      topVolume: sortedByVolume[0] || null,
      dataFreshness,
    };
  }, [assets]);

  const getAsset = useCallback((symbol: string): AssetPrice | undefined => {
    return assets.find(a => a.symbol.toLowerCase() === symbol.toLowerCase());
  }, [assets]);

  const searchAssets = useCallback((query: string): AssetPrice[] => {
    const q = query.toLowerCase();
    return assets.filter(a => 
      a.symbol.toLowerCase().includes(q) ||
      a.base.toLowerCase().includes(q) ||
      a.quote.toLowerCase().includes(q)
    );
  }, [assets]);

  const sortAssets = useCallback((by: 'symbol' | 'price' | 'change' | 'volume' | 'volatility'): AssetPrice[] => {
    return [...assets].sort((a, b) => {
      switch (by) {
        case 'symbol': return a.symbol.localeCompare(b.symbol);
        case 'price': return b.price - a.price;
        case 'change': return b.change - a.change;
        case 'volume': return b.volume - a.volume;
        case 'volatility': return b.volatility - a.volatility;
        default: return 0;
      }
    });
  }, [assets]);

  return {
    assets,
    stats,
    isLoading,
    lastRefresh,
    refresh,
    getAsset,
    searchAssets,
    sortAssets,
  };
};
