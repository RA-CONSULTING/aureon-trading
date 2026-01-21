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
import { qgitaSignalGenerator, type QGITASignal } from './qgitaSignalGenerator';
import { hocusPatternPipeline, type PipelineState } from './hocusPatternPipeline';
import { hncProbabilityMatrix, type ProbabilityMatrix, type TradingSignal as ProbabilitySignal } from './hncProbabilityMatrix';
import { quantumTelescope, type TelescopeObservation } from './quantumTelescope';
import { imperialPredictability, type CosmicState, type ImperialPrediction } from './imperialPredictability';
import { crossExchangeArbitrageScanner, type ArbitrageScanResult } from './crossExchangeArbitrageScanner';
import { trailingStopManager, type TrailingStop } from './trailingStopManager';
import { positionHeatTracker, type HeatState } from './positionHeatTracker';
import { portfolioRebalancer } from './portfolioRebalancer';
import { adaptiveFilterThresholds } from './adaptiveFilterThresholds';
import { unifiedStateAggregator } from './unifiedStateAggregator';
import { notificationManager } from './notificationManager';
import { exchangeLearningTracker } from './exchangeLearningTracker';
import { tradeLogger } from './tradeLogger';
import { adaptiveLearningEngine } from './adaptiveLearningEngine';
import { tickerCacheManager, type CachedTicker } from './tickerCacheManager';
import { opportunityScanner, type ScoredOpportunity } from './opportunityScanner';
import { positionManager, type Position } from './positionManager';
import { capitalPool, type CapitalState, type PositionSizeResult } from './capitalPool';
import { gaiaLatticeEngine, type LatticeState } from './gaiaLatticeEngine';
import { startupHarvester } from './startupHarvester';
import { lotSizeValidator } from './lotSizeValidator';
import { supabase } from '@/integrations/supabase/client';
import { getEarthStreams, earthStreamsMonitor, type SimpleEarthStreams } from '@/lib/earth-streams';


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
  hocusPatternState: PipelineState | null;
  probabilityMatrix: ProbabilityMatrix | null;
  probabilitySignal: ProbabilitySignal | null;
  telescopeObservation: TelescopeObservation | null;
  cosmicState: CosmicState | null;
  imperialPrediction: ImperialPrediction | null;
  arbitrageScan: ArbitrageScanResult | null;
  heatState: HeatState | null;
  trailingStops: TrailingStop[];
  routingDecision: RoutingDecision | null;
  qgitaSignal: QGITASignal | null;
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
    qgitaTier?: 1 | 2 | 3;
    probabilityH1?: string;
    cosmicPhase?: string;
    heatBlocked?: boolean;
    arbitrageOpportunity?: boolean;
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
  minCoherence: 0.35, // Lowered from 0.70 for demo mode
  minConfidence: 0.40, // Lowered from 0.50 for demo mode
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
    temporalLadder.registerSystem(SYSTEMS.HOCUS_PATTERN);
    
    // Initialize Earth streams monitoring
    if (!earthStreamsMonitor.isMonitoringActive()) {
      earthStreamsMonitor.initialize();
    }
  }
  
  /**
   * Fetch Earth streams data
   */
  private async fetchEarthStreams(): Promise<SimpleEarthStreams | null> {
    try {
      return await getEarthStreams();
    } catch (err) {
      console.debug('[Orchestrator] Earth streams unavailable');
      return null;
    }
  }
  
  /**
   * Fetch Schumann resonance data from edge function
   */
  private async fetchSchumannData(): Promise<{ coherenceBoost: number; fundamentalHz: number } | null> {
    try {
      const { data, error } = await supabase.functions.invoke('fetch-schumann-data');
      if (error || !data) return null;
      return {
        coherenceBoost: data.coherenceBoost || 0,
        fundamentalHz: data.fundamentalHz || 7.83
      };
    } catch (err) {
      console.debug('[Orchestrator] Schumann data unavailable');
      return null;
    }
  }
  
  /**
   * Run a complete orchestration cycle
   */
  async runCycle(marketSnapshot: MarketSnapshot, symbol: string = 'BTCUSDT'): Promise<OrchestrationResult> {
    this.currentSymbol = symbol;
    const timestamp = Date.now();
    
    // Step 0: Fetch Earth streams and Schumann data to feed into MasterEquation
    try {
      const earthStreams = await this.fetchEarthStreams();
      if (earthStreams) {
        this.masterEquation.setEarthStreams(earthStreams);
      }
      
      const schumannData = await this.fetchSchumannData();
      if (schumannData && schumannData.coherenceBoost) {
        this.masterEquation.setUserLocation(0, 0, 0, schumannData.coherenceBoost);
      }
    } catch (err) {
      // Non-critical - continue with cycle
      console.debug('[Orchestrator] Earth/Schumann data unavailable:', err);
    }
    
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
    
    // Step 6c: Generate QGITA signal directly in orchestrator
    const qgitaSignal = qgitaSignalGenerator.generateSignal(
      timestamp,
      marketSnapshot.price,
      marketSnapshot.volume,
      lambdaState.lambda,
      lambdaState.coherence,
      lambdaState.substrate,
      lambdaState.observer,
      lambdaState.echo
    );
    this.publishQGITA(qgitaSignal);
    
    // Step 6d: Publish Prism state to UnifiedBus
    this.publishPrism(prismOutput);
    
    // Step 6e: Run Hocus→Pattern→Template Pipeline (background automation)
    const hocusPatternState = hocusPatternPipeline.step(lambdaState.lambda);
    this.publishHocusPattern(hocusPatternState);
    temporalLadder.heartbeat(SYSTEMS.HOCUS_PATTERN, hocusPatternState.totalCoherence);
    
    // Step 6f: HNC Probability Matrix - 2-hour temporal forecasting
    const probSnapshot = hncProbabilityMatrix.createSnapshot(
      symbol,
      marketSnapshot.price,
      marketSnapshot.volume,
      marketSnapshot.momentum,
      lambdaState.coherence
    );
    hncProbabilityMatrix.addSnapshot(probSnapshot);
    
    const currentMarketData = {
      price: marketSnapshot.price,
      volume: marketSnapshot.volume,
      momentum: marketSnapshot.momentum,
      coherence: lambdaState.coherence,
    };
    const probabilityMatrix = hncProbabilityMatrix.generateMatrix(symbol, { ...currentMarketData, resonance: prismOutput.resonance });
    const probabilitySignal = hncProbabilityMatrix.getTradingSignal(symbol, currentMarketData);
    this.publishProbabilityMatrix(probabilityMatrix, probabilitySignal);
    temporalLadder.heartbeat(SYSTEMS.PROBABILITY_MATRIX, probabilitySignal.confidence);
    
    // Step 7: Quantum Telescope - Geometric light analysis
    const telescopeObservation = quantumTelescope.observe({
      price: marketSnapshot.price,
      volume: marketSnapshot.volume,
      volatility: marketSnapshot.volatility,
      momentum: marketSnapshot.momentum,
    }, symbol);
    quantumTelescope.registerAndPublish(telescopeObservation);
    
    // Step 8: Imperial Predictability - Cosmic synchronization
    const { cosmicState, prediction: imperialPrediction } = imperialPredictability.runCycle(
      lambdaState.coherence,
      symbol,
      marketSnapshot.momentum
    );
    
    // Step 9: Get multi-exchange state and position sizing (moved up for heat tracker)
    const exchangeState = multiExchangeClient.getState();
    const positionSizing = multiExchangeClient.calculatePositionSize(0.02, 'USDT');
    
    // Step 10: Cross-Exchange Arbitrage Scanner
    // Update price cache with current market snapshot
    crossExchangeArbitrageScanner.updatePrice(symbol, 'binance', marketSnapshot.price);
    const arbitrageScan = crossExchangeArbitrageScanner.scanDirectArbitrage([symbol]);
    if (arbitrageScan.bestOpportunity?.isViable) {
      console.log(`[Orchestrator:Arbitrage] 💰 Opportunity: ${arbitrageScan.bestOpportunity.symbol} ` +
        `Buy@${arbitrageScan.bestOpportunity.buyExchange} → Sell@${arbitrageScan.bestOpportunity.sellExchange} ` +
        `Net: ${(arbitrageScan.bestOpportunity.netProfitPct * 100).toFixed(2)}%`);
    }
    
    // Step 11: Position Heat Tracker - Check correlation concentration
    positionHeatTracker.setCapital(exchangeState.totalEquityUsd || 10000);
    const heatState = positionHeatTracker.getHeatState();
    const heatCheck = positionHeatTracker.canAddPosition(symbol, positionSizing.positionSizeUsd);
    if (!heatCheck.allowed) {
      console.log(`[Orchestrator:Heat] 🔥 Position blocked: ${heatCheck.reason}`);
    }
    
    // Step 12: Trailing Stop Manager - Update existing stops
    const trailingStops = trailingStopManager.getAllStops();
    for (const stop of trailingStops) {
      const stopUpdate = trailingStopManager.updateStop(stop.symbol, marketSnapshot.price);
      if (stopUpdate.triggered) {
        console.log(`[Orchestrator:TrailingStop] ⚠️ Stop triggered for ${stop.symbol}`);
      }
    }
    
    // Step 13: Get Smart Order Router recommendation
    let routingDecision: RoutingDecision | null = null;
    try {
      routingDecision = await smartOrderRouter.getBestQuote(symbol, 'BUY', positionSizing.positionSizeUsd / marketSnapshot.price);
    } catch (err) {
      console.warn('[UnifiedOrchestrator] Smart routing failed, using default:', err);
    }
    
    // Step 14: Check Elephant Memory for avoidance
    const avoidance = elephantMemory.shouldAvoid(symbol);
    
    // Step 14b: Adaptive Filter Thresholds - Detect market regime
    const priceHistory = [marketSnapshot.price]; // In production, maintain a window
    const volumeHistory = [marketSnapshot.volume];
    const regimeResult = adaptiveFilterThresholds.detectRegime(priceHistory, volumeHistory);
    const passesAdaptiveThresholds = adaptiveFilterThresholds.passesThresholds(
      lambdaState.coherence,
      marketSnapshot.momentum,
      marketSnapshot.volume
    );
    
    // Step 14c: Unified State Aggregator - Check symbol insights
    const symbolInsight = unifiedStateAggregator.getSymbolInsight(symbol);
    const isOptimalHour = unifiedStateAggregator.isOptimalTradingHour();
    const isPrimeSymbol = unifiedStateAggregator.isPrimeSymbol(symbol);
    
    // Step 15: Get bus consensus
    const busSnapshot = unifiedBus.snapshot();
    const consensus = unifiedBus.checkConsensus();
    
    // Step 16: Make final decision with QGITA tier integration and heat check
    const finalDecision = this.makeFinalDecision(
      consensus,
      lambdaState,
      lighthouseState,
      avoidance,
      symbol,
      ecosystemState,
      routingDecision,
      positionSizing,
      qgitaSignal,
      heatCheck
    );
    
    // Step 17: Apply adaptive learning engine before trade
    const frequencyBand = tradeLogger.classifyFrequencyBand(prismOutput.frequency);
    const adaptiveCheck = adaptiveLearningEngine.shouldTrade({
      coherence: lambdaState.coherence,
      confidence: finalDecision.confidence,
      frequencyBand,
      regime: regimeResult.regime,
      hour: new Date().getHours(),
    });
    
    // Step 18: Execute trade if conditions met (also check adaptive thresholds)
    let tradeExecuted = false;
    let tradeResult: TradeExecutionResult | null = null;
    // Also check imperial should trade, heat allows, and adaptive thresholds pass
    if (finalDecision.action !== 'HOLD' && !this.config.dryRun && cosmicState.shouldTrade && heatCheck.allowed && passesAdaptiveThresholds && adaptiveCheck.allowed) {
      // Apply adaptive position size modifier
      const adjustedPositionSize = adaptiveLearningEngine.adjustPositionSize(finalDecision.positionSizeUsd || positionSizing.positionSizeUsd) * adaptiveCheck.modifier;
      
      tradeResult = await this.executeTrade(
        { ...finalDecision, positionSizeUsd: adjustedPositionSize }, 
        symbol, 
        marketSnapshot, 
        lambdaState, 
        lighthouseState, 
        prismOutput
      );
      tradeExecuted = tradeResult.success;
      
      if (tradeResult.success) {
        // Log trade entry via TradeLogger
        await tradeLogger.logEntry({
          symbol,
          side: finalDecision.action as 'BUY' | 'SELL',
          price: tradeResult.executedPrice || marketSnapshot.price,
          quantity: tradeResult.quantity || adjustedPositionSize / marketSnapshot.price,
          positionSizeUsd: adjustedPositionSize,
          prismFrequency: prismOutput.frequency,
          coherence: lambdaState.coherence,
          lambda: lambdaState.lambda,
          lighthouseConfidence: lighthouseState.confidence,
          hncProbability: probabilitySignal.probability,
          qgitaTier: qgitaSignal?.tier || 3,
          exchange: tradeResult.exchange || 'binance',
          orderId: tradeResult.orderId,
          regime: regimeResult.regime,
          cosmicPhase: cosmicState.phase,
        });
        
        // Add position to heat tracker
        positionHeatTracker.addPosition(symbol, adjustedPositionSize);
        // Create trailing stop for new position
        trailingStopManager.createStop(symbol, marketSnapshot.price, marketSnapshot.price);
        // Record to adaptive thresholds for learning
        adaptiveFilterThresholds.recordTrade({
          symbol,
          profit: 0, // Will be updated on close
          coherenceAtEntry: lambdaState.coherence,
          momentumAtEntry: marketSnapshot.momentum,
          volumeAtEntry: marketSnapshot.volume,
          regime: regimeResult.regime,
          timestamp: Date.now(),
        });
        // Update state aggregator
        unifiedStateAggregator.updateSymbolInsight(symbol, 0, true);
        // Record to exchange learning tracker
        const routedExchange = (routingDecision?.bestQuote?.exchange || 'binance') as 'binance' | 'kraken' | 'alpaca' | 'capital';
        exchangeLearningTracker.recordTrade(routedExchange, symbol, 0, true, 50);
        // Send notification
        await notificationManager.notifyTrade(
          symbol, 
          finalDecision.action as 'BUY' | 'SELL', 
          marketSnapshot.price, 
          adjustedPositionSize / marketSnapshot.price
        );
      } else {
        console.warn('[UnifiedOrchestrator] Trade failed:', tradeResult.error);
      }
    } else if (!adaptiveCheck.allowed) {
      console.log(`[UnifiedOrchestrator] Adaptive learning blocked trade: ${adaptiveCheck.reason}`);
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
      hocusPatternState,
      probabilityMatrix,
      probabilitySignal,
      telescopeObservation,
      cosmicState,
      imperialPrediction,
      arbitrageScan,
      heatState,
      trailingStops,
      routingDecision,
      qgitaSignal,
      positionSizing,
      finalDecision: {
        ...finalDecision,
        cosmicPhase: cosmicState.phase,
        heatBlocked: !heatCheck.allowed,
        arbitrageOpportunity: arbitrageScan.bestOpportunity?.isViable || false,
      },
      tradeExecuted,
    };
  }
  
  /**
   * Publish HNC Probability Matrix state to bus
   */
  private publishProbabilityMatrix(matrix: ProbabilityMatrix, signal: ProbabilitySignal): void {
    let busSignal: SignalType = 'NEUTRAL';
    if (signal.action === 'BUY') busSignal = 'BUY';
    else if (signal.action === 'SELL') busSignal = 'SELL';
    
    const h1State = matrix.hourPlus1?.state || 'NEUTRAL';
    const probEmoji = signal.action === 'BUY' ? '🟢' : signal.action === 'SELL' ? '🔴' : '⚪';
    
    console.log(
      `[Orchestrator:ProbMatrix] ${probEmoji} ${signal.action} | ` +
      `H+1: ${h1State} (${(signal.probability * 100).toFixed(1)}%) | ` +
      `Conf: ${(signal.confidence * 100).toFixed(1)}% | ` +
      `Mod: ${signal.modifier.toFixed(2)} | ` +
      `FineTune: ${(signal.fineTune * 100).toFixed(1)}%`
    );
    
    unifiedBus.publish({
      systemName: 'ProbabilityMatrix',
      timestamp: Date.now(),
      ready: true,
      coherence: signal.confidence,
      confidence: signal.probability,
      signal: busSignal,
      data: {
        matrix,
        signal,
        h1State,
        h2State: matrix.hourPlus2?.state || 'NEUTRAL',
        combinedProbability: matrix.combinedProbability,
        fineTunedProbability: matrix.fineTunedProbability,
        positionModifier: matrix.positionModifier,
        recommendedAction: matrix.recommendedAction,
      },
    });
  }
  
  /**
   * Publish QGITA signal to bus with logging
   */
  private publishQGITA(signal: QGITASignal): void {
    // Map HOLD to NEUTRAL for SignalType
    let busSignal: SignalType = 'NEUTRAL';
    if (signal.signalType === 'BUY') busSignal = 'BUY';
    else if (signal.signalType === 'SELL') busSignal = 'SELL';

    // Structured logging
    const tierEmoji = signal.tier === 1 ? '🥇' : signal.tier === 2 ? '🥈' : '🥉';
    const signalEmoji = signal.signalType === 'BUY' ? '🟢' : signal.signalType === 'SELL' ? '🔴' : '⚪';
    const lheEmoji = signal.lighthouse.isLHE ? '🔥' : '';
    
    console.log(
      `[Orchestrator:QGITA] ${signalEmoji} ${signal.signalType} | ` +
      `${tierEmoji} Tier ${signal.tier} | ` +
      `Conf: ${signal.confidence.toFixed(1)}% | ` +
      `${lheEmoji}LHE: ${signal.lighthouse.isLHE} (L=${signal.lighthouse.L.toFixed(3)}) | ` +
      `FTCP: ${signal.ftcpDetected} | Curv: ${signal.curvatureDirection}`
    );

    unifiedBus.publish({
      systemName: 'QGITASignal',
      timestamp: Date.now(),
      ready: true,
      coherence: (signal.coherence.linearCoherence + signal.coherence.nonlinearCoherence + signal.coherence.crossScaleCoherence) / 3,
      confidence: signal.confidence / 100,
      signal: busSignal,
      data: {
        signal,
        signalType: signal.signalType,
        tier: signal.tier,
        confidence: signal.confidence,
        curvature: signal.curvature,
        curvatureDirection: signal.curvatureDirection,
        ftcpDetected: signal.ftcpDetected,
        goldenRatioScore: signal.goldenRatioScore,
        lighthouseL: signal.lighthouse.L,
        isLHE: signal.lighthouse.isLHE,
        anomalyPointer: signal.anomalyPointer,
      },
    });
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
   * Publish Hocus→Pattern→Template Pipeline state to bus (background automation)
   */
  private publishHocusPattern(state: PipelineState): void {
    // Determine signal based on pipeline stage and dominant template
    let signal: SignalType = 'NEUTRAL';
    if (state.pipelineStage === 'TEMPLATE' && state.totalCoherence > 0.7) {
      // When templates are locked with high coherence, favor BUY (love frequency alignment)
      const dominantMode = state.modes[state.dominantMode];
      if (dominantMode && dominantMode.frequency >= 500 && dominantMode.frequency <= 600) {
        signal = 'BUY'; // Love frequency band (528 Hz)
      } else if (dominantMode && dominantMode.frequency < 100) {
        signal = 'SELL'; // Low/fear frequency band
      }
    }
    
    unifiedBus.publish({
      systemName: 'HocusPattern',
      timestamp: Date.now(),
      ready: state.activeTemplates > 0,
      coherence: state.totalCoherence,
      confidence: state.dominantCoherence,
      signal,
      data: {
        pipelineStage: state.pipelineStage,
        activeTemplates: state.activeTemplates,
        dominantMode: state.dominantMode,
        dominantEmotionalPhase: state.dominantEmotionalPhase,
        harmonicResonance: state.harmonicResonance,
        codexEnhanced: state.codexEnhanced,
      },
    });
  }
  
  /**
   * Make final trading decision based on all inputs including QGITA tier and heat check
   */
  private makeFinalDecision(
    consensus: { ready: boolean; signal: SignalType; confidence: number },
    lambdaState: LambdaState,
    lighthouseState: LighthouseState,
    avoidance: { avoid: boolean; reason: string | null },
    symbol: string,
    ecosystemState: EcosystemState | null,
    routingDecision: RoutingDecision | null,
    positionSizing: { positionSizeUsd: number; availableBalance: number; riskAmount: number } | null,
    qgitaSignal: QGITASignal | null,
    heatCheck?: { allowed: boolean; reason: string; projectedHeat: number }
  ): { action: 'BUY' | 'SELL' | 'HOLD'; symbol: string; confidence: number; reason: string; harmonic6D?: { score: number; waveState: string; harmonicLock: boolean }; recommendedExchange?: string; positionSizeUsd?: number; qgitaTier?: 1 | 2 | 3 } {
    // Extract 6D probability fusion from ecosystem state
    const probabilityFusion = ecosystemState?.probabilityFusion ?? null;
    const waveState = probabilityFusion?.waveState ?? 'RESONANT';
    const harmonicLock = probabilityFusion?.harmonicLock ?? false;
    const harmonic6DScore = probabilityFusion ? (probabilityFusion.fusedProbability - 0.5) * 2 : 0;
    const harmonic6DData = { score: harmonic6DScore, waveState, harmonicLock };

    // Check heat limit first
    if (heatCheck && !heatCheck.allowed) {
      return {
        action: 'HOLD',
        symbol,
        confidence: 0,
        reason: `Heat Limit: ${heatCheck.reason}`,
        harmonic6D: harmonic6DData,
      };
    }

    // Check avoidance
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
    
    // QGITA tier-based position sizing and thresholds
    const qgitaTier = qgitaSignal?.tier || 3;
    const qgitaPositionMultiplier = qgitaSignalGenerator.getPositionSizeMultiplier(qgitaTier);
    
    // Tier 1: Lower confidence threshold, full position
    // Tier 2: Normal threshold, half position
    // Tier 3: Higher threshold, force HOLD
    if (qgitaTier === 3 && qgitaSignal?.signalType !== 'HOLD') {
      console.log('[UnifiedOrchestrator] QGITA Tier 3 - forcing reduced confidence');
      effectiveConfidence *= 0.7;
    } else if (qgitaTier === 1 && qgitaSignal?.lighthouse.isLHE) {
      console.log('[UnifiedOrchestrator] QGITA Tier 1 + LHE - boosting confidence');
      effectiveConfidence = Math.min(1, effectiveConfidence + 0.15);
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
        qgitaTier,
      };
    }
    
    // Apply QGITA position sizing
    let finalPositionSize = positionSizing?.positionSizeUsd || 0;
    if (qgitaPositionMultiplier < 1) {
      finalPositionSize *= qgitaPositionMultiplier;
      console.log(`[UnifiedOrchestrator] QGITA Tier ${qgitaTier} reducing position: $${finalPositionSize.toFixed(2)}`);
    }
    
    // Build reason with QGITA context
    const lockStatus = harmonicLock ? ' [528Hz LOCKED]' : '';
    const exchangeInfo = routingDecision ? ` | Route: ${routingDecision.recommendedExchange}` : '';
    const positionInfo = finalPositionSize > 0 ? ` | Size: $${finalPositionSize.toFixed(2)}` : '';
    const qgitaInfo = ` | QGITA: T${qgitaTier} ${qgitaSignal?.signalType || 'N/A'} ${qgitaSignal?.lighthouse.isLHE ? '🔥LHE' : ''}`;
    const reason = `Consensus: ${consensus.signal} at ${(effectiveConfidence * 100).toFixed(1)}% | 6D: ${waveState}${lockStatus}${qgitaInfo}${exchangeInfo}${positionInfo}`;
    
    return {
      action: consensus.signal,
      symbol,
      confidence: effectiveConfidence,
      reason,
      harmonic6D: harmonic6DData,
      recommendedExchange: routingDecision?.recommendedExchange,
      positionSizeUsd: finalPositionSize,
      qgitaTier,
    };
  }
  
  /**
   * Execute a trade with smart order routing via edge function
   * Phase 5C: Enhanced credential validation before execution
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
      // Phase 5C: Pre-validate authentication and credentials
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session?.access_token) {
        console.error('[UnifiedOrchestrator] No auth session available for trade execution');
        return { success: false, error: 'Not authenticated' };
      }
      
      // Phase 5C: Validate user has credentials for target exchange
      const { data: userSession, error: sessionError } = await supabase
        .from('aureon_user_sessions')
        .select('binance_api_key_encrypted, kraken_api_key_encrypted, alpaca_api_key_encrypted, capital_api_key_encrypted')
        .eq('user_id', session.user.id)
        .maybeSingle();
      
      if (sessionError || !userSession) {
        console.error('[UnifiedOrchestrator] Cannot verify user credentials:', sessionError?.message);
        return { success: false, error: 'Cannot verify trading credentials' };
      }
      
      // Check exchange-specific credentials
      const credentialField = `${exchange}_api_key_encrypted` as keyof typeof userSession;
      if (!userSession[credentialField]) {
        console.error(`[UnifiedOrchestrator] Missing ${exchange} API credentials`);
        return { success: false, error: `Missing ${exchange} API credentials. Add them in Settings.` };
      }

      // Prepare trade payload
      const signalType = decision.action === 'BUY' ? 'LONG' : 'SHORT';
      const currentPrice = marketSnapshot?.price || 0;
      
      // GAP CLOSURE: Validate lot size before execution
      const quantity = positionSize / currentPrice;
      const lotValidation = await lotSizeValidator.validate(symbol, quantity, currentPrice, exchange);
      
      if (!lotValidation.valid) {
        console.warn(`[UnifiedOrchestrator] Lot size validation failed: ${lotValidation.error}`);
        return { success: false, error: lotValidation.error };
      }
      
      const payload = {
        symbol,
        signalType,
        coherence: lambdaState?.coherence || 0,
        lighthouseValue: lighthouseState?.L || 0,
        lighthouseConfidence: lighthouseState?.confidence || 0,
        prismLevel: prismOutput?.level || 1,
        currentPrice: lotValidation.adjustedPrice,
        price: lotValidation.adjustedPrice,
        quantity: lotValidation.adjustedQuantity,
        recommendedExchange: exchange,
        positionSizeUsd: lotValidation.adjustedQuantity * lotValidation.adjustedPrice,
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
   * Run FULL trading cycle like Python aureon_unified_ecosystem
   * 1. Update Capital Pool with latest equity
   * 2. Refresh all tickers
   * 3. Apply Gaia Lattice filtering
   * 4. Scan for opportunities
   * 5. Find best opportunity 
   * 6. Run full cycle on best symbol
   * 7. Check existing positions for TP/SL
   * 8. Log market sweep
   */
  async runFullCycle(): Promise<{
    tickersScanned: number;
    opportunitiesFound: number;
    filteredOpportunities: number;
    bestOpportunity: ScoredOpportunity | null;
    result: OrchestrationResult | null;
    positionsChecked: number;
    positionsClosed: number;
    capitalState: { availableCapital: number; positionCount: number };
    latticePhase: string;
  }> {
    const startTime = Date.now();
    
    // Step 1: Update Capital Pool with latest equity
    const exchangeState = multiExchangeClient.getState();
    capitalPool.updateEquity(exchangeState.totalEquityUsd || 1000, 0);
    const capitalState = capitalPool.getState();
    
    // Step 2: Check if we can open new positions
    const canOpen = capitalPool.canOpenPosition();
    if (!canOpen.allowed) {
      console.log(`[Orchestrator:FullCycle] ⚠️ Cannot open positions: ${canOpen.reason}`);
    }
    
    // Step 3: Refresh ticker cache (fetches all 500+ pairs)
    console.log('[Orchestrator:FullCycle] 🔄 Refreshing ticker cache...');
    await tickerCacheManager.refreshAll();
    const allTickers = tickerCacheManager.getAllTickers();
    const tickerCount = allTickers.length;
    temporalLadder.heartbeat(SYSTEMS.TICKER_CACHE, 1.0);
    
    // Step 4: Update Gaia Lattice with current market coherence
    const avgMomentum = allTickers.reduce((s, t) => s + Math.abs(t.momentum), 0) / Math.max(allTickers.length, 1);
    const marketCoherence = Math.max(0.3, Math.min(0.95, 1 - avgMomentum * 10));
    const latticeState = gaiaLatticeEngine.update(marketCoherence);
    
    // Step 5: Update position manager current prices for all tickers
    console.log(`[Orchestrator:FullCycle] 📊 Scanning ${tickerCount} tickers for opportunities...`);
    for (const ticker of allTickers) {
      positionManager.updatePrice(ticker.symbol, ticker.price);
    }
    
    // Step 6: Scan for opportunities
    const scanResult = await opportunityScanner.scan();
    let opportunities = scanResult.opportunities;
    const preFilterCount = opportunities.length;
    temporalLadder.heartbeat(SYSTEMS.OPPORTUNITY_SCANNER, opportunities.length > 0 ? 0.9 : 0.3);
    
    // Step 7: Apply Gaia Lattice filtering (Triadic Envelope Protocol)
    opportunities = gaiaLatticeEngine.filterSignals(opportunities);
    const filteredCount = opportunities.length;
    
    if (preFilterCount !== filteredCount) {
      console.log(`[Orchestrator:FullCycle] 🌍 Gaia Lattice filtered ${preFilterCount} → ${filteredCount}`);
    }
    
    console.log(`[Orchestrator:FullCycle] 🎯 Found ${filteredCount} valid opportunities`);
    
    // Step 8: Log market sweep
    console.log(`[MarketSweep] 📊 ${tickerCount} tickers | ${preFilterCount}→${filteredCount} opps | Lattice: ${latticeState.phase} | Capital: $${capitalState.availableCapital.toFixed(2)}`);
    
    // Step 9: Check existing positions for TP/SL exits
    const positionsChecked = positionManager.getPositions().length;
    const positionsToClose = positionManager.checkAllPositions();
    temporalLadder.heartbeat(SYSTEMS.POSITION_MANAGER, 1.0);
    
    // Release capital for closed positions
    for (const pos of positionsToClose) {
      capitalPool.release(pos.symbol, pos.unrealizedPnl);
    }
    
    if (positionsToClose.length > 0) {
      console.log(`[Orchestrator:FullCycle] 💰 Closed ${positionsToClose.length} positions`);
    }
    
    // Step 10: Run full cycle on best opportunity
    let result: OrchestrationResult | null = null;
    const bestOpportunity = opportunities.find(o => !o.isBlacklisted && o.tier <= 2) || opportunities[0] || null;
    
    if (bestOpportunity && canOpen.allowed) {
      console.log(`[Orchestrator:FullCycle] 🎯 Best: ${bestOpportunity.symbol} Score=${bestOpportunity.score.toFixed(3)} Tier=${bestOpportunity.tier}`);
      
      // Calculate position size using Capital Pool
      const positionSize = capitalPool.calculatePositionSize(
        bestOpportunity.score,
        bestOpportunity.volatility,
        bestOpportunity.tier
      );
      
      if (positionSize.sizeUsd >= 10) {
        const ticker = tickerCacheManager.getTicker(bestOpportunity.symbol);
        if (ticker) {
          const marketSnapshot: MarketSnapshot = {
            price: ticker.price,
            volume: ticker.volume,
            volatility: ticker.volatility,
            momentum: ticker.momentum,
            spread: ticker.spread,
            timestamp: ticker.timestamp,
          };
          
          result = await this.runCycle(marketSnapshot, bestOpportunity.symbol);
          
          if (result.tradeExecuted) {
            capitalPool.reserve(bestOpportunity.symbol, positionSize.sizeUsd);
          }
        }
      }
    } else if (!bestOpportunity) {
      console.log('[Orchestrator:FullCycle] ⚠️ No opportunities above threshold');
    }
    
    const elapsed = Date.now() - startTime;
    console.log(`[Orchestrator:FullCycle] ✅ ${elapsed}ms | Tickers:${tickerCount} | Opps:${filteredCount}/${preFilterCount} | Positions:${positionsChecked}`);
    
    return {
      tickersScanned: tickerCount,
      opportunitiesFound: preFilterCount,
      filteredOpportunities: filteredCount,
      bestOpportunity,
      result,
      positionsChecked,
      positionsClosed: positionsToClose.length,
      capitalState: { availableCapital: capitalState.availableCapital, positionCount: capitalState.positionCount },
      latticePhase: latticeState.phase,
    };
  }
  
  /**
   * Run startup harvest - scan existing positions and close profitable ones
   */
  async runStartupHarvest(dryRun: boolean = true): Promise<{ harvested: number; profit: number }> {
    console.log('[Orchestrator] 🌾 Running startup harvest...');
    const harvestResult = await startupHarvester.harvest(dryRun);
    return { harvested: harvestResult.harvested, profit: harvestResult.totalProfit };
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
