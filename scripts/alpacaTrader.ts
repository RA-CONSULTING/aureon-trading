/**
 * 🦙 ALPACA FULL TRADER 🦙
 * 
 * Trade ALL US stocks on Alpaca - Commission-free!
 * Dynamically loads tradeable symbols | Full market coverage
 * 
 * Strategy: Mean Reversion + Momentum
 * - BUY when down > 1.5% (oversold)
 * - SELL when up > 1.5% (overbought)
 * - Uses coherence from 9 Auris nodes
 * 
 * Author: Gary Leckey
 */

import * as dotenv from 'dotenv';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

const CONFIG = {
  API_KEY: process.env.ALPACA_API_KEY || '',
  API_SECRET: process.env.ALPACA_SECRET || '',
  PAPER: process.env.ALPACA_PAPER !== 'false',
  
  // API endpoints
  get BASE_URL() {
    return this.PAPER 
      ? 'https://paper-api.alpaca.markets'
      : 'https://api.alpaca.markets';
  },
  DATA_URL: 'https://data.alpaca.markets',
  
  // Trading settings
  COHERENCE_THRESHOLD: 0.76,
  RISK_PERCENT: 2,
  ENTRY_THRESHOLD: 1.5,
  TAKE_PROFIT: 2.0,
  STOP_LOSS: 1.0,
  MIN_VOLUME: 500000,      // Min daily volume
  MIN_PRICE: 5,            // Min stock price
  MAX_PRICE: 500,          // Max stock price
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 10,
};

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface Asset {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  tradable: boolean;
  fractionable: boolean;
  minOrderSize: number;
  minTradeIncrement: number;
}

interface Position {
  symbol: string;
  side: 'long' | 'short';
  qty: number;
  avgPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  entryTime: Date;
}

interface Quote {
  symbol: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
  bid: number;
  ask: number;
}

interface Account {
  id: string;
  cash: number;
  buyingPower: number;
  portfolioValue: number;
  equity: number;
  status: string;
}

const state = {
  allAssets: new Map<string, Asset>(),
  tradableAssets: [] as Asset[],
  positions: new Map<string, Position>(),
  account: null as Account | null,
  trades: { total: 0, wins: 0, losses: 0 },
  pnl: 0,
  cycle: 0,
  startTime: new Date(),
  marketOpen: false,
};

// ═══════════════════════════════════════════════════════════════════════════════
// 9 AURIS NODES
// ═══════════════════════════════════════════════════════════════════════════════

const aurisNodes = {
  tiger: (d: Quote) => ((d.high - d.low) / d.price) * 100 + (d.volume > 1000000 ? 0.2 : 0),
  falcon: (d: Quote) => Math.abs(d.change) * 0.7 + Math.min(d.volume / 10000000, 0.3),
  hummingbird: (d: Quote) => 1 / (1 + ((d.high - d.low) / d.price) * 10),
  dolphin: (d: Quote) => Math.sin(d.change * Math.PI / 10) * 0.5 + 0.5,
  deer: (d: Quote) => (d.price > d.open ? 0.6 : 0.4) + (d.change > 0 ? 0.2 : -0.1),
  owl: (d: Quote) => Math.cos(d.change * Math.PI / 10) * 0.3 + (d.price < d.open ? 0.3 : 0),
  panda: (d: Quote) => 0.5 + Math.sin(Date.now() / 60000) * 0.1,
  cargoShip: (d: Quote) => d.volume > 5000000 ? 0.8 : d.volume > 1000000 ? 0.5 : 0.3,
  clownfish: (d: Quote) => Math.abs(d.price - d.open) / d.price * 100,
};

const nodeWeights = {
  tiger: 1.2, falcon: 1.1, hummingbird: 0.9, dolphin: 1.0,
  deer: 0.8, owl: 0.9, panda: 0.7, cargoShip: 1.0, clownfish: 0.7
};

const lambdaHistory: Map<string, number[]> = new Map();

function computeLambda(symbol: string, data: Quote): number {
  if (!lambdaHistory.has(symbol)) lambdaHistory.set(symbol, []);
  const history = lambdaHistory.get(symbol)!;
  
  let sum = 0, weightSum = 0;
  for (const [name, fn] of Object.entries(aurisNodes)) {
    sum += fn(data) * nodeWeights[name as keyof typeof nodeWeights];
    weightSum += nodeWeights[name as keyof typeof nodeWeights];
  }
  const S = sum / weightSum;
  const O = history.length > 0 ? history[history.length - 1] * 0.3 : 0;
  const E = history.length >= 5 ? history.slice(-5).reduce((a, b) => a + b, 0) / 5 * 0.2 : 0;
  
  const lambda = S + O + E;
  history.push(lambda);
  if (history.length > 50) history.shift();
  return lambda;
}

