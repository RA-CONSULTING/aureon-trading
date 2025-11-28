/**
 * 🌐 OKX API 🌐
 * 
 * Major global crypto exchange
 * Good UK support, high liquidity
 * 
 * Features:
 * - 350+ trading pairs
 * - Spot, Margin, Futures, Options
 * - Low fees
 * - Advanced trading features
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
  API_KEY: process.env.OKX_API_KEY || '',
  API_SECRET: process.env.OKX_API_SECRET || '',
  PASSPHRASE: process.env.OKX_PASSPHRASE || '',
  
  // API Endpoint
  BASE_URL: process.env.OKX_DEMO === 'true'
    ? 'https://www.okx.com'  // Demo flag in header
    : 'https://www.okx.com',
  
  // Demo mode
  IS_DEMO: process.env.OKX_DEMO === 'true',
  
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

export interface OKXTicker {
  instId: string;
  last: string;
  lastSz: string;
  askPx: string;
  askSz: string;
  bidPx: string;
  bidSz: string;
  open24h: string;
  high24h: string;
  low24h: string;
  vol24h: string;
  ts: string;
}

export interface OKXBalance {
  ccy: string;
  bal: string;
  availBal: string;
  frozenBal: string;
}

export interface OKXOrder {
  ordId: string;
  clOrdId: string;
  instId: string;
  side: 'buy' | 'sell';
  ordType: string;
  sz: string;
  px: string;
  state: string;
  fillPx: string;
  fillSz: string;
  avgPx: string;
  pnl: string;
  cTime: string;
}

export interface OKXPosition {
  instId: string;
  posSide: 'long' | 'short' | 'net';
  pos: string;
  availPos: string;
  avgPx: string;
  upl: string;
  uplRatio: string;
  lever: string;
  liqPx: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Pairs
// ═══════════════════════════════════════════════════════════════════════════

const TRADING_PAIRS = [
  // Major pairs (USDT)
  { instId: 'BTC-USDT', base: 'BTC', quote: 'USDT', name: 'Bitcoin' },
  { instId: 'ETH-USDT', base: 'ETH', quote: 'USDT', name: 'Ethereum' },
  { instId: 'SOL-USDT', base: 'SOL', quote: 'USDT', name: 'Solana' },
  { instId: 'XRP-USDT', base: 'XRP', quote: 'USDT', name: 'Ripple' },
  { instId: 'DOGE-USDT', base: 'DOGE', quote: 'USDT', name: 'Dogecoin' },
  { instId: 'ADA-USDT', base: 'ADA', quote: 'USDT', name: 'Cardano' },
  { instId: 'AVAX-USDT', base: 'AVAX', quote: 'USDT', name: 'Avalanche' },
  { instId: 'DOT-USDT', base: 'DOT', quote: 'USDT', name: 'Polkadot' },
  { instId: 'MATIC-USDT', base: 'MATIC', quote: 'USDT', name: 'Polygon' },
  { instId: 'LINK-USDT', base: 'LINK', quote: 'USDT', name: 'Chainlink' },
  { instId: 'UNI-USDT', base: 'UNI', quote: 'USDT', name: 'Uniswap' },
  { instId: 'ATOM-USDT', base: 'ATOM', quote: 'USDT', name: 'Cosmos' },
  { instId: 'LTC-USDT', base: 'LTC', quote: 'USDT', name: 'Litecoin' },
  { instId: 'FIL-USDT', base: 'FIL', quote: 'USDT', name: 'Filecoin' },
  { instId: 'NEAR-USDT', base: 'NEAR', quote: 'USDT', name: 'Near Protocol' },
  { instId: 'APT-USDT', base: 'APT', quote: 'USDT', name: 'Aptos' },
  { instId: 'ARB-USDT', base: 'ARB', quote: 'USDT', name: 'Arbitrum' },
  { instId: 'OP-USDT', base: 'OP', quote: 'USDT', name: 'Optimism' },
  
  // BTC pairs
  { instId: 'ETH-BTC', base: 'ETH', quote: 'BTC', name: 'ETH/BTC' },
  { instId: 'SOL-BTC', base: 'SOL', quote: 'BTC', name: 'SOL/BTC' },
  
  // USDC pairs
  { instId: 'BTC-USDC', base: 'BTC', quote: 'USDC', name: 'Bitcoin/USDC' },
  { instId: 'ETH-USDC', base: 'ETH', quote: 'USDC', name: 'Ethereum/USDC' },
];

// ═══════════════════════════════════════════════════════════════════════════
// OKX Client
// ═══════════════════════════════════════════════════════════════════════════

class OKXClient {
  private apiKey: string;
  private apiSecret: string;
  private passphrase: string;
  private baseUrl: string;
  private isDemo: boolean;

  constructor() {
    this.apiKey = CONFIG.API_KEY;
    this.apiSecret = CONFIG.API_SECRET;
    this.passphrase = CONFIG.PASSPHRASE;
    this.baseUrl = CONFIG.BASE_URL;
    this.isDemo = CONFIG.IS_DEMO;
  }

  private sign(timestamp: string, method: string, path: string, body: string = ''): string {
    const message = timestamp + method + path + body;
    const hmac = crypto.createHmac('sha256', this.apiSecret);
    return hmac.update(message).digest('base64');
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' = 'GET',
    body?: any,
    isPrivate: boolean = false
  ): Promise<any> {
    const timestamp = new Date().toISOString();
    const path = `/api/v5${endpoint}`;
    const bodyStr = body ? JSON.stringify(body) : '';
    
    const url = `${this.baseUrl}${path}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (isPrivate) {
      const signature = this.sign(timestamp, method, path, bodyStr);
      headers['OK-ACCESS-KEY'] = this.apiKey;
      headers['OK-ACCESS-SIGN'] = signature;
      headers['OK-ACCESS-TIMESTAMP'] = timestamp;
      headers['OK-ACCESS-PASSPHRASE'] = this.passphrase;
      
      if (this.isDemo) {
        headers['x-simulated-trading'] = '1';
      }
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (body) {
      options.body = bodyStr;
    }

    try {
      const response = await fetch(url, options);
      const data = await response.json();
      
      if (data.code !== '0') {
        throw new Error(`OKX API Error: ${data.code} - ${data.msg}`);
      }

      return data.data;
    } catch (error) {
      console.error(`OKX Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Public Endpoints
  // ═══════════════════════════════════════════════════════════════════════

  async getInstruments(instType: 'SPOT' | 'MARGIN' | 'SWAP' | 'FUTURES' = 'SPOT'): Promise<any[]> {
    return this.request(`/public/instruments?instType=${instType}`);
  }

  async getTicker(instId: string): Promise<OKXTicker> {
    const data = await this.request(`/market/ticker?instId=${instId}`);
    return data[0];
  }

  async getTickers(instType: 'SPOT' | 'SWAP' = 'SPOT'): Promise<OKXTicker[]> {
    return this.request(`/market/tickers?instType=${instType}`);
  }

  async getOrderBook(instId: string, depth: number = 20): Promise<any> {
    const data = await this.request(`/market/books?instId=${instId}&sz=${depth}`);
    return data[0];
  }

  async getCandles(
    instId: string,
    bar: string = '5m',
    limit: number = 100
  ): Promise<any[]> {
    return this.request(`/market/candles?instId=${instId}&bar=${bar}&limit=${limit}`);
  }

  async getTrades(instId: string, limit: number = 100): Promise<any[]> {
    return this.request(`/market/trades?instId=${instId}&limit=${limit}`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account
  // ═══════════════════════════════════════════════════════════════════════

  async getBalance(ccy?: string): Promise<OKXBalance[]> {
    let endpoint = '/account/balance';
    if (ccy) endpoint += `?ccy=${ccy}`;
    
    const data = await this.request(endpoint, 'GET', undefined, true);
    return data[0]?.details || [];
  }

  async getAccountBalance(currency: string = 'USDT'): Promise<{ available: number; total: number }> {
    const balances = await this.getBalance(currency);
    const balance = balances.find(b => b.ccy === currency);
    
    return {
      available: parseFloat(balance?.availBal || '0'),
      total: parseFloat(balance?.bal || '0'),
    };
  }

  async getAccountConfig(): Promise<any> {
    const data = await this.request('/account/config', 'GET', undefined, true);
    return data[0];
  }

  async getPositions(instType?: string, instId?: string): Promise<OKXPosition[]> {
    let endpoint = '/account/positions';
    const params: string[] = [];
    if (instType) params.push(`instType=${instType}`);
    if (instId) params.push(`instId=${instId}`);
    if (params.length) endpoint += `?${params.join('&')}`;
    
    return this.request(endpoint, 'GET', undefined, true);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async placeOrder(
    instId: string,
    side: 'buy' | 'sell',
    sz: string,
    ordType: 'market' | 'limit' | 'post_only' | 'fok' | 'ioc' = 'market',
    px?: string,
    tdMode: 'cash' | 'cross' | 'isolated' = 'cash'
  ): Promise<OKXOrder> {
    const body: any = {
      instId,
      tdMode,
      side,
      ordType,
      sz,
    };

    if (ordType === 'limit' && px) {
      body.px = px;
    }

    const data = await this.request('/trade/order', 'POST', body, true);
    return data[0];
  }

  async marketBuy(instId: string, sz: string): Promise<OKXOrder> {
    return this.placeOrder(instId, 'buy', sz, 'market');
  }

  async marketSell(instId: string, sz: string): Promise<OKXOrder> {
    return this.placeOrder(instId, 'sell', sz, 'market');
  }

  async limitBuy(instId: string, sz: string, px: string): Promise<OKXOrder> {
    return this.placeOrder(instId, 'buy', sz, 'limit', px);
  }

  async limitSell(instId: string, sz: string, px: string): Promise<OKXOrder> {
    return this.placeOrder(instId, 'sell', sz, 'limit', px);
  }

  async getOrder(instId: string, ordId?: string, clOrdId?: string): Promise<OKXOrder> {
    let endpoint = `/trade/order?instId=${instId}`;
    if (ordId) endpoint += `&ordId=${ordId}`;
    if (clOrdId) endpoint += `&clOrdId=${clOrdId}`;
    
    const data = await this.request(endpoint, 'GET', undefined, true);
    return data[0];
  }

  async getPendingOrders(instType?: string, instId?: string): Promise<OKXOrder[]> {
    let endpoint = '/trade/orders-pending';
    const params: string[] = [];
    if (instType) params.push(`instType=${instType}`);
    if (instId) params.push(`instId=${instId}`);
    if (params.length) endpoint += `?${params.join('&')}`;
    
    return this.request(endpoint, 'GET', undefined, true);
  }

  async getOrderHistory(
    instType: 'SPOT' | 'MARGIN' | 'SWAP' = 'SPOT',
    instId?: string,
    limit: number = 100
  ): Promise<OKXOrder[]> {
    let endpoint = `/trade/orders-history-archive?instType=${instType}&limit=${limit}`;
    if (instId) endpoint += `&instId=${instId}`;
    
    return this.request(endpoint, 'GET', undefined, true);
  }

  async cancelOrder(instId: string, ordId?: string, clOrdId?: string): Promise<any> {
    const body: any = { instId };
    if (ordId) body.ordId = ordId;
    if (clOrdId) body.clOrdId = clOrdId;
    
    const data = await this.request('/trade/cancel-order', 'POST', body, true);
    return data[0];
  }

  async cancelAllOrders(instType: 'SPOT' | 'MARGIN' | 'SWAP' = 'SPOT'): Promise<any> {
    // Get pending orders first
    const orders = await this.getPendingOrders(instType);
    const results = [];
    
    for (const order of orders) {
      try {
        const result = await this.cancelOrder(order.instId, order.ordId);
        results.push(result);
      } catch (err) {
        console.error(`Failed to cancel order ${order.ordId}`);
      }
    }
    
    return results;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Fills & Trades
  // ═══════════════════════════════════════════════════════════════════════

  async getFills(
    instType: 'SPOT' | 'MARGIN' | 'SWAP' = 'SPOT',
    instId?: string,
    limit: number = 100
  ): Promise<any[]> {
    let endpoint = `/trade/fills-history?instType=${instType}&limit=${limit}`;
    if (instId) endpoint += `&instId=${instId}`;
    
    return this.request(endpoint, 'GET', undefined, true);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class OKXCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(instId: string, price: number): void {
    if (!this.priceHistory.has(instId)) {
      this.priceHistory.set(instId, []);
    }
    const history = this.priceHistory.get(instId)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(instId: string): number {
    const history = this.priceHistory.get(instId);
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

  getSignal(instId: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(instId);
    const history = this.priceHistory.get(instId);

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

export default OKXClient;
export {
  OKXClient,
  OKXCoherenceEngine,
  TRADING_PAIRS as OKX_PAIRS,
  CONFIG as OKX_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🌐 OKX TRADER 🌐                                                            ║
  ║                                                                               ║
  ║   Major Global Exchange • High Liquidity • Low Fees                           ║
  ║                                                                               ║
  ║   Assets:                                                                     ║
  ║   • BTC, ETH, SOL, XRP, DOGE...                                              ║
  ║   • 350+ Trading Pairs                                                        ║
  ║   • Spot, Margin, Futures                                                     ║
  ║   • Advanced Order Types                                                      ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.API_SECRET || !CONFIG.PASSPHRASE) {
    console.log('❌ Missing OKX credentials!');
    console.log('\nTo set up OKX:');
    console.log('1. Create account at https://www.okx.com');
    console.log('2. Go to API > Create API Key');
    console.log('3. Set passphrase and enable trading');
    console.log('4. Add to .env:');
    console.log('   OKX_API_KEY=your_api_key');
    console.log('   OKX_API_SECRET=your_api_secret');
    console.log('   OKX_PASSPHRASE=your_passphrase');
    console.log('   OKX_DEMO=true  # Use demo mode first');
    console.log('\n📖 Docs: https://www.okx.com/docs-v5/');
    return;
  }

  const client = new OKXClient();
  const engine = new OKXCoherenceEngine();

  // Get balance
  const balance = await client.getAccountBalance('USDT');
  console.log(`\n💰 USDT Balance: $${balance.available.toFixed(2)}`);
  console.log(`📊 Total: $${balance.total.toFixed(2)}`);

  // Get all balances
  const allBalances = await client.getBalance();
  console.log('\n📈 Holdings:');
  for (const bal of allBalances) {
    const available = parseFloat(bal.availBal);
    if (available > 0) {
      console.log(`   ${bal.ccy}: ${available.toFixed(8)}`);
    }
  }

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  setInterval(async () => {
    try {
      for (const pair of TRADING_PAIRS) {
        try {
          const ticker = await client.getTicker(pair.instId);
          const price = parseFloat(ticker.last);
          
          engine.addPrice(pair.instId, price);
          
          const signal = engine.getSignal(pair.instId);
          const coherence = engine.calculateCoherence(pair.instId);

          if (signal !== 'HOLD' && coherence >= 0.938) {
            console.log(`
  🎯 SIGNAL: ${signal} ${pair.name} (${pair.instId})
     Price: $${price.toFixed(4)}
     Bid: ${ticker.bidPx} | Ask: ${ticker.askPx}
     24h Vol: ${parseFloat(ticker.vol24h).toFixed(2)}
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
const isMainModule = process.argv[1]?.includes('okxApi');
if (isMainModule) {
  main().catch(console.error);
}
