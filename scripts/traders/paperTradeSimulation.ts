import fs from 'node:fs';
import path from 'node:path';

export interface FieldMetricsRow {
  t: number;
  L: number;
  C_lin: number;
  C_nonlin: number;
  C_phi: number;
  G_eff: number;
  Q_abs: number;
}

interface TradeRecord {
  botId: number;
  entryIndex: number;
  exitIndex: number;
  entryTime: number;
  exitTime: number;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  netPnl: number;
  grossDelta: number;
  netDelta: number;
  holdDuration: number;
  maxCoherence: number;
  minCoherence: number;
  technicolorScore: number;
  exitReason: string;
}

export interface SimulationSummary {
  trades: TradeRecord[];
  initialBalance: number;
  finalBalance: number;
  grossPnl: number;
  netPnl: number;
  hitRate: number;
  netHitRate: number;
  avgDuration: number;
  avgTechnicolorScore: number;
  maxDrawdown: number;
  botUtilization: number;
}

const INITIAL_BALANCE = 1000;
const BOT_COUNT = 15;
const TRADE_QUOTA_PER_BOT = 50;

const ENTRY_COHERENCE = 0.938;
const ENTRY_ENERGY = 0.21;
const ENTRY_PHASE = 0.01;
const EXIT_COHERENCE = 0.934;
const EXIT_ENERGY = 0.19;
const TAKE_PROFIT = 0.018;
const STOP_LOSS = -0.008;
const ENTRY_BUFFER = 0.001;
const ENTRY_VELOCITY = 0.0004;
const ENTRY_PRICE_MOMENTUM = 0.0004;
const MIN_TECHNICOLOR_ENTRY = 0.02;
const MIN_ABSURDITY_BAND = 0.01;
const TRAILING_STOP_BUFFER = 0.004;
const TREND_LOOKBACK = 1;
const MIN_PROFIT_LOCK = 0.002;
const COHERENCE_ROLLOVER_DELTA = -0.00025;
const MAKER_FEE_RATE = 0.0002;
const TAKER_FEE_RATE = 0.0007;
const SLIPPAGE_RATE = 0.0005;
const ROUND_TRIP_COST_RATE = MAKER_FEE_RATE + TAKER_FEE_RATE + SLIPPAGE_RATE;

// Configurable enhancements via environment
const MAX_CONCURRENT_POSITIONS = Math.max(1, Number(process.env.SIM_MAX_CONCURRENT || '7'));
const BREAKEVEN_ARM = Number(process.env.SIM_BREAKEVEN_ARM || '0.004');
const BREAKEVEN_LOCK = Number(process.env.SIM_BREAKEVEN_LOCK || '0.0005');
const TRAIL_VOL_MULT = Number(process.env.SIM_TRAIL_VOL_MULT || '5');

export function loadFieldMetrics(): FieldMetricsRow[] {
  const csvPath = path.resolve(process.cwd(), 'public/data/field_metrics_core.csv');
  const raw = fs.readFileSync(csvPath, 'utf-8').trim();
  const lines = raw.split(/\r?\n/);
  const [, ...dataLines] = lines;

  return dataLines
    .filter(Boolean)
    .map(line => {
      const [t, L, C_lin, C_nonlin, C_phi, G_eff, Q_abs] = line.split(',').map(Number);
      const row: FieldMetricsRow = { t, L, C_lin, C_nonlin, C_phi, G_eff, Q_abs };
      return row;
    });
}

interface BotState {
  id: number;
  tradesExecuted: number;
  activeTrade: {
    entryRow: FieldMetricsRow;
    entryIndex: number;
    maxCoherence: number;
    minCoherence: number;
    technicolorAccumulator: number;
    peakGain: number;
    drawdown: number;
    maxDrawdown: number;
    positionSize: number; // Amount of quote currency invested
    breakevenArmed: boolean;
  } | null;
  winStreak: number;
  lossStreak: number;
  momentumBarsLeft: number;
  cooldownBarsLeft: number;
}

