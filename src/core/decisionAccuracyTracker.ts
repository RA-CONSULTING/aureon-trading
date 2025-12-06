/**
 * Decision Accuracy Tracker
 * Compares predicted decisions vs actual price movements for temporal feedback
 */

import { DecisionAction, DecisionExplanation } from './decisionExplainer';
import { unifiedBus } from './unifiedBus';

export interface TrackedDecision {
  id: string;
  decision: DecisionExplanation;
  priceAtDecision: number;
  priceAfter1m?: number;
  priceAfter5m?: number;
  priceAfter15m?: number;
  actualDirection1m?: 'UP' | 'DOWN' | 'FLAT';
  actualDirection5m?: 'UP' | 'DOWN' | 'FLAT';
  actualDirection15m?: 'UP' | 'DOWN' | 'FLAT';
  accuracy1m?: boolean;
  accuracy5m?: boolean;
  accuracy15m?: boolean;
  completedAt?: number;
}

export interface AccuracyMetrics {
  total: number;
  correct1m: number;
  correct5m: number;
  correct15m: number;
  accuracy1m: number;
  accuracy5m: number;
  accuracy15m: number;
  buyAccuracy: number;
  sellAccuracy: number;
  holdAccuracy: number;
  recentStreak: number;
  lastUpdated: number;
}

class DecisionAccuracyTrackerClass {
  private trackedDecisions: TrackedDecision[] = [];
  private readonly maxTracked = 200;
  private listeners: Set<(metrics: AccuracyMetrics) => void> = new Set();
  private priceHistory: { timestamp: number; price: number }[] = [];

  trackDecision(decision: DecisionExplanation, currentPrice: number): TrackedDecision {
    const tracked: TrackedDecision = {
      id: decision.id,
      decision,
      priceAtDecision: currentPrice
    };

    this.trackedDecisions.unshift(tracked);
    if (this.trackedDecisions.length > this.maxTracked) {
      this.trackedDecisions.pop();
    }

    // Schedule price checks
    this.schedulePriceCheck(tracked.id, 1);
    this.schedulePriceCheck(tracked.id, 5);
    this.schedulePriceCheck(tracked.id, 15);

    return tracked;
  }

  updatePrice(price: number): void {
    const now = Date.now();
    this.priceHistory.push({ timestamp: now, price });

    // Keep only last 20 minutes of price history
    const cutoff = now - 20 * 60 * 1000;
    this.priceHistory = this.priceHistory.filter(p => p.timestamp >= cutoff);

    // Check pending decisions for completion
    this.checkPendingDecisions();
  }

  private schedulePriceCheck(decisionId: string, minutesAfter: number): void {
    setTimeout(() => {
      this.evaluateDecision(decisionId, minutesAfter);
    }, minutesAfter * 60 * 1000);
  }

  private evaluateDecision(decisionId: string, minutesAfter: number): void {
    const tracked = this.trackedDecisions.find(t => t.id === decisionId);
    if (!tracked) return;

    // Get latest price from history
    const latestPrice = this.priceHistory[this.priceHistory.length - 1]?.price;
    if (!latestPrice) return;

    const priceDiff = latestPrice - tracked.priceAtDecision;
    const pctChange = (priceDiff / tracked.priceAtDecision) * 100;

    // Determine actual direction (0.05% threshold for FLAT)
    let direction: 'UP' | 'DOWN' | 'FLAT';
    if (pctChange > 0.05) direction = 'UP';
    else if (pctChange < -0.05) direction = 'DOWN';
    else direction = 'FLAT';

    // Determine accuracy based on decision action
    const action = tracked.decision.action;
    let accurate = false;
    if (action === 'BUY' && direction === 'UP') accurate = true;
    else if (action === 'SELL' && direction === 'DOWN') accurate = true;
    else if (action === 'HOLD' && direction === 'FLAT') accurate = true;

    // Update tracked decision
    if (minutesAfter === 1) {
      tracked.priceAfter1m = latestPrice;
      tracked.actualDirection1m = direction;
      tracked.accuracy1m = accurate;
    } else if (minutesAfter === 5) {
      tracked.priceAfter5m = latestPrice;
      tracked.actualDirection5m = direction;
      tracked.accuracy5m = accurate;
    } else if (minutesAfter === 15) {
      tracked.priceAfter15m = latestPrice;
      tracked.actualDirection15m = direction;
      tracked.accuracy15m = accurate;
      tracked.completedAt = Date.now();
    }

    // Recalculate and notify
    const metrics = this.getMetrics();
    this.notifyListeners(metrics);

    // Publish to bus
    unifiedBus.publish({
      systemName: 'AccuracyTracker',
      timestamp: Date.now(),
      ready: true,
      coherence: metrics.accuracy5m,
      confidence: metrics.accuracy15m,
      signal: 'NEUTRAL',
      data: { metrics, latestEvaluation: { decisionId, minutesAfter, accurate, direction } }
    });
  }

