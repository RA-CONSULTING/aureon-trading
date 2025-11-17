import { BacktestEngine, type BacktestConfig, type BacktestResults } from './backtestEngine';

export type RandomizationMethod = 'bootstrap' | 'parameter_variation' | 'noise_injection' | 'combined';

export interface MonteCarloConfig {
  baseConfig: BacktestConfig;
  numSimulations: number;
  randomizationMethod: RandomizationMethod;
  parameterRanges?: {
    positionSize?: [number, number];
    stopLoss?: [number, number];
    takeProfit?: [number, number];
    minCoherence?: [number, number];
    minLighthouseConfidence?: [number, number];
  };
  bootstrapBlockSize?: number;
  noiseLevel?: number;
}

export interface SimulationResult {
  simulationId: number;
  config: BacktestConfig;
  results: BacktestResults;
}

export interface MonteCarloResults {
  simulations: SimulationResult[];
  aggregateMetrics: {
    totalReturn: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      ci95Lower: number;
      ci95Upper: number;
      ci99Lower: number;
      ci99Upper: number;
    };
    winRate: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      ci95Lower: number;
      ci95Upper: number;
    };
    profitFactor: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      ci95Lower: number;
      ci95Upper: number;
    };
    maxDrawdown: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      ci95Lower: number;
      ci95Upper: number;
    };
    sharpeRatio: {
      mean: number;
      median: number;
      std: number;
      min: number;
      max: number;
      ci95Lower: number;
      ci95Upper: number;
    };
  };
  distribution: {
    totalReturns: number[];
    winRates: number[];
    profitFactors: number[];
    maxDrawdowns: number[];
  };
  robustnessScore: number; // 0-100, higher is better
  successRate: number; // % of simulations with positive returns
}

export class MonteCarloEngine {
  private backtestEngine: BacktestEngine;

  constructor() {
    this.backtestEngine = new BacktestEngine();
  }

  async runSimulation(
    candles: any[],
    config: MonteCarloConfig,
    onProgress?: (progress: number, currentSim: number) => void
  ): Promise<MonteCarloResults> {
    console.log(`🎲 Starting Monte Carlo simulation with ${config.numSimulations} iterations`);
    
    const simulations: SimulationResult[] = [];

    for (let i = 0; i < config.numSimulations; i++) {
      // Generate randomized configuration and/or data
      const { randomConfig, randomCandles } = this.generateRandomizedScenario(
        candles,
        config.baseConfig,
        config
      );

      // Run backtest with randomized scenario
      const results = await this.backtestEngine.runBacktest(randomCandles, randomConfig);

      simulations.push({
        simulationId: i + 1,
        config: randomConfig,
        results,
      });

      // Report progress
      const progress = ((i + 1) / config.numSimulations) * 100;
      if (onProgress) {
        onProgress(progress, i + 1);
      }

      console.log(`✅ Simulation ${i + 1}/${config.numSimulations} complete: ${results.metrics.totalReturnPercent.toFixed(2)}% return`);
    }

    // Calculate aggregate metrics and confidence intervals
    const aggregateMetrics = this.calculateAggregateMetrics(simulations);
    const distribution = this.extractDistributions(simulations);
    const robustnessScore = this.calculateRobustnessScore(simulations, aggregateMetrics);
    const successRate = (simulations.filter(s => s.results.metrics.totalReturn > 0).length / simulations.length) * 100;

    return {
      simulations,
      aggregateMetrics,
      distribution,
      robustnessScore,
      successRate,
    };
  }

  private generateRandomizedScenario(
    candles: any[],
    baseConfig: BacktestConfig,
    mcConfig: MonteCarloConfig
  ): { randomConfig: BacktestConfig; randomCandles: any[] } {
    let randomConfig = { ...baseConfig };
    let randomCandles = [...candles];

    switch (mcConfig.randomizationMethod) {
      case 'bootstrap':
        randomCandles = this.bootstrapResample(candles, mcConfig.bootstrapBlockSize || 10);
        break;

      case 'parameter_variation':
        randomConfig = this.varyParameters(baseConfig, mcConfig.parameterRanges!);
        break;

      case 'noise_injection':
        randomCandles = this.injectNoise(candles, mcConfig.noiseLevel || 0.01);
        break;

      case 'combined':
        randomConfig = this.varyParameters(baseConfig, mcConfig.parameterRanges!);
        randomCandles = this.bootstrapResample(candles, mcConfig.bootstrapBlockSize || 10);
        randomCandles = this.injectNoise(randomCandles, mcConfig.noiseLevel || 0.005);
        break;
    }

    return { randomConfig, randomCandles };
  }

