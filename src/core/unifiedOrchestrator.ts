// UnifiedOrchestrator - Central coordinator for all systems
// Runs the complete quantum cycle and manages consensus-based trading

import { unifiedBus, type BusSnapshot, type SignalType } from './unifiedBus';
import { elephantMemory } from './elephantMemory';
import { MasterEquation, type LambdaState } from './masterEquation';
import { LighthouseConsensus, type LighthouseState } from './lighthouseConsensus';
import { RainbowBridge, type RainbowState } from './rainbowBridge';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { ecosystemConnector, type EcosystemState } from './ecosystemConnector';
import { thePrism, type PrismOutput } from './thePrism';
import type { MarketSnapshot } from './aurisNodes';
import { attuneToAkashicFrequency, calculateAkashicBoost } from './akashicFrequencyMapper';
import { fullEcosystemConnector } from './fullEcosystemConnector';
import { multiExchangeClient } from './multiExchangeClient';
import { smartOrderRouter, type RoutingDecision } from './smartOrderRouter';
import { supabase } from '@/integrations/supabase/client';

export interface TradeExecutionResult {
  success: boolean;
  orderId?: string;
  executedPrice?: number;
  quantity?: number;
  error?: string;
  exchange?: string;
}

export interface OrchestrationResult {
  timestamp: number;
  busSnapshot: BusSnapshot;
  lambdaState: LambdaState | null;
  lighthouseState: LighthouseState | null;
  rainbowState: RainbowState | null;
  prismOutput: PrismOutput | null;
  ecosystemState: EcosystemState | null;
  routingDecision: RoutingDecision | null;
  positionSizing: {
    positionSizeUsd: number;
    availableBalance: number;
    riskAmount: number;
  } | null;
  finalDecision: {
    action: 'BUY' | 'SELL' | 'HOLD';
    symbol: string;
    confidence: number;
    reason: string;
    recommendedExchange?: string;
    positionSizeUsd?: number;
  };
  tradeExecuted: boolean;
}

export interface OrchestratorConfig {
  minCoherence: number;
  minConfidence: number;
  requireLHE: boolean;
  dryRun: boolean;
}

const DEFAULT_CONFIG: OrchestratorConfig = {
  minCoherence: 0.70,
  minConfidence: 0.50,
  requireLHE: false,
  dryRun: true,
};

export class UnifiedOrchestrator {
  private masterEquation: MasterEquation;
  private lighthouse: LighthouseConsensus;
  private rainbowBridge: RainbowBridge;
  private config: OrchestratorConfig;
  private isRunning: boolean = false;
  private currentSymbol: string = 'BTCUSDT';
  
  constructor(config: Partial<OrchestratorConfig> = {}) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.masterEquation = new MasterEquation();
    this.lighthouse = new LighthouseConsensus();
    this.rainbowBridge = new RainbowBridge();
    
