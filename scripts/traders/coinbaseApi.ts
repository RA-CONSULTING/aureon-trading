/**
 * 🪙 COINBASE ADVANCED TRADE API 🪙
 * 
 * Major crypto exchange with excellent UK support
 * FCA registered, highly regulated
 * 
 * Features:
 * - 200+ crypto pairs
 * - Low fees with Coinbase One
 * - Advanced order types
 * - Portfolio management
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
  // API Credentials (CDP API Key)
  API_KEY: process.env.COINBASE_API_KEY || '',
  API_SECRET: process.env.COINBASE_API_SECRET || '',
  
  // API Endpoint
  BASE_URL: 'https://api.coinbase.com',
  
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

export interface CoinbaseAccount {
  uuid: string;
  name: string;
  currency: string;
  available_balance: { value: string; currency: string };
  hold: { value: string; currency: string };
}

export interface CoinbaseProduct {
  product_id: string;
  price: string;
  price_percentage_change_24h: string;
  volume_24h: string;
  base_currency_id: string;
  quote_currency_id: string;
  status: string;
}

export interface CoinbaseOrder {
  order_id: string;
  product_id: string;
  side: 'BUY' | 'SELL';
  order_type: string;
  status: string;
  size: string;
  filled_size: string;
  average_filled_price: string;
  created_time: string;
}

export interface CoinbasePosition {
  product_id: string;
  side: 'LONG' | 'SHORT';
  size: string;
  entry_price: string;
  current_price: string;
  unrealized_pnl: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Pairs
// ═══════════════════════════════════════════════════════════════════════════

const TRADING_PAIRS = [
  // Major pairs
  { productId: 'BTC-GBP', base: 'BTC', quote: 'GBP', name: 'Bitcoin' },
  { productId: 'ETH-GBP', base: 'ETH', quote: 'GBP', name: 'Ethereum' },
  { productId: 'SOL-GBP', base: 'SOL', quote: 'GBP', name: 'Solana' },
  { productId: 'XRP-GBP', base: 'XRP', quote: 'GBP', name: 'Ripple' },
  { productId: 'ADA-GBP', base: 'ADA', quote: 'GBP', name: 'Cardano' },
  { productId: 'DOGE-GBP', base: 'DOGE', quote: 'GBP', name: 'Dogecoin' },
  { productId: 'DOT-GBP', base: 'DOT', quote: 'GBP', name: 'Polkadot' },
  { productId: 'MATIC-GBP', base: 'MATIC', quote: 'GBP', name: 'Polygon' },
  { productId: 'LINK-GBP', base: 'LINK', quote: 'GBP', name: 'Chainlink' },
  { productId: 'AVAX-GBP', base: 'AVAX', quote: 'GBP', name: 'Avalanche' },
  
  // USD pairs (often more liquid)
  { productId: 'BTC-USD', base: 'BTC', quote: 'USD', name: 'Bitcoin (USD)' },
  { productId: 'ETH-USD', base: 'ETH', quote: 'USD', name: 'Ethereum (USD)' },
  { productId: 'SOL-USD', base: 'SOL', quote: 'USD', name: 'Solana (USD)' },
  
  // DeFi tokens
  { productId: 'UNI-GBP', base: 'UNI', quote: 'GBP', name: 'Uniswap' },
  { productId: 'AAVE-GBP', base: 'AAVE', quote: 'GBP', name: 'Aave' },
  { productId: 'MKR-GBP', base: 'MKR', quote: 'GBP', name: 'Maker' },
  
  // Stablecoins
  { productId: 'USDT-GBP', base: 'USDT', quote: 'GBP', name: 'Tether' },
  { productId: 'USDC-GBP', base: 'USDC', quote: 'GBP', name: 'USD Coin' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Coinbase Advanced Trade Client
// ═══════════════════════════════════════════════════════════════════════════

class CoinbaseClient {
  private apiKey: string;
  private apiSecret: string;
  private baseUrl: string;

  constructor() {
    this.apiKey = CONFIG.API_KEY;
    this.apiSecret = CONFIG.API_SECRET;
    this.baseUrl = CONFIG.BASE_URL;
  }

  private sign(
    timestamp: string,
    method: string,
    path: string,
    body: string = ''
  ): string {
    const message = timestamp + method + path + body;
    const hmac = crypto.createHmac('sha256', this.apiSecret);
    return hmac.update(message).digest('hex');
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const timestamp = Math.floor(Date.now() / 1000).toString();
    const path = `/api/v3/brokerage${endpoint}`;
    const bodyStr = body ? JSON.stringify(body) : '';
    const signature = this.sign(timestamp, method, path, bodyStr);

    const url = `${this.baseUrl}${path}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'CB-ACCESS-KEY': this.apiKey,
      'CB-ACCESS-SIGN': signature,
      'CB-ACCESS-TIMESTAMP': timestamp,
    };

    const options: RequestInit = {
      method,
      headers,
    };

    if (body) {
      options.body = bodyStr;
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Coinbase API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Coinbase Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Accounts
  // ═══════════════════════════════════════════════════════════════════════

  async getAccounts(): Promise<CoinbaseAccount[]> {
    const response = await this.request('/accounts');
    return response.accounts || [];
  }

  async getAccount(accountId: string): Promise<CoinbaseAccount | null> {
    const response = await this.request(`/accounts/${accountId}`);
    return response.account || null;
  }

  async getBalance(currency: string = 'GBP'): Promise<{ available: number; hold: number }> {
    const accounts = await this.getAccounts();
    const account = accounts.find(a => a.currency === currency);
    
    return {
      available: parseFloat(account?.available_balance?.value || '0'),
      hold: parseFloat(account?.hold?.value || '0'),
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Products & Market Data
  // ═══════════════════════════════════════════════════════════════════════

  async getProducts(): Promise<CoinbaseProduct[]> {
    const response = await this.request('/products');
    return response.products || [];
  }

  async getProduct(productId: string): Promise<CoinbaseProduct | null> {
    const response = await this.request(`/products/${productId}`);
    return response || null;
  }

  async getTicker(productId: string): Promise<any> {
    const response = await this.request(`/products/${productId}/ticker`);
    return response;
  }

  async getProductCandles(
    productId: string,
    granularity: 'ONE_MINUTE' | 'FIVE_MINUTE' | 'FIFTEEN_MINUTE' | 'ONE_HOUR' | 'ONE_DAY' = 'FIVE_MINUTE',
    start?: string,
    end?: string
  ): Promise<any[]> {
    let endpoint = `/products/${productId}/candles?granularity=${granularity}`;
    if (start) endpoint += `&start=${start}`;
    if (end) endpoint += `&end=${end}`;
    
    const response = await this.request(endpoint);
    return response.candles || [];
  }

  async getBestBidAsk(productIds: string[]): Promise<any> {
    const ids = productIds.join(',');
    const response = await this.request(`/best_bid_ask?product_ids=${ids}`);
    return response.pricebooks || [];
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async createOrder(
    productId: string,
    side: 'BUY' | 'SELL',
    size: string,
    orderType: 'market' | 'limit' | 'stop_limit' = 'market',
    limitPrice?: string,
    stopPrice?: string
  ): Promise<CoinbaseOrder> {
    const clientOrderId = crypto.randomUUID();
    
    const orderConfig: any = {};
    
    if (orderType === 'market') {
      if (side === 'BUY') {
        orderConfig.market_market_ioc = { quote_size: size };
      } else {
        orderConfig.market_market_ioc = { base_size: size };
      }
    } else if (orderType === 'limit') {
      orderConfig.limit_limit_gtc = {
        base_size: size,
        limit_price: limitPrice,
      };
    } else if (orderType === 'stop_limit') {
      orderConfig.stop_limit_stop_limit_gtc = {
        base_size: size,
        limit_price: limitPrice,
        stop_price: stopPrice,
        stop_direction: side === 'BUY' ? 'STOP_DIRECTION_STOP_UP' : 'STOP_DIRECTION_STOP_DOWN',
      };
    }

    const response = await this.request('/orders', 'POST', {
      client_order_id: clientOrderId,
      product_id: productId,
      side,
      order_configuration: orderConfig,
    });

    return {
      order_id: response.order_id || response.success_response?.order_id,
      product_id: productId,
      side,
      order_type: orderType,
      status: response.order_status || 'PENDING',
      size,
      filled_size: '0',
      average_filled_price: '0',
      created_time: new Date().toISOString(),
    };
  }

  async marketBuy(productId: string, quoteAmount: string): Promise<CoinbaseOrder> {
    return this.createOrder(productId, 'BUY', quoteAmount, 'market');
  }

  async marketSell(productId: string, baseAmount: string): Promise<CoinbaseOrder> {
    return this.createOrder(productId, 'SELL', baseAmount, 'market');
  }

  async limitBuy(productId: string, size: string, price: string): Promise<CoinbaseOrder> {
    return this.createOrder(productId, 'BUY', size, 'limit', price);
  }

  async limitSell(productId: string, size: string, price: string): Promise<CoinbaseOrder> {
    return this.createOrder(productId, 'SELL', size, 'limit', price);
  }

  async getOrder(orderId: string): Promise<CoinbaseOrder | null> {
    const response = await this.request(`/orders/historical/${orderId}`);
    return response.order || null;
  }

  async getOrders(
    productId?: string,
    status?: string[],
    limit: number = 100
  ): Promise<CoinbaseOrder[]> {
    let endpoint = `/orders/historical/batch?limit=${limit}`;
    if (productId) endpoint += `&product_id=${productId}`;
    if (status) endpoint += `&order_status=${status.join(',')}`;
    
    const response = await this.request(endpoint);
    return response.orders || [];
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    try {
      await this.request('/orders/batch_cancel', 'POST', {
        order_ids: [orderId],
      });
      return true;
    } catch {
      return false;
    }
  }

  async cancelAllOrders(productId?: string): Promise<boolean> {
    try {
      const body: any = {};
      if (productId) body.product_id = productId;
      
      await this.request('/orders/batch_cancel', 'POST', body);
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Portfolio & Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getPortfolios(): Promise<any[]> {
    const response = await this.request('/portfolios');
    return response.portfolios || [];
  }

  async getPortfolioBreakdown(portfolioId: string): Promise<any> {
    const response = await this.request(`/portfolios/${portfolioId}`);
    return response;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Fills & Transactions
  // ═══════════════════════════════════════════════════════════════════════

  async getFills(
    productId?: string,
    orderId?: string,
    limit: number = 100
  ): Promise<any[]> {
    let endpoint = `/orders/historical/fills?limit=${limit}`;
    if (productId) endpoint += `&product_id=${productId}`;
    if (orderId) endpoint += `&order_id=${orderId}`;
    
    const response = await this.request(endpoint);
    return response.fills || [];
  }

  async getTransactions(limit: number = 100): Promise<any[]> {
    const response = await this.request(`/transactions?limit=${limit}`);
    return response.transactions || [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class CoinbaseCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(productId: string, price: number): void {
    if (!this.priceHistory.has(productId)) {
      this.priceHistory.set(productId, []);
    }
    const history = this.priceHistory.get(productId)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(productId: string): number {
    const history = this.priceHistory.get(productId);
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

  getSignal(productId: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(productId);
    const history = this.priceHistory.get(productId);

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

export default CoinbaseClient;
export {
  CoinbaseClient,
  CoinbaseCoherenceEngine,
  TRADING_PAIRS as COINBASE_PAIRS,
  CONFIG as COINBASE_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🪙 COINBASE ADVANCED TRADE 🪙                                               ║
  ║                                                                               ║
  ║   FCA Registered • UK Supported • Regulated Exchange                          ║
  ║                                                                               ║
  ║   Assets:                                                                     ║
  ║   • BTC, ETH, SOL, XRP, ADA, DOGE...                                         ║
  ║   • 200+ Trading Pairs                                                        ║
  ║   • GBP & USD Markets                                                         ║
  ║   • DeFi Tokens                                                               ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET) {
    console.log('❌ Missing Coinbase credentials!');
    console.log('\nTo set up Coinbase:');
    console.log('1. Create account at https://www.coinbase.com');
    console.log('2. Go to Settings > API > New API Key');
    console.log('3. Create a CDP API Key with trading permissions');
    console.log('4. Add to .env:');
    console.log('   COINBASE_API_KEY=your_api_key');
    console.log('   COINBASE_API_SECRET=your_api_secret');
    console.log('\n📖 Docs: https://docs.cdp.coinbase.com/advanced-trade/docs/welcome');
    return;
  }

  const client = new CoinbaseClient();
  const engine = new CoinbaseCoherenceEngine();

  // Get balance
  const balance = await client.getBalance('GBP');
  console.log(`\n💰 GBP Balance: £${balance.available.toFixed(2)}`);
  console.log(`🔒 On Hold: £${balance.hold.toFixed(2)}`);

  // Get accounts overview
  const accounts = await client.getAccounts();
  const nonZeroAccounts = accounts.filter(a => 
    parseFloat(a.available_balance?.value || '0') > 0
  );
  
  console.log(`\n📊 Active Accounts: ${nonZeroAccounts.length}`);
  for (const acc of nonZeroAccounts.slice(0, 5)) {
    console.log(`   ${acc.currency}: ${parseFloat(acc.available_balance.value).toFixed(6)}`);
  }

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  const productIds = TRADING_PAIRS.map(p => p.productId);

  setInterval(async () => {
    try {
      for (const pair of TRADING_PAIRS) {
        try {
          const ticker = await client.getTicker(pair.productId);
          const price = parseFloat(ticker.price);
          
          engine.addPrice(pair.productId, price);
          
          const signal = engine.getSignal(pair.productId);
          const coherence = engine.calculateCoherence(pair.productId);

          if (signal !== 'HOLD' && coherence >= 0.938) {
            console.log(`
  🎯 SIGNAL: ${signal} ${pair.name} (${pair.productId})
     Price: ${pair.quote === 'GBP' ? '£' : '$'}${price.toFixed(2)}
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
const isMainModule = process.argv[1]?.includes('coinbaseApi');
if (isMainModule) {
  main().catch(console.error);
}
