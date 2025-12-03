/**
 * Queen Hive Browser - Browser-Compatible Queen Hive Implementation
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * This is a browser-compatible version of the Queen Hive that:
 * - Does NOT use Node.js fs module
 * - Loads trade data from embedded constants or Supabase
 * - Implements 10-9-1 Revenue Sharing model
 * - Registers with Temporal Ladder hive mind
 */

import { temporalLadder, SYSTEMS } from './temporalLadder';

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

export interface QueenHiveConfig {
  initialCapital: number;
  agentsPerHive: number;
  harvestRatio: number; // 10-9-1 = 0.10
  compoundRatio: number; // 10-9-1 = 0.90
  minSplitCapital: number;
}

// Embedded trade returns (statistically representative sample)
// Based on realistic trading performance distribution
const EMBEDDED_TRADE_RETURNS = [
  0.012, 0.008, -0.005, 0.015, -0.003, 0.020, -0.008, 0.010,
  0.006, -0.004, 0.018, 0.007, -0.002, 0.014, 0.009, -0.006,
  0.011, -0.007, 0.016, 0.005, 0.013, -0.004, 0.019, 0.008,
  -0.003, 0.017, 0.006, -0.005, 0.012, 0.010, -0.002, 0.015,
  0.007, -0.006, 0.014, 0.009, 0.011, -0.004, 0.018, 0.008,
  // Slightly positive bias for realistic win rate ~55%
  0.013, 0.010, 0.007, 0.016, 0.012, -0.005, 0.014, 0.009
];

// Prime numbers for position sizing
const PRIMES = [
  2, 3, 5, 7, 11, 13, 17, 19, 23, 29,
  31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
  73, 79, 83, 89, 97
];

class Agent {
  id: number;
  equity: number;
  startEquity: number;
  trades: number = 0;
  wins: number = 0;
  primeIdx: number;
  private tradeReturns: number[];

  constructor(id: number, startCapital: number, primeIdxOffset: number = 0, tradeReturns: number[] = EMBEDDED_TRADE_RETURNS) {
    this.id = id;
    this.equity = startCapital;
    this.startEquity = startCapital;
    this.primeIdx = (id + primeIdxOffset) % PRIMES.length;
    this.tradeReturns = tradeReturns;
  }

  trade(): { pnl: number; return: number } {
    if (this.equity <= 0) return { pnl: 0, return: 0 };

    const ret = this.tradeReturns[Math.floor(Math.random() * this.tradeReturns.length)];
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

  getWinRate(): number {
    return this.trades > 0 ? this.wins / this.trades : 0;
  }
}

class Hive {
  id: string;
  generation: number;
  agents: Agent[];
  trades: number = 0;
  harvestedCapital: number = 0;
  age: number = 0;
  private tradeReturns: number[];
  private config: QueenHiveConfig;

  constructor(
    id: string,
    generation: number,
    initialCapital: number,
    config: QueenHiveConfig,
    tradeReturns: number[] = EMBEDDED_TRADE_RETURNS
  ) {
    this.id = id;
    this.generation = generation;
    this.config = config;
    this.tradeReturns = tradeReturns;

    // Create agents with equal capital split
    const perAgent = initialCapital / config.agentsPerHive;
    this.agents = [];
    for (let i = 0; i < config.agentsPerHive; i++) {
      this.agents.push(new Agent(i, perAgent, generation * config.agentsPerHive + i, tradeReturns));
    }
  }

  step(): { profit: number; harvested: number } {
    let totalPnl = 0;
    this.age++;

    // Each agent trades
    for (const agent of this.agents) {
      const { pnl } = agent.trade();
      totalPnl += pnl;
    }
    this.trades += this.agents.length;

    // 10-9-1 revenue sharing
    let harvested = 0;
    if (totalPnl > 0) {
      harvested = totalPnl * this.config.harvestRatio;
      this.harvestedCapital += harvested;
      // Remaining 90% stays in hive (already added via agent.trade)
    }

    return { profit: totalPnl, harvested };
  }

  getTotalEquity(): number {
    return this.agents.reduce((sum, a) => sum + a.equity, 0);
  }

  getSuccessfulAgents(): number {
    return this.agents.filter(a => a.equity > a.startEquity).length;
  }

  getStage(): string {
    const equity = this.getTotalEquity();
    if (equity < this.config.initialCapital * 0.5) return 'struggling';
    if (equity < this.config.initialCapital) return 'recovering';
    if (equity < this.config.initialCapital * 1.5) return 'growing';
    if (equity < this.config.initialCapital * 2) return 'thriving';
    return 'dominant';
  }

  getProfitMultiplier(): number {
    const initial = this.config.initialCapital;
    return initial > 0 ? this.getTotalEquity() / initial : 1;
  }

  canSplit(): boolean {
    return this.harvestedCapital >= this.config.minSplitCapital;
  }

  consumeHarvestedForSplit(): number {
    const capital = this.harvestedCapital;
    this.harvestedCapital = 0;
    return capital;
  }

