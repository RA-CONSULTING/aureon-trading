/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * 🎵 THE DANCE OF SPACE AND TIME 🎵
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * QUACKERS LIVE SYMPHONY - 12 API Keys | One Wallet | Maximum Harmony
 * 
 * Master Equation: Λ(t) = S(t) + O(t) + E(t)
 * 9 Auris Nodes | Rainbow Bridge | Real Money | REAL TRADES
 * 
 * Author: Gary Leckey
 * Date: November 25, 2025
 * 
 * "Four chords, infinite possibilities" 🦆
 * ═══════════════════════════════════════════════════════════════════════════════
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Load API keys
const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

// ═══════════════════════════════════════════════════════════════════════════════
// 🦆 QUACKER CLIENTS - 12 API connections to one wallet
// ═══════════════════════════════════════════════════════════════════════════════

interface QuackerClient {
  name: string;
  client: any;
  lastUsed: number;
  requestCount: number;
}

const quackers: QuackerClient[] = [];
let currentQuacker = 0;

// ═══════════════════════════════════════════════════════════════════════════════
// 9 AURIS NODES - The Ensemble
// ═══════════════════════════════════════════════════════════════════════════════

interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  change: number;
  bid: number;
  ask: number;
}

const aurisNodes = {
  tiger: (d: MarketData) => ((d.high - d.low) / d.price) * 100 + (d.volume > 1000000 ? 0.2 : 0),
  falcon: (d: MarketData) => Math.abs(d.change) * 0.7 + Math.min(d.volume / 10000000, 0.3),
  hummingbird: (d: MarketData) => 1 / (1 + ((d.high - d.low) / d.price) * 10),
  dolphin: (d: MarketData) => Math.sin(d.change * Math.PI / 10) * 0.5 + 0.5,
  deer: (d: MarketData) => (d.price > d.open ? 0.6 : 0.4) + (d.change > 0 ? 0.2 : -0.1),
  owl: (d: MarketData) => Math.cos(d.change * Math.PI / 10) * 0.3 + (d.price < d.open ? 0.3 : 0),
  panda: (d: MarketData) => 0.5 + Math.sin(Date.now() / 60000) * 0.1,
  cargoShip: (d: MarketData) => d.volume > 5000000 ? 0.8 : d.volume > 1000000 ? 0.5 : 0.3,
  clownfish: (d: MarketData) => Math.abs(d.price - d.open) / d.price * 100,
};

const nodeWeights = {
  tiger: 1.2, falcon: 1.1, hummingbird: 0.9, dolphin: 1.0,
  deer: 0.8, owl: 0.9, panda: 0.7, cargoShip: 1.0, clownfish: 0.7
};

// ═══════════════════════════════════════════════════════════════════════════════
// MASTER EQUATION: Λ(t) = S(t) + O(t) + E(t)
// ═══════════════════════════════════════════════════════════════════════════════

const lambdaHistory: Map<string, number[]> = new Map();
const OBSERVER_WEIGHT = 0.3;
const ECHO_WEIGHT = 0.2;
const ECHO_DEPTH = 5;

function computeSubstrate(data: MarketData): number {
  let sum = 0;
  let weightSum = 0;
  
  for (const [name, fn] of Object.entries(aurisNodes)) {
    const weight = nodeWeights[name as keyof typeof nodeWeights];
    sum += fn(data) * weight;
    weightSum += weight;
  }
  
  return sum / weightSum;
}

function computeLambda(symbol: string, data: MarketData): number {
  if (!lambdaHistory.has(symbol)) {
    lambdaHistory.set(symbol, []);
  }
  const history = lambdaHistory.get(symbol)!;
  
  const S = computeSubstrate(data);
  const O = history.length > 0 ? history[history.length - 1] * OBSERVER_WEIGHT : 0;
  const E = history.length >= ECHO_DEPTH 
    ? history.slice(-ECHO_DEPTH).reduce((a, b) => a + b, 0) / ECHO_DEPTH * ECHO_WEIGHT 
    : 0;
  
  const lambda = S + O + E;
  history.push(lambda);
  if (history.length > 100) history.shift();
  
  return lambda;
}

