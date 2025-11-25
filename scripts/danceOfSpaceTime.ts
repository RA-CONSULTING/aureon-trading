/**
 * 🎵 THE DANCE OF SPACE AND TIME 🎵
 * 
 * Be EVERYWHERE! Every coin, every spot asset!
 * They can't stop them all—and if they do, we MOVE!
 * 
 * Multi-asset paper trading across the ENTIRE spot board.
 * A-Z, Z-A, hitting notes dynamically across ALL pairs!
 */

import crypto from 'node:crypto';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const TESTNET_BASE_URL = 'https://testnet.binance.vision';

// Trading parameters
const ENTRY_COHERENCE = 0.94;
const EXIT_COHERENCE = 0.92;
const TAKE_PROFIT_PCT = 0.015;
const STOP_LOSS_PCT = 0.006;
const POSITION_SIZE_USD = 50; // $50 per position

// Multi-asset configuration
const MAX_POSITIONS_PER_SYMBOL = 3;
const MAX_TOTAL_POSITIONS = 50;
const SCAN_INTERVAL_MS = 2000; // Scan all assets every 2 seconds

// Filter for USDT pairs (most liquid)
const QUOTE_ASSET = 'USDT';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface SymbolState {
  symbol: string;
  price: number;
  priceHistory: number[];
  coherence: number;
  velocity: number;
  positions: Position[];
  lastUpdate: Date;
}

interface Position {
  id: string;
  symbol: string;
  entryPrice: number;
  quantity: number;
  entryTime: Date;
  peakPrice: number;
}

