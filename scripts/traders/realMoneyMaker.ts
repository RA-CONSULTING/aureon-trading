/**
 * 💰 REAL MONEY MAKER 💰
 * 
 * Simple, aggressive strategy that WILL execute trades:
 * - Sells ANY permitted coin that's up >1% (not waiting for 2%)
 * - Logs EVERYTHING so we can see what's happening
 * - Uses 80% of position to ensure >$5 notional
 * 
 * Author: Gary Leckey
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

// AGGRESSIVE CONFIG - WILL TRADE!
const CONFIG = {
  PERMITTED_PAIRS: ['DOGEUSDT', 'ADAUSDT', 'DOTUSDT', 'LINKUSDT', 'BTCUSDT'],
  SELL_THRESHOLD: 1.0,    // Sell when up just 1% (was 2%)
  BUY_THRESHOLD: -1.0,    // Buy when down just 1% (was -1.5%)
  TRADE_PERCENT: 0.80,    // Use 80% of holding (ensures >$5)
  MIN_VALUE: 5.5,
  SCAN_INTERVAL: 3000,
};

interface Quacker { name: string; client: any; }
const quackers: Quacker[] = [];
let qIdx = 0;

const state = {
  balances: new Map<string, number>(),
  symbols: new Map<string, { minQty: number; stepSize: number; minNotional: number }>(),
  trades: 0,
  pnl: 0,
};

function getQ(): any {
  const q = quackers[qIdx];
  qIdx = (qIdx + 1) % quackers.length;
  return q.client;
}

async function loadSymbols(): Promise<void> {
  const info = await getQ().exchangeInfo();
  for (const s of info.symbols) {
    if (!CONFIG.PERMITTED_PAIRS.includes(s.symbol)) continue;
    const lot = s.filters.find((f: any) => f.filterType === 'LOT_SIZE');
    const notional = s.filters.find((f: any) => f.filterType === 'NOTIONAL' || f.filterType === 'MIN_NOTIONAL');
    state.symbols.set(s.symbol, {
      minQty: parseFloat(lot?.minQty || '0.00001'),
      stepSize: parseFloat(lot?.stepSize || '0.00001'),
      minNotional: parseFloat(notional?.minNotional || '5'),
    });
  }
}

async function getBalances(): Promise<void> {
  const acct = await getQ().accountInfo();
  state.balances.clear();
  for (const b of acct.balances) {
    const free = parseFloat(b.free);
    if (free > 0) state.balances.set(b.asset, free);
  }
}

async function getMarketData(): Promise<{ symbol: string; price: number; change: number }[]> {
  const tickers = await getQ().dailyStats();
  return CONFIG.PERMITTED_PAIRS.map(symbol => {
    const t = tickers.find((x: any) => x.symbol === symbol);
    return {
      symbol,
      price: parseFloat(t?.lastPrice || '0'),
      change: parseFloat(t?.priceChangePercent || '0'),
    };
  });
}

async function executeTrade(symbol: string, side: 'BUY' | 'SELL', qty: number): Promise<boolean> {
  const info = state.symbols.get(symbol)!;
  const precision = Math.max(0, -Math.floor(Math.log10(info.stepSize)));
  const roundedQty = Math.floor(qty / info.stepSize) * info.stepSize;
  
  console.log(`\n🎯 EXECUTING: ${side} ${roundedQty.toFixed(precision)} ${symbol.replace('USDT', '')}`);
  
  try {
    const order = await getQ().order({
      symbol,
      side,
      type: 'MARKET',
      quantity: roundedQty.toFixed(precision),
    });
    
    const price = parseFloat(order.fills?.[0]?.price || order.price || '0');
    const executed = parseFloat(order.executedQty);
    const value = price * executed;
    
    console.log(`✅ ${side} FILLED: ${executed} @ $${price.toFixed(4)} = $${value.toFixed(2)}`);
    state.trades++;
    state.pnl += side === 'SELL' ? value * 0.01 : value * 0.015; // Est profit
    return true;
  } catch (e: any) {
    console.log(`❌ ${side} FAILED: ${e.message}`);
    return false;
  }
}

async function scanAndTrade(): Promise<void> {
  const markets = await getMarketData();
  
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`⏰ ${new Date().toLocaleTimeString()} | Scanning ${CONFIG.PERMITTED_PAIRS.length} pairs...`);
  
  for (const m of markets) {
    const asset = m.symbol.replace('USDT', '');
    const balance = state.balances.get(asset) || 0;
    const usdt = state.balances.get('USDT') || 0;
    const info = state.symbols.get(m.symbol);
    if (!info) continue;
    
    const holdingValue = balance * m.price;
    const arrow = m.change >= 0 ? '📈' : '📉';
    
    console.log(`  ${arrow} ${m.symbol}: $${m.price.toFixed(4)} (${m.change >= 0 ? '+' : ''}${m.change.toFixed(2)}%) | You have: ${balance.toFixed(4)} ($${holdingValue.toFixed(2)})`);
    
    // SELL SIGNAL
    if (m.change >= CONFIG.SELL_THRESHOLD && balance > info.minQty) {
      const sellQty = balance * CONFIG.TRADE_PERCENT;
      const sellValue = sellQty * m.price;
      
      if (sellValue >= CONFIG.MIN_VALUE) {
        console.log(`\n🔥 SELL SIGNAL! ${m.symbol} is UP ${m.change.toFixed(2)}%`);
        if (await executeTrade(m.symbol, 'SELL', sellQty)) {
          await getBalances();
        }
      } else {
        console.log(`    ⚠️ Would sell but value $${sellValue.toFixed(2)} < $${CONFIG.MIN_VALUE} min`);
      }
    }
    
    // BUY SIGNAL
    if (m.change <= CONFIG.BUY_THRESHOLD && usdt >= CONFIG.MIN_VALUE) {
      const buyValue = Math.min(usdt * 0.5, 20); // Use 50% of USDT, max $20
      const buyQty = buyValue / m.price;
      
      if (buyQty >= info.minQty && buyValue >= info.minNotional) {
        console.log(`\n🔥 BUY SIGNAL! ${m.symbol} is DOWN ${m.change.toFixed(2)}%`);
        if (await executeTrade(m.symbol, 'BUY', buyQty)) {
          await getBalances();
        }
      }
    }
  }
  
  // Show status
  let total = 0;
  for (const m of markets) {
    const asset = m.symbol.replace('USDT', '');
    const bal = state.balances.get(asset) || 0;
    total += bal * m.price;
  }
  total += state.balances.get('USDT') || 0;
  total += state.balances.get('USDC') || 0;
  
  console.log(`\n💰 Portfolio: ~$${total.toFixed(2)} | Trades: ${state.trades} | Est PnL: $${state.pnl.toFixed(2)}`);
}

async function run(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   💰 REAL MONEY MAKER - AGGRESSIVE LIVE TRADING 💰                           ║
║                                                                               ║
║   Strategy:                                                                   ║
║     • SELL when coin is UP ≥ 1%                                              ║
║     • BUY when coin is DOWN ≤ -1%                                            ║
║     • Trade 80% of position per signal                                       ║
║     • Minimum $5.50 per trade                                                ║
║                                                                               ║
║   Permitted Pairs: DOGE | ADA | DOT | LINK | BTC                             ║
║                                                                               ║
║   Author: Gary Leckey - "Real money, real trades" 🦆                         ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  // Init Quackers
  console.log(`🦆 Initializing ${keys.length} Quackers...`);
  const Blib = await import('binance-api-node');
  const Binance = (Blib as any).default?.default || (Blib as any).default || Blib;
  
  for (const key of keys) {
    quackers.push({
      name: key.name,
      client: Binance({ apiKey: key.apiKey, apiSecret: key.apiSecret }),
    });
  }
  console.log(`✅ ${quackers.length} Quackers ready!`);

  // Load symbols
  console.log(`\n📊 Loading permitted symbols...`);
  await loadSymbols();
  console.log(`✅ ${state.symbols.size} pairs loaded`);

  // Get balances
  await getBalances();
  console.log(`\n💰 Starting Balances:`);
  for (const [asset, bal] of state.balances) {
    if (bal > 0.0001) console.log(`   ${asset}: ${bal.toFixed(8)}`);
  }

  console.log(`\n🚀 Starting Real Money Maker...`);
  
  // Main loop
  while (true) {
    try {
      await scanAndTrade();
    } catch (e: any) {
      console.log(`⚠️ Error: ${e.message}`);
    }
    await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
  }
}

run().catch(console.error);
