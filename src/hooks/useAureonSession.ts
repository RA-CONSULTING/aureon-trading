import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { unifiedOrchestrator, type OrchestrationResult } from '@/core/unifiedOrchestrator';
import { unifiedBus, type BusSnapshot } from '@/core/unifiedBus';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';
import { multiExchangeClient, type MultiExchangeState } from '@/core/multiExchangeClient';
import { thePrism, type PrismOutput } from '@/core/thePrism';
import { toast } from 'sonner';

export interface QuantumState {
  coherence: number;
  lambda: number;
  lighthouseSignal: number;
  dominantNode: string;
  prismLevel: number;
  prismState: string;
  substrate: number;
  observer: number;
  echo: number;
}

export interface TradingState {
  isActive: boolean;
  totalEquity: number;
  availableBalance: number;
  totalTrades: number;
  winningTrades: number;
  totalPnl: number;
  gasTankBalance: number;
  recentTrades: Array<{
    time: string;
    side: string;
    symbol: string;
    quantity: number;
    pnl: number;
    success: boolean;
  }>;
}

export interface SystemStatus {
  masterEquation: boolean;
  lighthouse: boolean;
  rainbowBridge: boolean;
  elephantMemory: boolean;
  orderRouter: boolean;
}

export interface BusState {
  snapshot: BusSnapshot | null;
  consensusSignal: string;
  consensusConfidence: number;
  systemsReady: number;
}

export interface ExchangeState {
  totalEquityUsd: number;
  exchanges: Array<{ exchange: string; connected: boolean; totalUsdValue: number }>;
}

export interface PrismState {
  output: PrismOutput | null;
  frequency: number;
  resonance: number;
  isLoveLocked: boolean;
}

export interface MarketData {
  price: number;
  volume: number;
  volatility: number;
  momentum: number;
  spread: number;
  timestamp: number;
}