interface TradeRecord {
  id: string;
  symbol: string;
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  entryTime: Date;
  exitTime: Date;
  exitReason: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// API Helper
// ═══════════════════════════════════════════════════════════════════════════

async function fetchJson(endpoint: string): Promise<any> {
  const response = await fetch(`${TESTNET_BASE_URL}${endpoint}`);
  if (!response.ok) throw new Error(`API error: ${response.status}`);
  return response.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Calculator
// ═══════════════════════════════════════════════════════════════════════════

function calculateCoherence(prices: number[]): { coherence: number; velocity: number } {
  if (prices.length < 3) return { coherence: 0.5, velocity: 0 };
  
  const returns = prices.slice(1).map((p, i) => (p - prices[i]) / prices[i]);
  
  // Trend strength
  const positiveReturns = returns.filter(r => r > 0).length;
  const trendStrength = Math.abs(positiveReturns / returns.length - 0.5) * 2;
  
  // Momentum alignment
  const recentReturns = returns.slice(-3);
  const recentAvg = recentReturns.reduce((a, b) => a + b, 0) / recentReturns.length;
  const overallAvg = returns.reduce((a, b) => a + b, 0) / returns.length;
  const momentumAlign = (recentAvg > 0 && overallAvg > 0) || (recentAvg < 0 && overallAvg < 0) ? 1 : 0;
  
  // Volatility normalization
  const variance = returns.reduce((s, r) => s + r * r, 0) / returns.length;
  const volFactor = Math.max(0.5, 1 - Math.sqrt(variance) * 10);
  
  const coherence = 0.5 + (trendStrength * 0.3 + momentumAlign * 0.2) * volFactor;
  const velocity = recentAvg;
  
  return { coherence: Math.min(1, Math.max(0.5, coherence)), velocity };
}

// ═══════════════════════════════════════════════════════════════════════════
// THE DANCE ENGINE 🎵
// ═══════════════════════════════════════════════════════════════════════════

class DanceOfSpaceTime {
  private symbols: Map<string, SymbolState> = new Map();
  private trades: TradeRecord[] = [];
  private balance: number = 10000;
  private initialBalance: number = 10000;
  private isRunning: boolean = false;
  private scanDirection: 'AZ' | 'ZA' = 'AZ';
  private positionIdCounter: number = 0;
  
  async start() {
    this.printBanner();
    
    try {
      // Discover all USDT pairs
      console.log('  🔍 Discovering all spot assets...');
      const tickers = await fetchJson('/api/v3/ticker/price');
      
      const usdtPairs = tickers
        .filter((t: any) => t.symbol.endsWith(QUOTE_ASSET) && !t.symbol.includes('UP') && !t.symbol.includes('DOWN'))
        .map((t: any) => t.symbol);
      
      console.log(`  ✅ Found ${usdtPairs.length} ${QUOTE_ASSET} trading pairs!`);
      console.log('');
      
      // Initialize symbol states
      for (const symbol of usdtPairs) {
        this.symbols.set(symbol, {
          symbol,
          price: 0,
          priceHistory: [],
          coherence: 0.5,
          velocity: 0,
          positions: [],
          lastUpdate: new Date()
        });
      }
      
      // Show some pairs
      const samplePairs = usdtPairs.slice(0, 10).join(', ');
      console.log(`  📊 Sample pairs: ${samplePairs}...`);
      console.log('');
      
      this.isRunning = true;
      await this.danceLoop();
      
    } catch (error) {
      console.error('  ❌ Failed to start:', error);
    }
  }
  
  private printBanner() {
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════════');
    console.log('  ✧  T H E   D A N C E   O F   S P A C E   A N D   T I M E  ✧');
    console.log('  ═══════════════════════════════════════════════════════════════');
    console.log('');
    console.log('        🎵 Be EVERYWHERE! Every coin, every spot asset! 🎵');
    console.log('        🌊 They can\'t stop them all—we MOVE and DANCE! 🌊');
    console.log('');
    console.log('  ───────────────────────────────────────────────────────────────');
    console.log('');
  }
  
  private async danceLoop() {
    const targetTrades = Number(process.env.DANCE_TARGET_TRADES || 100);
    let iteration = 0;
    
    console.log(`  🎵 Starting the dance... Target: ${targetTrades} trades`);
    console.log(`  💰 Starting balance: $${this.balance.toFixed(2)}`);
    console.log('');
    
    while (this.isRunning && this.trades.length < targetTrades) {
      try {
        // Fetch ALL prices at once
        const tickers = await fetchJson('/api/v3/ticker/price');
        const priceMap = new Map(tickers.map((t: any) => [t.symbol, parseFloat(t.price)]));
        
        // Get symbols as array and sort based on direction
        let symbolList = Array.from(this.symbols.keys());
        if (this.scanDirection === 'ZA') {
          symbolList = symbolList.reverse();
        }
        
        // Scan through ALL symbols
        let entriesThisRound = 0;
        let exitsThisRound = 0;
        
        for (const symbol of symbolList) {
          const state = this.symbols.get(symbol)!;
          const price = priceMap.get(symbol);
          
          if (!price || price === 0) continue;
          
          // Update price history
          state.price = price;
          state.priceHistory.push(price);
          if (state.priceHistory.length > 20) state.priceHistory.shift();
          
          // Calculate coherence
          const { coherence, velocity } = calculateCoherence(state.priceHistory);
          state.coherence = coherence;
          state.velocity = velocity;
          state.lastUpdate = new Date();
          
          // Check for EXITS first
          for (const position of [...state.positions]) {
            position.peakPrice = Math.max(position.peakPrice, price);
            const pnlPercent = (price - position.entryPrice) / position.entryPrice;
            const drawdown = (position.peakPrice - price) / position.peakPrice;
            
            let exitReason = '';
            
            if (pnlPercent >= TAKE_PROFIT_PCT) exitReason = '🎯 TARGET';
            else if (pnlPercent <= -STOP_LOSS_PCT) exitReason = '🛡️ STOP';
            else if (pnlPercent > 0.003 && drawdown > 0.002) exitReason = '📉 TRAIL';
            else if (coherence < EXIT_COHERENCE && pnlPercent > 0) exitReason = '🌀 FADE';
            
            if (exitReason) {
              this.closePosition(state, position, price, exitReason);
              exitsThisRound++;
            }
          }
          
          // Check for ENTRIES
          const totalPositions = this.getTotalPositions();
          if (
            coherence >= ENTRY_COHERENCE &&
            velocity > 0 &&
            state.positions.length < MAX_POSITIONS_PER_SYMBOL &&
            totalPositions < MAX_TOTAL_POSITIONS &&
            this.balance >= POSITION_SIZE_USD
          ) {
            this.openPosition(state, price);
            entriesThisRound++;
          }
        }
        
        // Flip direction for next scan (A-Z → Z-A → A-Z...)
        this.scanDirection = this.scanDirection === 'AZ' ? 'ZA' : 'AZ';
        
        // Status update every 5 iterations
        if (iteration % 5 === 0) {
          this.printStatus(entriesThisRound, exitsThisRound);
        }
        
        iteration++;
        await this.sleep(SCAN_INTERVAL_MS);
        
      } catch (error) {
        console.error('  ⚠️ Scan error:', error);
        await this.sleep(SCAN_INTERVAL_MS * 2);
      }
    }
    
    this.printFinalReport();
  }
  
  private openPosition(state: SymbolState, price: number) {
    const quantity = POSITION_SIZE_USD / price;
    const position: Position = {
      id: `POS-${++this.positionIdCounter}`,
      symbol: state.symbol,
      entryPrice: price,
      quantity,
      entryTime: new Date(),
      peakPrice: price
    };
    
    state.positions.push(position);
    this.balance -= POSITION_SIZE_USD;
    
    const priceStr = price < 1 ? price.toFixed(6) : price.toFixed(2);
    console.log(`  🟢 ENTRY ${state.symbol} @ $${priceStr} | Φ=${state.coherence.toFixed(3)} | Pos: ${this.getTotalPositions()}/${MAX_TOTAL_POSITIONS}`);
  }
  
  private closePosition(state: SymbolState, position: Position, price: number, reason: string) {
    const pnl = (price - position.entryPrice) * position.quantity;
    const pnlPercent = (price - position.entryPrice) / position.entryPrice;
    
    this.trades.push({
      id: position.id,
      symbol: state.symbol,
      entryPrice: position.entryPrice,
      exitPrice: price,
      quantity: position.quantity,
      pnl,
      pnlPercent,
      entryTime: position.entryTime,
      exitTime: new Date(),
      exitReason: reason
    });
    
    state.positions = state.positions.filter(p => p.id !== position.id);
    this.balance += price * position.quantity;
    
    const emoji = pnl > 0 ? '🟢' : '🔴';
    const priceStr = price < 1 ? price.toFixed(6) : price.toFixed(2);
    console.log(`  ${emoji} EXIT ${state.symbol} @ $${priceStr} | PnL: $${pnl.toFixed(2)} (${(pnlPercent * 100).toFixed(2)}%) | ${reason}`);
  }
  
  private getTotalPositions(): number {
    let total = 0;
    for (const state of this.symbols.values()) {
      total += state.positions.length;
    }
    return total;
  }
  
  private printStatus(entries: number, exits: number) {
    const winners = this.trades.filter(t => t.pnl > 0).length;
    const hitRate = this.trades.length > 0 ? (winners / this.trades.length * 100).toFixed(1) : '0.0';
    const totalPnl = this.trades.reduce((s, t) => s + t.pnl, 0);
    const direction = this.scanDirection === 'AZ' ? 'A→Z' : 'Z→A';
    
    // Find hottest symbols
    const hotSymbols = Array.from(this.symbols.values())
      .filter(s => s.coherence >= 0.9)
      .slice(0, 3)
      .map(s => s.symbol.replace('USDT', ''))
      .join(', ');
    
    console.log('');
    console.log(`  ═══════════════════════════════════════════════════════════════`);
    console.log(`  📊 ${new Date().toISOString().slice(11, 19)} | ${direction} | Trades: ${this.trades.length} (${hitRate}% win) | PnL: $${totalPnl.toFixed(2)}`);
    console.log(`  💰 Balance: $${this.balance.toFixed(2)} | Positions: ${this.getTotalPositions()}/${MAX_TOTAL_POSITIONS}`);
    if (hotSymbols) console.log(`  🔥 Hot: ${hotSymbols}`);
    console.log(`  ═══════════════════════════════════════════════════════════════`);
    console.log('');
  }
  
  private printFinalReport() {
    const winners = this.trades.filter(t => t.pnl > 0);
    const losers = this.trades.filter(t => t.pnl <= 0);
    const totalPnl = this.trades.reduce((s, t) => s + t.pnl, 0);
    const hitRate = this.trades.length > 0 ? winners.length / this.trades.length : 0;
    
    // Group by symbol
    const bySymbol = new Map<string, TradeRecord[]>();
    for (const trade of this.trades) {
      if (!bySymbol.has(trade.symbol)) bySymbol.set(trade.symbol, []);
      bySymbol.get(trade.symbol)!.push(trade);
    }
    
    // Top performers
    const symbolPerformance = Array.from(bySymbol.entries())
      .map(([symbol, trades]) => ({
        symbol,
        trades: trades.length,
        pnl: trades.reduce((s, t) => s + t.pnl, 0),
        winRate: trades.filter(t => t.pnl > 0).length / trades.length
      }))
      .sort((a, b) => b.pnl - a.pnl);
    
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════════');
    console.log('  ✧  T H E   D A N C E   I S   C O M P L E T E  ✧');
    console.log('  ═══════════════════════════════════════════════════════════════');
    console.log('');
    console.log(`  📊 Total Trades: ${this.trades.length}`);
    console.log(`  🏆 Winners: ${winners.length} | Losers: ${losers.length}`);
    console.log(`  🎯 Hit Rate: ${(hitRate * 100).toFixed(2)}%`);
    console.log(`  💰 Total PnL: $${totalPnl.toFixed(2)}`);
    console.log(`  📈 Initial: $${this.initialBalance.toFixed(2)} → Final: $${this.balance.toFixed(2)}`);
    console.log(`  📊 Return: ${((this.balance - this.initialBalance) / this.initialBalance * 100).toFixed(2)}%`);
    console.log('');
    
    console.log('  🏅 Top Performers:');
    symbolPerformance.slice(0, 5).forEach((s, i) => {
      const medal = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i];
      console.log(`     ${medal} ${s.symbol}: $${s.pnl.toFixed(2)} (${s.trades} trades, ${(s.winRate * 100).toFixed(0)}% win)`);
    });
    console.log('');
    
    if (symbolPerformance.length > 5) {
      console.log('  📉 Bottom Performers:');
      symbolPerformance.slice(-3).reverse().forEach((s) => {
        console.log(`     ⚠️ ${s.symbol}: $${s.pnl.toFixed(2)} (${s.trades} trades, ${(s.winRate * 100).toFixed(0)}% win)`);
      });
      console.log('');
    }
    
    // Wave visualization
    console.log('  🌊 Trade Wave:');
    const waveWidth = 60;
    let wave = '  ';
    for (let i = 0; i < Math.min(waveWidth, this.trades.length); i++) {
      wave += this.trades[i].pnl > 0 ? '◆' : '◇';
    }
    console.log(wave);
    console.log('');
    
    console.log('  ───────────────────────────────────────────────────────────────');
    console.log('  🎵 "We dance through every coin, every asset, every time,');
    console.log('      They cannot stop us all—we move, we flow, we rhyme." 🎵');
    console.log('  ───────────────────────────────────────────────────────────────');
    console.log('');
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
  
  stop() {
    this.isRunning = false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Entry
// ═══════════════════════════════════════════════════════════════════════════

const dance = new DanceOfSpaceTime();

process.on('SIGINT', () => {
  console.log('\n  ⏹️  Stopping the dance...');
  dance.stop();
});

dance.start().catch(console.error);
