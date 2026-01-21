import { useState, useEffect, useRef } from 'react';
import { globalSystemsManager } from '@/core/globalSystemsManager';

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
  const messageCountRef = useRef(0);

  useEffect(() => {
    // Public WebSocket - no credentials required for market data
    const streams = symbols.map(s => `${s.toLowerCase()}@ticker`).join('/');
    const ws = new WebSocket(`wss://stream.binance.com:9443/stream?streams=${streams}`);

    ws.onopen = () => {
      console.log('🌈 Connected to Binance WebSocket');
      setConnected(true);
      // Update global state
      globalSystemsManager['updateState']?.({ wsConnected: true });
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.data) {
          const ticker = message.data;
          messageCountRef.current += 1;
          
          // Update global state with WS message count periodically
          if (messageCountRef.current % 10 === 0) {
            globalSystemsManager['updateState']?.({ 
              wsMessageCount: messageCountRef.current 
            });
          }
          
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
      globalSystemsManager['updateState']?.({ wsConnected: false });
    };

    ws.onclose = () => {
      console.log('WebSocket closed');
      setConnected(false);
      globalSystemsManager['updateState']?.({ wsConnected: false });
    };

    return () => {
      ws.close();
    };
  }, [symbols.join(',')]);

  return { marketData, connected, messageCount: messageCountRef.current };
};
