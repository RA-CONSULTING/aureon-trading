import { MasterEquation } from './masterEquation';
import { RainbowBridge } from './rainbowBridge';
import { Prism } from './prism';
import { FTCPDetector } from './ftcpDetector';
import { LighthouseConsensus } from './lighthouseConsensus';
import { TradingSignalGenerator } from './tradingSignals';
import type { MarketData } from './binanceWebSocket';

export interface BacktestConfig {
  symbol: string;
  startDate: Date;
  endDate: Date;
  initialCapital: number;
  positionSize: number; // percentage of capital per trade (0-1)
  stopLossPercent: number;
  takeProfitPercent: number;
  tradingFee: number; // e.g., 0.001 for 0.1%
  slippage: number; // e.g., 0.0001 for 0.01%
  minCoherence: number;
  minLighthouseConfidence: number;
  minPrismLevel: number;
  requireLHE: boolean;
}

export interface BacktestTrade {
  entryTime: number;
  exitTime: number;
  symbol: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  exitReason: 'STOP_LOSS' | 'TAKE_PROFIT' | 'SIGNAL_EXIT' | 'END_OF_PERIOD';
  signalStrength: number;
  coherence: number;
  lighthouseValue: number;
}

export interface BacktestResults {
  config: BacktestConfig;
  trades: BacktestTrade[];
  equityCurve: { timestamp: number; equity: number; drawdown: number }[];
  metrics: {
    initialCapital: number;
    finalCapital: number;
    totalReturn: number;
    totalReturnPercent: number;
    totalTrades: number;
    winningTrades: number;
    losingTrades: number;
    winRate: number;
    profitFactor: number;
    maxDrawdown: number;
    maxDrawdownPercent: number;
    avgTradeDuration: number;
    sharpeRatio: number;
    avgWin: number;
    avgLoss: number;
    largestWin: number;
    largestLoss: number;
  };
}

export class BacktestEngine {
  private masterEq: MasterEquation;
  private rainbowBridge: RainbowBridge;
  private prism: Prism;
  private ftcpDetector: FTCPDetector;
  private lighthouse: LighthouseConsensus;
  private signalGen: TradingSignalGenerator;

  constructor() {
    this.masterEq = new MasterEquation();
    this.rainbowBridge = new RainbowBridge();
    this.prism = new Prism();
    this.ftcpDetector = new FTCPDetector();
    this.lighthouse = new LighthouseConsensus();
    this.signalGen = new TradingSignalGenerator();
  }

