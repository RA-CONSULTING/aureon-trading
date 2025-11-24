import { useState, useEffect, useCallback } from 'react';
import { useBinanceCredentials } from './useBinanceCredentials';

interface MarketPair {
  symbol: string;
  price: number;
  volume24h: number;
  priceChange24h: number;
  volatility: number;
  opportunityScore: number;
}

export function useMarketScanner() {
  const [pairs, setPairs] = useState<MarketPair[]>([]);
  const [isScanning, setIsScanning] = useState(false);
  const [lastScan, setLastScan] = useState<Date | null>(null);
  const { hasCredentials } = useBinanceCredentials();

  const scanMarket = useCallback(async () => {
    if (!hasCredentials) return;
    
    setIsScanning(true);
    try {
      // Fetch 24hr ticker for all USDT pairs
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      const tickers = await response.json();
      
      // Filter for USDT pairs with sufficient volume
      const usdtPairs = tickers
        .filter((t: any) => t.symbol.endsWith('USDT') && parseFloat(t.quoteVolume) > 100000)
        .map((t: any) => {
          const priceChange = parseFloat(t.priceChangePercent);
          const volume = parseFloat(t.quoteVolume);
          const volatility = Math.abs(priceChange);
          
          // Opportunity score: high volatility + high volume + positive momentum
          const volumeScore = Math.min(volume / 1000000, 10); // Cap at 10
          const volatilityScore = Math.min(volatility * 2, 10);
          const momentumScore = priceChange > 0 ? 5 : -2;
          const opportunityScore = volumeScore + volatilityScore + momentumScore;
          
          return {
            symbol: t.symbol,
            price: parseFloat(t.lastPrice),
            volume24h: volume,
            priceChange24h: priceChange,
            volatility,
            opportunityScore: Math.max(0, opportunityScore),
          };
        })
        .sort((a: MarketPair, b: MarketPair) => b.opportunityScore - a.opportunityScore)
        .slice(0, 50); // Top 50 opportunities
      
      setPairs(usdtPairs);
      setLastScan(new Date());
    } catch (error) {
      console.error('Market scan error:', error);
    } finally {
      setIsScanning(false);
    }
  }, [hasCredentials]);

  // Auto-scan every 30 seconds
  useEffect(() => {
    if (!hasCredentials) return;
    
    scanMarket();
    const interval = setInterval(scanMarket, 30000);
    return () => clearInterval(interval);
  }, [hasCredentials, scanMarket]);

  return {
    pairs,
    isScanning,
    lastScan,
    scanMarket,
  };
}
