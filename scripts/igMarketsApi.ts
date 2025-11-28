/**
 * 🇬🇧 IG MARKETS API 🇬🇧
 * 
 * UK-based, FCA regulated broker
 * SPREAD BETTING = TAX FREE PROFITS in UK!
 * 
 * Assets:
 * - Forex
 * - Indices
 * - Commodities
 * - Shares (CFD & Spread Betting)
 * - Crypto
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
  API_KEY: process.env.IG_API_KEY || '',
  USERNAME: process.env.IG_USERNAME || '',
  PASSWORD: process.env.IG_PASSWORD || '',
  
  // API Endpoints
  BASE_URL: process.env.IG_DEMO === 'true' 
    ? 'https://demo-api.ig.com/gateway/deal'
    : 'https://api.ig.com/gateway/deal',
  
  // Trading settings
  RISK_PERCENT: 2,
  TAKE_PROFIT_POINTS: 20,
  STOP_LOSS_POINTS: 10,
  SCAN_INTERVAL: 5000,
  MAX_POSITIONS: 10,
  
  // Spread betting vs CFD
  USE_SPREAD_BETTING: true, // Tax-free in UK!
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface IGSession {
  clientId: string;
  accountId: string;
  timezoneOffset: number;
  lightstreamerEndpoint: string;
  cst: string;
  securityToken: string;
}

export interface IGPosition {
  dealId: string;
  epic: string;
  direction: 'BUY' | 'SELL';
  size: number;
  openLevel: number;
  currentLevel: number;
  pnl: number;
  stopLevel?: number;
  limitLevel?: number;
  createdDate: string;
}

export interface IGMarket {
  epic: string;
  instrumentName: string;
  instrumentType: string;
  expiry: string;
  high: number;
  low: number;
  bid: number;
  offer: number;
  percentageChange: number;
  netChange: number;
  updateTime: string;
  marketStatus: string;
  scalingFactor: number;
}

export interface IGOrder {
  dealId: string;
  dealReference: string;
  status: string;
  reason: string;
  epic: string;
  direction: 'BUY' | 'SELL';
  size: number;
  level: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Trading Instruments (EPICs)
// ═══════════════════════════════════════════════════════════════════════════

// Forex (Spread Betting)
const FOREX_MARKETS = [
  { epic: 'CS.D.EURUSD.TODAY.IP', name: 'EUR/USD', minSize: 0.5 },
  { epic: 'CS.D.GBPUSD.TODAY.IP', name: 'GBP/USD', minSize: 0.5 },
  { epic: 'CS.D.USDJPY.TODAY.IP', name: 'USD/JPY', minSize: 0.5 },
  { epic: 'CS.D.EURGBP.TODAY.IP', name: 'EUR/GBP', minSize: 0.5 },
  { epic: 'CS.D.AUDUSD.TODAY.IP', name: 'AUD/USD', minSize: 0.5 },
  { epic: 'CS.D.USDCHF.TODAY.IP', name: 'USD/CHF', minSize: 0.5 },
  { epic: 'CS.D.USDCAD.TODAY.IP', name: 'USD/CAD', minSize: 0.5 },
  { epic: 'CS.D.NZDUSD.TODAY.IP', name: 'NZD/USD', minSize: 0.5 },
];

// Indices (Spread Betting)
const INDEX_MARKETS = [
  { epic: 'IX.D.FTSE.DAILY.IP', name: 'FTSE 100', minSize: 0.5 },
  { epic: 'IX.D.DAX.DAILY.IP', name: 'Germany 40', minSize: 0.5 },
  { epic: 'IX.D.DOW.DAILY.IP', name: 'Wall Street', minSize: 0.5 },
  { epic: 'IX.D.NASDAQ.DAILY.IP', name: 'US Tech 100', minSize: 0.5 },
  { epic: 'IX.D.SPTRD.DAILY.IP', name: 'US 500', minSize: 0.5 },
  { epic: 'IX.D.NIKKEI.DAILY.IP', name: 'Japan 225', minSize: 0.5 },
];

// Commodities (Spread Betting)
const COMMODITY_MARKETS = [
  { epic: 'CS.D.USCGC.TODAY.IP', name: 'Gold', minSize: 0.5 },
  { epic: 'CS.D.USCSI.TODAY.IP', name: 'Silver', minSize: 0.5 },
  { epic: 'CS.D.USOIL.TODAY.IP', name: 'US Crude Oil', minSize: 0.5 },
  { epic: 'CS.D.BRENT.TODAY.IP', name: 'Brent Crude', minSize: 0.5 },
  { epic: 'CS.D.COPPER.TODAY.IP', name: 'Copper', minSize: 0.5 },
  { epic: 'CS.D.NATGAS.TODAY.IP', name: 'Natural Gas', minSize: 0.5 },
];

// UK Shares (Spread Betting)
const UK_SHARE_MARKETS = [
  { epic: 'KA.D.HSBA.DAILY.IP', name: 'HSBC', minSize: 1 },
  { epic: 'KA.D.BP.DAILY.IP', name: 'BP', minSize: 1 },
  { epic: 'KA.D.SHEL.DAILY.IP', name: 'Shell', minSize: 1 },
  { epic: 'KA.D.AZN.DAILY.IP', name: 'AstraZeneca', minSize: 1 },
  { epic: 'KA.D.GSK.DAILY.IP', name: 'GSK', minSize: 1 },
  { epic: 'KA.D.BARC.DAILY.IP', name: 'Barclays', minSize: 1 },
  { epic: 'KA.D.LLOY.DAILY.IP', name: 'Lloyds', minSize: 1 },
  { epic: 'KA.D.VOD.DAILY.IP', name: 'Vodafone', minSize: 1 },
];

// Crypto (Spread Betting)
const CRYPTO_MARKETS = [
  { epic: 'CS.D.BITCOIN.TODAY.IP', name: 'Bitcoin', minSize: 0.1 },
  { epic: 'CS.D.ETHUSD.TODAY.IP', name: 'Ethereum', minSize: 0.1 },
  { epic: 'CS.D.XRPUSD.TODAY.IP', name: 'Ripple', minSize: 1 },
  { epic: 'CS.D.LTCUSD.TODAY.IP', name: 'Litecoin', minSize: 0.5 },
];

// ═══════════════════════════════════════════════════════════════════════════
// IG Markets Client
// ═══════════════════════════════════════════════════════════════════════════

class IGMarketsClient {
  private baseUrl: string;
  private apiKey: string;
  private cst: string = '';
  private securityToken: string = '';
  private accountId: string = '';
  private authenticated: boolean = false;

  constructor() {
    this.baseUrl = CONFIG.BASE_URL;
    this.apiKey = CONFIG.API_KEY;
  }

  private async request(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any,
    version: number = 1
  ): Promise<any> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'Accept': 'application/json; charset=UTF-8',
      'X-IG-API-KEY': this.apiKey,
      'Version': version.toString(),
    };

    if (this.cst) {
      headers['CST'] = this.cst;
      headers['X-SECURITY-TOKEN'] = this.securityToken;
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
      
      // Update tokens from response headers
      if (response.headers.get('CST')) {
        this.cst = response.headers.get('CST') || '';
        this.securityToken = response.headers.get('X-SECURITY-TOKEN') || '';
      }

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`IG API Error: ${response.status} - ${error}`);
      }

      const text = await response.text();
      return text ? JSON.parse(text) : {};
    } catch (error) {
      console.error(`IG Request failed: ${endpoint}`, error);
      throw error;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Authentication
  // ═══════════════════════════════════════════════════════════════════════

  async authenticate(): Promise<boolean> {
    try {
      const response = await this.request('/session', 'POST', {
        identifier: CONFIG.USERNAME,
        password: CONFIG.PASSWORD,
      }, 3);

      this.accountId = response.currentAccountId;
      this.authenticated = true;
      
      console.log('✅ IG Markets authenticated');
      console.log(`   Account: ${this.accountId}`);
      
      return true;
    } catch (error) {
      console.error('❌ IG Authentication failed:', error);
      return false;
    }
  }

  async logout(): Promise<void> {
    if (this.authenticated) {
      await this.request('/session', 'DELETE');
      this.authenticated = false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Account Info
  // ═══════════════════════════════════════════════════════════════════════

  async getAccounts(): Promise<any[]> {
    const response = await this.request('/accounts');
    return response.accounts || [];
  }

  async getBalance(): Promise<{ balance: number; available: number; pnl: number; currency: string }> {
    const response = await this.request('/accounts');
    const account = response.accounts.find((a: any) => a.accountId === this.accountId);
    
    return {
      balance: account?.balance?.balance || 0,
      available: account?.balance?.available || 0,
      pnl: account?.balance?.profitLoss || 0,
      currency: account?.currency || 'GBP',
    };
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Market Data
  // ═══════════════════════════════════════════════════════════════════════

  async getMarkets(epics: string[]): Promise<IGMarket[]> {
    const epicStr = epics.join(',');
    const response = await this.request(`/markets?epics=${epicStr}`, 'GET', undefined, 2);
    
    return (response.marketDetails || []).map((m: any) => ({
      epic: m.instrument.epic,
      instrumentName: m.instrument.name,
      instrumentType: m.instrument.type,
      expiry: m.instrument.expiry,
      high: m.snapshot.high,
      low: m.snapshot.low,
      bid: m.snapshot.bid,
      offer: m.snapshot.offer,
      percentageChange: m.snapshot.percentageChange,
      netChange: m.snapshot.netChange,
      updateTime: m.snapshot.updateTime,
      marketStatus: m.snapshot.marketStatus,
      scalingFactor: m.snapshot.scalingFactor,
    }));
  }

  async getMarket(epic: string): Promise<IGMarket | null> {
    const markets = await this.getMarkets([epic]);
    return markets[0] || null;
  }

  async searchMarkets(searchTerm: string): Promise<any[]> {
    const response = await this.request(`/markets?searchTerm=${encodeURIComponent(searchTerm)}`);
    return response.markets || [];
  }

  async getPrices(
    epic: string,
    resolution: string = 'MINUTE_5',
    numPoints: number = 50
  ): Promise<any> {
    const response = await this.request(
      `/prices/${epic}?resolution=${resolution}&max=${numPoints}`,
      'GET',
      undefined,
      3
    );
    return response;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Positions
  // ═══════════════════════════════════════════════════════════════════════

  async getPositions(): Promise<IGPosition[]> {
    const response = await this.request('/positions', 'GET', undefined, 2);
    
    return (response.positions || []).map((p: any) => ({
      dealId: p.position.dealId,
      epic: p.market.epic,
      direction: p.position.direction,
      size: p.position.size,
      openLevel: p.position.openLevel,
      currentLevel: p.market.bid,
      pnl: p.position.profit,
      stopLevel: p.position.stopLevel,
      limitLevel: p.position.limitLevel,
      createdDate: p.position.createdDate,
    }));
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Orders
  // ═══════════════════════════════════════════════════════════════════════

  async openPosition(
    epic: string,
    direction: 'BUY' | 'SELL',
    size: number,
    stopDistance?: number,
    limitDistance?: number
  ): Promise<IGOrder> {
    const market = await this.getMarket(epic);
    if (!market) throw new Error(`Market not found: ${epic}`);

    const orderPayload: any = {
      epic,
      expiry: '-', // Spread bet = daily funded bet
      direction,
      size,
      orderType: 'MARKET',
      currencyCode: 'GBP',
      forceOpen: true,
      guaranteedStop: false,
    };

    if (stopDistance) {
      orderPayload.stopDistance = stopDistance;
    }
    if (limitDistance) {
      orderPayload.limitDistance = limitDistance;
    }

    const response = await this.request('/positions/otc', 'POST', orderPayload, 2);
    
    // Confirm the deal
    const confirmation = await this.request(`/confirms/${response.dealReference}`);
    
    return {
      dealId: confirmation.dealId,
      dealReference: response.dealReference,
      status: confirmation.dealStatus,
      reason: confirmation.reason,
      epic: confirmation.epic,
      direction: confirmation.direction,
      size: confirmation.size,
      level: confirmation.level,
    };
  }

  async closePosition(dealId: string, size?: number): Promise<IGOrder> {
    const positions = await this.getPositions();
    const position = positions.find(p => p.dealId === dealId);
    
    if (!position) throw new Error(`Position not found: ${dealId}`);

    const closeDirection = position.direction === 'BUY' ? 'SELL' : 'BUY';
    const closeSize = size || position.size;

    const response = await this.request('/positions/otc', 'POST', {
      dealId,
      direction: closeDirection,
      size: closeSize,
      orderType: 'MARKET',
    }, 1);

    const confirmation = await this.request(`/confirms/${response.dealReference}`);
    
    return {
      dealId: confirmation.dealId,
      dealReference: response.dealReference,
      status: confirmation.dealStatus,
      reason: confirmation.reason,
      epic: confirmation.epic,
      direction: closeDirection,
      size: closeSize,
      level: confirmation.level,
    };
  }

  async updatePosition(
    dealId: string,
    stopLevel?: number,
    limitLevel?: number
  ): Promise<any> {
    const response = await this.request(`/positions/otc/${dealId}`, 'PUT', {
      stopLevel,
      limitLevel,
    }, 2);
    return response;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Working Orders
  // ═══════════════════════════════════════════════════════════════════════

  async getWorkingOrders(): Promise<any[]> {
    const response = await this.request('/workingorders', 'GET', undefined, 2);
    return response.workingOrders || [];
  }

  async createWorkingOrder(
    epic: string,
    direction: 'BUY' | 'SELL',
    size: number,
    level: number,
    type: 'LIMIT' | 'STOP' = 'LIMIT',
    stopDistance?: number,
    limitDistance?: number
  ): Promise<any> {
    const response = await this.request('/workingorders/otc', 'POST', {
      epic,
      expiry: '-',
      direction,
      size,
      level,
      type,
      currencyCode: 'GBP',
      timeInForce: 'GOOD_TILL_CANCELLED',
      stopDistance,
      limitDistance,
    }, 2);
    
    return response;
  }

  async deleteWorkingOrder(dealId: string): Promise<boolean> {
    try {
      await this.request(`/workingorders/otc/${dealId}`, 'DELETE');
      return true;
    } catch {
      return false;
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Activity & History
  // ═══════════════════════════════════════════════════════════════════════

  async getActivityHistory(from?: Date, to?: Date): Promise<any[]> {
    let endpoint = '/history/activity';
    const params: string[] = [];
    
    if (from) params.push(`from=${from.toISOString()}`);
    if (to) params.push(`to=${to.toISOString()}`);
    
    if (params.length) endpoint += `?${params.join('&')}`;
    
    const response = await this.request(endpoint, 'GET', undefined, 3);
    return response.activities || [];
  }

  async getTransactionHistory(
    type: 'ALL' | 'DEPOSIT' | 'WITHDRAWAL' | 'ALL_DEAL' = 'ALL_DEAL',
    from?: Date,
    to?: Date
  ): Promise<any[]> {
    let endpoint = `/history/transactions?type=${type}`;
    
    if (from) endpoint += `&from=${from.toISOString()}`;
    if (to) endpoint += `&to=${to.toISOString()}`;
    
    const response = await this.request(endpoint, 'GET', undefined, 2);
    return response.transactions || [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Trading Engine
// ═══════════════════════════════════════════════════════════════════════════

class IGCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;

  addPrice(epic: string, price: number): void {
    if (!this.priceHistory.has(epic)) {
      this.priceHistory.set(epic, []);
    }
    const history = this.priceHistory.get(epic)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }

  calculateCoherence(epic: string): number {
    const history = this.priceHistory.get(epic);
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

  getSignal(epic: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(epic);
    const history = this.priceHistory.get(epic);

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

export default IGMarketsClient;
export {
  IGMarketsClient,
  IGCoherenceEngine,
  FOREX_MARKETS,
  INDEX_MARKETS,
  COMMODITY_MARKETS,
  UK_SHARE_MARKETS,
  CRYPTO_MARKETS,
  CONFIG as IG_CONFIG,
};

// ═══════════════════════════════════════════════════════════════════════════
// Main Trading Loop
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🇬🇧 IG MARKETS TRADER 🇬🇧                                                    ║
  ║                                                                               ║
  ║   FCA Regulated • Spread Betting (TAX FREE!) • UK Based                       ║
  ║                                                                               ║
  ║   Markets:                                                                    ║
  ║   • Forex     - EUR/USD, GBP/USD, USD/JPY...                                 ║
  ║   • Indices   - FTSE 100, DAX, DOW, NASDAQ...                                ║
  ║   • Commodities - Gold, Silver, Oil...                                       ║
  ║   • UK Shares - HSBC, BP, Shell, AstraZeneca...                              ║
  ║   • Crypto    - Bitcoin, Ethereum...                                         ║
  ║                                                                               ║
  ║   💰 Spread Betting = Tax-Free Profits in UK!                                ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  if (!CONFIG.API_KEY || !CONFIG.USERNAME || !CONFIG.PASSWORD) {
    console.log('❌ Missing IG Markets credentials!');
    console.log('\nTo set up IG Markets:');
    console.log('1. Create account at https://www.ig.com/uk');
    console.log('2. Apply for API access in My IG > Settings > API');
    console.log('3. Add to .env:');
    console.log('   IG_API_KEY=your_api_key');
    console.log('   IG_USERNAME=your_username');
    console.log('   IG_PASSWORD=your_password');
    console.log('   IG_DEMO=true  # Use demo account first');
    console.log('\n📖 Docs: https://labs.ig.com/rest-trading-api-reference');
    return;
  }

  const client = new IGMarketsClient();
  const engine = new IGCoherenceEngine();

  // Authenticate
  const authenticated = await client.authenticate();
  if (!authenticated) {
    console.log('❌ Failed to authenticate with IG Markets');
    return;
  }

  // Get account info
  const balance = await client.getBalance();
  console.log(`\n💰 Account Balance: ${balance.currency} ${balance.balance.toFixed(2)}`);
  console.log(`📊 Available: ${balance.currency} ${balance.available.toFixed(2)}`);
  console.log(`📈 P&L: ${balance.currency} ${balance.pnl.toFixed(2)}`);

  // Start trading loop
  console.log('\n🎵 Starting coherence-based spread betting...\n');

  const allMarkets = [...FOREX_MARKETS, ...INDEX_MARKETS, ...COMMODITY_MARKETS];
  const epics = allMarkets.map(m => m.epic);

  setInterval(async () => {
    try {
      const markets = await client.getMarkets(epics);

      for (const market of markets) {
        const midPrice = (market.bid + market.offer) / 2;
        engine.addPrice(market.epic, midPrice);
        
        const signal = engine.getSignal(market.epic);
        const coherence = engine.calculateCoherence(market.epic);

        if (signal !== 'HOLD' && coherence >= 0.938) {
          const marketInfo = allMarkets.find(m => m.epic === market.epic);
          console.log(`
  🎯 SIGNAL: ${signal} ${marketInfo?.name}
     Bid: ${market.bid} | Offer: ${market.offer}
     Coherence: ${(coherence * 100).toFixed(1)}%
     Change: ${market.percentageChange.toFixed(2)}%
          `);
        }
      }
    } catch (error) {
      console.error('Trading loop error:', error);
    }
  }, CONFIG.SCAN_INTERVAL);
}

// Run if executed directly
const isMainModule = process.argv[1]?.includes('igMarketsApi');
if (isMainModule) {
  main().catch(console.error);
}
