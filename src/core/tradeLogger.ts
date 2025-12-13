// TradeLogger - Comprehensive trade history with frequency band classification
// Phase 5A: Closes the Python ecosystem gap for trade_logger + calibration_trades

import { supabase } from '@/integrations/supabase/client';

export type FrequencyBand = '396Hz' | '432Hz' | '528Hz' | '639Hz' | '741Hz' | '852Hz' | '963Hz' | 'UNKNOWN';

export interface TradeLogEntry {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  entryPrice: number;
  exitPrice?: number;
  entryTime: number;
  exitTime?: number;
  quantity: number;
  positionSizeUsd: number;
  
  // Frequency band classification
  frequencyBand: FrequencyBand;
  prismFrequency: number;
  
  // Quantum state at entry
  coherenceAtEntry: number;
  lambdaAtEntry: number;
  lighthouseConfidence: number;
  hncProbability: number;
  qgitaTier: 1 | 2 | 3;
  
  // Outcome
  pnl?: number;
  pnlPercent?: number;
  isWin?: boolean;
  
  // Metadata
  exchange: string;
  orderId?: string;
  regime: string;
  cosmicPhase?: string;
  isForced?: boolean;
}

export interface PredictionRecord {
  id: string;
  symbol: string;
  predictedDirection: 'UP' | 'DOWN' | 'HOLD';
  actualDirection?: 'UP' | 'DOWN';
  predictedAt: number;
  verifiedAt?: number;
  priceAtPrediction: number;
  priceAtVerification?: number;
  wasCorrect?: boolean;
  confidenceAtPrediction: number;
}

export interface CalibrationData {
  totalTrades: number;
  winRate: number;
  avgPnlPercent: number;
  profitFactor: number;
  bandPerformance: Record<FrequencyBand, { trades: number; winRate: number; avgPnl: number }>;
  tierPerformance: Record<1 | 2 | 3, { trades: number; winRate: number; avgPnl: number }>;
  optimalCoherenceRange: { min: number; max: number };
  bestHours: number[];
  // New: Prediction accuracy tracking
  predictionAccuracy: {
    total: number;
    correct: number;
    accuracy: number;
    byConfidence: Record<string, { total: number; correct: number }>;
  };
}

class TradeLogger {
  private logBuffer: TradeLogEntry[] = [];
  private openPositions: Map<string, TradeLogEntry> = new Map();
  private predictions: PredictionRecord[] = [];
  private pendingPredictions: Map<string, PredictionRecord> = new Map();

  /**
   * Classify frequency into Solfeggio band
   */
  classifyFrequencyBand(frequency: number): FrequencyBand {
    if (frequency < 414) return '396Hz'; // Fear release
    if (frequency < 480) return '432Hz'; // Natural harmony
    if (frequency < 583) return '528Hz'; // Love/DNA repair
    if (frequency < 690) return '639Hz'; // Connection
    if (frequency < 796) return '741Hz'; // Expression
    if (frequency < 907) return '852Hz'; // Intuition
    if (frequency >= 907) return '963Hz'; // Awakening
    return 'UNKNOWN';
  }

  /**
   * Log a new trade entry
   */
  async logEntry(params: {
    symbol: string;
    side: 'BUY' | 'SELL';
    price: number;
    quantity: number;
    positionSizeUsd: number;
    prismFrequency: number;
    coherence: number;
    lambda: number;
    lighthouseConfidence: number;
    hncProbability: number;
    qgitaTier: 1 | 2 | 3;
    exchange: string;
    orderId?: string;
    regime: string;
    cosmicPhase?: string;
    isForced?: boolean;
  }): Promise<TradeLogEntry> {
    const entry: TradeLogEntry = {
      id: crypto.randomUUID(),
      symbol: params.symbol,
      side: params.side,
      entryPrice: params.price,
      entryTime: Date.now(),
      quantity: params.quantity,
      positionSizeUsd: params.positionSizeUsd,
      frequencyBand: this.classifyFrequencyBand(params.prismFrequency),
      prismFrequency: params.prismFrequency,
      coherenceAtEntry: params.coherence,
      lambdaAtEntry: params.lambda,
      lighthouseConfidence: params.lighthouseConfidence,
      hncProbability: params.hncProbability,
      qgitaTier: params.qgitaTier,
      exchange: params.exchange,
      orderId: params.orderId,
      regime: params.regime,
      cosmicPhase: params.cosmicPhase,
      isForced: params.isForced,
    };

    this.openPositions.set(params.symbol, entry);
    this.logBuffer.push(entry);

    // Persist to database
    await this.persistEntry(entry);

    console.log(
      `[TradeLogger] 📝 ENTRY | ${params.side} ${params.symbol} @ ${params.price} | ` +
      `Band: ${entry.frequencyBand} | Tier: ${params.qgitaTier} | Γ: ${params.coherence.toFixed(3)}`
    );

    return entry;
  }

