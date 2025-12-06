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

export interface OrchestrationResult {
  timestamp: number;
  busSnapshot: BusSnapshot;
  lambdaState: LambdaState | null;
  lighthouseState: LighthouseState | null;
  rainbowState: RainbowState | null;
  prismOutput: PrismOutput | null;
  ecosystemState: EcosystemState | null;
  finalDecision: {
    action: 'BUY' | 'SELL' | 'HOLD';
    symbol: string;
    confidence: number;
    reason: string;
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
    
    // Step 7: Check Elephant Memory for avoidance
    const avoidance = elephantMemory.shouldAvoid(symbol);
    
    // Step 8: Get bus consensus
    const busSnapshot = unifiedBus.snapshot();
    const consensus = unifiedBus.checkConsensus();
    
    // Step 9: Make final decision
    const finalDecision = this.makeFinalDecision(
      consensus,
      lambdaState,
      lighthouseState,
      avoidance,
      symbol
    );
    
    // Step 10: Execute trade if conditions met
    let tradeExecuted = false;
    if (finalDecision.action !== 'HOLD' && !this.config.dryRun) {
      tradeExecuted = await this.executeTrade(finalDecision, symbol);
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
   * Make final trading decision based on all inputs
   */
  private makeFinalDecision(
    consensus: { ready: boolean; signal: SignalType; confidence: number },
    lambdaState: LambdaState,
    lighthouseState: LighthouseState,
    avoidance: { avoid: boolean; reason: string | null },
    symbol: string
  ): { action: 'BUY' | 'SELL' | 'HOLD'; symbol: string; confidence: number; reason: string } {
    // Check avoidance first
    if (avoidance.avoid) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: `Elephant Memory: ${avoidance.reason}`,
      };
    }
    
    // Check if consensus is ready
    if (!consensus.ready) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: 'Systems not ready for consensus',
      };
    }
    
    // Check minimum coherence
    if (lambdaState.coherence < this.config.minCoherence) {
      return {
        action: 'HOLD',
        symbol,
        confidence: lambdaState.coherence,
        reason: `Coherence ${(lambdaState.coherence * 100).toFixed(1)}% below threshold`,
      };
    }
    
    // Check minimum confidence
    if (consensus.confidence < this.config.minConfidence) {
      return {
        action: 'HOLD',
        symbol,
        confidence: consensus.confidence,
        reason: `Confidence ${(consensus.confidence * 100).toFixed(1)}% below threshold`,
      };
    }
    
    // Check LHE requirement
    if (this.config.requireLHE && !lighthouseState.isLHE) {
      return {
        action: 'HOLD',
        symbol,
        confidence: consensus.confidence,
        reason: 'Lighthouse Event not detected',
      };
    }
    
    // Return consensus signal
    if (consensus.signal === 'NEUTRAL') {
      return {
        action: 'HOLD',
        symbol,
        confidence: consensus.confidence,
        reason: 'No clear signal from consensus',
      };
    }
    
    return {
      action: consensus.signal,
      symbol,
      confidence: consensus.confidence,
      reason: `Consensus: ${consensus.signal} at ${(consensus.confidence * 100).toFixed(1)}% confidence`,
    };
  }
  
  /**
   * Execute a trade (stub - would integrate with trading execution)
   */
  private async executeTrade(
    decision: { action: 'BUY' | 'SELL' | 'HOLD'; symbol: string; confidence: number },
    symbol: string
  ): Promise<boolean> {
    console.log(`[UnifiedOrchestrator] Executing ${decision.action} on ${symbol}`);
    
    // In a real implementation, this would call the trading execution edge function
    // For now, we just broadcast the event
    temporalLadder.broadcast(SYSTEMS.MASTER_EQUATION, 'TRADE_EXECUTED', {
      action: decision.action,
      symbol,
      confidence: decision.confidence,
    });
    
    return true;
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
  
  /**
   * Get current configuration
   */
  getConfig(): OrchestratorConfig {
    return { ...this.config };
  }
  
  /**
   * Update configuration
   */
  setConfig(config: Partial<OrchestratorConfig>): void {
    this.config = { ...this.config, ...config };
  }
}

// Singleton instance
export const unifiedOrchestrator = new UnifiedOrchestrator();
