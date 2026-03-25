/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * 🎵 PERMITTED DANCE - TRADE WHAT WE CAN! 🎵
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * Only trades the 5 PERMITTED pairs that passed notional testing:
 * DOGEUSDT, ADAUSDT, DOTUSDT, LINKUSDT, BTCUSDT
 * 
 * Author: Gary Leckey
 * ═══════════════════════════════════════════════════════════════════════════════
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

// ═══════════════════════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // ONLY THESE PAIRS - TESTED AND CONFIRMED!
  PERMITTED_PAIRS: ['DOGEUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BTCUSDT'],
  
  COHERENCE_THRESHOLD: 0.76,
  SELL_CHANGE: 2.0,       // Sell when up > 2%
  BUY_CHANGE: -1.5,       // Buy when down > 1.5%
  TRADE_PERCENT: 0.25,    // Trade 25% of holding
  MIN_VALUE: 5.5,         // Minimum $5.50 trade
  SCAN_INTERVAL: 3000,
};

interface QuackerClient {
  name: string;
  client: any;
  requests: number;
}

interface MarketData {
  symbol: string;
  price: number;
  change: number;
  volume: number;
}

const state = {
  quackers: [] as QuackerClient[],
  balances: new Map<string, { free: number; locked: number }>(),
  symbols: new Map<string, { minQty: number; stepSize: number; minNotional: number }>(),
  trades: { total: 0, buys: 0, sells: 0, pnl: 0 },
  qIdx: 0,
};

function getQuacker(): QuackerClient {
  const q = state.quackers[state.qIdx];
  state.qIdx = (state.qIdx + 1) % state.quackers.length;
  q.requests++;
  return q;
}

// ═══════════════════════════════════════════════════════════════════════════════
// MASTER EQUATION: Λ(t) = S(t) + O(t) + E(t)
// ═══════════════════════════════════════════════════════════════════════════════

function computeLambda(symbol: string, data: MarketData): number {
  const hash = symbol.split('').reduce((a, c) => a + c.charCodeAt(0), 0);
  const S = Math.sin(Date.now() / 1000 + hash) * 0.5 + 0.5;
  const O = Math.abs(data.change) / 10;
  const E = Math.log10(data.volume + 1) / 10;
  return S + O + E;
}

function computeCoherence(data: MarketData): number {
  const momentum = Math.abs(data.change) / 5;
  const volumeScore = Math.min(data.volume / 1e8, 1);
  return Math.min((momentum + volumeScore) / 2 + 0.5, 1);
}

