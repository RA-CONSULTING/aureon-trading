/**
 * Quick one-shot: market sell all free USDC → USDT
 */
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const keysPath = path.join(__dirname, 'binanceKeys.json');
const { keys } = JSON.parse(fs.readFileSync(keysPath, 'utf-8'));

(async () => {
  const Blib = await import('binance-api-node');
  const Binance = (Blib as any).default?.default || (Blib as any).default || Blib;
  const client = Binance({ apiKey: keys[0].apiKey, apiSecret: keys[0].apiSecret });

  const acct = await client.accountInfo();
  const usdc = acct.balances.find((b: any) => b.asset === 'USDC');
  const free = parseFloat(usdc?.free || '0');
  console.log('USDC available:', free);

  if (free < 5) {
    console.log('Not enough USDC (≥$5 needed). Skipping conversion.');
    process.exit(0);
  }

  const info = await client.exchangeInfo();
  const sym = info.symbols.find((s: any) => s.symbol === 'USDCUSDT');
  const lot = sym.filters.find((f: any) => f.filterType === 'LOT_SIZE');
  const stepSize = parseFloat(lot.stepSize);
  const qty = Math.floor(free / stepSize) * stepSize;

  console.log(`Selling ${qty} USDC → USDT...`);
  const order = await client.order({
    symbol: 'USDCUSDT',
    side: 'SELL',
    type: 'MARKET',
    quantity: qty.toFixed(2),
  });
  const filled = parseFloat(order.executedQty);
  const price = order.fills?.[0]?.price || '1';
  console.log(`✅ Filled: ${filled} USDC @ $${price}`);
  console.log(`Now you have ~$${(filled * parseFloat(price)).toFixed(2)} more USDT.`);
})().catch((e) => console.error('❌', e.message));
