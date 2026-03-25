/**
 * 🎵 THE DANCE OF SPACE AND TIME - CAPITAL.COM EDITION 🎵
 * 
 * Multi-Asset Coherence Trading across:
 * - Crypto (BTC, ETH, SOL, XRP, DOGE...)
 * - Forex (EUR/USD, GBP/USD, USD/JPY...)
 * - Indices (S&P 500, Nasdaq, DAX, FTSE...)
 * - Stocks (AAPL, MSFT, TSLA, NVDA...)
 * - Commodities (Gold, Silver, Oil, Gas...)
 * 
 * "They can't stop them all!" - The Wave Rider
 */

import CapitalComClient, { MarketInfo, Position } from './capitalComApi.js';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // Coherence thresholds
  ENTRY_COHERENCE: 0.938,    // Φ threshold to enter
  EXIT_COHERENCE: 0.934,     // Φ threshold to exit
  
  // Position management
  MAX_POSITIONS: 50,         // Maximum concurrent positions
  POSITION_SIZE: 0.1,        // Size per position (CFD units)
  
  // Risk management
  STOP_DISTANCE: 50,         // Stop loss in points
  LIMIT_DISTANCE: 100,       // Take profit in points
  
  // Scan timing
  SCAN_INTERVAL_MS: 5000,    // 5 seconds between scans
  
  // Which categories to trade
  CATEGORIES: ['crypto', 'forex', 'indices', 'stocks', 'commodities']
};

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Engine (same as Binance version)
// ═══════════════════════════════════════════════════════════════════════════

class CoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  
  private PHI = 1.618033988749895;
  private PHI_MINOR = 0.381966011250105;
  
  addPrice(epic: string, price: number): void {
    if (!this.priceHistory.has(epic)) {
      this.priceHistory.set(epic, []);
    }
    const history = this.priceHistory.get(epic)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }
  
  calculateCoherence(epic: string): number {
    const history = this.priceHistory.get(epic);
    if (!history || history.length < 10) return 0;
    
    // Calculate harmonics
    const recent = history.slice(-20);
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    if (range === 0) return 0.5;
    
    const current = recent[recent.length - 1];
    const normalized = (current - min) / range;
    
    // Phi alignment
    const phiMajorDist = Math.abs(normalized - (1 / this.PHI));
    const phiMinorDist = Math.abs(normalized - this.PHI_MINOR);
    const phiScore = 1 - Math.min(phiMajorDist, phiMinorDist);
    
    // Momentum
    const momentum = (current - recent[0]) / recent[0];
    const momentumScore = Math.tanh(momentum * 50) * 0.5 + 0.5;
    
    // Wave position
    const wavePosition = Math.sin(normalized * Math.PI) ** 2;
    
    // Final coherence
    return (phiScore * 0.4 + momentumScore * 0.3 + wavePosition * 0.3);
  }
  
  getSignal(epic: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(epic);
    const history = this.priceHistory.get(epic);
    
    if (!history || history.length < 10) return 'HOLD';
    
    const trend = history[history.length - 1] > history[history.length - 10] ? 1 : -1;
    
    if (coherence >= CONFIG.ENTRY_COHERENCE && trend > 0) return 'BUY';
    if (coherence >= CONFIG.ENTRY_COHERENCE && trend < 0) return 'SELL';
    
    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Capital.com Dance Engine
// ═══════════════════════════════════════════════════════════════════════════

class CapitalDance {
  private client: CapitalComClient;
  private coherence: CoherenceEngine;
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private allMarkets: MarketInfo[] = [];
  private positions: Map<string, Position> = new Map();
  
  // Stats
  private wins = 0;
  private losses = 0;
  private totalPnL = 0;
  private scans = 0;
  
  constructor() {
    this.client = new CapitalComClient();
    this.coherence = new CoherenceEngine();
  }
  
  async start(): Promise<void> {
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  DANCE OF SPACE AND TIME - CAPITAL.COM  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    
    // Authenticate
    const success = await this.client.authenticate();
    if (!success) {
      console.log('  ❌ Authentication failed. Set environment variables.');
      return;
    }
    
    // Get account info
    const account = await this.client.getAccountBalance();
    console.log(`  💰 Starting Balance: ${account.currency} ${account.balance.toFixed(2)}`);
    console.log('');
    
    // Load all markets
    await this.loadMarkets();
    
    // Start dancing
    await this.dance();
  }
  
  private async loadMarkets(): Promise<void> {
    console.log('  🌍 Loading markets...');
    
    const popularMarkets = this.client.getPopularMarkets();
    const allEpics: string[] = [];
    
    for (const category of CONFIG.CATEGORIES) {
      const epics = popularMarkets[category] || [];
      allEpics.push(...epics);
    }
    
    // Search for each to get full market info
    for (const epic of allEpics) {
      try {
        const markets = await this.client.searchMarkets(epic, 1);
        if (markets.length > 0) {
          this.allMarkets.push(markets[0]);
        }
      } catch (e) {
        // Skip unavailable markets
      }
    }
    
    console.log(`  ✅ Loaded ${this.allMarkets.length} tradable markets`);
    console.log('');
  }
  
  private async dance(): Promise<void> {
    console.log('  🎵 The Dance begins...');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('');
    
    while (true) {
      this.scans++;
      
      // Flip direction each scan
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      // Sort markets
      const markets = [...this.allMarkets];
      markets.sort((a, b) => {
        const cmp = a.epic.localeCompare(b.epic);
        return this.scanDirection === 'A→Z' ? cmp : -cmp;
      });
      
      // Update positions
      await this.updatePositions();
      
      // Scan for opportunities
      let entriesThisScan = 0;
      
      for (const market of markets) {
        // Skip if already have position
        if (this.positions.has(market.epic)) continue;
        
        // Skip if at max positions
        if (this.positions.size >= CONFIG.MAX_POSITIONS) break;
        
        // Update price history
        const midPrice = (market.bid + market.offer) / 2;
        this.coherence.addPrice(market.epic, midPrice);
        
        // Get signal
        const signal = this.coherence.getSignal(market.epic);
        
        if (signal !== 'HOLD') {
          const result = await this.openPosition(market, signal);
          if (result) entriesThisScan++;
        }
      }
      
      // Display status
      this.displayStatus(entriesThisScan);
      
      // Wait before next scan
      await this.sleep(CONFIG.SCAN_INTERVAL_MS);
    }
  }
  
  private async updatePositions(): Promise<void> {
    try {
      const positions = await this.client.getPositions();
      
      // Check for closed positions
      const currentIds = new Set(positions.map(p => p.dealId));
      
      for (const [epic, oldPos] of this.positions) {
        if (!currentIds.has(oldPos.dealId)) {
          // Position was closed (hit SL/TP or manually)
          if (oldPos.pnl >= 0) {
            this.wins++;
          } else {
            this.losses++;
          }
          this.totalPnL += oldPos.pnl;
          this.positions.delete(epic);
          
          console.log(`  ${oldPos.pnl >= 0 ? '✅' : '❌'} Closed: ${epic} | P&L: ${oldPos.pnl.toFixed(2)}`);
        }
      }
      
      // Update current positions
      for (const pos of positions) {
        this.positions.set(pos.epic, pos);
      }
    } catch (e) {
      // Ignore errors
    }
  }
  
  private async openPosition(market: MarketInfo, direction: 'BUY' | 'SELL'): Promise<boolean> {
    try {
      const result = await this.client.openPosition(
        market.epic,
        direction,
        CONFIG.POSITION_SIZE,
        CONFIG.STOP_DISTANCE,
        CONFIG.LIMIT_DISTANCE
      );
      
      if (result.status === 'ACCEPTED') {
        console.log(`  ⚡ ${direction}: ${market.epic} @ ${direction === 'BUY' ? market.offer : market.bid}`);
        return true;
      } else {
        return false;
      }
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
      .reduce((sum, p) => sum + p.pnl, 0);
    
    console.log('');
    console.log(`  ┌─────────────────────────────────────────────────────────┐`);
    console.log(`  │  Scan #${this.scans.toString().padStart(4, '0')} [${direction}]  │  Positions: ${this.positions.size}/${CONFIG.MAX_POSITIONS}  │  Entries: ${entries}  │`);
    console.log(`  ├─────────────────────────────────────────────────────────┤`);
    console.log(`  │  Wins: ${this.wins}  │  Losses: ${this.losses}  │  Hit Rate: ${hitRate}%  │`);
    console.log(`  │  Realized P&L: ${this.totalPnL.toFixed(2)}  │  Open P&L: ${openPnL.toFixed(2)}  │`);
    console.log(`  └─────────────────────────────────────────────────────────┘`);
    console.log('');
    
    // Wave visualization
    this.displayWave();
  }
  
  private displayWave(): void {
    const positions = Array.from(this.positions.values());
    if (positions.length === 0) return;
    
    console.log('  🌊 Active Positions:');
    
    for (const pos of positions.slice(0, 10)) {
      const emoji = pos.pnl >= 0 ? '🟢' : '🔴';
      const dir = pos.direction === 'BUY' ? '⬆' : '⬇';
      const pnlStr = pos.pnl >= 0 ? `+${pos.pnl.toFixed(2)}` : pos.pnl.toFixed(2);
      
      console.log(`     ${emoji} ${pos.epic.padEnd(12)} ${dir} ${pos.size} @ ${pos.openLevel.toFixed(4)} → ${pnlStr}`);
    }
    
    if (positions.length > 10) {
      console.log(`     ... and ${positions.length - 10} more`);
    }
    
    console.log('');
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  const dance = new CapitalDance();
  
  // Handle graceful shutdown
  process.on('SIGINT', async () => {
    console.log('\n  🎵 The Dance pauses...');
    console.log('  Closing positions gracefully...');
    process.exit(0);
  });
  
  await dance.start();
}

main().catch(console.error);
