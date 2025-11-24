import { useState, useEffect, useCallback, useRef } from 'react';
import { useMarketScanner } from './useMarketScanner';
import { useQueenHive } from './useQueenHive';
import { useOMSQueue } from './useOMSQueue';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { QGITASignalGenerator } from '@/core/qgitaSignalGenerator';

export function useAutonomousTrading() {
  const [isActive, setIsActive] = useState(false);
  const [tradesExecuted, setTradesExecuted] = useState(0);
  const [totalProfit, setTotalProfit] = useState(0);
  const { pairs, isScanning } = useMarketScanner();
  const { session } = useQueenHive();
  const { enqueueOrder, status } = useOMSQueue(session?.id || null);
  const { toast } = useToast();
  const signalGenerator = useRef(new QGITASignalGenerator());
  const lastProcessedRef = useRef<Set<string>>(new Set());

  const processTopOpportunities = useCallback(async () => {
    if (!isActive || !session || !pairs.length) return;

    // Take top 10 opportunities
    const topPairs = pairs.slice(0, 10);
    
    for (const pair of topPairs) {
      // Skip if recently processed
      const key = `${pair.symbol}-${Date.now()}`;
      if (lastProcessedRef.current.has(pair.symbol)) continue;
      
      // Check rate limit utilization
      if (status && status.rateLimit.utilization > 0.8) {
        console.log('⏸️ Rate limit approaching, pausing...');
        break;
      }

      try {
        // Generate QGITA signal
        const marketData = {
          timestamp: Date.now(),
          price: pair.price,
          volume: pair.volume24h,
          volatility: pair.volatility / 100,
          momentum: pair.priceChange24h / 100,
          spread: 0.001,
        };

        const signal = signalGenerator.current.generateSignal(
          marketData.timestamp,
          marketData.price,
          marketData.volume,
          marketData.volatility,
          marketData.momentum,
          marketData.spread,
          0, // liquidityDepth
          0  // orderImbalance
        );
        
        // Only trade Tier 1 and Tier 2 signals
        if (signal.tier <= 2 && signal.signalType !== 'HOLD') {
          // Get hive and agent
          const { data: hives } = await supabase
            .from('hive_instances')
            .select('id')
            .eq('status', 'active')
            .limit(1)
            .single();

          if (!hives) continue;

          const { data: agent } = await supabase
            .from('hive_agents')
            .select('id')
            .eq('hive_id', hives.id)
            .limit(1)
            .single();

          if (!agent) continue;

          // Calculate position size based on opportunity score and tier
          const baseSize = 100;
          const tierMultiplier = signal.tier === 1 ? 2.0 : 1.0;
          const opportunityMultiplier = Math.min(pair.opportunityScore / 10, 2);
          const positionSize = baseSize * tierMultiplier * opportunityMultiplier;
          const quantity = positionSize / pair.price;

          // Calculate priority
          let priority = Math.floor(signal.confidence);
          if (signal.ftcpDetected) priority = Math.min(100, priority + 10);
          if (signal.coherence.crossScaleCoherence > 0.95) priority = Math.min(100, priority + 5);

          // Enqueue order
          await enqueueOrder({
            hiveId: hives.id,
            agentId: agent.id,
            symbol: pair.symbol,
            side: signal.signalType as 'BUY' | 'SELL',
            quantity,
            price: pair.price,
            priority,
            metadata: {
              signalStrength: signal.confidence,
              coherence: signal.coherence.crossScaleCoherence,
              lighthouseValue: signal.lighthouse.L,
            },
          });

          setTradesExecuted(prev => prev + 1);
          lastProcessedRef.current.add(pair.symbol);

          // Cleanup old entries
          setTimeout(() => lastProcessedRef.current.delete(pair.symbol), 60000);
        }
      } catch (error) {
        console.error(`Error processing ${pair.symbol}:`, error);
      }
    }
  }, [isActive, session, pairs, enqueueOrder, status]);

  // Process opportunities every 5 seconds when active
  useEffect(() => {
    if (!isActive) return;

    const interval = setInterval(processTopOpportunities, 5000);
    return () => clearInterval(interval);
  }, [isActive, processTopOpportunities]);

  const start = useCallback(async () => {
    if (!session) {
      toast({
        title: '❌ No Active Session',
        description: 'Start a Queen-Hive session first',
        variant: 'destructive',
      });
      return;
    }

    setIsActive(true);
    toast({
      title: '🚀 Autonomous Trading Started',
      description: 'Scanning market and executing optimal trades',
    });
  }, [session, toast]);

  const stop = useCallback(() => {
    setIsActive(false);
    toast({
      title: '⏸️ Autonomous Trading Stopped',
      description: `Executed ${tradesExecuted} trades`,
    });
  }, [tradesExecuted, toast]);

  return {
    isActive,
    tradesExecuted,
    totalProfit,
    topPairs: pairs.slice(0, 10),
    isScanning,
    start,
    stop,
  };
}