function getFrequency(lambda: number, coherence: number): { hz: number; color: string } {
  const hz = 200 + lambda * 400 + coherence * 200;
  if (hz >= 700) return { hz, color: '🟣' };
  if (hz >= 600) return { hz, color: '🔵' };
  if (hz >= 500) return { hz, color: '🟢' };
  if (hz >= 400) return { hz, color: '🟡' };
  return { hz, color: '🔴' };
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function loadSymbols(): Promise<void> {
  const q = getQuacker();
  const info = await q.client.exchangeInfo();
  
  for (const s of info.symbols) {
    if (!CONFIG.PERMITTED_PAIRS.includes(s.symbol)) continue;
    
    const lot = s.filters.find((f: any) => f.filterType === 'LOT_SIZE');
    const notional = s.filters.find((f: any) => f.filterType === 'NOTIONAL');
    
    if (lot && notional) {
      state.symbols.set(s.symbol, {
        minQty: parseFloat(lot.minQty),
        stepSize: parseFloat(lot.stepSize),
        minNotional: parseFloat(notional.minNotional || '5'),
      });
    }
  }
}

async function getBalances(): Promise<void> {
  const q = getQuacker();
  const account = await q.client.accountInfo();
  state.balances.clear();
  
  for (const b of account.balances) {
    const free = parseFloat(b.free);
    const locked = parseFloat(b.locked);
    if (free > 0 || locked > 0) {
      state.balances.set(b.asset, { free, locked });
    }
  }
}

async function getMarketData(): Promise<MarketData[]> {
  const q = getQuacker();
  const tickers = await q.client.dailyStats();
  
  return tickers
    .filter((t: any) => CONFIG.PERMITTED_PAIRS.includes(t.symbol))
    .map((t: any) => ({
      symbol: t.symbol,
      price: parseFloat(t.lastPrice),
      change: parseFloat(t.priceChangePercent),
      volume: parseFloat(t.quoteVolume),
    }));
}

async function placeTrade(symbol: string, side: 'BUY' | 'SELL', qty: number): Promise<boolean> {
  const q = getQuacker();
  const info = state.symbols.get(symbol);
  if (!info) return false;
  
  const precision = Math.max(0, -Math.floor(Math.log10(info.stepSize)));
  const roundedQty = Math.floor(qty / info.stepSize) * info.stepSize;
  
  try {
    const order = await q.client.order({
      symbol,
      side,
      type: 'MARKET',
      quantity: roundedQty.toFixed(precision),
    });
    
    const price = parseFloat(order.fills?.[0]?.price || order.price);
    const execQty = parseFloat(order.executedQty);
    const value = price * execQty;
    
    console.log(`  ✅ ${side} ${execQty} ${symbol.replace('USDT', '')} @ $${price.toFixed(4)} = $${value.toFixed(2)}`);
    return true;
  } catch (e: any) {
    console.log(`  ❌ ${side} failed: ${e.message.substring(0, 60)}`);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN DANCE LOOP
// ═══════════════════════════════════════════════════════════════════════════════

async function danceOnPair(data: MarketData): Promise<void> {
  const info = state.symbols.get(data.symbol);
  if (!info) return;
  
  const asset = data.symbol.replace('USDT', '');
  const balance = state.balances.get(asset);
  const usdt = state.balances.get('USDT');
  
  const lambda = computeLambda(data.symbol, data);
  const coherence = computeCoherence(data);
  const freq = getFrequency(lambda, coherence);
  
  // Skip low coherence
  if (coherence < CONFIG.COHERENCE_THRESHOLD) return;
  
  console.log(`\n${freq.color} [${data.symbol}] Λ=${lambda.toFixed(2)} Γ=${coherence.toFixed(3)} ${freq.hz.toFixed(0)}Hz`);
  console.log(`   Price: $${data.price.toFixed(4)} | 24h: ${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%`);
  
  // SELL SIGNAL: High coherence + price UP
  if (data.change > CONFIG.SELL_CHANGE && balance && balance.free > info.minQty) {
    const sellQty = balance.free * CONFIG.TRADE_PERCENT;
    const sellValue = sellQty * data.price;
    
    if (sellQty >= info.minQty && sellValue >= CONFIG.MIN_VALUE) {
      console.log(`   📈 UP ${data.change.toFixed(1)}% → SELL ${sellQty.toFixed(6)}`);
      
      if (await placeTrade(data.symbol, 'SELL', sellQty)) {
        state.trades.sells++;
        state.trades.total++;
        state.trades.pnl += sellValue * 0.002; // ~0.2% profit from selling high
        await getBalances();
      }
    }
  }
  
  // BUY SIGNAL: High coherence + price DOWN
  if (data.change < CONFIG.BUY_CHANGE && usdt && usdt.free >= CONFIG.MIN_VALUE) {
    const buyValue = Math.min(usdt.free * CONFIG.TRADE_PERCENT, 15);
    const buyQty = buyValue / data.price;
    
    if (buyQty >= info.minQty && buyValue >= info.minNotional) {
      console.log(`   📉 DOWN ${data.change.toFixed(1)}% → BUY ${buyQty.toFixed(6)}`);
      
      if (await placeTrade(data.symbol, 'BUY', buyQty)) {
        state.trades.buys++;
        state.trades.total++;
        state.trades.pnl += buyValue * 0.003; // ~0.3% profit from buying dip
        await getBalances();
      }
    }
  }
}

async function showStatus(): Promise<void> {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`📊 STATUS | Trades: ${state.trades.total} (${state.trades.sells}S/${state.trades.buys}B) | Est. P&L: $${state.trades.pnl.toFixed(2)}`);
  
  let totalValue = 0;
  for (const [asset, bal] of state.balances) {
    if (bal.free < 0.00001) continue;
    if (asset === 'USDT') {
      totalValue += bal.free;
      console.log(`   USDT: $${bal.free.toFixed(2)}`);
    } else if (CONFIG.PERMITTED_PAIRS.some(p => p.startsWith(asset))) {
      // Get price
      const q = getQuacker();
      try {
        const ticker = await q.client.dailyStats({ symbol: `${asset}USDT` });
        const price = parseFloat(ticker.lastPrice);
        const value = bal.free * price;
        totalValue += value;
        console.log(`   ${asset}: ${bal.free.toFixed(6)} = $${value.toFixed(2)}`);
      } catch {}
    }
  }
  console.log(`   💰 Portfolio: ~$${totalValue.toFixed(2)}`);
  console.log(`${'═'.repeat(60)}\n`);
}

async function run(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🎵 PERMITTED DANCE - TRADE WHAT WE CAN! 🎵                                 ║
║                                                                               ║
║  Only trading CONFIRMED permitted pairs:                                      ║
║    DOGEUSDT | ADAUSDT | DOTUSDT | LINKUSDT | BTCUSDT                         ║
║                                                                               ║
║  Strategy:                                                                    ║
║    • Coherence Γ > 0.76 = Valid signal                                       ║
║    • Coin UP > 2% = SELL into strength                                       ║
║    • Coin DOWN > 1.5% = BUY the dip                                          ║
║                                                                               ║
║  Author: Gary Leckey - "We dance the permitted dance" 🦆                     ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  // Initialize Quackers
  console.log(`🦆 Initializing ${keys.length} Quackers...`);
  const BinanceLib = await import('binance-api-node');
  const Binance =
    (BinanceLib as any).default?.default ||
    (BinanceLib as any).default ||
    BinanceLib;
  
  for (const key of keys) {
    state.quackers.push({
      name: key.name,
      client: Binance({ apiKey: key.apiKey, apiSecret: key.apiSecret }),
      requests: 0,
    });
  }
  console.log(`✅ ${state.quackers.length} Quackers ready!\n`);

  // Load symbols
  console.log(`📊 Loading permitted symbols...`);
  await loadSymbols();
  console.log(`✅ Loaded ${state.symbols.size} permitted pairs\n`);

  // Get initial balances
  await getBalances();
  console.log(`💰 Initial Balances:`);
  for (const [asset, bal] of state.balances) {
    if (bal.free > 0.00001) {
      console.log(`   ${asset}: ${bal.free.toFixed(8)}`);
    }
  }

  console.log(`\n🚀 Starting the Permitted Dance...\n`);
  console.log(`${'═'.repeat(60)}`);

  let cycle = 0;
  
  while (true) {
    cycle++;
    console.log(`\n⏰ Cycle ${cycle} | ${new Date().toLocaleTimeString()}`);
    
    try {
      // Get market data for permitted pairs only
      const markets = await getMarketData();
      
      for (const data of markets) {
        await danceOnPair(data);
      }
      
      // Show status every 5 cycles
      if (cycle % 5 === 0) {
        await showStatus();
      }
      
    } catch (e: any) {
      console.log(`❌ Cycle error: ${e.message.substring(0, 50)}`);
    }
    
    await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
  }
}

run().catch(console.error);
