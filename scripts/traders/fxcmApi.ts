/**
 * 💹 FXCM API 💹
 * 
 * Forex Capital Markets - Global forex specialist
 * FCA regulated, excellent for UK traders
 * 
 * Features:
 * - 40+ forex pairs
 * - CFDs on indices, commodities
 * - Low spreads
 * - Active trader pricing
 * - Free API access
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
  // API Credentials (REST API)
  ACCESS_TOKEN: process.env.FXCM_ACCESS_TOKEN || '',
  
  // API Endpoints
  BASE_URL: process.env.FXCM_DEMO === 'true'
    ? 'https://api-demo.fxcm.com'
    : 'https://api.fxcm.com',
  
  // Socket.io for streaming
  SOCKET_URL: process.env.FXCM_DEMO === 'true'
    ? 'https://api-demo.fxcm.com:443'
    : 'https://api.fxcm.com:443',
  
  // Trading settings
  RISK_PERCENT: 2,
  TAKE_PROFIT_PIPS: 50,
  STOP_LOSS_PIPS: 25,
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 5,
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface FXCMAccount {
  accountId: string;
  accountName: string;
  balance: number;
  equity: number;
  usedMargin: number;
  usableMargin: number;
  currency: string;
  marginCall: boolean;
}

export interface FXCMPosition {
  tradeId: string;
  accountId: string;
  symbol: string;
  isBuy: boolean;
  amount: number;
  openPrice: number;
  currentPrice: number;
  pl: number;
  grossPL: number;
  stop: number;
  limit: number;
  openTime: string;
}

export interface FXCMSymbol {
  symbol: string;
  description: string;
  pip: number;
  pipCost: number;
  tradeable: boolean;
  minQuantity: number;
  maxQuantity: number;
  currency: string;
}

export interface FXCMPrice {
  symbol: string;
  bid: number;
  ask: number;
  spread: number;
  high: number;
  low: number;
  updated: string;
}

export interface FXCMOrder {
  orderId: string;
  accountId: string;
  symbol: string;
  isBuy: boolean;
  amount: number;
  price: number;
  stop: number;
  limit: number;
  status: string;
  type: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Instruments
// ═══════════════════════════════════════════════════════════════════════════

// Major Forex Pairs
const MAJOR_PAIRS = [
  { symbol: 'EUR/USD', pip: 0.0001, description: 'Euro / US Dollar' },
  { symbol: 'GBP/USD', pip: 0.0001, description: 'British Pound / US Dollar' },
  { symbol: 'USD/JPY', pip: 0.01, description: 'US Dollar / Japanese Yen' },
  { symbol: 'USD/CHF', pip: 0.0001, description: 'US Dollar / Swiss Franc' },
  { symbol: 'AUD/USD', pip: 0.0001, description: 'Australian Dollar / US Dollar' },
  { symbol: 'USD/CAD', pip: 0.0001, description: 'US Dollar / Canadian Dollar' },
  { symbol: 'NZD/USD', pip: 0.0001, description: 'New Zealand Dollar / US Dollar' },
];

// GBP Crosses (Important for UK traders)
const GBP_CROSSES = [
  { symbol: 'GBP/JPY', pip: 0.01, description: 'British Pound / Japanese Yen' },
  { symbol: 'GBP/CHF', pip: 0.0001, description: 'British Pound / Swiss Franc' },
  { symbol: 'GBP/AUD', pip: 0.0001, description: 'British Pound / Australian Dollar' },
  { symbol: 'GBP/CAD', pip: 0.0001, description: 'British Pound / Canadian Dollar' },
  { symbol: 'GBP/NZD', pip: 0.0001, description: 'British Pound / New Zealand Dollar' },
  { symbol: 'EUR/GBP', pip: 0.0001, description: 'Euro / British Pound' },
];

// Euro Crosses
const EUR_CROSSES = [
  { symbol: 'EUR/JPY', pip: 0.01, description: 'Euro / Japanese Yen' },
  { symbol: 'EUR/CHF', pip: 0.0001, description: 'Euro / Swiss Franc' },
  { symbol: 'EUR/AUD', pip: 0.0001, description: 'Euro / Australian Dollar' },
  { symbol: 'EUR/CAD', pip: 0.0001, description: 'Euro / Canadian Dollar' },
  { symbol: 'EUR/NZD', pip: 0.0001, description: 'Euro / New Zealand Dollar' },
];

// Indices CFDs
const INDEX_CFDS = [
  { symbol: 'UK100', pip: 0.1, description: 'UK 100 Index' },
  { symbol: 'GER30', pip: 0.1, description: 'Germany 30 Index' },
  { symbol: 'US30', pip: 0.1, description: 'US 30 Index' },
  { symbol: 'SPX500', pip: 0.1, description: 'S&P 500 Index' },
  { symbol: 'NAS100', pip: 0.1, description: 'Nasdaq 100 Index' },
  { symbol: 'FRA40', pip: 0.1, description: 'France 40 Index' },
];

// Commodities
const COMMODITIES = [
  { symbol: 'XAU/USD', pip: 0.01, description: 'Gold / US Dollar' },
  { symbol: 'XAG/USD', pip: 0.001, description: 'Silver / US Dollar' },
  { symbol: 'USOil', pip: 0.01, description: 'US Crude Oil' },
  { symbol: 'UKOil', pip: 0.01, description: 'UK Brent Crude Oil' },
  { symbol: 'NGAS', pip: 0.001, description: 'Natural Gas' },
  { symbol: 'Copper', pip: 0.001, description: 'Copper' },
];

// ═══════════════════════════════════════════════════════════════════════════
// FXCM Client
// ═══════════════════════════════════════════════════════════════════════════

class FXCMClient {
  private baseUrl: string;
  private accessToken: string;
  private bearerToken: string = '';
  private accountId: string = '';

  constructor() {
    this.baseUrl = CONFIG.BASE_URL;
    this.accessToken = CONFIG.ACCESS_TOKEN;
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    params?: Record<string, any>
  ): Promise<any> {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    
    const headers: Record<string, string> = {
      'Accept': 'application/json',
      'Content-Type': 'application/x-www-form-urlencoded',
      'User-Agent': 'AureonTrading/1.0',
    };

    if (this.bearerToken) {
      headers['Authorization'] = `Bearer ${this.bearerToken}`;
    }

    const options: RequestInit = {
      method,
      headers,
    };

    if (method === 'GET' && params) {
      Object.keys(params).forEach(key => 
        url.searchParams.append(key, params[key])
      );
    } else if (params) {
      options.body = new URLSearchParams(params).toString();
    }

    try {
      const response = await fetch(url.toString(), options);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`FXCM API Error: ${response.status} - ${error}`);
      }

      return response.json();
    } catch (error) {
      console.error(`FXCM Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Authentication
  // ═══════════════════════════════════════════════════════════════════════

  async connect(): Promise<boolean> {
    try {
      // FXCM uses Socket.io for primary connection
      // REST API requires bearer token from socket handshake
      // For simplicity, using REST with access token
      
      const response = await fetch(`${this.baseUrl}/connect`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `access_token=${this.accessToken}`,
      });

      if (response.ok) {
        const data = await response.json();
        this.bearerToken = data.access_token;
        console.log('✅ Connected to FXCM');
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('FXCM connection failed:', error);
      return false;
    }
  }

  async disconnect(): Promise<void> {
    if (this.bearerToken) {
      try {
        await this.request('/disconnect', 'GET');
      } catch {}
    }
    this.bearerToken = '';
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account
  // ═══════════════════════════════════════════════════════════════════════

  async getAccounts(): Promise<FXCMAccount[]> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'Account',
    });
    return response.accounts || [];
  }

  async getAccountId(): Promise<string> {
    if (this.accountId) return this.accountId;
    
    const accounts = await this.getAccounts();
    if (accounts.length > 0) {
      this.accountId = accounts[0].accountId;
    }
    return this.accountId;
  }

  async getBalance(): Promise<{ balance: number; equity: number; margin: number }> {
    const accounts = await this.getAccounts();
    
    if (accounts.length === 0) {
      return { balance: 0, equity: 0, margin: 0 };
    }

    const account = accounts[0];
    return {
      balance: account.balance,
      equity: account.equity,
      margin: account.usedMargin,
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getPositions(): Promise<FXCMPosition[]> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'OpenPosition',
    });
    return response.open_positions || [];
  }

  async getClosedPositions(): Promise<any[]> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'ClosedPosition',
    });
    return response.closed_positions || [];
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Prices & Market Data
  // ═══════════════════════════════════════════════════════════════════════

  async getSymbols(): Promise<FXCMSymbol[]> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'Offer',
    });
    return response.offers || [];
  }

  async getPrice(symbol: string): Promise<FXCMPrice> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'Offer',
    });
    
    const offer = response.offers?.find((o: any) => o.currency === symbol);
    
    return {
      symbol,
      bid: offer?.sellPrice || 0,
      ask: offer?.buyPrice || 0,
      spread: offer?.spread || 0,
      high: offer?.high || 0,
      low: offer?.low || 0,
      updated: offer?.time || new Date().toISOString(),
    };
  }

  async getCandles(
    symbol: string,
    period: 'm1' | 'm5' | 'm15' | 'm30' | 'H1' | 'H4' | 'D1' = 'H1',
    count: number = 100
  ): Promise<any[]> {
    const response = await this.request('/candles', 'GET', {
      num: count,
      symbol,
      period,
    });
    return response.candles || [];
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async openTrade(
    symbol: string,
    isBuy: boolean,
    amount: number,
    stopPips?: number,
    limitPips?: number,
    atMarket: boolean = true
  ): Promise<FXCMOrder> {
    const accountId = await this.getAccountId();
    const price = await this.getPrice(symbol);
    
    const params: Record<string, any> = {
      account_id: accountId,
      symbol,
      is_buy: isBuy,
      amount,
      time_in_force: 'GTC',
      order_type: atMarket ? 'AtMarket' : 'MarketRange',
    };

    // Calculate stop/limit prices
    const pip = MAJOR_PAIRS.find(p => p.symbol === symbol)?.pip || 0.0001;
    const currentPrice = isBuy ? price.ask : price.bid;

    if (stopPips) {
      params.stop = isBuy 
        ? currentPrice - (stopPips * pip)
        : currentPrice + (stopPips * pip);
    }

    if (limitPips) {
      params.limit = isBuy 
        ? currentPrice + (limitPips * pip)
        : currentPrice - (limitPips * pip);
    }

    const response = await this.request('/trading/open_trade', 'POST', params);

    return {
      orderId: response.data?.orderId || '',
      accountId,
      symbol,
      isBuy,
      amount,
      price: currentPrice,
      stop: params.stop || 0,
      limit: params.limit || 0,
      status: 'Executed',
      type: 'Market',
    };
  }

  async buy(
    symbol: string,
    amount: number,
    stopPips?: number,
    limitPips?: number
  ): Promise<FXCMOrder> {
    return this.openTrade(symbol, true, amount, stopPips, limitPips);
  }

  async sell(
    symbol: string,
    amount: number,
    stopPips?: number,
    limitPips?: number
  ): Promise<FXCMOrder> {
    return this.openTrade(symbol, false, amount, stopPips, limitPips);
  }

  async closeTrade(tradeId: string, amount?: number): Promise<boolean> {
    try {
      await this.request('/trading/close_trade', 'POST', {
        trade_id: tradeId,
        amount: amount,
      });
      return true;
    } catch {
      return false;
    }
  }

  async closeAllPositions(): Promise<boolean> {
    try {
      await this.request('/trading/close_all_for_symbol', 'POST', {
        forSymbol: '*',
      });
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Pending Orders
  // ═══════════════════════════════════════════════════════════════════════

  async getOrders(): Promise<FXCMOrder[]> {
    const response = await this.request('/trading/get_model', 'GET', {
      models: 'Order',
    });
    return response.orders || [];
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    try {
      await this.request('/trading/delete_order', 'POST', {
        order_id: orderId,
      });
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Modify Positions
  // ═══════════════════════════════════════════════════════════════════════

  async modifyPosition(
    tradeId: string,
    stopPrice?: number,
    limitPrice?: number
  ): Promise<boolean> {
    try {
      const params: Record<string, any> = {
        trade_id: tradeId,
        is_stop: stopPrice !== undefined,
        is_limit: limitPrice !== undefined,
      };

      if (stopPrice !== undefined) params.rate = stopPrice;
      if (limitPrice !== undefined) params.rate = limitPrice;

      await this.request('/trading/change_trade_stop_limit', 'POST', params);
      return true;
    } catch {
      return false;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class FXCMCoherenceEngine {
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

    // Phi analysis
    const phiLevel = 1 / this.PHI;
    const phiDist = Math.abs(normalized - phiLevel);
    const phiScore = 1 - phiDist;

    // Trend analysis
    const sma5 = recent.slice(-5).reduce((a, b) => a + b, 0) / 5;
    const sma20 = recent.reduce((a, b) => a + b, 0) / recent.length;
    const trendScore = current > sma5 && sma5 > sma20 ? 1 : 
                       current < sma5 && sma5 < sma20 ? 0 : 0.5;

    // Volatility score
    const stdDev = Math.sqrt(
      recent.reduce((sum, p) => sum + (p - sma20) ** 2, 0) / recent.length
    );
    const volatility = stdDev / sma20;
    const volatilityScore = Math.exp(-volatility * 10);

    return phiScore * 0.4 + trendScore * 0.35 + volatilityScore * 0.25;
  }

  getSignal(symbol: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(symbol);
    const history = this.priceHistory.get(symbol);

    if (!history || history.length < 10) return 'HOLD';

    const sma5 = history.slice(-5).reduce((a, b) => a + b, 0) / 5;
    const sma10 = history.slice(-10).reduce((a, b) => a + b, 0) / 10;
    const current = history[history.length - 1];

    if (coherence >= 0.938 && current > sma5 && sma5 > sma10) return 'BUY';
    if (coherence >= 0.938 && current < sma5 && sma5 < sma10) return 'SELL';

    return 'HOLD';
  }

  analyzePair(symbol: string): {
    coherence: number;
    signal: 'BUY' | 'SELL' | 'HOLD';
    strength: 'WEAK' | 'MODERATE' | 'STRONG';
  } {
    const coherence = this.calculateCoherence(symbol);
    const signal = this.getSignal(symbol);
    
    let strength: 'WEAK' | 'MODERATE' | 'STRONG' = 'WEAK';
    if (coherence >= 0.95) strength = 'STRONG';
    else if (coherence >= 0.90) strength = 'MODERATE';

    return { coherence, signal, strength };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Export
// ═══════════════════════════════════════════════════════════════════════════

export default FXCMClient;
export {
  FXCMClient,
  FXCMCoherenceEngine,
  MAJOR_PAIRS as FXCM_MAJOR_PAIRS,
  GBP_CROSSES as FXCM_GBP_CROSSES,
  EUR_CROSSES as FXCM_EUR_CROSSES,
  INDEX_CFDS as FXCM_INDEX_CFDS,
  COMMODITIES as FXCM_COMMODITIES,
  CONFIG as FXCM_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   💹 FXCM FOREX TRADER 💹                                                     ║
  ║                                                                               ║
  ║   FCA Regulated Forex Specialist • Low Spreads • Active Trader Pricing        ║
  ║                                                                               ║
  ║   Instruments:                                                                ║
  ║   • Major Forex Pairs (EUR/USD, GBP/USD, etc.)                               ║
  ║   • GBP Crosses (GBP/JPY, EUR/GBP, etc.)                                     ║
  ║   • Index CFDs (UK100, US30, etc.)                                           ║
  ║   • Commodities (Gold, Oil, etc.)                                            ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.ACCESS_TOKEN) {
    console.log('❌ Missing FXCM credentials!');
    console.log('\nTo set up FXCM:');
    console.log('1. Create account at https://www.fxcm.com/uk');
    console.log('2. Request API access (free with account)');
    console.log('3. Generate API token in Trading Station');
    console.log('4. Add to .env:');
    console.log('   FXCM_ACCESS_TOKEN=your_access_token');
    console.log('   FXCM_DEMO=true  # Use demo account first');
    console.log('\n📖 Docs: https://fxcm.github.io/rest-api-docs/');
    return;
  }

  const client = new FXCMClient();
  const engine = new FXCMCoherenceEngine();

  // Connect
  const connected = await client.connect();
  if (!connected) {
    console.log('❌ Failed to connect to FXCM');
    return;
  }

  // Get balance
  const balance = await client.getBalance();
  console.log(`\n💰 Account Balance: $${balance.balance.toFixed(2)}`);
  console.log(`📊 Equity: $${balance.equity.toFixed(2)}`);
  console.log(`📈 Used Margin: $${balance.margin.toFixed(2)}`);

  // Get positions
  const positions = await client.getPositions();
  console.log(`\n📈 Open Positions: ${positions.length}`);

  // Start trading loop
  console.log('\n🎵 Starting coherence-based forex trading...\n');

  const allPairs = [...MAJOR_PAIRS, ...GBP_CROSSES];

  setInterval(async () => {
    try {
      for (const pair of allPairs) {
        try {
          const price = await client.getPrice(pair.symbol);
          const mid = (price.bid + price.ask) / 2;
          
          engine.addPrice(pair.symbol, mid);
          
          const analysis = engine.analyzePair(pair.symbol);

          if (analysis.signal !== 'HOLD' && analysis.coherence >= 0.938) {
            console.log(`
  🎯 SIGNAL: ${analysis.signal} ${pair.symbol}
     Bid: ${price.bid.toFixed(5)} | Ask: ${price.ask.toFixed(5)}
     Spread: ${price.spread.toFixed(1)} pips
     Coherence: ${(analysis.coherence * 100).toFixed(1)}%
     Strength: ${analysis.strength}
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

  // Cleanup on exit
  process.on('SIGINT', async () => {
    console.log('\n🛑 Shutting down FXCM trader...');
    await client.disconnect();
    process.exit(0);
  });
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('fxcmApi');
if (isMainModule) {
  main().catch(console.error);
}
