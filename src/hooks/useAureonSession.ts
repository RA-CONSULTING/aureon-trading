import { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { MasterEquation } from '@/core/masterEquation';
import { LighthouseConsensus } from '@/core/lighthouseConsensus';
import { RainbowBridge } from '@/core/rainbowBridge';
import { toast } from 'sonner';

export interface QuantumState {
  coherence: number;
  lambda: number;
  lighthouseSignal: number;
  dominantNode: string;
  prismLevel: number;
  prismState: string;
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

export function useAureonSession(userId: string | null) {
  const [quantumState, setQuantumState] = useState<QuantumState>({
    coherence: 0,
    lambda: 0,
    lighthouseSignal: 0,
    dominantNode: 'Tiger',
    prismLevel: 0,
    prismState: 'FORMING'
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
  
  const [lastSignal, setLastSignal] = useState<string | null>(null);
  const [nextCheckIn, setNextCheckIn] = useState(3);
  
  const masterEquationRef = useRef<MasterEquation | null>(null);
  const lighthouseRef = useRef<LighthouseConsensus | null>(null);
  const rainbowBridgeRef = useRef<RainbowBridge | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const countdownRef = useRef<NodeJS.Timeout | null>(null);

  // Initialize quantum systems
  const initializeSystems = useCallback(() => {
    try {
      masterEquationRef.current = new MasterEquation();
      lighthouseRef.current = new LighthouseConsensus();
      rainbowBridgeRef.current = new RainbowBridge();
      
      setSystemStatus({
        masterEquation: true,
        lighthouse: true,
        rainbowBridge: true,
        elephantMemory: true,
        orderRouter: true
      });
      
      return true;
    } catch (error) {
      console.error('[Aureon] Failed to initialize systems:', error);
      return false;
    }
  }, []);

  // Run quantum computation cycle
  const runQuantumCycle = useCallback(async () => {
    if (!userId || !masterEquationRef.current || !lighthouseRef.current || !rainbowBridgeRef.current) {
      return;
    }

    try {
      // Fetch market data
      const marketData = {
        price: 67000 + (Math.random() - 0.5) * 1000,
        volume: 1000000 + Math.random() * 500000,
        volatility: 0.02 + Math.random() * 0.03,
        momentum: (Math.random() - 0.5) * 0.1,
        spread: 0.0001 + Math.random() * 0.0005,
        timestamp: Date.now()
      };

      // Compute Master Equation (async)
      const fieldState = await masterEquationRef.current.step(marketData);
      
      // Run Lighthouse Consensus
      const lighthouseResult = lighthouseRef.current.validate(
        fieldState.lambda,
        fieldState.coherence,
        fieldState.substrate,
        fieldState.observer,
        fieldState.echo,
        0.5, // Geff
        false // ftcpDetected
      );
      
      // Map to Rainbow Bridge
      const bridgeState = rainbowBridgeRef.current.map(fieldState.lambda, fieldState.coherence);
      
      // Update quantum state
      const newQuantumState: QuantumState = {
        coherence: fieldState.coherence,
        lambda: fieldState.lambda,
        lighthouseSignal: lighthouseResult.L,
        dominantNode: fieldState.dominantNode,
        prismLevel: Math.floor(fieldState.coherence * 5),
        prismState: fieldState.coherence > 0.9 ? 'MANIFEST' : fieldState.coherence > 0.7 ? 'CONVERGING' : 'FORMING'
      };
      
      setQuantumState(newQuantumState);

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

      // Check if we should trade (coherence > 0.70 for demo)
      if (newQuantumState.coherence > 0.70 && lighthouseResult.isLHE && tradingState.gasTankBalance > 0) {
        const signal = lighthouseResult.L > 0 ? 'BUY' : 'SELL';
        setLastSignal(`${signal} BTCUSDT @ $${marketData.price.toFixed(2)}`);
        
        // Simulate trade execution for paper trading
        const pnl = (Math.random() - 0.3) * 50; // Slight positive bias
        const newTrade = {
          time: new Date().toLocaleTimeString(),
          side: signal,
          symbol: 'BTCUSDT',
          quantity: 0.01,
          pnl: pnl,
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
  }, [userId, tradingState.gasTankBalance]);

  // Start autonomous trading
  const startTrading = useCallback(() => {
    if (!userId) return;
    
    const initialized = initializeSystems();
    if (!initialized) {
      toast.error('Failed to initialize quantum systems');
      return;
    }
    
    setTradingState(prev => ({ ...prev, isActive: true }));
    
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

  // Load user session data
  useEffect(() => {
    if (!userId) return;

    const loadSession = async () => {
      const { data } = await supabase
        .from('aureon_user_sessions')
        .select('*')
        .eq('user_id', userId)
        .single();

      if (data) {
        setQuantumState({
          coherence: Number(data.current_coherence) || 0,
          lambda: Number(data.current_lambda) || 0,
          lighthouseSignal: Number(data.current_lighthouse_signal) || 0,
          dominantNode: data.dominant_node || 'Tiger',
          prismLevel: data.prism_level || 0,
          prismState: data.prism_state || 'FORMING'
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

        // Auto-start if was active
        if (data.is_trading_active) {
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
    lastSignal,
    nextCheckIn,
    startTrading,
    stopTrading
  };
}