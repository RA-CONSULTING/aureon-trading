import { DataIngestionSnapshot } from './dataIngestion';
import { LighthouseEvent } from './qgitaEngine';
import type { ProbabilityFusion } from './enhanced6DProbabilityMatrix';

type DecisionAction = 'buy' | 'sell' | 'hold';

type EnsembleModel = 'lstm' | 'randomForest' | 'xgboost' | 'transformer';

export interface ModelSignal {
  model: EnsembleModel;
  score: number;
  confidence: number;
}

/** Autonomy Hub consensus signal from Python backend (The Big Wheel) */
export interface AutonomyHubSignal {
  direction: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  confidence: number;      // 0-1
  strength: number;        // -1 to +1
  rollingWinRate: number;  // 0-1 from feedback loop
  numPredictors: number;
  agreementRatio: number;
}

export interface DecisionSignal {
  action: DecisionAction;
  positionSize: number;
  confidence: number;
  modelSignals: ModelSignal[];
  sentimentScore: number;
  // 6D Harmonic fields
  harmonic6DScore: number;
  waveState: string;
  harmonicLock: boolean;
  // Autonomy Hub integration
  autonomyHubAligned: boolean;
}

export interface DecisionFusionConfig {
  buyThreshold: number;
  sellThreshold: number;
  weights: {
    ensemble: number;
    sentiment: number;
    qgita: number;
    harmonic6D: number;
    autonomyHub: number; // Big Wheel consensus from Python backend
  };
  minimumConfidence: number;
}

const DEFAULT_CONFIG: DecisionFusionConfig = {
  buyThreshold: 0.15,
  sellThreshold: -0.15,
  weights: {
    ensemble: 0.40,     // Reduced to make room for autonomy hub
    sentiment: 0.10,
    qgita: 0.15,
    harmonic6D: 0.10,
    autonomyHub: 0.25,  // Big Wheel: 25% weight (highest after ensemble)
  },
  minimumConfidence: 0.35,
};

const generateModelSignal = (model: EnsembleModel, snapshot: DataIngestionSnapshot): ModelSignal => {
  const trend = snapshot.consolidatedOHLCV.close - snapshot.consolidatedOHLCV.open;
  const volatility = snapshot.consolidatedOHLCV.high - snapshot.consolidatedOHLCV.low;
  const sentiment = snapshot.sentiment.reduce((acc, s) => acc + s.score, 0) / snapshot.sentiment.length;
  const normalizedTrend = Math.tanh(trend / Math.max(1, volatility));
  const baseConfidence = 0.4 + Math.random() * 0.5;

  const bias = model === 'lstm' ? 0.2 : model === 'randomForest' ? -0.1 : model === 'xgboost' ? 0.1 : 0;
  const score = normalizedTrend + sentiment * 0.2 + bias + (Math.random() - 0.5) * 0.1;

  return {
    model,
    score,
    confidence: Math.max(0.2, Math.min(0.95, baseConfidence - Math.abs(score) * 0.1)),
  } satisfies ModelSignal;
};

export class DecisionFusionLayer {
  private readonly config: DecisionFusionConfig;

  constructor(config: Partial<DecisionFusionConfig> = {}) {
    this.config = {
      ...DEFAULT_CONFIG,
      ...config,
      weights: { ...DEFAULT_CONFIG.weights, ...(config.weights ?? {}) },
    } satisfies DecisionFusionConfig;
  }

