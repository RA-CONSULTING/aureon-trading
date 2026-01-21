import { useEffect, useState, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface BinanceMarketData {
  symbol: string;
  timestamp: number;
  price: number;
  highPrice: number;
  lowPrice: number;
  openPrice: number;
  previousClosePrice: number;
  priceChange: number;
  priceChangePercent: number;
  avgPrice: number;
  weightedAvgPrice: number;
  volume: number;
  quoteVolume: number;
  volumeNormalized: number;
  bidPrice: number;
  askPrice: number;
  spread: number;
  spreadPercent: number;
  volatility: number;
  momentum: number;
  tradeCount: number;
  recentTrades: Array<{
    price: number;
    quantity: number;
    time: number;
    isBuyerMaker: boolean;
  }>;
  topBids: Array<{ price: number; quantity: number }>;
  topAsks: Array<{ price: number; quantity: number }>;
  fetchedAt: string;
}

export const useBinanceMarketData = (symbol: string = 'BTCUSDT', refreshInterval: number = 5000) => {
  const [marketData, setMarketData] = useState<BinanceMarketData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchMarketData = async () => {
    setIsLoading(true);
    setError(null);

    try {
      console.log('[useBinanceMarketData] Fetching data for:', symbol);
      
      const { data, error: functionError } = await supabase.functions.invoke('fetch-binance-market-data', {
        body: { symbol },
      });

      if (functionError) {
        throw functionError;
      }

      if (data.error) {
        throw new Error(data.error);
      }

      setMarketData(data);
      setIsConnected(true);
      setError(null);
      
      console.log('[useBinanceMarketData] Data fetched successfully:', {
        symbol: data.symbol,
        price: data.price,
        volume: data.volume,
      });
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch market data';
      console.error('[useBinanceMarketData] Error:', errorMessage);
      setError(errorMessage);
      setIsConnected(false);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchMarketData();

    // Set up polling interval
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchMarketData, refreshInterval);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [symbol, refreshInterval]);

  return {
    marketData,
    isLoading,
    isConnected,
    error,
    refetch: fetchMarketData,
  };
};
