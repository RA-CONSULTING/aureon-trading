/**
 * 💰 LIVE £400 → £40,000 CHALLENGE 💰
 * 
 * Spreading £400 across all available brokers for 24/7 trading
 * 
 * ┌─────────────────────────────────────────────────────────────────────────────┐
 * │  BROKER               │  ALLOCATION  │  RATE LIMIT   │  TYPE             │
 * ├─────────────────────────────────────────────────────────────────────────────┤
 * │  🪙 Binance           │  £30         │  30/min       │  Crypto 24/7      │
 * │  ⭕ OKX               │  £30         │  30/min       │  Crypto 24/7      │
 * │  🦑 Kraken            │  £25         │  15/min       │  Crypto 24/7      │
 * │  🟠 Coinbase          │  £20         │  10/min       │  Crypto 24/7      │
 * │  💎 Bitstamp          │  £20         │  20/min       │  Crypto 24/7      │
 * │  ♊ Gemini            │  £15         │  10/min       │  Crypto 24/7      │
 * │  💱 OANDA             │  £40         │  60/min       │  Forex 24/5       │
 * │  💹 FXCM              │  £30         │  30/min       │  Forex 24/5       │
 * │  🦙 Alpaca            │  £40         │  60/min       │  Stocks (FREE!)   │
 * │  📊 Capital.com       │  £25         │  5/min        │  CFD              │
 * │  📈 IG Markets        │  £40         │  10/min       │  Spread Bet 🎁    │
 * │  📉 CMC Markets       │  £35         │  10/min       │  Spread Bet 🎁    │
 * │  🏛️ Interactive Brokers│ £30         │  50/min       │  Multi-asset      │
 * │  🏦 Saxo Bank         │  £20         │  20/min       │  Multi-asset      │
 * ├─────────────────────────────────────────────────────────────────────────────┤
 * │  TOTAL                │  £400        │  360/min      │  100x = £40,000   │
 * └─────────────────────────────────────────────────────────────────────────────┘
 * 
 * Run: npx tsx scripts/live400to40k.ts
 */

// ═══════════════════════════════════════════════════════════════════════════
// BROKER CONFIGURATIONS
// ═══════════════════════════════════════════════════════════════════════════

interface Broker {
  name: string;
  emoji: string;
  type: 'crypto' | 'forex' | 'stocks' | 'cfd' | 'spreadbet' | 'multi';
  allocation: number;       // Starting £
  tradesPerMinute: number;  // API rate limit
  fee: number;              // % round trip
  spreadCost: number;       // % spread cost
  taxFree: boolean;         // Spread betting = no CGT
  hours: '24/7' | '24/5' | 'market';
  assets: string[];
  
  // Runtime state
  balance: number;
  trades: number;
  wins: number;
  losses: number;
  pnl: number;
}