  private bootstrapResample(candles: any[], blockSize: number): any[] {
    // Block bootstrap to preserve time series structure
    const numBlocks = Math.ceil(candles.length / blockSize);
    const resampled: any[] = [];

    for (let i = 0; i < numBlocks; i++) {
      const randomStart = Math.floor(Math.random() * (candles.length - blockSize));
      const block = candles.slice(randomStart, randomStart + blockSize);
      resampled.push(...block);
    }

    return resampled.slice(0, candles.length);
  }

  private varyParameters(
    baseConfig: BacktestConfig,
    ranges: NonNullable<MonteCarloConfig['parameterRanges']>
  ): BacktestConfig {
    const config = { ...baseConfig };

    if (ranges.positionSize) {
      config.positionSize = this.randomInRange(ranges.positionSize[0], ranges.positionSize[1]);
    }

    if (ranges.stopLoss) {
      config.stopLossPercent = this.randomInRange(ranges.stopLoss[0], ranges.stopLoss[1]);
    }

    if (ranges.takeProfit) {
      config.takeProfitPercent = this.randomInRange(ranges.takeProfit[0], ranges.takeProfit[1]);
    }

    if (ranges.minCoherence) {
      config.minCoherence = this.randomInRange(ranges.minCoherence[0], ranges.minCoherence[1]);
    }

    if (ranges.minLighthouseConfidence) {
      config.minLighthouseConfidence = this.randomInRange(
        ranges.minLighthouseConfidence[0],
        ranges.minLighthouseConfidence[1]
      );
    }

    return config;
  }

  private injectNoise(candles: any[], noiseLevel: number): any[] {
    return candles.map(candle => {
      const priceNoise = 1 + (Math.random() - 0.5) * 2 * noiseLevel;
      const volumeNoise = 1 + (Math.random() - 0.5) * 2 * noiseLevel;

      return {
        ...candle,
        open: candle.open * priceNoise,
        high: candle.high * priceNoise,
        low: candle.low * priceNoise,
        close: candle.close * priceNoise,
        volume: candle.volume * volumeNoise,
      };
    });
  }

  private randomInRange(min: number, max: number): number {
    return min + Math.random() * (max - min);
  }

  private calculateAggregateMetrics(simulations: SimulationResult[]) {
    const totalReturns = simulations.map(s => s.results.metrics.totalReturnPercent);
    const winRates = simulations.map(s => s.results.metrics.winRate);
    const profitFactors = simulations.map(s => s.results.metrics.profitFactor);
    const maxDrawdowns = simulations.map(s => s.results.metrics.maxDrawdownPercent);
    const sharpeRatios = simulations.map(s => s.results.metrics.sharpeRatio);

    return {
      totalReturn: this.calculateStats(totalReturns),
      winRate: this.calculateStats(winRates),
      profitFactor: this.calculateStats(profitFactors),
      maxDrawdown: this.calculateStats(maxDrawdowns),
      sharpeRatio: this.calculateStats(sharpeRatios),
    };
  }

  private calculateStats(values: number[]) {
    const sorted = [...values].sort((a, b) => a - b);
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + Math.pow(v - mean, 2), 0) / values.length;
    const std = Math.sqrt(variance);

    // Confidence intervals
    const ci95Lower = sorted[Math.floor(values.length * 0.025)];
    const ci95Upper = sorted[Math.floor(values.length * 0.975)];
    const ci99Lower = sorted[Math.floor(values.length * 0.005)];
    const ci99Upper = sorted[Math.floor(values.length * 0.995)];

    return {
      mean,
      median: sorted[Math.floor(values.length / 2)],
      std,
      min: sorted[0],
      max: sorted[sorted.length - 1],
      ci95Lower,
      ci95Upper,
      ci99Lower,
      ci99Upper,
    };
  }

  private extractDistributions(simulations: SimulationResult[]) {
    return {
      totalReturns: simulations.map(s => s.results.metrics.totalReturnPercent),
      winRates: simulations.map(s => s.results.metrics.winRate),
      profitFactors: simulations.map(s => s.results.metrics.profitFactor),
      maxDrawdowns: simulations.map(s => s.results.metrics.maxDrawdownPercent),
    };
  }

  private calculateRobustnessScore(
    simulations: SimulationResult[],
    aggregateMetrics: MonteCarloResults['aggregateMetrics']
  ): number {
    // Robustness score based on:
    // 1. Consistency (low std relative to mean)
    // 2. Positive returns in most scenarios
    // 3. Limited downside risk
    
    const consistencyScore = Math.max(0, 100 - (aggregateMetrics.totalReturn.std / Math.abs(aggregateMetrics.totalReturn.mean)) * 50);
    const positiveReturns = simulations.filter(s => s.results.metrics.totalReturn > 0).length;
    const successScore = (positiveReturns / simulations.length) * 100;
    const downsideScore = Math.max(0, 100 - aggregateMetrics.maxDrawdown.mean);

    return (consistencyScore * 0.3 + successScore * 0.4 + downsideScore * 0.3);
  }
}
