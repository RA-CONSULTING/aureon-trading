/**
 * 🎵 LIVE PAPER TRADING - The Song of Space and Time 🎵
 * 
 * Real paper trades on Binance Testnet to ensure we correct, my friend!
 * 
 * LIVE MODE: Connects to real Binance Testnet with streaming prices!
 * 
 * Setup:
 * 1. Get Binance TESTNET API keys from: https://testnet.binance.vision/
 * 2. Set environment variables:
 *    export BINANCE_TESTNET_API_KEY="your_testnet_api_key"
 *    export BINANCE_TESTNET_API_SECRET="your_testnet_api_secret"
 * 3. Run: npm run paper:live
 */

import crypto from 'node:crypto';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const TESTNET_BASE_URL = 'https://testnet.binance.vision';
const TESTNET_WS_URL = 'wss://testnet.binance.vision/ws';

// For LIVE mode without auth - we use public endpoints only
const LIVE_MODE = process.env.PAPER_LIVE === '1' || process.env.PAPER_LIVE === 'true';
const API_KEY = process.env.BINANCE_TESTNET_API_KEY || '';
const API_SECRET = process.env.BINANCE_TESTNET_API_SECRET || '';

const SYMBOL = process.env.PAPER_SYMBOL || 'BTCUSDT';
const QUOTE_ASSET = 'USDT';
const BASE_ASSET = SYMBOL.replace(QUOTE_ASSET, '');

// Trading parameters (from our simulation)
const ENTRY_COHERENCE = 0.938;
const EXIT_COHERENCE = 0.934;
const TAKE_PROFIT_PCT = 0.018;
const STOP_LOSS_PCT = 0.008;
const POSITION_SIZE_PCT = 0.02; // 2% of balance per trade

// Bot configuration
const BOT_COUNT = 15;
const CHECK_INTERVAL_MS = 1000; // Check every second in live mode

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface Position {
  botId: number;
  symbol: string;
  entryPrice: number;
  quantity: number;
  entryTime: Date;
  orderId: string;
  peakPrice: number;
}

interface TradeRecord {
  botId: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  entryTime: Date;
  exitTime: Date;
  exitReason: string;
}

interface MarketState {
  price: number;
  coherence: number;
  velocity: number;
  timestamp: Date;
}

// ═══════════════════════════════════════════════════════════════════════════
// Binance API Helpers
// ═══════════════════════════════════════════════════════════════════════════

function createSignature(queryString: string): string {
  return crypto.createHmac('sha256', API_SECRET).update(queryString).digest('hex');
}