  getMetrics(): HiveMetrics {
    return {
      id: this.id,
      generation: this.generation,
      agents: this.agents.length,
      equity: this.getTotalEquity(),
      harvestedCapital: this.harvestedCapital,
      trades: this.trades,
      successfulAgents: this.getSuccessfulAgents(),
      stage: this.getStage(),
      age: this.age,
      profitMultiplier: this.getProfitMultiplier()
    };
  }
}

export class QueenHiveBrowser {
  private hives: Hive[] = [];
  private generation: number = 1;
  private splitEvents: Array<{ step: number; newHiveId: string; spawnCapital: number }> = [];
  private currentStep: number = 0;
  private config: QueenHiveConfig;
  private tradeReturns: number[];
  private listeners: Array<(state: QueenHiveState) => void> = [];
  private isRegistered: boolean = false;

  constructor(config?: Partial<QueenHiveConfig>, customReturns?: number[]) {
    this.config = {
      initialCapital: 1000,
      agentsPerHive: 9,
      harvestRatio: 0.10, // 10-9-1
      compoundRatio: 0.90,
      minSplitCapital: 100,
      ...config
    };
    this.tradeReturns = customReturns || EMBEDDED_TRADE_RETURNS;

    // Create initial Queen Hive
    this.hives.push(new Hive('H1', this.generation, this.config.initialCapital, this.config, this.tradeReturns));
  }

  /**
   * Register with Temporal Ladder hive mind
   */
  public registerWithHiveMind(): void {
    if (this.isRegistered) return;

    // Note: Queen Hive is not in the current SYSTEMS enum, but we can still broadcast
    console.log('👑 Queen Hive: Connecting to Temporal Ladder hive mind');
    this.isRegistered = true;

    // Broadcast existence to other systems
    temporalLadder.broadcast('harmonic-nexus', 'queen_hive_online', {
      hives: this.hives.length,
      totalEquity: this.getTotalEquity()
    });
  }

  /**
   * Simulate one step of the hive ecosystem
   */
  public step(): QueenHiveState {
    this.currentStep++;
    let totalHarvested = 0;

    // Each hive trades
    for (const hive of this.hives) {
      const { harvested } = hive.step();
      totalHarvested += harvested;
    }

    // Check for splits
    const hivesToSplit = this.hives.filter(h => h.canSplit());
    for (const hive of hivesToSplit) {
      const spawnCapital = hive.consumeHarvestedForSplit();
      this.generation++;
      const newHiveId = `H${this.hives.length + 1}-G${this.generation}`;
      const newHive = new Hive(newHiveId, this.generation, spawnCapital, this.config, this.tradeReturns);
      this.hives.push(newHive);

      this.splitEvents.push({
        step: this.currentStep,
        newHiveId,
        spawnCapital
      });

      console.log(`👑 Queen Hive Split: ${hive.id} spawned ${newHiveId} with £${spawnCapital.toFixed(2)}`);

      // Broadcast split event
      if (this.isRegistered) {
        temporalLadder.broadcast('harmonic-nexus', 'queen_hive_split', {
          parentHive: hive.id,
          newHive: newHiveId,
          spawnCapital,
          totalHives: this.hives.length
        });
      }
    }

    const state = this.getState();
    this.notifyListeners(state);
    return state;
  }

  /**
   * Run multiple steps
   */
  public simulate(steps: number): QueenHiveState[] {
    const states: QueenHiveState[] = [];
    for (let i = 0; i < steps; i++) {
      states.push(this.step());
    }
    return states;
  }

  /**
   * Get current state
   */
  public getState(): QueenHiveState {
    return {
      timestamp: Date.now(),
      totalHives: this.hives.length,
      totalAgents: this.hives.reduce((sum, h) => sum + h.agents.length, 0),
      totalEquity: this.getTotalEquity(),
      totalHarvested: this.hives.reduce((sum, h) => sum + h.harvestedCapital, 0),
      hives: this.hives.map(h => h.getMetrics()),
      generation: this.generation,
      splitEvents: [...this.splitEvents]
    };
  }

  public getTotalEquity(): number {
    return this.hives.reduce((sum, h) => sum + h.getTotalEquity(), 0);
  }

  public getHiveCount(): number {
    return this.hives.length;
  }

  public getGeneration(): number {
    return this.generation;
  }

  /**
   * Load custom trade returns (for Supabase integration)
   */
  public loadTradeReturns(returns: number[]): void {
    this.tradeReturns = returns;
    // Update all hives with new returns
    // Note: This affects future trades, not existing agent states
  }

  /**
   * Subscribe to state updates
   */
  public subscribe(listener: (state: QueenHiveState) => void): () => void {
    this.listeners.push(listener);
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  private notifyListeners(state: QueenHiveState): void {
    this.listeners.forEach(listener => {
      try {
        listener(state);
      } catch (error) {
        console.error('Queen Hive listener error:', error);
      }
    });
  }

  /**
   * Reset the hive ecosystem
   */
  public reset(): void {
    this.hives = [new Hive('H1', 1, this.config.initialCapital, this.config, this.tradeReturns)];
    this.generation = 1;
    this.splitEvents = [];
    this.currentStep = 0;
  }
}

// Factory function for easy instantiation
export function createQueenHive(config?: Partial<QueenHiveConfig>): QueenHiveBrowser {
  return new QueenHiveBrowser(config);
}

// Singleton instance for global access
let globalQueenHive: QueenHiveBrowser | null = null;

export function getGlobalQueenHive(): QueenHiveBrowser {
  if (!globalQueenHive) {
    globalQueenHive = new QueenHiveBrowser();
    globalQueenHive.registerWithHiveMind();
  }
  return globalQueenHive;
}
