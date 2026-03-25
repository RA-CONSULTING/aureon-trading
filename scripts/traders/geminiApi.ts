/**
 * 💎 GEMINI API 💎
 * 
 * Winklevoss twins' regulated crypto exchange
 * Strong UK/EU support, high security
 * 
 * Features:
 * - 100+ crypto pairs
 * - GBP support
 * - Institutional-grade security
 * - SOC 2 Type 2 certified
 * 
 * Author: Gary Leckey - R&A Consulting
 */

import * as crypto from 'crypto';
import * as dotenv from 'dotenv';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  // API Credentials
  API_KEY: process.env.GEMINI_TRADING_KEY || '',
  API_SECRET: process.env.GEMINI_TRADING_SECRET || '',
  
  // API Endpoint
  BASE_URL: process.env.GEMINI_SANDBOX === 'true'
    ? 'https://api.sandbox.gemini.com'
    : 'https://api.gemini.com',
  
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

export interface GeminiTicker {
  bid: string;
  ask: string;
  last: string;
  volume: { [key: string]: string };
}

export interface GeminiBalance {
  type: string;
  currency: string;
  amount: string;
  available: string;
  availableForWithdrawal: string;
}

export interface GeminiOrder {
  order_id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: string;
  price: string;
  original_amount: string;
  executed_amount: string;
  remaining_amount: string;
  avg_execution_price: string;
  is_live: boolean;
  is_cancelled: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Pairs
// ═══════════════════════════════════════════════════════════════════════════

const TRADING_PAIRS = [
  // GBP pairs
  { symbol: 'btcgbp', base: 'BTC', quote: 'GBP', name: 'Bitcoin/GBP' },
  { symbol: 'ethgbp', base: 'ETH', quote: 'GBP', name: 'Ethereum/GBP' },
  
  // USD pairs (main liquidity)
  { symbol: 'btcusd', base: 'BTC', quote: 'USD', name: 'Bitcoin/USD' },
  { symbol: 'ethusd', base: 'ETH', quote: 'USD', name: 'Ethereum/USD' },
  { symbol: 'solusd', base: 'SOL', quote: 'USD', name: 'Solana/USD' },
  { symbol: 'dogeusd', base: 'DOGE', quote: 'USD', name: 'Dogecoin/USD' },
  { symbol: 'maticusd', base: 'MATIC', quote: 'USD', name: 'Polygon/USD' },
  { symbol: 'linkusd', base: 'LINK', quote: 'USD', name: 'Chainlink/USD' },
  { symbol: 'avaxusd', base: 'AVAX', quote: 'USD', name: 'Avalanche/USD' },
  { symbol: 'uniusd', base: 'UNI', quote: 'USD', name: 'Uniswap/USD' },
  { symbol: 'aaveusd', base: 'AAVE', quote: 'USD', name: 'Aave/USD' },
  { symbol: 'ltcusd', base: 'LTC', quote: 'USD', name: 'Litecoin/USD' },
  { symbol: 'filusd', base: 'FIL', quote: 'USD', name: 'Filecoin/USD' },
  { symbol: 'atomusd', base: 'ATOM', quote: 'USD', name: 'Cosmos/USD' },
  { symbol: 'xlmusd', base: 'XLM', quote: 'USD', name: 'Stellar/USD' },
  { symbol: 'manausd', base: 'MANA', quote: 'USD', name: 'Decentraland/USD' },
  { symbol: 'sandusd', base: 'SAND', quote: 'USD', name: 'The Sandbox/USD' },
  { symbol: 'axsusd', base: 'AXS', quote: 'USD', name: 'Axie Infinity/USD' },
  
  // Stablecoins
  { symbol: 'gusd', base: 'GUSD', quote: 'USD', name: 'Gemini Dollar' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Gemini Client
// ═══════════════════════════════════════════════════════════════════════════

class GeminiClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = CONFIG.API_KEY;
    this.apiSecret = CONFIG.API_SECRET;
    this.baseUrl = CONFIG.BASE_URL;
  }

  private generatePayload(request: string, params: any = {}): { payload: string; signature: string } {
    const nonce = Date.now();
    const payload = {
      request,
      nonce,
      ...params,
    };
    
    const encodedPayload = Buffer.from(JSON.stringify(payload)).toString('base64');
    const signature = crypto
      .createHmac('sha384', this.apiSecret)
      .update(encodedPayload)
      .digest('hex');
    
    return { payload: encodedPayload, signature };
  }

  private async publicRequest(endpoint: string): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    try {
      const response = await fetch(url);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Gemini API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Gemini Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  private async privateRequest(endpoint: string, params: any = {}): Promise<any> {
    const { payload, signature } = this.generatePayload(endpoint, params);
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'text/plain',
      'Content-Length': '0',
      'X-GEMINI-APIKEY': this.apiKey,
      'X-GEMINI-PAYLOAD': payload,
      'X-GEMINI-SIGNATURE': signature,
      'Cache-Control': 'no-cache',
    };

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers,
      });
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Gemini API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Gemini Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Public Endpoints
  // ═══════════════════════════════════════════════════════════════════════