async function binanceRequest(
  endpoint: string,
  method: 'GET' | 'POST' | 'DELETE' = 'GET',
  params: Record<string, string | number> = {},
  signed = false
): Promise<any> {
  const url = new URL(endpoint, TESTNET_BASE_URL);
  
  if (signed) {
    params.timestamp = Date.now();
    params.recvWindow = 60000;
  }
  
  const queryString = Object.entries(params)
    .map(([k, v]) => `${k}=${v}`)
    .join('&');
  
  if (signed) {
    const signature = createSignature(queryString);
    url.search = `${queryString}&signature=${signature}`;
  } else if (queryString) {
    url.search = queryString;
  }
  
  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers['X-MBX-APIKEY'] = API_KEY;
  }
  
  const response = await fetch(url.toString(), { method, headers });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Binance API error ${response.status}: ${error}`);
  }
  
  return response.json();
}

// ═══════════════════════════════════════════════════════════════════════════
// Market Analysis (Coherence Calculation)
// ═══════════════════════════════════════════════════════════════════════════

class CoherenceEngine {
  private priceHistory: number[] = [];
  private readonly windowSize = 20;
  
  update(price: number): MarketState {
    this.priceHistory.push(price);
    if (this.priceHistory.length > this.windowSize) {
      this.priceHistory.shift();
    }
    
    const coherence = this.calculateCoherence();
    const velocity = this.calculateVelocity();
    
    return {
      price,
      coherence,
      velocity,
      timestamp: new Date()
    };
  }
  
  private calculateCoherence(): number {
    if (this.priceHistory.length < 3) return 0.5;
    
    // Coherence = normalized trend strength + momentum alignment
    const prices = this.priceHistory;
    const returns = prices.slice(1).map((p, i) => (p - prices[i]) / prices[i]);
    
    // Trend strength: consistency of direction
    const positiveReturns = returns.filter(r => r > 0).length;
    const trendStrength = Math.abs(positiveReturns / returns.length - 0.5) * 2;
    
    // Momentum: recent vs historical
    const recentReturns = returns.slice(-5);
    const recentAvg = recentReturns.reduce((a, b) => a + b, 0) / recentReturns.length;
    const overallAvg = returns.reduce((a, b) => a + b, 0) / returns.length;
    const momentumAlign = recentAvg > 0 && overallAvg > 0 ? 1 : (recentAvg < 0 && overallAvg < 0 ? 1 : 0);
    
    // Volatility normalization
    const variance = returns.reduce((s, r) => s + r * r, 0) / returns.length;
    const volFactor = Math.max(0.5, 1 - Math.sqrt(variance) * 10);
    
    // Combine into coherence score [0.5, 1.0]
    const rawCoherence = 0.5 + (trendStrength * 0.3 + momentumAlign * 0.2) * volFactor;
    return Math.min(1, Math.max(0.5, rawCoherence));
  }
  
  private calculateVelocity(): number {
    if (this.priceHistory.length < 2) return 0;
    const recent = this.priceHistory.slice(-3);
    return (recent[recent.length - 1] - recent[0]) / recent[0];
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Paper Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class PaperTradingEngine {
  private positions: Map<number, Position> = new Map();
  private trades: TradeRecord[] = [];
  private coherenceEngine = new CoherenceEngine();
  private balance = 0;
  private initialBalance = 0;
  private isRunning = false;
  
  async start() {
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  L I V E   P A P E R   T R A D I N G   E N G I N E  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    
    if (LIVE_MODE) {
      console.log('  🔴 LIVE MODE ACTIVATED - Real Testnet Prices!');
      console.log('');
      await this.runLiveMode();
      return;
    }
    
    if (!API_KEY || !API_SECRET) {
      console.log('  ⚠️  SIMULATION MODE (No API keys detected)');
      console.log('');
      console.log('  To enable real testnet trading:');
      console.log('  1. Get keys from: https://testnet.binance.vision/');
      console.log('  2. export BINANCE_TESTNET_API_KEY="your_key"');
      console.log('  3. export BINANCE_TESTNET_API_SECRET="your_secret"');
      console.log('');
      console.log('  Or run with LIVE prices (no auth needed):');
      console.log('  PAPER_LIVE=1 npm run paper:live');
      console.log('');
      await this.runSimulatedMode();
      return;
    }
    
    // Test connection and get balance
    try {
      console.log(`  🔗 Connecting to Binance Testnet...`);
      await binanceRequest('/api/v3/ping');
      console.log('  ✅ Connected to Binance Testnet');
      
      const account = await binanceRequest('/api/v3/account', 'GET', {}, true);
      const usdtBalance = account.balances.find((b: any) => b.asset === QUOTE_ASSET);
      this.balance = parseFloat(usdtBalance?.free || '0');
      this.initialBalance = this.balance;
      
      console.log(`  💰 Available Balance: ${this.balance.toFixed(2)} ${QUOTE_ASSET}`);
      console.log(`  📊 Trading Pair: ${SYMBOL}`);
      console.log(`  🤖 Active Bots: ${BOT_COUNT}`);
      console.log('');
      
      this.isRunning = true;
      await this.tradingLoop();
      
    } catch (error) {
      console.error('  ❌ Connection failed:', error);
      console.log('  Falling back to simulation mode...');
      await this.runSimulatedMode();
    }
  }
  
  private async runLiveMode() {
    console.log(`  🔗 Connecting to Binance Testnet...`);
    
    try {
      await binanceRequest('/api/v3/ping');
      console.log('  ✅ Connected to Binance Testnet');
      
      // Get initial price
      const ticker = await binanceRequest('/api/v3/ticker/price', 'GET', { symbol: SYMBOL });
      const initialPrice = parseFloat(ticker.price);
      console.log(`  📊 ${SYMBOL} Price: $${initialPrice.toFixed(2)}`);
      
      this.balance = 10000; // Virtual balance for paper trading
      this.initialBalance = this.balance;
      
      console.log(`  💰 Virtual Balance: $${this.balance.toFixed(2)} USDT`);
      console.log(`  🤖 Active Bots: ${BOT_COUNT}`);
      console.log('');
      console.log('  🎵 Starting the Song of Space and Time...');
      console.log('  ─────────────────────────────────────────────────────────');
      console.log('');
      
      this.isRunning = true;
      const targetTrades = Number(process.env.PAPER_TARGET_TRADES || 50);
      let iteration = 0;
      
      while (this.isRunning && this.trades.length < targetTrades) {
        try {
          // Fetch REAL price from testnet
          const ticker = await binanceRequest('/api/v3/ticker/price', 'GET', { symbol: SYMBOL });
          const price = parseFloat(ticker.price);
          
          // Update coherence with real price
          const state = this.coherenceEngine.update(price);
          
          // Log state every 5 iterations
          if (iteration % 5 === 0) {
            this.logState(state);
          }
          
          // Check for entries (15 bots can enter simultaneously!)
          if (state.coherence >= ENTRY_COHERENCE && state.velocity > 0) {
            const activeCount = this.positions.size;
            const slotsAvailable = BOT_COUNT - activeCount;
            
            for (let botId = 1; botId <= BOT_COUNT && this.positions.size < BOT_COUNT; botId++) {
              if (!this.positions.has(botId)) {
                const positionValue = this.balance * POSITION_SIZE_PCT;
                if (positionValue < 10) continue; // Min position size
                
                const quantity = positionValue / state.price;
                
                this.positions.set(botId, {
                  botId,
                  symbol: SYMBOL,
                  entryPrice: state.price,
                  quantity,
                  entryTime: new Date(),
                  orderId: `LIVE-${Date.now()}-${botId}`,
                  peakPrice: state.price
                });
                this.balance -= positionValue;
                
                console.log(`  🟢 Bot ${botId} ENTRY @ $${state.price.toFixed(2)} | Φ=${state.coherence.toFixed(3)} | Qty=${quantity.toFixed(6)}`);
              }
            }
          }
          
          // Check for exits
          for (const [botId, position] of this.positions) {
            position.peakPrice = Math.max(position.peakPrice, state.price);
            const pnlPercent = (state.price - position.entryPrice) / position.entryPrice;
            const drawdownFromPeak = (position.peakPrice - state.price) / position.peakPrice;
            
            let exitReason = '';
            
            if (pnlPercent >= TAKE_PROFIT_PCT) exitReason = 'target_met';
            else if (pnlPercent <= -STOP_LOSS_PCT) exitReason = 'stop_loss';
            else if (pnlPercent > 0.005 && drawdownFromPeak > 0.003) exitReason = 'trailing_stop';
            else if (state.coherence < EXIT_COHERENCE && pnlPercent > 0) exitReason = 'coherence_drop';
            
            if (exitReason) {
              const pnl = (state.price - position.entryPrice) * position.quantity;
              this.trades.push({
                botId,
                symbol: SYMBOL,
                side: 'SELL',
                entryPrice: position.entryPrice,
                exitPrice: state.price,
                quantity: position.quantity,
                pnl,
                pnlPercent,
                entryTime: position.entryTime,
                exitTime: new Date(),
                exitReason
              });
              this.positions.delete(botId);
              this.balance += state.price * position.quantity;
              
              const emoji = pnl > 0 ? '🟢' : '🔴';
              console.log(`  ${emoji} Bot ${botId} EXIT @ $${state.price.toFixed(2)} | PnL: $${pnl.toFixed(2)} (${(pnlPercent * 100).toFixed(2)}%) | ${exitReason}`);
            }
          }
          
          iteration++;
          await this.sleep(CHECK_INTERVAL_MS);
          
        } catch (error) {
          console.error('  ⚠️ Error fetching price:', error);
          await this.sleep(CHECK_INTERVAL_MS * 2);
        }
      }
      
      await this.printFinalReport();
      
    } catch (error) {
      console.error('  ❌ Live mode failed:', error);
    }
  }
  
  private async tradingLoop() {
    console.log('  🎵 Starting the Song of Space and Time...');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('');
    
    let iteration = 0;
    const targetTrades = Number(process.env.PAPER_TARGET_TRADES || 50);
    
    while (this.isRunning && this.trades.length < targetTrades) {
      try {
        // Get current price
        const ticker = await binanceRequest('/api/v3/ticker/price', 'GET', { symbol: SYMBOL });
        const price = parseFloat(ticker.price);
        
        // Update coherence
        const state = this.coherenceEngine.update(price);
        
        // Log state every 10 iterations
        if (iteration % 10 === 0) {
          this.logState(state);
        }
        
        // Check for entries
        await this.checkEntries(state);
        
        // Check for exits
        await this.checkExits(state);
        
        iteration++;
        await this.sleep(CHECK_INTERVAL_MS);
        
      } catch (error) {
        console.error('  ⚠️ Error in trading loop:', error);
        await this.sleep(CHECK_INTERVAL_MS * 2);
      }
    }
    
    await this.printFinalReport();
  }
  
  private async checkEntries(state: MarketState) {
    // Entry signal: coherence above threshold with positive velocity
    if (state.coherence >= ENTRY_COHERENCE && state.velocity > 0) {
      const activeCount = this.positions.size;
      const slotsAvailable = BOT_COUNT - activeCount;
      
      if (slotsAvailable > 0) {
        // Find available bot IDs
        for (let botId = 1; botId <= BOT_COUNT && this.positions.size < BOT_COUNT; botId++) {
          if (!this.positions.has(botId)) {
            await this.openPosition(botId, state);
            break; // One entry per tick
          }
        }
      }
    }
  }
  
  private async checkExits(state: MarketState) {
    for (const [botId, position] of this.positions) {
      position.peakPrice = Math.max(position.peakPrice, state.price);
      
      const pnlPercent = (state.price - position.entryPrice) / position.entryPrice;
      const drawdownFromPeak = (position.peakPrice - state.price) / position.peakPrice;
      
      let exitReason = '';
      
      // Take profit
      if (pnlPercent >= TAKE_PROFIT_PCT) {
        exitReason = 'target_met';
      }
      // Stop loss
      else if (pnlPercent <= -STOP_LOSS_PCT) {
        exitReason = 'stop_loss';
      }
      // Trailing stop (after 0.5% profit, trail at 0.3%)
      else if (pnlPercent > 0.005 && drawdownFromPeak > 0.003) {
        exitReason = 'trailing_stop';
      }
      // Coherence drop
      else if (state.coherence < EXIT_COHERENCE) {
        exitReason = 'coherence_drop';
      }
      
      if (exitReason) {
        await this.closePosition(botId, state, exitReason);
      }
    }
  }
  
  private async openPosition(botId: number, state: MarketState) {
    const positionValue = this.balance * POSITION_SIZE_PCT;
    const quantity = positionValue / state.price;
    
    try {
      // Place market buy order on testnet
      const order = await binanceRequest('/api/v3/order', 'POST', {
        symbol: SYMBOL,
        side: 'BUY',
        type: 'MARKET',
        quoteOrderQty: positionValue.toFixed(2)
      }, true);
      
      const position: Position = {
        botId,
        symbol: SYMBOL,
        entryPrice: parseFloat(order.fills?.[0]?.price || state.price),
        quantity: parseFloat(order.executedQty || quantity),
        entryTime: new Date(),
        orderId: order.orderId,
        peakPrice: state.price
      };
      
      this.positions.set(botId, position);
      this.balance -= positionValue;
      
      console.log(`  🟢 Bot ${botId} ENTRY @ ${position.entryPrice.toFixed(2)} | Φ=${state.coherence.toFixed(3)} | Qty=${position.quantity.toFixed(6)}`);
      
    } catch (error) {
      console.error(`  ❌ Bot ${botId} entry failed:`, error);
    }
  }
  
  private async closePosition(botId: number, state: MarketState, reason: string) {
    const position = this.positions.get(botId);
    if (!position) return;
    
    try {
      // Place market sell order on testnet
      const order = await binanceRequest('/api/v3/order', 'POST', {
        symbol: SYMBOL,
        side: 'SELL',
        type: 'MARKET',
        quantity: position.quantity.toFixed(6)
      }, true);
      
      const exitPrice = parseFloat(order.fills?.[0]?.price || state.price);
      const pnl = (exitPrice - position.entryPrice) * position.quantity;
      const pnlPercent = (exitPrice - position.entryPrice) / position.entryPrice;
      
      const trade: TradeRecord = {
        botId,
        symbol: SYMBOL,
        side: 'SELL',
        entryPrice: position.entryPrice,
        exitPrice,
        quantity: position.quantity,
        pnl,
        pnlPercent,
        entryTime: position.entryTime,
        exitTime: new Date(),
        exitReason: reason
      };
      
      this.trades.push(trade);
      this.positions.delete(botId);
      this.balance += exitPrice * position.quantity;
      
      const emoji = pnl > 0 ? '🟢' : '🔴';
      console.log(`  ${emoji} Bot ${botId} EXIT @ ${exitPrice.toFixed(2)} | PnL: $${pnl.toFixed(2)} (${(pnlPercent * 100).toFixed(2)}%) | ${reason}`);
      
    } catch (error) {
      console.error(`  ❌ Bot ${botId} exit failed:`, error);
    }
  }
  
  private logState(state: MarketState) {
    const activePositions = this.positions.size;
    const completedTrades = this.trades.length;
    const winners = this.trades.filter(t => t.pnl > 0).length;
    const hitRate = completedTrades > 0 ? (winners / completedTrades * 100).toFixed(1) : '0.0';
    
    console.log(`  📊 ${state.timestamp.toISOString().slice(11, 19)} | ${SYMBOL}: $${state.price.toFixed(2)} | Φ=${state.coherence.toFixed(3)} | Active: ${activePositions}/${BOT_COUNT} | Trades: ${completedTrades} (${hitRate}% win)`);
  }
  
  private async runSimulatedMode() {
    console.log('  🎮 Running in SIMULATION mode with mock data...');
    console.log('');
    
    this.balance = 10000;
    this.initialBalance = this.balance;
    
    const targetTrades = Number(process.env.PAPER_TARGET_TRADES || 50);
    let mockPrice = 95000 + Math.random() * 5000;
    
    for (let i = 0; i < 1000 && this.trades.length < targetTrades; i++) {
      // Simulate price movement
      const trend = Math.sin(i / 50) * 0.001;
      const noise = (Math.random() - 0.5) * 0.002;
      mockPrice *= (1 + trend + noise);
      
      const state = this.coherenceEngine.update(mockPrice);
      
      if (i % 20 === 0) {
        this.logState(state);
      }
      
      // Simulated entries
      if (state.coherence >= ENTRY_COHERENCE && state.velocity > 0) {
        for (let botId = 1; botId <= BOT_COUNT; botId++) {
          if (!this.positions.has(botId)) {
            const positionValue = this.balance * POSITION_SIZE_PCT;
            const quantity = positionValue / state.price;
            
            this.positions.set(botId, {
              botId,
              symbol: SYMBOL,
              entryPrice: state.price,
              quantity,
              entryTime: new Date(),
              orderId: `SIM-${Date.now()}`,
              peakPrice: state.price
            });
            this.balance -= positionValue;
            
            console.log(`  🟢 Bot ${botId} ENTRY @ ${state.price.toFixed(2)} | Φ=${state.coherence.toFixed(3)}`);
            break;
          }
        }
      }
      
      // Simulated exits
      for (const [botId, position] of this.positions) {
        position.peakPrice = Math.max(position.peakPrice, state.price);
        const pnlPercent = (state.price - position.entryPrice) / position.entryPrice;
        
        let exitReason = '';
        if (pnlPercent >= TAKE_PROFIT_PCT) exitReason = 'target_met';
        else if (pnlPercent <= -STOP_LOSS_PCT) exitReason = 'stop_loss';
        else if (state.coherence < EXIT_COHERENCE && pnlPercent > 0) exitReason = 'coherence_drop';
        
        if (exitReason) {
          const pnl = (state.price - position.entryPrice) * position.quantity;
          this.trades.push({
            botId,
            symbol: SYMBOL,
            side: 'SELL',
            entryPrice: position.entryPrice,
            exitPrice: state.price,
            quantity: position.quantity,
            pnl,
            pnlPercent,
            entryTime: position.entryTime,
            exitTime: new Date(),
            exitReason
          });
          this.positions.delete(botId);
          this.balance += state.price * position.quantity;
          
          const emoji = pnl > 0 ? '🟢' : '🔴';
          console.log(`  ${emoji} Bot ${botId} EXIT @ ${state.price.toFixed(2)} | PnL: $${pnl.toFixed(2)} | ${exitReason}`);
        }
      }
      
      await this.sleep(50); // Fast simulation
    }
    
    await this.printFinalReport();
  }
  
  private async printFinalReport() {
    const winners = this.trades.filter(t => t.pnl > 0);
    const losers = this.trades.filter(t => t.pnl <= 0);
    const totalPnl = this.trades.reduce((s, t) => s + t.pnl, 0);
    const hitRate = this.trades.length > 0 ? winners.length / this.trades.length : 0;
    
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  F I N A L   R E P O R T  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    console.log(`  📊 Total Trades: ${this.trades.length}`);
    console.log(`  🏆 Winners: ${winners.length} | Losers: ${losers.length}`);
    console.log(`  🎯 Hit Rate: ${(hitRate * 100).toFixed(2)}%`);
    console.log(`  💰 Total PnL: $${totalPnl.toFixed(2)}`);
    console.log(`  📈 Initial Balance: $${this.initialBalance.toFixed(2)}`);
    console.log(`  💵 Final Balance: $${this.balance.toFixed(2)}`);
    console.log(`  📊 Return: ${((this.balance - this.initialBalance) / this.initialBalance * 100).toFixed(2)}%`);
    console.log('');
    
    // Wave visualization
    console.log('  🌊 Trade Wave:');
    const waveWidth = 50;
    let wave = '  ';
    for (let i = 0; i < Math.min(waveWidth, this.trades.length); i++) {
      wave += this.trades[i].pnl > 0 ? '◆' : '◇';
    }
    console.log(wave);
    console.log('');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('  "We ride the wave, through space and time,');
    console.log('   Each note a trade, each beat sublime."');
    console.log('  ─────────────────────────────────────────────────────────');
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

const engine = new PaperTradingEngine();

process.on('SIGINT', () => {
  console.log('\n  ⏹️  Stopping paper trading...');
  engine.stop();
});

engine.start().catch(console.error);