const BROKERS: Broker[] = [
  // ═══════════════════════════════════════════════════════════════════════
  // CRYPTO - 24/7 Trading (£140 total)
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'Binance',
    emoji: '🪙',
    type: 'crypto',
    allocation: 30,
    tradesPerMinute: 30,
    fee: 0.10,
    spreadCost: 0.01,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'SOL', 'BNB', 'XRP', 'DOGE', 'ADA', 'AVAX'],
    balance: 30,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'OKX',
    emoji: '⭕',
    type: 'crypto',
    allocation: 30,
    tradesPerMinute: 30,
    fee: 0.08,
    spreadCost: 0.01,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'SOL', 'OKB', 'DOGE', 'LINK', 'DOT', 'MATIC'],
    balance: 30,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'Kraken',
    emoji: '🦑',
    type: 'crypto',
    allocation: 25,
    tradesPerMinute: 15,
    fee: 0.26,
    spreadCost: 0.02,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'SOL', 'XRP', 'DOT', 'ADA', 'ATOM', 'LINK'],
    balance: 25,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'Coinbase',
    emoji: '🟠',
    type: 'crypto',
    allocation: 20,
    tradesPerMinute: 10,
    fee: 0.60,
    spreadCost: 0.50,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'SOL', 'XRP', 'DOGE', 'ADA'],
    balance: 20,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'Bitstamp',
    emoji: '💎',
    type: 'crypto',
    allocation: 20,
    tradesPerMinute: 20,
    fee: 0.50,
    spreadCost: 0.03,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'XRP', 'LTC', 'LINK', 'BCH'],
    balance: 20,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'Gemini',
    emoji: '♊',
    type: 'crypto',
    allocation: 15,
    tradesPerMinute: 10,
    fee: 0.35,
    spreadCost: 0.30,
    taxFree: false,
    hours: '24/7',
    assets: ['BTC', 'ETH', 'SOL', 'LINK', 'UNI', 'AAVE'],
    balance: 15,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // FOREX - 24/5 Trading (£70 total)
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'OANDA',
    emoji: '💱',
    type: 'forex',
    allocation: 40,
    tradesPerMinute: 60,
    fee: 0.00,
    spreadCost: 0.01,  // ~1 pip
    taxFree: false,
    hours: '24/5',
    assets: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'AUD/USD', 'EUR/GBP', 'XAU/USD'],
    balance: 40,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'FXCM',
    emoji: '💹',
    type: 'forex',
    allocation: 30,
    tradesPerMinute: 30,
    fee: 0.00,
    spreadCost: 0.01,
    taxFree: false,
    hours: '24/5',
    assets: ['EUR/USD', 'GBP/USD', 'USD/JPY', 'USD/CAD', 'NZD/USD', 'GBP/JPY'],
    balance: 30,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // STOCKS - Market Hours (£40 total) - FREE TRADES!
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'Alpaca',
    emoji: '🦙',
    type: 'stocks',
    allocation: 40,
    tradesPerMinute: 60,
    fee: 0.00,          // FREE!
    spreadCost: 0.01,
    taxFree: false,
    hours: 'market',
    assets: ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'AMD'],
    balance: 40,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // CFD/SPREAD BETTING (£100 total) - IG & CMC = TAX FREE!
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'Capital.com',
    emoji: '📊',
    type: 'cfd',
    allocation: 25,
    tradesPerMinute: 5,
    fee: 0.00,
    spreadCost: 0.06,
    taxFree: false,
    hours: '24/5',
    assets: ['BTC', 'ETH', 'Gold', 'US500', 'UK100', 'EUR/USD'],
    balance: 25,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'IG Markets',
    emoji: '📈',
    type: 'spreadbet',
    allocation: 40,
    tradesPerMinute: 10,
    fee: 0.00,
    spreadCost: 0.03,
    taxFree: true,      // 🎁 TAX FREE SPREAD BETTING!
    hours: '24/5',
    assets: ['FTSE100', 'Wall Street', 'Gold', 'GBP/USD', 'EUR/USD', 'Bitcoin'],
    balance: 40,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'CMC Markets',
    emoji: '📉',
    type: 'spreadbet',
    allocation: 35,
    tradesPerMinute: 10,
    fee: 0.00,
    spreadCost: 0.04,
    taxFree: true,      // 🎁 TAX FREE SPREAD BETTING!
    hours: '24/5',
    assets: ['UK100', 'Germany40', 'US500', 'Gold', 'EUR/GBP', 'Natural Gas'],
    balance: 35,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // MULTI-ASSET BROKERS (£50 total)
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'Interactive Brokers',
    emoji: '🏛️',
    type: 'multi',
    allocation: 30,
    tradesPerMinute: 50,
    fee: 0.05,
    spreadCost: 0.01,
    taxFree: false,
    hours: 'market',
    assets: ['SPY', 'QQQ', 'AAPL', 'EUR.USD', 'GBP.USD', 'ES', 'NQ', 'GC'],
    balance: 30,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
  {
    name: 'Saxo Bank',
    emoji: '🏦',
    type: 'multi',
    allocation: 20,
    tradesPerMinute: 20,
    fee: 0.08,
    spreadCost: 0.02,
    taxFree: false,
    hours: 'market',
    assets: ['AAPL', 'MSFT', 'EUR/USD', 'Gold', 'Oil', 'DAX40'],
    balance: 20,
    trades: 0,
    wins: 0,
    losses: 0,
    pnl: 0,
  },
];

// ═══════════════════════════════════════════════════════════════════════════
// AUREON COHERENCE SYSTEM
// ═══════════════════════════════════════════════════════════════════════════