  async runBacktest(candles: any[], config: BacktestConfig): Promise<BacktestResults> {
    console.log(`🎯 Starting backtest with ${candles.length} candles`);
    
    // Reset all engines
    this.masterEq = new MasterEquation();
    this.rainbowBridge = new RainbowBridge();
    this.prism = new Prism();
    this.ftcpDetector = new FTCPDetector();
    this.lighthouse = new LighthouseConsensus();
    this.signalGen = new TradingSignalGenerator();

    const trades: BacktestTrade[] = [];
    const equityCurve: { timestamp: number; equity: number; drawdown: number }[] = [];
    
    let capital = config.initialCapital;
    let position: BacktestTrade | null = null;
    let peakCapital = capital;

    for (let i = 0; i < candles.length; i++) {
      const candle = candles[i];
      
      // Convert candle to MarketData format
      const marketData: MarketData = {
        timestamp: candle.timestamp,
        price: candle.close,
        volume: candle.volume,
        volatility: this.calculateVolatility(candles.slice(Math.max(0, i - 20), i + 1)),
        momentum: i > 0 ? (candle.close - candles[i - 1].close) / candles[i - 1].close : 0,
        spread: (candle.high - candle.low) / candle.close,
      };

      // Process through AUREON system
      const lambdaState = await this.masterEq.step(marketData);
      const rainbowState = this.rainbowBridge.map(lambdaState.lambda, lambdaState.coherence);
      const prismOutput = this.prism.transform(lambdaState.lambda, lambdaState.coherence, rainbowState.frequency);
      const ftcpResult = this.ftcpDetector.addPoint(marketData.timestamp, lambdaState.lambda);
      const Geff = this.ftcpDetector.computeGeff();
      const lighthouseState = this.lighthouse.validate(
        lambdaState.lambda,
        lambdaState.coherence,
        lambdaState.substrate,
        lambdaState.observer,
        lambdaState.echo,
        Geff,
        ftcpResult?.isFTCP || false
      );
      const signal = this.signalGen.generateSignal(lambdaState, lighthouseState, prismOutput);

      // Check if we have an open position
      if (position) {
        const currentPrice = candle.close;
        let shouldExit = false;
        let exitReason: BacktestTrade['exitReason'] = 'SIGNAL_EXIT';

        // Calculate current P&L
        if (position.side === 'LONG') {
          const pnlPercent = ((currentPrice - position.entryPrice) / position.entryPrice) * 100;
          
          if (pnlPercent <= -config.stopLossPercent) {
            shouldExit = true;
            exitReason = 'STOP_LOSS';
          } else if (pnlPercent >= config.takeProfitPercent) {
            shouldExit = true;
            exitReason = 'TAKE_PROFIT';
          } else if (signal.type === 'SHORT') {
            shouldExit = true;
            exitReason = 'SIGNAL_EXIT';
          }
        } else { // SHORT
          const pnlPercent = ((position.entryPrice - currentPrice) / position.entryPrice) * 100;
          
          if (pnlPercent <= -config.stopLossPercent) {
            shouldExit = true;
            exitReason = 'STOP_LOSS';
          } else if (pnlPercent >= config.takeProfitPercent) {
            shouldExit = true;
            exitReason = 'TAKE_PROFIT';
          } else if (signal.type === 'LONG') {
            shouldExit = true;
            exitReason = 'SIGNAL_EXIT';
          }
        }

        // Exit position if needed
        if (shouldExit || i === candles.length - 1) {
          const exitPrice = currentPrice * (1 + (position.side === 'LONG' ? -config.slippage : config.slippage));
          const grossPnl = position.side === 'LONG' 
            ? (exitPrice - position.entryPrice) * position.quantity
            : (position.entryPrice - exitPrice) * position.quantity;
          const fees = (position.entryPrice * position.quantity + exitPrice * position.quantity) * config.tradingFee;
          const netPnl = grossPnl - fees;
          
          position.exitTime = candle.timestamp;
          position.exitPrice = exitPrice;
          position.pnl = netPnl;
          position.pnlPercent = (netPnl / (position.entryPrice * position.quantity)) * 100;
          position.exitReason = i === candles.length - 1 ? 'END_OF_PERIOD' : exitReason;
          
          trades.push(position);
          capital += netPnl;
          position = null;

          console.log(`📤 Closed position: ${netPnl >= 0 ? '+' : ''}$${netPnl.toFixed(2)} (${exitReason})`);
        }
      }

      // Check for new entry signal
      if (!position && signal.type !== 'HOLD') {
        // Check filters
        const meetsCoherence = lambdaState.coherence >= config.minCoherence;
        const meetsLighthouse = lighthouseState.confidence >= config.minLighthouseConfidence;
        const meetsPrism = prismOutput.level >= config.minPrismLevel;
        const meetsLHE = !config.requireLHE || lighthouseState.isLHE;

        if (meetsCoherence && meetsLighthouse && meetsPrism && meetsLHE) {
          const positionValue = capital * config.positionSize;
          const entryPrice = candle.close * (1 + (signal.type === 'LONG' ? config.slippage : -config.slippage));
          const quantity = positionValue / entryPrice;

          position = {
            entryTime: candle.timestamp,
            exitTime: 0,
            symbol: config.symbol,
            side: signal.type as 'LONG' | 'SHORT',
            entryPrice,
            exitPrice: 0,
            quantity,
            pnl: 0,
            pnlPercent: 0,
            exitReason: 'SIGNAL_EXIT',
            signalStrength: signal.strength,
            coherence: lambdaState.coherence,
            lighthouseValue: lighthouseState.L,
          };

          console.log(`📥 Opened ${signal.type} position at $${entryPrice.toFixed(2)}`);
        }
      }

      // Update equity curve
      peakCapital = Math.max(peakCapital, capital);
      const drawdown = ((peakCapital - capital) / peakCapital) * 100;
      equityCurve.push({
        timestamp: candle.timestamp,
        equity: capital,
        drawdown,
      });
    }

    // Calculate final metrics
    const winningTrades = trades.filter(t => t.pnl > 0);
    const losingTrades = trades.filter(t => t.pnl < 0);
    const totalWinPnl = winningTrades.reduce((sum, t) => sum + t.pnl, 0);
    const totalLossPnl = Math.abs(losingTrades.reduce((sum, t) => sum + t.pnl, 0));
    
    const returns = equityCurve.map((point, i) => 
      i > 0 ? (point.equity - equityCurve[i - 1].equity) / equityCurve[i - 1].equity : 0
    );
    const avgReturn = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const stdReturn = Math.sqrt(returns.reduce((sum, r) => sum + Math.pow(r - avgReturn, 2), 0) / returns.length);
    const sharpeRatio = stdReturn > 0 ? (avgReturn / stdReturn) * Math.sqrt(252) : 0; // Annualized

    const avgTradeDuration = trades.reduce((sum, t) => sum + (t.exitTime - t.entryTime), 0) / (trades.length || 1);

    const results: BacktestResults = {
      config,
      trades,
      equityCurve,
      metrics: {
        initialCapital: config.initialCapital,
        finalCapital: capital,
        totalReturn: capital - config.initialCapital,
        totalReturnPercent: ((capital - config.initialCapital) / config.initialCapital) * 100,
        totalTrades: trades.length,
        winningTrades: winningTrades.length,
        losingTrades: losingTrades.length,
        winRate: trades.length > 0 ? (winningTrades.length / trades.length) * 100 : 0,
        profitFactor: totalLossPnl > 0 ? totalWinPnl / totalLossPnl : 0,
        maxDrawdown: Math.max(...equityCurve.map(e => e.drawdown)),
        maxDrawdownPercent: Math.max(...equityCurve.map(e => e.drawdown)),
        avgTradeDuration: avgTradeDuration / (1000 * 60), // Convert to minutes
        sharpeRatio,
        avgWin: winningTrades.length > 0 ? totalWinPnl / winningTrades.length : 0,
        avgLoss: losingTrades.length > 0 ? totalLossPnl / losingTrades.length : 0,
        largestWin: winningTrades.length > 0 ? Math.max(...winningTrades.map(t => t.pnl)) : 0,
        largestLoss: losingTrades.length > 0 ? Math.min(...losingTrades.map(t => t.pnl)) : 0,
      },
    };

    console.log(`✅ Backtest complete: ${results.metrics.totalTrades} trades, ${results.metrics.totalReturnPercent.toFixed(2)}% return`);

    return results;
  }

  private calculateVolatility(candles: any[]): number {
    if (candles.length < 2) return 0;
    
    const returns = [];
    for (let i = 1; i < candles.length; i++) {
      returns.push((candles[i].close - candles[i - 1].close) / candles[i - 1].close);
    }
    
    const mean = returns.reduce((sum, r) => sum + r, 0) / returns.length;
    const variance = returns.reduce((sum, r) => sum + Math.pow(r - mean, 2), 0) / returns.length;
    return Math.sqrt(variance);
  }
}
