/**
 * 🎵 THE DANCE OF SPACE AND TIME - ALPACA EDITION 🎵
 * 
 * Commission-Free Trading across:
 * - US Stocks (AAPL, MSFT, TSLA, NVDA...)
 * - ETFs (SPY, QQQ, IWM, ARKK...)
 * - Crypto (BTC, ETH, SOL, DOGE...)
 * 
 * "They can't stop them all!" - The Wave Rider
 */

import AlpacaClient, { Position, Quote } from './alpacaApi.js';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // Coherence thresholds
  ENTRY_COHERENCE: 0.938,
  EXIT_COHERENCE: 0.934,
  
  // Position management
  MAX_POSITIONS: 30,
  POSITION_SIZE_USD: 100,  // $100 per position
  
  // Risk management
  STOP_LOSS_PCT: 0.02,     // 2% stop loss
  TAKE_PROFIT_PCT: 0.04,   // 4% take profit
  
  // Scan timing
  SCAN_INTERVAL_MS: 10000, // 10 seconds
  
  // What to trade
  TRADE_STOCKS: true,
  TRADE_CRYPTO: true
};

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Engine
// ═══════════════════════════════════════════════════════════════════════════

class CoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  
  private PHI = 1.618033988749895;
  private PHI_MINOR = 0.381966011250105;
  
  addPrice(symbol: string, price: number): void {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }
    const history = this.priceHistory.get(symbol)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }
  
  calculateCoherence(symbol: string): number {
    const history = this.priceHistory.get(symbol);
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
  
  getSignal(symbol: string): 'BUY' | 'HOLD' {
    const coherence = this.calculateCoherence(symbol);
    const history = this.priceHistory.get(symbol);
    
    if (!history || history.length < 10) return 'HOLD';
    
    const trend = history[history.length - 1] > history[history.length - 10] ? 1 : -1;
    
    // Alpaca only supports long positions for most retail accounts
    if (coherence >= CONFIG.ENTRY_COHERENCE && trend > 0) return 'BUY';
    
    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Alpaca Dance Engine
// ═══════════════════════════════════════════════════════════════════════════

class AlpacaDance {
  private client: AlpacaClient;
  private coherence: CoherenceEngine;
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private symbols: string[] = [];
  private positions: Map<string, Position> = new Map();
  
  // Stats
  private wins = 0;
  private losses = 0;
  private totalPnL = 0;
  private scans = 0;
  
  constructor() {
    this.client = new AlpacaClient();
    this.coherence = new CoherenceEngine();
  }
  
  async start(): Promise<void> {
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  DANCE OF SPACE AND TIME - ALPACA  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    
    // Check auth
    const auth = await this.client.isAuthenticated();
    if (!auth) {
      console.log('  ❌ Not authenticated. Run: npm run alpaca');
      return;
    }
    
    // Get account
    const account = await this.client.getAccount();
    console.log(`  💰 Starting Balance: $${account.portfolioValue.toFixed(2)}`);
    console.log(`  💵 Buying Power: $${account.buyingPower.toFixed(2)}`);
    console.log('');
    
    // Check market
    const clock = await this.client.getClock();
    console.log(`  🕐 Market: ${clock.isOpen ? '🟢 OPEN' : '🔴 CLOSED'}`);
    if (!clock.isOpen) {
      console.log(`  ⏰ Next Open: ${new Date(clock.nextOpen).toLocaleString()}`);
      console.log('');
      console.log('  💡 Crypto markets trade 24/7!');
    }
    console.log('');
    
    // Load symbols
    await this.loadSymbols();
    
    // Start dancing
    await this.dance();
  }
  
  private async loadSymbols(): Promise<void> {
    console.log('  📦 Loading symbols...');
    
    const popular = this.client.getPopularSymbols();
    
    if (CONFIG.TRADE_STOCKS) {
      this.symbols.push(...popular.stocks);
    }
    if (CONFIG.TRADE_CRYPTO) {
      this.symbols.push(...popular.crypto);
    }
    
    console.log(`  ✅ Loaded ${this.symbols.length} symbols`);
    console.log('');
  }
  
  private async dance(): Promise<void> {
    console.log('  🎵 The Dance begins...');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('');
    
    while (true) {
      this.scans++;
      
      // Flip direction
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      // Sort symbols
      const symbols = [...this.symbols];
      symbols.sort((a, b) => {
        const cmp = a.localeCompare(b);
        return this.scanDirection === 'A→Z' ? cmp : -cmp;
      });
      
      // Update positions
      await this.updatePositions();
      
      // Scan for opportunities
      let entriesThisScan = 0;
      
      for (const symbol of symbols) {
        // Skip if already have position
        if (this.positions.has(symbol)) continue;
        
        // Skip if at max positions
        if (this.positions.size >= CONFIG.MAX_POSITIONS) break;
        
        // Get quote
        try {
          const quote = await this.client.getQuote(symbol);
          if (quote.lastPrice <= 0) continue;
          
          // Update coherence
          this.coherence.addPrice(symbol, quote.lastPrice);
          
          // Get signal
          const signal = this.coherence.getSignal(symbol);
          
          if (signal === 'BUY') {
            const qty = Math.floor(CONFIG.POSITION_SIZE_USD / quote.lastPrice);
            if (qty > 0) {
              await this.openPosition(symbol, qty, quote.lastPrice);
              entriesThisScan++;
            }
          }
        } catch (e) {
          // Skip on error
        }
        
        // Small delay to respect rate limits
        await this.sleep(100);
      }
      
      // Display status
      this.displayStatus(entriesThisScan);
      
      // Wait before next scan
      await this.sleep(CONFIG.SCAN_INTERVAL_MS);
    }
  }
  
  private async updatePositions(): Promise<void> {
    try {
      const currentPositions = await this.client.getPositions();
      
      // Check for closed positions
      const currentSymbols = new Set(currentPositions.map(p => p.symbol));
      
      for (const [symbol, oldPos] of this.positions) {
        if (!currentSymbols.has(symbol)) {
          // Position was closed
          if (oldPos.unrealizedPL >= 0) {
            this.wins++;
          } else {
            this.losses++;
          }
          this.totalPnL += oldPos.unrealizedPL;
          this.positions.delete(symbol);
          
          console.log(`  ${oldPos.unrealizedPL >= 0 ? '✅' : '❌'} Closed: ${symbol} | P&L: $${oldPos.unrealizedPL.toFixed(2)}`);
        }
      }
      
      // Check for stop loss / take profit
      for (const pos of currentPositions) {
        const prevPos = this.positions.get(pos.symbol);
        
        // Check stop loss
        if (pos.unrealizedPLPercent <= -CONFIG.STOP_LOSS_PCT * 100) {
          console.log(`  🛑 Stop Loss: ${pos.symbol} at ${pos.unrealizedPLPercent.toFixed(1)}%`);
          await this.client.closePosition(pos.symbol);
          continue;
        }
        
        // Check take profit
        if (pos.unrealizedPLPercent >= CONFIG.TAKE_PROFIT_PCT * 100) {
          console.log(`  🎯 Take Profit: ${pos.symbol} at ${pos.unrealizedPLPercent.toFixed(1)}%`);
          await this.client.closePosition(pos.symbol);
          continue;
        }
        
        this.positions.set(pos.symbol, pos);
      }
    } catch (e) {
      // Ignore errors
    }
  }
  
  private async openPosition(symbol: string, qty: number, price: number): Promise<boolean> {
    try {
      const order = await this.client.submitOrder(symbol, qty, 'buy', 'market');
      
      if (order.status === 'filled' || order.status === 'accepted' || order.status === 'new') {
        console.log(`  ⚡ BUY: ${symbol} x${qty} @ $${price.toFixed(2)}`);
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
    const openPnL = Array.from(this.positions.values())
      .reduce((sum, p) => sum + p.unrealizedPL, 0);
    
    console.log('');
    console.log(`  ┌─────────────────────────────────────────────────────────┐`);
    console.log(`  │  Scan #${this.scans.toString().padStart(4, '0')} [${direction}]  │  Positions: ${this.positions.size}/${CONFIG.MAX_POSITIONS}  │  New: ${entries}  │`);
    console.log(`  ├─────────────────────────────────────────────────────────┤`);
    console.log(`  │  Wins: ${this.wins}  │  Losses: ${this.losses}  │  Hit Rate: ${hitRate}%  │`);
    console.log(`  │  Realized: $${this.totalPnL.toFixed(2)}  │  Open: $${openPnL.toFixed(2)}  │`);
    console.log(`  └─────────────────────────────────────────────────────────┘`);
    console.log('');
    
    // Show top positions
    if (this.positions.size > 0) {
      console.log('  📈 Top Positions:');
      const sorted = Array.from(this.positions.values())
        .sort((a, b) => b.unrealizedPL - a.unrealizedPL);
      
      sorted.slice(0, 5).forEach(p => {
        const emoji = p.unrealizedPL >= 0 ? '🟢' : '🔴';
        console.log(`     ${emoji} ${p.symbol.padEnd(8)} ${p.qty} @ $${p.avgEntryPrice.toFixed(2)} → $${p.unrealizedPL.toFixed(2)} (${p.unrealizedPLPercent.toFixed(1)}%)`);
      });
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
  const dance = new AlpacaDance();
  
  process.on('SIGINT', async () => {
    console.log('\n  🎵 The Dance pauses...');
    process.exit(0);
  });
  
  await dance.start();
}

main().catch(console.error);