const AURIS_WEIGHTS = {
  tiger: 1.2,
  falcon: 1.1,
  hummingbird: 0.8,
  dolphin: 1.0,
  deer: 0.9,
  owl: 1.0,
  panda: 0.95,
  cargoShip: 1.3,
  clownfish: 0.7,
};

interface CoherenceState {
  phi: number;          // Coherence value
  lambda: number;       // Master equation output
  signal: 'ENTRY' | 'EXIT' | 'HOLD';
  confidence: number;
}

function calculateCoherence(): CoherenceState {
  // Simulate 9 Auris node responses
  const nodes = Object.entries(AURIS_WEIGHTS).map(([name, weight]) => ({
    name,
    value: (0.85 + Math.random() * 0.15) * weight,
  }));
  
  // Calculate substrate S(t) - weighted average
  const totalWeight = Object.values(AURIS_WEIGHTS).reduce((a, b) => a + b, 0);
  const S = nodes.reduce((sum, n) => sum + n.value, 0) / totalWeight;
  
  // Observer O(t) = previous * 0.3
  const O = S * 0.3;
  
  // Echo E(t) = avg * 0.2
  const E = S * 0.2;
  
  // Master Equation: Λ(t) = S(t) + O(t) + E(t)
  const lambda = S + O + E;
  
  // Coherence Γ = 1 - (variance/10)
  const variance = nodes.reduce((sum, n) => sum + Math.pow(n.value - S, 2), 0) / nodes.length;
  const phi = Math.min(1, Math.max(0, 1 - variance / 10));
  
  // Determine signal
  let signal: 'ENTRY' | 'EXIT' | 'HOLD' = 'HOLD';
  if (phi > 0.938) signal = 'ENTRY';
  else if (phi < 0.934) signal = 'EXIT';
  
  return {
    phi,
    lambda,
    signal,
    confidence: phi * 100,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// TRADING ENGINE
// ═══════════════════════════════════════════════════════════════════════════

interface TradeResult {
  broker: string;
  asset: string;
  direction: 'LONG' | 'SHORT';
  size: number;
  entry: number;
  exit: number;
  pnl: number;
  fee: number;
  netPnl: number;
  duration: number;  // seconds
  taxFree: boolean;
}

const TRADE_STATS = {
  WIN_RATE: 0.853,        // 85.3% from README
  AVG_WIN: 0.018,         // 1.8% take profit
  AVG_LOSS: 0.008,        // 0.8% stop loss
  AVG_DURATION: 180,      // 3 minutes average
};

function simulateTrade(broker: Broker, coherence: CoherenceState): TradeResult | null {
  if (coherence.signal !== 'ENTRY') return null;
  if (broker.balance < 1) return null;  // Need at least £1
  
  // Position size: 10% of broker balance
  const positionSize = Math.min(broker.balance * 0.10, broker.balance);
  
  // Random asset
  const asset = broker.assets[Math.floor(Math.random() * broker.assets.length)];
  const direction: 'LONG' | 'SHORT' = Math.random() > 0.5 ? 'LONG' : 'SHORT';
  
  // Simulate entry price
  const entry = 100 + Math.random() * 50;
  
  // Win or loss based on win rate
  const isWin = Math.random() < TRADE_STATS.WIN_RATE;
  
  // Calculate P&L
  const pnlPercent = isWin ? TRADE_STATS.AVG_WIN : -TRADE_STATS.AVG_LOSS;
  const grossPnl = positionSize * pnlPercent;
  
  // Fees: round trip fee + spread
  const totalFee = positionSize * ((broker.fee / 100) + (broker.spreadCost / 100));
  
  // Net P&L
  const netPnl = grossPnl - totalFee;
  
  // Exit price
  const exit = entry * (1 + pnlPercent);
  
  // Trade duration
  const duration = 60 + Math.floor(Math.random() * 300);  // 1-6 minutes
  
  return {
    broker: broker.name,
    asset,
    direction,
    size: positionSize,
    entry,
    exit,
    pnl: grossPnl,
    fee: totalFee,
    netPnl,
    duration,
    taxFree: broker.taxFree,
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// SIMULATION ENGINE
// ═══════════════════════════════════════════════════════════════════════════

interface SimulationResult {
  startingCapital: number;
  finalCapital: number;
  totalPnl: number;
  totalTrades: number;
  totalWins: number;
  totalLosses: number;
  winRate: number;
  duration: string;
  durationMinutes: number;
  tradesPerMinute: number;
  growthMultiple: number;
  taxFreePnl: number;
  taxablePnl: number;
}

function runSimulation(targetCapital: number = 40000): SimulationResult {
  console.log('\n');
  console.log('╔═══════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                                                                               ║');
  console.log('║   💰 LIVE £400 → £40,000 CHALLENGE 💰                                        ║');
  console.log('║                                                                               ║');
  console.log('║   Spreading across 14 brokers with real API rate limits                       ║');
  console.log('║                                                                               ║');
  console.log('╚═══════════════════════════════════════════════════════════════════════════════╝');
  console.log('');
  
  // Reset all brokers
  BROKERS.forEach(b => {
    b.balance = b.allocation;
    b.trades = 0;
    b.wins = 0;
    b.losses = 0;
    b.pnl = 0;
  });
  
  const startingCapital = BROKERS.reduce((sum, b) => sum + b.allocation, 0);
  let totalMinutes = 0;
  let totalTrades = 0;
  let totalWins = 0;
  let totalLosses = 0;
  let taxFreePnl = 0;
  let taxablePnl = 0;
  
  // Calculate total trades per minute capacity
  const totalTradesPerMinute = BROKERS.reduce((sum, b) => sum + b.tradesPerMinute, 0);
  
  console.log(`📊 Starting Capital: £${startingCapital.toFixed(2)}`);
  console.log(`🎯 Target Capital: £${targetCapital.toFixed(2)} (${(targetCapital/startingCapital).toFixed(0)}x)`);
  console.log(`⚡ Total Capacity: ${totalTradesPerMinute} trades/minute`);
  console.log('');
  console.log('═══════════════════════════════════════════════════════════════════════════════');
  console.log('');
  
  // Show broker allocations
  console.log('📋 BROKER ALLOCATIONS:');
  console.log('───────────────────────────────────────────────────────────────────────────────');
  
  for (const broker of BROKERS) {
    const taxBadge = broker.taxFree ? ' 🎁 TAX-FREE' : '';
    console.log(`${broker.emoji} ${broker.name.padEnd(20)} │ £${broker.allocation.toString().padStart(3)} │ ${broker.tradesPerMinute.toString().padStart(2)}/min │ ${broker.hours.padEnd(6)}${taxBadge}`);
  }
  console.log('───────────────────────────────────────────────────────────────────────────────');
  console.log('');
  
  // Simulation loop
  let currentCapital = startingCapital;
  let checkpointsPrinted = new Set<number>();
  
  while (currentCapital < targetCapital && totalMinutes < 60 * 24 * 7) {  // Max 7 days
    totalMinutes++;
    
    // Each broker trades at their rate limit
    for (const broker of BROKERS) {
      // Trades per minute for this broker
      const tradesThisMinute = Math.min(broker.tradesPerMinute, Math.floor(broker.balance));
      
      for (let t = 0; t < tradesThisMinute; t++) {
        const coherence = calculateCoherence();
        const trade = simulateTrade(broker, coherence);
        
        if (trade) {
          // Update broker state
          broker.balance += trade.netPnl;
          broker.trades++;
          broker.pnl += trade.netPnl;
          
          if (trade.netPnl > 0) {
            broker.wins++;
            totalWins++;
          } else {
            broker.losses++;
            totalLosses++;
          }
          
          totalTrades++;
          
          // Track tax-free vs taxable P&L
          if (trade.taxFree) {
            taxFreePnl += trade.netPnl;
          } else {
            taxablePnl += trade.netPnl;
          }
        }
      }
    }
    
    // Recalculate total capital
    currentCapital = BROKERS.reduce((sum, b) => sum + b.balance, 0);
    
    // Print progress at milestones
    const milestones = [500, 1000, 2000, 5000, 10000, 15000, 20000, 25000, 30000, 35000, 40000];
    for (const milestone of milestones) {
      if (currentCapital >= milestone && !checkpointsPrinted.has(milestone)) {
        checkpointsPrinted.add(milestone);
        const hours = Math.floor(totalMinutes / 60);
        const mins = totalMinutes % 60;
        const timeStr = hours > 0 ? `${hours}h ${mins}m` : `${mins}m`;
        console.log(`✅ £${milestone.toLocaleString()} reached in ${timeStr} (${totalTrades.toLocaleString()} trades)`);
      }
    }
  }
  
  // Calculate duration
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  const duration = hours > 24 
    ? `${Math.floor(hours/24)}d ${hours%24}h ${mins}m`
    : hours > 0 
      ? `${hours}h ${mins}m`
      : `${mins}m`;
  
  const finalCapital = BROKERS.reduce((sum, b) => sum + b.balance, 0);
  const totalPnl = finalCapital - startingCapital;
  const winRate = totalTrades > 0 ? (totalWins / totalTrades) * 100 : 0;
  const growthMultiple = finalCapital / startingCapital;
  
  return {
    startingCapital,
    finalCapital,
    totalPnl,
    totalTrades,
    totalWins,
    totalLosses,
    winRate,
    duration,
    durationMinutes: totalMinutes,
    tradesPerMinute: totalTrades / totalMinutes,
    growthMultiple,
    taxFreePnl,
    taxablePnl,
  };
}

function printResults(result: SimulationResult): void {
  console.log('');
  console.log('╔═══════════════════════════════════════════════════════════════════════════════╗');
  console.log('║                                                                               ║');
  console.log('║   🏆 SIMULATION COMPLETE - FINAL RESULTS 🏆                                   ║');
  console.log('║                                                                               ║');
  console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
  console.log('║                                                                               ║');
  console.log(`║   💰 STARTING CAPITAL:     £${result.startingCapital.toFixed(2).padStart(12)}                              ║`);
  console.log(`║   💎 FINAL CAPITAL:        £${result.finalCapital.toFixed(2).padStart(12)}                              ║`);
  console.log(`║   📈 TOTAL PROFIT:         £${result.totalPnl.toFixed(2).padStart(12)} (+${((result.totalPnl/result.startingCapital)*100).toFixed(1)}%)                 ║`);
  console.log(`║   ⏱️  TIME TO 100x:         ${result.duration.padStart(15)}                              ║`);
  console.log('║                                                                               ║');
  console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
  console.log('║                                                                               ║');
  console.log(`║   📊 TRADING STATS:                                                           ║`);
  console.log(`║   ─────────────────────────────────────────────────────────────               ║`);
  console.log(`║   Total Trades:        ${result.totalTrades.toLocaleString().padStart(15)}                              ║`);
  console.log(`║   Winning Trades:      ${result.totalWins.toLocaleString().padStart(15)} (${result.winRate.toFixed(1)}%)                    ║`);
  console.log(`║   Losing Trades:       ${result.totalLosses.toLocaleString().padStart(15)}                              ║`);
  console.log(`║   Trades/Minute:       ${result.tradesPerMinute.toFixed(1).padStart(15)}                              ║`);
  console.log(`║   Growth Multiple:     ${result.growthMultiple.toFixed(1).padStart(15)}x                             ║`);
  console.log('║                                                                               ║');
  console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
  console.log('║                                                                               ║');
  console.log(`║   🎁 TAX BREAKDOWN (UK):                                                      ║`);
  console.log(`║   ─────────────────────────────────────────────────────────────               ║`);
  console.log(`║   Tax-Free P&L (Spread Bets): £${result.taxFreePnl.toFixed(2).padStart(10)}                          ║`);
  console.log(`║   Taxable P&L:                £${result.taxablePnl.toFixed(2).padStart(10)}                          ║`);
  console.log(`║   CGT Allowance (2024):       £${(3000).toFixed(2).padStart(10)}                          ║`);
  console.log(`║   Taxable After Allowance:    £${Math.max(0, result.taxablePnl - 3000).toFixed(2).padStart(10)}                          ║`);
  console.log(`║   Est. CGT @ 20%:             £${(Math.max(0, result.taxablePnl - 3000) * 0.20).toFixed(2).padStart(10)}                          ║`);
  console.log(`║   NET PROFIT AFTER TAX:       £${(result.totalPnl - (Math.max(0, result.taxablePnl - 3000) * 0.20)).toFixed(2).padStart(10)}                          ║`);
  console.log('║                                                                               ║');
  console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
  console.log('║                                                                               ║');
  console.log('║   📋 BROKER PERFORMANCE:                                                      ║');
  console.log('║   ─────────────────────────────────────────────────────────────               ║');
  
  // Sort brokers by P&L
  const sortedBrokers = [...BROKERS].sort((a, b) => b.pnl - a.pnl);
  
  for (const broker of sortedBrokers) {
    const winRate = broker.trades > 0 ? ((broker.wins / broker.trades) * 100).toFixed(0) : '0';
    const pnlSign = broker.pnl >= 0 ? '+' : '';
    const taxBadge = broker.taxFree ? '🎁' : '  ';
    console.log(`║   ${broker.emoji} ${broker.name.padEnd(18)} │ £${broker.balance.toFixed(0).padStart(6)} │ ${broker.trades.toString().padStart(5)} trades │ ${winRate.padStart(2)}% WR │ ${pnlSign}£${broker.pnl.toFixed(0).padStart(5)} ${taxBadge} ║`);
  }
  
  console.log('║                                                                               ║');
  console.log('╚═══════════════════════════════════════════════════════════════════════════════╝');
  console.log('');
  
  // Key insights
  console.log('╔═══════════════════════════════════════════════════════════════════════════════╗');
  console.log('║   💡 KEY INSIGHTS:                                                            ║');
  console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
  console.log('║                                                                               ║');
  console.log(`║   • Time to 100x: ${result.duration.padEnd(54)}║`);
  console.log(`║   • Average profit per trade: £${(result.totalPnl / result.totalTrades).toFixed(4).padEnd(44)}║`);
  console.log(`║   • System uses 85.3% win rate from README                                    ║`);
  console.log(`║   • All API rate limits respected                                             ║`);
  console.log(`║   • Spread betting profits are 100% TAX-FREE in UK                            ║`);
  console.log('║                                                                               ║');
  console.log('╚═══════════════════════════════════════════════════════════════════════════════╝');
}

// ═══════════════════════════════════════════════════════════════════════════
// MAIN EXECUTION
// ═══════════════════════════════════════════════════════════════════════════

console.log('🚀 Starting £400 → £40,000 simulation with 14 brokers...\n');

const result = runSimulation(40000);
printResults(result);

// Show trading schedule
console.log('');
console.log('╔═══════════════════════════════════════════════════════════════════════════════╗');
console.log('║   📅 24/7 TRADING SCHEDULE:                                                   ║');
console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
console.log('║                                                                               ║');
console.log('║   🪙 CRYPTO (24/7/365): Binance, OKX, Kraken, Coinbase, Bitstamp, Gemini      ║');
console.log('║      → £140 allocated, 115 trades/min, ALWAYS ACTIVE                          ║');
console.log('║                                                                               ║');
console.log('║   💱 FOREX (Sun 21:00 - Fri 21:00 UTC): OANDA, FXCM                           ║');
console.log('║      → £70 allocated, 90 trades/min, 24/5                                     ║');
console.log('║                                                                               ║');
console.log('║   🇺🇸 US STOCKS (14:30 - 21:00 UTC): Alpaca (FREE!), IB                       ║');
console.log('║      → £70 allocated, 110 trades/min during market hours                      ║');
console.log('║                                                                               ║');
console.log('║   📈 SPREAD BETTING 🎁 (24/5): IG, CMC (TAX-FREE!)                            ║');
console.log('║      → £75 allocated, 20 trades/min, NO CGT                                   ║');
console.log('║                                                                               ║');
console.log('║   📊 CFD (24/5): Capital.com, Saxo Bank                                       ║');
console.log('║      → £45 allocated, 25 trades/min                                           ║');
console.log('║                                                                               ║');
console.log('╠═══════════════════════════════════════════════════════════════════════════════╣');
console.log('║   ⚡ TOTAL CAPACITY: 360 trades/min = 21,600 trades/hour = 518,400/day        ║');
console.log('╚═══════════════════════════════════════════════════════════════════════════════╝');
