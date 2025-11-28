/**
 * 🏛️ BITSTAMP API 🏛️
 * 
 * The oldest crypto exchange (since 2011)
 * Highly regulated, UK-friendly
 * 
 * Features:
 * - Major crypto pairs
 * - GBP & EUR support
 * - Low fees
 * - High liquidity
 * - Excellent API
 * 
 * Author: Gary Leckey - R&A Consulting
 */

import * as crypto from 'crypto';
import * as dotenv from 'dotenv';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { v4 as uuidv4 } from 'uuid';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // API Credentials
  API_KEY: process.env.BITSTAMP_API_KEY || '',
  API_SECRET: process.env.BITSTAMP_API_SECRET || '',
  
  // API Endpoint
  BASE_URL: 'https://www.bitstamp.net/api/v2',
  
  // Trading settings
  RISK_PERCENT: 2,
  TAKE_PROFIT: 3.0,
  STOP_LOSS: 1.5,
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 10,
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface BitstampTicker {
  last: string;
  high: string;
  low: string;
  vwap: string;
  volume: string;
  bid: string;
  ask: string;
  timestamp: string;
  open: string;
  percent_change_24: string;
}

export interface BitstampBalance {
  available: string;
  balance: string;
  reserved: string;
  currency: string;
}

export interface BitstampOrder {
  id: string;
  datetime: string;
  type: '0' | '1'; // 0 = buy, 1 = sell
  price: string;
  amount: string;
  currency_pair: string;
  status: string;
}

