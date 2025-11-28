/**
 * 🏦 SAXO BANK API 🏦
 * 
 * Premium multi-asset trading platform
 * Excellent UK support, very comprehensive
 * 
 * Features:
 * - Stocks (40,000+)
 * - Forex (180+ pairs)
 * - CFDs
 * - Futures
 * - Options
 * - Bonds
 * - ETFs
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
  // OAuth2 Credentials
  APP_KEY: process.env.SAXO_APP_KEY || '',
  APP_SECRET: process.env.SAXO_APP_SECRET || '',
  ACCESS_TOKEN: process.env.SAXO_ACCESS_TOKEN || '',
  
  // API Endpoint
  BASE_URL: process.env.SAXO_DEMO === 'true'
    ? 'https://gateway.saxobank.com/sim/openapi'
    : 'https://gateway.saxobank.com/openapi',
  
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

export interface SaxoAccount {
  AccountId: string;
  AccountKey: string;
  AccountType: string;
  Currency: string;
  Balance: number;
  CashBalance: number;
  UnrealizedPnL: number;
}

export interface SaxoPosition {
  PositionId: string;
  NetPositionId: string;
  AssetType: string;
  Amount: number;
  AverageOpenPrice: number;
  CurrentPrice: number;
  ProfitLossOnTrade: number;
  Uic: number;
  Symbol: string;
}

export interface SaxoInstrument {
  Uic: number;
  Symbol: string;
  Description: string;
  AssetType: string;
  ExchangeId: string;
  Currency: string;
  TradableAs: string[];
}

export interface SaxoPrice {
  Uic: number;
  AssetType: string;
  Bid: number;
  Ask: number;
  Mid: number;
  LastUpdated: string;
  PriceSource: string;
}

export interface SaxoOrder {
  OrderId: string;
  OrderType: string;
  AssetType: string;
  Uic: number;
  BuySell: 'Buy' | 'Sell';
  Amount: number;
  Price: number;
  Status: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Instruments
// ═══════════════════════════════════════════════════════════════════════════

// UK Stocks
const UK_STOCKS = [
  { uic: 16099, symbol: 'HSBA:xlon', name: 'HSBC Holdings', assetType: 'Stock' },
  { uic: 1347, symbol: 'BP.:xlon', name: 'BP PLC', assetType: 'Stock' },
  { uic: 17254, symbol: 'SHEL:xlon', name: 'Shell PLC', assetType: 'Stock' },
  { uic: 478, symbol: 'AZN:xlon', name: 'AstraZeneca', assetType: 'Stock' },
  { uic: 14422, symbol: 'GSK:xlon', name: 'GSK PLC', assetType: 'Stock' },
  { uic: 20159, symbol: 'ULVR:xlon', name: 'Unilever', assetType: 'Stock' },
  { uic: 17284, symbol: 'RIO:xlon', name: 'Rio Tinto', assetType: 'Stock' },
  { uic: 542, symbol: 'BARC:xlon', name: 'Barclays', assetType: 'Stock' },
];

// US Stocks
const US_STOCKS = [
  { uic: 211, symbol: 'AAPL:xnas', name: 'Apple Inc', assetType: 'Stock' },
  { uic: 1228, symbol: 'MSFT:xnas', name: 'Microsoft', assetType: 'Stock' },
  { uic: 14445, symbol: 'GOOGL:xnas', name: 'Alphabet', assetType: 'Stock' },
  { uic: 209, symbol: 'AMZN:xnas', name: 'Amazon', assetType: 'Stock' },
  { uic: 16123, symbol: 'NVDA:xnas', name: 'NVIDIA', assetType: 'Stock' },
  { uic: 27884, symbol: 'TSLA:xnas', name: 'Tesla', assetType: 'Stock' },
];

// Forex Pairs
const FOREX_PAIRS = [
  { uic: 21, symbol: 'EURUSD', name: 'EUR/USD', assetType: 'FxSpot' },
  { uic: 31, symbol: 'GBPUSD', name: 'GBP/USD', assetType: 'FxSpot' },
  { uic: 46, symbol: 'USDJPY', name: 'USD/JPY', assetType: 'FxSpot' },
  { uic: 23, symbol: 'EURGBP', name: 'EUR/GBP', assetType: 'FxSpot' },
  { uic: 4, symbol: 'AUDUSD', name: 'AUD/USD', assetType: 'FxSpot' },
  { uic: 49, symbol: 'USDCHF', name: 'USD/CHF', assetType: 'FxSpot' },
  { uic: 47, symbol: 'USDCAD', name: 'USD/CAD', assetType: 'FxSpot' },
  { uic: 39, symbol: 'NZDUSD', name: 'NZD/USD', assetType: 'FxSpot' },
];

// Indices CFDs
const INDEX_CFDS = [
  { uic: 14295, symbol: 'UK100', name: 'UK 100', assetType: 'CfdOnIndex' },
  { uic: 6410, symbol: 'GER40', name: 'Germany 40', assetType: 'CfdOnIndex' },
  { uic: 4918, symbol: 'US30', name: 'US 30', assetType: 'CfdOnIndex' },
  { uic: 31983, symbol: 'US500', name: 'US 500', assetType: 'CfdOnIndex' },
  { uic: 31984, symbol: 'USTECH', name: 'US Tech 100', assetType: 'CfdOnIndex' },
];

// Commodities
const COMMODITIES = [
  { uic: 5001, symbol: 'XAUUSD', name: 'Gold', assetType: 'CfdOnIndex' },
  { uic: 5002, symbol: 'XAGUSD', name: 'Silver', assetType: 'CfdOnIndex' },
  { uic: 5201, symbol: 'OILUK', name: 'Brent Crude', assetType: 'CfdOnIndex' },
  { uic: 5200, symbol: 'OILUS', name: 'WTI Crude', assetType: 'CfdOnIndex' },
];

// ═══════════════════════════════════════════════════════════════════════════
// Saxo Bank Client
// ═══════════════════════════════════════════════════════════════════════════

class SaxoBankClient {
  private baseUrl: string;
  private accessToken: string;
  private accountKey: string = '';

  constructor() {
    this.baseUrl = CONFIG.BASE_URL;
    this.accessToken = CONFIG.ACCESS_TOKEN;
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${this.accessToken}`,
    };

    const options: RequestInit = {
      method,
      headers,
    };

    if (body) {
      options.body = JSON.stringify(body);
    }

    try {
      const response = await fetch(url, options);
      
      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Saxo API Error: ${response.status} - ${error}`);
      }

      const text = await response.text();
      return text ? JSON.parse(text) : {};
    } catch (error) {
      console.error(`Saxo Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account
  // ═══════════════════════════════════════════════════════════════════════

  async getAccounts(): Promise<SaxoAccount[]> {
    const response = await this.request('/port/v1/accounts/me');
    return response.Data || [];
  }

  async getAccountKey(): Promise<string> {
    if (this.accountKey) return this.accountKey;
    
    const accounts = await this.getAccounts();
    if (accounts.length > 0) {
      this.accountKey = accounts[0].AccountKey;
    }
    return this.accountKey;
  }

  async getBalance(): Promise<{ balance: number; available: number; currency: string }> {
    const accountKey = await this.getAccountKey();
    const response = await this.request(`/port/v1/balances?AccountKey=${accountKey}`);
    
    return {
      balance: response.TotalValue || 0,
      available: response.CashAvailableForTrading || 0,
      currency: response.Currency || 'GBP',
    };
  }

  async getAccountSummary(): Promise<any> {
    const accountKey = await this.getAccountKey();
    return this.request(`/port/v1/accounts/${accountKey}`);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getPositions(): Promise<SaxoPosition[]> {
    const accountKey = await this.getAccountKey();
    const response = await this.request(`/port/v1/positions?AccountKey=${accountKey}`);
    return response.Data || [];
  }

  async getNetPositions(): Promise<any[]> {
    const accountKey = await this.getAccountKey();
    const response = await this.request(`/port/v1/netpositions?AccountKey=${accountKey}`);
    return response.Data || [];
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Instruments & Prices
  // ═══════════════════════════════════════════════════════════════════════

  async searchInstruments(
    keywords: string,
    assetTypes: string[] = ['Stock', 'FxSpot', 'CfdOnIndex']
  ): Promise<SaxoInstrument[]> {
    const assetTypeStr = assetTypes.join(',');
    const response = await this.request(
      `/ref/v1/instruments?Keywords=${encodeURIComponent(keywords)}&AssetTypes=${assetTypeStr}`
    );
    return response.Data || [];
  }

  async getInstrumentDetails(uic: number, assetType: string): Promise<SaxoInstrument | null> {
    const response = await this.request(`/ref/v1/instruments/details?Uics=${uic}&AssetType=${assetType}`);
    return response.Data?.[0] || null;
  }

  async getPrice(uic: number, assetType: string): Promise<SaxoPrice> {
    const accountKey = await this.getAccountKey();
    const response = await this.request(
      `/trade/v1/infoprices?Uic=${uic}&AssetType=${assetType}&AccountKey=${accountKey}`
    );
    
    return {
      Uic: uic,
      AssetType: assetType,
      Bid: response.Quote?.Bid || 0,
      Ask: response.Quote?.Ask || 0,
      Mid: response.Quote?.Mid || 0,
      LastUpdated: response.LastUpdated || '',
      PriceSource: response.PriceSource || '',
    };
  }

  async getPrices(instruments: { uic: number; assetType: string }[]): Promise<SaxoPrice[]> {
    const results: SaxoPrice[] = [];
    
    for (const inst of instruments) {
      try {
        const price = await this.getPrice(inst.uic, inst.assetType);
        results.push(price);
      } catch (err) {
        // Skip unavailable instruments
      }
    }
    
    return results;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async placeOrder(
    uic: number,
    assetType: string,
    buySell: 'Buy' | 'Sell',
    amount: number,
    orderType: 'Market' | 'Limit' | 'Stop' = 'Market',
    price?: number,
    stopLossPrice?: number,
    takeProfitPrice?: number
  ): Promise<SaxoOrder> {
    const accountKey = await this.getAccountKey();
    
    const orderBody: any = {
      AccountKey: accountKey,
      Uic: uic,
      AssetType: assetType,
      BuySell: buySell,
      Amount: amount,
      OrderType: orderType,
      OrderDuration: { DurationType: 'DayOrder' },
    };

    if (orderType === 'Limit' && price) {
      orderBody.OrderPrice = price;
    }

    // Add related orders for SL/TP
    if (stopLossPrice || takeProfitPrice) {
      orderBody.Orders = [];
      
      if (stopLossPrice) {
        orderBody.Orders.push({
          OrderType: 'StopIfTraded',
          OrderPrice: stopLossPrice,
          BuySell: buySell === 'Buy' ? 'Sell' : 'Buy',
          Amount: amount,
        });
      }
      
      if (takeProfitPrice) {
        orderBody.Orders.push({
          OrderType: 'Limit',
          OrderPrice: takeProfitPrice,
          BuySell: buySell === 'Buy' ? 'Sell' : 'Buy',
          Amount: amount,
        });
      }
    }

    const response = await this.request('/trade/v2/orders', 'POST', orderBody);
    
    return {
      OrderId: response.OrderId,
      OrderType: orderType,
      AssetType: assetType,
      Uic: uic,
      BuySell: buySell,
      Amount: amount,
      Price: price || 0,
      Status: 'Placed',
    };
  }

  async marketBuy(uic: number, assetType: string, amount: number): Promise<SaxoOrder> {
    return this.placeOrder(uic, assetType, 'Buy', amount, 'Market');
  }

  async marketSell(uic: number, assetType: string, amount: number): Promise<SaxoOrder> {
    return this.placeOrder(uic, assetType, 'Sell', amount, 'Market');
  }

  async limitBuy(uic: number, assetType: string, amount: number, price: number): Promise<SaxoOrder> {
    return this.placeOrder(uic, assetType, 'Buy', amount, 'Limit', price);
  }

  async limitSell(uic: number, assetType: string, amount: number, price: number): Promise<SaxoOrder> {
    return this.placeOrder(uic, assetType, 'Sell', amount, 'Limit', price);
  }

  async getOrders(): Promise<SaxoOrder[]> {
    const accountKey = await this.getAccountKey();
    const response = await this.request(`/port/v1/orders?AccountKey=${accountKey}`);
    return response.Data || [];
  }

  async cancelOrder(orderId: string): Promise<boolean> {
    try {
      const accountKey = await this.getAccountKey();
      await this.request(`/trade/v2/orders/${orderId}?AccountKey=${accountKey}`, 'DELETE');
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Close Positions
  // ═══════════════════════════════════════════════════════════════════════

  async closePosition(positionId: string): Promise<boolean> {
    try {
      const accountKey = await this.getAccountKey();
      await this.request('/trade/v2/positions', 'DELETE', {
        AccountKey: accountKey,
        PositionId: positionId,
      });
      return true;
    } catch {
      return false;
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class SaxoCoherenceEngine {
  private priceHistory: Map<number, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(uic: number, price: number): void {
    if (!this.priceHistory.has(uic)) {
      this.priceHistory.set(uic, []);
    }
    const history = this.priceHistory.get(uic)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(uic: number): number {
    const history = this.priceHistory.get(uic);
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

  getSignal(uic: number): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(uic);
    const history = this.priceHistory.get(uic);

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

export default SaxoBankClient;
export {
  SaxoBankClient,
  SaxoCoherenceEngine,
  UK_STOCKS as SAXO_UK_STOCKS,
  US_STOCKS as SAXO_US_STOCKS,
  FOREX_PAIRS as SAXO_FOREX,
  INDEX_CFDS as SAXO_INDICES,
  COMMODITIES as SAXO_COMMODITIES,
  CONFIG as SAXO_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🏦 SAXO BANK TRADER 🏦                                                      ║
  ║                                                                               ║
  ║   Premium Multi-Asset Platform • 40,000+ Instruments • UK Friendly            ║
  ║                                                                               ║
  ║   Assets:                                                                     ║
  ║   • UK & US Stocks                                                            ║
  ║   • Forex (180+ pairs)                                                        ║
  ║   • Indices CFDs                                                              ║
  ║   • Commodities                                                               ║
  ║   • Futures & Options                                                         ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.ACCESS_TOKEN) {
    console.log('❌ Missing Saxo Bank credentials!');
    console.log('\nTo set up Saxo Bank:');
    console.log('1. Create account at https://www.home.saxo');
    console.log('2. Register for API access at https://www.developer.saxo');
    console.log('3. Create an application and get OAuth2 tokens');
    console.log('4. Add to .env:');
    console.log('   SAXO_APP_KEY=your_app_key');
    console.log('   SAXO_APP_SECRET=your_app_secret');
    console.log('   SAXO_ACCESS_TOKEN=your_access_token');
    console.log('   SAXO_DEMO=true  # Use simulation first');
    console.log('\n📖 Docs: https://www.developer.saxo/openapi/learn');
    return;
  }

  const client = new SaxoBankClient();
  const engine = new SaxoCoherenceEngine();

  // Get balance
  const balance = await client.getBalance();
  console.log(`\n💰 Account Balance: ${balance.currency} ${balance.balance.toFixed(2)}`);
  console.log(`📊 Available: ${balance.currency} ${balance.available.toFixed(2)}`);

  // Get positions
  const positions = await client.getPositions();
  console.log(`\n📈 Open Positions: ${positions.length}`);

  // Start trading loop
  console.log('\n🎵 Starting coherence-based trading...\n');

  const allInstruments = [...FOREX_PAIRS, ...INDEX_CFDS];

  setInterval(async () => {
    try {
      for (const inst of allInstruments) {
        try {
          const price = await client.getPrice(inst.uic, inst.assetType);
          const mid = price.Mid || (price.Bid + price.Ask) / 2;
          
          engine.addPrice(inst.uic, mid);
          
          const signal = engine.getSignal(inst.uic);
          const coherence = engine.calculateCoherence(inst.uic);

          if (signal !== 'HOLD' && coherence >= 0.938) {
            console.log(`
  🎯 SIGNAL: ${signal} ${inst.name} (${inst.symbol})
     Bid: ${price.Bid} | Ask: ${price.Ask}
     Coherence: ${(coherence * 100).toFixed(1)}%
            `);
          }
        } catch (err) {
          // Skip unavailable instruments
        }
      }
    } catch (error) {
      console.error('Trading loop error:', error);
    }
  }, CONFIG.SCAN_INTERVAL);
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('saxoBankApi');
if (isMainModule) {
  main().catch(console.error);
}
