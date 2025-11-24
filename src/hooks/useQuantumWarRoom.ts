import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';

export interface QuantumState {
  coherence: number;
  entanglement: number;
  superposition: number;
  waveFunction: number[];
  dominantFrequency: number | null;
}

export type AssaultStatus = 'idle' | 'active' | 'emergency_stopped';

export interface WarRoomState {
  status: AssaultStatus;
  quantumState: QuantumState;
  tradesExecuted: number;
  netPnL: number;
  currentBalance: number;
}

const WAVE_SLOTS = 10;
const COHERENCE_DECAY = 0.002;
const ENTANGLEMENT_DECAY = 0.001;

export function useQuantumWarRoom() {
  const [state, setState] = useState<WarRoomState>({
    status: 'idle',
    quantumState: createInitialQuantumState(),
    tradesExecuted: 0,
    netPnL: 0,
    currentBalance: 0,
  });

  const { toast } = useToast();
  const evolutionRef = useRef<NodeJS.Timeout | null>(null);
  const balanceIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Register with temporal ladder
  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    
    return () => {
      temporalLadder.unregisterSystem(SYSTEMS.QUANTUM_QUACKERS);
      if (evolutionRef.current) clearInterval(evolutionRef.current);
      if (balanceIntervalRef.current) clearInterval(balanceIntervalRef.current);
    };
  }, []);

  // Heartbeat to temporal ladder
  useEffect(() => {
    const interval = setInterval(() => {
      temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, state.quantumState.coherence);
    }, 2000);
    return () => clearInterval(interval);
  }, [state.quantumState.coherence]);

  // Auto-evolve quantum state
  useEffect(() => {
    if (state.status !== 'active') return;

    evolutionRef.current = setInterval(() => {
      setState(prev => ({
        ...prev,
        quantumState: evolveQuantumState(prev.quantumState),
      }));
    }, 100);

    return () => {
      if (evolutionRef.current) {
        clearInterval(evolutionRef.current);
        evolutionRef.current = null;
      }
    };
  }, [state.status]);

  // Real-time subscriptions
  useEffect(() => {
    if (state.status !== 'active') return;

    const channel = supabase
      .channel('quantum-war-room')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trading_executions',
        },
        (payload) => {
          console.log('🎯 New execution:', payload.new);
          setState(prev => ({
            ...prev,
            tradesExecuted: prev.tradesExecuted + 1,
            quantumState: boostQuantumState(prev.quantumState, 0.05),
          }));

          // Broadcast to hive mind
          temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'trade_execution', {
            symbol: payload.new.symbol,
            side: payload.new.side,
            coherence: state.quantumState.coherence,
          });
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
            const pnl = parseFloat(String(position.realized_pnl));
            setState(prev => ({
              ...prev,
              netPnL: prev.netPnL + pnl,
              quantumState: boostQuantumState(prev.quantumState, pnl > 0 ? 0.03 : -0.02),
            }));
          }
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload: any) => {
          if (payload.new.is_lhe) {
            console.log('🔥 LHE EVENT!', payload.new);
            setState(prev => ({
              ...prev,
              quantumState: boostQuantumState(prev.quantumState, 0.1),
            }));

            // Request assistance if high coherence
            if (state.quantumState.coherence > 0.9) {
              temporalLadder.requestAssistance(
                SYSTEMS.QUANTUM_QUACKERS,
                SYSTEMS.NEXUS_FEED,
                'lhe_amplification'
              );
            }
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [state.status, state.quantumState.coherence]);

  // Fetch balance periodically
  useEffect(() => {
    if (state.status !== 'active') return;

    const fetchBalance = async () => {
      try {
        const { data, error } = await supabase.functions.invoke('get-binance-balances');
        if (!error && data?.totals?.totalUSDT) {
          setState(prev => ({
            ...prev,
            currentBalance: parseFloat(data.totals.totalUSDT),
          }));
        }
      } catch (err) {
        console.error('Failed to fetch balance:', err);
      }
    };

    fetchBalance();
    balanceIntervalRef.current = setInterval(fetchBalance, 5000);

    return () => {
      if (balanceIntervalRef.current) {
        clearInterval(balanceIntervalRef.current);
        balanceIntervalRef.current = null;
      }
    };
  }, [state.status]);

  const launchAssault = useCallback(async () => {
    if (state.status === 'active') return;

    try {
      // Enable trading
      const { error } = await supabase
        .from('trading_config')
        .update({ is_enabled: true })
        .eq('id', (await supabase.from('trading_config').select('id').single()).data?.id || '');

      if (error) throw error;

      setState(prev => ({
        ...prev,
        status: 'active',
        tradesExecuted: 0,
        netPnL: 0,
      }));

      toast({
        title: '🚀 QUANTUM ASSAULT LAUNCHED',
        description: 'Autonomous trading activated. Quantum Quackers is now in control.',
      });

      // Broadcast launch
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'assault_launched', {
        timestamp: new Date().toISOString(),
        coherence: state.quantumState.coherence,
      });

    } catch (error: any) {
      console.error('Failed to launch assault:', error);
      toast({
        title: '❌ Launch Failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [state, toast]);

  const emergencyStop = useCallback(async () => {
    try {
      await supabase.functions.invoke('emergency-stop');
      
      setState(prev => ({
        ...prev,
        status: 'emergency_stopped',
      }));

      toast({
        title: '🚨 EMERGENCY STOP',
        description: 'All trading halted immediately.',
        variant: 'destructive',
      });

      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'emergency_stop', {
        timestamp: new Date().toISOString(),
      });
    } catch (error: any) {
      console.error('Emergency stop failed:', error);
    }
  }, [toast]);

  return {
    state,
    launchAssault,
    emergencyStop,
  };
}

function createInitialQuantumState(): QuantumState {
  return {
    coherence: 0.75,
    entanglement: 0.5,
    superposition: 0.6,
    waveFunction: Array.from({ length: WAVE_SLOTS }, () => 1 / WAVE_SLOTS),
    dominantFrequency: null,
  };
}

function evolveQuantumState(state: QuantumState): QuantumState {
  const newWave = state.waveFunction.map(amp => {
    const noise = (Math.random() - 0.5) * 0.02;
    return Math.max(0, Math.min(1, amp + noise));
  });

  const sum = newWave.reduce((a, b) => a + b, 0);
  const normalized = sum > 0 ? newWave.map(a => a / sum) : newWave;

  return {
    ...state,
    coherence: Math.max(0.3, state.coherence - COHERENCE_DECAY),
    entanglement: Math.max(0.2, state.entanglement - ENTANGLEMENT_DECAY),
    waveFunction: normalized,
  };
}

function boostQuantumState(state: QuantumState, boost: number): QuantumState {
  return {
    ...state,
    coherence: Math.min(1, Math.max(0, state.coherence + boost)),
    entanglement: Math.min(1, Math.max(0, state.entanglement + boost * 0.5)),
    superposition: Math.min(1, Math.max(0, state.superposition + boost * 0.3)),
  };
}
