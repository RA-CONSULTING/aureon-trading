/**
 * 🎵 24-HOUR DAY TRADING SIMULATION 🎵
 * 
 * Runs 24 cycles (1 per hour) to simulate a full trading day
 * Each cycle = 500 trades per broker (2000 total)
 * 24 cycles = 48,000 trades total
 */

// Broker configurations with real fee structures
const BROKERS = {
  binance: {
    name: '🪙 Binance',
    assets: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'ADAUSDT', 'DOGEUSDT', 'MATICUSDT', 'DOTUSDT', 'AVAXUSDT'],
    feeRate: 0.00075, // 0.075% with BNB
    minOrder: 5,
  },
  capital: {
    name: '📊 Capital',
    assets: ['BTCUSD', 'ETHUSD', 'EURUSD_C', 'GBPUSD_C', 'GOLD_C', 'TSLA_C', 'AAPL_C', 'AMZN_C', 'SPX500', 'US100'],
    feeRate: 0.001, // ~0.1% spread
    minOrder: 10,
  },
  alpaca: {
    name: '🦙 Alpaca',
    assets: ['AAPL', 'TSLA', 'NVDA', 'AMD', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NFLX', 'MARA'],
    feeRate: 0.0, // FREE for stocks!
    minOrder: 1,
  },
  oanda: {
    name: '💱 OANDA',
    assets: ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', 'NZDUSD', 'XAUUSD', 'BCOUSD', 'WTICOUSD', 'SPX500USD'],
    feeRate: 0.00012, // ~1.2 pips as percentage
    minOrder: 1,
  }
};

const CONFIG = {
  CYCLES: 24,
  TRADES_PER_BROKER: 500,
  STARTING_CAPITAL: 100,
  POSITION_SIZE: 0.05,
  STOP_LOSS: 0.008,
  TAKE_PROFIT: 0.018,
  COHERENCE_THRESHOLD: 0.70,
};

interface CycleResult {
  hour: number;
  trades: number;
  wins: number;
  losses: number;
  grossPnL: number;
  fees: number;
  netPnL: number;
  brokerResults: { [key: string]: { pnl: number; wins: number; losses: number; fees: number } };
}

interface BrokerState {
  capital: number;
  totalTrades: number;
  wins: number;
  losses: number;
  totalFees: number;
  grossPnL: number;
}

function generateCoherence(): number {
  // Weighted towards winning coherence (simulating our edge)
  const base = Math.random();
  const boost = Math.random() > 0.43 ? 0.1 : 0; // 57% win bias
  return Math.min(1, base * 0.4 + 0.55 + boost);
}

function simulateTrade(capital: number, feeRate: number): { pnl: number; fee: number; win: boolean } {
  const positionSize = capital * CONFIG.POSITION_SIZE;
  const coherence = generateCoherence();
  const win = coherence > CONFIG.COHERENCE_THRESHOLD;
  
  const pnlPercent = win ? CONFIG.TAKE_PROFIT : -CONFIG.STOP_LOSS;
  const grossPnL = positionSize * pnlPercent;
  const fee = positionSize * feeRate * 2; // Entry + exit
  
  return { pnl: grossPnL, fee, win };
}

function runCycle(hour: number, brokerStates: { [key: string]: BrokerState }): CycleResult {
  const result: CycleResult = {
    hour,
    trades: 0,
    wins: 0,
    losses: 0,
    grossPnL: 0,
    fees: 0,
    netPnL: 0,
    brokerResults: {},
  };

  for (const [brokerId, broker] of Object.entries(BROKERS)) {
    const state = brokerStates[brokerId];
    let cycleWins = 0;
    let cycleLosses = 0;
    let cyclePnL = 0;
    let cycleFees = 0;

    for (let i = 0; i < CONFIG.TRADES_PER_BROKER; i++) {
      const trade = simulateTrade(state.capital, broker.feeRate);
      
      if (trade.win) {
        cycleWins++;
        state.wins++;
      } else {
        cycleLosses++;
        state.losses++;
      }
      
      cyclePnL += trade.pnl;
      cycleFees += trade.fee;
      state.capital += trade.pnl - trade.fee;
      state.totalTrades++;
    }

    state.grossPnL += cyclePnL;
    state.totalFees += cycleFees;

    result.brokerResults[brokerId] = {
      pnl: cyclePnL,
      wins: cycleWins,
      losses: cycleLosses,
      fees: cycleFees,
    };

    result.trades += CONFIG.TRADES_PER_BROKER;
    result.wins += cycleWins;
    result.losses += cycleLosses;
    result.grossPnL += cyclePnL;
    result.fees += cycleFees;
  }

  result.netPnL = result.grossPnL - result.fees;
  return result;
}

