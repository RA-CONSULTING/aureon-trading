import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { useMarketScanner } from './useMarketScanner';
import { useBinanceBalances } from './useBinanceBalances';

export type WarMode = 'paper' | 'live';
export type WarStatus = 'idle' | 'active' | 'paused' | 'emergency_stopped';

export interface WarConfig {
  lighthouseThreshold: number;
  positionCapUSD: number;
  maxSymbols: number;
  mode: WarMode;
}

export interface WarState {
  status: WarStatus;
  config: WarConfig;
  tradesExecuted: number;
  winCount: number;
  lossCount: number;
  netPnL: number;
  activeSessions: number;
}

const DEFAULT_CONFIG: WarConfig = {
  lighthouseThreshold: 0.45,
  positionCapUSD: 100,
  maxSymbols: 20,
  mode: 'paper',
};

export function useWarRoom() {
  const [warState, setWarState] = useState<WarState>({
    status: 'idle',
    config: DEFAULT_CONFIG,
    tradesExecuted: 0,
    winCount: 0,
    lossCount: 0,
    netPnL: 0,
    activeSessions: 0,
  });

  const { toast } = useToast();
  const { opportunities, scanMarket, isScanning } = useMarketScanner();
  const { accounts, totals, refresh: refreshBalances } = useBinanceBalances();
  const processingRef = useRef(false);
  const scanIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Real-time subscriptions for trading events
  useEffect(() => {
    if (warState.status !== 'active') return;

    const channel = supabase
      .channel('war-room-realtime')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trading_executions',
        },
        (payload) => {
          console.log('🔥 New execution:', payload.new);
          setWarState(prev => ({
            ...prev,
            tradesExecuted: prev.tradesExecuted + 1,
          }));
          refreshBalances();
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'trading_positions',
        },
        (payload: any) => {
          const position = payload.new;
          if (position.status === 'closed' && position.realized_pnl) {
            setWarState(prev => ({
              ...prev,
              netPnL: prev.netPnL + parseFloat(position.realized_pnl),
              winCount: position.realized_pnl > 0 ? prev.winCount + 1 : prev.winCount,
              lossCount: position.realized_pnl < 0 ? prev.lossCount + 1 : prev.lossCount,
            }));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [warState.status, refreshBalances]);

  const launchWar = useCallback(async () => {
    if (warState.status === 'active') return;

    try {
      // Enable trading config
      const { error: configError } = await supabase
        .from('trading_config')
        .update({
          is_enabled: true,
          min_coherence: warState.config.lighthouseThreshold,
          base_position_size_usdt: warState.config.positionCapUSD,
          trading_mode: warState.config.mode,
        })
        .eq('id', (await supabase.from('trading_config').select('id').single()).data?.id || '');

      if (configError) throw configError;

      setWarState(prev => ({
        ...prev,
        status: 'active',
        tradesExecuted: 0,
        winCount: 0,
        lossCount: 0,
        netPnL: 0,
      }));

      // Start aggressive market scanning
      scanMarket();
      scanIntervalRef.current = setInterval(() => {
        scanMarket();
      }, 10000); // Every 10 seconds

      toast({
        title: '🔥 TOTAL WAR LAUNCHED',
        description: `${warState.config.mode.toUpperCase()} mode | Γ≥${warState.config.lighthouseThreshold} | $${warState.config.positionCapUSD} cap`,
      });

      console.log('🔥🔥🔥 TOTAL WAR DECLARED 🔥🔥🔥');
      console.log(`Mode: ${warState.config.mode.toUpperCase()}`);
      console.log(`Lighthouse Threshold: Γ ≥ ${warState.config.lighthouseThreshold}`);
      console.log(`Position Cap: $${warState.config.positionCapUSD}`);
      console.log(`Max Symbols: ${warState.config.maxSymbols}`);
      console.log('🎯 GENERAL QUACKERS: ENGAGING ALL TARGETS');

    } catch (error: any) {
      console.error('Failed to launch war:', error);
      toast({
        title: '❌ Launch Failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [warState, scanMarket, toast]);

  const pauseWar = useCallback(() => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }
    
    setWarState(prev => ({ ...prev, status: 'paused' }));
    
    toast({
      title: '⏸️ War Paused',
      description: 'All trading activity suspended',
    });
  }, [toast]);

  const resumeWar = useCallback(() => {
    setWarState(prev => ({ ...prev, status: 'active' }));
    
    scanMarket();
    scanIntervalRef.current = setInterval(() => {
      scanMarket();
    }, 10000);
    
    toast({
      title: '▶️ War Resumed',
      description: 'Trading activity reactivated',
    });
  }, [scanMarket, toast]);

  const stopWar = useCallback(async () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }

    try {
      const { error } = await supabase
        .from('trading_config')
        .update({ is_enabled: false })
        .eq('id', (await supabase.from('trading_config').select('id').single()).data?.id || '');

      if (error) throw error;

      setWarState(prev => ({ ...prev, status: 'idle' }));
      
      toast({
        title: '🛑 War Stopped',
        description: `${warState.tradesExecuted} trades executed | Net P&L: $${warState.netPnL.toFixed(2)}`,
      });
    } catch (error: any) {
      console.error('Failed to stop war:', error);
      toast({
        title: '❌ Stop Failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [warState.tradesExecuted, warState.netPnL, toast]);

  const emergencyHalt = useCallback(async () => {
    if (scanIntervalRef.current) {
      clearInterval(scanIntervalRef.current);
      scanIntervalRef.current = null;
    }

    try {
      const { error } = await supabase.functions.invoke('emergency-stop');
      
      if (error) throw error;

      setWarState(prev => ({ ...prev, status: 'emergency_stopped' }));
      
      toast({
        title: '🚨 EMERGENCY STOP EXECUTED',
        description: 'All positions closed, orders cancelled',
        variant: 'destructive',
      });
    } catch (error: any) {
      console.error('Emergency stop failed:', error);
      toast({
        title: '❌ Emergency Stop Failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [toast]);

  const updateConfig = useCallback((config: Partial<WarConfig>) => {
    setWarState(prev => ({
      ...prev,
      config: { ...prev.config, ...config },
    }));
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (scanIntervalRef.current) {
        clearInterval(scanIntervalRef.current);
      }
    };
  }, []);

  return {
    warState,
    opportunities: opportunities.slice(0, warState.config.maxSymbols),
    accounts,
    totals,
    isScanning,
    launchWar,
    pauseWar,
    resumeWar,
    stopWar,
    emergencyHalt,
    updateConfig,
  };
}