// ═══════════════════════════════════════════════════════════════════════════════
// COHERENCE: Γ = 1 - σ²/c
// ═══════════════════════════════════════════════════════════════════════════════

function computeCoherence(data: MarketData): number {
  const responses: number[] = [];
  for (const fn of Object.values(aurisNodes)) {
    responses.push(fn(data));
  }
  
  const mean = responses.reduce((a, b) => a + b, 0) / responses.length;
  const variance = responses.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / responses.length;
  
  return Math.max(0, Math.min(1, 1 - variance / 10));
}

// ═══════════════════════════════════════════════════════════════════════════════
// RAINBOW BRIDGE: Frequency Mapping
// ═══════════════════════════════════════════════════════════════════════════════

function getFrequency(lambda: number, coherence: number): { hz: number; color: string; state: string } {
  const baseHz = 110 + lambda * 100;
  const targetHz = 528; // Love frequency
  const hz = baseHz * (1 - coherence * 0.3) + targetHz * (coherence * 0.3);
  
  if (hz < 200) return { hz, color: '🔴', state: 'FEAR' };
  if (hz < 300) return { hz, color: '🟠', state: 'FORMING' };
  if (hz < 400) return { hz, color: '🟡', state: 'FOCUS' };
  if (hz < 528) return { hz, color: '🟢', state: 'FLOW' };
  if (hz < 700) return { hz, color: '💚', state: 'LOVE' };
  if (hz < 850) return { hz, color: '🔵', state: 'AWE' };
  return { hz, color: '🟣', state: 'UNITY' };
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING CONFIG
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // Coherence thresholds
  ENTRY_THRESHOLD: 0.75,  // Lower threshold to catch more opportunities
  EXIT_THRESHOLD: 0.70,
  
  // Risk management
  RISK_PER_TRADE: 0.02,   // 2% of available balance per trade
  STOP_LOSS: 0.008,       // 0.8%
  TAKE_PROFIT: 0.018,     // 1.8%
  
  // Trading pairs - what we have in wallet
  PAIRS: [
    { symbol: 'DOGEUSDT', asset: 'DOGE', minQty: 1, stepSize: 1 },
    { symbol: 'ADAUSDT', asset: 'ADA', minQty: 1, stepSize: 1 },
    { symbol: 'DOTUSDT', asset: 'DOT', minQty: 0.01, stepSize: 0.01 },
    { symbol: 'LINKUSDT', asset: 'LINK', minQty: 0.01, stepSize: 0.01 },
    { symbol: 'BNBUSDT', asset: 'BNB', minQty: 0.001, stepSize: 0.001 },
    { symbol: 'BTCUSDT', asset: 'BTC', minQty: 0.00001, stepSize: 0.00001 },
  ],
  
  // Timing
  SCAN_INTERVAL: 3000, // 3 seconds
};

// ═══════════════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════════════

interface Position {
  symbol: string;
  asset: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  quantity: number;
  stopLoss: number;
  takeProfit: number;
  entryTime: Date;
  quacker: string;
}

interface WalletBalance {
  asset: string;
  free: number;
  locked: number;
}

const state = {
  balances: new Map<string, WalletBalance>(),
  positions: new Map<string, Position>(),
  trades: { wins: 0, losses: 0, total: 0 },
  pnl: 0,
  startTime: new Date(),
  startValue: 0,
  cycle: 0,
};

// ═══════════════════════════════════════════════════════════════════════════════
// QUACKER ROUND-ROBIN - Distribute API calls across 12 keys
// ═══════════════════════════════════════════════════════════════════════════════

function getNextQuacker(): QuackerClient {
  const quacker = quackers[currentQuacker];
  currentQuacker = (currentQuacker + 1) % quackers.length;
  quacker.lastUsed = Date.now();
  quacker.requestCount++;
  return quacker;
}

