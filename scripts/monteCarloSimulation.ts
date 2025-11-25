import { loadFieldMetrics, simulateTrades, type FieldMetricsRow, type SimulationSummary } from './paperTradeSimulation.ts';

// Simple seeded RNG (LCG)
function makeRng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 0xffffffff;
  };
}

function parseArg(name: string, def: number) {
  const ix = process.argv.findIndex(a => a === `--${name}`);
  if (ix !== -1 && process.argv[ix + 1]) return Number(process.argv[ix + 1]);
  return def;
}

interface TrialResult {
  finalBalance: number;
  maxDrawdown: number;
  netPnl: number;
}

function bootstrapRows(rows: FieldMetricsRow[], window: number, length: number, rng: () => number, noiseSigma: number, starts?: number[]): FieldMetricsRow[] {
  const out: FieldMetricsRow[] = [];
  const maxStart = Math.max(0, rows.length - window);
  const pool = (starts && starts.length > 0) ? starts : Array.from({ length: maxStart + 1 }, (_, i) => i);
  while (out.length < length) {
    const pick = Math.floor(rng() * pool.length);
    const start = pool[pick];
    const chunk = rows.slice(start, start + window);
    for (const r of chunk) {
      if (out.length >= length) break;
      const Lnoise = (rng() * 2 - 1) * noiseSigma * r.L; // symmetric noise
      out.push({
        ...r,
        L: Math.max(1e-9, r.L + Lnoise)
      });
    }
  }
  // Re-time the series to maintain monotonic t
  return out.map((r, i) => ({ ...r, t: i / 100 }));
}

function percentiles(values: number[], ps: number[]) {
  const a = [...values].sort((x, y) => x - y);
  return ps.map(p => {
    const idx = (a.length - 1) * p;
    const lo = Math.floor(idx);
    const hi = Math.ceil(idx);
    if (lo === hi) return a[lo];
    const w = idx - lo;
    return a[lo] * (1 - w) + a[hi] * w;
  });
}

function main() {
  const trials = parseArg('trials', 250);
  const seed = parseArg('seed', 42);
  const window = parseArg('window', 8);
  const noise = parseArg('noise', 0.0); // fraction of L
  const lengthMult = parseArg('lengthMult', 1);
  const riskPct = parseArg('risk', 0); // 0 = disabled, else fraction of balance per trade
  const cohThresh = parseArg('coh', 0); // 0 disables filtering
  const energyThresh = parseArg('energy', 0);

  const baseRows = loadFieldMetrics();
  const rng = makeRng(seed);

  const results: TrialResult[] = [];

  // Precompute regime-filtered start indices if thresholds provided
  let starts: number[] | undefined = undefined;
  if (cohThresh > 0 || energyThresh > 0) {
    const maxStart = Math.max(0, baseRows.length - window);
    const s: number[] = [];
    for (let i = 0; i <= maxStart; i++) {
      const chunk = baseRows.slice(i, i + window);
      const avgC = chunk.reduce((a, r) => a + r.C_nonlin, 0) / chunk.length;
      const avgE = chunk.reduce((a, r) => a + r.G_eff, 0) / chunk.length;
      if ((cohThresh === 0 || avgC >= cohThresh) && (energyThresh === 0 || avgE >= energyThresh)) {
        s.push(i);
      }
    }
    if (s.length > 0) starts = s;
  }
  for (let i = 0; i < trials; i++) {
    const boot = bootstrapRows(baseRows, window, baseRows.length * Math.max(1, lengthMult), rng, noise, starts);
    // Configure risk percent for this trial (constant across a run)
    if (riskPct > 0) process.env.SIM_RISK_PCT = String(riskPct);
    const summary: SimulationSummary = simulateTrades(boot);
    results.push({
      finalBalance: summary.finalBalance,
      maxDrawdown: summary.maxDrawdown,
      netPnl: summary.netPnl
    });
  }

  const finals = results.map(r => r.finalBalance);
  const drawdowns = results.map(r => r.maxDrawdown);
  const pnls = results.map(r => r.netPnl);

  const [p05, p50, p95] = percentiles(finals, [0.05, 0.5, 0.95]);
  const lossProb = finals.filter(v => v < 1000).length / finals.length;
  const avgFinal = finals.reduce((a, b) => a + b, 0) / finals.length;
  const avgPnl = pnls.reduce((a, b) => a + b, 0) / pnls.length;
  const avgDd = drawdowns.reduce((a, b) => a + b, 0) / drawdowns.length;

  console.log('=== Monte Carlo (bootstrap path) ===');
  console.log(`Trials: ${trials} | seed: ${seed} | window: ${window} | noise: ${noise} | lengthMult: ${lengthMult} | risk: ${riskPct} | coh>=${cohThresh} | energy>=${energyThresh}`);
  console.log(`Final balance avg: $${avgFinal.toFixed(2)} | p05: $${p05.toFixed(2)} | p50: $${p50.toFixed(2)} | p95: $${p95.toFixed(2)}`);
  console.log(`Loss probability (<$1000): ${(lossProb * 100).toFixed(1)}%`);
  console.log(`Avg net PnL: $${avgPnl.toFixed(2)} | Avg max drawdown (ΔL): ${avgDd.toFixed(4)}`);
}

main();
