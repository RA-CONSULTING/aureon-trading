/**
 * 🎵 THE GRAND SYMPHONY - 500 TRADE SIMULATION 🎵
 * 
 * Real rates, £100 per broker, 500 trades each
 * 
 * Target: 2000 total trades (500 x 4 brokers)
 * Starting Capital: £400 (£100 x 4)
 */

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const TRADES_PER_BROKER = 500;
const BALANCE_PER_BROKER = 100;
const POSITION_SIZE_PCT = 0.05;   // 5% of balance per trade
const STOP_LOSS_PCT = 0.008;      // 0.8% stop loss
const TAKE_PROFIT_PCT = 0.018;    // 1.8% take profit
const MAX_CONCURRENT = 15;        // Max positions per broker

// ═══════════════════════════════════════════════════════════════════════════
// Real Market Prices (November 2025)
// ═══════════════════════════════════════════════════════════════════════════

const REAL_PRICES: Record<string, { price: number; volatility: number }> = {
  // Binance - Crypto
  'BTCUSDT': { price: 95000, volatility: 0.0025 },
  'ETHUSDT': { price: 3500, volatility: 0.003 },
  'SOLUSDT': { price: 250, volatility: 0.004 },
  'XRPUSDT': { price: 1.45, volatility: 0.005 },
  'DOGEUSDT': { price: 0.40, volatility: 0.006 },
  'ADAUSDT': { price: 1.05, volatility: 0.004 },
  'AVAXUSDT': { price: 42, volatility: 0.005 },
  'DOTUSDT': { price: 9.5, volatility: 0.004 },
  'LINKUSDT': { price: 18.5, volatility: 0.004 },
  'MATICUSDT': { price: 0.55, volatility: 0.005 },
  'ATOMUSDT': { price: 12.5, volatility: 0.004 },
  'NEARUSDT': { price: 7.2, volatility: 0.005 },
  'UNIUSDT': { price: 13.5, volatility: 0.004 },
  'AAVEUSDT': { price: 185, volatility: 0.004 },
  'LTCUSDT': { price: 95, volatility: 0.004 },
  
  // Capital.com - CFDs
  'GOLD': { price: 2650, volatility: 0.0012 },
  'SILVER': { price: 31.5, volatility: 0.002 },
  'OIL': { price: 75, volatility: 0.0025 },
  'NATGAS': { price: 3.2, volatility: 0.004 },
  'US500': { price: 6000, volatility: 0.001 },
  'US100': { price: 21000, volatility: 0.0012 },
  'UK100': { price: 8300, volatility: 0.001 },
  'DE40': { price: 19500, volatility: 0.0012 },
  'AAPL_C': { price: 175, volatility: 0.002 },
  'MSFT_C': { price: 420, volatility: 0.0015 },
  'TSLA_C': { price: 350, volatility: 0.004 },
  'NVDA_C': { price: 145, volatility: 0.003 },
  'META_C': { price: 580, volatility: 0.002 },
  'BTCUSD': { price: 95000, volatility: 0.0025 },
  'ETHUSD': { price: 3500, volatility: 0.003 },
  
  // Alpaca - US Stocks
  'AAPL': { price: 175, volatility: 0.002 },
  'MSFT': { price: 420, volatility: 0.0015 },
  'GOOGL': { price: 175, volatility: 0.002 },
  'AMZN': { price: 210, volatility: 0.002 },
  'META': { price: 580, volatility: 0.002 },
  'NVDA': { price: 145, volatility: 0.003 },
  'TSLA': { price: 350, volatility: 0.004 },
  'AMD': { price: 140, volatility: 0.003 },
  'NFLX': { price: 900, volatility: 0.0025 },
  'JPM': { price: 245, volatility: 0.0012 },
  'SPY': { price: 600, volatility: 0.001 },
  'QQQ': { price: 510, volatility: 0.0012 },
  'IWM': { price: 235, volatility: 0.0015 },
  'COIN': { price: 320, volatility: 0.004 },
  'MARA': { price: 25, volatility: 0.005 },
  
  // OANDA - Forex
  'EURUSD': { price: 1.0500, volatility: 0.0006 },
  'GBPUSD': { price: 1.2700, volatility: 0.0008 },
  'USDJPY': { price: 154.50, volatility: 0.0006 },
  'USDCHF': { price: 0.8850, volatility: 0.0006 },
  'AUDUSD': { price: 0.6500, volatility: 0.0008 },
  'USDCAD': { price: 1.4000, volatility: 0.0006 },
  'NZDUSD': { price: 0.5900, volatility: 0.0008 },
  'EURGBP': { price: 0.8270, volatility: 0.0005 },
  'EURJPY': { price: 162.20, volatility: 0.0008 },
  'GBPJPY': { price: 196.20, volatility: 0.001 },
  'XAUUSD': { price: 2650, volatility: 0.0012 },
  'XAGUSD': { price: 31.5, volatility: 0.002 },
  'BCOUSD': { price: 75, volatility: 0.0025 },
  'SPX500': { price: 6000, volatility: 0.001 },
  'NAS100': { price: 21000, volatility: 0.0012 },
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface Position {
  symbol: string;
  direction: 'LONG' | 'SHORT';
  entryPrice: number;
  size: number;
  stopLoss: number;
  takeProfit: number;
}

interface Trade {
  symbol: string;
  direction: 'LONG' | 'SHORT';
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  result: 'WIN' | 'LOSS';
}

interface Broker {
  name: string;
  emoji: string;
  balance: number;
  positions: Map<string, Position>;
  trades: Trade[];
  assets: string[];
  wins: number;
  losses: number;
  prices: Map<string, number>;
}

// ═══════════════════════════════════════════════════════════════════════════
// Price Simulator with Trends
// ═══════════════════════════════════════════════════════════════════════════

class PriceEngine {
  private trends: Map<string, number> = new Map();
  private durations: Map<string, number> = new Map();
  private lastPrices: Map<string, number> = new Map();
  
  getPrice(symbol: string): number {
    const asset = REAL_PRICES[symbol];
    if (!asset) return 100;
    
    // Initialize last price
    if (!this.lastPrices.has(symbol)) {
      this.lastPrices.set(symbol, asset.price);
    }
    
    // Get or create trend
    let trend = this.trends.get(symbol) || 0;
    let duration = this.durations.get(symbol) || 0;
    
    if (duration <= 0) {
      trend = (Math.random() - 0.5) * 2;
      duration = Math.floor(Math.random() * 30) + 10;
      this.trends.set(symbol, trend);
    }
    this.durations.set(symbol, duration - 1);
    
    // Calculate new price
    const lastPrice = this.lastPrices.get(symbol)!;
    const randomMove = (Math.random() - 0.5) * 2 * asset.volatility;
    const trendMove = trend * asset.volatility * 0.5;
    const newPrice = lastPrice * (1 + randomMove + trendMove);
    
    this.lastPrices.set(symbol, newPrice);
    return newPrice;
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Signal Generator
// ═══════════════════════════════════════════════════════════════════════════

class SignalEngine {
  private history: Map<string, number[]> = new Map();
  
  addPrice(key: string, price: number): void {
    if (!this.history.has(key)) {
      this.history.set(key, []);
    }
    const h = this.history.get(key)!;
    h.push(price);
    if (h.length > 30) h.shift();
  }
  
  getSignal(key: string): 'BUY' | 'SELL' | 'HOLD' {
    const h = this.history.get(key);
    if (!h || h.length < 5) return 'HOLD';
    
    // Calculate momentum
    const recent = h.slice(-5);
    const first = recent[0];
    const last = recent[recent.length - 1];
    const momentum = (last - first) / first;
    
    // Calculate volatility score
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    const normalized = range > 0 ? (last - min) / range : 0.5;
    
    // Phi alignment
    const phi = 0.618;
    const phiScore = 1 - Math.abs(normalized - phi);
    
    // Combined signal strength
    const strength = phiScore * 0.5 + Math.abs(momentum) * 1000;
    
    // Generate signal with 35% probability when conditions are right
    if (strength > 0.4 && Math.random() < 0.35) {
      return momentum > 0 ? 'BUY' : 'SELL';
    }
    
    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Simulation
// ═══════════════════════════════════════════════════════════════════════════

async function runSimulation() {
  console.log('\n');
  console.log('  ╔═════════════════════════════════════════════════════════════════╗');
  console.log('  ║                                                                 ║');
  console.log('  ║   🎵 GRAND SYMPHONY - 500 TRADE SIMULATION 🎵                   ║');
  console.log('  ║                                                                 ║');
  console.log('  ║   Target: 500 trades per broker (2000 total)                    ║');
  console.log('  ║   Capital: £100 per broker (£400 total)                         ║');
  console.log('  ║   Risk: 0.8% SL / 1.8% TP per trade                             ║');
  console.log('  ║                                                                 ║');
  console.log('  ╚═════════════════════════════════════════════════════════════════╝');
  console.log('');
  
  const priceEngine = new PriceEngine();
  const signalEngine = new SignalEngine();
  
  // Initialize brokers
  const brokers: Broker[] = [
    {
      name: 'Binance', emoji: '🪙',
      balance: BALANCE_PER_BROKER,
      positions: new Map(), trades: [],
      assets: ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT', 'ATOMUSDT', 'NEARUSDT', 'UNIUSDT', 'AAVEUSDT', 'LTCUSDT'],
      wins: 0, losses: 0, prices: new Map()
    },
    {
      name: 'Capital', emoji: '📊',
      balance: BALANCE_PER_BROKER,
      positions: new Map(), trades: [],
      assets: ['GOLD', 'SILVER', 'OIL', 'NATGAS', 'US500', 'US100', 'UK100', 'DE40', 'AAPL_C', 'MSFT_C', 'TSLA_C', 'NVDA_C', 'META_C', 'BTCUSD', 'ETHUSD'],
      wins: 0, losses: 0, prices: new Map()
    },
    {
      name: 'Alpaca', emoji: '🦙',
      balance: BALANCE_PER_BROKER,
      positions: new Map(), trades: [],
      assets: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'NFLX', 'JPM', 'SPY', 'QQQ', 'IWM', 'COIN', 'MARA'],
      wins: 0, losses: 0, prices: new Map()
    },
    {
      name: 'OANDA', emoji: '💱',
      balance: BALANCE_PER_BROKER,
      positions: new Map(), trades: [],
      assets: ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD', 'EURGBP', 'EURJPY', 'GBPJPY', 'XAUUSD', 'XAGUSD', 'BCOUSD', 'SPX500', 'NAS100'],
      wins: 0, losses: 0, prices: new Map()
    }
  ];
  
  let totalTrades = 0;
  const targetTrades = TRADES_PER_BROKER * 4;
  let tick = 0;
  let direction: 'AZ' | 'ZA' = 'AZ';
  const startTime = Date.now();
  
  console.log('  🎵 Running 2000 trades across 4 brokers...');
  console.log('');
  
  // Main loop
  while (totalTrades < targetTrades) {
    tick++;
    direction = direction === 'AZ' ? 'ZA' : 'AZ';
    
    // Update all prices
    for (const broker of brokers) {
      for (const symbol of broker.assets) {
        const price = priceEngine.getPrice(symbol);
        broker.prices.set(symbol, price);
        signalEngine.addPrice(`${broker.name}:${symbol}`, price);
      }
    }
    
    // Process each broker
    for (const broker of brokers) {
      if (broker.trades.length >= TRADES_PER_BROKER) continue;
      
      // Sort by direction
      const assets = [...broker.assets];
      if (direction === 'ZA') assets.reverse();
      
      // Check positions for exit
      for (const [symbol, pos] of broker.positions) {
        const price = broker.prices.get(symbol) || pos.entryPrice;
        let shouldClose = false;
        let exitPrice = price;
        
        if (pos.direction === 'LONG') {
          if (price <= pos.stopLoss) { shouldClose = true; exitPrice = pos.stopLoss; }
          else if (price >= pos.takeProfit) { shouldClose = true; exitPrice = pos.takeProfit; }
        } else {
          if (price >= pos.stopLoss) { shouldClose = true; exitPrice = pos.stopLoss; }
          else if (price <= pos.takeProfit) { shouldClose = true; exitPrice = pos.takeProfit; }
        }
        
        if (shouldClose) {
          const diff = exitPrice - pos.entryPrice;
          const mult = pos.direction === 'LONG' ? 1 : -1;
          const pnl = (diff / pos.entryPrice) * pos.size * mult;
          
          broker.trades.push({
            symbol, direction: pos.direction,
            entryPrice: pos.entryPrice, exitPrice,
            pnl, result: pnl >= 0 ? 'WIN' : 'LOSS'
          });
          
          broker.balance += pnl;
          if (pnl >= 0) broker.wins++; else broker.losses++;
          broker.positions.delete(symbol);
          totalTrades++;
        }
      }
      
      // Open new positions
      for (const symbol of assets) {
        if (broker.trades.length >= TRADES_PER_BROKER) break;
        if (broker.positions.has(symbol)) continue;
        if (broker.positions.size >= MAX_CONCURRENT) continue;
        
        const signal = signalEngine.getSignal(`${broker.name}:${symbol}`);
        
        if (signal !== 'HOLD') {
          const price = broker.prices.get(symbol)!;
          const size = broker.balance * POSITION_SIZE_PCT;
          
          const stopLoss = signal === 'BUY' 
            ? price * (1 - STOP_LOSS_PCT) 
            : price * (1 + STOP_LOSS_PCT);
          const takeProfit = signal === 'BUY'
            ? price * (1 + TAKE_PROFIT_PCT)
            : price * (1 - TAKE_PROFIT_PCT);
          
          broker.positions.set(symbol, {
            symbol,
            direction: signal === 'BUY' ? 'LONG' : 'SHORT',
            entryPrice: price,
            size, stopLoss, takeProfit
          });
        }
      }
    }
    
    // Progress every 500 ticks
    if (tick % 500 === 0) {
      const pct = ((totalTrades / targetTrades) * 100).toFixed(0);
      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      process.stdout.write(`\r  📊 ${pct}% | ${totalTrades}/2000 trades | ${elapsed}s | 🪙${brokers[0].trades.length} 📊${brokers[1].trades.length} 🦙${brokers[2].trades.length} 💱${brokers[3].trades.length}    `);
    }
  }
  
  const totalTime = ((Date.now() - startTime) / 1000).toFixed(2);
  
  // ═══════════════════════════════════════════════════════════════════════════
  // RESULTS
  // ═══════════════════════════════════════════════════════════════════════════
  
  console.log('\n\n');
  console.log('  ═════════════════════════════════════════════════════════════════');
  console.log('  ✧  SIMULATION COMPLETE  ✧');
  console.log('  ═════════════════════════════════════════════════════════════════');
  console.log('');
  console.log(`  ⏱️  Time: ${totalTime}s | 📈 Trades: ${totalTrades}`);
  console.log('');
  
  console.log('  ┌────────────┬─────────┬─────────┬─────────┬─────────┬───────────┐');
  console.log('  │  Broker    │  Start  │   End   │   W/L   │ HitRate │  Net P&L  │');
  console.log('  ├────────────┼─────────┼─────────┼─────────┼─────────┼───────────┤');
  
  let totalStart = 0, totalEnd = 0, totalWins = 0, totalLosses = 0;
  
  for (const b of brokers) {
    const netPnL = b.balance - BALANCE_PER_BROKER;
    const hitRate = ((b.wins / b.trades.length) * 100).toFixed(1);
    const pnlStr = netPnL >= 0 ? `+£${netPnL.toFixed(2)}` : `-£${Math.abs(netPnL).toFixed(2)}`;
    const emoji = netPnL >= 0 ? '🟢' : '🔴';
    
    console.log(`  │ ${b.emoji} ${b.name.padEnd(8)} │  £${BALANCE_PER_BROKER.toString().padStart(4)} │ £${b.balance.toFixed(2).padStart(6)} │ ${b.wins.toString().padStart(3)}/${b.losses.toString().padStart(3)} │  ${hitRate.padStart(5)}% │ ${emoji}${pnlStr.padStart(8)} │`);
    
    totalStart += BALANCE_PER_BROKER;
    totalEnd += b.balance;
    totalWins += b.wins;
    totalLosses += b.losses;
  }
  
  console.log('  ├────────────┼─────────┼─────────┼─────────┼─────────┼───────────┤');
  
  const grandPnL = totalEnd - totalStart;
  const grandRate = ((totalWins / (totalWins + totalLosses)) * 100).toFixed(1);
  const grandStr = grandPnL >= 0 ? `+£${grandPnL.toFixed(2)}` : `-£${Math.abs(grandPnL).toFixed(2)}`;
  const grandEmoji = grandPnL >= 0 ? '🟢' : '🔴';
  const roi = ((grandPnL / totalStart) * 100).toFixed(2);
  
  console.log(`  │ 🎵 TOTAL   │  £${totalStart.toString().padStart(4)} │ £${totalEnd.toFixed(2).padStart(6)} │${totalWins.toString().padStart(4)}/${totalLosses.toString().padStart(3)} │  ${grandRate.padStart(5)}% │ ${grandEmoji}${grandStr.padStart(8)} │`);
  console.log('  └────────────┴─────────┴─────────┴─────────┴─────────┴───────────┘');
  
  console.log('');
  console.log('  ╔═════════════════════════════════════════════════════════════════╗');
  console.log('  ║                                                                 ║');
  console.log(`  ║   💰 STARTING CAPITAL:  £${totalStart.toFixed(2).padEnd(10)}                        ║`);
  console.log(`  ║   💎 ENDING CAPITAL:    £${totalEnd.toFixed(2).padEnd(10)}                        ║`);
  console.log(`  ║   📈 NET PROFIT:        ${grandStr.padEnd(12)}                        ║`);
  console.log(`  ║   📊 ROI:               ${roi}%                                   ║`);
  console.log(`  ║   🎯 WIN RATE:          ${grandRate}%                                  ║`);
  console.log('  ║                                                                 ║');
  console.log('  ╚═════════════════════════════════════════════════════════════════╝');
  console.log('');
  
  // Top performers
  console.log('  🏆 TOP PERFORMERS:');
  console.log('');
  
  for (const b of brokers) {
    const bySymbol = new Map<string, { pnl: number; count: number; wins: number }>();
    for (const t of b.trades) {
      const s = bySymbol.get(t.symbol) || { pnl: 0, count: 0, wins: 0 };
      s.pnl += t.pnl;
      s.count++;
      if (t.result === 'WIN') s.wins++;
      bySymbol.set(t.symbol, s);
    }
    
    const sorted = [...bySymbol.entries()].sort((a, b) => b[1].pnl - a[1].pnl);
    const top = sorted[0];
    if (top) {
      const pnlStr = top[1].pnl >= 0 ? `+£${top[1].pnl.toFixed(2)}` : `-£${Math.abs(top[1].pnl).toFixed(2)}`;
      console.log(`  ${b.emoji} ${b.name}: ${top[0]} → ${pnlStr} (${top[1].count} trades, ${((top[1].wins/top[1].count)*100).toFixed(0)}% win)`);
    }
  }
  
  console.log('');
  
  // Win wave
  const allTrades = brokers.flatMap(b => b.trades);
  const waveLen = 60;
  let wave = '  ';
  for (let i = 0; i < waveLen; i++) {
    const idx = Math.floor((i / waveLen) * allTrades.length);
    wave += allTrades[idx]?.result === 'WIN' ? '◆' : '◇';
  }
  console.log('  🌊 Trade Results Wave:');
  console.log(wave);
  console.log(`  ◆ Wins: ${totalWins}  ◇ Losses: ${totalLosses}`);
  console.log('');
  
  console.log('  ─────────────────────────────────────────────────────────────────');
  console.log('  🎵 "Four chords, 2000 trades, one unified profit" 🎵');
  console.log('  ─────────────────────────────────────────────────────────────────');
  console.log('');
}

runSimulation().catch(console.error);
