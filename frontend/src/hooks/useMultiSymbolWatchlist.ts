import { useState, useEffect, useRef } from 'react';

export type WatchlistSymbol = {
  symbol: string;
  price: number;
  change24h: number;
  changePercent: number;
  volume: number;
  high24h: number;
  low24h: number;
  lastUpdate: number;
};

export const useMultiSymbolWatchlist = (symbols: string[]) => {
  const [symbolData, setSymbolData] = useState<Map<string, WatchlistSymbol>>(new Map());
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (symbols.length === 0) return;

    // Create combined stream URL for all symbols
    const streams = symbols.map(s => `${s.toLowerCase()}@ticker`).join('/');
    const wsUrl = `wss://stream.binance.com:9443/stream?streams=${streams}`;

    console.log('Connecting to multi-symbol watchlist:', wsUrl);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('✅ Watchlist WebSocket connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (!message.data) return;

        const ticker = message.data;
        
        // Extract 24hr ticker data
        const symbolInfo: WatchlistSymbol = {
          symbol: ticker.s, // Symbol
          price: parseFloat(ticker.c), // Current price
          change24h: parseFloat(ticker.p), // Price change
          changePercent: parseFloat(ticker.P), // Price change percent
          volume: parseFloat(ticker.v), // Volume
          high24h: parseFloat(ticker.h), // High price
          low24h: parseFloat(ticker.l), // Low price
          lastUpdate: Date.now(),
        };

        setSymbolData(prev => {
          const next = new Map(prev);
          next.set(ticker.s, symbolInfo);
          return next;
        });
      } catch (error) {
        console.error('Error parsing watchlist message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Watchlist WebSocket error:', error);
      setIsConnected(false);
    };

    ws.onclose = () => {
      console.log('Watchlist WebSocket disconnected');
      setIsConnected(false);
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [symbols]);

  return { symbolData, isConnected };
};
