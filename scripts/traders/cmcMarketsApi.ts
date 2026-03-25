/**
 * 🇬🇧 CMC MARKETS API 🇬🇧
 * 
 * UK-based, FCA regulated broker
 * Spread Betting & CFDs
 * 
 * Assets:
 * - Forex (330+ pairs)
 * - Indices
 * - Commodities
 * - Shares (9000+)
 * - Crypto
 * - Treasuries
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
  API_KEY: process.env.CMC_API_KEY || '',
  ACCOUNT_ID: process.env.CMC_ACCOUNT_ID || '',
  PASSWORD: process.env.CMC_PASSWORD || '',
  
  // API Endpoints (CMC uses a different structure)
  BASE_URL: process.env.CMC_DEMO === 'true'
    ? 'https://ciapi.cityindex.com/TradingAPI'
    : 'https://ciapi.cmcmarkets.com/TradingAPI',
  
  // Trading settings
  RISK_PERCENT: 2,
  TAKE_PROFIT_POINTS: 20,
  STOP_LOSS_POINTS: 10,
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 10,
  
  // Spread betting (tax-free in UK)
  USE_SPREAD_BETTING: true,
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface CMCSession {
  session: string;
  accountId: number;
  username: string;
}

export interface CMCPosition {
  orderId: number;
  marketId: number;
  marketName: string;
  direction: 'buy' | 'sell';
  quantity: number;
  price: number;
  currentPrice: number;
  pnl: number;
  stopLoss?: number;
  takeProfit?: number;
  createdDate: string;
}

export interface CMCMarket {
  marketId: number;
  name: string;
  exchangeId: number;
  marketType: string;
  bid: number;
  offer: number;
  high: number;
  low: number;
  change: number;
  percentChange: number;
  spreadBetting: boolean;
}

export interface CMCOrder {
  orderId: number;
  marketId: number;
  direction: 'buy' | 'sell';
  quantity: number;
  price: number;
  status: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Instruments
// ═══════════════════════════════════════════════════════════════════════════

// Forex Markets
const FOREX_MARKETS = [
  { marketId: 400616150, name: 'EUR/USD', symbol: 'EURUSD' },
  { marketId: 400616157, name: 'GBP/USD', symbol: 'GBPUSD' },
  { marketId: 400616170, name: 'USD/JPY', symbol: 'USDJPY' },
  { marketId: 400616153, name: 'EUR/GBP', symbol: 'EURGBP' },
  { marketId: 400616143, name: 'AUD/USD', symbol: 'AUDUSD' },
  { marketId: 400616168, name: 'USD/CHF', symbol: 'USDCHF' },
  { marketId: 400616167, name: 'USD/CAD', symbol: 'USDCAD' },
  { marketId: 400616161, name: 'NZD/USD', symbol: 'NZDUSD' },
  { marketId: 400616155, name: 'EUR/JPY', symbol: 'EURJPY' },
  { marketId: 400616158, name: 'GBP/JPY', symbol: 'GBPJPY' },
];

// Index Markets
const INDEX_MARKETS = [
  { marketId: 400616508, name: 'UK 100', symbol: 'UK100' },
  { marketId: 400616492, name: 'Germany 40', symbol: 'GER40' },
  { marketId: 400616548, name: 'Wall Street', symbol: 'US30' },
  { marketId: 400616545, name: 'US Tech 100', symbol: 'USTEC' },
  { marketId: 400616544, name: 'US 500', symbol: 'US500' },
  { marketId: 400616499, name: 'Japan 225', symbol: 'JPN225' },
  { marketId: 400616490, name: 'France 40', symbol: 'FRA40' },
  { marketId: 400616487, name: 'EU Stocks 50', symbol: 'EU50' },
];

// Commodity Markets
const COMMODITY_MARKETS = [
  { marketId: 400616407, name: 'Gold', symbol: 'XAUUSD' },
  { marketId: 400616408, name: 'Silver', symbol: 'XAGUSD' },
  { marketId: 400616413, name: 'US Crude Oil', symbol: 'USOIL' },
  { marketId: 400616416, name: 'Brent Crude', symbol: 'UKOIL' },
  { marketId: 400616401, name: 'Copper', symbol: 'COPPER' },
  { marketId: 400616411, name: 'Natural Gas', symbol: 'NATGAS' },
  { marketId: 400616414, name: 'Platinum', symbol: 'PLATINUM' },
  { marketId: 400616412, name: 'Palladium', symbol: 'PALLADIUM' },
];

// UK Shares
const UK_SHARES = [
  { marketId: 400750001, name: 'HSBC Holdings', symbol: 'HSBA.L' },
  { marketId: 400750002, name: 'BP PLC', symbol: 'BP.L' },
  { marketId: 400750003, name: 'Shell PLC', symbol: 'SHEL.L' },
  { marketId: 400750004, name: 'AstraZeneca', symbol: 'AZN.L' },
  { marketId: 400750005, name: 'GSK PLC', symbol: 'GSK.L' },
  { marketId: 400750006, name: 'Unilever', symbol: 'ULVR.L' },
  { marketId: 400750007, name: 'Barclays', symbol: 'BARC.L' },
  { marketId: 400750008, name: 'Lloyds Banking', symbol: 'LLOY.L' },
];

// Crypto Markets
const CRYPTO_MARKETS = [
  { marketId: 400750100, name: 'Bitcoin/USD', symbol: 'BTCUSD' },
  { marketId: 400750101, name: 'Ethereum/USD', symbol: 'ETHUSD' },
  { marketId: 400750102, name: 'Ripple/USD', symbol: 'XRPUSD' },
  { marketId: 400750103, name: 'Litecoin/USD', symbol: 'LTCUSD' },
  { marketId: 400750104, name: 'Bitcoin Cash/USD', symbol: 'BCHUSD' },
];

// ═══════════════════════════════════════════════════════════════════════════
// CMC Markets Client
// ═══════════════════════════════════════════════════════════════════════════

class CMCMarketsClient {
  private baseUrl: string;
  private session: string = '';
  private accountId: number = 0;
  private authenticated: boolean = false;

  constructor() {
    this.baseUrl = CONFIG.BASE_URL;
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any
  ): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.session) {
      headers['Session'] = this.session;
      headers['UserName'] = CONFIG.ACCOUNT_ID;
    }

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
        throw new Error(`CMC API Error: ${response.status} - ${error}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`CMC Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Authentication
  // ═══════════════════════════════════════════════════════════════════════

  async authenticate(): Promise<boolean> {
    try {
      const response = await this.request('/session', 'POST', {
        UserName: CONFIG.ACCOUNT_ID,
        Password: CONFIG.PASSWORD,
        AppKey: CONFIG.API_KEY,
      });

      this.session = response.Session;
      this.accountId = response.TradingAccounts?.[0]?.TradingAccountId || 0;
      this.authenticated = true;
      
      console.log('✅ CMC Markets authenticated');
      console.log(`   Account: ${this.accountId}`);
      
      return true;
    } catch (error) {
      console.error('❌ CMC Authentication failed:', error);
      return false;
    }
  }

  async logout(): Promise<void> {
    if (this.authenticated) {
      await this.request('/session', 'DELETE');
      this.authenticated = false;
    }
  }

  async keepAlive(): Promise<void> {
    await this.request('/session/validate', 'POST');
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account Info
  // ═══════════════════════════════════════════════════════════════════════

  async getAccountInfo(): Promise<any> {
    const response = await this.request('/useraccount/ClientAndTradingAccount');
    return response;
  }

  async getBalance(): Promise<{ balance: number; equity: number; margin: number; available: number }> {
    const response = await this.request(`/margin/ClientAccountMargin`);
    
    return {
      balance: response.Cash || 0,
      equity: response.Equity || 0,
      margin: response.Margin || 0,
      available: response.CashAvailable || 0,
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Market Data
  // ═══════════════════════════════════════════════════════════════════════

  async searchMarkets(searchTerm: string, maxResults: number = 20): Promise<any[]> {
    const response = await this.request(
      `/market/search?SearchByMarketName=true&Query=${encodeURIComponent(searchTerm)}&MaxResults=${maxResults}`
    );
    return response.Markets || [];
  }

  async getMarketInfo(marketId: number): Promise<CMCMarket | null> {
    const response = await this.request(`/market/${marketId}/information`);
    
    if (!response) return null;
    
    return {
      marketId: response.MarketId,
      name: response.Name,
      exchangeId: response.ExchangeId,
      marketType: response.MarketType,
      bid: response.Bid,
      offer: response.Offer,
      high: response.High,
      low: response.Low,
      change: response.Change,
      percentChange: response.PercentageChange,
      spreadBetting: response.SpreadBettingAllowed,
    };
  }

  async getPrices(marketIds: number[]): Promise<CMCMarket[]> {
    const ids = marketIds.join(',');
    const response = await this.request(`/market/price?MarketIds=${ids}`);
    
    return (response.Prices || []).map((p: any) => ({
      marketId: p.MarketId,
      name: p.Name,
      bid: p.Bid,
      offer: p.Offer,
      high: p.High,
      low: p.Low,
      change: p.Change,
      percentChange: p.PercentageChange,
    }));
  }

  async getPriceHistory(
    marketId: number,
    interval: 'MINUTE' | 'HOUR' | 'DAY' = 'MINUTE',
    numTicks: number = 100
  ): Promise<any> {
    const response = await this.request(
      `/market/${marketId}/barhistory?interval=${interval}&span=1&PriceBars=${numTicks}`
    );
    return response.PriceBars || [];
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getOpenPositions(): Promise<CMCPosition[]> {
    const response = await this.request('/order/openpositions');
    
    return (response.OpenPositions || []).map((p: any) => ({
      orderId: p.OrderId,
      marketId: p.MarketId,
      marketName: p.MarketName,
      direction: p.Direction.toLowerCase(),
      quantity: p.Quantity,
      price: p.Price,
      currentPrice: p.CurrentPrice,
      pnl: p.UnrealisedPnL,
      stopLoss: p.Stop?.OrderId ? p.Stop.TriggerPrice : undefined,
      takeProfit: p.Limit?.OrderId ? p.Limit.TriggerPrice : undefined,
      createdDate: p.CreatedDateTimeUtc,
    }));
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async placeOrder(
    marketId: number,
    direction: 'buy' | 'sell',
    quantity: number,
    stopLoss?: number,
    takeProfit?: number
  ): Promise<CMCOrder> {
    const orderPayload: any = {
      MarketId: marketId,
      Direction: direction,
      Quantity: quantity,
      TradingAccountId: this.accountId,
      Type: 'Market',
    };

    if (stopLoss) {
      orderPayload.IfDone = orderPayload.IfDone || [];
      orderPayload.IfDone.push({
        Stop: {
          TriggerPrice: stopLoss,
          Direction: direction === 'buy' ? 'sell' : 'buy',
        }
      });
    }

    if (takeProfit) {
      orderPayload.IfDone = orderPayload.IfDone || [];
      orderPayload.IfDone.push({
        Limit: {
          TriggerPrice: takeProfit,
          Direction: direction === 'buy' ? 'sell' : 'buy',
        }
      });
    }

    const response = await this.request('/order/newtradeorder', 'POST', orderPayload);
    
    return {
      orderId: response.OrderId,
      marketId,
      direction,
      quantity,
      price: response.Price,
      status: response.Status,
    };
  }

  async closePosition(orderId: number): Promise<boolean> {
    try {
      const positions = await this.getOpenPositions();
      const position = positions.find(p => p.orderId === orderId);
      
      if (!position) return false;

      await this.request('/order/newtradeorder', 'POST', {
        MarketId: position.marketId,
        Direction: position.direction === 'buy' ? 'sell' : 'buy',
        Quantity: position.quantity,
        TradingAccountId: this.accountId,
        Type: 'Market',
        Close: [orderId],
      });
      
      return true;
    } catch {
      return false;
    }
  }

  async updateOrder(
    orderId: number,
    stopLoss?: number,
    takeProfit?: number
  ): Promise<boolean> {
    try {
      await this.request('/order/updatetradeorder', 'POST', {
        OrderId: orderId,
        TradingAccountId: this.accountId,
        IfDone: [
          stopLoss ? { Stop: { TriggerPrice: stopLoss } } : null,
          takeProfit ? { Limit: { TriggerPrice: takeProfit } } : null,
        ].filter(Boolean),
      });
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Working Orders
  // ═══════════════════════════════════════════════════════════════════════

  async getWorkingOrders(): Promise<any[]> {
    const response = await this.request('/order/activeorders');
    return response.ActiveOrders || [];
  }

  async cancelOrder(orderId: number): Promise<boolean> {
    try {
      await this.request('/order/cancel', 'POST', { OrderId: orderId });
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Trade History
  // ═══════════════════════════════════════════════════════════════════════

  async getTradeHistory(maxResults: number = 100): Promise<any[]> {
    const response = await this.request(`/order/tradehistory?MaxResults=${maxResults}`);
    return response.TradeHistory || [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class CMCCoherenceEngine {
  private priceHistory: Map<number, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(marketId: number, price: number): void {
    if (!this.priceHistory.has(marketId)) {
      this.priceHistory.set(marketId, []);
    }
    const history = this.priceHistory.get(marketId)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(marketId: number): number {
    const history = this.priceHistory.get(marketId);
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

  getSignal(marketId: number): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(marketId);
    const history = this.priceHistory.get(marketId);

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

export default CMCMarketsClient;
export {
  CMCMarketsClient,
  CMCCoherenceEngine,
  FOREX_MARKETS as CMC_FOREX,
  INDEX_MARKETS as CMC_INDICES,
  COMMODITY_MARKETS as CMC_COMMODITIES,
  UK_SHARES as CMC_UK_SHARES,
  CRYPTO_MARKETS as CMC_CRYPTO,
  CONFIG as CMC_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🇬🇧 CMC MARKETS TRADER 🇬🇧                                                   ║
  ║                                                                               ║
  ║   FCA Regulated • Spread Betting (TAX FREE!) • UK Based                       ║
  ║                                                                               ║
  ║   Markets:                                                                    ║
  ║   • 330+ Forex Pairs                                                          ║
  ║   • Global Indices                                                            ║
  ║   • Commodities                                                               ║
  ║   • 9000+ Shares                                                              ║
  ║   • Cryptocurrencies                                                          ║
  ║                                                                               ║
  ║   💰 Spread Betting = Tax-Free Profits in UK!                                ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.ACCOUNT_ID || !CONFIG.PASSWORD) {
    console.log('❌ Missing CMC Markets credentials!');
    console.log('\nTo set up CMC Markets:');
    console.log('1. Create account at https://www.cmcmarkets.com/');
    console.log('2. Apply for API access');
    console.log('3. Add to .env:');
    console.log('   CMC_API_KEY=your_api_key');
    console.log('   CMC_ACCOUNT_ID=your_account_id');
    console.log('   CMC_PASSWORD=your_password');
    console.log('   CMC_DEMO=true  # Use demo account first');
    console.log('\n📖 Docs: https://www.cmcmarkets.com/en-gb/trading-guides/api');
    return;
  }

  const client = new CMCMarketsClient();
  const engine = new CMCCoherenceEngine();

  // Authenticate
  const authenticated = await client.authenticate();
  if (!authenticated) {
    console.log('❌ Failed to authenticate with CMC Markets');
    return;
  }

  // Get account info
  const balance = await client.getBalance();
  console.log(`\n💰 Account Balance: £${balance.balance.toFixed(2)}`);
  console.log(`📊 Equity: £${balance.equity.toFixed(2)}`);
  console.log(`📈 Available: £${balance.available.toFixed(2)}`);

  // Start trading loop
  console.log('\n🎵 Starting coherence-based spread betting...\n');

  const allMarkets = [...FOREX_MARKETS, ...INDEX_MARKETS, ...COMMODITY_MARKETS];
  const marketIds = allMarkets.map(m => m.marketId);

  // Keep session alive
  setInterval(() => client.keepAlive(), 60000);

  setInterval(async () => {
    try {
      const prices = await client.getPrices(marketIds);

      for (const price of prices) {
        const midPrice = (price.bid + price.offer) / 2;
        engine.addPrice(price.marketId, midPrice);
        
        const signal = engine.getSignal(price.marketId);
        const coherence = engine.calculateCoherence(price.marketId);

        if (signal !== 'HOLD' && coherence >= 0.938) {
          const marketInfo = allMarkets.find(m => m.marketId === price.marketId);
          console.log(`
  🎯 SIGNAL: ${signal} ${marketInfo?.name}
     Bid: ${price.bid} | Offer: ${price.offer}
     Coherence: ${(coherence * 100).toFixed(1)}%
     Change: ${price.percentChange?.toFixed(2)}%
          `);
        }
      }
    } catch (error) {
      console.error('Trading loop error:', error);
    }
  }, CONFIG.SCAN_INTERVAL);
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('cmcMarketsApi');
if (isMainModule) {
  main().catch(console.error);
}
