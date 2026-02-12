/**
 * Prediction Accuracy Tracker
 * Records forecasts and validates against actual price movements
 * 
 * Gap Closure: Implements Python's prediction_validator.py functionality
 */

import { supabase } from '@/integrations/supabase/client';
import { unifiedBus } from './unifiedBus';

export interface PredictionRecord {
  id: string;
  symbol: string;
  timestamp: number;
  
  // Prediction details
  predictedDirection: 'UP' | 'DOWN' | 'NEUTRAL';
  predictedConfidence: number;
  priceAtPrediction: number;
  
  // H+1 forecast from probability matrix
  h1Probability: number;
  h1State: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  
  // Validation (filled after validation window)
  priceAfter1m?: number;
  priceAfter5m?: number;
  priceAfter15m?: number;
  actualDirection1m?: 'UP' | 'DOWN' | 'NEUTRAL';
  actualDirection5m?: 'UP' | 'DOWN' | 'NEUTRAL';
  actualDirection15m?: 'UP' | 'DOWN' | 'NEUTRAL';
  isAccurate1m?: boolean;
  isAccurate5m?: boolean;
  isAccurate15m?: boolean;
  validatedAt?: number;
}

export interface AccuracyStats {
  totalPredictions: number;
  validated: number;
  accuracy1m: number;
  accuracy5m: number;
  accuracy15m: number;
  avgConfidenceWhenCorrect: number;
  avgConfidenceWhenWrong: number;
  bestPerformingSymbol: string | null;
  worstPerformingSymbol: string | null;
}

const VALIDATION_WINDOWS = {
  '1m': 60 * 1000,
  '5m': 5 * 60 * 1000,
  '15m': 15 * 60 * 1000,
};

const MIN_PRICE_MOVE_PCT = 0.0001; // 0.01% threshold to count as directional move

class PredictionAccuracyTracker {
  private predictions: Map<string, PredictionRecord> = new Map();
  private pendingValidations: PredictionRecord[] = [];
  private validationInterval: NodeJS.Timeout | null = null;
  private isRunning: boolean = false;

  constructor() {
    console.log('🔮 Prediction Accuracy Tracker initialized');
  }

  /**
   * Start the validation loop
   */
  start(): void {
    if (this.isRunning) return;
    
    this.isRunning = true;
    
    // Check for validations every 30 seconds
    this.validationInterval = setInterval(() => {
      this.processValidations().catch(console.error);
    }, 30000);
    
    console.log('[PredictionTracker] Started validation loop');
  }

  /**
   * Stop the validation loop
   */
  stop(): void {
    if (this.validationInterval) {
      clearInterval(this.validationInterval);
      this.validationInterval = null;
    }
    this.isRunning = false;
  }

  /**
   * Record a new prediction
   */
  async recordPrediction(params: {
    symbol: string;
    predictedDirection: 'UP' | 'DOWN' | 'NEUTRAL';
    predictedConfidence: number;
    currentPrice: number;
    h1Probability: number;
    h1State: 'BULLISH' | 'BEARISH' | 'NEUTRAL';
  }): Promise<PredictionRecord> {
    const record: PredictionRecord = {
      id: crypto.randomUUID(),
      symbol: params.symbol,
      timestamp: Date.now(),
      predictedDirection: params.predictedDirection,
      predictedConfidence: params.predictedConfidence,
      priceAtPrediction: params.currentPrice,
      h1Probability: params.h1Probability,
      h1State: params.h1State,
    };

    this.predictions.set(record.id, record);
    this.pendingValidations.push(record);

    // Persist to database
    await this.persistPrediction(record);

    console.log(
      `[PredictionTracker] 📝 ${params.predictedDirection} ${params.symbol} @ $${params.currentPrice.toFixed(2)} | ` +
      `Conf: ${(params.predictedConfidence * 100).toFixed(1)}% | H+1: ${params.h1State}`
    );

    return record;
  }

  /**
   * Process pending validations
   */
  private async processValidations(): Promise<void> {
    const now = Date.now();
    const toValidate = this.pendingValidations.filter(p => {
      const age = now - p.timestamp;
      // Keep in pending until 15m validation is complete
      return age < VALIDATION_WINDOWS['15m'] + 60000;
    });

    for (const prediction of toValidate) {
      await this.validatePrediction(prediction, now);
    }

    // Remove fully validated predictions from pending
    this.pendingValidations = this.pendingValidations.filter(p => {
      return !p.validatedAt || now - p.timestamp < VALIDATION_WINDOWS['15m'];
    });

    // Publish accuracy stats to bus
    this.publishAccuracyStats();
  }

