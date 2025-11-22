import { useState, useEffect } from 'react';
import { qgitaSignalGenerator, QGITASignal } from '@/core/qgitaSignalGenerator';
import { useBinanceMarketData } from './useBinanceMarketData';
import { MasterEquation } from '@/core/masterEquation';

export function useQGITASignals(symbol: string) {
  const [signals, setSignals] = useState<QGITASignal[]>([]);
  const [latestSignal, setLatestSignal] = useState<QGITASignal | null>(null);
  const [masterEq] = useState(() => new MasterEquation());
  
  const { marketData } = useBinanceMarketData(symbol);
  
  useEffect(() => {
    if (!marketData) return;
    
    const interval = setInterval(() => {
      // Step the Master Equation with current market data
      const marketSnapshot = {
        timestamp: marketData.timestamp,
        price: marketData.price,
        volume: marketData.volume,
        volatility: marketData.volatility,
        momentum: marketData.momentum,
        spread: marketData.spread,
      };
      
      const lambdaState = masterEq.step(marketSnapshot);
      
      // Generate QGITA signal
      const signal = qgitaSignalGenerator.generateSignal(
        Date.now(),
        marketData.price,
        marketData.volume,
        lambdaState.lambda,
        lambdaState.coherence,
        lambdaState.substrate,
        lambdaState.observer,
        lambdaState.echo
      );
      
      setLatestSignal(signal);
      
      // Only keep signals that are actionable (BUY/SELL with confidence > 60%)
      if (signal.signalType !== 'HOLD' && signal.confidence >= 60) {
        setSignals(prev => {
          const updated = [...prev, signal];
          // Keep only last 50 signals
          return updated.slice(-50);
        });
      }
    }, 5000); // Check every 5 seconds
    
    return () => clearInterval(interval);
  }, [marketData, masterEq]);
  
  const stats = {
    totalSignals: signals.length,
    buySignals: signals.filter(s => s.signalType === 'BUY').length,
    sellSignals: signals.filter(s => s.signalType === 'SELL').length,
    avgConfidence: signals.length > 0 
      ? signals.reduce((sum, s) => sum + s.confidence, 0) / signals.length 
      : 0,
    tier1Signals: signals.filter(s => s.tier === 1).length,
    tier2Signals: signals.filter(s => s.tier === 2).length,
  };
  
  return {
    signals,
    latestSignal,
    stats,
  };
}