// ═══════════════════════════════════════════════════════════════════════════════
// BINANCE FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function getBalances(): Promise<void> {
  const quacker = getNextQuacker();
  const account = await quacker.client.accountInfo();
  
  state.balances.clear();
  for (const b of account.balances) {
    const free = parseFloat(b.free);
    const locked = parseFloat(b.locked);
    if (free > 0 || locked > 0) {
      state.balances.set(b.asset, { asset: b.asset, free, locked });
    }
  }
}

async function getMarketData(symbol: string): Promise<MarketData> {
  const quacker = getNextQuacker();
  const [ticker, book] = await Promise.all([
    quacker.client.dailyStats({ symbol }),
    quacker.client.book({ symbol, limit: 1 }),
  ]);
  
  return {
    symbol,
    price: parseFloat(ticker.lastPrice),
    volume: parseFloat(ticker.volume),
    high: parseFloat(ticker.highPrice),
    low: parseFloat(ticker.lowPrice),
    open: parseFloat(ticker.openPrice),
    change: parseFloat(ticker.priceChangePercent),
    bid: parseFloat(book.bids[0]?.price || ticker.lastPrice),
    ask: parseFloat(book.asks[0]?.price || ticker.lastPrice),
  };
}

async function placeTrade(
  symbol: string, 
  side: 'BUY' | 'SELL', 
  quantity: number,
  stepSize: number
): Promise<{ success: boolean; price?: number; qty?: number; quacker?: string }> {
  const quacker = getNextQuacker();
  
  // Round quantity to step size
  const precision = stepSize.toString().split('.')[1]?.length || 0;
  const roundedQty = Math.floor(quantity / stepSize) * stepSize;
  const qtyStr = roundedQty.toFixed(precision);
  
  try {
    const order = await quacker.client.order({
      symbol,
      side,
      type: 'MARKET',
      quantity: qtyStr,
    });
    
    const filledPrice = order.fills?.length > 0 
      ? parseFloat(order.fills[0].price) 
      : parseFloat(order.price);
    
    return { 
      success: true, 
      price: filledPrice, 
      qty: parseFloat(order.executedQty),
      quacker: quacker.name 
    };
  } catch (error: any) {
    console.log(`  ❌ ${quacker.name}: ${error.message}`);
    return { success: false };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

async function checkEntry(pair: typeof CONFIG.PAIRS[0], data: MarketData): Promise<void> {
  if (state.positions.has(pair.symbol)) return;
  
  const lambda = computeLambda(pair.symbol, data);
  const coherence = computeCoherence(data);
  const freq = getFrequency(lambda, coherence);
  
  // Check if we have balance to trade
  const balance = state.balances.get(pair.asset);
  const usdtBalance = state.balances.get('USDT') || state.balances.get('LDUSDC');
  
  if (coherence >= CONFIG.ENTRY_THRESHOLD) {
    const direction = data.change > 0 ? 'LONG' : 'SHORT';
    
    console.log(`\n${freq.color} [${pair.symbol}] Λ=${lambda.toFixed(3)} Γ=${coherence.toFixed(3)} ${freq.hz.toFixed(0)}Hz ${freq.state}`);
    
    let quantity = 0;
    let side: 'BUY' | 'SELL' = 'BUY';
    
    if (direction === 'LONG' && usdtBalance && usdtBalance.free > 5) {
      // Buy with USDT
      const tradeAmount = usdtBalance.free * CONFIG.RISK_PER_TRADE;
      quantity = tradeAmount / data.ask;
      side = 'BUY';
    } else if (direction === 'SHORT' && balance && balance.free > pair.minQty) {
      // Sell existing asset
      quantity = balance.free * CONFIG.RISK_PER_TRADE;
      side = 'SELL';
    } else {
      return; // No balance for this direction
    }
    
    if (quantity < pair.minQty) return;
    
    console.log(`  🎯 ${direction} SIGNAL @ $${data.price.toFixed(4)}`);
    
    const result = await placeTrade(pair.symbol, side, quantity, pair.stepSize);
    
    if (result.success && result.price && result.qty) {
      const stopLoss = direction === 'LONG' 
        ? result.price * (1 - CONFIG.STOP_LOSS)
        : result.price * (1 + CONFIG.STOP_LOSS);
      const takeProfit = direction === 'LONG'
        ? result.price * (1 + CONFIG.TAKE_PROFIT)
        : result.price * (1 - CONFIG.TAKE_PROFIT);
      
      state.positions.set(pair.symbol, {
        symbol: pair.symbol,
        asset: pair.asset,
        side: direction,
        entryPrice: result.price,
        quantity: result.qty,
        stopLoss,
        takeProfit,
        entryTime: new Date(),
        quacker: result.quacker!,
      });
      
      state.trades.total++;
      console.log(`  ✅ FILLED via ${result.quacker}: ${result.qty} @ $${result.price.toFixed(4)}`);
      console.log(`  📊 SL: $${stopLoss.toFixed(4)} | TP: $${takeProfit.toFixed(4)}`);
    }
  }
}

async function checkExit(pair: typeof CONFIG.PAIRS[0], data: MarketData): Promise<void> {
  const position = state.positions.get(pair.symbol);
  if (!position) return;
  
  const coherence = computeCoherence(data);
  let exitReason = '';
  let isWin = false;
  
  // Check stop loss
  if (position.side === 'LONG' && data.price <= position.stopLoss) {
    exitReason = '🛑 STOP LOSS';
  } else if (position.side === 'SHORT' && data.price >= position.stopLoss) {
    exitReason = '🛑 STOP LOSS';
  }
  // Check take profit
  else if (position.side === 'LONG' && data.price >= position.takeProfit) {
    exitReason = '🎯 TAKE PROFIT';
    isWin = true;
  } else if (position.side === 'SHORT' && data.price <= position.takeProfit) {
    exitReason = '🎯 TAKE PROFIT';
    isWin = true;
  }
  // Check coherence drop
  else if (coherence < CONFIG.EXIT_THRESHOLD) {
    exitReason = '📉 COHERENCE DROP';
    isWin = (position.side === 'LONG' && data.price > position.entryPrice) ||
            (position.side === 'SHORT' && data.price < position.entryPrice);
  }
  
  if (exitReason) {
    const pnlPercent = position.side === 'LONG'
      ? (data.price - position.entryPrice) / position.entryPrice * 100
      : (position.entryPrice - data.price) / position.entryPrice * 100;
    const pnlValue = position.quantity * position.entryPrice * (pnlPercent / 100);
    
    console.log(`\n  ${exitReason} [${pair.symbol}]`);
    
    const side = position.side === 'LONG' ? 'SELL' : 'BUY';
    const result = await placeTrade(pair.symbol, side, position.quantity, pair.stepSize);
    
    if (result.success) {
      console.log(`  ${pnlPercent >= 0 ? '✅' : '❌'} PnL: ${pnlPercent >= 0 ? '+' : ''}${pnlPercent.toFixed(2)}% ($${pnlValue.toFixed(4)})`);
      console.log(`  📤 Closed via ${result.quacker}`);
      
      state.positions.delete(pair.symbol);
      state.pnl += pnlValue;
      if (isWin || pnlPercent > 0) state.trades.wins++;
      else state.trades.losses++;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISPLAY
// ═══════════════════════════════════════════════════════════════════════════════

function displayStatus(): void {
  const elapsed = (Date.now() - state.startTime.getTime()) / 1000 / 60;
  const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
  
  // Calculate current portfolio value
  let portfolioValue = 0;
  state.balances.forEach((b, asset) => {
    if (asset === 'USDT' || asset === 'LDUSDC') {
      portfolioValue += b.free + b.locked;
    }
  });
  
  const roi = state.startValue > 0 ? ((portfolioValue - state.startValue) / state.startValue * 100) : 0;
  
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🎵 THE DANCE OF SPACE AND TIME - ${new Date().toLocaleTimeString()}                        ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  ⏱️  Runtime: ${elapsed.toFixed(1)} min | 🦆 Quackers: ${quackers.length} | 📊 Cycle: ${state.cycle}              ║
║  💰 Trades: ${state.trades.total} (W:${state.trades.wins} L:${state.trades.losses}) | 🎯 Win Rate: ${winRate.toFixed(1)}%                   ║
║  📈 PnL: $${state.pnl.toFixed(4)} | 📍 Positions: ${state.positions.size}                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝`);
  
  // Show quacker activity
  const activeQuackers = quackers.filter(q => q.requestCount > 0);
  if (activeQuackers.length > 0) {
    console.log(`  🦆 Quacker Activity: ${activeQuackers.map(q => `${q.name}(${q.requestCount})`).join(' ')}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN LOOP
// ═══════════════════════════════════════════════════════════════════════════════

async function initializeQuackers(): Promise<void> {
  const BinanceLib = await import('binance-api-node');
  
  for (const key of keys) {
    const client = (BinanceLib as any).default({
      apiKey: key.apiKey,
      apiSecret: key.apiSecret,
    });
    
    quackers.push({
      name: key.name,
      client,
      lastUsed: 0,
      requestCount: 0,
    });
  }
}

async function runTheDance(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🎵 THE DANCE OF SPACE AND TIME 🎵                                          ║
║                                                                               ║
║   ████████╗██╗  ██╗███████╗    ██████╗  █████╗ ███╗   ██╗ ██████╗███████╗    ║
║   ╚══██╔══╝██║  ██║██╔════╝    ██╔══██╗██╔══██╗████╗  ██║██╔════╝██╔════╝    ║
║      ██║   ███████║█████╗      ██║  ██║███████║██╔██╗ ██║██║     █████╗      ║
║      ██║   ██╔══██║██╔══╝      ██║  ██║██╔══██║██║╚██╗██║██║     ██╔══╝      ║
║      ██║   ██║  ██║███████╗    ██████╔╝██║  ██║██║ ╚████║╚██████╗███████╗    ║
║      ╚═╝   ╚═╝  ╚═╝╚══════╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝    ║
║                                                                               ║
║  🔴 LIVE TRADING - BINANCE - 12 QUACKERS - ONE WALLET 🔴                     ║
║                                                                               ║
║  Master Equation: Λ(t) = S(t) + O(t) + E(t)                                  ║
║  9 Auris Nodes | Rainbow Bridge | Coherence Trading                          ║
║                                                                               ║
║  Author: Gary Leckey                                                          ║
║  "Four chords, infinite possibilities" 🦆                                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  // Initialize all quacker clients
  console.log(`\n🦆 Initializing ${keys.length} Quackers...`);
  await initializeQuackers();
  console.log(`✅ ${quackers.length} Quackers ready to dance!\n`);

  // Get initial balances
  try {
    await getBalances();
    console.log(`💰 Wallet loaded:`);
    state.balances.forEach((b, asset) => {
      console.log(`   ${asset}: ${b.free.toFixed(8)} (free) + ${b.locked.toFixed(8)} (locked)`);
    });
    
    // Calculate starting value
    const usdt = state.balances.get('USDT');
    const ldusdc = state.balances.get('LDUSDC');
    state.startValue = (usdt?.free || 0) + (ldusdc?.free || 0);
    
  } catch (error: any) {
    console.error(`❌ Failed to load wallet: ${error.message}`);
    return;
  }

  console.log(`\n🚀 Starting the dance...\n`);
  console.log(`${'═'.repeat(60)}`);

  // Main trading loop
  while (true) {
    state.cycle++;
    
    try {
      // Refresh balances every 10 cycles
      if (state.cycle % 10 === 0) {
        await getBalances();
      }
      
      // Scan all pairs
      for (const pair of CONFIG.PAIRS) {
        try {
          const data = await getMarketData(pair.symbol);
          await checkExit(pair, data);
          await checkEntry(pair, data);
        } catch (error: any) {
          // Silently continue on individual pair errors
        }
      }
      
      // Display status every 10 cycles
      if (state.cycle % 10 === 0) {
        displayStatus();
      }
      
    } catch (error: any) {
      console.log(`  ⚠️  Cycle error: ${error.message}`);
    }
    
    // Wait before next scan
    await new Promise(resolve => setTimeout(resolve, CONFIG.SCAN_INTERVAL));
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// 🎵 START THE DANCE! 🎵
// ═══════════════════════════════════════════════════════════════════════════════

runTheDance().catch(console.error);
