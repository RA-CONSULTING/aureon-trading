/**
 * 💰 CAPITAL.COM LIVE TRADER 💰
 * 
 * Trade CFDs on Capital.com - No API restrictions!
 * Supports: Crypto, Forex, Stocks, Commodities
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
  API_KEY: process.env.CAPITAL_API_KEY || '',
  PASSWORD: process.env.CAPITAL_PASSWORD || '',
  IS_DEMO: process.env.CAPITAL_DEMO === 'true',
  
  // API endpoints
  BASE_URL: process.env.CAPITAL_DEMO === 'true' 
    ? 'https://demo-api-capital.backend-capital.com'
    : 'https://api-capital.backend-capital.com',
    
  // Trading settings
  RISK_PERCENT: 2,        // Risk 2% per trade
  TAKE_PROFIT: 1.5,       // 1.5% take profit
  STOP_LOSS: 0.8,         // 0.8% stop loss
  SCAN_INTERVAL: 5000,    // 5 seconds
};

interface Session {
  CST: string;
  X_SECURITY_TOKEN: string;
}

interface Position {
  dealId: string;
  epic: string;
  direction: string;
  size: number;
  openLevel: number;
  pnl: number;
}

interface MarketData {
  epic: string;
  name: string;
  bid: number;
  offer: number;
  change: number;
  changePercent: number;
}

const state = {
  session: null as Session | null,
  positions: [] as Position[],
  trades: { total: 0, wins: 0, losses: 0 },
  pnl: 0,
  balance: 0,
};

// ═══════════════════════════════════════════════════════════════════════════════
// CAPITAL.COM API
// ═══════════════════════════════════════════════════════════════════════════════

async function login(): Promise<boolean> {
  console.log('🔐 Logging into Capital.com', CONFIG.IS_DEMO ? '(DEMO)' : '(LIVE)', '...');
  
  try {
    const response = await fetch(`${CONFIG.BASE_URL}/api/v1/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CAP-API-KEY': CONFIG.API_KEY,
      },
      body: JSON.stringify({
        identifier: CONFIG.API_KEY,
        password: CONFIG.PASSWORD,
      }),
    });
    
    if (!response.ok) {
      const error = await response.text();
      console.log('❌ Login failed:', error);
      return false;
    }
    
    state.session = {
      CST: response.headers.get('CST') || '',
      X_SECURITY_TOKEN: response.headers.get('X-SECURITY-TOKEN') || '',
    };
    
    console.log('✅ Logged in successfully!');
    return true;
  } catch (e: any) {
    console.log('❌ Login error:', e.message);
    return false;
  }
}

async function apiRequest(endpoint: string, method = 'GET', body?: any): Promise<any> {
  if (!state.session) throw new Error('Not logged in');
  
  const response = await fetch(`${CONFIG.BASE_URL}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'X-CAP-API-KEY': CONFIG.API_KEY,
      'CST': state.session.CST,
      'X-SECURITY-TOKEN': state.session.X_SECURITY_TOKEN,
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  
  if (!response.ok) {
    const error = await response.text();
    throw new Error(error);
  }
  
  return response.json();
}

async function getAccountInfo(): Promise<void> {
  const data = await apiRequest('/api/v1/accounts');
  const account = data.accounts?.[0];
  if (account) {
    state.balance = account.balance?.balance || 0;
    console.log('💰 Account Balance:', state.balance.toFixed(2), account.currency);
  }
}

async function getPositions(): Promise<void> {
  const data = await apiRequest('/api/v1/positions');
  state.positions = (data.positions || []).map((p: any) => ({
    dealId: p.position.dealId,
    epic: p.market.epic,
    direction: p.position.direction,
    size: p.position.size,
    openLevel: p.position.level,
    pnl: p.position.upl || 0,
  }));
}

async function getMarketData(epics: string[]): Promise<MarketData[]> {
  const epicList = epics.join(',');
  const data = await apiRequest(`/api/v1/markets?epics=${epicList}`);
  
  return (data.marketDetails || []).map((m: any) => ({
    epic: m.instrument.epic,
    name: m.instrument.name,
    bid: m.snapshot.bid,
    offer: m.snapshot.offer,
    change: m.snapshot.netChange,
    changePercent: m.snapshot.percentageChange,
  }));
}

async function openPosition(epic: string, direction: 'BUY' | 'SELL', size: number): Promise<boolean> {
  console.log(`\n🎯 Opening ${direction} position: ${epic} x ${size}`);
  
  try {
    const result = await apiRequest('/api/v1/positions', 'POST', {
      epic,
      direction,
      size,
      guaranteedStop: false,
      forceOpen: true,
    });
    
    console.log('✅ Position opened! Deal ID:', result.dealReference);
    state.trades.total++;
    return true;
  } catch (e: any) {
    console.log('❌ Failed to open position:', e.message);
    return false;
  }
}

async function closePosition(dealId: string): Promise<boolean> {
  try {
    await apiRequest(`/api/v1/positions/${dealId}`, 'DELETE');
    console.log('✅ Position closed:', dealId);
    return true;
  } catch (e: any) {
    console.log('❌ Failed to close position:', e.message);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

// Crypto pairs available on Capital.com
const CRYPTO_EPICS = [
  'BTCUSD',   // Bitcoin
  'ETHUSD',   // Ethereum
  'DOGEUSD',  // Dogecoin
  'XRPUSD',   // Ripple
  'ADAUSD',   // Cardano
  'SOLUSD',   // Solana
  'DOTUSD',   // Polkadot
  'LINKUSD', // Chainlink
  'BNBUSD',   // BNB
  'AVAXUSD',  // Avalanche
];

function computeSignal(data: MarketData): { action: 'BUY' | 'SELL' | 'HOLD'; strength: number } {
  const change = data.changePercent;
  
  // Simple momentum strategy
  if (change > 2) {
    return { action: 'BUY', strength: Math.min(change / 5, 1) };  // Buy on strong upward momentum
  } else if (change < -2) {
    return { action: 'SELL', strength: Math.min(Math.abs(change) / 5, 1) };  // Sell on strong downward
  }
  
  return { action: 'HOLD', strength: 0 };
}

async function tradingCycle(): Promise<void> {
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`⏰ ${new Date().toLocaleTimeString()} | Scanning markets...`);
  
  try {
    // Get market data
    const markets = await getMarketData(CRYPTO_EPICS);
    
    for (const market of markets) {
      const signal = computeSignal(market);
      const arrow = market.changePercent >= 0 ? '📈' : '📉';
      
      console.log(`  ${arrow} ${market.epic}: $${market.bid.toFixed(2)} (${market.changePercent >= 0 ? '+' : ''}${market.changePercent.toFixed(2)}%)`);
      
      if (signal.action !== 'HOLD') {
        console.log(`     🎯 Signal: ${signal.action} (strength: ${(signal.strength * 100).toFixed(0)}%)`);
        
        // Check if we already have a position
        const existingPos = state.positions.find(p => p.epic === market.epic);
        
        if (!existingPos && state.positions.length < 5) {
          // Calculate position size (risk 2% of balance)
          const riskAmount = state.balance * (CONFIG.RISK_PERCENT / 100);
          const size = Math.max(0.01, riskAmount / market.bid);
          
          await openPosition(market.epic, signal.action, parseFloat(size.toFixed(2)));
          await getPositions();
        }
      }
    }
    
    // Check existing positions for take profit / stop loss
    await getPositions();
    for (const pos of state.positions) {
      const pnlPercent = (pos.pnl / (pos.openLevel * pos.size)) * 100;
      
      if (pnlPercent >= CONFIG.TAKE_PROFIT) {
        console.log(`\n💰 Take Profit hit on ${pos.epic}! P&L: $${pos.pnl.toFixed(2)}`);
        if (await closePosition(pos.dealId)) {
          state.trades.wins++;
          state.pnl += pos.pnl;
        }
      } else if (pnlPercent <= -CONFIG.STOP_LOSS) {
        console.log(`\n🛑 Stop Loss hit on ${pos.epic}! P&L: $${pos.pnl.toFixed(2)}`);
        if (await closePosition(pos.dealId)) {
          state.trades.losses++;
          state.pnl += pos.pnl;
        }
      }
    }
    
    // Status update
    const totalPnl = state.positions.reduce((sum, p) => sum + p.pnl, 0);
    console.log(`\n💼 Open Positions: ${state.positions.length} | Unrealized P&L: $${totalPnl.toFixed(2)}`);
    console.log(`📊 Trades: ${state.trades.total} | Wins: ${state.trades.wins} | Losses: ${state.trades.losses} | Realized P&L: $${state.pnl.toFixed(2)}`);
    
  } catch (e: any) {
    console.log('⚠️ Error:', e.message);
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// MAIN
// ═══════════════════════════════════════════════════════════════════════════════

async function run(): Promise<void> {
  console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   💰 CAPITAL.COM LIVE TRADER 💰                                              ║
║                                                                               ║
║   Mode: ${CONFIG.IS_DEMO ? 'DEMO (Paper Trading)' : '🔴 LIVE TRADING 🔴'}                                          ║
║                                                                               ║
║   Markets: BTC, ETH, DOGE, XRP, ADA, SOL, DOT, LINK, BNB, AVAX               ║
║                                                                               ║
║   Strategy:                                                                   ║
║     • Buy on +2% momentum                                                    ║
║     • Sell on -2% momentum                                                   ║
║     • Take Profit: +1.5%                                                     ║
║     • Stop Loss: -0.8%                                                       ║
║     • Risk: 2% per trade                                                     ║
║                                                                               ║
║   Author: Gary Leckey - "Capital gains" 🦆                                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  if (!CONFIG.API_KEY || !CONFIG.PASSWORD) {
    console.log('❌ Missing Capital.com credentials in .env');
    return;
  }
  
  // Login
  if (!await login()) {
    return;
  }
  
  // Get account info
  await getAccountInfo();
  await getPositions();
  
  console.log(`\n🚀 Starting Capital.com Trader...`);
  
  // Main loop
  while (true) {
    await tradingCycle();
    await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
  }
}

run().catch(console.error);
