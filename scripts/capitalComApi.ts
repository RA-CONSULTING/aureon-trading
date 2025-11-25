/**
 * 🎵 CAPITAL.COM API CLIENT 🎵
 * 
 * The Song of Space and Time - Capital.com Edition
 * 
 * Supports:
 * - Stocks, Forex, Indices, Crypto, Commodities
 * - Demo and Live trading
 * - CFD positions with leverage
 * 
 * Setup:
 * 1. Create account at https://capital.com
 * 2. Get API key from Settings → API
 * 3. Set environment variables:
 *    export CAPITAL_API_KEY="your_api_key"
 *    export CAPITAL_API_PASSWORD="your_password"
 *    export CAPITAL_IDENTIFIER="your_email_or_username"
 *    export CAPITAL_DEMO="true"  # or "false" for live
 */

import crypto from 'node:crypto';
import fs from 'node:fs';

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const DEMO_URL = 'https://demo-api-capital.backend-capital.com';
const LIVE_URL = 'https://api-capital.backend-capital.com';

const IS_DEMO = process.env.CAPITAL_DEMO !== 'false';
const BASE_URL = IS_DEMO ? DEMO_URL : LIVE_URL;

const API_KEY = process.env.CAPITAL_API_KEY || '';
const PASSWORD = process.env.CAPITAL_API_PASSWORD || '';
const IDENTIFIER = process.env.CAPITAL_IDENTIFIER || '';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface SessionTokens {
  cst: string;           // Client Session Token
  securityToken: string; // X-SECURITY-TOKEN
}

export interface AccountInfo {
  accountId: string;
  accountName: string;
  balance: number;
  deposit: number;
  profitLoss: number;
  available: number;
  currency: string;
}

export interface MarketInfo {
  epic: string;
  instrumentName: string;
  instrumentType: string;
  bid: number;
  offer: number;
  spread: number;
  minDealSize: number;
  maxDealSize: number;
  marginFactor: number;
  marginFactorUnit: string;
}

export interface Position {
  dealId: string;
  epic: string;
  direction: 'BUY' | 'SELL';
  size: number;
  openLevel: number;
  currentLevel: number;
  pnl: number;
  currency: string;
  createdDate: string;
  stopLevel?: number;
  limitLevel?: number;
}

export interface TradeResult {
  dealReference: string;
  dealId: string;
  status: 'ACCEPTED' | 'REJECTED';
  reason?: string;
  affectedDeals?: Array<{
    dealId: string;
    status: string;
  }>;
}

export interface PriceUpdate {
  epic: string;
  bid: number;
  offer: number;
  updateTime: string;
}

// ═══════════════════════════════════════════════════════════════════════════
// Capital.com API Client
// ═══════════════════════════════════════════════════════════════════════════

export class CapitalComClient {
  private session: SessionTokens | null = null;
  private accountId: string = '';
  
  constructor() {}
  
  // ─────────────────────────────────────────────────────────────────────────
  // Authentication
  // ─────────────────────────────────────────────────────────────────────────
  