export interface BitstampTrade {
  id: string;
  type: '0' | '1';
  datetime: string;
  price: string;
  amount: string;
  fee: string;
  order_id: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Pairs
// ═══════════════════════════════════════════════════════════════════════════

const TRADING_PAIRS = [
  // GBP pairs
  { pair: 'btcgbp', base: 'BTC', quote: 'GBP', name: 'Bitcoin/GBP' },
  { pair: 'ethgbp', base: 'ETH', quote: 'GBP', name: 'Ethereum/GBP' },
  { pair: 'xrpgbp', base: 'XRP', quote: 'GBP', name: 'Ripple/GBP' },
  { pair: 'ltcgbp', base: 'LTC', quote: 'GBP', name: 'Litecoin/GBP' },
  { pair: 'linkgbp', base: 'LINK', quote: 'GBP', name: 'Chainlink/GBP' },
  
  // USD pairs (more liquid)
  { pair: 'btcusd', base: 'BTC', quote: 'USD', name: 'Bitcoin/USD' },
  { pair: 'ethusd', base: 'ETH', quote: 'USD', name: 'Ethereum/USD' },
  { pair: 'solusd', base: 'SOL', quote: 'USD', name: 'Solana/USD' },
  { pair: 'xrpusd', base: 'XRP', quote: 'USD', name: 'Ripple/USD' },
  { pair: 'adausd', base: 'ADA', quote: 'USD', name: 'Cardano/USD' },
  { pair: 'dogeusd', base: 'DOGE', quote: 'USD', name: 'Dogecoin/USD' },
  { pair: 'dotusd', base: 'DOT', quote: 'USD', name: 'Polkadot/USD' },
  { pair: 'avaxusd', base: 'AVAX', quote: 'USD', name: 'Avalanche/USD' },
  { pair: 'maticusd', base: 'MATIC', quote: 'USD', name: 'Polygon/USD' },
  { pair: 'linkusd', base: 'LINK', quote: 'USD', name: 'Chainlink/USD' },
  { pair: 'uniusd', base: 'UNI', quote: 'USD', name: 'Uniswap/USD' },
  { pair: 'aaveusd', base: 'AAVE', quote: 'USD', name: 'Aave/USD' },
  { pair: 'ltcusd', base: 'LTC', quote: 'USD', name: 'Litecoin/USD' },
  
  // EUR pairs
  { pair: 'btceur', base: 'BTC', quote: 'EUR', name: 'Bitcoin/EUR' },
  { pair: 'etheur', base: 'ETH', quote: 'EUR', name: 'Ethereum/EUR' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Bitstamp Client
// ═══════════════════════════════════════════════════════════════════════════

class BitstampClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = CONFIG.API_KEY;
    this.apiSecret = CONFIG.API_SECRET;
    this.baseUrl = CONFIG.BASE_URL;
  }

  private generateSignature(
    nonce: string,
    timestamp: string,
    method: string,
    path: string,
    contentType: string = '',
    body: string = ''
  ): string {
    const message = `BITSTAMP ${this.apiKey}${method}www.bitstamp.net${path}${contentType}${nonce}${timestamp}v2${body}`;
    const hmac = crypto.createHmac('sha256', this.apiSecret);
    return hmac.update(message).digest('hex').toUpperCase();
  }

  private async publicRequest(endpoint: string): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Bitstamp API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Bitstamp Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  private async privateRequest(
    endpoint: string,
    method: 'POST' | 'GET' = 'POST',
    params: Record<string, string> = {}
  ): Promise<any> {
    const nonce = uuidv4();
    const timestamp = Date.now().toString();
    const path = `/api/v2${endpoint}/`;
    const contentType = 'application/x-www-form-urlencoded';
    
    const body = new URLSearchParams(params).toString();
    const signature = this.generateSignature(nonce, timestamp, method, path, contentType, body);

    const url = `${this.baseUrl}${endpoint}/`;
    
    const headers: Record<string, string> = {
      'Content-Type': contentType,
      'X-Auth': `BITSTAMP ${this.apiKey}`,
      'X-Auth-Signature': signature,
      'X-Auth-Nonce': nonce,
      'X-Auth-Timestamp': timestamp,
      'X-Auth-Version': 'v2',
    };

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: body || undefined,
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Bitstamp API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Bitstamp Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Public Endpoints
  // ═══════════════════════════════════════════════════════════════════════

  async getTicker(pair: string): Promise<BitstampTicker> {
    return this.publicRequest(`/ticker/${pair}/`);
  }

  async getTickerHourly(pair: string): Promise<BitstampTicker> {
    return this.publicRequest(`/ticker_hour/${pair}/`);
  }

  async getOrderBook(pair: string): Promise<any> {
    return this.publicRequest(`/order_book/${pair}/`);
  }

  async getTransactions(pair: string, time: 'minute' | 'hour' | 'day' = 'hour'): Promise<any[]> {
    return this.publicRequest(`/transactions/${pair}/?time=${time}`);
  }

  async getTradingPairsInfo(): Promise<any[]> {
    return this.publicRequest('/trading-pairs-info/');
  }

  async getOHLC(
    pair: string,
    step: number = 60, // seconds: 60, 180, 300, 900, 1800, 3600, 7200, 14400, 21600, 43200, 86400
    limit: number = 100
  ): Promise<any> {
    return this.publicRequest(`/ohlc/${pair}/?step=${step}&limit=${limit}`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account
  // ═══════════════════════════════════════════════════════════════════════

  async getBalance(): Promise<Record<string, BitstampBalance>> {
    const response = await this.privateRequest('/balance');
    
    const balances: Record<string, BitstampBalance> = {};
    const currencies = ['gbp', 'usd', 'eur', 'btc', 'eth', 'xrp', 'ltc', 'sol', 'ada', 'doge'];
    
    for (const currency of currencies) {
      balances[currency.toUpperCase()] = {
        available: response[`${currency}_available`] || '0',
        balance: response[`${currency}_balance`] || '0',
        reserved: response[`${currency}_reserved`] || '0',
        currency: currency.toUpperCase(),
      };
    }
    
    return balances;
  }

  async getAccountBalance(currency: string = 'GBP'): Promise<{ available: number; total: number }> {
    const balances = await this.getBalance();
    const bal = balances[currency.toUpperCase()];
    
    return {
      available: parseFloat(bal?.available || '0'),
      total: parseFloat(bal?.balance || '0'),
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async buyMarketOrder(pair: string, amount: string): Promise<BitstampOrder> {
    return this.privateRequest(`/buy/market/${pair}`, 'POST', { amount });
  }

  async sellMarketOrder(pair: string, amount: string): Promise<BitstampOrder> {
    return this.privateRequest(`/sell/market/${pair}`, 'POST', { amount });
  }

  async buyLimitOrder(pair: string, amount: string, price: string): Promise<BitstampOrder> {
    return this.privateRequest(`/buy/${pair}`, 'POST', { amount, price });
  }

  async sellLimitOrder(pair: string, amount: string, price: string): Promise<BitstampOrder> {
    return this.privateRequest(`/sell/${pair}`, 'POST', { amount, price });
  }

  async buyInstantOrder(pair: string, amount: string): Promise<BitstampOrder> {
    return this.privateRequest(`/buy/instant/${pair}`, 'POST', { amount });
  }

  async sellInstantOrder(pair: string, amount: string): Promise<BitstampOrder> {
    return this.privateRequest(`/sell/instant/${pair}`, 'POST', { amount });
  }

  async getOpenOrders(pair?: string): Promise<BitstampOrder[]> {
    const endpoint = pair ? `/open_orders/${pair}` : '/open_orders/all';
    return this.privateRequest(endpoint);
  }

  async getOrderStatus(orderId: string): Promise<any> {
    return this.privateRequest('/order_status', 'POST', { id: orderId });
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    try {
      await this.privateRequest('/cancel_order', 'POST', { id: orderId });
      return true;
    } catch {
      return false;
    }
  }

  async cancelAllOrders(pair?: string): Promise<boolean> {
    try {
      const endpoint = pair ? `/cancel_all_orders/${pair}` : '/cancel_all_orders';
      await this.privateRequest(endpoint);
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Trade History
  // ═══════════════════════════════════════════════════════════════════════

  async getUserTransactions(
    pair?: string,
    offset: number = 0,
    limit: number = 100
  ): Promise<BitstampTrade[]> {
    const endpoint = pair ? `/user_transactions/${pair}` : '/user_transactions';
    return this.privateRequest(endpoint, 'POST', {
      offset: offset.toString(),
      limit: limit.toString(),
    });
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Withdrawal & Deposit
  // ═══════════════════════════════════════════════════════════════════════

  async getDepositAddress(currency: string): Promise<any> {
    return this.privateRequest(`/${currency.toLowerCase()}_address`);
  }

  async getWithdrawalRequests(): Promise<any[]> {
    return this.privateRequest('/withdrawal_requests');
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class BitstampCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(pair: string, price: number): void {
    if (!this.priceHistory.has(pair)) {
      this.priceHistory.set(pair, []);
    }
    const history = this.priceHistory.get(pair)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(pair: string): number {
    const history = this.priceHistory.get(pair);
    if (!history || history.length < 10) return 0;

    const recent = history.slice(-20);
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    if (range === 0) return 0.5;

    const current = recent[recent.length - 1];
    const normalized = (current - min) / range;

    const phiMajorDist = Math.abs(normalized - (1 / this.PHI));
    const phiMinorDist = Math.abs(normalized - (this.PHI - 1));
    const phiScore = 1 - Math.min(phiMajorDist, phiMinorDist);

    const momentum = (current - recent[0]) / recent[0];
    const momentumScore = Math.tanh(momentum * 50) * 0.5 + 0.5;

    const wavePosition = Math.sin(normalized * Math.PI) ** 2;

    return phiScore * 0.4 + momentumScore * 0.3 + wavePosition * 0.3;
  }

  getSignal(pair: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(pair);
    const history = this.priceHistory.get(pair);

    if (!history || history.length < 5) return 'HOLD';

    const trend = history[history.length - 1] > history[history.length - 5] ? 1 : -1;

    if (coherence >= 0.938 && trend > 0) return 'BUY';
    if (coherence >= 0.938 && trend < 0) return 'SELL';

    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Export
// ═══════════════════════════════════════════════════════════════════════════

export default BitstampClient;
export {
  BitstampClient,
  BitstampCoherenceEngine,
  TRADING_PAIRS as BITSTAMP_PAIRS,
  CONFIG as BITSTAMP_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🏛️ BITSTAMP TRADER 🏛️                                                      ║
  ║                                                                               ║
  ║   The Oldest Exchange (Since 2011) • Highly Regulated • UK Friendly           ║
  ║                                                                               ║
  ║   Assets:                                                                     ║
  ║   • BTC, ETH, SOL, XRP, ADA, LTC...                                          ║
  ║   • GBP, USD, EUR Markets                                                     ║
  ║   • High Liquidity                                                            ║
  ║   • Low Fees                                                                  ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Bitstamp credentials!');
    console.log('\nTo set up Bitstamp:');
    console.log('1. Create account at https://www.bitstamp.net');
    console.log('2. Go to Settings > API Access > New API Key');
    console.log('3. Enable trading permissions');
    console.log('4. Add to .env:');
    console.log('   BITSTAMP_API_KEY=your_api_key');
    console.log('   BITSTAMP_API_SECRET=your_api_secret');
    console.log('\n📖 Docs: https://www.bitstamp.net/api/');
    return;
  }

  const client = new BitstampClient();
  const engine = new BitstampCoherenceEngine();

  // Get balance
  const balance = await client.getAccountBalance('GBP');
  console.log(`\n💰 GBP Balance: £${balance.available.toFixed(2)}`);
  console.log(`📊 Total: £${balance.total.toFixed(2)}`);

  // Get all balances
  const allBalances = await client.getBalance();
  console.log('\n📈 Crypto Holdings:');
  for (const [currency, bal] of Object.entries(allBalances)) {
    const available = parseFloat(bal.available);
    if (available > 0 && !['GBP', 'USD', 'EUR'].includes(currency)) {
      console.log(`   ${currency}: ${available.toFixed(8)}`);
    }
  }

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  setInterval(async () => {
    try {
      for (const pair of TRADING_PAIRS) {
        try {
          const ticker = await client.getTicker(pair.pair);
          const price = parseFloat(ticker.last);
          
          engine.addPrice(pair.pair, price);
          
          const signal = engine.getSignal(pair.pair);
          const coherence = engine.calculateCoherence(pair.pair);

          if (signal !== 'HOLD' && coherence >= 0.938) {
            const currencySymbol = pair.quote === 'GBP' ? '£' : pair.quote === 'EUR' ? '€' : '$';
            console.log(`
  🎯 SIGNAL: ${signal} ${pair.name}
     Price: ${currencySymbol}${price.toFixed(2)}
     Coherence: ${(coherence * 100).toFixed(1)}%
     24h Change: ${ticker.percent_change_24}%
            `);
          }
        } catch (err) {
          // Skip unavailable pairs
        }
      }
    } catch (error) {
      console.error('Trading loop error:', error);
    }
  }, CONFIG.SCAN_INTERVAL);
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('bitstampApi');
if (isMainModule) {
  main().catch(console.error);
}
