/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * 🎵 THE GRAND DANCE OF SPACE AND TIME 🎵
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * EVERY SINGLE COIN ON BINANCE SPOT - The Full Symphony!
 * 
 * 12 Quackers | One Wallet | ALL USDT Pairs | Maximum Harmony
 * 
 * Master Equation: Λ(t) = S(t) + O(t) + E(t)
 * 9 Auris Nodes | Rainbow Bridge | Real Money | ALL COINS
 * 
 * Author: Gary Leckey
 * Date: November 25, 2025
 * 
 * "Four chords, infinite possibilities - across EVERY coin" 🦆
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
// 🦆 QUACKER CLIENTS
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
// 9 AURIS NODES
// ═══════════════════════════════════════════════════════════════════════════════

interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  high: number;
  low: number;
  open: number;
  change: number;
  quoteVolume: number;
}

const aurisNodes = {
  tiger: (d: MarketData) => ((d.high - d.low) / d.price) * 100 + (d.quoteVolume > 1000000 ? 0.2 : 0),
  falcon: (d: MarketData) => Math.abs(d.change) * 0.7 + Math.min(d.quoteVolume / 10000000, 0.3),
  hummingbird: (d: MarketData) => 1 / (1 + ((d.high - d.low) / d.price) * 10),
  dolphin: (d: MarketData) => Math.sin(d.change * Math.PI / 10) * 0.5 + 0.5,
  deer: (d: MarketData) => (d.price > d.open ? 0.6 : 0.4) + (d.change > 0 ? 0.2 : -0.1),
  owl: (d: MarketData) => Math.cos(d.change * Math.PI / 10) * 0.3 + (d.price < d.open ? 0.3 : 0),
  panda: (d: MarketData) => 0.5 + Math.sin(Date.now() / 60000) * 0.1,
  cargoShip: (d: MarketData) => d.quoteVolume > 5000000 ? 0.8 : d.quoteVolume > 1000000 ? 0.5 : 0.3,
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
  let sum = 0, weightSum = 0;
  for (const [name, fn] of Object.entries(aurisNodes)) {
    const weight = nodeWeights[name as keyof typeof nodeWeights];
    sum += fn(data) * weight;
    weightSum += weight;
  }
  return sum / weightSum;
}

function computeLambda(symbol: string, data: MarketData): number {
  if (!lambdaHistory.has(symbol)) lambdaHistory.set(symbol, []);
  const history = lambdaHistory.get(symbol)!;
  
  const S = computeSubstrate(data);
  const O = history.length > 0 ? history[history.length - 1] * OBSERVER_WEIGHT : 0;
  const E = history.length >= ECHO_DEPTH 
    ? history.slice(-ECHO_DEPTH).reduce((a, b) => a + b, 0) / ECHO_DEPTH * ECHO_WEIGHT : 0;
  
  const lambda = S + O + E;
  history.push(lambda);
  if (history.length > 50) history.shift();
  return lambda;
}

function computeCoherence(data: MarketData): number {
  const responses = Object.values(aurisNodes).map(fn => fn(data));
  const mean = responses.reduce((a, b) => a + b, 0) / responses.length;
  const variance = responses.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / responses.length;
  return Math.max(0, Math.min(1, 1 - variance / 10));
}

function getFrequency(lambda: number, coherence: number): { hz: number; color: string; state: string } {
  const baseHz = 110 + lambda * 100;
  const hz = baseHz * (1 - coherence * 0.3) + 528 * (coherence * 0.3);
  
  if (hz < 200) return { hz, color: '🔴', state: 'FEAR' };
  if (hz < 300) return { hz, color: '🟠', state: 'FORMING' };
  if (hz < 400) return { hz, color: '🟡', state: 'FOCUS' };
  if (hz < 528) return { hz, color: '🟢', state: 'FLOW' };
  if (hz < 700) return { hz, color: '💚', state: 'LOVE' };
  if (hz < 850) return { hz, color: '🔵', state: 'AWE' };
  return { hz, color: '🟣', state: 'UNITY' };
}

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIG
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG = {
  ENTRY_THRESHOLD: 0.78,
  EXIT_THRESHOLD: 0.72,
  RISK_PER_TRADE: 0.02,
  STOP_LOSS: 0.008,
  TAKE_PROFIT: 0.018,
  MIN_QUOTE_VOLUME: 100000, // $100k daily volume minimum
  SCAN_INTERVAL: 2000,
  MAX_POSITIONS: 10,
};