export function useAureonSession(userId: string | null) {
  const [quantumState, setQuantumState] = useState<QuantumState>({
    coherence: 0,
    lambda: 0,
    lighthouseSignal: 0,
    dominantNode: 'Tiger',
    prismLevel: 0,
    prismState: 'FORMING',
    substrate: 0,
    observer: 0,
    echo: 0
  });

  const [prismState, setPrismState] = useState<PrismState>({
    output: null,
    frequency: 0,
    resonance: 0,
    isLoveLocked: false
  });

  const [marketData, setMarketData] = useState<MarketData>({
    price: 0,
    volume: 0,
    volatility: 0,
    momentum: 0,
    spread: 0,
    timestamp: 0
  });
  
  const [tradingState, setTradingState] = useState<TradingState>({
    isActive: false,
    totalEquity: 0,
    availableBalance: 0,
    totalTrades: 0,
    winningTrades: 0,
    totalPnl: 0,
    gasTankBalance: 100,
    recentTrades: []
  });
  
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    masterEquation: false,
    lighthouse: false,
    rainbowBridge: false,
    elephantMemory: false,
    orderRouter: false
  });

  const [busState, setBusState] = useState<BusState>({
    snapshot: null,
    consensusSignal: 'NEUTRAL',
    consensusConfidence: 0,
    systemsReady: 0
  });

  const [exchangeState, setExchangeState] = useState<ExchangeState>({
    totalEquityUsd: 0,
    exchanges: []
  });
  
  const [lastSignal, setLastSignal] = useState<string | null>(null);
  const [nextCheckIn, setNextCheckIn] = useState(3);
  const [lastDecision, setLastDecision] = useState<OrchestrationResult | null>(null);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);
  const busUnsubRef = useRef<(() => void) | null>(null);
  const exchangeUnsubRef = useRef<(() => void) | null>(null);

  // Fetch real market data via edge function
  const fetchMarketData = useCallback(async (symbol: string = 'BTCUSDT') => {
    try {
      const { data, error } = await supabase.functions.invoke('get-user-market-data', {
        body: { symbol }
      });

      if (error) throw error;
      return data;
    } catch (error) {
      console.error('[Aureon] Market data fetch failed, using fallback:', error);
      // Fallback to simulated data if edge function fails
      return {
        price: 67000 + (Math.random() - 0.5) * 1000,
        volume: 1000000 + Math.random() * 500000,
        volatility: 0.02 + Math.random() * 0.03,
        momentum: (Math.random() - 0.5) * 0.1,
        spread: 0.0001 + Math.random() * 0.0005,
        timestamp: Date.now()
      };
    }
  }, []);

  // Initialize all systems
  const initializeSystems = useCallback(async () => {
    try {
      // Register systems with Temporal Ladder
      temporalLadder.registerSystem(SYSTEMS.MASTER_EQUATION);
      temporalLadder.registerSystem(SYSTEMS.HARMONIC_NEXUS);
      temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);

      // Initialize multi-exchange client
      await multiExchangeClient.initialize();

      // Subscribe to UnifiedBus updates
      busUnsubRef.current = unifiedBus.subscribe((snapshot) => {
        setBusState({
          snapshot,
          consensusSignal: snapshot.consensusSignal,
          consensusConfidence: snapshot.consensusConfidence,
          systemsReady: snapshot.systemsReady
        });
      });

      // Subscribe to exchange updates
      exchangeUnsubRef.current = multiExchangeClient.subscribe((state: MultiExchangeState) => {
        setExchangeState({
          totalEquityUsd: state.totalEquityUsd,
          exchanges: state.exchanges.map(e => ({
            exchange: e.exchange,
            connected: e.connected,
            totalUsdValue: e.totalUsdValue
          }))
        });
      });

      setSystemStatus({
        masterEquation: true,
        lighthouse: true,
        rainbowBridge: true,
        elephantMemory: true,
        orderRouter: true
      });

      console.log('[Aureon] All systems initialized and registered with Temporal Ladder');
      return true;
    } catch (error) {
      console.error('[Aureon] Failed to initialize systems:', error);
      return false;
    }
  }, []);

  // Run quantum computation cycle using UnifiedOrchestrator
  const runQuantumCycle = useCallback(async () => {
    if (!userId) return;

    try {
      // Fetch real market data
      const marketData = await fetchMarketData('BTCUSDT');

      // Run unified orchestrator cycle (handles all systems + bus + consensus)
      const result = await unifiedOrchestrator.runCycle(marketData, 'BTCUSDT');
      setLastDecision(result);

      // Store market data for Prism
      setMarketData(marketData);

      // Update quantum state from orchestration result
      if (result.lambdaState) {
        // Run The Prism transformation
        const prismOutput = thePrism.transform({
          lambda: result.lambdaState.lambda,
          coherence: result.lambdaState.coherence,
          substrate: result.lambdaState.substrate,
          observer: result.lambdaState.observer,
          echo: result.lambdaState.echo,
          volatility: marketData.volatility,
          momentum: marketData.momentum,
          baseFrequency: result.rainbowState?.frequency || 396
        });

        setPrismState({
          output: prismOutput,
          frequency: prismOutput.frequency,
          resonance: prismOutput.resonance,
          isLoveLocked: prismOutput.isLoveLocked
        });

        const newQuantumState: QuantumState = {
          coherence: result.lambdaState.coherence,
          lambda: result.lambdaState.lambda,
          lighthouseSignal: result.lighthouseState?.L || 0,
          dominantNode: result.lambdaState.dominantNode,
          prismLevel: prismOutput.level,
          prismState: prismOutput.state,
          substrate: result.lambdaState.substrate,
          observer: result.lambdaState.observer,
          echo: result.lambdaState.echo
        };
        
        setQuantumState(newQuantumState);

        // Send heartbeat to Temporal Ladder
        temporalLadder.heartbeat(SYSTEMS.MASTER_EQUATION, result.lambdaState.coherence);
        temporalLadder.heartbeat(SYSTEMS.HARMONIC_NEXUS, result.busSnapshot.consensusConfidence);

        // Update database
        await supabase
          .from('aureon_user_sessions')
          .update({
            current_coherence: newQuantumState.coherence,
            current_lambda: newQuantumState.lambda,
            current_lighthouse_signal: newQuantumState.lighthouseSignal,
            dominant_node: newQuantumState.dominantNode,
            prism_level: newQuantumState.prismLevel,
            prism_state: newQuantumState.prismState,
            last_quantum_update_at: new Date().toISOString()
          })
          .eq('user_id', userId);
      }

      // Handle trade signals
      if (result.finalDecision.action !== 'HOLD' && tradingState.gasTankBalance > 0) {
        const signal = `${result.finalDecision.action} BTCUSDT @ $${marketData.price.toFixed(2)}`;
        setLastSignal(signal);

        // Broadcast trade signal to Temporal Ladder
        temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'TRADE_SIGNAL', {
          action: result.finalDecision.action,
          symbol: 'BTCUSDT',
          confidence: result.finalDecision.confidence,
          reason: result.finalDecision.reason
        });
        
        // Simulate trade execution for paper trading
        const pnl = (Math.random() - 0.3) * 50;
        const newTrade = {
          time: new Date().toLocaleTimeString(),
          side: result.finalDecision.action,
          symbol: 'BTCUSDT',
          quantity: 0.01,
          pnl,
          success: pnl > 0
        };
        
        setTradingState(prev => ({
          ...prev,
          totalTrades: prev.totalTrades + 1,
          winningTrades: pnl > 0 ? prev.winningTrades + 1 : prev.winningTrades,
          totalPnl: prev.totalPnl + pnl,
          recentTrades: [newTrade, ...prev.recentTrades.slice(0, 9)]
        }));
      }
      
    } catch (error) {
      console.error('[Aureon] Quantum cycle error:', error);
    }
  }, [userId, fetchMarketData, tradingState.gasTankBalance]);

  // Start autonomous trading
  const startTrading = useCallback(async () => {
    if (!userId) return;
    
    const initialized = await initializeSystems();
    if (!initialized) {
      toast.error('Failed to initialize quantum systems');
      return;
    }
    
    setTradingState(prev => ({ ...prev, isActive: true }));
    
    // Broadcast trading started
    temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'TRADING_STARTED', { userId });
    
    // Run quantum cycle every 3 seconds
    intervalRef.current = setInterval(runQuantumCycle, 3000);
    
    // Countdown timer
    countdownRef.current = setInterval(() => {
      setNextCheckIn(prev => prev <= 1 ? 3 : prev - 1);
    }, 1000);
    
    // Run immediately
    runQuantumCycle();
    
    toast.success('Autonomous trading activated');
  }, [userId, initializeSystems, runQuantumCycle]);

  // Stop trading
  const stopTrading = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    if (countdownRef.current) {
      clearInterval(countdownRef.current);
      countdownRef.current = null;
    }
    if (busUnsubRef.current) {
      busUnsubRef.current();
      busUnsubRef.current = null;
    }
    if (exchangeUnsubRef.current) {
      exchangeUnsubRef.current();
      exchangeUnsubRef.current = null;
    }
    
    // Unregister from Temporal Ladder
    temporalLadder.unregisterSystem(SYSTEMS.MASTER_EQUATION);
    temporalLadder.unregisterSystem(SYSTEMS.HARMONIC_NEXUS);
    
    setTradingState(prev => ({ ...prev, isActive: false }));
    setSystemStatus({
      masterEquation: false,
      lighthouse: false,
      rainbowBridge: false,
      elephantMemory: false,
      orderRouter: false
    });
    
    toast.info('Trading stopped');
  }, []);

  // Load user session data and AUTO-START on login
  useEffect(() => {
    if (!userId) return;

    const loadSession = async () => {
      const { data, error } = await supabase
        .from('aureon_user_sessions')
        .select('*')
        .eq('user_id', userId)
        .single();

      if (error && error.code === 'PGRST116') {
        // No session exists - create one and auto-start
        console.log('[Aureon] No session found, creating new session...');
        const { error: insertError } = await supabase
          .from('aureon_user_sessions')
          .insert({
            user_id: userId,
            payment_completed: true,
            is_trading_active: true,
            gas_tank_balance: 100,
            trading_mode: 'paper'
          });
        
        if (!insertError) {
          console.log('[Aureon] Session created, auto-starting trading...');
          startTrading();
        }
        return;
      }

      if (data) {
        setQuantumState({
          coherence: Number(data.current_coherence) || 0,
          lambda: Number(data.current_lambda) || 0,
          lighthouseSignal: Number(data.current_lighthouse_signal) || 0,
          dominantNode: data.dominant_node || 'Tiger',
          prismLevel: data.prism_level || 0,
          prismState: data.prism_state || 'FORMING',
          substrate: 0,
          observer: 0,
          echo: 0
        });
        
        setTradingState({
          isActive: data.is_trading_active || false,
          totalEquity: Number(data.total_equity_usdt) || 0,
          availableBalance: Number(data.available_balance_usdt) || 0,
          totalTrades: data.total_trades || 0,
          winningTrades: data.winning_trades || 0,
          totalPnl: Number(data.total_pnl_usdt) || 0,
          gasTankBalance: Number(data.gas_tank_balance) || 100,
          recentTrades: (data.recent_trades as any[]) || []
        });

        // AUTO-START: If payment completed, start trading automatically
        if (data.payment_completed && !data.is_trading_active) {
          console.log('[Aureon] Payment verified, auto-starting trading...');
          startTrading();
        } else if (data.is_trading_active) {
          // Resume if was already active
          startTrading();
        }
      }
    };

    loadSession();

    // Subscribe to realtime updates
    const channel = supabase
      .channel(`aureon_session_${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'aureon_user_sessions',
          filter: `user_id=eq.${userId}`
        },
        (payload) => {
          const data = payload.new as any;
          setTradingState(prev => ({
            ...prev,
            totalEquity: Number(data.total_equity_usdt) || prev.totalEquity,
            gasTankBalance: Number(data.gas_tank_balance) || prev.gasTankBalance,
          }));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
      stopTrading();
    };
  }, [userId]);

  return {
    quantumState,
    tradingState,
    systemStatus,
    busState,
    exchangeState,
    prismState,
    marketData,
    lastSignal,
    nextCheckIn,
    lastDecision,
    startTrading,
    stopTrading
  };
}
