/**
 * 🔍 COINAPI ANOMALY DETECTOR
 * 
 * Detects wash trading, pump & dump schemes, and other
 * market manipulation patterns for signal filtering.
 */

import { unifiedBus, type SystemState } from './unifiedBus';
import { temporalLadder } from './temporalLadder';

export enum AnomalyType {
  WASH_TRADING = 'WASH_TRADING',
  PUMP_AND_DUMP = 'PUMP_AND_DUMP',
  SPOOFING = 'SPOOFING',
  LAYERING = 'LAYERING',
  VOLUME_SPIKE = 'VOLUME_SPIKE',
  PRICE_MANIPULATION = 'PRICE_MANIPULATION',
  WHALE_ACTIVITY = 'WHALE_ACTIVITY',
  NONE = 'NONE'
}

export interface Anomaly {
  type: AnomalyType;
  symbol: string;
  severity: number; // 0-1
  timestamp: number;
  description: string;
  recommendation: 'BLACKLIST' | 'REDUCE_SIZE' | 'MONITOR' | 'IGNORE';
  duration?: number; // How long to apply recommendation
}

export interface AnomalyDetectorState {
  anomalies: Anomaly[];
  blacklistedSymbols: Set<string>;
  reducedSymbols: Map<string, number>; // symbol -> reduction factor
  overallMarketHealth: number;
  lastScan: number;
}

export class CoinAPIAnomalyDetector {
  private anomalies: Anomaly[] = [];
  private blacklist: Map<string, number> = new Map(); // symbol -> expiry timestamp
  private reducedSymbols: Map<string, { factor: number; expiry: number }> = new Map();
  private priceHistory: Map<string, number[]> = new Map();
  private volumeHistory: Map<string, number[]> = new Map();
  private registered = false;
  
  // Configuration
  private readonly blacklistDuration = 3600 * 1000; // 1 hour in ms
  private readonly minSeverity = 0.4;
  private readonly volumeSpikeThreshold = 5.0; // 5x normal volume
  private readonly priceManipulationThreshold = 0.1; // 10% sudden move
  
  constructor() {}
  
  register(): void {
    if (this.registered) return;
    
    temporalLadder.registerSystem('anomaly-detector');
    
    // Start heartbeat
    setInterval(() => {
      temporalLadder.heartbeat('anomaly-detector', this.getMarketHealth());
    }, 5000);
    
    this.registered = true;
    console.log('🔍 CoinAPI Anomaly Detector registered');
  }
  
  addDataPoint(symbol: string, price: number, volume: number): void {
    // Update price history
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }
    const prices = this.priceHistory.get(symbol)!;
    prices.push(price);
    if (prices.length > 100) prices.shift();
    