export function simulateTrades(rows: FieldMetricsRow[]): SimulationSummary {
  const trades: TradeRecord[] = [];
  let currentBalance = INITIAL_BALANCE;
  
  // Initialize bots
  const bots: BotState[] = Array.from({ length: BOT_COUNT }, (_, i) => ({
    id: i + 1,
    tradesExecuted: 0,
    activeTrade: null,
    winStreak: 0,
    lossStreak: 0,
    momentumBarsLeft: 0,
    cooldownBarsLeft: 0
  }));

  let previousRow: FieldMetricsRow | null = null;
  let globalMaxDrawdown = 0;

  rows.forEach((row, index) => {
    const coherence = row.C_nonlin;
    const phi = row.C_phi;
    const previousCoherence = previousRow?.C_nonlin ?? coherence;
    const previousPhi = previousRow?.C_phi ?? phi;
    const coherenceVelocity = coherence - previousCoherence;
    const phaseVelocity = phi - previousPhi;
    const priceMomentum = row.L - (previousRow?.L ?? row.L);
    
    const bullishTrend = (() => {
      if (index < TREND_LOOKBACK) return false;
      for (let i = index - TREND_LOOKBACK + 1; i <= index; i++) {
        if (rows[i].L <= rows[i - 1].L) {
          return false;
        }
      }
      return true;
    })();

    const structuralEntryOk = bullishTrend || (priceMomentum >= ENTRY_PRICE_MOMENTUM * 1.5 && coherenceVelocity >= ENTRY_VELOCITY * 1.2);
    
    // Entry Logic
    // Momentum bias after wins: slightly loosen thresholds for a few bars
    const anyMomentum = bots.some(b => b.activeTrade === null && b.momentumBarsLeft > 0);
    const bufferLocal = anyMomentum ? ENTRY_BUFFER * 0.8 : ENTRY_BUFFER;
    const priceMomentumLocal = anyMomentum ? ENTRY_PRICE_MOMENTUM * 0.8 : ENTRY_PRICE_MOMENTUM;

    const enterSignal =
      coherence >= ENTRY_COHERENCE + bufferLocal &&
      phi >= ENTRY_PHASE &&
      row.G_eff >= ENTRY_ENERGY &&
      row.Q_abs >= MIN_ABSURDITY_BAND &&
      coherenceVelocity >= ENTRY_VELOCITY &&
      phaseVelocity >= 0 &&
      priceMomentum >= priceMomentumLocal &&
      structuralEntryOk;
      
    const technicolorSeed = coherence - ENTRY_COHERENCE + row.Q_abs + phi;

    if (enterSignal && technicolorSeed >= MIN_TECHNICOLOR_ENTRY) {
      // Exposure throttle: respect global max concurrent positions
      const activeCount = bots.filter(b => b.activeTrade !== null).length;
      const slotsAvailable = MAX_CONCURRENT_POSITIONS - activeCount;
      
      if (slotsAvailable > 0) {
      // Find ALL available bots and let them enter simultaneously (up to available slots)
      const availableBots = bots
        .filter(b => b.activeTrade === null && b.tradesExecuted < TRADE_QUOTA_PER_BOT)
        .sort((a, b) => (b.momentumBarsLeft - a.momentumBarsLeft) || (a.lossStreak - b.lossStreak))
        .slice(0, slotsAvailable);
      
      for (const availableBot of availableBots) {
        // COMPOUND GAME: Each bot draws from the shared balance pool
        // Prefer explicit risk percent if provided, else distribute over remaining slots
        const riskPctEnv = Number(process.env.SIM_RISK_PCT || '0');
        const riskPct = Number.isFinite(riskPctEnv) && riskPctEnv > 0 ? Math.min(1, Math.max(0.0001, riskPctEnv)) : 0;
        let allocation: number;
        
        // Momentum Sizing: If this specific bot has momentum, bet slightly bigger
        const momentumBonus = availableBot.momentumBarsLeft > 0 ? 1.2 : 1.0;

        if (riskPct > 0) {
          // Adaptive risk multiplier based on streaks
          const WIN_RISK_BONUS = 0.5; // +50% per win up to cap
          const LOSS_RISK_PENALTY = 0.5; // -50% when in cooldown
          const MAX_RISK_PCT = 0.1;
          const winFactor = 1 + WIN_RISK_BONUS * Math.min(2, availableBot.winStreak);
          const lossFactor = availableBot.cooldownBarsLeft > 0 ? LOSS_RISK_PENALTY : 1;
          const riskAdj = Math.min(MAX_RISK_PCT, riskPct * winFactor * lossFactor * momentumBonus);
          allocation = currentBalance * riskAdj;
        } else {
          const remainingBots = bots.filter(b => b.activeTrade === null && b.tradesExecuted < TRADE_QUOTA_PER_BOT).length;
          const remainingTradeSlots = remainingBots * TRADE_QUOTA_PER_BOT;
          const baseAlloc = currentBalance / Math.max(1, remainingTradeSlots);
          const WIN_ALLOC_BONUS = 0.35;
          const LOSS_ALLOC_PENALTY = 0.5;
          const winFactor = 1 + WIN_ALLOC_BONUS * Math.min(2, availableBot.winStreak);
          const lossFactor = availableBot.cooldownBarsLeft > 0 ? LOSS_ALLOC_PENALTY : 1;
          allocation = baseAlloc * winFactor * lossFactor * momentumBonus;
        }
        
        availableBot.activeTrade = {
          entryRow: row,
          entryIndex: index,
          maxCoherence: coherence,
          minCoherence: coherence,
          technicolorAccumulator: technicolorSeed,
          peakGain: 0,
          drawdown: 0,
          maxDrawdown: 0,
          positionSize: allocation,
          breakevenArmed: false
        };
        availableBot.tradesExecuted++;
      }
      }
    }

    // Exit Logic for Active Bots
    bots.forEach(bot => {
      if (!bot.activeTrade) return;

      const trade = bot.activeTrade;
      trade.maxCoherence = Math.max(trade.maxCoherence, coherence);
      trade.minCoherence = Math.min(trade.minCoherence, coherence);
      trade.technicolorAccumulator += coherence - ENTRY_COHERENCE + row.Q_abs + phi;

      const priceDelta = (row.L - trade.entryRow.L) / trade.entryRow.L;
      trade.peakGain = Math.max(trade.peakGain, priceDelta);
      trade.drawdown = Math.min(trade.drawdown, priceDelta);
      trade.maxDrawdown = Math.min(trade.maxDrawdown, trade.drawdown);
      globalMaxDrawdown = Math.min(globalMaxDrawdown, trade.maxDrawdown);

      // Dynamic Trailing Stop: Widen buffer if volatility (Q_abs) is high
      const dynamicTrailingBuffer = TRAILING_STOP_BUFFER * (1 + row.Q_abs * TRAIL_VOL_MULT);

      const exitForCoherence = coherence <= EXIT_COHERENCE;
      const exitForEnergy = row.G_eff <= EXIT_ENERGY;
      const exitForStop = priceDelta <= STOP_LOSS;
      const exitForTrailing = trade.peakGain > dynamicTrailingBuffer && priceDelta <= trade.peakGain - dynamicTrailingBuffer;
      
      // Stalemate Exit: If held too long with no profit, cut it
      const duration = index - trade.entryIndex;
      const exitForStalemate = duration > 25 && priceDelta < 0.002;

      // Breakeven lock-in: once a trade moves enough in favor, don't let it turn red
      if (!trade.breakevenArmed && priceDelta >= BREAKEVEN_ARM) {
        trade.breakevenArmed = true;
      }
      const exitForBreakeven = trade.breakevenArmed && priceDelta <= BREAKEVEN_LOCK;

      // Technicolor Fade Exit: If the trade loses its "color" (quality)
      const currentTechnicolorScore = trade.technicolorAccumulator / Math.max(1, duration);
      const exitForFade = duration > 10 && currentTechnicolorScore < 0.015;

      let exitReason = '';
      if (coherence >= ENTRY_COHERENCE + 0.01 && phi >= ENTRY_PHASE + 0.01 && priceDelta >= TAKE_PROFIT) exitReason = 'target_met';
      else if (priceDelta >= MIN_PROFIT_LOCK && coherenceVelocity <= COHERENCE_ROLLOVER_DELTA) exitReason = 'coherence_rollover';
      else if (priceDelta >= MIN_PROFIT_LOCK && phaseVelocity < 0) exitReason = 'phase_backspin';
      else if (exitForCoherence) exitReason = 'coherence_drop';
      else if (exitForEnergy) exitReason = 'energy_dip';
      else if (exitForStop) exitReason = 'drawdown_guard';
      else if (exitForTrailing) exitReason = 'trailing_stop';
      else if (exitForBreakeven) exitReason = 'breakeven_lock';
      else if (exitForStalemate) exitReason = 'stalemate';
      else if (exitForFade) exitReason = 'technicolor_fade';

      if (exitReason) {
        closeTrade(bot, row, index, exitReason);
      }
    });

    // Decay per-bot momentum/cooldown counters each bar
    bots.forEach(b => {
      if (b.momentumBarsLeft > 0) b.momentumBarsLeft--;
      if (b.cooldownBarsLeft > 0) b.cooldownBarsLeft--;
    });

    previousRow = row;
  });

  // Force close remaining positions
  const lastRow = rows.at(-1);
  if (lastRow) {
    bots.forEach(bot => {
      if (bot.activeTrade) {
        closeTrade(bot, lastRow, rows.length - 1, 'forced_close');
      }
    });
  }

  function closeTrade(bot: BotState, exitRow: FieldMetricsRow, exitIndex: number, reason: string) {
    if (!bot.activeTrade) return;
    const trade = bot.activeTrade;
    
    const exitPrice = exitRow.L;
    const priceDelta = (exitPrice - trade.entryRow.L) / trade.entryRow.L;
    const grossPnlAmt = trade.positionSize * priceDelta;
    const cost = trade.positionSize * ROUND_TRIP_COST_RATE;
    const netPnlAmt = grossPnlAmt - cost;
    
    // COMPOUND: Reinvest profits/losses back into the balance pool
    currentBalance += netPnlAmt;

    trades.push({
      botId: bot.id,
      entryIndex: trade.entryIndex,
      exitIndex: exitIndex,
      entryTime: trade.entryRow.t,
      exitTime: exitRow.t,
      entryPrice: trade.entryRow.L,
      exitPrice: exitPrice,
      pnl: grossPnlAmt,
      netPnl: netPnlAmt,
      grossDelta: priceDelta,
      netDelta: priceDelta - ROUND_TRIP_COST_RATE,
      holdDuration: exitRow.t - trade.entryRow.t,
      maxCoherence: trade.maxCoherence,
      minCoherence: trade.minCoherence,
      technicolorScore: trade.technicolorAccumulator / Math.max(1, exitIndex - trade.entryIndex + 1),
      exitReason: reason
    });

    bot.activeTrade = null;
    // Update streaks and momentum/cooldown windows
    if (netPnlAmt > 0) {
      bot.winStreak = Math.min(10, bot.winStreak + 1);
      bot.lossStreak = 0;
      bot.momentumBarsLeft = Math.max(bot.momentumBarsLeft, 3);
      bot.cooldownBarsLeft = 0;
    } else {
      bot.lossStreak = Math.min(10, bot.lossStreak + 1);
      bot.winStreak = 0;
      bot.cooldownBarsLeft = Math.max(bot.cooldownBarsLeft, 2);
      bot.momentumBarsLeft = 0;
    }
  }

  const grossPnl = trades.reduce((sum, trade) => sum + trade.pnl, 0); // Sum of deltas
  const netPnl = trades.reduce((sum, trade) => sum + trade.netPnl, 0); // Sum of net deltas
  const winners = trades.filter(trade => trade.netPnl > 0).length;
  const hitRate = trades.length ? winners / trades.length : 0;
  const netWinners = trades.filter(trade => trade.netPnl > 0).length;
  const netHitRate = trades.length ? netWinners / trades.length : 0;
  const avgDuration = trades.length ? trades.reduce((sum, trade) => sum + trade.holdDuration, 0) / trades.length : 0;
  const avgTechnicolorScore = trades.length ? trades.reduce((sum, trade) => sum + trade.technicolorScore, 0) / trades.length : 0;
  const activeBots = bots.filter(b => b.tradesExecuted > 0).length;

  return { 
    trades, 
    initialBalance: INITIAL_BALANCE,
    finalBalance: currentBalance,
    grossPnl, 
    netPnl, 
    hitRate, 
    netHitRate, 
    avgDuration, 
    avgTechnicolorScore, 
    maxDrawdown: globalMaxDrawdown,
    botUtilization: activeBots / BOT_COUNT
  };
}

