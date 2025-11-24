import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';

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
      // Use existing fetch-binance-symbols edge function
      const { data, error } = await supabase.functions.invoke('fetch-binance-symbols');
      
      if (error) throw error;

      const symbols = data.symbols || [];

      // Calculate opportunity scores
      const opportunities = symbols
        .filter((s: any) => s.volume24h > 1000000 && s.price > 0) // Min $1M volume
        .map((symbol: any) => {
          const volatility = Math.abs(symbol.priceChange24h || 0);
          const volumeScore = Math.log10(symbol.volume24h) / 10;
          const momentum = (symbol.priceChange24h || 0) / 100;
          
          const opportunityScore = 
            (volatility * 0.3) + 
            (volumeScore * 0.4) + 
            (Math.abs(momentum) * 0.3);

          return {
            symbol: symbol.symbol,
            baseAsset: symbol.baseAsset,
            price: symbol.price,
            volume24h: symbol.volume24h,
            priceChange24h: symbol.priceChange24h,
            volatility,
            momentum,
            opportunityScore,
          };
        })
        .sort((a: any, b: any) => b.opportunityScore - a.opportunityScore)
        .slice(0, 50); // Top 50 opportunities

      setOpportunities(opportunities);
      setLastScan(new Date());
      console.log(`✅ Market scan complete: ${opportunities.length} opportunities from ${symbols.length} symbols`);

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
    scanMarket,
  };
}
