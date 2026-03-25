/**
 * 🐙 KRAKEN TRADER 🐙
 * 
 * Trade crypto on Kraken - Lower fees, reliable API
 * Supports: BTC, ETH, SOL, XRP, ADA, DOT, LINK, DOGE + more
 * 
 * Strategy: Momentum with Mean Reversion
 * - BUY when down > 1.5% (oversold)
 * - SELL when up > 1.5% (overbought)
 * 
 * Author: Gary Leckey
 */

import * as crypto from 'crypto';
import * as dotenv from 'dotenv';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

const CONFIG = {
  API_KEY: process.env.KRAKEN_API_KEY || '',
  API_SECRET: process.env.KRAKEN_API_SECRET || '',
  
  BASE_URL: 'https://api.kraken.com',
  
  // Trading settings
  RISK_PERCENT: 2,        // 2% per trade
  ENTRY_THRESHOLD: 1.5,   // Enter on 1.5% move
  TAKE_PROFIT: 2.0,       // 2% take profit
  STOP_LOSS: 1.0,         // 1% stop loss
  SCAN_INTERVAL: 5000,    // 5 seconds
  MAX_POSITIONS: 3,
};

// Kraken trading pairs (XBT = BTC on Kraken)
const TRADING_PAIRS = [
  { pair: 'XXBTZUSD', base: 'XBT', quote: 'USD', name: 'BTC/USD' },
  { pair: 'XETHZUSD', base: 'ETH', quote: 'USD', name: 'ETH/USD' },
  { pair: 'SOLUSD', base: 'SOL', quote: 'USD', name: 'SOL/USD' },
  { pair: 'XXRPZUSD', base: 'XRP', quote: 'USD', name: 'XRP/USD' },
  { pair: 'ADAUSD', base: 'ADA', quote: 'USD', name: 'ADA/USD' },
  { pair: 'DOTUSD', base: 'DOT', quote: 'USD', name: 'DOT/USD' },
  { pair: 'LINKUSD', base: 'LINK', quote: 'USD', name: 'LINK/USD' },
  { pair: 'XDGUSD', base: 'XDG', quote: 'USD', name: 'DOGE/USD' },
];

interface Position {
  pair: string;
  side: 'buy' | 'sell';
  price: number;
  volume: number;
  orderId: string;
  entryTime: Date;
}

interface MarketData {
  pair: string;
  name: string;
  price: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  change: number;
}

const state = {
  positions: new Map<string, Position>(),
  balances: new Map<string, number>(),
  trades: { total: 0, wins: 0, losses: 0 },
  pnl: 0,
  nonce: Date.now(),
};

// ═══════════════════════════════════════════════════════════════════════════════
// KRAKEN API
// ═══════════════════════════════════════════════════════════════════════════════

function getSignature(path: string, postData: string, nonce: number): string {
  const message = nonce + postData;
  const hash = crypto.createHash('sha256').update(message).digest();
  const secretBuffer = Buffer.from(CONFIG.API_SECRET, 'base64');
  const hmac = crypto.createHmac('sha512', secretBuffer);
  hmac.update(path);
  hmac.update(hash);
  return hmac.digest('base64');
}

async function publicRequest(endpoint: string): Promise<any> {
  const response = await fetch(`${CONFIG.BASE_URL}/0/public/${endpoint}`);
  const data = await response.json();
  
  if (data.error && data.error.length > 0) {
    throw new Error(data.error.join(', '));
  }
  
  return data.result;
}

