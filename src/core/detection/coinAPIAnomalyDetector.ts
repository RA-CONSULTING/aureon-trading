/**
 * CoinAPI Anomaly Detector
 * Ported from Python ecosystem - detects market manipulation patterns
 */

import { unifiedBus } from '../unifiedBus';
import { temporalLadder, SystemName } from '../temporalLadder';

export type AnomalyType = 
  | 'PRICE_MANIPULATION'
  | 'WASH_TRADING'
  | 'FRONTRUNNING'
  | 'SPOOFING'
  | 'LAYERING'
  | 'PUMP_DUMP'
  | 'FLASH_CRASH'
  | 'ABNORMAL_SPREAD'
  | 'VOLUME_SPIKE'
  | 'ORDER_IMBALANCE';

export interface AnomalyAlert {
  id: string;
  type: AnomalyType;
  symbol: string;
  exchange: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  description: string;
  timestamp: number;
  metrics: {
    priceDeviation?: number;
    volumeMultiplier?: number;
    spreadRatio?: number;
    orderImbalance?: number;
  };
  recommendation: 'AVOID' | 'CAUTION' | 'MONITOR' | 'SAFE';
}

export interface AnomalyDetectorState {
  activeAlerts: AnomalyAlert[];
  detectedCount: Record<AnomalyType, number>;
  lastScanTime: number;
  isScanning: boolean;
  safeSymbols: string[];
  flaggedSymbols: string[];
}

// Detection thresholds from Python
const THRESHOLDS = {
  PRICE_DEVIATION_PCT: 5.0,      // 5% sudden price move
  VOLUME_SPIKE_MULTIPLIER: 10,   // 10x normal volume
  SPREAD_ABNORMAL_RATIO: 3.0,    // Spread 3x normal
  ORDER_IMBALANCE_RATIO: 0.85,   // 85% one-sided orders
  WASH_TRADE_THRESHOLD: 0.9,     // 90% similarity in buy/sell patterns
  PUMP_DUMP_WINDOW_MS: 300000,   // 5 minute window for pump detection
};

class CoinAPIAnomalyDetector {
  private state: AnomalyDetectorState;
  private priceHistory: Map<string, { price: number; volume: number; timestamp: number }[]> = new Map();
  private systemName: SystemName = 'data-ingestion';
  private maxHistoryLength = 100;

  constructor() {
    this.state = {
      activeAlerts: [],
      detectedCount: {
        PRICE_MANIPULATION: 0,
        WASH_TRADING: 0,
        FRONTRUNNING: 0,
        SPOOFING: 0,
        LAYERING: 0,
        PUMP_DUMP: 0,
        FLASH_CRASH: 0,
        ABNORMAL_SPREAD: 0,
        VOLUME_SPIKE: 0,
        ORDER_IMBALANCE: 0,
      },
      lastScanTime: 0,
      isScanning: false,
      safeSymbols: [],
      flaggedSymbols: [],
    };

    console.log('🔍 CoinAPI Anomaly Detector initialized');
  }

  /**
   * Add price data for monitoring
   */
  addPriceData(symbol: string, price: number, volume: number): void {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }

    const history = this.priceHistory.get(symbol)!;
    history.push({ price, volume, timestamp: Date.now() });