  decide(
    snapshot: DataIngestionSnapshot,
    lighthouseEvent: LighthouseEvent | null,
    probabilityFusion?: ProbabilityFusion | null,
    autonomyHubSignal?: AutonomyHubSignal | null
  ): DecisionSignal {
    const models: EnsembleModel[] = ['lstm', 'randomForest', 'xgboost', 'transformer'];
    const modelSignals = models.map(model => generateModelSignal(model, snapshot));

    const aggregateScore = modelSignals.reduce((acc, signal) => acc + signal.score * signal.confidence, 0);
    const totalConfidence = modelSignals.reduce((acc, signal) => acc + signal.confidence, 0);
    const normalizedScore = totalConfidence === 0 ? 0 : aggregateScore / totalConfidence;

    const sentimentScore = snapshot.sentiment.reduce((acc, s) => acc + s.score, 0) / snapshot.sentiment.length;
    const qgitaBoost = lighthouseEvent ? lighthouseEvent.confidence * (lighthouseEvent.direction === 'long' ? 1 : -1) : 0;

    // 6D Harmonic probability integration
    const raw6DProb = probabilityFusion?.fusedProbability ?? 0.5;
    const harmonic6DScore = (raw6DProb - 0.5) * 2;
    const harmonicLock = probabilityFusion?.harmonicLock ?? false;
    const lockBoost = harmonicLock ? 0.1 : 0;
    const boosted6DScore = harmonic6DScore + (harmonic6DScore > 0 ? lockBoost : -lockBoost);
    const waveState = probabilityFusion?.waveState ?? 'RESONANT';

    // Autonomy Hub integration (The Big Wheel - Python backend consensus)
    // Converts hub consensus into a -1 to +1 score weighted by confidence and rolling win rate
    let autonomyHubScore = 0;
    let autonomyHubAligned = false;
    if (autonomyHubSignal && autonomyHubSignal.direction !== 'NEUTRAL') {
      const directionMult = autonomyHubSignal.direction === 'BULLISH' ? 1 : -1;
      // Scale by confidence AND rolling win rate (proven accuracy amplifies signal)
      const winRateBoost = Math.max(0.5, autonomyHubSignal.rollingWinRate);
      autonomyHubScore = autonomyHubSignal.strength * autonomyHubSignal.confidence * winRateBoost * directionMult;

      // Check alignment: hub agrees with ensemble direction
      const ensembleDir = normalizedScore > 0 ? 'BULLISH' : normalizedScore < 0 ? 'BEARISH' : 'NEUTRAL';
      autonomyHubAligned = autonomyHubSignal.direction === ensembleDir;
    }

    // Normalize weights (now includes autonomy hub)
    const weights = this.config.weights;
    const weightTotal = weights.ensemble + weights.sentiment + weights.qgita + weights.harmonic6D + weights.autonomyHub;
    const normalizedWeights = {
      ensemble: weights.ensemble / weightTotal,
      sentiment: weights.sentiment / weightTotal,
      qgita: weights.qgita / weightTotal,
      harmonic6D: weights.harmonic6D / weightTotal,
      autonomyHub: weights.autonomyHub / weightTotal,
    };

    // Calculate final score with ALL contributions including Big Wheel
    const finalScore =
      normalizedScore * normalizedWeights.ensemble +
      sentimentScore * normalizedWeights.sentiment +
      qgitaBoost * normalizedWeights.qgita +
      boosted6DScore * normalizedWeights.harmonic6D +
      autonomyHubScore * normalizedWeights.autonomyHub;

    // Dynamic thresholds based on 6D wave state
    let buyThreshold = this.config.buyThreshold;
    let sellThreshold = this.config.sellThreshold;

    if (waveState === 'CRYSTALLINE') {
      buyThreshold *= 0.8;
      sellThreshold *= 0.8;
    } else if (waveState === 'CHAOTIC') {
      buyThreshold *= 1.5;
      sellThreshold *= 1.5;
    }

    // Autonomy Hub alignment bonus: tighter thresholds when Big Wheel agrees
    if (autonomyHubAligned && autonomyHubSignal && autonomyHubSignal.agreementRatio > 0.7) {
      buyThreshold *= 0.9;
      sellThreshold *= 0.9;
    }

    let action: DecisionAction = 'hold';
    if (finalScore > buyThreshold) {
      action = 'buy';
    } else if (finalScore < sellThreshold) {
      action = 'sell';
    }

    const baseSize = Math.min(1, Math.abs(finalScore));
    const qgitaConfidence = lighthouseEvent?.confidence ?? 0.4;

    const crystallineBoost = waveState === 'CRYSTALLINE' ? 0.1 : 0;
    const hubBoost = autonomyHubAligned ? 0.05 : 0;
    const combinedConfidence = Math.max(
      this.config.minimumConfidence,
      Math.min(1, Math.abs(finalScore) + qgitaConfidence * normalizedWeights.qgita + crystallineBoost + hubBoost)
    );

    return {
      action,
      positionSize: Number((baseSize * (0.5 + qgitaConfidence)).toFixed(3)),
      confidence: combinedConfidence,
      modelSignals,
      sentimentScore,
      harmonic6DScore: boosted6DScore,
      waveState,
      harmonicLock,
      autonomyHubAligned,
    } satisfies DecisionSignal;
  }
}