  async getSymbols(): Promise<string[]> {
    return this.publicRequest('/v1/symbols');
  }

  async getSymbolDetails(symbol: string): Promise<any> {
    return this.publicRequest(`/v1/symbols/details/${symbol}`);
  }

  async getTicker(symbol: string): Promise<GeminiTicker> {
    return this.publicRequest(`/v1/pubticker/${symbol}`);
  }

  async getTickerV2(symbol: string): Promise<any> {
    return this.publicRequest(`/v2/ticker/${symbol}`);
  }

  async getOrderBook(symbol: string): Promise<any> {
    return this.publicRequest(`/v1/book/${symbol}`);
  }

  async getTradeHistory(symbol: string, limit: number = 50): Promise<any[]> {
    return this.publicRequest(`/v1/trades/${symbol}?limit_trades=${limit}`);
  }

  async getCandles(symbol: string, timeframe: string = '5m'): Promise<any[]> {
    return this.publicRequest(`/v2/candles/${symbol}/${timeframe}`);
  }

  async getPriceFeed(): Promise<any[]> {
    return this.publicRequest('/v1/pricefeed');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account
  // ═══════════════════════════════════════════════════════════════════════

  async getBalances(): Promise<GeminiBalance[]> {
    return this.privateRequest('/v1/balances');
  }

  async getBalance(currency: string): Promise<{ available: number; total: number }> {
    const balances = await this.getBalances();
    const balance = balances.find(b => b.currency.toUpperCase() === currency.toUpperCase());
    
    return {
      available: parseFloat(balance?.available || '0'),
      total: parseFloat(balance?.amount || '0'),
    };
  }

  async getNotionalBalances(currency: string = 'USD'): Promise<any[]> {
    return this.privateRequest('/v1/notionalbalances/' + currency.toLowerCase());
  }

  async getAccountDetail(): Promise<any> {
    return this.privateRequest('/v1/account');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async newOrder(
    symbol: string,
    side: 'buy' | 'sell',
    amount: string,
    price: string,
    type: 'exchange limit' | 'exchange stop limit' = 'exchange limit',
    options: string[] = ['maker-or-cancel']
  ): Promise<GeminiOrder> {
    return this.privateRequest('/v1/order/new', {
      symbol,
      amount,
      price,
      side,
      type,
      options,
    });
  }

  async marketBuy(symbol: string, amount: string): Promise<GeminiOrder> {
    const ticker = await this.getTicker(symbol);
    const price = (parseFloat(ticker.ask) * 1.01).toFixed(2); // 1% above ask
    
    return this.newOrder(symbol, 'buy', amount, price, 'exchange limit', ['immediate-or-cancel']);
  }

  async marketSell(symbol: string, amount: string): Promise<GeminiOrder> {
    const ticker = await this.getTicker(symbol);
    const price = (parseFloat(ticker.bid) * 0.99).toFixed(2); // 1% below bid
    
    return this.newOrder(symbol, 'sell', amount, price, 'exchange limit', ['immediate-or-cancel']);
  }

  async limitBuy(symbol: string, amount: string, price: string): Promise<GeminiOrder> {
    return this.newOrder(symbol, 'buy', amount, price);
  }

  async limitSell(symbol: string, amount: string, price: string): Promise<GeminiOrder> {
    return this.newOrder(symbol, 'sell', amount, price);
  }

  async getOrderStatus(orderId: string): Promise<GeminiOrder> {
    return this.privateRequest('/v1/order/status', { order_id: parseInt(orderId) });
  }

  async getActiveOrders(): Promise<GeminiOrder[]> {
    return this.privateRequest('/v1/orders');
  }

  async cancelOrder(orderId: string): Promise<GeminiOrder> {
    return this.privateRequest('/v1/order/cancel', { order_id: parseInt(orderId) });
  }

  async cancelAllOrders(): Promise<any> {
    return this.privateRequest('/v1/order/cancel/all');
  }

  async cancelSessionOrders(): Promise<any> {
    return this.privateRequest('/v1/order/cancel/session');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Trade History
  // ═══════════════════════════════════════════════════════════════════════

  async getMyTrades(symbol?: string, limit: number = 50): Promise<any[]> {
    const params: any = { limit_trades: limit };
    if (symbol) params.symbol = symbol;
    
    return this.privateRequest('/v1/mytrades', params);
  }

  async getTradeVolume(): Promise<any[]> {
    return this.privateRequest('/v1/tradevolume');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Transfers
  // ═══════════════════════════════════════════════════════════════════════

  async getDepositAddresses(network: string): Promise<any> {
    return this.privateRequest('/v1/addresses/' + network);
  }

  async getTransfers(limit: number = 50): Promise<any[]> {
    return this.privateRequest('/v1/transfers', { limit_transfers: limit });
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class GeminiCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(symbol: string, price: number): void {
    if (!this.priceHistory.has(symbol)) {
      this.priceHistory.set(symbol, []);
    }
    const history = this.priceHistory.get(symbol)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(symbol: string): number {
    const history = this.priceHistory.get(symbol);
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

  getSignal(symbol: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(symbol);
    const history = this.priceHistory.get(symbol);

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

export default GeminiClient;
export {
  GeminiClient,
  GeminiCoherenceEngine,
  TRADING_PAIRS as GEMINI_PAIRS,
  CONFIG as GEMINI_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   💎 GEMINI TRADER 💎                                                         ║
  ║                                                                               ║
  ║   Winklevoss Twins' Exchange • SOC 2 Certified • UK Friendly                  ║
  ║                                                                               ║
  ║   Assets:                                                                     ║
  ║   • BTC, ETH, SOL, DOGE, LINK...                                             ║
  ║   • 100+ Trading Pairs                                                        ║
  ║   • GBP & USD Markets                                                         ║
  ║   • Gemini Dollar (GUSD)                                                      ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Gemini credentials!');
    console.log('\nTo set up Gemini:');
    console.log('1. Create account at https://www.gemini.com');
    console.log('2. Go to Account > API > Create API Key');
    console.log('3. Enable trading permissions');
    console.log('4. Add to .env:');
    console.log('   GEMINI_TRADING_KEY=your_api_key');
    console.log('   GEMINI_TRADING_SECRET=your_api_secret');
    console.log('   GEMINI_SANDBOX=true  # Use sandbox first');
    console.log('\n📖 Docs: https://docs.gemini.com/rest-api/');
    return;
  }

  const client = new GeminiClient();
  const engine = new GeminiCoherenceEngine();

  // Get balances
  const balances = await client.getBalances();
  console.log('\n💰 Account Balances:');
  for (const bal of balances) {
    const available = parseFloat(bal.available);
    if (available > 0) {
      console.log(`   ${bal.currency}: ${available.toFixed(8)}`);
    }
  }

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  setInterval(async () => {
    try {
      for (const pair of TRADING_PAIRS) {
        try {
          const ticker = await client.getTicker(pair.symbol);
          const price = parseFloat(ticker.last);
          
          engine.addPrice(pair.symbol, price);
          
          const signal = engine.getSignal(pair.symbol);
          const coherence = engine.calculateCoherence(pair.symbol);

          if (signal !== 'HOLD' && coherence >= 0.938) {
            const currencySymbol = pair.quote === 'GBP' ? '£' : '$';
            console.log(`
  🎯 SIGNAL: ${signal} ${pair.name}
     Price: ${currencySymbol}${price.toFixed(2)}
     Bid: ${ticker.bid} | Ask: ${ticker.ask}
     Coherence: ${(coherence * 100).toFixed(1)}%
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
const isMainModule = process.argv[1]?.includes('geminiApi');
if (isMainModule) {
  main().catch(console.error);
}
