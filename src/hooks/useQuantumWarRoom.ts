import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';

export interface QuantumState {
  coherence: number;           // REAL Γ from lighthouse_events
  lambda: number;              // REAL Λ(t) from lighthouse_events
  dominantNode: string | null; // REAL from lighthouse_events
  lighthouseSignal: number;    // REAL L value
  prismLevel: number;          // REAL prism level (1-5)
  prismState: string;          // FORMING | CONVERGING | MANIFEST
  isLHE: boolean;              // Is Lighthouse Event active?
  entanglement: number;        // Derived from hive mind coherence
  superposition: number;       // Derived from active systems
  waveFunction: number[];      // 9 Auris node weights
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

export function useQuantumWarRoom() {
  const [state, setState] = useState<WarRoomState>({
    status: 'idle',
    quantumState: createInitialQuantumState(),
    tradesExecuted: 0,
    netPnL: 0,
    currentBalance: 0,
    hiveMindCoherence: 0,
  });

  const { toast } = useToast();
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const balanceIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const dataIngestionIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Register with Temporal Ladder on mount
  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    console.log('🦆 Quantum Quackers registered with Temporal Ladder');

    return () => {
      temporalLadder.unregisterSystem(SYSTEMS.QUANTUM_QUACKERS);
      console.log('🦆 Quantum Quackers unregistered from Temporal Ladder');
    };
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

  // Send heartbeat to Temporal Ladder
  useEffect(() => {
    if (state.status !== 'active') return;

    heartbeatIntervalRef.current = setInterval(() => {
      temporalLadder.heartbeat(SYSTEMS.QUANTUM_QUACKERS, state.quantumState.coherence);
    }, 2000);

    return () => {
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
        heartbeatIntervalRef.current = null;
      }
    };
  }, [state.status, state.quantumState.coherence]);

  // Real-time subscription to lighthouse_events for REAL quantum data
  useEffect(() => {
    if (state.status !== 'active') return;

    const channel = supabase
      .channel('quantum-war-room')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload: any) => {
          const event = payload.new;
          console.log('🔥 REAL Lighthouse Event:', event);
          
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
          }));

          // Broadcast trade to hive mind
          temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'TRADE_EXECUTED', {
            symbol: payload.new.symbol,
            side: payload.new.side,
            status: payload.new.status,
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
            }));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [state.status]);

  // Fetch real-time node weights from master_equation_field_history
  useEffect(() => {
    if (state.status !== 'active') return;

    const fetchNodeWeights = async () => {
      const { data } = await supabase
        .from('master_equation_field_history')
        .select('node_weights')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      if (data?.node_weights) {
        const weights = Object.values(data.node_weights) as number[];
        setState(prev => ({
          ...prev,
          quantumState: {
            ...prev.quantumState,
            waveFunction: weights.length === 9 ? weights : prev.quantumState.waveFunction,
          },
        }));
      }
    };

    fetchNodeWeights();
    const interval = setInterval(fetchNodeWeights, 3000);

    return () => clearInterval(interval);
  }, [state.status]);

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

  // 🔥 DATA INGESTION LOOP - Connect MasterEquation to database
  useEffect(() => {
    if (state.status !== 'active') return;

    const ingestQuantumData = async () => {
      try {
        // Import dynamically to avoid circular deps
        const { MasterEquation } = await import('@/core/masterEquation');
        const { getTemporalId, getSentinelName } = await import('@/core/primelinesIdentity');
        
        const masterEq = new MasterEquation();
        
        // Fetch current market data (simplified for now)
        const snapshot = {
          price: 50000, // Would fetch real BTC price
          volume: 1000000,
          volatility: 0.02,
          momentum: 0.01,
          spread: 0.001,
          timestamp: Date.now()
        };
        
        // Compute Master Equation field state
        const lambdaState = await masterEq.step(snapshot);
        
        // Persist to database via edge function
        const { error } = await supabase.functions.invoke('ingest-master-equation', {
          body: {
            temporal_id: getTemporalId(),
            sentinel_name: getSentinelName(),
            symbol: 'BTCUSDT',
            lambda: lambdaState.lambda,
            substrate: lambdaState.substrate,
            observer: lambdaState.observer,
            echo: lambdaState.echo,
            coherence: lambdaState.coherence,
            coherence_linear: 1.0,
            coherence_nonlinear: lambdaState.coherence,
            coherence_phi: lambdaState.coherence,
            quality_factor: lambdaState.coherence,
            effective_gain: lambdaState.lambda,
            dominant_node: lambdaState.dominantNode,
            node_weights: lambdaState.nodeResponses,
            price: snapshot.price,
            volume: snapshot.volume,
            volatility: snapshot.volatility,
            momentum: snapshot.momentum,
            metadata: {
              stargateInfluence: lambdaState.stargateInfluence,
              earthFieldInfluence: lambdaState.earthFieldInfluence,
              nexusInfluence: lambdaState.nexusInfluence
            }
          }
        });
        
        if (error) {
          console.error('Data ingestion failed:', error);
        } else {
          console.log('✅ Quantum data ingested:', {
            lambda: lambdaState.lambda.toFixed(3),
            coherence: lambdaState.coherence.toFixed(3),
            dominant: lambdaState.dominantNode
          });
        }
      } catch (err) {
        console.error('Data ingestion error:', err);
      }
    };

    // Ingest immediately, then every 3 seconds
    ingestQuantumData();
    dataIngestionIntervalRef.current = setInterval(ingestQuantumData, 3000);

    return () => {
      if (dataIngestionIntervalRef.current) {
        clearInterval(dataIngestionIntervalRef.current);
        dataIngestionIntervalRef.current = null;
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

      // Broadcast assault launch to hive mind
      temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'ASSAULT_LAUNCHED', {
        timestamp: Date.now(),
      });

      toast({
        title: '🚀 QUANTUM ASSAULT LAUNCHED',
        description: 'Autonomous trading activated. Quantum Quackers connected to hive mind.',
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
    coherence: 0,
    lambda: 0,
    dominantNode: null,
    lighthouseSignal: 0,
    prismLevel: 0,
    prismState: 'FORMING',
    isLHE: false,
    entanglement: 0,
    superposition: 0,
    waveFunction: Array(9).fill(1 / 9),
    dominantFrequency: null,
  };
}
