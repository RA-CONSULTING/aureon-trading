/**
 * 🧪 TEST WITH CORRECT NOTIONAL VALUES
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

async function testNotional() {
  console.log(`\n🧪 TESTING WITH CORRECT NOTIONAL VALUES...\n`);
  
  const BinanceLib = await import('binance-api-node');
  const client = (BinanceLib as any).default({
    apiKey: keys[0].apiKey,
    apiSecret: keys[0].apiSecret,
  });

  // Get exchange info
  const info = await client.exchangeInfo();
  
  // Get prices
  const prices = await client.prices();

  // Test each asset we own
  const holdings = [
    { asset: 'DOGE', balance: 68.04 },
    { asset: 'ADA', balance: 24.30 },
    { asset: 'DOT', balance: 4.36 },
    { asset: 'LINK', balance: 0.79 },
    { asset: 'BNB', balance: 0.011 },
    { asset: 'XRP', balance: 0.087 },
    { asset: 'BTC', balance: 0.000385 },
  ];

  console.log(`📊 CHECKING EACH HOLDING:\n`);

  for (const h of holdings) {
    const symbol = `${h.asset}USDT`;
    const price = parseFloat(prices[symbol] || '0');
    const totalValue = h.balance * price;
    
    // Get symbol filters
    const symbolData = info.symbols.find((s: any) => s.symbol === symbol);
    if (!symbolData) continue;

    const lotSize = symbolData.filters.find((f: any) => f.filterType === 'LOT_SIZE');
    const notional = symbolData.filters.find((f: any) => f.filterType === 'NOTIONAL');
    
    const minNotional = parseFloat(notional?.minNotional || '5');
    const minQty = parseFloat(lotSize?.minQty || '1');
    const stepSize = parseFloat(lotSize?.stepSize || '1');

    console.log(`${h.asset}USDT:`);
    console.log(`   Price: $${price.toFixed(6)}`);
    console.log(`   You have: ${h.balance} = $${totalValue.toFixed(2)}`);
    console.log(`   Min Notional: $${minNotional}`);
    console.log(`   Min Qty: ${minQty}`);
    console.log(`   Step Size: ${stepSize}`);

    // Calculate tradeable quantity
    const minQtyForNotional = minNotional / price;
    const canTrade = totalValue >= minNotional;

    if (canTrade) {
      // Calculate how much we can trade
      const tradeQty = Math.max(minQtyForNotional, minQty);
      const roundedQty = Math.floor(h.balance * 0.5 / stepSize) * stepSize; // 50% of holding
      
      console.log(`   ✅ CAN TRADE - ${roundedQty.toFixed(8)} ${h.asset} = $${(roundedQty * price).toFixed(2)}`);
      
      // Test order
      try {
        await client.orderTest({
          symbol,
          side: 'SELL',
          type: 'MARKET',
          quantity: roundedQty.toFixed(8),
        });
        console.log(`   ✅ TEST ORDER PASSED!\n`);
      } catch (e: any) {
        console.log(`   ❌ TEST FAILED: ${e.message}\n`);
      }
    } else {
      console.log(`   ❌ CANNOT TRADE - Need $${minNotional}, have $${totalValue.toFixed(2)}\n`);
    }
  }

  // Summary
  console.log(`\n${'═'.repeat(60)}`);
  console.log(`\n📋 SUMMARY:`);
  console.log(`   Your LDUSDC ($36.27) is in Binance Earn - REDEEM it first!`);
  console.log(`   Most holdings are below minimum trade value ($5-10)`);
  console.log(`   DOGE ($27) and ADA ($22) can be traded!`);
}

testNotional().catch(console.error);