  private checkPendingDecisions(): void {
    const now = Date.now();
    const latestPrice = this.priceHistory[this.priceHistory.length - 1]?.price;
    if (!latestPrice) return;

    for (const tracked of this.trackedDecisions) {
      const decisionTime = tracked.decision.timestamp;

      // Check 1 minute
      if (!tracked.accuracy1m && now - decisionTime >= 60000) {
        this.evaluateDecisionWithPrice(tracked, 1, latestPrice);
      }

      // Check 5 minutes
      if (!tracked.accuracy5m && now - decisionTime >= 300000) {
        this.evaluateDecisionWithPrice(tracked, 5, latestPrice);
      }

      // Check 15 minutes
      if (!tracked.accuracy15m && now - decisionTime >= 900000) {
        this.evaluateDecisionWithPrice(tracked, 15, latestPrice);
      }
    }
  }

  private evaluateDecisionWithPrice(tracked: TrackedDecision, minutesAfter: number, currentPrice: number): void {
    const priceDiff = currentPrice - tracked.priceAtDecision;
    const pctChange = (priceDiff / tracked.priceAtDecision) * 100;

    let direction: 'UP' | 'DOWN' | 'FLAT';
    if (pctChange > 0.05) direction = 'UP';
    else if (pctChange < -0.05) direction = 'DOWN';
    else direction = 'FLAT';

    const action = tracked.decision.action;
    let accurate = false;
    if (action === 'BUY' && direction === 'UP') accurate = true;
    else if (action === 'SELL' && direction === 'DOWN') accurate = true;
    else if (action === 'HOLD' && direction === 'FLAT') accurate = true;

    if (minutesAfter === 1 && !tracked.accuracy1m) {
      tracked.priceAfter1m = currentPrice;
      tracked.actualDirection1m = direction;
      tracked.accuracy1m = accurate;
    } else if (minutesAfter === 5 && !tracked.accuracy5m) {
      tracked.priceAfter5m = currentPrice;
      tracked.actualDirection5m = direction;
      tracked.accuracy5m = accurate;
    } else if (minutesAfter === 15 && !tracked.accuracy15m) {
      tracked.priceAfter15m = currentPrice;
      tracked.actualDirection15m = direction;
      tracked.accuracy15m = accurate;
      tracked.completedAt = Date.now();
    }
  }

  getMetrics(): AccuracyMetrics {
    const completed = this.trackedDecisions.filter(t => t.accuracy1m !== undefined);

    const correct1m = completed.filter(t => t.accuracy1m).length;
    const correct5m = completed.filter(t => t.accuracy5m).length;
    const correct15m = completed.filter(t => t.accuracy15m).length;

    const buys = completed.filter(t => t.decision.action === 'BUY');
    const sells = completed.filter(t => t.decision.action === 'SELL');
    const holds = completed.filter(t => t.decision.action === 'HOLD');

    const buyAccuracy = buys.length > 0 ? buys.filter(t => t.accuracy5m).length / buys.length : 0;
    const sellAccuracy = sells.length > 0 ? sells.filter(t => t.accuracy5m).length / sells.length : 0;
    const holdAccuracy = holds.length > 0 ? holds.filter(t => t.accuracy5m).length / holds.length : 0;

    // Calculate recent streak
    let streak = 0;
    for (const t of completed) {
      if (t.accuracy5m) streak++;
      else break;
    }

    return {
      total: completed.length,
      correct1m,
      correct5m,
      correct15m,
      accuracy1m: completed.length > 0 ? correct1m / completed.length : 0,
      accuracy5m: completed.length > 0 ? correct5m / completed.length : 0,
      accuracy15m: completed.length > 0 ? correct15m / completed.length : 0,
      buyAccuracy,
      sellAccuracy,
      holdAccuracy,
      recentStreak: streak,
      lastUpdated: Date.now()
    };
  }

  getTrackedDecisions(): TrackedDecision[] {
    return [...this.trackedDecisions];
  }

  subscribe(listener: (metrics: AccuracyMetrics) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(metrics: AccuracyMetrics): void {
    this.listeners.forEach(listener => listener(metrics));
  }

  clear(): void {
    this.trackedDecisions = [];
    this.priceHistory = [];
  }
}

export const decisionAccuracyTracker = new DecisionAccuracyTrackerClass();
