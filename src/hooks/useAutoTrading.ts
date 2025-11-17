import { useEffect, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import type { TradingSignal } from '@/core/tradingSignals';
import type { LighthouseState } from '@/core/lighthouseConsensus';
import type { PrismOutput } from '@/core/prism';

type AutoTradingProps = {
  isEnabled: boolean;
  signal: TradingSignal | null;
  lighthouse: LighthouseState | null;
  prism: PrismOutput | null;
  currentPrice: number;
  currentSymbol: string;
};

export const useAutoTrading = ({
  isEnabled,
  signal,
  lighthouse,
  prism,
  currentPrice,
  currentSymbol,
}: AutoTradingProps) => {
  const { toast } = useToast();
  const lastSignalRef = useRef<string>('');

  useEffect(() => {
    if (!isEnabled || !signal || !lighthouse || !prism) return;

    const executeAutoTrade = async () => {
      // Check if signal is actionable (not HOLD)
      if (signal.type === 'HOLD') return;

      // Create unique signal key to avoid duplicate executions
      const signalKey = `${signal.timestamp}-${signal.type}-${currentSymbol}`;
      if (lastSignalRef.current === signalKey) return;

      // Check if lighthouse event was detected
      if (!lighthouse.isLHE) {
        console.log('No LHE detected, skipping auto-trade');
        return;
      }

      console.log('🎯 Auto-trading: Executing trade on signal', {
        type: signal.type,
        strength: signal.strength,
        lighthouse: lighthouse.L,
        coherence: signal.coherence,
        prismLevel: prism.level,
      });

      lastSignalRef.current = signalKey;

      try {
        const { data, error } = await supabase.functions.invoke('execute-trade', {
          body: {
            signalType: signal.type,
            symbol: currentSymbol,
            coherence: signal.coherence,
            lighthouseValue: signal.lighthouse,
            lighthouseConfidence: lighthouse.confidence,
            prismLevel: prism.level,
            currentPrice,
          },
        });

        if (error) throw error;

        if (data?.success) {
          toast({
            title: '✅ Trade Executed',
            description: data.message,
            duration: 5000,
          });
        } else {
          toast({
            title: 'Trade Skipped',
            description: data.error || 'Trade did not meet criteria',
            variant: 'destructive',
            duration: 3000,
          });
        }
      } catch (error) {
        console.error('Auto-trading error:', error);
        toast({
          title: 'Trade Execution Failed',
          description: error instanceof Error ? error.message : 'Unknown error',
          variant: 'destructive',
          duration: 5000,
        });
      }
    };

    executeAutoTrade();
  }, [isEnabled, signal, lighthouse, prism, currentPrice, currentSymbol, toast]);
};
