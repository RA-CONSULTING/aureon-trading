import { useEffect, useState } from 'react';
import { BinanceWebSocketClient, MarketData } from '@/core/binanceWebSocket';
import { MasterEquation } from '@/core/masterEquation';
import type { LambdaState } from '@/core/masterEquation';

export interface LiveTradingSignal {
  timestamp: number;
  signal: 'LONG' | 'SHORT' | 'HOLD';
  strength: number;
  reason: string;
  lambda: LambdaState;
  marketData: MarketData;
  prismLevel: number;
}

export const useLiveTradingSignals = (symbol: string = 'btcusdt') => {
  const [signals, setSignals] = useState<LiveTradingSignal[]>([]);
  const [currentLambda, setCurrentLambda] = useState<LambdaState | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [wsClient, setWsClient] = useState<BinanceWebSocketClient | null>(null);
  const [lastMarketData, setLastMarketData] = useState<MarketData | null>(null);
  const [masterEq] = useState(() => new MasterEquation());

  useEffect(() => {
    console.log('[useLiveTradingSignals] Initializing WebSocket for', symbol);
    
    const client = new BinanceWebSocketClient(symbol);
    
    client.onConnect(() => {
      console.log('✅ [useLiveTradingSignals] Connected to Binance');
      setIsConnected(true);
    });

    client.onDisconnect(() => {
      console.log('🔌 [useLiveTradingSignals] Disconnected from Binance');
      setIsConnected(false);
    });

    client.onError((error) => {
      console.error('❌ [useLiveTradingSignals] Error:', error);
      setIsConnected(false);
    });

    client.onData(async (marketData: MarketData) => {
      setLastMarketData(marketData);
      
      // Compute Master Equation state
      const lambda = await masterEq.step({
        price: marketData.price,
        volume: marketData.volume,
        volatility: marketData.volatility,
        momentum: marketData.momentum,
        spread: marketData.spread,
        timestamp: marketData.timestamp,
      });
      
      setCurrentLambda(lambda);

      // Generate trading signals based on coherence threshold
      if (lambda.coherence >= 0.92) {
        const newSignal: LiveTradingSignal = {
          timestamp: Date.now(),
          signal: lambda.substrate > 0 ? 'LONG' : lambda.substrate < -0.1 ? 'SHORT' : 'HOLD',
          strength: lambda.coherence,
          reason: `Λ=${lambda.lambda.toFixed(3)}, Γ=${lambda.coherence.toFixed(3)}, ${lambda.dominantNode.toUpperCase()}`,
          lambda,
          marketData,
          prismLevel: Math.floor(lambda.coherence * 5), // 0-5 prism levels
        };

        setSignals(prev => [newSignal, ...prev].slice(0, 50)); // Keep last 50 signals
      }
    });

    client.connect();
    setWsClient(client);

    return () => {
      console.log('[useLiveTradingSignals] Cleaning up WebSocket');
      client.disconnect();
    };
  }, [symbol, masterEq]);

  return {
    signals,
    currentLambda,
    isConnected,
    lastMarketData,
    connectionHealth: wsClient?.getConnectionHealth() || { connected: false, healthy: false, attempts: 0 },
  };
};