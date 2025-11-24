import { useState, useEffect, useCallback, useRef } from 'react';
import { useMarketScanner } from './useMarketScanner';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { QGITASignalGenerator } from '@/core/qgitaSignalGenerator';

const TRADING_FEE_RATE = 0.001; // 0.1% per trade

export function useAutonomousTrading() {
  const [isActive, setIsActive] = useState(false);
  const [tradesExecuted, setTradesExecuted] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);
  const [totalFees, setTotalFees] = useState(0);
  const [netProfit, setNetProfit] = useState(0);
  const { opportunities, scanMarket, isScanning } = useMarketScanner();
  const { toast } = useToast();
  const signalGenerator = useRef(new QGITASignalGenerator());
  const processingRef = useRef(false);

  // Calculate net profit
  useEffect(() => {
    setNetProfit(totalProfit - totalFees);
  }, [totalProfit, totalFees]);

  const processOpportunity = useCallback(async (opp: any) => {
    try {
      // Generate QGITA signal
      const signal = signalGenerator.current.generateSignal(
        Date.now(),
        opp.price,
        opp.volume24h,
        opp.volatility,
        opp.momentum,
        0.001, // spread
        0, // liquidityDepth
        0  // orderImbalance
      );

      // Only trade Tier 1 and Tier 2 signals
      if (signal.tier > 2 || signal.signalType === 'HOLD') return;

      console.log(`🎯 Signal generated for ${opp.symbol}: ${signal.signalType} | Tier ${signal.tier} | Strength ${signal.confidence.toFixed(2)}`);

      // Use existing execute-trade edge function
      const { data, error } = await supabase.functions.invoke('execute-trade', {
        body: {
          symbol: opp.symbol,
          signalType: signal.signalType === 'BUY' ? 'LONG' : 'SHORT',
          coherence: signal.coherence.crossScaleCoherence,
          lighthouseValue: signal.lighthouse.L,
          lighthouseConfidence: signal.confidence,
          prismLevel: signal.tier,
          currentPrice: opp.price,
        }
      });

      if (error) {
        console.error(`❌ Trade execution failed for ${opp.symbol}:`, error);
        return;
      }

      if (data?.success) {
        setTradesExecuted(prev => prev + 1);
        
        // Calculate estimated fee (both entry and exit)
        const positionSize = 100; // From trading config
        const estimatedFee = (positionSize * TRADING_FEE_RATE * 2); // Entry + exit
        setTotalFees(prev => prev + estimatedFee);
        
        const estimatedProfit = positionSize * 0.02; // 2% target
        setTotalProfit(prev => prev + estimatedProfit);
        
        console.log(`✅ Trade executed: ${data.message}`);
      }
    } catch (error) {
      console.error(`❌ Failed to process ${opp.symbol}:`, error);
    }
  }, []);

  // Process opportunities when active
  useEffect(() => {
    if (!isActive || processingRef.current) return;

    const processTopOpportunities = async () => {
      if (opportunities.length === 0) return;
      
      processingRef.current = true;
      
      // Process top 10 opportunities in parallel (respecting rate limits)
      const topOpportunities = opportunities.slice(0, 10);
      
      for (const opp of topOpportunities) {
        if (!isActive) break;
        await processOpportunity(opp);
        await new Promise(resolve => setTimeout(resolve, 200)); // Rate limiting
      }
      
      processingRef.current = false;
    };

    processTopOpportunities();
  }, [opportunities, isActive, processOpportunity]);

  // Auto-scan every 30 seconds when active
  useEffect(() => {
    if (!isActive) return;

    scanMarket();
    const interval = setInterval(scanMarket, 30000);
    return () => clearInterval(interval);
  }, [isActive, scanMarket]);

  const start = useCallback(() => {
    setIsActive(true);
    setTradesExecuted(0);
    setTotalProfit(0);
    setTotalFees(0);
    toast({
      title: '🚀 Autonomous Trading Started',
      description: 'Using execute-trade, fetch-binance-symbols edge functions',
    });
    console.log('🚀 Autonomous trading started - using existing edge functions');
  }, [toast]);

  const stop = useCallback(() => {
    setIsActive(false);
    toast({
      title: '⏸️ Autonomous Trading Stopped',
      description: `Executed ${tradesExecuted} trades | Net: $${netProfit.toFixed(2)}`,
    });
    console.log('⏸️ Autonomous trading stopped');
  }, [tradesExecuted, netProfit, toast]);

  return {
    isActive,
    isScanning,
    tradesExecuted,
    totalProfit,
    totalFees,
    netProfit,
    opportunities: opportunities.slice(0, 10),
    start,
    stop,
  };
}