    // Register with Temporal Ladder
    temporalLadder.registerSystem(SYSTEMS.MASTER_EQUATION);
  }
  
  /**
   * Run a complete orchestration cycle
   */
  async runCycle(marketSnapshot: MarketSnapshot, symbol: string = 'BTCUSDT'): Promise<OrchestrationResult> {
    this.currentSymbol = symbol;
    const timestamp = Date.now();
    
    // Step 1: Publish DataIngestion state
    this.publishDataIngestion(marketSnapshot);
    
    // Step 2: Compute Master Equation Λ(t)
    const lambdaState = await this.masterEquation.step(marketSnapshot);
    this.publishMasterEquation(lambdaState);
    
    // Step 3: Compute Lighthouse consensus
    const lighthouseState = this.lighthouse.validate(
      lambdaState.lambda,
      lambdaState.coherence,
      lambdaState.substrate,
      lambdaState.observer,
      lambdaState.echo,
      lambdaState.coherence * 0.8, // G_eff estimate
      false, // ftcpDetected
      marketSnapshot.volume / 1000000, // volumeSpike normalized
      Math.abs(marketSnapshot.spread) * 10, // spreadExpansion
      Math.abs(marketSnapshot.momentum) // priceAcceleration
    );
    this.publishLighthouse(lighthouseState, lambdaState.coherence);
    
    // Step 4: Compute Rainbow Bridge emotional state
    const rainbowState = this.rainbowBridge.map(lambdaState.lambda, lambdaState.coherence);
    this.publishRainbowBridge(rainbowState);
    
    // Step 5: Compute The Prism transformation (Fear → Love)
    const prismOutput = thePrism.transform({
      lambda: lambdaState.lambda,
      coherence: lambdaState.coherence,
      substrate: lambdaState.substrate,
      observer: lambdaState.observer,
      echo: lambdaState.echo,
      volatility: marketSnapshot.volatility,
      momentum: marketSnapshot.momentum,
      baseFrequency: rainbowState.frequency,
    });
    
    // Step 6: Run full Ecosystem cycle (HNC, Omega, QGITA, etc.)
    const akashicAttunement = attuneToAkashicFrequency(7);
    const akashicBoost = calculateAkashicBoost(akashicAttunement, lambdaState.coherence);
    const ecosystemState = ecosystemConnector.runCycle(
      marketSnapshot,
      lambdaState,
      akashicAttunement,
      akashicBoost,
      lighthouseState,
      prismOutput
    );
    
    // Step 6b: Wire fullEcosystemConnector to persist ALL states to database
    fullEcosystemConnector.processMarketData(
      marketSnapshot.price,
      marketSnapshot.volume,
      marketSnapshot.volatility,
      marketSnapshot.momentum,
      lambdaState.lambda,
      lambdaState.coherence,
      lambdaState.substrate,
      lambdaState.observer,
      lambdaState.echo
    ).catch(err => console.warn('[UnifiedOrchestrator] Ecosystem persistence error:', err));
    
    // Step 6c: Publish Prism state to UnifiedBus
    this.publishPrism(prismOutput);
    
    // Step 7: Get multi-exchange state and position sizing
    const exchangeState = multiExchangeClient.getState();
    const positionSizing = multiExchangeClient.calculatePositionSize(0.02, 'USDT');
    
    // Step 8: Get Smart Order Router recommendation
    let routingDecision: RoutingDecision | null = null;
    try {
      routingDecision = await smartOrderRouter.getBestQuote(symbol, 'BUY', positionSizing.positionSizeUsd / marketSnapshot.price);
    } catch (err) {
      console.warn('[UnifiedOrchestrator] Smart routing failed, using default:', err);
    }
    
    // Step 9: Check Elephant Memory for avoidance
    const avoidance = elephantMemory.shouldAvoid(symbol);
    
    // Step 10: Get bus consensus
    const busSnapshot = unifiedBus.snapshot();
    const consensus = unifiedBus.checkConsensus();
    
    // Step 11: Make final decision with 6D probability integration + exchange data
    const finalDecision = this.makeFinalDecision(
      consensus,
      lambdaState,
      lighthouseState,
      avoidance,
      symbol,
      ecosystemState,
      routingDecision,
      positionSizing
    );
    
    // Step 12: Execute trade if conditions met
    let tradeExecuted = false;
    let tradeResult: TradeExecutionResult | null = null;
    if (finalDecision.action !== 'HOLD' && !this.config.dryRun) {
      tradeResult = await this.executeTrade(
        finalDecision, 
        symbol, 
        marketSnapshot, 
        lambdaState, 
        lighthouseState, 
        prismOutput
      );
      tradeExecuted = tradeResult.success;
      
      if (!tradeResult.success) {
        console.warn('[UnifiedOrchestrator] Trade failed:', tradeResult.error);
      }
    }
    
    // Send heartbeat to Temporal Ladder
    temporalLadder.heartbeat(SYSTEMS.MASTER_EQUATION, lambdaState.coherence);
    
    return {
      timestamp,
      busSnapshot,
      lambdaState,
      lighthouseState,
      rainbowState,
      prismOutput,
      ecosystemState,
      routingDecision,
      positionSizing,
      finalDecision,
      tradeExecuted,
    };
  }
  
  /**
   * Publish DataIngestion state to bus
   */
  private publishDataIngestion(snapshot: MarketSnapshot): void {
    const hasData = snapshot.price > 0 && snapshot.volume > 0;
    
    unifiedBus.publish({
      systemName: 'DataIngestion',
      timestamp: Date.now(),
      ready: hasData,
      coherence: hasData ? 0.9 : 0,
      confidence: hasData ? 0.95 : 0,
      signal: 'NEUTRAL',
      data: {
        price: snapshot.price,
        volume: snapshot.volume,
        volatility: snapshot.volatility,
        momentum: snapshot.momentum,
      },
    });
  }
  
  /**
   * Publish Master Equation state to bus
   */
  private publishMasterEquation(state: LambdaState): void {
    // Determine signal from Lambda
    let signal: SignalType = 'NEUTRAL';
    if (state.lambda > 0.5 && state.coherence > this.config.minCoherence) {
      signal = 'BUY';
    } else if (state.lambda < -0.5 && state.coherence > this.config.minCoherence) {
      signal = 'SELL';
    }
    
    unifiedBus.publish({
      systemName: 'MasterEquation',
      timestamp: Date.now(),
      ready: true,
      coherence: state.coherence,
      confidence: Math.min(Math.abs(state.lambda), 1),
      signal,
      data: {
        lambda: state.lambda,
        substrate: state.substrate,
        observer: state.observer,
        echo: state.echo,
        dominantNode: state.dominantNode,
      },
    });
  }
  
  /**
   * Publish Lighthouse state to bus
   */
  private publishLighthouse(state: LighthouseState, coherence: number): void {
    let signal: SignalType = 'NEUTRAL';
    if (state.isLHE) {
      signal = state.L > 0.5 ? 'BUY' : 'SELL';
    }
    
    unifiedBus.publish({
      systemName: 'Lighthouse',
      timestamp: Date.now(),
      ready: true,
      coherence,
      confidence: state.confidence,
      signal,
      data: {
        L: state.L,
        isLHE: state.isLHE,
        threshold: state.threshold,
        metrics: state.metrics,
      },
    });
  }
  
  /**
   * Publish Rainbow Bridge state to bus
   */
  private publishRainbowBridge(state: RainbowState): void {
    // Map phase to signal
    let signal: SignalType = 'NEUTRAL';
    if (state.phase === 'LOVE' || state.phase === 'AWE' || state.phase === 'UNITY') {
      signal = 'BUY';
    } else if (state.phase === 'FEAR') {
      signal = 'SELL';
    }
    
    unifiedBus.publish({
      systemName: 'RainbowBridge',
      timestamp: Date.now(),
      ready: true,
      coherence: state.intensity,
      confidence: state.intensity,
      signal,
      data: {
        frequency: state.frequency,
        phase: state.phase,
        intensity: state.intensity,
      },
    });
  }
  
  /**
   * Publish Prism state to bus
   */
  private publishPrism(output: PrismOutput): void {
    let signal: SignalType = 'NEUTRAL';
    if (output.state === 'MANIFEST' && output.isLoveLocked) {
      signal = 'BUY';
    } else if (output.state === 'FORMING' && output.resonance < 0.3) {
      signal = 'SELL';
    }
    
    unifiedBus.publish({
      systemName: 'Prism',
      timestamp: Date.now(),
      ready: true,
      coherence: output.resonance,
      confidence: output.harmonicPurity,
      signal,
      data: {
        level: output.level,
        frequency: output.frequency,
        state: output.state,
        resonance: output.resonance,
        isLoveLocked: output.isLoveLocked,
        harmonicPurity: output.harmonicPurity,
        layers: output.layers,
      },
    });
  }
  
  /**
   * Make final trading decision based on all inputs including 6D Harmonic probability + exchange routing
   */
  private makeFinalDecision(
    consensus: { ready: boolean; signal: SignalType; confidence: number },
    lambdaState: LambdaState,
    lighthouseState: LighthouseState,
    avoidance: { avoid: boolean; reason: string | null },
    symbol: string,
    ecosystemState: EcosystemState | null,
    routingDecision: RoutingDecision | null,
    positionSizing: { positionSizeUsd: number; availableBalance: number; riskAmount: number } | null
  ): { action: 'BUY' | 'SELL' | 'HOLD'; symbol: string; confidence: number; reason: string; harmonic6D?: { score: number; waveState: string; harmonicLock: boolean }; recommendedExchange?: string; positionSizeUsd?: number } {
    // Extract 6D probability fusion from ecosystem state
    const probabilityFusion = ecosystemState?.probabilityFusion ?? null;
    const waveState = probabilityFusion?.waveState ?? 'RESONANT';
    const harmonicLock = probabilityFusion?.harmonicLock ?? false;
    const harmonic6DScore = probabilityFusion ? (probabilityFusion.fusedProbability - 0.5) * 2 : 0;
    const harmonic6DData = { score: harmonic6DScore, waveState, harmonicLock };

    // Check avoidance first
    if (avoidance.avoid) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: `Elephant Memory: ${avoidance.reason}`,
        harmonic6D: harmonic6DData,
      };
    }
    
    // Check if we have sufficient balance for trading
    if (positionSizing && positionSizing.positionSizeUsd < 10) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: `Insufficient balance: $${positionSizing.positionSizeUsd.toFixed(2)} (min $10)`,
        harmonic6D: harmonic6DData,
      };
    }
    
    // Check if consensus is ready
    if (!consensus.ready) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: 'Systems not ready for consensus',
        harmonic6D: harmonic6DData,
      };
    }
    
    // Dynamic coherence threshold based on 6D wave state
    let effectiveMinCoherence = this.config.minCoherence;
    if (waveState === 'CRYSTALLINE') {
      // Lower threshold when 6D is highly aligned
      effectiveMinCoherence *= 0.85;
    } else if (waveState === 'CHAOTIC') {
      // Higher threshold in chaotic conditions
      effectiveMinCoherence *= 1.2;
    }
    
    // Check minimum coherence with dynamic threshold
    if (lambdaState.coherence < effectiveMinCoherence) {
      return {
        action: 'HOLD',
        symbol,
        confidence: lambdaState.coherence,
        reason: `Coherence ${(lambdaState.coherence * 100).toFixed(1)}% below ${waveState} threshold`,
        harmonic6D: harmonic6DData,
      };
    }
    
    // Apply harmonic lock confidence boost
    let effectiveConfidence = consensus.confidence;
    if (harmonicLock) {
      effectiveConfidence = Math.min(1, effectiveConfidence + 0.1);
    }
    
    // Check minimum confidence
    if (effectiveConfidence < this.config.minConfidence) {
      return {
        action: 'HOLD',
        symbol,
        confidence: effectiveConfidence,
        reason: `Confidence ${(effectiveConfidence * 100).toFixed(1)}% below threshold`,
        harmonic6D: harmonic6DData,
      };
    }
    
    // Check LHE requirement
    if (this.config.requireLHE && !lighthouseState.isLHE) {
      return {
        action: 'HOLD',
        symbol,
        confidence: effectiveConfidence,
        reason: 'Lighthouse Event not detected',
        harmonic6D: harmonic6DData,
      };
    }
    
    // Return consensus signal
    if (consensus.signal === 'NEUTRAL') {
      return {
        action: 'HOLD',
        symbol,
        confidence: effectiveConfidence,
        reason: 'No clear signal from consensus',
        harmonic6D: harmonic6DData,
      };
    }
    
    // Build reason with 6D context + exchange routing
    const lockStatus = harmonicLock ? ' [528Hz LOCKED]' : '';
    const exchangeInfo = routingDecision ? ` | Route: ${routingDecision.recommendedExchange}` : '';
    const positionInfo = positionSizing ? ` | Size: $${positionSizing.positionSizeUsd.toFixed(2)}` : '';
    const reason = `Consensus: ${consensus.signal} at ${(effectiveConfidence * 100).toFixed(1)}% | 6D: ${waveState}${lockStatus}${exchangeInfo}${positionInfo}`;
    
    return {
      action: consensus.signal,
      symbol,
      confidence: effectiveConfidence,
      reason,
      harmonic6D: harmonic6DData,
      recommendedExchange: routingDecision?.recommendedExchange,
      positionSizeUsd: positionSizing?.positionSizeUsd,
    };
  }
  
  /**
   * Execute a trade with smart order routing via edge function
   */
  private async executeTrade(
    decision: { action: 'BUY' | 'SELL' | 'HOLD'; symbol: string; confidence: number; recommendedExchange?: string; positionSizeUsd?: number },
    symbol: string,
    marketSnapshot?: MarketSnapshot,
    lambdaState?: LambdaState | null,
    lighthouseState?: LighthouseState | null,
    prismOutput?: PrismOutput | null
  ): Promise<TradeExecutionResult> {
    const exchange = decision.recommendedExchange || 'binance';
    const positionSize = decision.positionSizeUsd || 100;
    
    console.log(`[UnifiedOrchestrator] Executing ${decision.action} on ${symbol} via ${exchange} | Size: $${positionSize.toFixed(2)}`);
    
    try {
      // Get current session for auth token
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        console.error('[UnifiedOrchestrator] No auth session available for trade execution');
        return { success: false, error: 'Not authenticated' };
      }

      // Prepare trade payload
      const signalType = decision.action === 'BUY' ? 'LONG' : 'SHORT';
      const currentPrice = marketSnapshot?.price || 0;
      
      const payload = {
        symbol,
        signalType,
        coherence: lambdaState?.coherence || 0,
        lighthouseValue: lighthouseState?.L || 0,
        lighthouseConfidence: lighthouseState?.confidence || 0,
        prismLevel: prismOutput?.level || 1,
        currentPrice,
        price: currentPrice,
        recommendedExchange: exchange,
        positionSizeUsd: positionSize,
      };

      console.log('[UnifiedOrchestrator] Calling execute-trade edge function:', payload);

      // Call the execute-trade edge function
      const { data, error } = await supabase.functions.invoke('execute-trade', {
        body: payload,
      });

      if (error) {
        console.error('[UnifiedOrchestrator] Trade execution failed:', error);
        return { success: false, error: error.message || 'Trade execution failed' };
      }

      if (!data?.success) {
        console.error('[UnifiedOrchestrator] Trade rejected:', data?.error);
        return { success: false, error: data?.error || 'Trade rejected' };
      }

      console.log('[UnifiedOrchestrator] Trade executed successfully:', data);

      // Broadcast the trade event with full routing info
      temporalLadder.broadcast(SYSTEMS.MASTER_EQUATION, 'TRADE_EXECUTED', {
        action: decision.action,
        symbol,
        confidence: decision.confidence,
        exchange,
        positionSizeUsd: positionSize,
        orderId: data.execution?.exchange_order_id,
        executedPrice: data.execution?.executed_price,
      });

      // Update elephant memory with trade result
      const estimatedProfit = positionSize * 0.01; // Assume small profit for now, will be updated on close
      elephantMemory.recordTrade(symbol, estimatedProfit, decision.action === 'BUY' ? 'BUY' : 'SELL');

      return {
        success: true,
        orderId: data.execution?.exchange_order_id,
        executedPrice: data.execution?.executed_price,
        quantity: data.execution?.quantity,
        exchange,
      };

    } catch (err: any) {
      console.error('[UnifiedOrchestrator] Trade execution error:', err);
      return { success: false, error: err.message || 'Unexpected error' };
    }
  }
  
  /**
   * Update dryRun configuration at runtime
   */
  setDryRun(dryRun: boolean): void {
    this.config.dryRun = dryRun;
    console.log(`[UnifiedOrchestrator] DryRun mode set to: ${dryRun}`);
  }
  
  /**
   * Get current configuration
   */
  getConfig(): OrchestratorConfig {
    return { ...this.config };
  }
  
  /**
   * Check if live trading is enabled
   */
  isLiveTrading(): boolean {
    return !this.config.dryRun;
  }
  
  /**
   * Start continuous orchestration
   */
  start(intervalMs: number = 3000): void {
    this.isRunning = true;
    console.log('[UnifiedOrchestrator] Started');
  }
  
  /**
   * Stop orchestration
   */
  stop(): void {
    this.isRunning = false;
    console.log('[UnifiedOrchestrator] Stopped');
  }
}

// Singleton instance
export const unifiedOrchestrator = new UnifiedOrchestrator();
