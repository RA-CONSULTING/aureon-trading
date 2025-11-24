import { useState, useEffect, useCallback } from 'react';
import { useBinanceCredentials } from './useBinanceCredentials';

export interface MarketData {
  symbol: string;
  price: number;
  priceChange24h: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  timestamp: number;
}

export const useBinanceWebSocket = (symbols: string[] = ['BTCUSDT', 'ETHUSDT']) => {
  const [marketData, setMarketData] = useState<Record<string, MarketData>>({});
  const [connected, setConnected] = useState(false);
  const { hasCredentials } = useBinanceCredentials();

  useEffect(() => {
    if (!hasCredentials) return;

    const streams = symbols.map(s => `${s.toLowerCase()}@ticker`).join('/');
    const ws = new WebSocket(`wss://stream.binance.com:9443/stream?streams=${streams}`);

    ws.onopen = () => {
      console.log('🌈 Connected to Binance WebSocket');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.data) {
          const ticker = message.data;
          setMarketData(prev => ({
            ...prev,
            [ticker.s]: {
              symbol: ticker.s,
              price: parseFloat(ticker.c),
              priceChange24h: parseFloat(ticker.P),
              volume24h: parseFloat(ticker.v),
              high24h: parseFloat(ticker.h),
              low24h: parseFloat(ticker.l),
              timestamp: Date.now(),
            }
          }));
        }
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [symbols, hasCredentials]);

  return { marketData, connected };
};