  async authenticate(): Promise<boolean> {
    console.log(`  🔐 Authenticating with Capital.com (${IS_DEMO ? 'DEMO' : 'LIVE'})...`);
    
    if (!API_KEY || !PASSWORD || !IDENTIFIER) {
      console.log('  ❌ Missing credentials!');
      console.log('  Set: CAPITAL_API_KEY, CAPITAL_API_PASSWORD, CAPITAL_IDENTIFIER');
      return false;
    }
    
    try {
      const response = await fetch(`${BASE_URL}/api/v1/session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CAP-API-KEY': API_KEY
        },
        body: JSON.stringify({
          identifier: IDENTIFIER,
          password: PASSWORD
        })
      });
      
      if (!response.ok) {
        const error = await response.json();
        console.log(`  ❌ Auth failed: ${error.errorCode || response.status}`);
        return false;
      }
      
      // Get session tokens from headers
      const cst = response.headers.get('CST') || '';
      const securityToken = response.headers.get('X-SECURITY-TOKEN') || '';
      
      if (!cst || !securityToken) {
        console.log('  ❌ No session tokens received');
        return false;
      }
      
      this.session = { cst, securityToken };
      
      // Get account info
      const data = await response.json();
      this.accountId = data.currentAccountId || data.accounts?.[0]?.accountId;
      
      console.log(`  ✅ Authenticated! Account: ${this.accountId}`);
      return true;
      
    } catch (error) {
      console.log(`  ❌ Auth error: ${error}`);
      return false;
    }
  }
  
  private getHeaders(): Record<string, string> {
    if (!this.session) throw new Error('Not authenticated');
    
    return {
      'Content-Type': 'application/json',
      'X-CAP-API-KEY': API_KEY,
      'CST': this.session.cst,
      'X-SECURITY-TOKEN': this.session.securityToken
    };
  }
  
  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET',
    body?: any
  ): Promise<T> {
    const response = await fetch(`${BASE_URL}${endpoint}`, {
      method,
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`API Error ${response.status}: ${error.errorCode || 'Unknown'}`);
    }
    
    return response.json();
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Account
  // ─────────────────────────────────────────────────────────────────────────
  
  async getAccounts(): Promise<AccountInfo[]> {
    const data = await this.request<{ accounts: any[] }>('/api/v1/accounts');
    
    return data.accounts.map(acc => ({
      accountId: acc.accountId,
      accountName: acc.accountName,
      balance: acc.balance.balance,
      deposit: acc.balance.deposit,
      profitLoss: acc.balance.profitLoss,
      available: acc.balance.available,
      currency: acc.currency
    }));
  }
  
  async getAccountBalance(): Promise<AccountInfo> {
    const accounts = await this.getAccounts();
    return accounts.find(a => a.accountId === this.accountId) || accounts[0];
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Markets
  // ─────────────────────────────────────────────────────────────────────────
  
  async searchMarkets(query: string, limit = 20): Promise<MarketInfo[]> {
    const data = await this.request<{ markets: any[] }>(
      `/api/v1/markets?searchTerm=${encodeURIComponent(query)}&limit=${limit}`
    );
    
    return data.markets.map(m => ({
      epic: m.epic,
      instrumentName: m.instrumentName,
      instrumentType: m.instrumentType,
      bid: m.snapshot?.bid || 0,
      offer: m.snapshot?.offer || 0,
      spread: (m.snapshot?.offer || 0) - (m.snapshot?.bid || 0),
      minDealSize: m.dealingRules?.minDealSize?.value || 0,
      maxDealSize: m.dealingRules?.maxDealSize?.value || 0,
      marginFactor: m.marginFactor || 0,
      marginFactorUnit: m.marginFactorUnit || ''
    }));
  }
  
  async getMarketDetails(epic: string): Promise<MarketInfo> {
    const data = await this.request<{ instrument: any; snapshot: any; dealingRules: any }>(
      `/api/v1/markets/${epic}`
    );
    
    return {
      epic: data.instrument.epic,
      instrumentName: data.instrument.name,
      instrumentType: data.instrument.type,
      bid: data.snapshot?.bid || 0,
      offer: data.snapshot?.offer || 0,
      spread: (data.snapshot?.offer || 0) - (data.snapshot?.bid || 0),
      minDealSize: data.dealingRules?.minDealSize?.value || 0,
      maxDealSize: data.dealingRules?.maxDealSize?.value || 0,
      marginFactor: data.instrument.marginFactor || 0,
      marginFactorUnit: data.instrument.marginFactorUnit || ''
    };
  }
  
  async getPrices(epics: string[]): Promise<PriceUpdate[]> {
    const epicList = epics.join(',');
    const data = await this.request<{ marketDetails: any[] }>(
      `/api/v1/markets?epics=${epicList}`
    );
    
    return data.marketDetails.map(m => ({
      epic: m.instrument.epic,
      bid: m.snapshot?.bid || 0,
      offer: m.snapshot?.offer || 0,
      updateTime: m.snapshot?.updateTime || new Date().toISOString()
    }));
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Popular Markets by Category
  // ─────────────────────────────────────────────────────────────────────────
  
  getPopularMarkets(): { [category: string]: string[] } {
    return {
      crypto: [
        'BTCUSD',    // Bitcoin
        'ETHUSD',    // Ethereum
        'SOLUSD',    // Solana
        'XRPUSD',    // Ripple
        'DOGEUSD',   // Dogecoin
        'ADAUSD',    // Cardano
        'AVAXUSD',   // Avalanche
        'DOTUSD',    // Polkadot
        'LINKUSD',   // Chainlink
        'MATICUSD'   // Polygon
      ],
      forex: [
        'EURUSD',    // Euro/USD
        'GBPUSD',    // Pound/USD
        'USDJPY',    // USD/Yen
        'AUDUSD',    // Aussie/USD
        'USDCAD',    // USD/CAD
        'USDCHF',    // USD/Swiss
        'NZDUSD',    // Kiwi/USD
        'EURGBP',    // Euro/Pound
        'EURJPY',    // Euro/Yen
        'GBPJPY'     // Pound/Yen
      ],
      indices: [
        'US500',     // S&P 500
        'US100',     // Nasdaq 100
        'US30',      // Dow Jones
        'UK100',     // FTSE 100
        'DE40',      // DAX 40
        'FR40',      // CAC 40
        'JP225',     // Nikkei 225
        'HK50',      // Hang Seng
        'AU200',     // ASX 200
        'EU50'       // Euro Stoxx 50
      ],
      stocks: [
        'AAPL',      // Apple
        'MSFT',      // Microsoft
        'GOOGL',     // Google
        'AMZN',      // Amazon
        'TSLA',      // Tesla
        'NVDA',      // Nvidia
        'META',      // Meta
        'NFLX',      // Netflix
        'AMD',       // AMD
        'COIN'       // Coinbase
      ],
      commodities: [
        'GOLD',      // Gold
        'SILVER',    // Silver
        'OIL_CRUDE', // Crude Oil
        'NATGAS',    // Natural Gas
        'COPPER',    // Copper
        'PLATINUM',  // Platinum
        'PALLADIUM', // Palladium
        'WHEAT',     // Wheat
        'CORN',      // Corn
        'COFFEE'     // Coffee
      ]
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Positions
  // ─────────────────────────────────────────────────────────────────────────
  
  async getPositions(): Promise<Position[]> {
    const data = await this.request<{ positions: any[] }>('/api/v1/positions');
    
    return data.positions.map(p => ({
      dealId: p.position.dealId,
      epic: p.market.epic,
      direction: p.position.direction,
      size: p.position.size,
      openLevel: p.position.level,
      currentLevel: p.market.bid, // Use bid for sell, offer for buy
      pnl: p.position.upl,
      currency: p.position.currency,
      createdDate: p.position.createdDate,
      stopLevel: p.position.stopLevel,
      limitLevel: p.position.limitLevel
    }));
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Trading
  // ─────────────────────────────────────────────────────────────────────────
  
  async openPosition(
    epic: string,
    direction: 'BUY' | 'SELL',
    size: number,
    stopDistance?: number,
    limitDistance?: number
  ): Promise<TradeResult> {
    const body: any = {
      epic,
      direction,
      size,
      guaranteedStop: false
    };
    
    if (stopDistance) body.stopDistance = stopDistance;
    if (limitDistance) body.limitDistance = limitDistance;
    
    const data = await this.request<any>('/api/v1/positions', 'POST', body);
    
    return {
      dealReference: data.dealReference,
      dealId: data.dealId || '',
      status: data.dealStatus === 'ACCEPTED' ? 'ACCEPTED' : 'REJECTED',
      reason: data.reason,
      affectedDeals: data.affectedDeals
    };
  }
  
  async closePosition(dealId: string): Promise<TradeResult> {
    const data = await this.request<any>(`/api/v1/positions/${dealId}`, 'DELETE');
    
    return {
      dealReference: data.dealReference,
      dealId: dealId,
      status: data.dealStatus === 'ACCEPTED' ? 'ACCEPTED' : 'REJECTED',
      reason: data.reason
    };
  }
  
  async updatePosition(
    dealId: string,
    stopLevel?: number,
    limitLevel?: number
  ): Promise<TradeResult> {
    const body: any = {};
    if (stopLevel !== undefined) body.stopLevel = stopLevel;
    if (limitLevel !== undefined) body.limitLevel = limitLevel;
    
    const data = await this.request<any>(`/api/v1/positions/${dealId}`, 'PUT', body);
    
    return {
      dealReference: data.dealReference,
      dealId: dealId,
      status: data.dealStatus === 'ACCEPTED' ? 'ACCEPTED' : 'REJECTED',
      reason: data.reason
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Orders (Pending)
  // ─────────────────────────────────────────────────────────────────────────
  
  async getOrders(): Promise<any[]> {
    const data = await this.request<{ workingOrders: any[] }>('/api/v1/workingorders');
    return data.workingOrders;
  }
  
  async placeOrder(
    epic: string,
    direction: 'BUY' | 'SELL',
    size: number,
    level: number,
    type: 'LIMIT' | 'STOP' = 'LIMIT',
    goodTillDate?: string
  ): Promise<TradeResult> {
    const body: any = {
      epic,
      direction,
      size,
      level,
      type,
      guaranteedStop: false
    };
    
    if (goodTillDate) body.goodTillDate = goodTillDate;
    
    const data = await this.request<any>('/api/v1/workingorders', 'POST', body);
    
    return {
      dealReference: data.dealReference,
      dealId: data.dealId || '',
      status: data.dealStatus === 'ACCEPTED' ? 'ACCEPTED' : 'REJECTED',
      reason: data.reason
    };
  }
  
  async cancelOrder(dealId: string): Promise<TradeResult> {
    const data = await this.request<any>(`/api/v1/workingorders/${dealId}`, 'DELETE');
    
    return {
      dealReference: data.dealReference,
      dealId: dealId,
      status: data.dealStatus === 'ACCEPTED' ? 'ACCEPTED' : 'REJECTED',
      reason: data.reason
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // History
  // ─────────────────────────────────────────────────────────────────────────
  
  async getTradeHistory(from?: Date, to?: Date): Promise<any[]> {
    let endpoint = '/api/v1/history/transactions';
    const params: string[] = [];
    
    if (from) params.push(`from=${from.toISOString()}`);
    if (to) params.push(`to=${to.toISOString()}`);
    
    if (params.length) endpoint += '?' + params.join('&');
    
    const data = await this.request<{ transactions: any[] }>(endpoint);
    return data.transactions;
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Utility
  // ─────────────────────────────────────────────────────────────────────────
  
  async ping(): Promise<boolean> {
    try {
      await this.request('/api/v1/ping');
      return true;
    } catch {
      return false;
    }
  }
  
  async logout(): Promise<void> {
    try {
      await this.request('/api/v1/session', 'DELETE');
      this.session = null;
      console.log('  📤 Logged out');
    } catch (e) {
      // Ignore logout errors
    }
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Test / Demo
// ═══════════════════════════════════════════════════════════════════════════

async function demo() {
  console.log('\n');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('  ✧  C A P I T A L . C O M   A P I   C L I E N T  ✧');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('');
  
  const client = new CapitalComClient();
  
  // Authenticate
  const success = await client.authenticate();
  if (!success) {
    console.log('');
    console.log('  📋 Setup Instructions:');
    console.log('');
    console.log('  1. Create account at https://capital.com');
    console.log('  2. Go to Settings → API Management');
    console.log('  3. Create API key');
    console.log('  4. Set environment variables:');
    console.log('');
    console.log('     export CAPITAL_API_KEY="your_api_key"');
    console.log('     export CAPITAL_API_PASSWORD="your_password"');
    console.log('     export CAPITAL_IDENTIFIER="your_email"');
    console.log('     export CAPITAL_DEMO="true"');
    console.log('');
    console.log('  5. Run: npm run capital');
    console.log('');
    return;
  }
  
  console.log('');
  
  // Get account info
  console.log('  📊 Account Info:');
  const account = await client.getAccountBalance();
  console.log(`     Balance: ${account.currency} ${account.balance.toFixed(2)}`);
  console.log(`     Available: ${account.currency} ${account.available.toFixed(2)}`);
  console.log(`     P&L: ${account.currency} ${account.profitLoss.toFixed(2)}`);
  console.log('');
  
  // Show popular markets
  console.log('  🌍 Available Markets:');
  const markets = client.getPopularMarkets();
  Object.entries(markets).forEach(([category, symbols]) => {
    console.log(`     ${category.toUpperCase()}: ${symbols.slice(0, 5).join(', ')}...`);
  });
  console.log('');
  
  // Search for a market
  console.log('  🔍 Searching for Bitcoin...');
  const btcMarkets = await client.searchMarkets('Bitcoin', 3);
  btcMarkets.forEach(m => {
    console.log(`     ${m.epic}: ${m.instrumentName} | Bid: ${m.bid} | Offer: ${m.offer}`);
  });
  console.log('');
  
  // Get open positions
  console.log('  📈 Open Positions:');
  const positions = await client.getPositions();
  if (positions.length === 0) {
    console.log('     No open positions');
  } else {
    positions.forEach(p => {
      const emoji = p.pnl >= 0 ? '🟢' : '🔴';
      console.log(`     ${emoji} ${p.epic}: ${p.direction} ${p.size} @ ${p.openLevel} | P&L: ${p.pnl.toFixed(2)}`);
    });
  }
  console.log('');
  
  // Logout
  await client.logout();
  
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('  🎵 "Dance through stocks, forex, and crypto with Capital!" 🎵');
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('');
}

// Run demo if executed directly
if (process.argv[1]?.includes('capitalComApi')) {
  demo().catch(console.error);
}

export default CapitalComClient;
