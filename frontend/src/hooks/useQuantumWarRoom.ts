import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';
import { unifiedBus } from '@/core/unifiedBus';
import { globalSystemsManager } from '@/core/globalSystemsManager';
import { useGlobalState, useGlobalTradingControls } from '@/hooks/useGlobalState';

export interface QuantumState {
  coherence: number;
  lambda: number;
  dominantNode: string | null;
  lighthouseSignal: number;
  prismLevel: number;
  prismState: string;
  isLHE: boolean;
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
  hiveMindCoherence: number;
}

function createInitialQuantumState(): QuantumState {
  return {
    coherence: 0,
    lambda: 0,
    dominantNode: null,
    lighthouseSignal: 0,
    prismLevel: 0,
    prismState: 'FORMING',
    isLHE: false,
    entanglement: 0,
    superposition: 0,
    waveFunction: Array(9).fill(0),
    dominantFrequency: null,
  };
}

export function useQuantumWarRoom() {
  // Get global state directly from GlobalSystemsManager
  const globalState = useGlobalState();
  const { startTrading, stopTrading } = useGlobalTradingControls();
  const { toast } = useToast();
  
  const [state, setState] = useState<WarRoomState>({
    status: globalState.isActive ? 'active' : 'idle',
    quantumState: createInitialQuantumState(),
    tradesExecuted: globalState.totalTrades,
    netPnL: globalState.totalPnl,
    currentBalance: globalState.totalEquity,
    hiveMindCoherence: 0,
  });

  // Register War Room with Temporal Ladder on mount
  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    console.log('🦆 War Room registered with Temporal Ladder');

    return () => {
      temporalLadder.unregisterSystem(SYSTEMS.QUANTUM_QUACKERS);
      console.log('🦆 War Room unregistered from Temporal Ladder');
    };
  }, []);

  // Subscribe to GlobalSystemsManager state changes
  useEffect(() => {
    setState(prev => ({
      ...prev,
      status: globalState.isActive ? 'active' : (globalState.isRunning ? 'active' : 'idle'),
      tradesExecuted: globalState.totalTrades,
      netPnL: globalState.totalPnl,
      currentBalance: globalState.totalEquity,
      quantumState: {
        ...prev.quantumState,
        coherence: globalState.coherence,
        lambda: globalState.lambda,
        dominantNode: globalState.dominantNode,
        lighthouseSignal: globalState.lighthouseSignal,
        prismLevel: globalState.prismLevel,
        prismState: globalState.prismState,
        isLHE: globalState.coherence > 0.945,
        dominantFrequency: globalState.prismOutput?.frequency || null,
      }
    }));
  }, [globalState]);

  // Subscribe to UnifiedBus for consensus data
  useEffect(() => {
    const unsubscribe = unifiedBus.subscribe((snapshot) => {
      setState(prev => ({
        ...prev,
        hiveMindCoherence: snapshot.consensusConfidence,
        quantumState: {
          ...prev.quantumState,
          entanglement: snapshot.consensusConfidence,
          superposition: Object.keys(snapshot.states).length / 10,
        }
      }));
    });

    return unsubscribe;
  }, []);

  // Subscribe to Temporal Ladder hive mind
  useEffect(() => {
    const unsubscribe = temporalLadder.subscribe((ladderState) => {
      setState(prev => ({
        ...prev,
        hiveMindCoherence: ladderState.hiveMindCoherence,
        quantumState: {
          ...prev.quantumState,
          entanglement: ladderState.hiveMindCoherence,
          superposition: ladderState.activeChain.length / 8,
        },
      }));
    });

    return unsubscribe;
  }, []);

  // Send heartbeat to Temporal Ladder when active
  useEffect(() => {
    if (state.status !== 'active') return;

    const interval = setInterval(() => {
      temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, state.quantumState.coherence);
    }, 2000);

    return () => clearInterval(interval);
  }, [state.status, state.quantumState.coherence]);

  // Real-time subscription to database events for live updates
  useEffect(() => {
    const channel = supabase
      .channel('war-room-live')
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'lighthouse_events' },
        (payload: any) => {
          const event = payload.new;
          console.log('🔥 War Room: Lighthouse Event:', event);
          
          // Get node weights from bus
          const busSnapshot = unifiedBus.snapshot();
          const masterEqState = busSnapshot.states['MasterEquation'];
          const nodeWeights = masterEqState?.data?.nodeWeights as number[] || Array(9).fill(0);
          
          setState(prev => ({
            ...prev,
            quantumState: {
              ...prev.quantumState,
              coherence: event.coherence,
              lambda: event.lambda_value,
              dominantNode: event.dominant_node,
              lighthouseSignal: event.lighthouse_signal,
              prismLevel: event.prism_level || 0,
              prismState: event.prism_state || 'FORMING',
              isLHE: event.is_lhe,
              dominantFrequency: event.is_lhe ? 528 : null,
              waveFunction: nodeWeights,
            },
          }));

          // Request assistance from Nexus Feed on high coherence
          if (event.coherence > 0.9) {
            temporalLadder.requestAssistance(
              SYSTEMS.QUANTUM_QUACKERS,
              SYSTEMS.NEXUS_FEED,
              'high_coherence_amplification'
            );
          }
        }
      )
      .on(
        'postgres_changes',
        { event: 'INSERT', schema: 'public', table: 'trading_executions' },
        (payload) => {
          console.log('🎯 War Room: New execution:', payload.new);
          setState(prev => ({
            ...prev,
            tradesExecuted: prev.tradesExecuted + 1,
          }));

          // Broadcast trade to hive mind
          temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'TRADE_EXECUTED', {
            symbol: (payload.new as any).symbol,
            side: (payload.new as any).side,
            status: (payload.new as any).status,
          });
        }
      )
      .on(
        'postgres_changes',
        { event: 'UPDATE', schema: 'public', table: 'trading_positions' },
        (payload: any) => {
          const position = payload.new;
          if (position.status === 'closed' && position.realized_pnl) {
            const pnl = parseFloat(String(position.realized_pnl));
            setState(prev => ({
              ...prev,
              netPnL: prev.netPnL + pnl,
            }));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const launchAssault = useCallback(async () => {
    if (state.status === 'active') return;

    try {
      // Use GlobalSystemsManager to start trading
      startTrading();
      
      setState(prev => ({
        ...prev,
        status: 'active',
        tradesExecuted: 0,
        netPnL: 0,
      }));

      // Broadcast assault launch to hive mind
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'ASSAULT_LAUNCHED', {
        timestamp: Date.now(),
      });

      toast({
        title: '🚀 QUANTUM ASSAULT LAUNCHED',
        description: 'Autonomous trading activated. Connected to GlobalSystemsManager.',
      });

    } catch (error: any) {
      console.error('Failed to launch assault:', error);
      toast({
        title: '❌ Launch Failed',
        description: error.message,
        variant: 'destructive',
      });
    }
  }, [state, toast, startTrading]);

  const emergencyStop = useCallback(async () => {
    try {
      await supabase.functions.invoke('emergency-stop');
      
      // Use GlobalSystemsManager to stop trading
      stopTrading();
      
      setState(prev => ({
        ...prev,
        status: 'emergency_stopped',
      }));

      // Broadcast emergency stop
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'EMERGENCY_STOP', {
        reason: 'manual_trigger',
      });

      toast({
        title: '🚨 EMERGENCY STOP',
        description: 'All trading halted immediately.',
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
  }, [toast, stopTrading]);

  return {
    state,
    launchAssault,
    emergencyStop,
  };
}
