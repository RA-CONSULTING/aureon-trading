/**
 * ═══════════════════════════════════════════════════════════════════════════════
 * AUREON QUACKERS FLEET - 12 API KEY BINANCE SYMPHONY
 * ═══════════════════════════════════════════════════════════════════════════════
 * 
 * Master Equation: Λ(t) = S(t) + O(t) + E(t)
 * 12 Quackers | 9 Auris Nodes | Rainbow Bridge | MAXIMUM THROUGHPUT
 * 
 * Author: Gary Leckey
 * Date: November 25, 2025
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

console.log(`
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   🦆 QUACKERS FLEET - 12 BINANCE API KEYS 🦆                                 ║
║                                                                               ║
║   █████╗ ██╗   ██╗██████╗ ███████╗ ██████╗ ███╗   ██╗                        ║
║  ██╔══██╗██║   ██║██╔══██╗██╔════╝██╔═══██╗████╗  ██║                        ║
║  ███████║██║   ██║██████╔╝█████╗  ██║   ██║██╔██╗ ██║                        ║
║  ██╔══██║██║   ██║██╔══██╗██╔══╝  ██║   ██║██║╚██╗██║                        ║
║  ██║  ██║╚██████╔╝██║  ██║███████╗╚██████╔╝██║ ╚████║                        ║
║  ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═══╝                        ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
`);

// ═══════════════════════════════════════════════════════════════════════════════
// API CAPACITY ANALYSIS
// ═══════════════════════════════════════════════════════════════════════════════

const BINANCE_LIMITS = {
  requestsPerMinute: 1200,
  ordersPerSecond: 10,
  ordersPerDay: 200000,
};

console.log(`\n🔑 QUACKERS FLEET STATUS\n${'─'.repeat(60)}`);

keys.forEach((key: any, i: number) => {
  console.log(`  🦆 ${key.name.padEnd(12)} | Key: ${key.apiKey.substring(0, 8)}...${key.apiKey.slice(-4)}`);
});

console.log(`\n${'─'.repeat(60)}`);
console.log(`  📊 Total API Keys: ${keys.length}`);
console.log(`  ⚡ Rate Limit per Key: ${BINANCE_LIMITS.requestsPerMinute}/min`);
console.log(`  🚀 Combined Rate: ${keys.length * BINANCE_LIMITS.requestsPerMinute}/min`);
console.log(`  📈 Orders/sec per Key: ${BINANCE_LIMITS.ordersPerSecond}`);
console.log(`  🎯 Combined Orders/sec: ${keys.length * BINANCE_LIMITS.ordersPerSecond}`);
console.log(`  📅 Orders/day per Key: ${BINANCE_LIMITS.ordersPerDay.toLocaleString()}`);
console.log(`  💎 Combined Orders/day: ${(keys.length * BINANCE_LIMITS.ordersPerDay).toLocaleString()}`);

// ═══════════════════════════════════════════════════════════════════════════════
// TRADING PAIRS DISTRIBUTION
// ═══════════════════════════════════════════════════════════════════════════════

const TRADING_PAIRS = [
  'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
  'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT', 'LINKUSDT', 'LTCUSDT',
];

console.log(`\n\n🎯 PAIR ASSIGNMENT (Round-Robin)\n${'─'.repeat(60)}`);

keys.forEach((key: any, i: number) => {
  const assignedPair = TRADING_PAIRS[i % TRADING_PAIRS.length];
  console.log(`  🦆 ${key.name.padEnd(12)} → ${assignedPair}`);
});

// ═══════════════════════════════════════════════════════════════════════════════
// THEORETICAL CAPACITY
// ═══════════════════════════════════════════════════════════════════════════════

console.log(`\n\n💰 THEORETICAL CAPACITY\n${'─'.repeat(60)}`);

const tradesPerHour = keys.length * BINANCE_LIMITS.ordersPerSecond * 3600 * 0.1; // 10% utilization
const tradesPerDay = tradesPerHour * 24;
const avgProfitPerTrade = 0.015; // 1.5% (our 1.8% TP adjusted for losses)
const startingCapital = 100; // £100 per key

console.log(`  📊 Conservative Trades/Hour: ${tradesPerHour.toLocaleString()}`);
console.log(`  📈 Conservative Trades/Day: ${tradesPerDay.toLocaleString()}`);
console.log(`  💵 Starting Capital: £${(startingCapital * keys.length).toLocaleString()} (£${startingCapital} × ${keys.length})`);
console.log(`  🎯 Avg Profit/Trade (85% WR): ${(avgProfitPerTrade * 100).toFixed(2)}%`);

const dailyROI = Math.pow(1 + avgProfitPerTrade * 0.05, tradesPerDay / keys.length) - 1; // 5% risk per trade
const dailyProfit = startingCapital * keys.length * dailyROI;

console.log(`  📈 Theoretical Daily ROI: ${(dailyROI * 100).toFixed(2)}%`);
console.log(`  💎 Theoretical Daily Profit: £${dailyProfit.toFixed(2)}`);

// ═══════════════════════════════════════════════════════════════════════════════
// CONNECTION TEST
// ═══════════════════════════════════════════════════════════════════════════════

console.log(`\n\n🔌 CONNECTION TEST\n${'─'.repeat(60)}`);

async function testConnection(key: any): Promise<{ name: string; status: string; balances?: any[] }> {
  try {
    const BinanceLib = await import('binance-api-node');
    const client = (BinanceLib as any).default({
      apiKey: key.apiKey,
      apiSecret: key.apiSecret,
    });
    
    const account = await client.accountInfo();
    // Get ALL balances with value > 0
    const balances = account.balances.filter((b: any) => 
      parseFloat(b.free) > 0 || parseFloat(b.locked) > 0
    ).map((b: any) => ({
      asset: b.asset,
      free: parseFloat(b.free),
      locked: parseFloat(b.locked),
      total: parseFloat(b.free) + parseFloat(b.locked)
    }));
    
    return { name: key.name, status: '✅ CONNECTED', balances };
  } catch (error: any) {
    if (error.message.includes('IP')) {
      return { name: key.name, status: '⚠️ IP NOT WHITELISTED' };
    }
    return { name: key.name, status: `❌ ${error.message.substring(0, 30)}` };
  }
}

async function testAllKeys() {
  console.log(`  Testing ${keys.length} API keys...\n`);
  
  let totalPortfolio: { [asset: string]: number } = {};
  let connectedKeys = 0;
  
  for (const key of keys) {
    const result = await testConnection(key);
    console.log(`\n  🦆 ${result.name}`);
    console.log(`     Status: ${result.status}`);
    
    if (result.balances && result.balances.length > 0) {
      connectedKeys++;
      console.log(`     Portfolio:`);
      result.balances.forEach((b: any) => {
        console.log(`       💰 ${b.asset}: ${b.total.toFixed(8)} (Free: ${b.free.toFixed(8)}, Locked: ${b.locked.toFixed(8)})`);
        totalPortfolio[b.asset] = (totalPortfolio[b.asset] || 0) + b.total;
      });
    } else if (result.balances) {
      connectedKeys++;
      console.log(`     Portfolio: Empty`);
    }
  }
  
  console.log(`\n\n${'═'.repeat(60)}`);
  console.log(`  📊 COMBINED PORTFOLIO ACROSS ALL QUACKERS`);
  console.log(`${'═'.repeat(60)}`);
  
  const assets = Object.entries(totalPortfolio).sort((a, b) => b[1] - a[1]);
  if (assets.length > 0) {
    for (const [asset, amount] of assets) {
      console.log(`  💎 ${asset.padEnd(8)}: ${amount.toFixed(8)}`);
    }
  } else {
    console.log(`  No assets found across all accounts`);
  }
  
  console.log(`\n${'─'.repeat(60)}`);
  console.log(`  ✅ Connected: ${connectedKeys}/${keys.length}`);
  
  return { totalPortfolio, connectedKeys };
}

testAllKeys().then(({ totalPortfolio, connectedKeys }) => {
  if (connectedKeys > 0) {
    console.log(`\n\n🚀 READY TO TRADE!`);
    console.log(`   Run: npx tsx scripts/quackersLive.ts`);
  }
});