// ═══════════════════════════════════════════════════════════════════════════════
// STATE
// ═══════════════════════════════════════════════════════════════════════════════

interface Position {
  symbol: string;
  side: 'LONG' | 'SHORT';
  entryPrice: number;
  quantity: number;
  stopLoss: number;
  takeProfit: number;
  entryTime: Date;
}

interface SymbolInfo {
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  minQty: number;
  stepSize: number;
  minNotional: number;
}

const state = {
  allSymbols: [] as SymbolInfo[],
  usdtPairs: [] as SymbolInfo[],
  positions: new Map<string, Position>(),
  balances: new Map<string, { free: number; locked: number }>(),
  trades: { wins: 0, losses: 0, total: 0 },
  pnl: 0,
  startTime: new Date(),
  cycle: 0,
  scannedThisCycle: 0,
  signalsFound: 0,
};

// ═══════════════════════════════════════════════════════════════════════════════
// QUACKER ROUND-ROBIN
// ═══════════════════════════════════════════════════════════════════════════════

function getNextQuacker(): QuackerClient {
  const quacker = quackers[currentQuacker];
  currentQuacker = (currentQuacker + 1) % quackers.length;
  quacker.requestCount++;
  return quacker;
}

// ═══════════════════════════════════════════════════════════════════════════════
// BINANCE FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function loadAllSymbols(): Promise<void> {
  const quacker = getNextQuacker();
  const info = await quacker.client.exchangeInfo();
  
  state.allSymbols = info.symbols
    .filter((s: any) => s.status === 'TRADING' && s.isSpotTradingAllowed)
    .map((s: any) => {
      const lotSize = s.filters.find((f: any) => f.filterType === 'LOT_SIZE');
      const notional = s.filters.find((f: any) => f.filterType === 'NOTIONAL' || f.filterType === 'MIN_NOTIONAL');
      return {
        symbol: s.symbol,
        baseAsset: s.baseAsset,
        quoteAsset: s.quoteAsset,
        minQty: parseFloat(lotSize?.minQty || '0.00001'),
        stepSize: parseFloat(lotSize?.stepSize || '0.00001'),
        minNotional: parseFloat(notional?.minNotional || '10'),
      };
    });
  
  // Filter USDT pairs only
  state.usdtPairs = state.allSymbols.filter(s => s.quoteAsset === 'USDT');
  
  console.log(`📊 Loaded ${state.allSymbols.length} total symbols`);
  console.log(`💵 Found ${state.usdtPairs.length} USDT trading pairs`);
}

async function getBalances(): Promise<void> {
  const quacker = getNextQuacker();
  const account = await quacker.client.accountInfo();
  
  state.balances.clear();
  for (const b of account.balances) {
    const free = parseFloat(b.free);
    const locked = parseFloat(b.locked);
    if (free > 0 || locked > 0) {
      state.balances.set(b.asset, { free, locked });
    }
  }
}

async function getAllTickers(): Promise<Map<string, MarketData>> {
  const quacker = getNextQuacker();
  const tickers = await quacker.client.dailyStats();
  
  const dataMap = new Map<string, MarketData>();
  for (const t of tickers) {
    if (t.symbol.endsWith('USDT')) {
      dataMap.set(t.symbol, {
        symbol: t.symbol,
        price: parseFloat(t.lastPrice),
        volume: parseFloat(t.volume),
        high: parseFloat(t.highPrice),
        low: parseFloat(t.lowPrice),
        open: parseFloat(t.openPrice),
        change: parseFloat(t.priceChangePercent),
        quoteVolume: parseFloat(t.quoteVolume),
      });
    }
  }
  return dataMap;
}