  /**
   * Validate a prediction against current price
   */
  private async validatePrediction(prediction: PredictionRecord, now: number): Promise<void> {
    const age = now - prediction.timestamp;
    
    // Get current price from ticker cache via edge function
    const currentPrice = await this.fetchCurrentPrice(prediction.symbol);
    if (!currentPrice) return;

    const priceDiff = currentPrice - prediction.priceAtPrediction;
    const priceDiffPct = priceDiff / prediction.priceAtPrediction;

    const getActualDirection = (): 'UP' | 'DOWN' | 'NEUTRAL' => {
      if (Math.abs(priceDiffPct) < MIN_PRICE_MOVE_PCT) return 'NEUTRAL';
      return priceDiff > 0 ? 'UP' : 'DOWN';
    };

    const isAccurate = (actual: 'UP' | 'DOWN' | 'NEUTRAL'): boolean => {
      if (prediction.predictedDirection === 'NEUTRAL') return actual === 'NEUTRAL';
      return prediction.predictedDirection === actual;
    };

    // 1-minute validation
    if (age >= VALIDATION_WINDOWS['1m'] && prediction.priceAfter1m === undefined) {
      prediction.priceAfter1m = currentPrice;
      prediction.actualDirection1m = getActualDirection();
      prediction.isAccurate1m = isAccurate(prediction.actualDirection1m);
      console.log(`[PredictionTracker] 1m validation: ${prediction.symbol} | Predicted: ${prediction.predictedDirection} | Actual: ${prediction.actualDirection1m} | ✓: ${prediction.isAccurate1m}`);
    }

    // 5-minute validation
    if (age >= VALIDATION_WINDOWS['5m'] && prediction.priceAfter5m === undefined) {
      prediction.priceAfter5m = currentPrice;
      prediction.actualDirection5m = getActualDirection();
      prediction.isAccurate5m = isAccurate(prediction.actualDirection5m);
      console.log(`[PredictionTracker] 5m validation: ${prediction.symbol} | Predicted: ${prediction.predictedDirection} | Actual: ${prediction.actualDirection5m} | ✓: ${prediction.isAccurate5m}`);
    }

    // 15-minute validation (final)
    if (age >= VALIDATION_WINDOWS['15m'] && prediction.priceAfter15m === undefined) {
      prediction.priceAfter15m = currentPrice;
      prediction.actualDirection15m = getActualDirection();
      prediction.isAccurate15m = isAccurate(prediction.actualDirection15m);
      prediction.validatedAt = now;
      
      console.log(`[PredictionTracker] ✅ 15m FINAL: ${prediction.symbol} | Predicted: ${prediction.predictedDirection} | Actual: ${prediction.actualDirection15m} | ✓: ${prediction.isAccurate15m}`);
      
      // Update database with final validation
      await this.updatePredictionValidation(prediction);
    }

    this.predictions.set(prediction.id, prediction);
  }

  /**
   * Fetch current price for a symbol
   */
  private async fetchCurrentPrice(symbol: string): Promise<number | null> {
    try {
      const { data } = await supabase.functions.invoke('fetch-binance-market-data', {
        body: { symbol }
      });
      return data?.price || null;
    } catch (err) {
      console.warn('[PredictionTracker] Failed to fetch price:', err);
      return null;
    }
  }

  /**
   * Get accuracy statistics
   */
  getStats(): AccuracyStats {
    const allPredictions = Array.from(this.predictions.values());
    const validated = allPredictions.filter(p => p.validatedAt !== undefined);

    if (validated.length === 0) {
      return {
        totalPredictions: allPredictions.length,
        validated: 0,
        accuracy1m: 0,
        accuracy5m: 0,
        accuracy15m: 0,
        avgConfidenceWhenCorrect: 0,
        avgConfidenceWhenWrong: 0,
        bestPerformingSymbol: null,
        worstPerformingSymbol: null,
      };
    }

    const accurate1m = validated.filter(p => p.isAccurate1m).length;
    const accurate5m = validated.filter(p => p.isAccurate5m).length;
    const accurate15m = validated.filter(p => p.isAccurate15m).length;

    const correctPredictions = validated.filter(p => p.isAccurate15m);
    const wrongPredictions = validated.filter(p => p.isAccurate15m === false);

    const avgConfidenceWhenCorrect = correctPredictions.length > 0
      ? correctPredictions.reduce((sum, p) => sum + p.predictedConfidence, 0) / correctPredictions.length
      : 0;

    const avgConfidenceWhenWrong = wrongPredictions.length > 0
      ? wrongPredictions.reduce((sum, p) => sum + p.predictedConfidence, 0) / wrongPredictions.length
      : 0;

    // Calculate per-symbol performance
    const symbolStats: Record<string, { correct: number; total: number }> = {};
    for (const p of validated) {
      if (!symbolStats[p.symbol]) symbolStats[p.symbol] = { correct: 0, total: 0 };
      symbolStats[p.symbol].total++;
      if (p.isAccurate15m) symbolStats[p.symbol].correct++;
    }

    const symbolPerformance = Object.entries(symbolStats)
      .filter(([, s]) => s.total >= 3) // Need at least 3 predictions
      .map(([symbol, s]) => ({ symbol, accuracy: s.correct / s.total }))
      .sort((a, b) => b.accuracy - a.accuracy);

    return {
      totalPredictions: allPredictions.length,
      validated: validated.length,
      accuracy1m: accurate1m / validated.length,
      accuracy5m: accurate5m / validated.length,
      accuracy15m: accurate15m / validated.length,
      avgConfidenceWhenCorrect,
      avgConfidenceWhenWrong,
      bestPerformingSymbol: symbolPerformance[0]?.symbol || null,
      worstPerformingSymbol: symbolPerformance[symbolPerformance.length - 1]?.symbol || null,
    };
  }

