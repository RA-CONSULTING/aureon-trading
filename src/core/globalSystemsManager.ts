/**
 * Global Systems Manager - The One Big Script
 * 
 * This singleton initializes ONCE at app load and NEVER restarts between tab navigation.
 * All quantum systems, orchestration loops, and state management run here continuously.
 */

import { unifiedBus, type BusSnapshot, type SignalType } from './unifiedBus';
import { temporalLadder, SYSTEMS, type TemporalLadderState } from './temporalLadder';
import { unifiedOrchestrator, type OrchestrationResult } from './unifiedOrchestrator';
import { fullEcosystemConnector, type FullEcosystemState } from './fullEcosystemConnector';
import { multiExchangeClient, type MultiExchangeState } from './multiExchangeClient';
import { ecosystemConnector, type EcosystemState } from './ecosystemConnector';
import { backgroundServices } from './backgroundServices';
import { thePrism, type PrismOutput } from './thePrism';
import { supabase } from '@/integrations/supabase/client';

export interface GlobalState {
  // Auth state
  userId: string | null;
  userEmail: string | null;
  isAuthenticated: boolean;
  
  // Quantum state
  coherence: number;
  lambda: number;
  lighthouseSignal: number;
  dominantNode: string;
  prismLevel: number;
  prismState: string;
  substrate: number;
  observer: number;
  echo: number;
  
  // Prism output
  prismOutput: PrismOutput | null;
  
  // Trading state
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
  
  // Market data
  marketData: {
    price: number;
    volume: number;
    volatility: number;
    momentum: number;
    spread: number;
    timestamp: number;
  };
  
  // System status
  systemStatus: {
    masterEquation: boolean;
    lighthouse: boolean;
    rainbowBridge: boolean;
    elephantMemory: boolean;
    orderRouter: boolean;
  };
  
  // Bus state
  busSnapshot: BusSnapshot | null;
  consensusSignal: SignalType;
  consensusConfidence: number;
  
  // Exchange state
  exchangeState: MultiExchangeState | null;
  
  // Orchestration
  lastDecision: OrchestrationResult | null;
  lastSignal: string | null;
  nextCheckIn: number;
  
  // Health
  ecosystemHealth: 'connected' | 'stale' | 'disconnected';
  lastDataReceived: number | null;
  
  // Manager state
  isInitialized: boolean;
  isRunning: boolean;
}

const initialState: GlobalState = {
  userId: null,
  userEmail: null,
  isAuthenticated: false,
  
  coherence: 0,
  lambda: 0,
  lighthouseSignal: 0,
  dominantNode: 'Tiger',
  prismLevel: 0,
  prismState: 'FORMING',
  substrate: 0,
  observer: 0,
  echo: 0,
  
  prismOutput: null,
  
  isActive: false,
  totalEquity: 0,
  availableBalance: 0,
  totalTrades: 0,
  winningTrades: 0,
  totalPnl: 0,
  gasTankBalance: 100,
  recentTrades: [],
  
  marketData: {
    price: 0,
    volume: 0,
    volatility: 0,
    momentum: 0,
    spread: 0,
    timestamp: 0,
  },
  
  systemStatus: {
    masterEquation: false,
    lighthouse: false,
    rainbowBridge: false,
    elephantMemory: false,
    orderRouter: false,
  },
  
  busSnapshot: null,
  consensusSignal: 'NEUTRAL',
  consensusConfidence: 0,
  
  exchangeState: null,
  
  lastDecision: null,
  lastSignal: null,
  nextCheckIn: 3,
  
  ecosystemHealth: 'disconnected',
  lastDataReceived: null,
  
  isInitialized: false,
  isRunning: false,
};

type StateListener = (state: GlobalState) => void;

class GlobalSystemsManager {
  private static instance: GlobalSystemsManager | null = null;
  
  private state: GlobalState = { ...initialState };
  private listeners: Set<StateListener> = new Set();
  
