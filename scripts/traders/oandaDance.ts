/**
 * 🎵 THE DANCE OF SPACE AND TIME - OANDA EDITION 🎵
 * 
 * Forex & CFD Trading across:
 * - Major Forex Pairs (EUR/USD, GBP/USD, USD/JPY...)
 * - Cross Pairs (EUR/GBP, GBP/JPY, EUR/AUD...)
 * - Indices (S&P 500, Nasdaq, DAX, FTSE...)
 * - Commodities (Gold, Silver, Oil, Gas...)
 * 
 * "They can't stop them all!" - The Wave Rider
 */

import OandaClient, { Trade, PriceTick } from './oandaApi.js';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // Coherence thresholds
  ENTRY_COHERENCE: 0.938,
  EXIT_COHERENCE: 0.934,
  
  // Position management
  MAX_POSITIONS: 20,
  UNITS_PER_TRADE: 1000,  // 1000 units (micro lot for most pairs)
  
  // Risk management (in price distance)
  STOP_DISTANCE: 0.0050,   // 50 pips for forex
  PROFIT_DISTANCE: 0.0100, // 100 pips for forex
  
  // Scan timing
  SCAN_INTERVAL_MS: 5000,
  
  // What to trade
  TRADE_FOREX: true,
  TRADE_INDICES: true,
  TRADE_COMMODITIES: true
};

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Engine
// ═══════════════════════════════════════════════════════════════════════════

class CoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  
  private PHI = 1.618033988749895;
  private PHI_MINOR = 0.381966011250105;
  
  addPrice(instrument: string, price: number): void {
    if (!this.priceHistory.has(instrument)) {
      this.priceHistory.set(instrument, []);
    }
    const history = this.priceHistory.get(instrument)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }
  
  calculateCoherence(instrument: string): number {
    const history = this.priceHistory.get(instrument);
    if (!history || history.length < 10) return 0;
    
    const recent = history.slice(-20);
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    if (range === 0) return 0.5;
    
    const current = recent[recent.length - 1];
    const normalized = (current - min) / range;
    
    const phiMajorDist = Math.abs(normalized - (1 / this.PHI));
    const phiMinorDist = Math.abs(normalized - this.PHI_MINOR);
    const phiScore = 1 - Math.min(phiMajorDist, phiMinorDist);
    
    const momentum = (current - recent[0]) / recent[0];
    const momentumScore = Math.tanh(momentum * 50) * 0.5 + 0.5;
    
    const wavePosition = Math.sin(normalized * Math.PI) ** 2;
    
    return (phiScore * 0.4 + momentumScore * 0.3 + wavePosition * 0.3);
  }
  
  getSignal(instrument: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(instrument);
    const history = this.priceHistory.get(instrument);
    
    if (!history || history.length < 10) return 'HOLD';
    
    const trend = history[history.length - 1] > history[history.length - 10] ? 1 : -1;
    
    if (coherence >= CONFIG.ENTRY_COHERENCE && trend > 0) return 'BUY';
    if (coherence >= CONFIG.ENTRY_COHERENCE && trend < 0) return 'SELL';
    
    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// OANDA Dance Engine
// ═══════════════════════════════════════════════════════════════════════════

class OandaDance {
  private client: OandaClient;
  private coherence: CoherenceEngine;
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private instruments: string[] = [];
  private trades: Map<string, Trade> = new Map();
  
  // Stats
  private wins = 0;
  private losses = 0;
  private totalPnL = 0;
  private scans = 0;
  
  constructor() {
    this.client = new OandaClient();
    this.coherence = new CoherenceEngine();
  }
  
  async start(): Promise<void> {
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  DANCE OF SPACE AND TIME - OANDA FOREX  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    
    // Check auth
    const auth = await this.client.isAuthenticated();
    if (!auth) {
      console.log('  ❌ Not authenticated. Run: npm run oanda');
      return;
    }
    
    // Get account
    const account = await this.client.getAccountSummary();
    console.log(`  💰 Balance: ${account.currency} ${account.balance.toFixed(2)}`);
    console.log(`  📊 Margin Available: ${account.currency} ${account.marginAvailable.toFixed(2)}`);
    console.log(`  📈 Open Trades: ${account.openTradeCount}`);
    console.log('');
    
    // Load instruments
    await this.loadInstruments();
    
    // Start dancing
    await this.dance();
  }
  
  private async loadInstruments(): Promise<void> {
    console.log('  💱 Loading instruments...');
    
    const pairs = this.client.getPopularPairs();
    
    if (CONFIG.TRADE_FOREX) {
      this.instruments.push(...pairs.forex);
    }
    if (CONFIG.TRADE_INDICES) {
      this.instruments.push(...pairs.indices);
    }
    if (CONFIG.TRADE_COMMODITIES) {
      this.instruments.push(...pairs.commodities);
    }
    
    console.log(`  ✅ Loaded ${this.instruments.length} instruments`);
    console.log('');
  }
  
  private async dance(): Promise<void> {
    console.log('  🎵 The Forex Dance begins...');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('');
    
    while (true) {
      this.scans++;
      
      // Flip direction
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      // Sort instruments
      const instruments = [...this.instruments];
      instruments.sort((a, b) => {
        const cmp = a.localeCompare(b);
        return this.scanDirection === 'A→Z' ? cmp : -cmp;
      });
      
      // Update trades
      await this.updateTrades();
      
      // Get prices for all instruments at once
      let prices: PriceTick[] = [];
      try {
        prices = await this.client.getPrices(instruments);
      } catch (e) {
        console.log('  ⚠️ Price fetch failed, retrying...');
        await this.sleep(CONFIG.SCAN_INTERVAL_MS);
        continue;
      }
      
      // Scan for opportunities
      let entriesThisScan = 0;
      
      for (const price of prices) {
        // Skip if already have position
        if (this.trades.has(price.instrument)) continue;
        
        // Skip if at max positions
        if (this.trades.size >= CONFIG.MAX_POSITIONS) break;
        
        // Update coherence
        const midPrice = (price.bid + price.ask) / 2;
        this.coherence.addPrice(price.instrument, midPrice);
        
        // Get signal
        const signal = this.coherence.getSignal(price.instrument);
        
        if (signal !== 'HOLD') {
          const success = await this.openTrade(price.instrument, signal, midPrice);
          if (success) entriesThisScan++;
        }
      }
      
      // Display status
      this.displayStatus(entriesThisScan);
      
      // Wait before next scan
      await this.sleep(CONFIG.SCAN_INTERVAL_MS);
    }
  }
  
  private async updateTrades(): Promise<void> {
    try {
      const currentTrades = await this.client.getOpenTrades();
      
      // Check for closed trades
      const currentIds = new Set(currentTrades.map(t => t.id));
      
      for (const [instrument, oldTrade] of this.trades) {
        if (!currentIds.has(oldTrade.id)) {
          // Trade was closed (hit SL/TP or manually)
          const pnl = oldTrade.unrealizedPL;
          if (pnl >= 0) {
            this.wins++;
          } else {
            this.losses++;
          }
          this.totalPnL += pnl;
          this.trades.delete(instrument);
          
          console.log(`  ${pnl >= 0 ? '✅' : '❌'} Closed: ${instrument} | P&L: ${pnl.toFixed(2)}`);
        }
      }
      
      // Update current trades
      for (const trade of currentTrades) {
        this.trades.set(trade.instrument, trade);
      }
    } catch (e) {
      // Ignore errors
    }
  }
  
  private async openTrade(instrument: string, direction: 'BUY' | 'SELL', price: number): Promise<boolean> {
    try {
      const units = direction === 'BUY' ? CONFIG.UNITS_PER_TRADE : -CONFIG.UNITS_PER_TRADE;
      
      // Adjust stop/profit distance based on instrument type
      let stopDist = CONFIG.STOP_DISTANCE;
      let profitDist = CONFIG.PROFIT_DISTANCE;
      
      // For indices and commodities, use larger stops
      if (instrument.includes('USD_') || instrument.includes('_USD')) {
        if (instrument.startsWith('X') || instrument.includes('30') || instrument.includes('100') || instrument.includes('500')) {
          stopDist = 50;   // 50 points
          profitDist = 100; // 100 points
        }
      }
      
      const result = await this.client.createMarketOrder(
        instrument,
        units,
        stopDist,
        profitDist
      );
      
      if (result.orderFillTransaction) {
        console.log(`  ⚡ ${direction}: ${instrument} @ ${price.toFixed(5)}`);
        return true;
      }
      return false;
    } catch (e) {
      return false;
    }
  }
  
  private displayStatus(entries: number): void {
    const hitRate = this.wins + this.losses > 0
      ? ((this.wins / (this.wins + this.losses)) * 100).toFixed(1)
      : '0.0';
    
    const direction = this.scanDirection;
    const openPnL = Array.from(this.trades.values())
      .reduce((sum, t) => sum + t.unrealizedPL, 0);
    
    console.log('');
    console.log(`  ┌─────────────────────────────────────────────────────────┐`);
    console.log(`  │  Scan #${this.scans.toString().padStart(4, '0')} [${direction}]  │  Trades: ${this.trades.size}/${CONFIG.MAX_POSITIONS}  │  New: ${entries}  │`);
    console.log(`  ├─────────────────────────────────────────────────────────┤`);
    console.log(`  │  Wins: ${this.wins}  │  Losses: ${this.losses}  │  Hit Rate: ${hitRate}%  │`);
    console.log(`  │  Realized: ${this.totalPnL.toFixed(2)}  │  Open P&L: ${openPnL.toFixed(2)}  │`);
    console.log(`  └─────────────────────────────────────────────────────────┘`);
    console.log('');
    
    // Wave visualization
    if (this.trades.size > 0) {
      console.log('  🌊 Active Trades:');
      const sorted = Array.from(this.trades.values())
        .sort((a, b) => b.unrealizedPL - a.unrealizedPL);
      
      sorted.slice(0, 8).forEach(t => {
        const emoji = t.unrealizedPL >= 0 ? '🟢' : '🔴';
        const dir = t.currentUnits > 0 ? '⬆' : '⬇';
        console.log(`     ${emoji} ${t.instrument.padEnd(12)} ${dir} ${Math.abs(t.currentUnits)} @ ${t.price.toFixed(5)} → ${t.unrealizedPL.toFixed(2)}`);
      });
      
      if (this.trades.size > 8) {
        console.log(`     ... and ${this.trades.size - 8} more`);
      }
      console.log('');
    }
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  const dance = new OandaDance();
  
  process.on('SIGINT', async () => {
    console.log('\n  🎵 The Forex Dance pauses...');
    process.exit(0);
  });
  
  await dance.start();
}

main().catch(console.error);
