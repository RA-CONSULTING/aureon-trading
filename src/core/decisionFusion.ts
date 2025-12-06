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
}

export interface DecisionFusionConfig {
  buyThreshold: number;
  sellThreshold: number;
  weights: {
    ensemble: number;
    sentiment: number;
    qgita: number;
    harmonic6D: number; // NEW: 15% weight for 6D Harmonic
  };
  minimumConfidence: number;
}

const DEFAULT_CONFIG: DecisionFusionConfig = {
  buyThreshold: 0.15,
  sellThreshold: -0.15,
  weights: {
    ensemble: 0.50,   // Reduced from 0.60
    sentiment: 0.15,  // Reduced from 0.20
    qgita: 0.20,      // Unchanged
    harmonic6D: 0.15, // NEW: 6D Harmonic weight
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
    probabilityFusion?: ProbabilityFusion | null
  ): DecisionSignal {
    const models: EnsembleModel[] = ['lstm', 'randomForest', 'xgboost', 'transformer'];
    const modelSignals = models.map(model => generateModelSignal(model, snapshot));

    const aggregateScore = modelSignals.reduce((acc, signal) => acc + signal.score * signal.confidence, 0);
    const totalConfidence = modelSignals.reduce((acc, signal) => acc + signal.confidence, 0);
    const normalizedScore = totalConfidence === 0 ? 0 : aggregateScore / totalConfidence;

    const sentimentScore = snapshot.sentiment.reduce((acc, s) => acc + s.score, 0) / snapshot.sentiment.length;
    const qgitaBoost = lighthouseEvent ? lighthouseEvent.confidence * (lighthouseEvent.direction === 'long' ? 1 : -1) : 0;

    // 6D Harmonic probability integration
    // Convert probability (0-1) to score (-1 to +1)
    const raw6DProb = probabilityFusion?.fusedProbability ?? 0.5;
    const harmonic6DScore = (raw6DProb - 0.5) * 2; // Maps 0→-1, 0.5→0, 1→+1
    
    // Apply harmonic lock boost when aligned to 528 Hz
    const harmonicLock = probabilityFusion?.harmonicLock ?? false;
    const lockBoost = harmonicLock ? 0.1 : 0;
    const boosted6DScore = harmonic6DScore + (harmonic6DScore > 0 ? lockBoost : -lockBoost);
    
    // Extract wave state for dynamic thresholds
    const waveState = probabilityFusion?.waveState ?? 'RESONANT';

    // Normalize weights
    const weights = this.config.weights;
    const weightTotal = weights.ensemble + weights.sentiment + weights.qgita + weights.harmonic6D;
    const normalizedWeights = {
      ensemble: weights.ensemble / weightTotal,
      sentiment: weights.sentiment / weightTotal,
      qgita: weights.qgita / weightTotal,
      harmonic6D: weights.harmonic6D / weightTotal,
    };

    // Calculate final score with 6D contribution
    const finalScore =
      normalizedScore * normalizedWeights.ensemble +
      sentimentScore * normalizedWeights.sentiment +
      qgitaBoost * normalizedWeights.qgita +
      boosted6DScore * normalizedWeights.harmonic6D;

    // Dynamic thresholds based on 6D wave state
    let buyThreshold = this.config.buyThreshold;
    let sellThreshold = this.config.sellThreshold;

    if (waveState === 'CRYSTALLINE') {
      // Tighter thresholds when 6D is highly aligned - more confident
      buyThreshold *= 0.8;
      sellThreshold *= 0.8;
    } else if (waveState === 'CHAOTIC') {
      // Wider thresholds in chaos - require stronger signal
      buyThreshold *= 1.5;
      sellThreshold *= 1.5;
    }
    // RESONANT uses default thresholds

    let action: DecisionAction = 'hold';
    if (finalScore > buyThreshold) {
      action = 'buy';
    } else if (finalScore < sellThreshold) {
      action = 'sell';
    }

    const baseSize = Math.min(1, Math.abs(finalScore));
    const qgitaConfidence = lighthouseEvent?.confidence ?? 0.4;
    
    // Boost confidence when 6D is in crystalline state
    const crystallineBoost = waveState === 'CRYSTALLINE' ? 0.1 : 0;
    const combinedConfidence = Math.max(
      this.config.minimumConfidence,
      Math.min(1, Math.abs(finalScore) + qgitaConfidence * normalizedWeights.qgita + crystallineBoost)
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
    } satisfies DecisionSignal;
  }
}
