/**
 * 🎵 OANDA API CLIENT 🎵
 * 
 * The Song of Space and Time - Forex Edition
 * 
 * Supports:
 * - 70+ Forex pairs
 * - CFDs on Indices, Commodities, Metals, Bonds
 * - Practice/Demo accounts
 * 
 * Setup:
 * 1. Create account at https://oanda.com
 * 2. Get API token from Account → API Access
 * 3. Set environment variables:
 *    export OANDA_API_TOKEN="your_token"
 *    export OANDA_ACCOUNT_ID="your_account_id"
 *    export OANDA_PRACTICE="true"  # or "false" for live
 */

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const PRACTICE_URL = 'https://api-fxpractice.oanda.com';
const LIVE_URL = 'https://api-fxtrade.oanda.com';

const IS_PRACTICE = process.env.OANDA_PRACTICE !== 'false';
const BASE_URL = IS_PRACTICE ? PRACTICE_URL : LIVE_URL;

const API_TOKEN = process.env.OANDA_API_TOKEN || '';
const ACCOUNT_ID = process.env.OANDA_ACCOUNT_ID || '';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface AccountSummary {
  id: string;
  currency: string;
  balance: number;
  unrealizedPL: number;
  realizedPL: number;
  marginUsed: number;
  marginAvailable: number;
  openTradeCount: number;
  openPositionCount: number;
}

export interface Instrument {
  name: string;
  type: string;
  displayName: string;
  pipLocation: number;
  minimumTradeSize: number;
  maximumTradeSize: number;
  marginRate: number;
}

export interface PriceTick {
  instrument: string;
  bid: number;
  ask: number;
  spread: number;
  time: string;
}

export interface Trade {
  id: string;
  instrument: string;
  currentUnits: number;
  price: number;
  unrealizedPL: number;
  realizedPL: number;
  state: string;
  openTime: string;
  takeProfitPrice?: number;
  stopLossPrice?: number;
}

export interface OrderResponse {
  orderCreateTransaction?: {
    id: string;
    type: string;
    instrument: string;
    units: string;
  };
  orderFillTransaction?: {
    id: string;
    price: string;
    pl: string;
  };
  orderCancelTransaction?: {
    id: string;
    reason: string;
  };
}

// ═══════════════════════════════════════════════════════════════════════════
// OANDA API Client
// ═══════════════════════════════════════════════════════════════════════════

export class OandaClient {
  
  constructor() {}
  
  private getHeaders(): Record<string, string> {
    return {
      'Authorization': `Bearer ${API_TOKEN}`,
      'Content-Type': 'application/json',
      'Accept-Datetime-Format': 'UNIX'
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
      throw new Error(`OANDA API Error ${response.status}: ${error.errorMessage || 'Unknown'}`);
    }
    
    return response.json();
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Account
  // ─────────────────────────────────────────────────────────────────────────
  
  async getAccounts(): Promise<{ id: string; tags: string[] }[]> {
    const data = await this.request<any>('/v3/accounts');
    return data.accounts;
  }
  
  async getAccountSummary(): Promise<AccountSummary> {
    const data = await this.request<any>(`/v3/accounts/${ACCOUNT_ID}/summary`);
    const acc = data.account;
    
    return {
      id: acc.id,
      currency: acc.currency,
      balance: parseFloat(acc.balance),
      unrealizedPL: parseFloat(acc.unrealizedPL),
      realizedPL: parseFloat(acc.pl),
      marginUsed: parseFloat(acc.marginUsed),
      marginAvailable: parseFloat(acc.marginAvailable),
      openTradeCount: acc.openTradeCount,
      openPositionCount: acc.openPositionCount
    };
  }
  
  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getAccounts();
      return true;
    } catch {
      return false;
    }
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Instruments
  // ─────────────────────────────────────────────────────────────────────────
  
  async getInstruments(): Promise<Instrument[]> {
    const data = await this.request<any>(`/v3/accounts/${ACCOUNT_ID}/instruments`);
    
    return data.instruments.map((i: any) => ({
      name: i.name,
      type: i.type,
      displayName: i.displayName,
      pipLocation: i.pipLocation,
      minimumTradeSize: parseFloat(i.minimumTradeSize),
      maximumTradeSize: parseFloat(i.maximumTrailingStopDistance || '1000000'),
      marginRate: parseFloat(i.marginRate)
    }));
  }
  