  // Intervals
  private orchestrationInterval: NodeJS.Timeout | null = null;
  private countdownInterval: NodeJS.Timeout | null = null;
  private healthCheckInterval: NodeJS.Timeout | null = null;
  
  // Subscriptions
  private busUnsubscribe: (() => void) | null = null;
  private exchangeUnsubscribe: (() => void) | null = null;
  private ecosystemUnsubscribe: (() => void) | null = null;
  private authUnsubscribe: (() => void) | null = null;
  
  private constructor() {
    console.log('🌌 GlobalSystemsManager: Singleton created');
  }
  
  static getInstance(): GlobalSystemsManager {
    if (!GlobalSystemsManager.instance) {
      GlobalSystemsManager.instance = new GlobalSystemsManager();
    }
    return GlobalSystemsManager.instance;
  }
  
  /**
   * Initialize the global systems manager - called ONCE at app startup
   * Wrapped with master timeout to prevent hanging
   */
  async initialize(): Promise<void> {
    if (this.state.isInitialized) {
      console.log('🌌 GlobalSystemsManager: Already initialized, skipping');
      return;
    }
    
    try {
      await Promise.race([
        this.doInitialize(),
        new Promise<void>((_, reject) => 
          setTimeout(() => reject(new Error('Master init timeout')), 10000)
        )
      ]);
    } catch (error) {
      console.error('🚨 Initialization timeout/failure - forcing ready state:', error);
      this.updateState({ isInitialized: true });
    }
  }
  
  /**
   * Actual initialization logic
   */
  private async doInitialize(): Promise<void> {
    console.log('🌌 GlobalSystemsManager: Initializing...');
    
    // 1. Setup auth listener (this persists across the entire app lifecycle)
    this.setupAuthListener();
    
    // 2. Check current auth state with timeout
    try {
      const sessionResult = await Promise.race([
        supabase.auth.getSession(),
        new Promise<never>((_, reject) => 
          setTimeout(() => reject(new Error('Auth session check timeout')), 3000)
        )
      ]);
      
      if (sessionResult.data?.session) {
        this.updateState({
          userId: sessionResult.data.session.user.id,
          userEmail: sessionResult.data.session.user.email || null,
          isAuthenticated: true,
        });
      }
    } catch (error) {
      console.warn('⚠️ Auth session check failed/timed out, continuing unauthenticated:', error);
      // Clear any stale session data
      try {
        await supabase.auth.signOut();
      } catch (e) {
        // Ignore signout errors
      }
    }
    
    // 3. Start background services
    backgroundServices.start();
    
    // 4. Setup bus subscription
    this.busUnsubscribe = unifiedBus.subscribe((snapshot) => {
      this.updateState({
        busSnapshot: snapshot,
        consensusSignal: snapshot.consensusSignal,
        consensusConfidence: snapshot.consensusConfidence,
      });
    });
    
    // 5. Setup ecosystem health monitoring
    this.ecosystemUnsubscribe = ecosystemConnector.subscribe(() => {
      this.updateState({
        lastDataReceived: Date.now(),
        ecosystemHealth: 'connected',
      });
    });
    
    this.healthCheckInterval = setInterval(() => {
      if (this.state.lastDataReceived) {
        const timeSince = Date.now() - this.state.lastDataReceived;
        if (timeSince > 30000) {
          this.updateState({ ecosystemHealth: 'disconnected' });
        } else if (timeSince > 10000) {
          this.updateState({ ecosystemHealth: 'stale' });
        } else {
          this.updateState({ ecosystemHealth: 'connected' });
        }
      }
    }, 2000);
    
    // 6. Initialize full ecosystem connector with timeout for graceful degradation
    try {
      await Promise.race([
        fullEcosystemConnector.initialize(),
        new Promise((_, reject) => 
          setTimeout(() => reject(new Error('Ecosystem init timeout')), 5000)
        )
      ]);
      console.log('✅ Full ecosystem initialized successfully');
    } catch (error) {
      console.warn('⚠️ Ecosystem initialization timed out or failed, continuing with degraded mode:', error);
      // Continue anyway - dashboard should still load
    }
    
    this.updateState({ isInitialized: true });
    console.log('✅ GlobalSystemsManager: Initialization complete (may be in degraded mode)');
    
    // 7. Auto-start trading if authenticated
    if (this.state.isAuthenticated && this.state.userId) {
      await this.loadUserSession();
    }
  }
  
