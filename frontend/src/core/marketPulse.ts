/**
 * 📊 MARKET PULSE - Cross-Exchange Sentiment Analysis
 * 
 * Aggregates data from multiple exchanges to provide
 * holistic market sentiment and arbitrage detection.
 */

import { unifiedBus, type SystemState } from './unifiedBus';
import { temporalLadder } from './temporalLadder';

export interface TickerData {
  symbol: string;
  source: string;
  lastPrice: number;
  priceChangePercent: number;
  volume: number;
  bid?: number;
  ask?: number;
}

export interface SentimentResult {
  avgChange24h: number;
  advanceDeclineRatio: number;
  label: 'Very Bullish' | 'Bullish' | 'Neutral' | 'Bearish' | 'Very Bearish';
}

export interface ArbitrageOpportunity {
  asset: string;
  spreadPct: number;
  buyAt: { source: string; price: number; symbol: string };
  sellAt: { source: string; price: number; symbol: string };
}

export interface MarketPulseState {
  cryptoSentiment: SentimentResult;
  stockSentiment: SentimentResult;
  arbitrageOpportunities: ArbitrageOpportunity[];
  topGainers: TickerData[];
  topLosers: TickerData[];
  totalAssetsScanned: number;
  overallSentiment: number;
  volatilityIndex: number;
}

export class MarketPulse {
  private tickers: TickerData[] = [];
  private currentState: MarketPulseState;
  private registered = false;
  
  constructor() {
    this.currentState = this.getDefaultState();
  }
  
  private getDefaultState(): MarketPulseState {
    return {
      cryptoSentiment: { avgChange24h: 0, advanceDeclineRatio: 1, label: 'Neutral' },
      stockSentiment: { avgChange24h: 0, advanceDeclineRatio: 1, label: 'Neutral' },
      arbitrageOpportunities: [],
      topGainers: [],
      topLosers: [],
      totalAssetsScanned: 0,
      overallSentiment: 0.5,
      volatilityIndex: 0.5
    };
  }
  
  register(): void {
    if (this.registered) return;
    
    temporalLadder.registerSystem('market-pulse');
    
    // Start heartbeat
    setInterval(() => {
      temporalLadder.heartbeat('market-pulse', this.currentState.overallSentiment);
    }, 3000);
    
    this.registered = true;
    console.log('📊 Market Pulse registered');
  }
  
  setTickers(tickers: TickerData[]): void {
    this.tickers = tickers;
  }
  
  analyze(): MarketPulseState {
    if (this.tickers.length === 0) {
      return this.getDefaultState();
    }
    
    // Split by source type
    const cryptoTickers = this.tickers.filter(t => 
      ['kraken', 'binance'].includes(t.source.toLowerCase())
    );
    const stockTickers = this.tickers.filter(t => 
      ['alpaca', 'capital'].includes(t.source.toLowerCase())
    );
    
    // Calculate sentiments
    const cryptoSentiment = this.calculateSentiment(cryptoTickers);
    const stockSentiment = this.calculateSentiment(stockTickers);
    
    // Find arbitrage opportunities
    const arbitrageOpportunities = this.findArbitrage();
    
    // Top movers
    const sorted = [...this.tickers].sort((a, b) => b.priceChangePercent - a.priceChangePercent);
    const topGainers = sorted.slice(0, 5);
    const topLosers = sorted.slice(-5).reverse();
    
    // Overall metrics
    const allChanges = this.tickers.map(t => t.priceChangePercent);
    const avgChange = allChanges.reduce((a, b) => a + b, 0) / allChanges.length;
    const overallSentiment = Math.max(0, Math.min(1, 0.5 + avgChange / 20));
    
    // Volatility index (standard deviation of changes)
    const variance = allChanges.reduce((sum, c) => sum + (c - avgChange) ** 2, 0) / allChanges.length;
    const volatilityIndex = Math.min(1, Math.sqrt(variance) / 10);
    
    this.currentState = {
      cryptoSentiment,
      stockSentiment,
      arbitrageOpportunities,
      topGainers,
      topLosers,
      totalAssetsScanned: this.tickers.length,
      overallSentiment,
      volatilityIndex
    };
    
    // Publish to UnifiedBus
    unifiedBus.publish({
      systemName: 'MarketPulse',
      timestamp: Date.now(),
      ready: true,
      coherence: overallSentiment,
      confidence: 1 - volatilityIndex,
      signal: overallSentiment > 0.6 ? 'BUY' : overallSentiment < 0.4 ? 'SELL' : 'NEUTRAL',
      data: {
        cryptoSentiment: cryptoSentiment.label,
        stockSentiment: stockSentiment.label,
        arbitrageCount: arbitrageOpportunities.length,
        volatilityIndex
      }
    });
    
    return this.currentState;
  }
  