  /**
   * Publish accuracy stats to UnifiedBus
   */
  private publishAccuracyStats(): void {
    const stats = this.getStats();

    unifiedBus.publish({
      systemName: 'PredictionAccuracy',
      timestamp: Date.now(),
      ready: stats.validated > 0,
      coherence: stats.accuracy15m,
      confidence: stats.validated / Math.max(stats.totalPredictions, 1),
      signal: stats.accuracy15m >= 0.55 ? 'BUY' : stats.accuracy15m <= 0.45 ? 'SELL' : 'NEUTRAL',
      data: stats,
    });

    // Feed accuracy data to Autonomy Hub bridge (closes the feedback loop)
    try {
      if (typeof globalThis !== 'undefined') {
        (globalThis as any).__predictionAccuracyFeedback = {
          timestamp: Date.now(),
          accuracy1m: stats.accuracy1m ?? 0,
          accuracy5m: stats.accuracy5m ?? 0,
          accuracy15m: stats.accuracy15m ?? 0,
          totalPredictions: stats.totalPredictions ?? 0,
          validated: stats.validated ?? 0,
          signal: stats.accuracy15m >= 0.55 ? 'BUY' : stats.accuracy15m <= 0.45 ? 'SELL' : 'NEUTRAL',
        };
      }
    } catch {
      // Hub bridge not available
    }
  }

  /**
   * Persist prediction to database
   */
  private async persistPrediction(prediction: PredictionRecord): Promise<void> {
    try {
      await supabase.from('decision_audit_log').insert({
        id: prediction.id,
        symbol: prediction.symbol,
        decision_timestamp: new Date(prediction.timestamp).toISOString(),
        decision_action: prediction.predictedDirection,
        coherence: prediction.predictedConfidence,
        confidence: prediction.predictedConfidence,
        lambda: prediction.h1Probability,
        user_id: (await supabase.auth.getUser()).data.user?.id || 'system',
        price_at_decision: prediction.priceAtPrediction,
        probability_fused: prediction.h1Probability,
      });
    } catch (err) {
      console.warn('[PredictionTracker] Persist failed:', err);
    }
  }

  /**
   * Update prediction with validation results
   */
  private async updatePredictionValidation(prediction: PredictionRecord): Promise<void> {
    try {
      await supabase.from('decision_audit_log').update({
        price_after_1m: prediction.priceAfter1m,
        price_after_5m: prediction.priceAfter5m,
        price_after_15m: prediction.priceAfter15m,
        actual_direction_1m: prediction.actualDirection1m,
        actual_direction_5m: prediction.actualDirection5m,
        actual_direction_15m: prediction.actualDirection15m,
        accuracy_1m: prediction.isAccurate1m,
        accuracy_5m: prediction.isAccurate5m,
        accuracy_15m: prediction.isAccurate15m,
        verified_at: new Date().toISOString(),
      }).eq('id', prediction.id);
    } catch (err) {
      console.warn('[PredictionTracker] Update validation failed:', err);
    }
  }

  /**
   * Load recent predictions from database
   */
  async loadFromDatabase(limit: number = 100): Promise<void> {
    try {
      const { data, error } = await supabase
        .from('decision_audit_log')
        .select('*')
        .order('decision_timestamp', { ascending: false })
        .limit(limit);

      if (error) throw error;

      if (data) {
        for (const row of data) {
          const prediction: PredictionRecord = {
            id: row.id,
            symbol: row.symbol,
            timestamp: new Date(row.decision_timestamp).getTime(),
            predictedDirection: row.decision_action as 'UP' | 'DOWN' | 'NEUTRAL',
            predictedConfidence: row.confidence,
            priceAtPrediction: row.price_at_decision || 0,
            h1Probability: row.probability_fused || 0.5,
            h1State: 'NEUTRAL',
          priceAfter1m: row.price_after_1m,
          priceAfter5m: row.price_after_5m,
          priceAfter15m: row.price_after_15m,
          actualDirection1m: row.actual_direction_1m as 'UP' | 'DOWN' | 'NEUTRAL' | undefined,
          actualDirection5m: row.actual_direction_5m as 'UP' | 'DOWN' | 'NEUTRAL' | undefined,
          actualDirection15m: row.actual_direction_15m as 'UP' | 'DOWN' | 'NEUTRAL' | undefined,
          isAccurate1m: row.accuracy_1m,
          isAccurate5m: row.accuracy_5m,
          isAccurate15m: row.accuracy_15m,
          validatedAt: row.verified_at ? new Date(row.verified_at).getTime() : undefined,
        };
          this.predictions.set(prediction.id, prediction);
        }
        console.log(`[PredictionTracker] Loaded ${data.length} predictions from database`);
      }
    } catch (err) {
      console.warn('[PredictionTracker] Load failed:', err);
    }
  }
}

export const predictionAccuracyTracker = new PredictionAccuracyTracker();