function renderReport(summary: SimulationSummary) {
  console.log('=== Quantum Quackers Paper Trade Simulation ===');
  console.log(`Initial Balance: $${summary.initialBalance.toFixed(2)}`);
  console.log(`Final Balance: $${summary.finalBalance.toFixed(2)}`);
  console.log(`Net Profit: $${(summary.finalBalance - summary.initialBalance).toFixed(2)} (${((summary.finalBalance - summary.initialBalance) / summary.initialBalance * 100).toFixed(2)}%)`);
  console.log(`Trades executed: ${summary.trades.length}`);
  console.log(`Bot Utilization: ${(summary.botUtilization * 100).toFixed(1)}%`);
  console.log(`Gross PnL: $${summary.grossPnl.toFixed(2)}`);
  console.log(`Net PnL (after fees): $${summary.netPnl.toFixed(2)}`);
  console.log(`Hit rate: ${(summary.hitRate * 100).toFixed(1)}%`);
  console.log(`Net hit rate: ${(summary.netHitRate * 100).toFixed(1)}%`);
  
  // Optional: report net-positive hit rate for first N trades
  const firstN = Number(process.env.SIM_MAX_TRADES || '0');
  if (Number.isFinite(firstN) && firstN > 0) {
    const subset = summary.trades.slice(0, firstN);
    if (subset.length > 0) {
      const winnersN = subset.filter(t => t.netPnl > 0).length;
      const netHitN = winnersN / subset.length;
      console.log(`Net hit rate (first ${subset.length} trades): ${(netHitN * 100).toFixed(1)}%`);
      const grossN = subset.reduce((s, t) => s + t.pnl, 0);
      const netN = subset.reduce((s, t) => s + t.netPnl, 0);
      console.log(`Subset PnL — Gross: $${grossN.toFixed(2)} | Net: $${netN.toFixed(2)}`);
    } else {
      console.log('Net hit rate (first N): no trades in subset');
    }
  }
  console.log(`Avg hold duration (Δt): ${summary.avgDuration.toFixed(3)}`);
  console.log(`Avg Technicolor score: ${summary.avgTechnicolorScore.toFixed(4)}`);
  console.log(`Max drawdown (ΔL): ${summary.maxDrawdown.toFixed(4)}`);
  console.log(`Round-trip cost rate applied: ${(ROUND_TRIP_COST_RATE * 100).toFixed(2)}%`);
  console.log('\nRecent trades:');
  summary.trades.slice(-5).forEach(trade => {
    console.log(
      `Bot ${trade.botId} | t${trade.entryTime.toFixed(2)}→${trade.exitTime.toFixed(2)} | pnl $${trade.pnl.toFixed(2)} | ` +
      `net $${trade.netPnl.toFixed(2)} | maxΦ ${trade.maxCoherence.toFixed(3)} | exit ${trade.exitReason}`
    );
  });
}