  /**
   * Log trade exit and compute P&L
   */
  async logExit(params: {
    symbol: string;
    exitPrice: number;
    orderId?: string;
  }): Promise<TradeLogEntry | null> {
    const entry = this.openPositions.get(params.symbol);
    if (!entry) {
      console.warn(`[TradeLogger] No open position for ${params.symbol}`);
      return null;
    }

    entry.exitPrice = params.exitPrice;
    entry.exitTime = Date.now();

    // Calculate P&L
    const priceChange = entry.side === 'BUY'
      ? params.exitPrice - entry.entryPrice
      : entry.entryPrice - params.exitPrice;
    
    entry.pnl = priceChange * entry.quantity;
    entry.pnlPercent = (priceChange / entry.entryPrice) * 100;
    entry.isWin = entry.pnl > 0;

    this.openPositions.delete(params.symbol);

    // Update persisted entry
    await this.persistEntry(entry);

    const pnlEmoji = entry.isWin ? '🟢' : '🔴';
    console.log(
      `[TradeLogger] 📝 EXIT | ${params.symbol} @ ${params.exitPrice} | ` +
      `${pnlEmoji} PnL: $${entry.pnl.toFixed(2)} (${entry.pnlPercent.toFixed(2)}%)`
    );

    return entry;
  }

  /**
   * Get trade history
   */
  getHistory(limit: number = 100): TradeLogEntry[] {
    return this.logBuffer.slice(-limit);
  }

  /**
   * Get closed trades only
   */
  getClosedTrades(): TradeLogEntry[] {
    return this.logBuffer.filter(t => t.exitPrice !== undefined);
  }

  /**
   * Export calibration data for learning
   */
  exportCalibration(): CalibrationData {
    const closedTrades = this.getClosedTrades();
    if (closedTrades.length === 0) {
      return {
        totalTrades: 0,
        winRate: 0,
        avgPnlPercent: 0,
        profitFactor: 0,
        bandPerformance: this.initBandPerformance(),
        tierPerformance: { 1: { trades: 0, winRate: 0, avgPnl: 0 }, 2: { trades: 0, winRate: 0, avgPnl: 0 }, 3: { trades: 0, winRate: 0, avgPnl: 0 } },
        optimalCoherenceRange: { min: 0.7, max: 1.0 },
        bestHours: [],
        predictionAccuracy: { total: 0, correct: 0, accuracy: 0, byConfidence: {} },
      };
    }

    const wins = closedTrades.filter(t => t.isWin);
    const losses = closedTrades.filter(t => !t.isWin);
    const totalPnl = closedTrades.reduce((sum, t) => sum + (t.pnlPercent || 0), 0);
    const grossProfit = wins.reduce((sum, t) => sum + (t.pnl || 0), 0);
    const grossLoss = Math.abs(losses.reduce((sum, t) => sum + (t.pnl || 0), 0));

    // Band performance
    const bandPerformance = this.initBandPerformance();
    for (const trade of closedTrades) {
      const band = trade.frequencyBand;
      bandPerformance[band].trades++;
      if (trade.isWin) bandPerformance[band].winRate++;
      bandPerformance[band].avgPnl += trade.pnlPercent || 0;
    }
    for (const band of Object.keys(bandPerformance) as FrequencyBand[]) {
      if (bandPerformance[band].trades > 0) {
        bandPerformance[band].winRate = bandPerformance[band].winRate / bandPerformance[band].trades;
        bandPerformance[band].avgPnl = bandPerformance[band].avgPnl / bandPerformance[band].trades;
      }
    }

    // Tier performance
    const tierPerformance: Record<1 | 2 | 3, { trades: number; winRate: number; avgPnl: number }> = {
      1: { trades: 0, winRate: 0, avgPnl: 0 },
      2: { trades: 0, winRate: 0, avgPnl: 0 },
      3: { trades: 0, winRate: 0, avgPnl: 0 },
    };
    for (const trade of closedTrades) {
      tierPerformance[trade.qgitaTier].trades++;
      if (trade.isWin) tierPerformance[trade.qgitaTier].winRate++;
      tierPerformance[trade.qgitaTier].avgPnl += trade.pnlPercent || 0;
    }
    for (const tier of [1, 2, 3] as (1 | 2 | 3)[]) {
      if (tierPerformance[tier].trades > 0) {
        tierPerformance[tier].winRate = tierPerformance[tier].winRate / tierPerformance[tier].trades;
        tierPerformance[tier].avgPnl = tierPerformance[tier].avgPnl / tierPerformance[tier].trades;
      }
    }

    // Optimal coherence range (based on winning trades)
    const winningCoherences = wins.map(t => t.coherenceAtEntry).sort((a, b) => a - b);
    const optimalCoherenceRange = winningCoherences.length >= 3
      ? { min: winningCoherences[Math.floor(winningCoherences.length * 0.25)], max: winningCoherences[Math.floor(winningCoherences.length * 0.75)] }
      : { min: 0.7, max: 1.0 };

    // Best trading hours
    const hourCounts: Record<number, { wins: number; total: number }> = {};
    for (const trade of closedTrades) {
      const hour = new Date(trade.entryTime).getHours();
      if (!hourCounts[hour]) hourCounts[hour] = { wins: 0, total: 0 };
      hourCounts[hour].total++;
      if (trade.isWin) hourCounts[hour].wins++;
    }
    const bestHours = Object.entries(hourCounts)
      .filter(([, v]) => v.total >= 3 && v.wins / v.total >= 0.55)
      .map(([h]) => parseInt(h))
      .sort((a, b) => a - b);

    // Prediction accuracy
    const verifiedPredictions = this.predictions.filter(p => p.wasCorrect !== undefined);
    const correctPredictions = verifiedPredictions.filter(p => p.wasCorrect);
    const byConfidence: Record<string, { total: number; correct: number }> = {};
    for (const pred of verifiedPredictions) {
      const bucket = pred.confidenceAtPrediction >= 0.8 ? 'high' : pred.confidenceAtPrediction >= 0.6 ? 'medium' : 'low';
      if (!byConfidence[bucket]) byConfidence[bucket] = { total: 0, correct: 0 };
      byConfidence[bucket].total++;
      if (pred.wasCorrect) byConfidence[bucket].correct++;
    }

    return {
      totalTrades: closedTrades.length,
      winRate: wins.length / closedTrades.length,
      avgPnlPercent: totalPnl / closedTrades.length,
      profitFactor: grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? Infinity : 0,
      bandPerformance,
      tierPerformance,
      optimalCoherenceRange,
      bestHours,
      predictionAccuracy: {
        total: verifiedPredictions.length,
        correct: correctPredictions.length,
        accuracy: verifiedPredictions.length > 0 ? correctPredictions.length / verifiedPredictions.length : 0,
        byConfidence,
      },
    };
  }