async function privateRequest(endpoint: string, params: Record<string, any> = {}): Promise<any> {
  const nonce = ++state.nonce;
  const postData = new URLSearchParams({ nonce: nonce.toString(), ...params }).toString();
  const path = `/0/private/${endpoint}`;
  const signature = getSignature(path, postData, nonce);
  
  const response = await fetch(`${CONFIG.BASE_URL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
      'API-Key': CONFIG.API_KEY,
      'API-Sign': signature,
    },
    body: postData,
  });
  
  const data = await response.json();
  
  if (data.error && data.error.length > 0) {
    throw new Error(data.error.join(', '));
  }
  
  return data.result;
}

async function getBalance(): Promise<void> {
  const balances = await privateRequest('Balance');
  state.balances.clear();
  
  for (const [asset, amount] of Object.entries(balances)) {
    const bal = parseFloat(amount as string);
    if (bal > 0) {
      state.balances.set(asset, bal);
    }
  }
}

async function getTicker(pairs: string[]): Promise<Map<string, MarketData>> {
  const pairList = pairs.join(',');
  const tickers = await publicRequest(`Ticker?pair=${pairList}`);
  
  const result = new Map<string, MarketData>();
  
  for (const pairInfo of TRADING_PAIRS) {
    const ticker = tickers[pairInfo.pair];
    if (ticker) {
      const price = parseFloat(ticker.c[0]); // Last trade price
      const open = parseFloat(ticker.o);     // Today's open
      const high = parseFloat(ticker.h[1]);  // 24h high
      const low = parseFloat(ticker.l[1]);   // 24h low
      const volume = parseFloat(ticker.v[1]); // 24h volume
      const change = ((price - open) / open) * 100;
      
      result.set(pairInfo.pair, {
        pair: pairInfo.pair,
        name: pairInfo.name,
        price,
        open,
        high,
        low,
        volume,
        change,
      });
    }
  }
  
  return result;
}

async function placeOrder(pair: string, side: 'buy' | 'sell', volume: number): Promise<string | null> {
  console.log(`\n🎯 ${side.toUpperCase()} ${volume} ${pair}`);
  
  try {
    const result = await privateRequest('AddOrder', {
      pair,
      type: side,
      ordertype: 'market',
      volume: volume.toString(),
    });
    
    const orderId = result.txid?.[0] || 'unknown';
    console.log(`✅ Order placed! ID: ${orderId}`);
    state.trades.total++;
    return orderId;
  } catch (e: any) {
    console.log(`❌ Order failed: ${e.message}`);
    return null;
  }
}

async function getOpenOrders(): Promise<void> {
  try {
    const orders = await privateRequest('OpenOrders');
    // Update positions from open orders if needed
  } catch (e: any) {
    // Ignore errors
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

function getSignal(data: MarketData): { action: 'BUY' | 'SELL' | 'HOLD'; reason: string } {
  const change = data.change;
  
  // Mean reversion strategy
  if (change <= -CONFIG.ENTRY_THRESHOLD) {
    return { action: 'BUY', reason: `Oversold (${change.toFixed(2)}%)` };
  } else if (change >= CONFIG.ENTRY_THRESHOLD) {
    return { action: 'SELL', reason: `Overbought (+${change.toFixed(2)}%)` };
  }
  
  return { action: 'HOLD', reason: 'No signal' };
}

async function tradingCycle(): Promise<void> {
  console.log(`\n${'═'.repeat(65)}`);
  console.log(`🐙 ${new Date().toLocaleTimeString()} | Scanning ${TRADING_PAIRS.length} pairs...`);
  
  try {
    // Get market data
    const pairs = TRADING_PAIRS.map(p => p.pair);
    const markets = await getTicker(pairs);
    
    for (const [pair, data] of markets) {
      const pairInfo = TRADING_PAIRS.find(p => p.pair === pair);
      if (!pairInfo) continue;
      
      const signal = getSignal(data);
      const arrow = data.change >= 0 ? '📈' : '📉';
      
      console.log(`  ${arrow} ${data.name}: $${data.price.toFixed(2)} (${data.change >= 0 ? '+' : ''}${data.change.toFixed(2)}%)`);
      
      // Check existing position
      const existingPos = state.positions.get(pair);
      
      if (existingPos) {
        // Check exit conditions
        const pnlPct = existingPos.side === 'buy'
          ? ((data.price - existingPos.price) / existingPos.price) * 100
          : ((existingPos.price - data.price) / existingPos.price) * 100;
        
        if (pnlPct >= CONFIG.TAKE_PROFIT || pnlPct <= -CONFIG.STOP_LOSS) {
          const reason = pnlPct >= CONFIG.TAKE_PROFIT ? '🎯 TP' : '🛑 SL';
          console.log(`     ${reason} ${pnlPct >= 0 ? '+' : ''}${pnlPct.toFixed(2)}%`);
          
          const closeSide = existingPos.side === 'buy' ? 'sell' : 'buy';
          if (await placeOrder(pair, closeSide, existingPos.volume)) {
            state.positions.delete(pair);
            state.pnl += existingPos.volume * existingPos.price * (pnlPct / 100);
            if (pnlPct > 0) state.trades.wins++;
            else state.trades.losses++;
          }
        }
        continue;
      }
      
      // Open new position
      if (signal.action !== 'HOLD' && state.positions.size < CONFIG.MAX_POSITIONS) {
        console.log(`     🎯 ${signal.action} Signal: ${signal.reason}`);
        
        // Calculate position size
        const usdBalance = state.balances.get('ZUSD') || state.balances.get('USD') || 0;
        const baseBalance = state.balances.get(pairInfo.base) || 0;
        
        let volume = 0;
        let side: 'buy' | 'sell' = 'buy';
        
        if (signal.action === 'BUY' && usdBalance > 10) {
          const tradeAmount = usdBalance * (CONFIG.RISK_PERCENT / 100);
          volume = tradeAmount / data.price;
          side = 'buy';
        } else if (signal.action === 'SELL' && baseBalance > 0) {
          volume = baseBalance * (CONFIG.RISK_PERCENT / 100);
          side = 'sell';
        }
        
        if (volume > 0.0001) {
          const orderId = await placeOrder(pair, side, volume);
          if (orderId) {
            state.positions.set(pair, {
              pair,
              side,
              price: data.price,
              volume,
              orderId,
              entryTime: new Date(),
            });
          }
        }
      }
    }
    
    // Status
    const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
    console.log(`\n💼 Positions: ${state.positions.size}/${CONFIG.MAX_POSITIONS} | Trades: ${state.trades.total} (W:${state.trades.wins} L:${state.trades.losses}) | Win Rate: ${winRate.toFixed(0)}%`);
    
    // Show balances
    console.log(`💰 Balances:`);
    state.balances.forEach((bal, asset) => {
      if (bal > 0.0001) {
        console.log(`   ${asset}: ${bal.toFixed(8)}`);
      }
    });
    
  } catch (e: any) {
    console.log(`⚠️ Error: ${e.message}`);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function run(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🐙 KRAKEN TRADER 🐙                                                        ║
║                                                                               ║
║   ██╗  ██╗██████╗  █████╗ ██╗  ██╗███████╗███╗   ██╗                         ║
║   ██║ ██╔╝██╔══██╗██╔══██╗██║ ██╔╝██╔════╝████╗  ██║                         ║
║   █████╔╝ ██████╔╝███████║█████╔╝ █████╗  ██╔██╗ ██║                         ║
║   ██╔═██╗ ██╔══██╗██╔══██║██╔═██╗ ██╔══╝  ██║╚██╗██║                         ║
║   ██║  ██╗██║  ██║██║  ██║██║  ██╗███████╗██║ ╚████║                         ║
║   ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝                         ║
║                                                                               ║
║   Pairs: BTC, ETH, SOL, XRP, ADA, DOT, LINK, DOGE                            ║
║                                                                               ║
║   Strategy: Mean Reversion                                                    ║
║     • BUY when down ≥ 1.5%                                                   ║
║     • SELL when up ≥ 1.5%                                                    ║
║     • Take Profit: 2% | Stop Loss: 1%                                        ║
║     • Risk: 2% per trade | Max 3 positions                                   ║
║                                                                               ║
║   Author: Gary Leckey - "Release the Kraken!" 🦆                             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Kraken API credentials!');
    console.log('');
    console.log('To set up Kraken:');
    console.log('1. Go to https://www.kraken.com/u/security/api');
    console.log('2. Create a new API key with trading permissions');
    console.log('3. Add to your .env file:');
    console.log('   KRAKEN_API_KEY=your_api_key');
    console.log('   KRAKEN_API_SECRET=your_api_secret');
    console.log('');
    return;
  }
  
  console.log('🔐 Connecting to Kraken...');
  
  try {
    await getBalance();
    console.log('✅ Connected!\n');
    
    console.log('💰 Your Balances:');
    if (state.balances.size === 0) {
      console.log('   (No balances found - deposit funds to trade)');
    } else {
      state.balances.forEach((bal, asset) => {
        console.log(`   ${asset}: ${bal.toFixed(8)}`);
      });
    }
    
    console.log('\n🚀 Starting Kraken Trader...');
    
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