/**
 * Sweep mode: cycle A→Z then Z→A through the dataset repeatedly,
 * dynamically hitting entry signals until TARGET_TRADES is reached.
 */
function sweepRows(baseRows: FieldMetricsRow[], targetTrades: number): FieldMetricsRow[] {
  const out: FieldMetricsRow[] = [];
  let forward = true;
  let cycle = 0;
  while (out.length < targetTrades * 100) { // rough upper bound on rows needed
    const chunk = forward ? [...baseRows] : [...baseRows].reverse();
    for (const r of chunk) {
      out.push({ ...r, t: out.length / 100 }); // re-time monotonically
    }
    forward = !forward;
    cycle++;
    if (cycle > 500) break; // safety cap
  }
  return out;
}

function main() {
  const targetTrades = Number(process.env.SIM_TARGET_TRADES || '0');
  let rows = loadFieldMetrics();

  if (targetTrades > 0) {
    // Sweep mode: cycle A-Z Z-A until enough rows to hit target trades
    rows = sweepRows(rows, targetTrades);
  }

  const summary = simulateTrades(rows);
  renderReport(summary);

  // If sweep mode, stop early once target trades reached and re-report subset
  if (targetTrades > 0 && summary.trades.length >= targetTrades) {
    const subset = summary.trades.slice(0, targetTrades);
    const winners = subset.filter(t => t.netPnl > 0).length;
    const netHit = winners / subset.length;
    const grossN = subset.reduce((s, t) => s + t.pnl, 0);
    const netN = subset.reduce((s, t) => s + t.netPnl, 0);
    
    // 🎵 The Song of Space and Time 🎵
    console.log('\n');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('  ✧  T H E   S O N G   O F   S P A C E   A N D   T I M E  ✧');
    console.log('  ═══════════════════════════════════════════════════════════');
    console.log('');
    
    // Render the wave visualization
    const waveWidth = 60;
    const waveHeight = 7;
    const waves: string[] = [];
    for (let y = 0; y < waveHeight; y++) {
      let line = '  ';
      for (let x = 0; x < waveWidth; x++) {
        const phase = (x / waveWidth) * Math.PI * 4;
        const amp = Math.sin(phase + y * 0.5);
        const tradeIdx = Math.floor((x / waveWidth) * Math.min(50, subset.length));
        const isWin = subset[tradeIdx]?.netPnl > 0;
        
        if (Math.abs(amp * 3 - (waveHeight / 2 - y)) < 1) {
          line += isWin ? '◆' : '◇';
        } else if (y === Math.floor(waveHeight / 2)) {
          line += '─';
        } else {
          line += ' ';
        }
      }
      waves.push(line);
    }
    waves.forEach(l => console.log(l));
    
    console.log('');
    console.log('       A ──────────────────────────────────────────▶ Z');
    console.log('       Z ◀────────────────────────────────────────── A');
    console.log('');
    
    // Harmonic stats
    const coherenceWave = subset.map(t => t.maxCoherence);
    const avgCoherence = coherenceWave.reduce((a, b) => a + b, 0) / coherenceWave.length;
    const peakCoherence = Math.max(...coherenceWave);
    const rhythm = subset.map((t, i) => i > 0 ? t.entryTime - subset[i-1].exitTime : 0);
    const avgRhythm = rhythm.slice(1).reduce((a, b) => a + b, 0) / Math.max(1, rhythm.length - 1);
    
    console.log('  ┌─────────────────────────────────────────────────────────┐');
    console.log('  │  ◆ = Win    ◇ = Loss    ─ = Time Horizon               │');
    console.log('  └─────────────────────────────────────────────────────────┘');
    console.log('');
    console.log(`  🌊 Wave Riders: ${winners} / ${subset.length} trades`);
    console.log(`  🎯 Harmonic Hit Rate: ${(netHit * 100).toFixed(2)}%`);
    console.log(`  💫 Peak Coherence (Φ): ${peakCoherence.toFixed(4)}`);
    console.log(`  🔮 Avg Coherence: ${avgCoherence.toFixed(4)}`);
    console.log(`  ⏱️  Avg Rhythm (Δt between trades): ${avgRhythm.toFixed(4)}`);
    console.log(`  💰 Net PnL: $${netN.toFixed(2)}`);
    console.log('');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('  "We ride the wave, through space and time,');
    console.log('   Each note a trade, each beat sublime."');
    console.log('  ─────────────────────────────────────────────────────────');
    console.log('');
  }
}

// Only run when executed directly (not when imported)
if (process.argv[1] && /paperTradeSimulation\.ts$/.test(process.argv[1])) {
  main();
}
