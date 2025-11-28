/**
 * 🧪 TEST ACTUAL TRADE - Find what's permitted
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

async function testTrades() {
  console.log(`\n🧪 TESTING ACTUAL TRADE EXECUTION...\n`);
  
  const BinanceLib = await import('binance-api-node');
  const client = (BinanceLib as any).default({
    apiKey: keys[0].apiKey,
    apiSecret: keys[0].apiSecret,
  });

  // Get exchange info for lot sizes
  const info = await client.exchangeInfo();
  const symbolInfo = new Map();
  for (const s of info.symbols) {
    if (s.quoteAsset === 'USDT') {
      const lot = s.filters.find((f: any) => f.filterType === 'LOT_SIZE');
      symbolInfo.set(s.symbol, {
        minQty: parseFloat(lot?.minQty || '0.001'),
        stepSize: parseFloat(lot?.stepSize || '0.001'),
        status: s.status,
        permissions: s.permissions,
      });
    }
  }

  // Test pairs we have balance for
  const testCases = [
    { symbol: 'DOGEUSDT', asset: 'DOGE', qty: 10 },  // We have 68 DOGE
    { symbol: 'ADAUSDT', asset: 'ADA', qty: 5 },     // We have 24 ADA
    { symbol: 'DOTUSDT', asset: 'DOT', qty: 0.5 },   // We have 4.3 DOT
  ];

  for (const test of testCases) {
    const si = symbolInfo.get(test.symbol);
    console.log(`\n📊 ${test.symbol}:`);
    console.log(`   Status: ${si?.status}`);
    console.log(`   Permissions: ${JSON.stringify(si?.permissions)}`);
    console.log(`   Min Qty: ${si?.minQty}`);
    
    // Try a TEST order (won't execute)
    try {
      const testOrder = await client.orderTest({
        symbol: test.symbol,
        side: 'SELL',
        type: 'MARKET',
        quantity: test.qty.toString(),
      });
      console.log(`   ✅ TEST ORDER PASSED - Can trade this pair!`);
    } catch (e: any) {
      console.log(`   ❌ TEST ORDER FAILED: ${e.message}`);
      
      // Check specific error
      if (e.message.includes('not permitted')) {
        console.log(`   ⚠️  This symbol is RESTRICTED for your account`);
      } else if (e.message.includes('LOT_SIZE')) {
        console.log(`   ⚠️  Quantity issue - try different amount`);
      } else if (e.message.includes('MIN_NOTIONAL')) {
        console.log(`   ⚠️  Trade value too small`);
      }
    }
  }

  // Check if LDUSDC can be used
  console.log(`\n\n📋 CHECKING LDUSDC (Locked USDC)...`);
  console.log(`   LDUSDC is "Locked Savings USDC" - it's in Binance Earn`);
  console.log(`   You need to REDEEM it to USDC first to use for trading`);
  console.log(`   Go to: Binance → Earn → Simple Earn → Redeem LDUSDC`);

  // Find tradeable pairs
  console.log(`\n\n🔍 FINDING ALL PERMITTED PAIRS FOR YOUR ASSETS...`);
  
  const assets = ['BTC', 'ETH', 'BNB', 'LINK', 'XRP', 'ADA', 'DOGE', 'SOL', 'DOT', 'AVAX'];
  const permittedPairs: string[] = [];
  
  for (const asset of assets) {
    const symbol = `${asset}USDT`;
    const si = symbolInfo.get(symbol);
    if (si && si.status === 'TRADING' && si.permissions?.includes('SPOT')) {
      try {
        await client.orderTest({
          symbol,
          side: 'SELL',
          type: 'MARKET',
          quantity: (si.minQty * 10).toString(), // Test with min qty
        });
        permittedPairs.push(symbol);
        console.log(`   ✅ ${symbol} - PERMITTED`);
      } catch (e: any) {
        console.log(`   ❌ ${symbol} - ${e.message.substring(0, 40)}`);
      }
    }
  }

  console.log(`\n${'═'.repeat(60)}`);
  console.log(`\n✅ PERMITTED PAIRS: ${permittedPairs.join(', ')}`);
  console.log(`\nUse these pairs for trading!`);
}

testTrades().catch(console.error);
