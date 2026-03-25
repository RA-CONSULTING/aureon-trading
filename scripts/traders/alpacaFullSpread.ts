/**
 * 🦙 ALPACA FULL SPREAD TRADER 🦙
 * 
 * Trade EVERYTHING on Alpaca - Full Market Coverage!
 * - ALL US Stocks (NYSE, NASDAQ, AMEX)
 * - ALL ETFs
 * - ALL Crypto (24/7)
 * - Options-enabled stocks
 * 
 * Dynamically loads ALL tradeable assets | Commission-free
 * 
 * Strategy: Mean Reversion + Momentum with 9 Auris Nodes
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
  COHERENCE_THRESHOLD: 0.75,
  RISK_PERCENT: 2,
  ENTRY_THRESHOLD: 1.5,
  TAKE_PROFIT: 2.5,
  STOP_LOSS: 1.0,
  
  // Stock filters
  STOCK_MIN_VOLUME: 500000,
  STOCK_MIN_PRICE: 2,
  STOCK_MAX_PRICE: 1000,
  
  // Crypto filters
  CRYPTO_MIN_VOLUME: 100000,
  
  // Scanning
  SCAN_BATCH_SIZE: 200,       // Symbols per API call
  SCAN_INTERVAL: 5000,        // 5 seconds between cycles
  SYMBOLS_PER_CYCLE: 500,     // How many symbols to scan per cycle
  
  MAX_POSITIONS: 15,
  MAX_STOCK_POSITIONS: 10,
  MAX_CRYPTO_POSITIONS: 5,
};

// ═══════════════════════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════════════════════

interface Asset {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  assetClass: 'us_equity' | 'crypto';
  tradable: boolean;
  fractionable: boolean;
  shortable: boolean;
  marginable: boolean;
  minOrderSize: number;
  minTradeIncrement: number;
  priceIncrement: number;
}

interface Position {
  symbol: string;
  assetClass: string;
  side: 'long' | 'short';
  qty: number;
  avgPrice: number;
  marketValue: number;
  unrealizedPnl: number;
  entryTime: Date;
}

interface Quote {
  symbol: string;
  assetClass: string;
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
  cryptoBuyingPower: number;
  tradingBlocked: boolean;
  patternDayTrader: boolean;
}

const state = {
  // Assets by class
  stocks: new Map<string, Asset>(),
  etfs: new Map<string, Asset>(),
  crypto: new Map<string, Asset>(),
  
  // All tradeable symbols
  allSymbols: [] as string[],
  stockSymbols: [] as string[],
  cryptoSymbols: [] as string[],
  
  // Current scan position
  scanIndex: 0,
  
  positions: new Map<string, Position>(),
  account: null as Account | null,
  
  // Stats
  trades: { total: 0, wins: 0, losses: 0, stocks: 0, crypto: 0 },
  pnl: 0,
  cycle: 0,
  startTime: new Date(),
  
  // Market status
  stockMarketOpen: false,
  cryptoMarketOpen: true, // Always open
  
  // Top movers cache
  topMovers: new Map<string, Quote>(),
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
// LOAD ALL ASSETS - FULL SPREAD
// ═══════════════════════════════════════════════════════════════════════════════

async function loadAllAssets(): Promise<void> {
  console.log('📊 Loading ALL Alpaca assets...');
  
  // Clear existing
  state.stocks.clear();
  state.etfs.clear();
  state.crypto.clear();
  state.stockSymbols = [];
  state.cryptoSymbols = [];
  
  // Load US Equities (stocks + ETFs)
  console.log('   📈 Loading US Equities...');
  const equities = await alpacaRequest('/v2/assets?status=active&asset_class=us_equity');
  
  let stockCount = 0;
  let etfCount = 0;
  
  for (const asset of equities) {
    if (!asset.tradable) continue;
    if (asset.status !== 'active') continue;
    
    const assetInfo: Asset = {
      id: asset.id,
      symbol: asset.symbol,
      name: asset.name,
      exchange: asset.exchange,
      assetClass: 'us_equity',
      tradable: asset.tradable,
      fractionable: asset.fractionable || false,
      shortable: asset.shortable || false,
      marginable: asset.marginable || false,
      minOrderSize: asset.min_order_size ? parseFloat(asset.min_order_size) : 1,
      minTradeIncrement: asset.min_trade_increment ? parseFloat(asset.min_trade_increment) : 0.0001,
      priceIncrement: asset.price_increment ? parseFloat(asset.price_increment) : 0.01,
    };
    
    // Classify as ETF or stock
    if (asset.name?.includes('ETF') || asset.name?.includes('Trust') || asset.name?.includes('Fund')) {
      state.etfs.set(asset.symbol, assetInfo);
      etfCount++;
    } else {
      state.stocks.set(asset.symbol, assetInfo);
      stockCount++;
    }
    
    state.stockSymbols.push(asset.symbol);
  }
  
  console.log(`   ✅ ${stockCount} stocks + ${etfCount} ETFs`);
  
  // Load Crypto
  console.log('   🪙 Loading Crypto...');
  try {
    const cryptoAssets = await alpacaRequest('/v2/assets?status=active&asset_class=crypto');
    
    for (const asset of cryptoAssets) {
      if (!asset.tradable) continue;
      
      const assetInfo: Asset = {
        id: asset.id,
        symbol: asset.symbol,
        name: asset.name,
        exchange: asset.exchange || 'CRYPTO',
        assetClass: 'crypto',
        tradable: asset.tradable,
        fractionable: true,
        shortable: false,
        marginable: false,
        minOrderSize: asset.min_order_size ? parseFloat(asset.min_order_size) : 0.0001,
        minTradeIncrement: asset.min_trade_increment ? parseFloat(asset.min_trade_increment) : 0.00000001,
        priceIncrement: asset.price_increment ? parseFloat(asset.price_increment) : 0.01,
      };
      
      state.crypto.set(asset.symbol, assetInfo);
      state.cryptoSymbols.push(asset.symbol);
    }
    
    console.log(`   ✅ ${state.crypto.size} crypto pairs`);
  } catch (e: any) {
    console.log(`   ⚠️ Crypto not available: ${e.message}`);
  }
  
  // Combine all symbols
  state.allSymbols = [...state.stockSymbols, ...state.cryptoSymbols];
  
  console.log(`\n✅ TOTAL: ${state.allSymbols.length} tradeable assets`);
  console.log(`   📈 Stocks: ${state.stocks.size}`);
  console.log(`   📊 ETFs: ${state.etfs.size}`);
  console.log(`   🪙 Crypto: ${state.crypto.size}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// GET MARKET DATA - BATCH PROCESSING
// ═══════════════════════════════════════════════════════════════════════════════

async function getStockQuotes(symbols: string[]): Promise<Map<string, Quote>> {
  const result = new Map<string, Quote>();
  if (symbols.length === 0) return result;
  
  // Batch into chunks
  const chunks = [];
  for (let i = 0; i < symbols.length; i += CONFIG.SCAN_BATCH_SIZE) {
    chunks.push(symbols.slice(i, i + CONFIG.SCAN_BATCH_SIZE));
  }
  
  for (const chunk of chunks) {
    try {
      const symbolList = chunk.join(',');
      
      // Get latest quotes and bars in parallel
      const [quotesResp, barsResp] = await Promise.all([
        alpacaRequest(`/v2/stocks/quotes/latest?symbols=${symbolList}`, 'GET', undefined, true),
        alpacaRequest(`/v2/stocks/bars/latest?symbols=${symbolList}`, 'GET', undefined, true),
      ]);
      
      for (const symbol of chunk) {
        const quote = quotesResp.quotes?.[symbol];
        const bar = barsResp.bars?.[symbol];
        
        if (!quote || !bar) continue;
        
        const price = (quote.bp + quote.ap) / 2;
        const open = bar.o;
        const change = open > 0 ? ((price - open) / open) * 100 : 0;
        
        result.set(symbol, {
          symbol,
          assetClass: 'us_equity',
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

async function getCryptoQuotes(symbols: string[]): Promise<Map<string, Quote>> {
  const result = new Map<string, Quote>();
  if (symbols.length === 0) return result;
  
  // Batch into chunks
  const chunks = [];
  for (let i = 0; i < symbols.length; i += 50) {
    chunks.push(symbols.slice(i, i + 50));
  }
  
  for (const chunk of chunks) {
    try {
      const symbolList = chunk.join(',');
      
      // Get crypto quotes and bars
      const [quotesResp, barsResp] = await Promise.all([
        alpacaRequest(`/v1beta3/crypto/us/latest/quotes?symbols=${symbolList}`, 'GET', undefined, true),
        alpacaRequest(`/v1beta3/crypto/us/latest/bars?symbols=${symbolList}`, 'GET', undefined, true),
      ]);
      
      for (const symbol of chunk) {
        const quote = quotesResp.quotes?.[symbol];
        const bar = barsResp.bars?.[symbol];
        
        if (!quote && !bar) continue;
        
        const bid = quote?.bp || bar?.c || 0;
        const ask = quote?.ap || bar?.c || 0;
        const price = (bid + ask) / 2 || bar?.c || 0;
        const open = bar?.o || price;
        const change = open > 0 ? ((price - open) / open) * 100 : 0;
        
        result.set(symbol, {
          symbol,
          assetClass: 'crypto',
          price,
          open,
          high: bar?.h || price,
          low: bar?.l || price,
          volume: bar?.v || 0,
          change,
          bid,
          ask,
        });
      }
    } catch (e: any) {
      // Skip failed chunks
    }
  }
  
  return result;
}

// ═══════════════════════════════════════════════════════════════════════════════
// SCREENERS - FIND OPPORTUNITIES
// ═══════════════════════════════════════════════════════════════════════════════

async function getTopStockMovers(): Promise<string[]> {
  const movers: string[] = [];
  
  try {
    // Most active by volume
    const active = await alpacaRequest('/v1beta1/screener/stocks/most-actives?by=volume&top=50', 'GET', undefined, true);
    movers.push(...(active.most_actives?.map((s: any) => s.symbol) || []));
    
    // Top gainers
    const gainers = await alpacaRequest('/v1beta1/screener/stocks/movers?top=25', 'GET', undefined, true);
    movers.push(...(gainers.gainers?.map((s: any) => s.symbol) || []));
    
    // Top losers (for short opportunities or bounce plays)
    movers.push(...(gainers.losers?.map((s: any) => s.symbol) || []));
  } catch {
    // Fallback
  }
  
  return [...new Set(movers)]; // Remove duplicates
}

async function scanMarketSlice(): Promise<Map<string, Quote>> {
  const allQuotes = new Map<string, Quote>();
  
  // Get top movers first (priority)
  const topMovers = await getTopStockMovers();
  
  // Get slice of all symbols for rotation
  const sliceStart = state.scanIndex;
  const sliceEnd = Math.min(sliceStart + CONFIG.SYMBOLS_PER_CYCLE, state.stockSymbols.length);
  const symbolSlice = state.stockSymbols.slice(sliceStart, sliceEnd);
  
  // Update scan index for next cycle
  state.scanIndex = sliceEnd >= state.stockSymbols.length ? 0 : sliceEnd;
  
  // Combine movers + slice (deduplicated)
  const stocksToScan = [...new Set([...topMovers, ...symbolSlice])];
  
  // Get stock quotes
  if (state.stockMarketOpen && stocksToScan.length > 0) {
    const stockQuotes = await getStockQuotes(stocksToScan);
    stockQuotes.forEach((q, s) => allQuotes.set(s, q));
  }
  
  // Always get crypto (24/7)
  if (state.cryptoSymbols.length > 0) {
    const cryptoQuotes = await getCryptoQuotes(state.cryptoSymbols);
    cryptoQuotes.forEach((q, s) => allQuotes.set(s, q));
  }
  
  return allQuotes;
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
    cryptoBuyingPower: parseFloat(account.non_marginable_buying_power || account.cash),
    tradingBlocked: account.trading_blocked,
    patternDayTrader: account.pattern_day_trader,
  };
}

async function getPositions(): Promise<void> {
  const positions = await alpacaRequest('/v2/positions');
  state.positions.clear();
  
  for (const pos of positions) {
    state.positions.set(pos.symbol, {
      symbol: pos.symbol,
      assetClass: pos.asset_class,
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
  state.stockMarketOpen = clock.is_open;
  return clock.is_open;
}

async function placeOrder(symbol: string, side: 'buy' | 'sell', notional: number, isCrypto = false): Promise<string | null> {
  const asset = state.stocks.get(symbol) || state.etfs.get(symbol) || state.crypto.get(symbol);
  const assetType = isCrypto ? '🪙' : '📈';
  
  console.log(`\n🎯 ${assetType} ${side.toUpperCase()} $${notional.toFixed(2)} of ${symbol}`);
  
  try {
    const orderData: any = {
      symbol,
      side,
      type: 'market',
      time_in_force: isCrypto ? 'gtc' : 'day',
      notional: notional.toFixed(2),
    };
    
    const result = await alpacaRequest('/v2/orders', 'POST', orderData);
    console.log(`✅ Order submitted! ID: ${result.id}`);
    state.trades.total++;
    if (isCrypto) state.trades.crypto++;
    else state.trades.stocks++;
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

async function processAsset(symbol: string, data: Quote): Promise<void> {
  const isCrypto = data.assetClass === 'crypto';
  const asset = state.stocks.get(symbol) || state.etfs.get(symbol) || state.crypto.get(symbol);
  
  if (!asset) return;
  
  // Apply filters based on asset class
  if (isCrypto) {
    if (data.volume * data.price < CONFIG.CRYPTO_MIN_VOLUME) return;
  } else {
    if (data.price < CONFIG.STOCK_MIN_PRICE || data.price > CONFIG.STOCK_MAX_PRICE) return;
    if (data.volume < CONFIG.STOCK_MIN_VOLUME) return;
  }
  
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
  
  // Check position limits by asset class
  const stockPositions = [...state.positions.values()].filter(p => p.assetClass === 'us_equity').length;
  const cryptoPositions = [...state.positions.values()].filter(p => p.assetClass === 'crypto').length;
  
  if (isCrypto && cryptoPositions >= CONFIG.MAX_CRYPTO_POSITIONS) return;
  if (!isCrypto && stockPositions >= CONFIG.MAX_STOCK_POSITIONS) return;
  if (state.positions.size >= CONFIG.MAX_POSITIONS) return;
  
  // Determine direction
  let signal: 'BUY' | 'SELL' | 'HOLD' = 'HOLD';
  if (data.change <= -CONFIG.ENTRY_THRESHOLD) signal = 'BUY';
  else if (data.change >= CONFIG.ENTRY_THRESHOLD) signal = 'SELL';
  
  if (signal === 'HOLD') return;
  
  // Calculate position size
  const buyingPower = isCrypto 
    ? (state.account?.cryptoBuyingPower || 0)
    : (state.account?.buyingPower || 0);
    
  if (buyingPower < 10) return;
  
  const tradeAmount = Math.min(buyingPower * (CONFIG.RISK_PERCENT / 100), 100);
  if (tradeAmount < 1) return;
  
  const assetType = isCrypto ? '🪙' : '📈';
  console.log(`\n${freq.color} ${assetType} [${symbol}] Λ=${lambda.toFixed(2)} Γ=${coherence.toFixed(3)} ${freq.hz.toFixed(0)}Hz`);
  console.log(`   ${signal} @ $${data.price.toFixed(4)} (${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%)`);
  
  if (signal === 'BUY') {
    const orderId = await placeOrder(symbol, 'buy', tradeAmount, isCrypto);
    if (orderId) {
      await getPositions();
      await getAccount();
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// DISPLAY
// ═══════════════════════════════════════════════════════════════════════════════

function displayStatus(quotes: Map<string, Quote>): void {
  const elapsed = (Date.now() - state.startTime.getTime()) / 1000 / 60;
  const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
  
  // Find top movers
  const stockMovers = [...quotes.values()]
    .filter(q => q.assetClass === 'us_equity' && q.volume > CONFIG.STOCK_MIN_VOLUME)
    .sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
    .slice(0, 3);
    
  const cryptoMovers = [...quotes.values()]
    .filter(q => q.assetClass === 'crypto')
    .sort((a, b) => Math.abs(b.change) - Math.abs(a.change))
    .slice(0, 3);
  
  const mode = CONFIG.PAPER ? '📝 PAPER' : '💵 LIVE';
  const stockStatus = state.stockMarketOpen ? '🟢' : '🔴';
  
  // Count positions by type
  const stockPos = [...state.positions.values()].filter(p => p.assetClass === 'us_equity').length;
  const cryptoPos = [...state.positions.values()].filter(p => p.assetClass === 'crypto').length;
  
  console.log(`
╔════════════════════════════════════════════════════════════════════════════════════╗
║  🦙 ALPACA FULL SPREAD - ${new Date().toLocaleTimeString()} ${mode}                              ║
╠════════════════════════════════════════════════════════════════════════════════════╣
║  ⏱️  ${elapsed.toFixed(1)}min | 📊 Total: ${state.allSymbols.length} (${state.stocks.size + state.etfs.size} stocks, ${state.crypto.size} crypto) | Cycle: ${state.cycle}  ║
║  📈 Stock Market: ${stockStatus} | 🪙 Crypto: 🟢 (24/7)                                        ║
║  💰 Equity: $${(state.account?.equity || 0).toFixed(2)} | Cash: $${(state.account?.cash || 0).toFixed(2)} | BP: $${(state.account?.buyingPower || 0).toFixed(2)}  ║
║  📍 Positions: ${state.positions.size}/${CONFIG.MAX_POSITIONS} (📈${stockPos} 🪙${cryptoPos}) | Trades: ${state.trades.total} (📈${state.trades.stocks} 🪙${state.trades.crypto})  ║
║  🏆 W:${state.trades.wins} L:${state.trades.losses} (${winRate.toFixed(0)}%) | 📈 PnL: $${state.pnl.toFixed(2)}                              ║
╚════════════════════════════════════════════════════════════════════════════════════╝`);

  // Show stock movers
  if (stockMovers.length > 0) {
    console.log(`  📈 Stock Movers:`);
    for (const q of stockMovers) {
      const arrow = q.change >= 0 ? '📈' : '📉';
      console.log(`     ${arrow} ${q.symbol}: $${q.price.toFixed(2)} (${q.change >= 0 ? '+' : ''}${q.change.toFixed(2)}%)`);
    }
  }
  
  // Show crypto movers
  if (cryptoMovers.length > 0) {
    console.log(`  🪙 Crypto Movers:`);
    for (const q of cryptoMovers) {
      const arrow = q.change >= 0 ? '📈' : '📉';
      console.log(`     ${arrow} ${q.symbol}: $${q.price.toFixed(4)} (${q.change >= 0 ? '+' : ''}${q.change.toFixed(2)}%)`);
    }
  }
  
  // Show positions
  if (state.positions.size > 0) {
    console.log(`  📍 Open Positions:`);
    state.positions.forEach((pos) => {
      const pnlPct = (pos.unrealizedPnl / (pos.avgPrice * pos.qty)) * 100;
      const type = pos.assetClass === 'crypto' ? '🪙' : '📈';
      console.log(`     ${type} ${pos.side.toUpperCase()} ${pos.symbol}: ${pos.unrealizedPnl >= 0 ? '+' : ''}$${pos.unrealizedPnl.toFixed(2)} (${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%)`);
    });
  }
  
  console.log(`  🔄 Scanning: symbols ${state.scanIndex}-${Math.min(state.scanIndex + CONFIG.SYMBOLS_PER_CYCLE, state.stockSymbols.length)} of ${state.stockSymbols.length}`);
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN TRADING LOOP
// ═══════════════════════════════════════════════════════════════════════════════

async function tradingCycle(): Promise<void> {
  state.cycle++;
  
  try {
    // Check market status
    await isMarketOpen();
    
    // Scan market slice (rotates through all symbols)
    const quotes = await scanMarketSlice();
    
    // Process each asset
    for (const [symbol, data] of quotes) {
      await processAsset(symbol, data);
    }
    
    // Refresh positions and account every 5 cycles
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
╔════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                    ║
║   🦙 ALPACA FULL SPREAD TRADER 🦙                                                 ║
║                                                                                    ║
║    █████╗ ██╗     ██████╗  █████╗  ██████╗ █████╗                                 ║
║   ██╔══██╗██║     ██╔══██╗██╔══██╗██╔════╝██╔══██╗                                ║
║   ███████║██║     ██████╔╝███████║██║     ███████║                                ║
║   ██╔══██║██║     ██╔═══╝ ██╔══██║██║     ██╔══██║                                ║
║   ██║  ██║███████╗██║     ██║  ██║╚██████╗██║  ██║                                ║
║   ╚═╝  ╚═╝╚══════╝╚═╝     ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝                                ║
║                                                                                    ║
║   🔴 ${mode} - FULL MARKET COVERAGE 🔴                               ║
║                                                                                    ║
║   ═══════════════════════════════════════════════════════════════════════════     ║
║                                                                                    ║
║   📈 US STOCKS - All NYSE, NASDAQ, AMEX stocks                                    ║
║   📊 ETFs - All exchange-traded funds                                             ║
║   🪙 CRYPTO - BTC, ETH, and 20+ altcoins (24/7)                                   ║
║                                                                                    ║
║   ═══════════════════════════════════════════════════════════════════════════     ║
║                                                                                    ║
║   Features:                                                                        ║
║     • Commission-free trading on ALL assets                                       ║
║     • Fractional shares - invest any amount                                       ║
║     • 24/7 crypto trading                                                         ║
║     • Rotates through ENTIRE market each day                                      ║
║     • 9 Auris Nodes coherence analysis                                            ║
║     • Automatic position management                                               ║
║                                                                                    ║
║   Strategy:                                                                        ║
║     • Coherence Γ > 0.75 = Valid signal                                           ║
║     • BUY when down ≥ 1.5%                                                        ║
║     • Take Profit: 2.5% | Stop Loss: 1%                                           ║
║     • Max 10 stock + 5 crypto positions                                           ║
║                                                                                    ║
║   Author: Gary Leckey - "Full Spread, Full Send!" 🦆                              ║
║                                                                                    ║
╚════════════════════════════════════════════════════════════════════════════════════╝
`);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Alpaca API credentials!');
    console.log('');
    console.log('To set up Alpaca:');
    console.log('1. Go to https://app.alpaca.markets/');
    console.log('2. Sign up for a free account');
    console.log('3. Enable crypto trading in settings');
    console.log('4. Go to API Keys and generate new keys');
    console.log('');
    console.log('5. Add to your .env file:');
    console.log('   ALPACA_API_KEY=your_api_key');
    console.log('   ALPACA_SECRET=your_secret_key');
    console.log('   ALPACA_PAPER=true   # Set to false for live trading');
    console.log('');
    return;
  }
  
  console.log('🔐 Connecting to Alpaca...');
  
  try {
    // Load ALL assets
    await loadAllAssets();
    
    // Get account info
    await getAccount();
    
    console.log(`\n✅ Connected to Alpaca (${CONFIG.PAPER ? 'Paper' : 'Live'})`);
    console.log(`   Account Status: ${state.account?.status}`);
    console.log(`   Equity: $${state.account?.equity.toFixed(2)}`);
    console.log(`   Cash: $${state.account?.cash.toFixed(2)}`);
    console.log(`   Buying Power: $${state.account?.buyingPower.toFixed(2)}`);
    console.log(`   Crypto BP: $${state.account?.cryptoBuyingPower.toFixed(2)}`);
    
    if (state.account?.tradingBlocked) {
      console.log('⚠️ Trading is blocked on this account');
    }
    
    if (state.account?.patternDayTrader) {
      console.log('📊 Pattern Day Trader: Yes');
    }
    
    // Get positions
    await getPositions();
    
    if (state.positions.size > 0) {
      console.log(`\n📍 Current Positions:`);
      state.positions.forEach((pos) => {
        const type = pos.assetClass === 'crypto' ? '🪙' : '📈';
        console.log(`   ${type} ${pos.side.toUpperCase()} ${pos.qty} ${pos.symbol} @ $${pos.avgPrice.toFixed(2)}`);
      });
    }
    
    // Check market status
    const marketOpen = await isMarketOpen();
    console.log(`\n🕐 Stock Market: ${marketOpen ? '🟢 OPEN' : '🔴 CLOSED'}`);
    console.log(`🪙 Crypto Market: 🟢 ALWAYS OPEN (24/7)`);
    
    console.log(`\n🚀 Starting Full Spread Trader...`);
    console.log(`   Scanning ${state.allSymbols.length} assets`);
    console.log(`   ${CONFIG.SYMBOLS_PER_CYCLE} symbols per cycle`);
    console.log(`${'═'.repeat(80)}`);
    
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