async function placeTrade(symbol: string, side: 'BUY' | 'SELL', quantity: number, stepSize: number): Promise<{ success: boolean; price?: number; qty?: number }> {
  const quacker = getNextQuacker();
  const precision = Math.max(0, -Math.floor(Math.log10(stepSize)));
  const roundedQty = Math.floor(quantity / stepSize) * stepSize;
  
  try {
    const order = await quacker.client.order({
      symbol, side, type: 'MARKET',
      quantity: roundedQty.toFixed(precision),
    });
    return { 
      success: true, 
      price: parseFloat(order.fills?.[0]?.price || order.price),
      qty: parseFloat(order.executedQty)
    };
  } catch (error: any) {
    return { success: false };
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

async function processSymbol(symbolInfo: SymbolInfo, data: MarketData): Promise<void> {
  // Skip low volume
  if (data.quoteVolume < CONFIG.MIN_QUOTE_VOLUME) return;
  
  const lambda = computeLambda(data.symbol, data);
  const coherence = computeCoherence(data);
  const freq = getFrequency(lambda, coherence);
  
  // Check existing position for exit
  const position = state.positions.get(data.symbol);
  if (position) {
    let exitReason = '';
    let isWin = false;
    
    if (position.side === 'LONG' && data.price <= position.stopLoss) exitReason = '🛑 SL';
    else if (position.side === 'SHORT' && data.price >= position.stopLoss) exitReason = '🛑 SL';
    else if (position.side === 'LONG' && data.price >= position.takeProfit) { exitReason = '🎯 TP'; isWin = true; }
    else if (position.side === 'SHORT' && data.price <= position.takeProfit) { exitReason = '🎯 TP'; isWin = true; }
    else if (coherence < CONFIG.EXIT_THRESHOLD) {
      exitReason = '📉 Γ↓';
      isWin = (position.side === 'LONG' && data.price > position.entryPrice) ||
              (position.side === 'SHORT' && data.price < position.entryPrice);
    }
    
    if (exitReason) {
      const pnlPct = position.side === 'LONG'
        ? (data.price - position.entryPrice) / position.entryPrice * 100
        : (position.entryPrice - data.price) / position.entryPrice * 100;
      
      const side = position.side === 'LONG' ? 'SELL' : 'BUY';
      const result = await placeTrade(data.symbol, side, position.quantity, symbolInfo.stepSize);
      
      if (result.success) {
        console.log(`${exitReason} ${data.symbol} ${pnlPct >= 0 ? '✅' : '❌'} ${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`);
        state.positions.delete(data.symbol);
        state.pnl += position.quantity * position.entryPrice * (pnlPct / 100);
        if (isWin || pnlPct > 0) state.trades.wins++;
        else state.trades.losses++;
      }
    }
    return;
  }
  
  // Check for entry
  if (state.positions.size >= CONFIG.MAX_POSITIONS) return;
  if (coherence < CONFIG.ENTRY_THRESHOLD) return;
  
  state.signalsFound++;
  const direction = data.change > 0 ? 'LONG' : 'SHORT';
  const usdt = state.balances.get('USDT');
  const baseBalance = state.balances.get(symbolInfo.baseAsset);
  
  let quantity = 0;
  let side: 'BUY' | 'SELL' = 'BUY';
  
  if (direction === 'LONG' && usdt && usdt.free > 15) {
    const tradeAmount = Math.min(usdt.free * CONFIG.RISK_PER_TRADE, 20);
    quantity = tradeAmount / data.price;
    side = 'BUY';
  } else if (direction === 'SHORT' && baseBalance && baseBalance.free * data.price > 10) {
    quantity = baseBalance.free * CONFIG.RISK_PER_TRADE;
    side = 'SELL';
  } else {
    return;
  }
  
  if (quantity < symbolInfo.minQty) return;
  if (quantity * data.price < symbolInfo.minNotional) return;
  
  console.log(`\n${freq.color} [${data.symbol}] Λ=${lambda.toFixed(2)} Γ=${coherence.toFixed(3)} ${freq.hz.toFixed(0)}Hz ${freq.state}`);
  console.log(`  🎯 ${direction} @ $${data.price.toFixed(6)}`);
  
  const result = await placeTrade(data.symbol, side, quantity, symbolInfo.stepSize);
  
  if (result.success && result.price && result.qty) {
    const sl = direction === 'LONG' ? result.price * (1 - CONFIG.STOP_LOSS) : result.price * (1 + CONFIG.STOP_LOSS);
    const tp = direction === 'LONG' ? result.price * (1 + CONFIG.TAKE_PROFIT) : result.price * (1 - CONFIG.TAKE_PROFIT);
    
    state.positions.set(data.symbol, {
      symbol: data.symbol,
      side: direction,
      entryPrice: result.price,
      quantity: result.qty,
      stopLoss: sl,
      takeProfit: tp,
      entryTime: new Date(),
    });
    
    state.trades.total++;
    console.log(`  ✅ FILLED: ${result.qty} @ $${result.price.toFixed(6)}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISPLAY
// ═══════════════════════════════════════════════════════════════════════════════

function displayStatus(): void {
  const elapsed = (Date.now() - state.startTime.getTime()) / 1000 / 60;
  const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
  
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🎵 THE GRAND DANCE - ALL ${state.usdtPairs.length} USDT PAIRS - ${new Date().toLocaleTimeString()}             ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  ⏱️  ${elapsed.toFixed(1)}min | 🦆 ${quackers.length} Quackers | 📊 Cycle ${state.cycle}                      ║
║  🔍 Scanned: ${state.scannedThisCycle} | ⚡ Signals: ${state.signalsFound} | 📍 Positions: ${state.positions.size}/${CONFIG.MAX_POSITIONS}        ║
║  💰 Trades: ${state.trades.total} (W:${state.trades.wins} L:${state.trades.losses}) | 🎯 ${winRate.toFixed(1)}% | 📈 $${state.pnl.toFixed(4)}     ║
╚═══════════════════════════════════════════════════════════════════════════════╝`);

  if (state.positions.size > 0) {
    console.log(`  📍 Open: ${Array.from(state.positions.keys()).join(', ')}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function runTheGrandDance(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🎵 THE GRAND DANCE OF SPACE AND TIME 🎵                                    ║
║                                                                               ║
║   ██████╗ ██████╗  █████╗ ███╗   ██╗██████╗                                  ║
║  ██╔════╝ ██╔══██╗██╔══██╗████╗  ██║██╔══██╗                                 ║
║  ██║  ███╗██████╔╝███████║██╔██╗ ██║██║  ██║                                 ║
║  ██║   ██║██╔══██╗██╔══██║██║╚██╗██║██║  ██║                                 ║
║  ╚██████╔╝██║  ██║██║  ██║██║ ╚████║██████╔╝                                 ║
║   ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═════╝                                  ║
║                                                                               ║
║  🔴 LIVE - EVERY SINGLE COIN ON BINANCE SPOT 🔴                              ║
║                                                                               ║
║  12 Quackers | One Wallet | ALL USDT Pairs | Maximum Harmony                 ║
║  Master Equation: Λ(t) = S(t) + O(t) + E(t)                                  ║
║                                                                               ║
║  Author: Gary Leckey                                                          ║
║  "We dance on EVERY single coin" 🦆                                          ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  // Initialize quackers
  console.log(`\n🦆 Initializing ${keys.length} Quackers...`);
  const BinanceLib = await import('binance-api-node');
  for (const key of keys) {
    quackers.push({
      name: key.name,
      client: (BinanceLib as any).default({ apiKey: key.apiKey, apiSecret: key.apiSecret }),
      lastUsed: 0,
      requestCount: 0,
    });
  }
  console.log(`✅ ${quackers.length} Quackers ready!\n`);

  // Load all symbols
  console.log(`📊 Loading all Binance spot symbols...`);
  await loadAllSymbols();
  
  // Get balances
  await getBalances();
  console.log(`\n💰 Wallet:`);
  state.balances.forEach((b, asset) => {
    if (b.free > 0.0001 || asset === 'USDT') {
      console.log(`   ${asset}: ${b.free.toFixed(8)}`);
    }
  });

  console.log(`\n🚀 Starting the Grand Dance across ${state.usdtPairs.length} pairs...\n`);
  console.log(`${'═'.repeat(70)}`);

  // Build symbol lookup
  const symbolLookup = new Map<string, SymbolInfo>();
  state.usdtPairs.forEach(s => symbolLookup.set(s.symbol, s));

  // Main loop
  while (true) {
    state.cycle++;
    state.scannedThisCycle = 0;
    state.signalsFound = 0;
    
    try {
      // Refresh balances every 20 cycles
      if (state.cycle % 20 === 0) await getBalances();
      
      // Get all tickers in ONE call (efficient!)
      const allData = await getAllTickers();
      
      // Process each symbol
      for (const [symbol, data] of allData) {
        const info = symbolLookup.get(symbol);
        if (!info) continue;
        
        state.scannedThisCycle++;
        await processSymbol(info, data);
      }
      
      // Display every 5 cycles
      if (state.cycle % 5 === 0) displayStatus();
      
    } catch (error: any) {
      console.log(`⚠️ ${error.message}`);
    }
    
    await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
  }
}

// 🎵 START THE GRAND DANCE! 🎵
runTheGrandDance().catch(console.error);