async function main() {
  console.log(`
  ╔═════════════════════════════════════════════════════════════════════════╗
  ║                                                                         ║
  ║   🌅 24-HOUR DAY TRADING SIMULATION 🌙                                  ║
  ║                                                                         ║
  ║   Cycles: 24 (one per hour)                                             ║
  ║   Trades per cycle: 2,000 (500 × 4 brokers)                             ║
  ║   Total trades: 48,000                                                  ║
  ║   Starting capital: £100 per broker (£400 total)                        ║
  ║                                                                         ║
  ╚═════════════════════════════════════════════════════════════════════════╝
  `);

  // Initialize broker states
  const brokerStates: { [key: string]: BrokerState } = {};
  for (const brokerId of Object.keys(BROKERS)) {
    brokerStates[brokerId] = {
      capital: CONFIG.STARTING_CAPITAL,
      totalTrades: 0,
      wins: 0,
      losses: 0,
      totalFees: 0,
      grossPnL: 0,
    };
  }

  const cycles: CycleResult[] = [];
  let runningCapital = CONFIG.STARTING_CAPITAL * 4;

  console.log('  ⏰ Hour │ Trades │  Wins  │ Losses │  Gross   │   Fees   │   Net    │ Capital');
  console.log('  ───────┼────────┼────────┼────────┼──────────┼──────────┼──────────┼──────────');

  for (let hour = 0; hour < CONFIG.CYCLES; hour++) {
    const cycle = runCycle(hour, brokerStates);
    cycles.push(cycle);
    
    runningCapital += cycle.netPnL;
    
    const hourStr = hour.toString().padStart(2, '0') + ':00';
    const emoji = cycle.netPnL >= 0 ? '🟢' : '🔴';
    
    console.log(
      `  ${emoji} ${hourStr} │ ${cycle.trades.toString().padStart(6)} │ ${cycle.wins.toString().padStart(6)} │ ${cycle.losses.toString().padStart(6)} │ ${cycle.grossPnL >= 0 ? '+' : ''}£${cycle.grossPnL.toFixed(2).padStart(7)} │ -£${cycle.fees.toFixed(2).padStart(6)} │ ${cycle.netPnL >= 0 ? '+' : ''}£${cycle.netPnL.toFixed(2).padStart(7)} │ £${runningCapital.toFixed(2).padStart(7)}`
    );
  }

  // Calculate totals
  const totalTrades = cycles.reduce((sum, c) => sum + c.trades, 0);
  const totalWins = cycles.reduce((sum, c) => sum + c.wins, 0);
  const totalLosses = cycles.reduce((sum, c) => sum + c.losses, 0);
  const totalGrossPnL = cycles.reduce((sum, c) => sum + c.grossPnL, 0);
  const totalFees = cycles.reduce((sum, c) => sum + c.fees, 0);
  const totalNetPnL = totalGrossPnL - totalFees;
  const finalCapital = Object.values(brokerStates).reduce((sum, s) => sum + s.capital, 0);
  const winRate = (totalWins / totalTrades * 100).toFixed(1);
  const roi = ((finalCapital - 400) / 400 * 100).toFixed(2);

  console.log('  ───────┴────────┴────────┴────────┴──────────┴──────────┴──────────┴──────────');

  console.log(`
  ═══════════════════════════════════════════════════════════════════════════
  ✧  24-HOUR SIMULATION COMPLETE  ✧
  ═══════════════════════════════════════════════════════════════════════════

  ┌───────────────────────────────────────────────────────────────────────────┐
  │                         📊 DAILY SUMMARY                                  │
  ├───────────────────────────────────────────────────────────────────────────┤
  │                                                                           │
  │   ⏱️  Duration:        24 hours (${CONFIG.CYCLES} cycles)                           │
  │   📈 Total Trades:    ${totalTrades.toLocaleString().padStart(6)}                                          │
  │   ✅ Wins:            ${totalWins.toLocaleString().padStart(6)} (${winRate}%)                                  │
  │   ❌ Losses:          ${totalLosses.toLocaleString().padStart(6)}                                          │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘

  ┌───────────────────────────────────────────────────────────────────────────┐
  │                         💰 FINANCIAL RESULTS                              │
  ├───────────────────────────────────────────────────────────────────────────┤
  │                                                                           │
  │   💵 Starting Capital:    £400.00                                         │
  │   📈 Gross Profit:        +£${totalGrossPnL.toFixed(2).padStart(7)}                                       │
  │   💸 Total Fees:          -£${totalFees.toFixed(2).padStart(7)}                                       │
  │   ─────────────────────────────────                                       │
  │   💎 Net Profit:          +£${totalNetPnL.toFixed(2).padStart(7)}                                       │
  │   🏦 Final Capital:       £${finalCapital.toFixed(2).padStart(7)}                                       │
  │   📊 ROI:                 ${roi}%                                          │
  │                                                                           │
  └───────────────────────────────────────────────────────────────────────────┘
  `);

  // Broker breakdown
  console.log('  ┌─────────────┬──────────┬──────────┬──────────┬──────────┬──────────┬──────────┐');
  console.log('  │   Broker    │  Trades  │   Wins   │  Losses  │  Gross   │   Fees   │ Final £  │');
  console.log('  ├─────────────┼──────────┼──────────┼──────────┼──────────┼──────────┼──────────┤');

  for (const [brokerId, broker] of Object.entries(BROKERS)) {
    const state = brokerStates[brokerId];
    const winRateBroker = (state.wins / state.totalTrades * 100).toFixed(1);
    console.log(
      `  │ ${broker.name.padEnd(11)} │ ${state.totalTrades.toString().padStart(8)} │ ${state.wins.toString().padStart(8)} │ ${state.losses.toString().padStart(8)} │ +£${state.grossPnL.toFixed(2).padStart(6)} │ -£${state.totalFees.toFixed(2).padStart(5)} │ £${state.capital.toFixed(2).padStart(7)} │`
    );
  }

  console.log('  └─────────────┴──────────┴──────────┴──────────┴──────────┴──────────┴──────────┘');

  // Hourly profit chart
  console.log(`
  📈 HOURLY NET PROFIT CHART:
  `);
  
  const maxProfit = Math.max(...cycles.map(c => Math.abs(c.netPnL)));
  const chartWidth = 40;
  
  for (let i = 0; i < cycles.length; i++) {
    const cycle = cycles[i];
    const barLength = Math.round((Math.abs(cycle.netPnL) / maxProfit) * chartWidth);
    const bar = cycle.netPnL >= 0 ? '█'.repeat(barLength) : '░'.repeat(barLength);
    const emoji = cycle.netPnL >= 0 ? '🟢' : '🔴';
    const hourStr = i.toString().padStart(2, '0') + ':00';
    const sign = cycle.netPnL >= 0 ? '+' : '';
    console.log(`  ${hourStr} ${emoji} ${bar.padEnd(chartWidth)} ${sign}£${cycle.netPnL.toFixed(2)}`);
  }

  // Winning/losing cycles
  const winningCycles = cycles.filter(c => c.netPnL > 0).length;
  const losingCycles = cycles.filter(c => c.netPnL <= 0).length;
  const avgCycleProfit = totalNetPnL / CONFIG.CYCLES;
  const bestCycle = cycles.reduce((best, c) => c.netPnL > best.netPnL ? c : best);
  const worstCycle = cycles.reduce((worst, c) => c.netPnL < worst.netPnL ? c : worst);

  console.log(`
  ═══════════════════════════════════════════════════════════════════════════
                              📊 CYCLE ANALYSIS
  ═══════════════════════════════════════════════════════════════════════════

  🟢 Profitable Cycles:  ${winningCycles}/24 (${(winningCycles/24*100).toFixed(1)}%)
  🔴 Losing Cycles:      ${losingCycles}/24 (${(losingCycles/24*100).toFixed(1)}%)
  📊 Avg Profit/Cycle:   +£${avgCycleProfit.toFixed(2)}
  🏆 Best Hour:          ${bestCycle.hour.toString().padStart(2, '0')}:00 (+£${bestCycle.netPnL.toFixed(2)})
  📉 Worst Hour:         ${worstCycle.hour.toString().padStart(2, '0')}:00 (${worstCycle.netPnL >= 0 ? '+' : ''}£${worstCycle.netPnL.toFixed(2)})

  ═══════════════════════════════════════════════════════════════════════════
  `);

  // Projections
  const dailyProfit = totalNetPnL;
  const weeklyProfit = dailyProfit * 7;
  const monthlyProfit = dailyProfit * 30;
  const yearlyProfit = dailyProfit * 365;

  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════╗
  ║                         🚀 PROFIT PROJECTIONS                             ║
  ╠═══════════════════════════════════════════════════════════════════════════╣
  ║                                                                           ║
  ║   Based on today's performance (£${dailyProfit.toFixed(2)} net profit):                   ║
  ║                                                                           ║
  ║   📅 Daily:    +£${dailyProfit.toFixed(2).padStart(8)}                                           ║
  ║   📆 Weekly:   +£${weeklyProfit.toFixed(2).padStart(8)}                                           ║
  ║   📆 Monthly:  +£${monthlyProfit.toFixed(2).padStart(8)}                                           ║
  ║   📆 Yearly:   +£${yearlyProfit.toFixed(2).padStart(8)}                                           ║
  ║                                                                           ║
  ║   Starting £400 → £${(400 + yearlyProfit).toFixed(2)} after 1 year                          ║
  ║   That's ${((400 + yearlyProfit) / 400 * 100 - 100).toFixed(0)}% annual return! 🔥                                         ║
  ║                                                                           ║
  ╚═══════════════════════════════════════════════════════════════════════════╝

  ─────────────────────────────────────────────────────────────────────────────
  🎵 "24 hours, 48,000 trades, the symphony never stops" 🎵
  ─────────────────────────────────────────────────────────────────────────────
  `);
}

main().catch(console.error);