    // Trim to max length
    if (history.length > this.maxHistoryLength) {
      history.shift();
    }
  }

  /**
   * Scan for anomalies in all tracked symbols
   */
  async scan(): Promise<AnomalyAlert[]> {
    this.state.isScanning = true;
    this.state.lastScanTime = Date.now();
    const newAlerts: AnomalyAlert[] = [];

    for (const [symbol, history] of this.priceHistory.entries()) {
      if (history.length < 3) continue;

      // Check for price manipulation (sudden large moves)
      const priceAlert = this.detectPriceManipulation(symbol, history);
      if (priceAlert) newAlerts.push(priceAlert);

      // Check for volume spikes
      const volumeAlert = this.detectVolumeSpike(symbol, history);
      if (volumeAlert) newAlerts.push(volumeAlert);

      // Check for pump and dump patterns
      const pumpAlert = this.detectPumpDump(symbol, history);
      if (pumpAlert) newAlerts.push(pumpAlert);

      // Check for flash crash
      const flashAlert = this.detectFlashCrash(symbol, history);
      if (flashAlert) newAlerts.push(flashAlert);
    }

    // Update state
    this.state.activeAlerts = [
      ...this.state.activeAlerts.filter(a => Date.now() - a.timestamp < 300000), // Keep last 5 min
      ...newAlerts,
    ];

    // Update counts
    for (const alert of newAlerts) {
      this.state.detectedCount[alert.type]++;
    }

    // Classify symbols
    this.state.flaggedSymbols = [...new Set(this.state.activeAlerts.map(a => a.symbol))];
    this.state.safeSymbols = [...this.priceHistory.keys()].filter(
      s => !this.state.flaggedSymbols.includes(s)
    );

    this.state.isScanning = false;

    // Publish to bus
    this.publishState();

    return newAlerts;
  }

  /**
   * Detect sudden price manipulation
   */
  private detectPriceManipulation(
    symbol: string, 
    history: { price: number; volume: number; timestamp: number }[]
  ): AnomalyAlert | null {
    const recent = history.slice(-3);
    if (recent.length < 3) return null;

    const priceChange = Math.abs(recent[2].price - recent[0].price) / recent[0].price * 100;

    if (priceChange > THRESHOLDS.PRICE_DEVIATION_PCT) {
      return this.createAlert(
        'PRICE_MANIPULATION',
        symbol,
        priceChange > 10 ? 'HIGH' : 'MEDIUM',
        Math.min(1, priceChange / 20),
        `Sudden ${priceChange.toFixed(2)}% price move detected in ${symbol}`,
        { priceDeviation: priceChange }
      );
    }

    return null;
  }

  /**
   * Detect abnormal volume spikes
   */
  private detectVolumeSpike(
    symbol: string,
    history: { price: number; volume: number; timestamp: number }[]
  ): AnomalyAlert | null {
    if (history.length < 10) return null;

    const avgVolume = history.slice(0, -1).reduce((sum, h) => sum + h.volume, 0) / (history.length - 1);
    const latestVolume = history[history.length - 1].volume;
    const multiplier = latestVolume / (avgVolume || 1);

    if (multiplier > THRESHOLDS.VOLUME_SPIKE_MULTIPLIER) {
      return this.createAlert(
        'VOLUME_SPIKE',
        symbol,
        multiplier > 20 ? 'HIGH' : 'MEDIUM',
        Math.min(1, multiplier / 30),
        `Volume spike ${multiplier.toFixed(1)}x average in ${symbol}`,
        { volumeMultiplier: multiplier }
      );
    }

    return null;
  }

  /**
   * Detect pump and dump patterns
   */
  private detectPumpDump(
    symbol: string,
    history: { price: number; volume: number; timestamp: number }[]
  ): AnomalyAlert | null {
    const windowMs = THRESHOLDS.PUMP_DUMP_WINDOW_MS;
    const now = Date.now();
    
    const recentHistory = history.filter(h => now - h.timestamp < windowMs);
    if (recentHistory.length < 5) return null;

    const prices = recentHistory.map(h => h.price);
    const maxPrice = Math.max(...prices);
    const minPrice = Math.min(...prices);
    const maxIdx = prices.indexOf(maxPrice);
    const currentPrice = prices[prices.length - 1];

    // Check for pump (rapid rise) followed by dump (rapid fall)
    const pumpPct = (maxPrice - minPrice) / minPrice * 100;
    const dumpPct = (maxPrice - currentPrice) / maxPrice * 100;

    if (pumpPct > 15 && dumpPct > 10 && maxIdx < prices.length - 2) {
      return this.createAlert(
        'PUMP_DUMP',
        symbol,
        'CRITICAL',
        Math.min(1, (pumpPct + dumpPct) / 50),
        `Pump (+${pumpPct.toFixed(1)}%) and Dump (-${dumpPct.toFixed(1)}%) pattern detected in ${symbol}`,
        { priceDeviation: pumpPct }
      );
    }

    return null;
  }

  /**
   * Detect flash crash
   */
  private detectFlashCrash(
    symbol: string,
    history: { price: number; volume: number; timestamp: number }[]
  ): AnomalyAlert | null {
    const recent = history.slice(-5);
    if (recent.length < 5) return null;

    // Check for rapid decline followed by quick recovery
    const prices = recent.map(h => h.price);
    const minPrice = Math.min(...prices);
    const startPrice = prices[0];
    const endPrice = prices[prices.length - 1];

    const crashPct = (startPrice - minPrice) / startPrice * 100;
    const recoveryPct = (endPrice - minPrice) / minPrice * 100;

    if (crashPct > 8 && recoveryPct > 5) {
      return this.createAlert(
        'FLASH_CRASH',
        symbol,
        'HIGH',
        Math.min(1, crashPct / 15),
        `Flash crash (-${crashPct.toFixed(1)}%) with ${recoveryPct.toFixed(1)}% recovery in ${symbol}`,
        { priceDeviation: crashPct }
      );
    }

    return null;
  }

  /**
   * Create an anomaly alert
   */
  private createAlert(
    type: AnomalyType,
    symbol: string,
    severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL',
    confidence: number,
    description: string,
    metrics: AnomalyAlert['metrics']
  ): AnomalyAlert {
    const recommendation = 
      severity === 'CRITICAL' ? 'AVOID' :
      severity === 'HIGH' ? 'CAUTION' :
      severity === 'MEDIUM' ? 'MONITOR' : 'SAFE';

    return {
      id: `${type}_${symbol}_${Date.now()}`,
      type,
      symbol,
      exchange: 'binance', // Default, can be extended
      severity,
      confidence,
      description,
      timestamp: Date.now(),
      metrics,
      recommendation,
    };
  }

  /**
   * Check if symbol is safe to trade
   */
  isSymbolSafe(symbol: string): { safe: boolean; alerts: AnomalyAlert[] } {
    const alerts = this.state.activeAlerts.filter(a => a.symbol === symbol);
    const hasCritical = alerts.some(a => a.severity === 'CRITICAL');
    const hasHigh = alerts.some(a => a.severity === 'HIGH');

    return {
      safe: !hasCritical && !hasHigh,
      alerts,
    };
  }

  /**
   * Get current state
   */
  getState(): AnomalyDetectorState {
    return { ...this.state };
  }

  /**
   * Get active alerts
   */
  getActiveAlerts(): AnomalyAlert[] {
    return [...this.state.activeAlerts];
  }

  /**
   * Publish state to UnifiedBus
   */
  private publishState(): void {
    const criticalCount = this.state.activeAlerts.filter(a => a.severity === 'CRITICAL').length;
    const highCount = this.state.activeAlerts.filter(a => a.severity === 'HIGH').length;

    unifiedBus.publish({
      systemName: 'CoinAPIAnomalyDetector',
      timestamp: Date.now(),
      ready: true,
      coherence: criticalCount === 0 && highCount < 3 ? 0.9 : 0.3,
      confidence: 1 - (criticalCount * 0.3 + highCount * 0.1),
      signal: 'NEUTRAL' as const,
      data: {
        activeAlerts: this.state.activeAlerts.length,
        criticalCount,
        highCount,
        safeSymbols: this.state.safeSymbols.length,
        flaggedSymbols: this.state.flaggedSymbols,
        shouldAvoid: criticalCount > 0 || highCount > 2,
      },
    });
  }

  /**
   * Register with Temporal Ladder
   */
  register(): void {
    temporalLadder.registerSystem(this.systemName);
  }
}

export const coinAPIAnomalyDetector = new CoinAPIAnomalyDetector();