function computeCoherence(data: Quote): number {
  const responses = Object.values(aurisNodes).map(fn => fn(data));
  const mean = responses.reduce((a, b) => a + b, 0) / responses.length;
  const variance = responses.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / responses.length;
  return Math.max(0, Math.min(1, 1 - variance / 10));
}

function getFrequency(lambda: number, coherence: number): { hz: number; color: string; state: string } {
  const hz = (110 + lambda * 100) * (1 - coherence * 0.3) + 528 * (coherence * 0.3);
  if (hz < 200) return { hz, color: '🔴', state: 'FEAR' };
  if (hz < 300) return { hz, color: '🟠', state: 'FORMING' };
  if (hz < 400) return { hz, color: '🟡', state: 'FOCUS' };
  if (hz < 528) return { hz, color: '🟢', state: 'FLOW' };
  if (hz < 700) return { hz, color: '💚', state: 'LOVE' };
  if (hz < 850) return { hz, color: '🔵', state: 'AWE' };
  return { hz, color: '🟣', state: 'UNITY' };
}

// ═══════════════════════════════════════════════════════════════════════════════
// ALPACA API
// ═══════════════════════════════════════════════════════════════════════════════

async function alpacaRequest(endpoint: string, method = 'GET', body?: any, isData = false): Promise<any> {
  const baseUrl = isData ? CONFIG.DATA_URL : CONFIG.BASE_URL;
  const url = `${baseUrl}${endpoint}`;
  
  const response = await fetch(url, {
    method,
    headers: {
      'APCA-API-KEY-ID': CONFIG.API_KEY,
      'APCA-API-SECRET-KEY': CONFIG.API_SECRET,
      'Content-Type': 'application/json',
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Alpaca API error: ${response.status} - ${error}`);
  }
  
  return response.json();
}

// ═══════════════════════════════════════════════════════════════════════════════
// LOAD ALL ASSETS
// ═══════════════════════════════════════════════════════════════════════════════

async function loadAllAssets(): Promise<void> {
  console.log('📊 Loading all Alpaca assets...');
  
  const assets = await alpacaRequest('/v2/assets?status=active&asset_class=us_equity');
  
  state.allAssets.clear();
  state.tradableAssets = [];
  
  for (const asset of assets) {
    if (!asset.tradable) continue;
    if (asset.status !== 'active') continue;
    
    const assetInfo: Asset = {
      id: asset.id,
      symbol: asset.symbol,
      name: asset.name,
      exchange: asset.exchange,
      tradable: asset.tradable,
      fractionable: asset.fractionable,
      minOrderSize: asset.min_order_size ? parseFloat(asset.min_order_size) : 1,
      minTradeIncrement: asset.min_trade_increment ? parseFloat(asset.min_trade_increment) : 0.01,
    };
    
    state.allAssets.set(asset.symbol, assetInfo);
    state.tradableAssets.push(assetInfo);
  }
  
  console.log(`✅ Loaded ${state.tradableAssets.length} tradeable stocks`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// GET MARKET DATA
// ═══════════════════════════════════════════════════════════════════════════════

async function getQuotes(symbols: string[]): Promise<Map<string, Quote>> {
  const result = new Map<string, Quote>();
  
  // Alpaca allows up to 100 symbols per request
  const chunks = [];
  for (let i = 0; i < symbols.length; i += 100) {
    chunks.push(symbols.slice(i, i + 100));
  }
  
  for (const chunk of chunks) {
    try {
      const symbolList = chunk.join(',');
      
      // Get latest quotes
      const quotes = await alpacaRequest(`/v2/stocks/quotes/latest?symbols=${symbolList}`, 'GET', undefined, true);
      
      // Get bars for OHLC data
      const bars = await alpacaRequest(`/v2/stocks/bars/latest?symbols=${symbolList}`, 'GET', undefined, true);
      
      for (const symbol of chunk) {
        const quote = quotes.quotes?.[symbol];
        const bar = bars.bars?.[symbol];
        
        if (!quote || !bar) continue;
        
        const price = (quote.bp + quote.ap) / 2;
        const open = bar.o;
        const change = open > 0 ? ((price - open) / open) * 100 : 0;
        
        result.set(symbol, {
          symbol,
          price,
          open,
          high: bar.h,
          low: bar.l,
          volume: bar.v,
          change,
          bid: quote.bp,
          ask: quote.ap,
        });
      }
    } catch (e: any) {
      // Skip failed chunks
    }
  }
  
  return result;
}

async function getTopMovers(): Promise<string[]> {
  // Get screener results for most active stocks
  try {
    const screener = await alpacaRequest('/v1beta1/screener/stocks/most-actives?by=volume&top=100', 'GET', undefined, true);
    return screener.most_actives?.map((s: any) => s.symbol) || [];
  } catch {
    // Fallback to popular symbols
    return [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AMD', 'NFLX', 'INTC',
      'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'ARKK', 'XLF', 'XLE', 'XLK',
      'COIN', 'MARA', 'RIOT', 'SQ', 'PYPL', 'SHOP', 'ROKU', 'SNAP', 'PINS', 'UBER',
      'NIO', 'RIVN', 'LCID', 'F', 'GM', 'BA', 'AAL', 'UAL', 'DAL', 'CCL',
      'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'V', 'MA', 'AXP', 'DIS',
    ];
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// ACCOUNT & POSITIONS
// ═══════════════════════════════════════════════════════════════════════════════

async function getAccount(): Promise<void> {
  const account = await alpacaRequest('/v2/account');
  state.account = {
    id: account.id,
    cash: parseFloat(account.cash),
    buyingPower: parseFloat(account.buying_power),
    portfolioValue: parseFloat(account.portfolio_value),
    equity: parseFloat(account.equity),
    status: account.status,
  };
}

async function getPositions(): Promise<void> {
  const positions = await alpacaRequest('/v2/positions');
  state.positions.clear();
  
  for (const pos of positions) {
    state.positions.set(pos.symbol, {
      symbol: pos.symbol,
      side: pos.side,
      qty: parseFloat(pos.qty),
      avgPrice: parseFloat(pos.avg_entry_price),
      marketValue: parseFloat(pos.market_value),
      unrealizedPnl: parseFloat(pos.unrealized_pl),
      entryTime: new Date(),
    });
  }
}

async function isMarketOpen(): Promise<boolean> {
  const clock = await alpacaRequest('/v2/clock');
  state.marketOpen = clock.is_open;
  return clock.is_open;
}

async function placeOrder(symbol: string, side: 'buy' | 'sell', qty: number, notional?: number): Promise<string | null> {
  console.log(`\n🎯 ${side.toUpperCase()} ${qty > 0 ? qty : `$${notional}`} ${symbol}`);
  
  try {
    const orderData: any = {
      symbol,
      side,
      type: 'market',
      time_in_force: 'day',
    };
    
    if (notional && notional > 0) {
      orderData.notional = notional.toFixed(2);
    } else {
      orderData.qty = qty.toString();
    }
    
    const result = await alpacaRequest('/v2/orders', 'POST', orderData);
    console.log(`✅ Order submitted! ID: ${result.id}`);
    state.trades.total++;
    return result.id;
  } catch (e: any) {
    console.log(`❌ Order failed: ${e.message}`);
    return null;
  }
}

async function closePosition(symbol: string): Promise<boolean> {
  try {
    await alpacaRequest(`/v2/positions/${symbol}`, 'DELETE');
    console.log(`✅ Closed ${symbol} position`);
    return true;
  } catch (e: any) {
    console.log(`❌ Failed to close ${symbol}: ${e.message}`);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

async function processStock(symbol: string, data: Quote): Promise<void> {
  // Skip if price out of range
  if (data.price < CONFIG.MIN_PRICE || data.price > CONFIG.MAX_PRICE) return;
  if (data.volume < CONFIG.MIN_VOLUME) return;
  
  const lambda = computeLambda(symbol, data);
  const coherence = computeCoherence(data);
  const freq = getFrequency(lambda, coherence);
  
  // Check existing position
  const existingPos = state.positions.get(symbol);
  
  if (existingPos) {
    const pnlPct = (existingPos.unrealizedPnl / (existingPos.avgPrice * existingPos.qty)) * 100;
    
    // Check exit conditions
    if (pnlPct >= CONFIG.TAKE_PROFIT || pnlPct <= -CONFIG.STOP_LOSS) {
      const reason = pnlPct >= CONFIG.TAKE_PROFIT ? '🎯 TP' : '🛑 SL';
      console.log(`\n${reason} ${symbol} ${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`);
      
      if (await closePosition(symbol)) {
        state.pnl += existingPos.unrealizedPnl;
        if (pnlPct > 0) state.trades.wins++;
        else state.trades.losses++;
        await getPositions();
      }
    }
    return;
  }
  
  // Skip if no signal or max positions reached
  if (coherence < CONFIG.COHERENCE_THRESHOLD) return;
  if (state.positions.size >= CONFIG.MAX_POSITIONS) return;
  
  // Determine direction
  let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
  if (data.change <= -CONFIG.ENTRY_THRESHOLD) signal = 'BUY';
  else if (data.change >= CONFIG.ENTRY_THRESHOLD) signal = 'SELL';
  
  if (signal === 'HOLD') return;
  
  // Calculate position size
  const buyingPower = state.account?.buyingPower || 0;
  if (buyingPower < 10) return;
  
  const tradeAmount = Math.min(buyingPower * (CONFIG.RISK_PERCENT / 100), 100);
  
  console.log(`\n${freq.color} [${symbol}] Λ=${lambda.toFixed(2)} Γ=${coherence.toFixed(3)} ${freq.hz.toFixed(0)}Hz`);
  console.log(`   ${signal} @ $${data.price.toFixed(2)} (${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%)`);
  
  if (signal === 'BUY') {
    const orderId = await placeOrder(symbol, 'buy', 0, tradeAmount);
    if (orderId) {
      await getPositions();
      await getAccount();
    }
  }
  // Note: Short selling requires margin account
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISPLAY
// ═══════════════════════════════════════════════════════════════════════════════

function displayStatus(quotes: Map<string, Quote>): void {
  const elapsed = (Date.now() - state.startTime.getTime()) / 1000 / 60;
  const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
  
  // Find top movers from scanned stocks
  const sorted = [...quotes.values()]
    .filter(q => q.volume > CONFIG.MIN_VOLUME && q.price >= CONFIG.MIN_PRICE)
    .sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
    .slice(0, 5);
  
  const mode = CONFIG.PAPER ? '📝 PAPER' : '💵 LIVE';
  
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║  🦙 ALPACA TRADER - ${new Date().toLocaleTimeString()} - US STOCKS ${mode}                  ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║  ⏱️  ${elapsed.toFixed(1)}min | 📊 Assets: ${state.tradableAssets.length} | 🔄 Cycle: ${state.cycle} | Market: ${state.marketOpen ? '🟢 OPEN' : '🔴 CLOSED'}  ║
║  💰 Equity: $${(state.account?.equity || 0).toFixed(2)} | Cash: $${(state.account?.cash || 0).toFixed(2)} | Buying Power: $${(state.account?.buyingPower || 0).toFixed(2)}  ║
║  📍 Positions: ${state.positions.size}/${CONFIG.MAX_POSITIONS} | Trades: ${state.trades.total} (W:${state.trades.wins} L:${state.trades.losses}) | WR: ${winRate.toFixed(0)}%    ║
║  📈 Realized PnL: $${state.pnl.toFixed(2)}                                                  ║
╚═══════════════════════════════════════════════════════════════════════════════╝`);

  // Show top movers
  if (sorted.length > 0) {
    console.log(`  📊 Top Movers:`);
    for (const q of sorted) {
      const arrow = q.change >= 0 ? '📈' : '📉';
      console.log(`     ${arrow} ${q.symbol}: $${q.price.toFixed(2)} (${q.change >= 0 ? '+' : ''}${q.change.toFixed(2)}%) Vol: ${(q.volume/1000000).toFixed(1)}M`);
    }
  }
  
  // Show positions
  if (state.positions.size > 0) {
    console.log(`  📍 Open Positions:`);
    state.positions.forEach((pos) => {
      const pnlPct = (pos.unrealizedPnl / (pos.avgPrice * pos.qty)) * 100;
      console.log(`     ${pos.side.toUpperCase()} ${pos.symbol}: ${pos.qty} @ $${pos.avgPrice.toFixed(2)} | P/L: ${pos.unrealizedPnl >= 0 ? '+' : ''}$${pos.unrealizedPnl.toFixed(2)} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)`);
    });
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN TRADING LOOP
// ═══════════════════════════════════════════════════════════════════════════════

async function tradingCycle(): Promise<void> {
  state.cycle++;
  
  try {
    // Check if market is open
    const marketOpen = await isMarketOpen();
    
    if (!marketOpen) {
      if (state.cycle % 60 === 0) {
        console.log('⏸️  Market closed. Waiting...');
      }
      return;
    }
    
    // Get top movers to scan
    const symbols = await getTopMovers();
    
    // Get quotes for all symbols
    const quotes = await getQuotes(symbols);
    
    // Process each stock
    for (const [symbol, data] of quotes) {
      await processStock(symbol, data);
    }
    
    // Refresh positions and account
    if (state.cycle % 5 === 0) {
      await getPositions();
      await getAccount();
    }
    
    // Display status every 5 cycles
    if (state.cycle % 5 === 0) {
      displayStatus(quotes);
    }
    
  } catch (e: any) {
    console.log(`⚠️ ${e.message}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function run(): Promise<void> {
  const mode = CONFIG.PAPER ? '📝 PAPER TRADING' : '💵 LIVE TRADING';
  
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🦙 ALPACA FULL TRADER - US STOCKS 🦙                                       ║
║                                                                               ║
║    █████╗ ██╗     ██████╗  █████╗  ██████╗ █████╗                            ║
║   ██╔══██╗██║     ██╔══██╗██╔══██╗██╔════╝██╔══██╗                           ║
║   ███████║██║     ██████╔╝███████║██║     ███████║                           ║
║   ██╔══██║██║     ██╔═══╝ ██╔══██║██║     ██╔══██║                           ║
║   ██║  ██║███████╗██║     ██║  ██║╚██████╗██║  ██║                           ║
║   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝                           ║
║                                                                               ║
║   🔴 ${mode} - COMMISSION FREE 🔴                              ║
║                                                                               ║
║   Features:                                                                   ║
║     • Trade ALL US stocks - Commission free!                                 ║
║     • Fractional shares supported                                            ║
║     • 9 Auris Nodes coherence analysis                                       ║
║     • Mean reversion + momentum strategy                                     ║
║     • Automatic position management                                          ║
║                                                                               ║
║   Strategy:                                                                   ║
║     • Coherence Γ > 0.76 = Valid signal                                      ║
║     • BUY when down ≥ 1.5%                                                   ║
║     • SELL when up ≥ 1.5%                                                    ║
║     • Take Profit: 2% | Stop Loss: 1%                                        ║
║                                                                               ║
║   Author: Gary Leckey - "Spit on 'em!" 🦆                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Alpaca API credentials!');
    console.log('');
    console.log('To set up Alpaca:');
    console.log('1. Go to https://app.alpaca.markets/');
    console.log('2. Sign up for a free account');
    console.log('3. Go to API Keys and generate new keys');
    console.log('');
    console.log('4. Add to your .env file:');
    console.log('   ALPACA_API_KEY=your_api_key');
    console.log('   ALPACA_SECRET=your_secret_key');
    console.log('   ALPACA_PAPER=true   # Set to false for live trading');
    console.log('');
    return;
  }
  
  console.log('🔐 Connecting to Alpaca...');
  
  try {
    // Load all assets
    await loadAllAssets();
    
    // Get account info
    await getAccount();
    
    console.log(`\n✅ Connected to Alpaca (${CONFIG.PAPER ? 'Paper' : 'Live'})`);
    console.log(`   Account Status: ${state.account?.status}`);
    console.log(`   Equity: $${state.account?.equity.toFixed(2)}`);
    console.log(`   Cash: $${state.account?.cash.toFixed(2)}`);
    console.log(`   Buying Power: $${state.account?.buyingPower.toFixed(2)}`);
    
    // Get positions
    await getPositions();
    
    if (state.positions.size > 0) {
      console.log(`\n📍 Current Positions:`);
      state.positions.forEach((pos) => {
        console.log(`   ${pos.side.toUpperCase()} ${pos.qty} ${pos.symbol} @ $${pos.avgPrice.toFixed(2)}`);
      });
    }
    
    // Check market status
    const marketOpen = await isMarketOpen();
    console.log(`\n🕐 Market Status: ${marketOpen ? '🟢 OPEN' : '🔴 CLOSED'}`);
    
    console.log(`\n🚀 Starting Alpaca Trader on ${state.tradableAssets.length} stocks...`);
    console.log(`${'═'.repeat(70)}`);
    
    // Main loop
    while (true) {
      await tradingCycle();
      await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
    }
    
  } catch (e: any) {
    console.log(`❌ Connection failed: ${e.message}`);
    console.log('');
    console.log('Check your API key and secret are correct.');
  }
}

run().catch(console.error);
