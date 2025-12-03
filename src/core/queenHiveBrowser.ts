/**
 * Queen-Hive Browser Version
 * Browser-safe implementation without Node.js fs dependency
 * Uses static return data or fetches from Supabase
 */

export interface HiveMetrics {
  id: string;
  generation: number;
  agents: number;
  equity: number;
  harvestedCapital: number;
  trades: number;
  successfulAgents: number;
  stage: string;
  age: number;
  profitMultiplier: number;
}

export interface QueenHiveState {
  timestamp: number;
  totalHives: number;
  totalAgents: number;
  totalEquity: number;
  totalHarvested: number;
  hives: HiveMetrics[];
  generation: number;
  splitEvents: Array<{ step: number; newHiveId: string; spawnCapital: number }>;
}

// Default return distribution (simulated from historical data)
const DEFAULT_RETURNS = [
  0.02, -0.01, 0.015, 0.03, -0.02, 0.01, -0.005, 0.025, 0.018, -0.012,
  0.04, -0.015, 0.022, 0.008, -0.025, 0.035, 0.012, -0.008, 0.028, 0.005,
  -0.03, 0.045, 0.016, -0.018, 0.032, 0.009, -0.022, 0.038, 0.014, -0.01
];

const PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97];

class Agent {
  id: number;
  equity: number;
  startEquity: number;
  trades: number = 0;
  wins: number = 0;
  primeIdx: number;
  private returns: number[];

  constructor(id: number, start: number, primeIdxOffset: number = 0, returns: number[] = DEFAULT_RETURNS) {
    this.id = id;
    this.equity = start;
    this.startEquity = start;
    this.primeIdx = (id + primeIdxOffset) % PRIMES.length;
    this.returns = returns;
  }

  trade(): { pnl: number; return: number } {
    if (this.equity <= 0) return { pnl: 0, return: 0 };
    const ret = this.returns[Math.floor(Math.random() * this.returns.length)];
    const prime = PRIMES[this.primeIdx % PRIMES.length];
    this.primeIdx++;
    const frac = prime * 0.01;
    const pnl = this.equity * frac * ret;
    this.equity += pnl;
    this.trades++;
    if (ret > 0) this.wins++;
    return { pnl, return: ret };
  }

  getProfitSinceStart(): number {
    return this.equity - this.startEquity;
  }
}

class Hive {
  id: string;
  generation: number;
  agents: Agent[];
  trades: number = 0;
  harvestedCapital: number = 0;
  age: number = 0;
  agentPerHive: number;
  startEquityPerAgent: number;
  targetPerAgent: number;
  successfulAgents: number = 0;
  private returns: number[];

  constructor(
    id: string,
    generation: number,
    agentCount: number,
    startEquityPerAgent: number,
    targetPerAgent: number,
    returns: number[] = DEFAULT_RETURNS
  ) {
    this.id = id;
    this.generation = generation;
    this.agentPerHive = agentCount;
    this.startEquityPerAgent = startEquityPerAgent;
    this.targetPerAgent = targetPerAgent;
    this.returns = returns;

    this.agents = [];
    for (let i = 0; i < agentCount; i++) {
      this.agents.push(new Agent(i, startEquityPerAgent, generation * 1000 + i, returns));
    }
  }

  step(): void {
    for (const agent of this.agents) {
      if (agent.equity > 0 && agent.equity < this.targetPerAgent) {
        agent.trade();
        this.trades++;
        if (agent.equity >= this.targetPerAgent) {
          this.successfulAgents++;
        }
      }
    }
    this.age++;
  }

  harvestCapital(): number {
    const totalEquity = this.getTotalEquity();
    const startTotal = this.startEquityPerAgent * this.agentPerHive;
    const totalProfit = Math.max(0, totalEquity - startTotal);
    const harvestAmount = totalProfit * 0.1;
    this.harvestedCapital += harvestAmount;

    for (const agent of this.agents) {
      const agentProfit = agent.getProfitSinceStart();
      const agentHarvest = agentProfit * 0.1;
      agent.equity -= agentHarvest;
    }

    return harvestAmount;
  }

  getTotalEquity(): number {
    return this.agents.reduce((sum, a) => sum + a.equity, 0);
  }

  getProfitMultiplier(): number {
    const startTotal = this.startEquityPerAgent * this.agentPerHive;
    return this.getTotalEquity() / startTotal;
  }