  private calculateSentiment(tickers: TickerData[]): SentimentResult {
    if (tickers.length === 0) {
      return { avgChange24h: 0, advanceDeclineRatio: 1, label: 'Neutral' };
    }
    
    const changes = tickers.map(t => t.priceChangePercent);
    const avgChange = changes.reduce((a, b) => a + b, 0) / changes.length;
    
    const advancers = changes.filter(c => c > 0).length;
    const decliners = changes.filter(c => c < 0).length;
    const ratio = decliners > 0 ? advancers / decliners : advancers > 0 ? Infinity : 1;
    
    let label: SentimentResult['label'] = 'Neutral';
    if (avgChange > 5.0) label = 'Very Bullish';
    else if (avgChange > 2.0) label = 'Bullish';
    else if (avgChange < -5.0) label = 'Very Bearish';
    else if (avgChange < -2.0) label = 'Bearish';
    
    return {
      avgChange24h: avgChange,
      advanceDeclineRatio: ratio,
      label
    };
  }
  
  private findArbitrage(): ArbitrageOpportunity[] {
    const opportunities: ArbitrageOpportunity[] = [];
    
    // Group by normalized symbol
    const assets = new Map<string, TickerData[]>();
    
    for (const ticker of this.tickers) {
      // Normalize symbol
      let normSym = ticker.symbol.toUpperCase()
        .replace('USDT', '')
        .replace('USD', '')
        .replace('XBT', 'BTC')
        .replace('XXBT', 'BTC')
        .replace('ZUSD', '')
        .replace('/', '');
      
      if (normSym.length < 2) continue;
      
      if (!assets.has(normSym)) {
        assets.set(normSym, []);
      }
      assets.get(normSym)!.push(ticker);
    }
    
    // Find price discrepancies
    for (const [sym, listings] of assets) {
      if (listings.length < 2) continue;
      
      const prices = listings
        .filter(l => l.lastPrice > 0)
        .map(l => ({
          source: l.source,
          price: l.lastPrice,
          symbol: l.symbol
        }));
      
      if (prices.length < 2) continue;
      
      prices.sort((a, b) => a.price - b.price);
      const minP = prices[0];
      const maxP = prices[prices.length - 1];
      
      const diffPct = ((maxP.price - minP.price) / minP.price) * 100;
      
      if (diffPct > 1.5) {
        opportunities.push({
          asset: sym,
          spreadPct: diffPct,
          buyAt: minP,
          sellAt: maxP
        });
      }
    }
    
    return opportunities.sort((a, b) => b.spreadPct - a.spreadPct);
  }
  
  getState(): MarketPulseState {
    return this.currentState;
  }
  
  getSentimentModifier(): number {
    const sentiment = this.currentState.overallSentiment;
    const volatility = this.currentState.volatilityIndex;
    
    // Higher sentiment = more aggressive, but tempered by volatility
    return 0.8 + (sentiment * 0.3) - (volatility * 0.1);
  }
}

export const marketPulse = new MarketPulse();