    // Update volume history
    if (!this.volumeHistory.has(symbol)) {
      this.volumeHistory.set(symbol, []);
    }
    const volumes = this.volumeHistory.get(symbol)!;
    volumes.push(volume);
    if (volumes.length > 100) volumes.shift();
  }
  
  scan(): Anomaly[] {
    const now = Date.now();
    this.anomalies = [];
    
    // Clean expired blacklist entries
    for (const [symbol, expiry] of this.blacklist) {
      if (now > expiry) {
        this.blacklist.delete(symbol);
      }
    }
    
    // Scan each symbol
    for (const [symbol, prices] of this.priceHistory) {
      const volumes = this.volumeHistory.get(symbol) || [];
      
      // Check for volume spike
      const volumeAnomaly = this.detectVolumeSpike(symbol, volumes);
      if (volumeAnomaly) this.anomalies.push(volumeAnomaly);
      
      // Check for price manipulation
      const priceAnomaly = this.detectPriceManipulation(symbol, prices);
      if (priceAnomaly) this.anomalies.push(priceAnomaly);
      
      // Check for wash trading patterns
      const washAnomaly = this.detectWashTrading(symbol, prices, volumes);
      if (washAnomaly) this.anomalies.push(washAnomaly);
      
      // Check for pump and dump
      const pumpAnomaly = this.detectPumpAndDump(symbol, prices, volumes);
      if (pumpAnomaly) this.anomalies.push(pumpAnomaly);
    }
    
    // Apply recommendations
    for (const anomaly of this.anomalies) {
      if (anomaly.severity >= this.minSeverity) {
        if (anomaly.recommendation === 'BLACKLIST') {
          this.blacklist.set(anomaly.symbol, now + this.blacklistDuration);
        } else if (anomaly.recommendation === 'REDUCE_SIZE') {
          this.reducedSymbols.set(anomaly.symbol, {
            factor: 1 - anomaly.severity,
            expiry: now + (anomaly.duration || 300000)
          });
        }
      }
    }
    
    // Publish to UnifiedBus
    unifiedBus.publish({
      systemName: 'AnomalyDetector',
      timestamp: now,
      ready: true,
      coherence: this.getMarketHealth(),
      confidence: 1 - (this.anomalies.length / 10),
      signal: this.getMarketHealth() > 0.7 ? 'NEUTRAL' : 'SELL',
      data: {
        anomalies: this.anomalies.length,
        blacklisted: this.blacklist.size,
        marketHealth: this.getMarketHealth()
      }
    });
    
    return this.anomalies;
  }
  
  private detectVolumeSpike(symbol: string, volumes: number[]): Anomaly | null {
    if (volumes.length < 10) return null;
    
    const recent = volumes.slice(-5);
    const historical = volumes.slice(0, -5);
    
    const avgRecent = recent.reduce((a, b) => a + b, 0) / recent.length;
    const avgHistorical = historical.reduce((a, b) => a + b, 0) / historical.length;
    
    if (avgHistorical === 0) return null;
    
    const ratio = avgRecent / avgHistorical;
    
    if (ratio > this.volumeSpikeThreshold) {
      return {
        type: AnomalyType.VOLUME_SPIKE,
        symbol,
        severity: Math.min(1, (ratio - this.volumeSpikeThreshold) / 10),
        timestamp: Date.now(),
        description: `Volume spike: ${ratio.toFixed(1)}x normal`,
        recommendation: ratio > 10 ? 'REDUCE_SIZE' : 'MONITOR',
        duration: 300000
      };
    }
    
    return null;
  }
  
  private detectPriceManipulation(symbol: string, prices: number[]): Anomaly | null {
    if (prices.length < 5) return null;
    
    const recent = prices[prices.length - 1];
    const previous = prices[prices.length - 2];
    
    if (previous === 0) return null;
    
    const change = Math.abs((recent - previous) / previous);
    
    if (change > this.priceManipulationThreshold) {
      return {
        type: AnomalyType.PRICE_MANIPULATION,
        symbol,
        severity: Math.min(1, change / 0.5),
        timestamp: Date.now(),
        description: `Sudden price move: ${(change * 100).toFixed(1)}%`,
        recommendation: change > 0.3 ? 'BLACKLIST' : 'REDUCE_SIZE',
        duration: change > 0.3 ? this.blacklistDuration : 600000
      };
    }
    
    return null;
  }
  
  private detectWashTrading(symbol: string, prices: number[], volumes: number[]): Anomaly | null {
    if (prices.length < 20 || volumes.length < 20) return null;
    
    // Wash trading indicator: high volume but minimal price movement
    const priceRange = Math.max(...prices.slice(-20)) - Math.min(...prices.slice(-20));
    const avgPrice = prices.slice(-20).reduce((a, b) => a + b, 0) / 20;
    const priceRangePct = priceRange / avgPrice;
    
    const avgVolume = volumes.slice(-20).reduce((a, b) => a + b, 0) / 20;
    const volumeStd = Math.sqrt(
      volumes.slice(-20).reduce((sum, v) => sum + (v - avgVolume) ** 2, 0) / 20
    );
    
    // High volume variance but low price movement
    if (volumeStd / avgVolume > 0.5 && priceRangePct < 0.01) {
      return {
        type: AnomalyType.WASH_TRADING,
        symbol,
        severity: 0.7,
        timestamp: Date.now(),
        description: 'Potential wash trading detected',
        recommendation: 'BLACKLIST',
        duration: this.blacklistDuration
      };
    }
    
    return null;
  }
  
  private detectPumpAndDump(symbol: string, prices: number[], volumes: number[]): Anomaly | null {
    if (prices.length < 30) return null;
    
    // Look for rapid rise followed by decline
    const mid = Math.floor(prices.length / 2);
    const firstHalf = prices.slice(0, mid);
    const secondHalf = prices.slice(mid);
    
    const firstAvg = firstHalf.reduce((a, b) => a + b, 0) / firstHalf.length;
    const peak = Math.max(...prices);
    const current = prices[prices.length - 1];
    
    const riseFromFirst = (peak - firstAvg) / firstAvg;
    const dropFromPeak = (peak - current) / peak;
    
    // Significant rise followed by significant drop
    if (riseFromFirst > 0.3 && dropFromPeak > 0.2) {
      return {
        type: AnomalyType.PUMP_AND_DUMP,
        symbol,
        severity: Math.min(1, (riseFromFirst + dropFromPeak) / 2),
        timestamp: Date.now(),
        description: `Pump and dump pattern: +${(riseFromFirst * 100).toFixed(0)}% then -${(dropFromPeak * 100).toFixed(0)}%`,
        recommendation: 'BLACKLIST',
        duration: this.blacklistDuration * 2
      };
    }
    
    return null;
  }
  
  isBlacklisted(symbol: string): boolean {
    const expiry = this.blacklist.get(symbol);
    if (!expiry) return false;
    if (Date.now() > expiry) {
      this.blacklist.delete(symbol);
      return false;
    }
    return true;
  }
  
  getPositionSizeMultiplier(symbol: string): number {
    if (this.isBlacklisted(symbol)) return 0;
    
    const reduced = this.reducedSymbols.get(symbol);
    if (reduced) {
      if (Date.now() > reduced.expiry) {
        this.reducedSymbols.delete(symbol);
        return 1;
      }
      return reduced.factor;
    }
    
    return 1;
  }
  
  getMarketHealth(): number {
    const totalSymbols = this.priceHistory.size;
    if (totalSymbols === 0) return 1;
    
    const anomalyRatio = this.anomalies.length / totalSymbols;
    const blacklistRatio = this.blacklist.size / totalSymbols;
    
    return Math.max(0, 1 - anomalyRatio * 0.5 - blacklistRatio * 0.3);
  }
  
  getState(): AnomalyDetectorState {
    return {
      anomalies: this.anomalies,
      blacklistedSymbols: new Set(this.blacklist.keys()),
      reducedSymbols: new Map(
        Array.from(this.reducedSymbols.entries())
          .map(([k, v]) => [k, v.factor])
      ),
      overallMarketHealth: this.getMarketHealth(),
      lastScan: Date.now()
    };
  }
}

export const coinAPIAnomalyDetector = new CoinAPIAnomalyDetector();