  // Popular forex pairs
  getPopularPairs(): { forex: string[]; indices: string[]; commodities: string[] } {
    return {
      forex: [
        // Major Pairs
        'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD', 'USD_CAD', 'NZD_USD',
        // Cross Pairs
        'EUR_GBP', 'EUR_JPY', 'GBP_JPY', 'EUR_CHF', 'EUR_AUD', 'GBP_CHF', 'AUD_JPY',
        // Exotic Pairs
        'USD_TRY', 'USD_ZAR', 'USD_MXN', 'EUR_TRY', 'USD_SEK', 'USD_NOK', 'USD_SGD'
      ],
      indices: [
        'US30_USD',    // Dow Jones
        'SPX500_USD',  // S&P 500
        'NAS100_USD',  // Nasdaq 100
        'UK100_GBP',   // FTSE 100
        'DE30_EUR',    // DAX
        'JP225_USD',   // Nikkei
        'AU200_AUD',   // ASX 200
        'HK33_HKD',    // Hang Seng
        'FR40_EUR',    // CAC 40
        'EU50_EUR'     // Euro Stoxx 50
      ],
      commodities: [
        'XAU_USD',     // Gold
        'XAG_USD',     // Silver
        'BCO_USD',     // Brent Crude
        'WTICO_USD',   // WTI Crude
        'NATGAS_USD',  // Natural Gas
        'XCU_USD',     // Copper
        'XPT_USD',     // Platinum
        'CORN_USD',    // Corn
        'WHEAT_USD',   // Wheat
        'SOYBN_USD'    // Soybeans
      ]
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Pricing
  // ─────────────────────────────────────────────────────────────────────────
  
  async getPrices(instruments: string[]): Promise<PriceTick[]> {
    const instrumentList = instruments.join(',');
    const data = await this.request<any>(
      `/v3/accounts/${ACCOUNT_ID}/pricing?instruments=${instrumentList}`
    );
    
    return data.prices.map((p: any) => ({
      instrument: p.instrument,
      bid: parseFloat(p.bids?.[0]?.price || '0'),
      ask: parseFloat(p.asks?.[0]?.price || '0'),
      spread: parseFloat(p.asks?.[0]?.price || '0') - parseFloat(p.bids?.[0]?.price || '0'),
      time: p.time
    }));
  }
  
  async getPrice(instrument: string): Promise<PriceTick> {
    const prices = await this.getPrices([instrument]);
    return prices[0];
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Trades
  // ─────────────────────────────────────────────────────────────────────────
  
  async getOpenTrades(): Promise<Trade[]> {
    const data = await this.request<any>(`/v3/accounts/${ACCOUNT_ID}/openTrades`);
    
    return data.trades.map((t: any) => ({
      id: t.id,
      instrument: t.instrument,
      currentUnits: parseFloat(t.currentUnits),
      price: parseFloat(t.price),
      unrealizedPL: parseFloat(t.unrealizedPL),
      realizedPL: parseFloat(t.realizedPL || '0'),
      state: t.state,
      openTime: t.openTime,
      takeProfitPrice: t.takeProfitOrder ? parseFloat(t.takeProfitOrder.price) : undefined,
      stopLossPrice: t.stopLossOrder ? parseFloat(t.stopLossOrder.price) : undefined
    }));
  }
  
  async closeTrade(tradeId: string, units?: number): Promise<OrderResponse> {
    const body = units ? { units: units.toString() } : {};
    return this.request<OrderResponse>(
      `/v3/accounts/${ACCOUNT_ID}/trades/${tradeId}/close`,
      'PUT',
      body
    );
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Orders
  // ─────────────────────────────────────────────────────────────────────────
  
  async createMarketOrder(
    instrument: string,
    units: number, // Positive for buy, negative for sell
    stopLossDistance?: number,
    takeProfitDistance?: number
  ): Promise<OrderResponse> {
    const order: any = {
      type: 'MARKET',
      instrument,
      units: units.toString(),
      timeInForce: 'FOK',
      positionFill: 'DEFAULT'
    };
    
    if (stopLossDistance) {
      order.stopLossOnFill = {
        distance: stopLossDistance.toString()
      };
    }
    
    if (takeProfitDistance) {
      order.takeProfitOnFill = {
        distance: takeProfitDistance.toString()
      };
    }
    
    return this.request<OrderResponse>(
      `/v3/accounts/${ACCOUNT_ID}/orders`,
      'POST',
      { order }
    );
  }
  
  async createLimitOrder(
    instrument: string,
    units: number,
    price: number,
    stopLossDistance?: number,
    takeProfitDistance?: number
  ): Promise<OrderResponse> {
    const order: any = {
      type: 'LIMIT',
      instrument,
      units: units.toString(),
      price: price.toString(),
      timeInForce: 'GTC',
      positionFill: 'DEFAULT'
    };
    
    if (stopLossDistance) {
      order.stopLossOnFill = { distance: stopLossDistance.toString() };
    }
    if (takeProfitDistance) {
      order.takeProfitOnFill = { distance: takeProfitDistance.toString() };
    }
    
    return this.request<OrderResponse>(
      `/v3/accounts/${ACCOUNT_ID}/orders`,
      'POST',
      { order }
    );
  }
  
  async getPendingOrders(): Promise<any[]> {
    const data = await this.request<any>(`/v3/accounts/${ACCOUNT_ID}/pendingOrders`);
    return data.orders;
  }
  
  async cancelOrder(orderId: string): Promise<void> {
    await this.request(`/v3/accounts/${ACCOUNT_ID}/orders/${orderId}/cancel`, 'PUT');
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // History
  // ─────────────────────────────────────────────────────────────────────────
  
  async getTransactionHistory(from?: string, to?: string): Promise<any[]> {
    let endpoint = `/v3/accounts/${ACCOUNT_ID}/transactions`;
    const params: string[] = [];
    if (from) params.push(`from=${from}`);
    if (to) params.push(`to=${to}`);
    if (params.length) endpoint += '?' + params.join('&');
    
    const data = await this.request<any>(endpoint);
    return data.transactions || [];
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Demo
// ═══════════════════════════════════════════════════════════════════════════

async function demo() {
  console.log('\n');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('  ✧  O A N D A   A P I   C L I E N T  ✧');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('');
  
  const client = new OandaClient();
  
  // Check authentication
  console.log(`  🔐 Checking credentials (${IS_PRACTICE ? 'PRACTICE' : 'LIVE'})...`);
  
  if (!API_TOKEN || !ACCOUNT_ID) {
    console.log('  ❌ Missing credentials!');
    console.log('');
    console.log('  📋 Setup Instructions:');
    console.log('');
    console.log('  1. Create account at https://oanda.com');
    console.log('  2. Go to Account → Manage API Access');
    console.log('  3. Generate personal access token');
    console.log('  4. Get your Account ID from account summary');
    console.log('  5. Set environment variables:');
    console.log('');
    console.log('     export OANDA_API_TOKEN="your_token"');
    console.log('     export OANDA_ACCOUNT_ID="your_account_id"');
    console.log('     export OANDA_PRACTICE="true"');
    console.log('');
    console.log('  6. Run: npm run oanda');
    console.log('');
    return;
  }
  
  const authenticated = await client.isAuthenticated();
  if (!authenticated) {
    console.log('  ❌ Authentication failed. Check your credentials.');
    return;
  }
  console.log('  ✅ Authenticated!');
  console.log('');
  
  // Get account info
  console.log('  📊 Account Summary:');
  const account = await client.getAccountSummary();
  console.log(`     Currency: ${account.currency}`);
  console.log(`     Balance: ${account.currency} ${account.balance.toFixed(2)}`);
  console.log(`     Unrealized P&L: ${account.currency} ${account.unrealizedPL.toFixed(2)}`);
  console.log(`     Margin Available: ${account.currency} ${account.marginAvailable.toFixed(2)}`);
  console.log(`     Open Trades: ${account.openTradeCount}`);
  console.log('');
  
  // Show popular pairs
  console.log('  💱 Available Instruments:');
  const pairs = client.getPopularPairs();
  console.log(`     Forex: ${pairs.forex.slice(0, 7).join(', ')}...`);
  console.log(`     Indices: ${pairs.indices.slice(0, 5).join(', ')}...`);
  console.log(`     Commodities: ${pairs.commodities.slice(0, 5).join(', ')}...`);
  console.log('');
  
  // Get sample prices
  console.log('  💹 Sample Prices:');
  try {
    const majorPairs = ['EUR_USD', 'GBP_USD', 'USD_JPY'];
    const prices = await client.getPrices(majorPairs);
    prices.forEach(p => {
      console.log(`     ${p.instrument}: Bid ${p.bid.toFixed(5)} | Ask ${p.ask.toFixed(5)} | Spread ${(p.spread * 10000).toFixed(1)} pips`);
    });
  } catch (e) {
    console.log('     (Unable to fetch prices)');
  }
  console.log('');
  
  // Get open trades
  console.log('  📈 Open Trades:');
  const trades = await client.getOpenTrades();
  if (trades.length === 0) {
    console.log('     No open trades');
  } else {
    trades.slice(0, 5).forEach(t => {
      const emoji = t.unrealizedPL >= 0 ? '🟢' : '🔴';
      const direction = t.currentUnits > 0 ? 'LONG' : 'SHORT';
      console.log(`     ${emoji} ${t.instrument}: ${direction} ${Math.abs(t.currentUnits)} @ ${t.price} | P&L: ${t.unrealizedPL.toFixed(2)}`);
    });
  }
  console.log('');
  
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('  🎵 "Dance through forex with the best spreads!" 🎵');
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('');
}

// Run demo if executed directly
if (process.argv[1]?.includes('oandaApi')) {
  demo().catch(console.error);
}

export default OandaClient;