  /**
   * Setup persistent auth listener
   */
  private setupAuthListener(): void {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      // Handle token refresh failures - clear stale session
      if (event === 'TOKEN_REFRESHED' && !session) {
        console.warn('⚠️ Token refresh failed, clearing stale session');
        supabase.auth.signOut().catch(() => {});
        return;
      }
      
      if (session) {
        const wasAuthenticated = this.state.isAuthenticated;
        this.updateState({
          userId: session.user.id,
          userEmail: session.user.email || null,
          isAuthenticated: true,
        });
        
        // If just logged in, load session and auto-start (deferred to avoid deadlock)
        if (!wasAuthenticated) {
          setTimeout(() => {
            this.loadUserSession();
          }, 0);
        }
      } else {
        // Logged out - stop trading but keep manager alive
        this.stopTrading();
        this.updateState({
          userId: null,
          userEmail: null,
          isAuthenticated: false,
        });
      }
    });
    
    this.authUnsubscribe = () => subscription.unsubscribe();
  }
  
  /**
   * Load user session from database
   */
  private async loadUserSession(): Promise<void> {
    if (!this.state.userId) return;
    
    const { data, error } = await supabase
      .from('aureon_user_sessions')
      .select('*')
      .eq('user_id', this.state.userId)
      .single();
    
    if (error && error.code === 'PGRST116') {
      // No session - create one
      console.log('[GlobalSystems] Creating new session...');
      await supabase
        .from('aureon_user_sessions')
        .insert({
          user_id: this.state.userId,
          payment_completed: true,
          is_trading_active: true,
          gas_tank_balance: 100,
          trading_mode: 'paper'
        });
      
      this.startTrading();
      return;
    }
    
    if (data) {
      this.updateState({
        coherence: Number(data.current_coherence) || 0,
        lambda: Number(data.current_lambda) || 0,
        lighthouseSignal: Number(data.current_lighthouse_signal) || 0,
        dominantNode: data.dominant_node || 'Tiger',
        prismLevel: data.prism_level || 0,
        prismState: data.prism_state || 'FORMING',
        totalEquity: Number(data.total_equity_usdt) || 0,
        availableBalance: Number(data.available_balance_usdt) || 0,
        totalTrades: data.total_trades || 0,
        winningTrades: data.winning_trades || 0,
        totalPnl: Number(data.total_pnl_usdt) || 0,
        gasTankBalance: Number(data.gas_tank_balance) || 100,
        recentTrades: (data.recent_trades as any[]) || [],
      });
      
      // Auto-start if payment completed
      if (data.payment_completed && !this.state.isRunning) {
        this.startTrading();
      }
    }
  }
  
  /**
   * Start autonomous trading loop
   */
  startTrading(): void {
    if (this.state.isRunning) {
      console.log('[GlobalSystems] Already running');
      return;
    }
    
    console.log('🚀 GlobalSystemsManager: Starting autonomous trading...');
    
    // Initialize exchange client
    multiExchangeClient.initialize().catch(console.error);
    
    // Subscribe to exchange updates
    this.exchangeUnsubscribe = multiExchangeClient.subscribe((state: MultiExchangeState) => {
      this.updateState({ exchangeState: state });
    });
    
    // Register systems with Temporal Ladder
    temporalLadder.registerSystem(SYSTEMS.MASTER_EQUATION);
    temporalLadder.registerSystem(SYSTEMS.HARMONIC_NEXUS);
    temporalLadder.registerSystem(SYSTEMS.QUANTUM_QUACKERS);
    
    this.updateState({
      isActive: true,
      isRunning: true,
      systemStatus: {
        masterEquation: true,
        lighthouse: true,
        rainbowBridge: true,
        elephantMemory: true,
        orderRouter: true,
      },
    });
    
    // Start 3-second orchestration loop
    this.orchestrationInterval = setInterval(() => this.runQuantumCycle(), 3000);
    
    // Countdown timer
    this.countdownInterval = setInterval(() => {
      this.updateState({
        nextCheckIn: this.state.nextCheckIn <= 1 ? 3 : this.state.nextCheckIn - 1,
      });
    }, 1000);
    
    // Run immediately
    this.runQuantumCycle();
    
    console.log('✅ GlobalSystemsManager: Autonomous trading active');
  }
  
  /**
   * Stop trading loop
   */
  stopTrading(): void {
    console.log('⏹️ GlobalSystemsManager: Stopping trading...');
    
    if (this.orchestrationInterval) {
      clearInterval(this.orchestrationInterval);
      this.orchestrationInterval = null;
    }
    
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
    
    if (this.exchangeUnsubscribe) {
      this.exchangeUnsubscribe();
      this.exchangeUnsubscribe = null;
    }
    
    // Unregister from Temporal Ladder
    temporalLadder.unregisterSystem(SYSTEMS.MASTER_EQUATION);
    temporalLadder.unregisterSystem(SYSTEMS.HARMONIC_NEXUS);
    
    this.updateState({
      isActive: false,
      isRunning: false,
      systemStatus: {
        masterEquation: false,
        lighthouse: false,
        rainbowBridge: false,
        elephantMemory: false,
        orderRouter: false,
      },
    });
    
    console.log('✅ GlobalSystemsManager: Trading stopped');
  }
  
  /**
   * Run a single quantum computation cycle
   */
  private async runQuantumCycle(): Promise<void> {
    if (!this.state.userId) return;
    
    try {
      // Fetch market data
      const marketData = await this.fetchMarketData('BTCUSDT');
      this.updateState({ marketData });
      
      // Run unified orchestrator
      const result = await unifiedOrchestrator.runCycle(marketData, 'BTCUSDT');
      
      // Update state from result
      if (result.lambdaState) {
        // Run Prism transformation
        const prismOutput = thePrism.transform({
          lambda: result.lambdaState.lambda,
          coherence: result.lambdaState.coherence,
          substrate: result.lambdaState.substrate,
          observer: result.lambdaState.observer,
          echo: result.lambdaState.echo,
          volatility: marketData.volatility,
          momentum: marketData.momentum,
          baseFrequency: result.rainbowState?.frequency || 396,
        });
        
        this.updateState({
          coherence: result.lambdaState.coherence,
          lambda: result.lambdaState.lambda,
          lighthouseSignal: result.lighthouseState?.L || 0,
          dominantNode: result.lambdaState.dominantNode,
          prismLevel: prismOutput.level,
          prismState: prismOutput.state,
          substrate: result.lambdaState.substrate,
          observer: result.lambdaState.observer,
          echo: result.lambdaState.echo,
          prismOutput,
          lastDecision: result,
        });
        
        // Heartbeats to Temporal Ladder
        temporalLadder.heartbeat(SYSTEMS.MASTER_EQUATION, result.lambdaState.coherence);
        temporalLadder.heartbeat(SYSTEMS.HARMONIC_NEXUS, result.busSnapshot.consensusConfidence);
        
        // Persist to database
        await supabase
          .from('aureon_user_sessions')
          .update({
            current_coherence: result.lambdaState.coherence,
            current_lambda: result.lambdaState.lambda,
            current_lighthouse_signal: result.lighthouseState?.L || 0,
            dominant_node: result.lambdaState.dominantNode,
            prism_level: prismOutput.level,
            prism_state: prismOutput.state,
            last_quantum_update_at: new Date().toISOString()
          })
          .eq('user_id', this.state.userId);
      }
      
      // Handle trade signals
      if (result.finalDecision.action !== 'HOLD' && this.state.gasTankBalance > 0) {
        const signal = `${result.finalDecision.action} BTCUSDT @ $${marketData.price.toFixed(2)}`;
        
        temporalLadder.broadcast(SYSTEMS.QUANTUM_QUACKERS, 'TRADE_SIGNAL', {
          action: result.finalDecision.action,
          symbol: 'BTCUSDT',
          confidence: result.finalDecision.confidence,
          reason: result.finalDecision.reason
        });
        
        // Execute trade via UnifiedOrchestrator (not simulation)
        // The orchestrator handles paper vs live mode internally via config.dryRun
        console.log(`[GlobalSystems] Trade signal: ${result.finalDecision.action} BTCUSDT`);
        
        // Record the trade attempt - actual execution happens in orchestrator
        const newTrade = {
          time: new Date().toLocaleTimeString(),
          side: result.finalDecision.action,
          symbol: 'BTCUSDT',
          quantity: 0.01,
          pnl: 0, // Real P&L will be calculated on trade close
          success: result.tradeExecuted,
          pending: !result.tradeExecuted
        };
        
        this.updateState({
          lastSignal: signal,
          totalTrades: result.tradeExecuted ? this.state.totalTrades + 1 : this.state.totalTrades,
          recentTrades: [newTrade, ...this.state.recentTrades.slice(0, 9)],
        });
      }
      
    } catch (error) {
      console.error('[GlobalSystems] Quantum cycle error:', error);
    }
  }
  
  /**
   * Fetch market data from edge function
   * THROWS if live data is unavailable - no simulation fallback
   */
  private async fetchMarketData(symbol: string = 'BTCUSDT'): Promise<GlobalState['marketData']> {
    const { data, error } = await supabase.functions.invoke('get-user-market-data', {
      body: { symbol }
    });
    
    if (error) {
      console.error('[GlobalSystems] Failed to fetch live market data:', error);
      throw new Error(`Live market data unavailable: ${error.message}`);
    }
    
    if (!data || !data.price || data.price <= 0) {
      throw new Error('Invalid market data received - price must be positive');
    }
    
    return data;
  }
  
  /**
   * Update state and notify listeners
   */
  private updateState(partial: Partial<GlobalState>): void {
    this.state = { ...this.state, ...partial };
    this.notifyListeners();
  }
  
  /**
   * Notify all subscribers
   */
  private notifyListeners(): void {
    this.listeners.forEach(listener => {
      try {
        listener(this.state);
      } catch (error) {
        console.error('[GlobalSystems] Listener error:', error);
      }
    });
  }
  
  /**
   * Subscribe to state changes
   */
  subscribe(listener: StateListener): () => void {
    this.listeners.add(listener);
    // Immediately call with current state
    listener(this.state);
    
    return () => {
      this.listeners.delete(listener);
    };
  }
  
  /**
   * Get current state (snapshot)
   */
  getState(): GlobalState {
    return { ...this.state };
  }
  
  /**
   * Cleanup (only call on app unmount, which basically never happens in SPA)
   */
  destroy(): void {
    console.log('🌌 GlobalSystemsManager: Destroying...');
    
    this.stopTrading();
    
    if (this.healthCheckInterval) {
      clearInterval(this.healthCheckInterval);
    }
    
    if (this.busUnsubscribe) this.busUnsubscribe();
    if (this.ecosystemUnsubscribe) this.ecosystemUnsubscribe();
    if (this.authUnsubscribe) this.authUnsubscribe();
    
    backgroundServices.stop();
    
    this.listeners.clear();
    GlobalSystemsManager.instance = null;
  }
}

// Export singleton instance
export const globalSystemsManager = GlobalSystemsManager.getInstance();