  canSplit(): boolean {
    return this.successfulAgents >= this.agentPerHive * 0.5;
  }

  getMetrics(): HiveMetrics {
    const stage = this.successfulAgents === this.agentPerHive ? 'mature' : this.canSplit() ? 'ready_to_split' : 'growing';
    return {
      id: this.id,
      generation: this.generation,
      agents: this.agentPerHive,
      equity: this.getTotalEquity(),
      harvestedCapital: this.harvestedCapital,
      trades: this.trades,
      successfulAgents: this.successfulAgents,
      stage,
      age: this.age,
      profitMultiplier: this.getProfitMultiplier(),
    };
  }
}

export class QueenHiveBrowser {
  hives: Map<string, Hive> = new Map();
  harvestPool: number = 0;
  maxGeneration: number = 0;
  agentPerHive: number;
  startEquityPerAgent: number;
  targetPerAgent: number;
  splitEvents: Array<{ step: number; newHiveId: string; spawnCapital: number }> = [];
  globalStep: number = 0;
  private returns: number[];

  constructor(
    agentPerHive: number = 100,
    startEquity: number = 100,
    targetPerAgent: number = 1_000_000,
    returns: number[] = DEFAULT_RETURNS
  ) {
    this.agentPerHive = agentPerHive;
    this.startEquityPerAgent = startEquity;
    this.targetPerAgent = targetPerAgent;
    this.returns = returns;

    const firstHive = new Hive('hive-0', 0, agentPerHive, startEquity, targetPerAgent, returns);
    this.hives.set(firstHive.id, firstHive);
  }

  /**
   * Load returns from Supabase backtest_results (optional enhancement)
   */
  async loadReturnsFromSupabase(): Promise<void> {
    // This could fetch from Supabase if needed
    // For now, using default returns
    console.log('📊 Using default return distribution for browser simulation');
  }

  step(): QueenHiveState {
    // Execute trading for all hives
    for (const hive of this.hives.values()) {
      hive.step();
    }

    // Harvest 10% from hives when they've doubled their starting capital
    for (const hive of this.hives.values()) {
      if (hive.getProfitMultiplier() >= 2) {
        const harvestedThisHive = hive.harvestCapital();
        this.harvestPool += harvestedThisHive;
      }
    }

    // Check for splits: if harvest pool >= cost of new hive, spawn new hive
    const newHiveCost = this.startEquityPerAgent * this.agentPerHive;
    while (this.harvestPool >= newHiveCost) {
      const hivesToSplit = Array.from(this.hives.values()).filter(h => h.getProfitMultiplier() >= 1.5);
      if (hivesToSplit.length > 0) {
        const newHiveId = `hive-${this.hives.size}`;
        const parentGen = hivesToSplit[0].generation;
        const newGeneration = parentGen + 1;
        const newHive = new Hive(newHiveId, newGeneration, this.agentPerHive, this.startEquityPerAgent, this.targetPerAgent, this.returns);
        this.hives.set(newHiveId, newHive);
        this.harvestPool -= newHiveCost;
        this.splitEvents.push({ step: this.globalStep, newHiveId, spawnCapital: newHiveCost });
        this.maxGeneration = Math.max(this.maxGeneration, newGeneration);
      } else {
        break;
      }
    }

    this.globalStep++;
    return this.getState();
  }

  getState(): QueenHiveState {
    const hiveMetrics = Array.from(this.hives.values()).map(h => h.getMetrics());
    const totalEquity = hiveMetrics.reduce((sum, m) => sum + m.equity, 0);
    const totalAgents = hiveMetrics.reduce((sum, m) => sum + m.agents, 0);
    const totalHarvested = hiveMetrics.reduce((sum, m) => sum + m.harvestedCapital, 0) + this.harvestPool;

    return {
      timestamp: Date.now(),
      totalHives: this.hives.size,
      totalAgents,
      totalEquity,
      totalHarvested,
      hives: hiveMetrics,
      generation: this.maxGeneration,
      splitEvents: this.splitEvents,
    };
  }

  run(maxSteps: number, onProgress?: (step: number, state: QueenHiveState) => void): QueenHiveState {
    for (let s = 0; s < maxSteps; s++) {
      const state = this.step();
      if (onProgress) {
        onProgress(s, state);
      }
    }
    return this.getState();
  }
}
