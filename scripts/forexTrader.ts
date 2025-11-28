/**
 * 💱 FOREX TRADER - Capital.com 💱
 * 
 * Pure Forex trading - Major & Minor pairs
 * No IP restrictions | CFD Trading | 24/5 Markets
 * 
 * Strategy: Momentum + Mean Reversion
 * - BUY when pair is down > 0.3% (oversold bounce)
 * - SELL when pair is up > 0.3% (overbought fade)
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
  EMAIL: process.env.CAPITAL_EMAIL || '', // Your Capital.com login email
  PASSWORD: process.env.CAPITAL_PASSWORD || '',
  IS_DEMO: process.env.CAPITAL_DEMO !== 'false', // Default to DEMO for safety
  
  BASE_URL: process.env.CAPITAL_DEMO !== 'false'
    ? 'https://demo-api-capital.backend-capital.com'
    : 'https://api-capital.backend-capital.com',
    
  // Forex-specific settings
  RISK_PERCENT: 1,        // 1% risk per trade (forex is leveraged!)
  TAKE_PROFIT_PIPS: 30,   // 30 pips TP
  STOP_LOSS_PIPS: 15,     // 15 pips SL (2:1 R:R)
  ENTRY_THRESHOLD: 0.3,   // Enter on 0.3% move
  SCAN_INTERVAL: 3000,    // 3 seconds
  MAX_POSITIONS: 3,       // Max 3 forex positions
};

// ═══════════════════════════════════════════════════════════════════════════════
// FOREX PAIRS - Major & Minor
// ═══════════════════════════════════════════════════════════════════════════════

const FOREX_PAIRS = [
  // Majors
  { epic: 'EURUSD', name: 'EUR/USD', pipSize: 0.0001 },
  { epic: 'GBPUSD', name: 'GBP/USD', pipSize: 0.0001 },
  { epic: 'USDJPY', name: 'USD/JPY', pipSize: 0.01 },
  { epic: 'USDCHF', name: 'USD/CHF', pipSize: 0.0001 },
  { epic: 'AUDUSD', name: 'AUD/USD', pipSize: 0.0001 },
  { epic: 'USDCAD', name: 'USD/CAD', pipSize: 0.0001 },
  { epic: 'NZDUSD', name: 'NZD/USD', pipSize: 0.0001 },
  
  // Minors (Crosses)
  { epic: 'EURGBP', name: 'EUR/GBP', pipSize: 0.0001 },
  { epic: 'EURJPY', name: 'EUR/JPY', pipSize: 0.01 },
  { epic: 'GBPJPY', name: 'GBP/JPY', pipSize: 0.01 },
  { epic: 'AUDJPY', name: 'AUD/JPY', pipSize: 0.01 },
  { epic: 'EURAUD', name: 'EUR/AUD', pipSize: 0.0001 },
];

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
  spread: number;
}

const state = {
  session: null as Session | null,
  positions: [] as Position[],
  trades: { total: 0, wins: 0, losses: 0 },
  pnl: 0,
  balance: 0,
  currency: 'USD',
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
        identifier: CONFIG.EMAIL,  // Use email, not API key
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
    state.currency = account.currency || 'USD';
    console.log(`💰 Balance: ${state.currency} ${state.balance.toFixed(2)}`);
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
    spread: m.snapshot.offer - m.snapshot.bid,
  }));
}

async function openPosition(epic: string, direction: 'BUY' | 'SELL', size: number): Promise<boolean> {
  console.log(`\n🎯 Opening ${direction} ${epic} x ${size.toFixed(2)} lots`);
  
  try {
    const result = await apiRequest('/api/v1/positions', 'POST', {
      epic,
      direction,
      size,
      guaranteedStop: false,
      forceOpen: true,
    });
    
    console.log('✅ Position opened! Deal:', result.dealReference);
    state.trades.total++;
    return true;
  } catch (e: any) {
    console.log('❌ Failed:', e.message);
    return false;
  }
}

async function closePosition(dealId: string): Promise<boolean> {
  try {
    await apiRequest(`/api/v1/positions/${dealId}`, 'DELETE');
    console.log('✅ Closed:', dealId);
    return true;
  } catch (e: any) {
    console.log('❌ Close failed:', e.message);
    return false;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// FOREX TRADING LOGIC
// ═══════════════════════════════════════════════════════════════════════════════

function getSignal(data: MarketData): { action: 'BUY' | 'SELL' | 'HOLD'; reason: string } {
  const change = data.changePercent;
  
  // Mean reversion strategy for forex
  // When pair drops, buy expecting bounce back
  // When pair rises, sell expecting pullback
  
  if (change <= -CONFIG.ENTRY_THRESHOLD) {
    return { action: 'BUY', reason: `Oversold (${change.toFixed(2)}%)` };
  } else if (change >= CONFIG.ENTRY_THRESHOLD) {
    return { action: 'SELL', reason: `Overbought (${change.toFixed(2)}%)` };
  }
  
  return { action: 'HOLD', reason: 'No signal' };
}

async function tradingCycle(): Promise<void> {
  console.log(`\n${'═'.repeat(65)}`);
  console.log(`⏰ ${new Date().toLocaleTimeString()} | Scanning ${FOREX_PAIRS.length} forex pairs...`);
  
  try {
    await getPositions();
    
    // Get market data
    const epics = FOREX_PAIRS.map(p => p.epic);
    const markets = await getMarketData(epics);
    
    for (const market of markets) {
      const pairInfo = FOREX_PAIRS.find(p => p.epic === market.epic);
      if (!pairInfo) continue;
      
      const signal = getSignal(market);
      const arrow = market.changePercent >= 0 ? '📈' : '📉';
      const spreadPips = (market.spread / pairInfo.pipSize).toFixed(1);
      
      console.log(`  ${arrow} ${market.epic}: ${market.bid.toFixed(pairInfo.pipSize === 0.01 ? 3 : 5)} (${market.changePercent >= 0 ? '+' : ''}${market.changePercent.toFixed(2)}%) [${spreadPips}pip]`);
      
      // Check for existing position
      const existingPos = state.positions.find(p => p.epic === market.epic);
      
      // Check exit conditions for existing positions
      if (existingPos) {
        const pnlPips = existingPos.pnl / pairInfo.pipSize;
        
        // Take profit or stop loss
        if (pnlPips >= CONFIG.TAKE_PROFIT_PIPS || pnlPips <= -CONFIG.STOP_LOSS_PIPS) {
          const reason = pnlPips >= CONFIG.TAKE_PROFIT_PIPS ? '🎯 TP' : '🛑 SL';
          console.log(`     ${reason} hit! PnL: ${pnlPips.toFixed(1)} pips`);
          
          if (await closePosition(existingPos.dealId)) {
            state.pnl += existingPos.pnl;
            if (pnlPips > 0) state.trades.wins++;
            else state.trades.losses++;
          }
        }
        continue;
      }
      
      // Open new position if signal and under max positions
      if (signal.action !== 'HOLD' && state.positions.length < CONFIG.MAX_POSITIONS) {
        console.log(`     🎯 ${signal.action} Signal: ${signal.reason}`);
        
        // Calculate lot size (mini lots for safety)
        const riskAmount = state.balance * (CONFIG.RISK_PERCENT / 100);
        const lotSize = Math.max(0.01, Math.min(0.1, riskAmount / 1000)); // 0.01 to 0.1 lots
        
        await openPosition(market.epic, signal.action, lotSize);
        await getPositions();
      }
    }
    
    // Status
    const totalPnl = state.positions.reduce((sum, p) => sum + p.pnl, 0);
    const winRate = state.trades.total > 0 ? (state.trades.wins / state.trades.total * 100) : 0;
    
    console.log(`\n💼 Positions: ${state.positions.length}/${CONFIG.MAX_POSITIONS} | Unrealized: ${state.currency}${totalPnl.toFixed(2)}`);
    console.log(`📊 Trades: ${state.trades.total} (W:${state.trades.wins} L:${state.trades.losses}) | Win Rate: ${winRate.toFixed(0)}% | Realized: ${state.currency}${state.pnl.toFixed(2)}`);
    
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
║   💱 FOREX TRADER - Capital.com 💱                                           ║
║                                                                               ║
║   ███████╗ ██████╗ ██████╗ ███████╗██╗  ██╗                                  ║
║   ██╔════╝██╔═══██╗██╔══██╗██╔════╝╚██╗██╔╝                                  ║
║   █████╗  ██║   ██║██████╔╝█████╗   ╚███╔╝                                   ║
║   ██╔══╝  ██║   ██║██╔══██╗██╔══╝   ██╔██╗                                   ║
║   ██║     ╚██████╔╝██║  ██║███████╗██╔╝ ██╗                                  ║
║   ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝                                  ║
║                                                                               ║
║   Mode: ${CONFIG.IS_DEMO ? 'DEMO (Paper Trading)         ' : '🔴 LIVE TRADING 🔴            '}                              ║
║                                                                               ║
║   Pairs: EUR/USD, GBP/USD, USD/JPY, USD/CHF, AUD/USD, USD/CAD, NZD/USD       ║
║          EUR/GBP, EUR/JPY, GBP/JPY, AUD/JPY, EUR/AUD                         ║
║                                                                               ║
║   Strategy: Mean Reversion                                                    ║
║     • BUY when pair is down ≥ 0.3%                                           ║
║     • SELL when pair is up ≥ 0.3%                                            ║
║     • Take Profit: 30 pips | Stop Loss: 15 pips (2:1 R:R)                    ║
║     • Risk: 1% per trade | Max 3 positions                                   ║
║                                                                               ║
║   Author: Gary Leckey - "Pips don't lie" 🦆                                  ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

  if (!CONFIG.API_KEY || !CONFIG.PASSWORD || !CONFIG.EMAIL) {
    console.log('❌ Missing Capital.com credentials!');
    console.log('');
    console.log('Add to your .env file:');
    console.log('  CAPITAL_API_KEY=your_api_key');
    console.log('  CAPITAL_EMAIL=your_login_email');
    console.log('  CAPITAL_PASSWORD=your_password');
    console.log('  CAPITAL_DEMO=true');
    console.log('');
    console.log('Get API key at: https://capital.com/trading/platform → Settings → API');
    return;
  }
  
  // Login
  if (!await login()) {
    return;
  }
  
  // Get account info
  await getAccountInfo();
  await getPositions();
  
  if (state.positions.length > 0) {
    console.log(`\n📍 Existing positions:`);
    for (const pos of state.positions) {
      console.log(`   ${pos.direction} ${pos.epic}: ${pos.size} lots @ ${pos.openLevel} (PnL: ${state.currency}${pos.pnl.toFixed(2)})`);
    }
  }
  
  console.log(`\n🚀 Starting Forex Trader...`);
  
  // Main loop
  while (true) {
    await tradingCycle();
    await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL));
  }
}

run().catch(console.error);
