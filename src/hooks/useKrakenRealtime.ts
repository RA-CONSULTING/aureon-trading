/**
 * useKrakenRealtime Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Manages Kraken WebSocket connection lifecycle and provides real-time ticker data
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { krakenWebSocket, KrakenTicker } from '@/core/krakenWebSocket';

interface KrakenRealtimeState {
  isConnected: boolean;
  tickers: Record<string, KrakenTicker>;
  lastUpdate: number | null;
  error: string | null;
  connectionAttempts: number;
}

interface UseKrakenRealtimeOptions {
  symbols?: string[];
  autoConnect?: boolean;
}

const DEFAULT_SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT'];

export function useKrakenRealtime(options: UseKrakenRealtimeOptions = {}) {
  const { symbols = DEFAULT_SYMBOLS, autoConnect = true } = options;
  
  const [state, setState] = useState<KrakenRealtimeState>({
    isConnected: false,
    tickers: {},
    lastUpdate: null,
    error: null,
    connectionAttempts: 0,
  });
  
  const isConnecting = useRef(false);
  const hasConnected = useRef(false);

  const handleTickerUpdate = useCallback((ticker: KrakenTicker) => {
    setState(prev => ({
      ...prev,
      tickers: {
        ...prev.tickers,
        [ticker.symbol]: ticker,
      },
      lastUpdate: Date.now(),
      error: null,
    }));
  }, []);

  const connect = useCallback(async () => {
    if (isConnecting.current || krakenWebSocket.getIsConnected()) {
      console.log('🦑 Already connected or connecting to Kraken');
      return;
    }

    isConnecting.current = true;
    setState(prev => ({
      ...prev,
      connectionAttempts: prev.connectionAttempts + 1,
    }));

    try {
      await krakenWebSocket.connect();
      
      // Subscribe to all symbols
      symbols.forEach(symbol => {
        krakenWebSocket.subscribeTicker(symbol, handleTickerUpdate);
      });

      setState(prev => ({
        ...prev,
        isConnected: true,
        error: null,
      }));
      
      hasConnected.current = true;
      console.log(`🦑 Kraken realtime connected, subscribed to ${symbols.length} symbols`);
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Connection failed';
      console.error('🦑 Kraken connection error:', errorMessage);
      setState(prev => ({
        ...prev,
        isConnected: false,
        error: errorMessage,
      }));
    } finally {
      isConnecting.current = false;
    }
  }, [symbols, handleTickerUpdate]);

  const disconnect = useCallback(() => {
    krakenWebSocket.disconnect();
    setState(prev => ({
      ...prev,
      isConnected: false,
    }));
    hasConnected.current = false;
    console.log('🦑 Kraken realtime disconnected');
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect && !hasConnected.current) {
      connect();
    }

    return () => {
      // Don't disconnect on unmount to preserve connection across component remounts
      // krakenWebSocket.disconnect();
    };
  }, [autoConnect, connect]);

  // Check connection status periodically
  useEffect(() => {
    const interval = setInterval(() => {
      const isConnected = krakenWebSocket.getIsConnected();
      setState(prev => {
        if (prev.isConnected !== isConnected) {
          return { ...prev, isConnected };
        }
        return prev;
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Get specific ticker
  const getTicker = useCallback((symbol: string): KrakenTicker | undefined => {
    // Map standard symbol to Kraken format for lookup
    const symbolMap: Record<string, string> = {
      'BTCUSDT': 'XBT/USDT',
      'ETHUSDT': 'ETH/USDT',
      'SOLUSDT': 'SOL/USDT',
      'XRPUSDT': 'XRP/USDT',
      'ADAUSDT': 'ADA/USDT',
    };
    const krakenSymbol = symbolMap[symbol] || symbol;
    return state.tickers[krakenSymbol];
  }, [state.tickers]);

  // Get BTC price specifically
  const btcPrice = state.tickers['XBT/USDT']?.price || state.tickers['XBT/USD']?.price || null;
  const ethPrice = state.tickers['ETH/USDT']?.price || state.tickers['ETH/USD']?.price || null;

  return {
    ...state,
    connect,
    disconnect,
    getTicker,
    btcPrice,
    ethPrice,
    tickerCount: Object.keys(state.tickers).length,
  };
}
