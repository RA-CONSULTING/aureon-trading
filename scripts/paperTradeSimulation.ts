import fs from 'node:fs';
import path from 'node:path';

interface FieldMetricsRow {
  t: number;
  L: number;
  C_lin: number;
  C_nonlin: number;
  C_phi: number;
  G_eff: number;
  Q_abs: number;
}

interface TradeRecord {
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

interface SimulationSummary {
  trades: TradeRecord[];
  grossPnl: number;
  netPnl: number;
  hitRate: number;
  netHitRate: number;
  avgDuration: number;
  avgTechnicolorScore: number;
  maxDrawdown: number;
}

const ENTRY_COHERENCE = 0.94;
const ENTRY_ENERGY = 0.22;
const ENTRY_PHASE = 0.01;
const EXIT_COHERENCE = 0.935;
const EXIT_ENERGY = 0.19;
const TAKE_PROFIT = 0.02;
const STOP_LOSS = -0.015;
const ENTRY_BUFFER = 0.0025;
const ENTRY_VELOCITY = 0.001;
const MIN_ABSURDITY_BAND = 0.015;
const MAKER_FEE_RATE = 0.0002;
const TAKER_FEE_RATE = 0.0007;
const SLIPPAGE_RATE = 0.0005;
const ROUND_TRIP_COST_RATE = MAKER_FEE_RATE + TAKER_FEE_RATE + SLIPPAGE_RATE;

function loadFieldMetrics(): FieldMetricsRow[] {
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

function simulateTrades(rows: FieldMetricsRow[]): SimulationSummary {
  const trades: TradeRecord[] = [];
  let positionOpen = false;
  let entryRow: FieldMetricsRow | null = null;
  let entryIndex = -1;
  let maxCoherence = 0;
  let minCoherence = 1;
  let technicolorAccumulator = 0;
  let drawdown = 0;
  let maxDrawdown = 0;
  let previousRow: FieldMetricsRow | null = null;

  rows.forEach((row, index) => {
    const coherence = row.C_nonlin;
    const phi = row.C_phi;
    const previousCoherence = previousRow?.C_nonlin ?? coherence;
    const previousPhi = previousRow?.C_phi ?? phi;
    const coherenceVelocity = coherence - previousCoherence;
    const phaseVelocity = phi - previousPhi;
    if (!positionOpen) {
      const enterSignal =
        coherence >= ENTRY_COHERENCE + ENTRY_BUFFER &&
        phi >= ENTRY_PHASE &&
        row.G_eff >= ENTRY_ENERGY &&
        row.Q_abs >= MIN_ABSURDITY_BAND &&
        coherenceVelocity >= ENTRY_VELOCITY &&
        phaseVelocity >= 0;
      if (enterSignal) {
        positionOpen = true;
        entryRow = row;
        entryIndex = index;
        maxCoherence = coherence;
        minCoherence = coherence;
        technicolorAccumulator = coherence - ENTRY_COHERENCE + row.Q_abs + phi;
      }
      previousRow = row;
      return;
    }

    if (!entryRow) return;

    maxCoherence = Math.max(maxCoherence, coherence);
    minCoherence = Math.min(minCoherence, coherence);
    technicolorAccumulator += coherence - ENTRY_COHERENCE + row.Q_abs + phi;

    const priceDelta = (row.L - entryRow.L) / entryRow.L;
    drawdown = Math.min(drawdown, priceDelta);
    maxDrawdown = Math.min(maxDrawdown, drawdown);

    const exitForCoherence = coherence <= EXIT_COHERENCE;
    const exitForEnergy = row.G_eff <= EXIT_ENERGY;
    const exitForStop = priceDelta <= STOP_LOSS;
    const exitReason = exitForCoherence ? 'coherence_drop' : exitForEnergy ? 'energy_dip' : exitForStop ? 'drawdown_guard' : 'target_met';

    if (coherence >= ENTRY_COHERENCE + 0.01 && phi >= ENTRY_PHASE + 0.01 && priceDelta >= TAKE_PROFIT) {
      recordTrade('target_met');
      return;
    }

    if (exitForCoherence || exitForEnergy || exitForStop) {
      recordTrade(exitReason);
      return;
    }

    function recordTrade(reason: string) {
      if (!positionOpen || !entryRow) return;
      const exitPrice = row.L;
      const pnl = exitPrice - entryRow.L;
      const grossDelta = priceDelta;
      const roundTripCost = entryRow.L * ROUND_TRIP_COST_RATE;
      const netPnl = pnl - roundTripCost;
      const netDelta = grossDelta - ROUND_TRIP_COST_RATE;
      const holdDuration = row.t - entryRow.t;
      const technicolorScore = technicolorAccumulator / Math.max(1, index - entryIndex + 1);
      trades.push({
        entryIndex,
        exitIndex: index,
        entryTime: entryRow.t,
        exitTime: row.t,
        entryPrice: entryRow.L,
        exitPrice,
        pnl,
        netPnl,
        grossDelta,
        netDelta,
        holdDuration,
        maxCoherence,
        minCoherence,
        technicolorScore,
        exitReason: reason
      });
      positionOpen = false;
      entryRow = null;
      entryIndex = -1;
      maxCoherence = 0;
      minCoherence = 1;
      technicolorAccumulator = 0;
      drawdown = 0;
    }
    previousRow = row;
  });

  if (positionOpen && entryRow) {
    const last = rows.at(-1);
    if (!last) {
      return { trades, grossPnl: 0, netPnl: 0, hitRate: 0, netHitRate: 0, avgDuration: 0, avgTechnicolorScore: 0, maxDrawdown };
    }
    const openRow = entryRow as FieldMetricsRow;
    const pnl = last.L - openRow.L;
    trades.push({
      entryIndex,
      exitIndex: rows.length - 1,
      entryTime: openRow.t,
      exitTime: last.t,
      entryPrice: openRow.L,
      exitPrice: last.L,
      pnl,
      netPnl: pnl - openRow.L * ROUND_TRIP_COST_RATE,
      grossDelta: pnl / Math.max(1, openRow.L),
      netDelta: pnl / Math.max(1, openRow.L) - ROUND_TRIP_COST_RATE,
      holdDuration: last.t - openRow.t,
      maxCoherence,
      minCoherence,
      technicolorScore: technicolorAccumulator / Math.max(1, rows.length - entryIndex),
      exitReason: 'forced_close'
    });
  }

  const grossPnl = trades.reduce((sum, trade) => sum + trade.pnl, 0);
  const netPnl = trades.reduce((sum, trade) => sum + trade.netPnl, 0);
  const winners = trades.filter(trade => trade.pnl > 0).length;
  const hitRate = trades.length ? winners / trades.length : 0;
  const netWinners = trades.filter(trade => trade.netPnl > 0).length;
  const netHitRate = trades.length ? netWinners / trades.length : 0;
  const avgDuration = trades.length ? trades.reduce((sum, trade) => sum + trade.holdDuration, 0) / trades.length : 0;
  const avgTechnicolorScore = trades.length ? trades.reduce((sum, trade) => sum + trade.technicolorScore, 0) / trades.length : 0;

  return { trades, grossPnl, netPnl, hitRate, netHitRate, avgDuration, avgTechnicolorScore, maxDrawdown };
}

function renderReport(summary: SimulationSummary) {
  console.log('=== Quantum Quackers Paper Trade Simulation ===');
  console.log(`Trades executed: ${summary.trades.length}`);
  console.log(`Gross ΔL PnL: ${summary.grossPnl.toFixed(6)}`);
  console.log(`Net ΔL PnL (after fees/slippage): ${summary.netPnl.toFixed(6)}`);
  console.log(`Hit rate: ${(summary.hitRate * 100).toFixed(1)}%`);
  console.log(`Net hit rate: ${(summary.netHitRate * 100).toFixed(1)}%`);
  console.log(`Avg hold duration (Δt): ${summary.avgDuration.toFixed(3)}`);
  console.log(`Avg Technicolor score: ${summary.avgTechnicolorScore.toFixed(4)}`);
  console.log(`Max drawdown (ΔL): ${summary.maxDrawdown.toFixed(4)}`);
  console.log(`Round-trip cost rate applied: ${(ROUND_TRIP_COST_RATE * 100).toFixed(2)}%`);
  console.log('\nRecent trades:');
  summary.trades.slice(-5).forEach(trade => {
    console.log(
      `t${trade.entryTime.toFixed(2)}→${trade.exitTime.toFixed(2)} | pnl ${trade.pnl.toFixed(5)} | ` +
      `net ${trade.netPnl.toFixed(5)} | maxΦ ${trade.maxCoherence.toFixed(3)} | exit ${trade.exitReason}`
    );
  });
}

function main() {
  const rows = loadFieldMetrics();
  const summary = simulateTrades(rows);
  renderReport(summary);
}

main();