  private initBandPerformance(): Record<FrequencyBand, { trades: number; winRate: number; avgPnl: number }> {
    return {
      '396Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '432Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '528Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '639Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '741Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '852Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      '963Hz': { trades: 0, winRate: 0, avgPnl: 0 },
      'UNKNOWN': { trades: 0, winRate: 0, avgPnl: 0 },
    };
  }

  private async persistEntry(entry: TradeLogEntry): Promise<void> {
    try {
      const { error } = await supabase.from('trade_audit_log' as any).upsert({
        id: entry.id,
        symbol: entry.symbol,
        side: entry.side,
        entry_price: entry.entryPrice,
        exit_price: entry.exitPrice,
        entry_time: new Date(entry.entryTime).toISOString(),
        exit_time: entry.exitTime ? new Date(entry.exitTime).toISOString() : null,
        quantity: entry.quantity,
        position_size_usd: entry.positionSizeUsd,
        frequency_band: entry.frequencyBand,
        prism_frequency: entry.prismFrequency,
        coherence_at_entry: entry.coherenceAtEntry,
        lambda_at_entry: entry.lambdaAtEntry,
        lighthouse_confidence: entry.lighthouseConfidence,
        hnc_probability: entry.hncProbability,
        qgita_tier: entry.qgitaTier,
        pnl: entry.pnl,
        pnl_percent: entry.pnlPercent,
        is_win: entry.isWin,
        exchange: entry.exchange,
        order_id: entry.orderId,
        regime: entry.regime,
        cosmic_phase: entry.cosmicPhase,
        is_forced: entry.isForced,
      });

      if (error) {
        console.warn('[TradeLogger] Persist warning:', error.message);
      }
    } catch (err) {
      console.warn('[TradeLogger] Persist error:', err);
    }
  }

  /**
   * Load history from database
   */
  async loadFromDatabase(limit: number = 500): Promise<void> {
    try {
      const { data, error } = await supabase
        .from('trade_audit_log' as any)
        .select('*')
        .order('entry_time', { ascending: false })
        .limit(limit);

      if (error) {
        console.warn('[TradeLogger] Load warning:', error.message);
        return;
      }

      if (data && Array.isArray(data)) {
        this.logBuffer = data.map((row: any) => ({
          id: row.id,
          symbol: row.symbol,
          side: row.side,
          entryPrice: row.entry_price,
          exitPrice: row.exit_price,
          entryTime: new Date(row.entry_time).getTime(),
          exitTime: row.exit_time ? new Date(row.exit_time).getTime() : undefined,
          quantity: row.quantity,
          positionSizeUsd: row.position_size_usd,
          frequencyBand: row.frequency_band,
          prismFrequency: row.prism_frequency,
          coherenceAtEntry: row.coherence_at_entry,
          lambdaAtEntry: row.lambda_at_entry,
          lighthouseConfidence: row.lighthouse_confidence,
          hncProbability: row.hnc_probability,
          qgitaTier: row.qgita_tier,
          pnl: row.pnl,
          pnlPercent: row.pnl_percent,
          isWin: row.is_win,
          exchange: row.exchange,
          orderId: row.order_id,
          regime: row.regime,
          cosmicPhase: row.cosmic_phase,
          isForced: row.is_forced,
        })).reverse();
        console.log(`[TradeLogger] Loaded ${this.logBuffer.length} trades from database`);
      }
    } catch (err) {
      console.warn('[TradeLogger] Load error:', err);
    }
  }
}

export const tradeLogger = new TradeLogger();
