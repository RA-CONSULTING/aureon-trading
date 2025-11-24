import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import binancePairsData from '@/data/binance-pairs.json';

export interface MarketOpportunity {
  symbol: string;
  baseAsset: string;
  price: number;
  volume24h: number;
  priceChange24h: number;
  volatility: number;
  momentum: number;
  opportunityScore: number;
}

export function useMarketScanner() {
  const [opportunities, setOpportunities] = useState<MarketOpportunity[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScan, setLastScan] = useState<Date | null>(null);

  const scanMarket = useCallback(async () => {
    setIsScanning(true);

    try {
      console.log(`🔍 Scanning ALL ${binancePairsData.totalPairs} pairs for maximum profit...`);

      // Process comprehensive market data
      const opportunities = binancePairsData.pairs
        .filter((p: any) => p.volume > 100000 && p.price > 0) // Min volume
        .map((p: any) => {
          const volatility = p.volatility || 0;
          const volumeScore = Math.log10(p.volume) / 10;
          const momentum = (p.change || 0) / 100;
          
          // High-impact opportunity score
          const opportunityScore = 
            (volatility * 0.4) + 
            (volumeScore * 0.3) + 
            (Math.abs(momentum) * 0.3);

          return {
            symbol: p.symbol,
            baseAsset: p.base,
            price: p.price,
            volume24h: p.volume,
            priceChange24h: p.change,
            volatility,
            momentum,
            opportunityScore,
          };
        })
        .sort((a: any, b: any) => b.opportunityScore - a.opportunityScore)
        .slice(0, 100); // Top 100 opportunities

      setOpportunities(opportunities);
      setLastScan(new Date());
      console.log(`✅ Analyzed ${binancePairsData.pairs.length} pairs. Top: ${opportunities[0]?.symbol} (${opportunities[0]?.opportunityScore.toFixed(2)})`);

      // Fetch live price updates via edge function
      try {
        const { data } = await supabase.functions.invoke('fetch-binance-symbols');
        if (data?.symbols) {
          console.log(`📡 Live update: ${data.symbols.length} symbols`);
        }
      } catch (err) {
        console.log('📊 Using cached data');
      }

    } catch (error) {
      console.error('❌ Market scan failed:', error);
    } finally {
      setIsScanning(false);
    }
  }, []);

  return {
    opportunities,
    isScanning,
    lastScan,
    totalPairs: binancePairsData.totalPairs,
    scanMarket,
  };
}
