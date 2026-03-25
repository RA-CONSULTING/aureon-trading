/**
 * 🏦 INTERACTIVE BROKERS API 🏦
 * 
 * The most comprehensive multi-asset broker:
 * - UK, EU, US Stocks
 * - Forex
 * - Futures
 * - Options
 * - Bonds
 * 
 * Uses IBKR Client Portal API (REST) or TWS API
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
  // Client Portal Gateway (local)
  GATEWAY_URL: process.env.IB_GATEWAY_URL || 'https://localhost:5000',
  
  // Account
  ACCOUNT_ID: process.env.IB_ACCOUNT_ID || '',
  
  // Trading settings
  RISK_PERCENT: 2,
  TAKE_PROFIT: 2.0,
  STOP_LOSS: 1.0,
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 10,
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface IBPosition {
  conid: number;
  contractDesc: string;
  position: number;
  mktPrice: number;
  mktValue: number;
  avgCost: number;
  unrealizedPnl: number;
  realizedPnl: number;
}

export interface IBOrder {
  orderId: number;
  conid: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  orderType: string;
  quantity: number;
  price?: number;
  status: string;
  filledQuantity: number;
  avgFillPrice: number;
}

export interface IBQuote {
  conid: number;
  symbol: string;
  lastPrice: number;
  bidPrice: number;
  askPrice: number;
  volume: number;
  change: number;
  changePercent: number;
}

export interface IBContract {
  conid: number;
  symbol: string;
  secType: string;
  exchange: string;
  currency: string;
  description: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Instruments
// ═══════════════════════════════════════════════════════════════════════════

// UK Stocks (LSE)
const UK_STOCKS = [
  { symbol: 'HSBA', conid: 8894, name: 'HSBC Holdings', exchange: 'LSE' },
  { symbol: 'BP', conid: 4815747, name: 'BP PLC', exchange: 'LSE' },
  { symbol: 'SHEL', conid: 9554, name: 'Shell PLC', exchange: 'LSE' },
  { symbol: 'AZN', conid: 6590, name: 'AstraZeneca', exchange: 'LSE' },
  { symbol: 'GSK', conid: 6641, name: 'GSK PLC', exchange: 'LSE' },
  { symbol: 'ULVR', conid: 9673, name: 'Unilever', exchange: 'LSE' },
  { symbol: 'RIO', conid: 9384, name: 'Rio Tinto', exchange: 'LSE' },
  { symbol: 'BARC', conid: 4726009, name: 'Barclays', exchange: 'LSE' },
  { symbol: 'LLOY', conid: 8159, name: 'Lloyds Banking', exchange: 'LSE' },
  { symbol: 'VOD', conid: 9700, name: 'Vodafone', exchange: 'LSE' },
];

// US Stocks (NYSE/NASDAQ)
const US_STOCKS = [
  { symbol: 'AAPL', conid: 265598, name: 'Apple Inc', exchange: 'NASDAQ' },
  { symbol: 'MSFT', conid: 272093, name: 'Microsoft', exchange: 'NASDAQ' },
  { symbol: 'GOOGL', conid: 208813720, name: 'Alphabet', exchange: 'NASDAQ' },
  { symbol: 'AMZN', conid: 3691937, name: 'Amazon', exchange: 'NASDAQ' },
  { symbol: 'NVDA', conid: 4815747, name: 'NVIDIA', exchange: 'NASDAQ' },
  { symbol: 'TSLA', conid: 76792991, name: 'Tesla', exchange: 'NASDAQ' },
  { symbol: 'META', conid: 107113386, name: 'Meta Platforms', exchange: 'NASDAQ' },
  { symbol: 'JPM', conid: 1520593, name: 'JP Morgan', exchange: 'NYSE' },
  { symbol: 'V', conid: 15124833, name: 'Visa', exchange: 'NYSE' },
  { symbol: 'JNJ', conid: 1520614, name: 'Johnson & Johnson', exchange: 'NYSE' },
];

// EU Stocks
const EU_STOCKS = [
  { symbol: 'SAP', conid: 8894, name: 'SAP SE', exchange: 'IBIS' },
  { symbol: 'ASML', conid: 6772798, name: 'ASML Holding', exchange: 'AEB' },
  { symbol: 'LVMH', conid: 4726009, name: 'LVMH', exchange: 'SBF' },
  { symbol: 'NVO', conid: 70839, name: 'Novo Nordisk', exchange: 'CSE' },
  { symbol: 'SIE', conid: 10428, name: 'Siemens', exchange: 'IBIS' },
];

// Forex Pairs
const FOREX_PAIRS = [
  { symbol: 'EUR.USD', conid: 12087792, name: 'EUR/USD' },
  { symbol: 'GBP.USD', conid: 12087797, name: 'GBP/USD' },
  { symbol: 'USD.JPY', conid: 12087820, name: 'USD/JPY' },
  { symbol: 'EUR.GBP', conid: 12087810, name: 'EUR/GBP' },
  { symbol: 'AUD.USD', conid: 12087776, name: 'AUD/USD' },
  { symbol: 'USD.CHF', conid: 12087817, name: 'USD/CHF' },
  { symbol: 'USD.CAD', conid: 12087814, name: 'USD/CAD' },
  { symbol: 'NZD.USD', conid: 12087823, name: 'NZD/USD' },
];

// Futures
const FUTURES = [
  { symbol: 'ES', conid: 495512552, name: 'E-mini S&P 500', exchange: 'CME' },
  { symbol: 'NQ', conid: 495512566, name: 'E-mini NASDAQ', exchange: 'CME' },
  { symbol: 'GC', conid: 495512557, name: 'Gold', exchange: 'COMEX' },
  { symbol: 'CL', conid: 495512551, name: 'Crude Oil', exchange: 'NYMEX' },
  { symbol: 'ZB', conid: 495512560, name: '30-Year T-Bond', exchange: 'CBOT' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Interactive Brokers Client
// ═══════════════════════════════════════════════════════════════════════════

class InteractiveBrokersClient {
  private baseUrl: string;
  private accountId: string;
  private authenticated: boolean = false;

  constructor() {
    this.baseUrl = CONFIG.GATEWAY_URL;
    this.accountId = CONFIG.ACCOUNT_ID;
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const url = `${this.baseUrl}/v1/api${endpoint}`;
    
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`IB API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`IB Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Authentication
  // ═══════════════════════════════════════════════════════════════════════

  async authenticate(): Promise<boolean> {
    try {
      // Check authentication status
      const status = await this.request('/iserver/auth/status', 'POST');
      
      if (status.authenticated) {
        this.authenticated = true;
        console.log('✅ IB Gateway authenticated');
        return true;
      }

      // Try to reauthenticate
      await this.request('/iserver/reauthenticate', 'POST');
      const recheck = await this.request('/iserver/auth/status', 'POST');
      
      this.authenticated = recheck.authenticated;
      return this.authenticated;
    } catch (error) {
      console.error('❌ IB Authentication failed:', error);
      return false;
    }
  }

  async tickle(): Promise<void> {
    // Keep session alive
    await this.request('/tickle', 'POST');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account Info
  // ═══════════════════════════════════════════════════════════════════════

  async getAccounts(): Promise<any[]> {
    const response = await this.request('/iserver/accounts');
    return response.accounts || [];
  }

  async getAccountSummary(): Promise<any> {
    const response = await this.request(`/portfolio/${this.accountId}/summary`);
    return response;
  }

  async getBalance(): Promise<{ balance: number; buyingPower: number; currency: string }> {
    const summary = await this.getAccountSummary();
    return {
      balance: summary.netliquidation?.amount || 0,
      buyingPower: summary.buyingpower?.amount || 0,
      currency: summary.netliquidation?.currency || 'GBP',
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getPositions(): Promise<IBPosition[]> {
    const response = await this.request(`/portfolio/${this.accountId}/positions/0`);
    return response || [];
  }

  async getPosition(conid: number): Promise<IBPosition | null> {
    const positions = await this.getPositions();
    return positions.find(p => p.conid === conid) || null;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Market Data
  // ═══════════════════════════════════════════════════════════════════════

  async searchContract(symbol: string, secType: string = 'STK'): Promise<IBContract[]> {
    const response = await this.request(`/iserver/secdef/search?symbol=${symbol}&secType=${secType}`);
    return response || [];
  }

  async getQuote(conids: number[]): Promise<IBQuote[]> {
    const conidStr = conids.join(',');
    const response = await this.request(`/iserver/marketdata/snapshot?conids=${conidStr}&fields=31,84,85,86,87,88`);
    
    return (response || []).map((q: any) => ({
      conid: q.conid,
      symbol: q.symbol,
      lastPrice: q['31'] || 0,
      bidPrice: q['84'] || 0,
      askPrice: q['85'] || 0,
      volume: q['87'] || 0,
      change: q['82'] || 0,
      changePercent: q['83'] || 0,
    }));
  }

  async getHistoricalData(
    conid: number,
    period: string = '1d',
    bar: string = '5min'
  ): Promise<any> {
    const response = await this.request(
      `/iserver/marketdata/history?conid=${conid}&period=${period}&bar=${bar}`
    );
    return response;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async placeOrder(
    conid: number,
    side: 'BUY' | 'SELL',
    quantity: number,
    orderType: 'MKT' | 'LMT' | 'STP' = 'MKT',
    price?: number,
    stopPrice?: number
  ): Promise<IBOrder> {
    const order: any = {
      conid,
      orderType,
      side,
      quantity,
      tif: 'DAY',
    };

    if (orderType === 'LMT' && price) {
      order.price = price;
    }
    if (orderType === 'STP' && stopPrice) {
      order.price = stopPrice;
    }

    // First, submit the order
    const response = await this.request(
      `/iserver/account/${this.accountId}/orders`,
      'POST',
      { orders: [order] }
    );

    // Handle confirmation if required
    if (response[0]?.id) {
      // Confirm the order
      const confirmResponse = await this.request(
        `/iserver/reply/${response[0].id}`,
        'POST',
        { confirmed: true }
      );
      return confirmResponse[0];
    }

    return response[0];
  }

  async placeBracketOrder(
    conid: number,
    side: 'BUY' | 'SELL',
    quantity: number,
    entryPrice: number,
    takeProfitPrice: number,
    stopLossPrice: number
  ): Promise<IBOrder[]> {
    const oppositeSide = side === 'BUY' ? 'SELL' : 'BUY';
    
    const orders = [
      {
        conid,
        orderType: 'LMT',
        side,
        quantity,
        price: entryPrice,
        tif: 'DAY',
      },
      {
        conid,
        orderType: 'LMT',
        side: oppositeSide,
        quantity,
        price: takeProfitPrice,
        tif: 'GTC',
        parentId: 'PARENT',
      },
      {
        conid,
        orderType: 'STP',
        side: oppositeSide,
        quantity,
        price: stopLossPrice,
        tif: 'GTC',
        parentId: 'PARENT',
      },
    ];

    const response = await this.request(
      `/iserver/account/${this.accountId}/orders`,
      'POST',
      { orders }
    );

    return response;
  }

  async getOrders(): Promise<IBOrder[]> {
    const response = await this.request('/iserver/account/orders');
    return response.orders || [];
  }

  async cancelOrder(orderId: number): Promise<boolean> {
    try {
      await this.request(
        `/iserver/account/${this.accountId}/order/${orderId}`,
        'DELETE'
      );
      return true;
    } catch {
      return false;
    }
  }

  async cancelAllOrders(): Promise<boolean> {
    try {
      await this.request(`/iserver/account/${this.accountId}/orders`, 'DELETE');
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Portfolio
  // ═══════════════════════════════════════════════════════════════════════

  async getPortfolioAllocation(): Promise<any> {
    const response = await this.request(`/portfolio/${this.accountId}/allocation`);
    return response;
  }

  async getPortfolioPerformance(): Promise<any> {
    const response = await this.request(`/pa/performance`);
    return response;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Scanners
  // ═══════════════════════════════════════════════════════════════════════

  async runScanner(scannerParams: any): Promise<any[]> {
    const response = await this.request('/iserver/scanner/run', 'POST', scannerParams);
    return response.contracts || [];
  }

  async getTopMovers(market: 'UK' | 'US' | 'EU' = 'UK'): Promise<any[]> {
    const locations: Record<string, string> = {
      UK: 'STK.LSE',
      US: 'STK.NASDAQ.NMS',
      EU: 'STK.IBIS',
    };

    const scannerParams = {
      instrument: 'STK',
      type: 'TOP_PERC_GAIN',
      location: locations[market],
      size: '25',
    };

    return this.runScanner(scannerParams);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class IBCoherenceEngine {
  private priceHistory: Map<number, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(conid: number, price: number): void {
    if (!this.priceHistory.has(conid)) {
      this.priceHistory.set(conid, []);
    }
    const history = this.priceHistory.get(conid)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(conid: number): number {
    const history = this.priceHistory.get(conid);
    if (!history || history.length < 10) return 0;

    const recent = history.slice(-20);
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    if (range === 0) return 0.5;

    const current = recent[recent.length - 1];
    const normalized = (current - min) / range;

    // Phi-based coherence
    const phiMajorDist = Math.abs(normalized - (1 / this.PHI));
    const phiMinorDist = Math.abs(normalized - (this.PHI - 1));
    const phiScore = 1 - Math.min(phiMajorDist, phiMinorDist);

    // Momentum
    const momentum = (current - recent[0]) / recent[0];
    const momentumScore = Math.tanh(momentum * 50) * 0.5 + 0.5;

    // Wave position
    const wavePosition = Math.sin(normalized * Math.PI) ** 2;

    return phiScore * 0.4 + momentumScore * 0.3 + wavePosition * 0.3;
  }

  getSignal(conid: number): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(conid);
    const history = this.priceHistory.get(conid);

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

export default InteractiveBrokersClient;
export { 
  InteractiveBrokersClient, 
  IBCoherenceEngine,
  UK_STOCKS, 
  US_STOCKS, 
  EU_STOCKS, 
  FOREX_PAIRS, 
  FUTURES,
  CONFIG as IB_CONFIG 
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🏦 INTERACTIVE BROKERS TRADER 🏦                                            ║
  ║                                                                               ║
  ║   Multi-Asset Trading:                                                        ║
  ║   • UK Stocks (LSE)     - HSBC, BP, Shell, AstraZeneca                       ║
  ║   • US Stocks (NYSE/NASDAQ) - Apple, Microsoft, Tesla                        ║
  ║   • EU Stocks           - SAP, ASML, LVMH                                    ║
  ║   • Forex               - EUR/USD, GBP/USD, USD/JPY                          ║
  ║   • Futures             - ES, NQ, Gold, Crude                                ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.ACCOUNT_ID) {
    console.log('❌ Missing Interactive Brokers credentials!');
    console.log('\nTo set up Interactive Brokers:');
    console.log('1. Download IB Gateway or TWS from https://www.interactivebrokers.com');
    console.log('2. Run the Client Portal Gateway');
    console.log('3. Add to .env:');
    console.log('   IB_GATEWAY_URL=https://localhost:5000');
    console.log('   IB_ACCOUNT_ID=your_account_id');
    console.log('\n📖 Docs: https://interactivebrokers.github.io/cpwebapi/');
    return;
  }

  const client = new InteractiveBrokersClient();
  const engine = new IBCoherenceEngine();

  // Authenticate
  const authenticated = await client.authenticate();
  if (!authenticated) {
    console.log('❌ Failed to authenticate with IB Gateway');
    console.log('Make sure the Client Portal Gateway is running');
    return;
  }

  // Get account info
  const balance = await client.getBalance();
  console.log(`\n💰 Account Balance: ${balance.currency} ${balance.balance.toFixed(2)}`);
  console.log(`📊 Buying Power: ${balance.currency} ${balance.buyingPower.toFixed(2)}`);

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  const allInstruments = [...UK_STOCKS, ...US_STOCKS];
  const conids = allInstruments.map(i => i.conid);

  setInterval(async () => {
    try {
      // Keep session alive
      await client.tickle();

      // Get quotes
      const quotes = await client.getQuote(conids);

      for (const quote of quotes) {
        engine.addPrice(quote.conid, quote.lastPrice);
        const signal = engine.getSignal(quote.conid);
        const coherence = engine.calculateCoherence(quote.conid);

        if (signal !== 'HOLD' && coherence >= 0.938) {
          const instrument = allInstruments.find(i => i.conid === quote.conid);
          console.log(`
  🎯 SIGNAL: ${signal} ${instrument?.symbol}
     Price: ${quote.lastPrice}
     Coherence: ${(coherence * 100).toFixed(1)}%
          `);
        }
      }
    } catch (error) {
      console.error('Trading loop error:', error);
    }
  }, CONFIG.SCAN_INTERVAL);
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('interactiveBrokersApi');
if (isMainModule) {
  main().catch(console.error);
}
