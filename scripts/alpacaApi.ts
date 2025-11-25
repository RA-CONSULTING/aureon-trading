/**
 * 🎵 ALPACA API CLIENT 🎵
 * 
 * The Song of Space and Time - US Stocks & Crypto Edition
 * 
 * Supports:
 * - US Stocks & ETFs (commission-free!)
 * - Cryptocurrency
 * - Fractional shares
 * - Paper trading (unlimited)
 * 
 * Setup:
 * 1. Create account at https://alpaca.markets
 * 2. Get API keys from dashboard
 * 3. Set environment variables:
 *    export ALPACA_API_KEY="your_api_key"
 *    export ALPACA_SECRET="your_secret_key"
 *    export ALPACA_PAPER="true"  # or "false" for live
 */

// ═══════════════════════════════════════════════════════════════════════════
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const PAPER_URL = 'https://paper-api.alpaca.markets';
const LIVE_URL = 'https://api.alpaca.markets';
const DATA_URL = 'https://data.alpaca.markets';

const IS_PAPER = process.env.ALPACA_PAPER !== 'false';
const BASE_URL = IS_PAPER ? PAPER_URL : LIVE_URL;

const API_KEY = process.env.ALPACA_API_KEY || '';
const SECRET_KEY = process.env.ALPACA_SECRET || '';

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

export interface AccountInfo {
  id: string;
  accountNumber: string;
  status: string;
  currency: string;
  cash: number;
  portfolioValue: number;
  equity: number;
  buyingPower: number;
  daytradeCount: number;
  patternDayTrader: boolean;
}

export interface Asset {
  id: string;
  symbol: string;
  name: string;
  exchange: string;
  assetClass: 'us_equity' | 'crypto';
  tradable: boolean;
  fractionable: boolean;
  marginable: boolean;
  shortable: boolean;
}

export interface Position {
  symbol: string;
  qty: number;
  side: 'long' | 'short';
  marketValue: number;
  costBasis: number;
  unrealizedPL: number;
  unrealizedPLPercent: number;
  currentPrice: number;
  avgEntryPrice: number;
}

export interface Quote {
  symbol: string;
  bidPrice: number;
  bidSize: number;
  askPrice: number;
  askSize: number;
  lastPrice: number;
  timestamp: string;
}

export interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  type: 'market' | 'limit' | 'stop' | 'stop_limit';
  qty: number;
  filledQty: number;
  status: string;
  submittedAt: string;
  filledAt?: string;
  filledAvgPrice?: number;
}

// ═══════════════════════════════════════════════════════════════════════════
// Alpaca API Client
// ═══════════════════════════════════════════════════════════════════════════

export class AlpacaClient {
  
  constructor() {}
  
  private getHeaders(): Record<string, string> {
    return {
      'APCA-API-KEY-ID': API_KEY,
      'APCA-API-SECRET-KEY': SECRET_KEY,
      'Content-Type': 'application/json'
    };
  }
  
  private async request<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any,
    useDataUrl = false
  ): Promise<T> {
    const baseUrl = useDataUrl ? DATA_URL : BASE_URL;
    const response = await fetch(`${baseUrl}${endpoint}`, {
      method,
      headers: this.getHeaders(),
      body: body ? JSON.stringify(body) : undefined
    });
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(`API Error ${response.status}: ${error.message || 'Unknown'}`);
    }
    
    return response.json();
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Account
  // ─────────────────────────────────────────────────────────────────────────
  
  async getAccount(): Promise<AccountInfo> {
    const data = await this.request<any>('/v2/account');
    
    return {
      id: data.id,
      accountNumber: data.account_number,
      status: data.status,
      currency: data.currency,
      cash: parseFloat(data.cash),
      portfolioValue: parseFloat(data.portfolio_value),
      equity: parseFloat(data.equity),
      buyingPower: parseFloat(data.buying_power),
      daytradeCount: data.daytrade_count,
      patternDayTrader: data.pattern_day_trader
    };
  }
  
  async isAuthenticated(): Promise<boolean> {
    try {
      await this.getAccount();
      return true;
    } catch {
      return false;
    }
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Assets
  // ─────────────────────────────────────────────────────────────────────────
  
  async getAssets(assetClass?: 'us_equity' | 'crypto'): Promise<Asset[]> {
    let endpoint = '/v2/assets?status=active';
    if (assetClass) endpoint += `&asset_class=${assetClass}`;
    
    const data = await this.request<any[]>(endpoint);
    
    return data.map(a => ({
      id: a.id,
      symbol: a.symbol,
      name: a.name,
      exchange: a.exchange,
      assetClass: a.class,
      tradable: a.tradable,
      fractionable: a.fractionable,
      marginable: a.marginable,
      shortable: a.shortable
    }));
  }
  
  async getAsset(symbol: string): Promise<Asset> {
    const data = await this.request<any>(`/v2/assets/${symbol}`);
    
    return {
      id: data.id,
      symbol: data.symbol,
      name: data.name,
      exchange: data.exchange,
      assetClass: data.class,
      tradable: data.tradable,
      fractionable: data.fractionable,
      marginable: data.marginable,
      shortable: data.shortable
    };
  }
  
  // Get popular tradable symbols
  getPopularSymbols(): { stocks: string[]; crypto: string[] } {
    return {
      stocks: [
        // Tech Giants
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'NVDA', 'TSLA', 'AMD', 'INTC', 'CRM',
        // Finance
        'JPM', 'BAC', 'WFC', 'GS', 'MS', 'V', 'MA', 'AXP', 'BLK', 'C',
        // Healthcare
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK', 'LLY', 'TMO', 'ABT', 'BMY', 'AMGN',
        // Consumer
        'WMT', 'HD', 'MCD', 'NKE', 'SBUX', 'TGT', 'COST', 'LOW', 'DIS', 'NFLX',
        // Energy
        'XOM', 'CVX', 'COP', 'SLB', 'EOG', 'OXY', 'PSX', 'VLO', 'MPC', 'HAL',
        // ETFs
        'SPY', 'QQQ', 'IWM', 'DIA', 'VTI', 'VOO', 'VTV', 'VUG', 'ARKK', 'XLF'
      ],
      crypto: [
        'BTC/USD', 'ETH/USD', 'SOL/USD', 'DOGE/USD', 'SHIB/USD',
        'AVAX/USD', 'DOT/USD', 'LINK/USD', 'UNI/USD', 'AAVE/USD',
        'LTC/USD', 'BCH/USD', 'XLM/USD', 'ALGO/USD', 'ATOM/USD'
      ]
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Market Data
  // ─────────────────────────────────────────────────────────────────────────
  
  async getQuote(symbol: string): Promise<Quote> {
    const isCrypto = symbol.includes('/');
    const endpoint = isCrypto
      ? `/v1beta3/crypto/us/latest/quotes?symbols=${encodeURIComponent(symbol)}`
      : `/v2/stocks/${symbol}/quotes/latest`;
    
    const data = await this.request<any>(endpoint, 'GET', undefined, true);
    
    if (isCrypto) {
      const quote = data.quotes[symbol];
      return {
        symbol,
        bidPrice: quote?.bp || 0,
        bidSize: quote?.bs || 0,
        askPrice: quote?.ap || 0,
        askSize: quote?.as || 0,
        lastPrice: (quote?.bp + quote?.ap) / 2 || 0,
        timestamp: quote?.t || new Date().toISOString()
      };
    } else {
      return {
        symbol,
        bidPrice: data.quote?.bp || 0,
        bidSize: data.quote?.bs || 0,
        askPrice: data.quote?.ap || 0,
        askSize: data.quote?.as || 0,
        lastPrice: (data.quote?.bp + data.quote?.ap) / 2 || 0,
        timestamp: data.quote?.t || new Date().toISOString()
      };
    }
  }
  
  async getQuotes(symbols: string[]): Promise<Map<string, Quote>> {
    const stocks = symbols.filter(s => !s.includes('/'));
    const crypto = symbols.filter(s => s.includes('/'));
    const quotes = new Map<string, Quote>();
    
    // Get stock quotes
    if (stocks.length > 0) {
      const stockSymbols = stocks.join(',');
      const data = await this.request<any>(
        `/v2/stocks/quotes/latest?symbols=${stockSymbols}`,
        'GET',
        undefined,
        true
      );
      
      for (const [symbol, quote] of Object.entries(data.quotes || {})) {
        const q = quote as any;
        quotes.set(symbol, {
          symbol,
          bidPrice: q.bp || 0,
          bidSize: q.bs || 0,
          askPrice: q.ap || 0,
          askSize: q.as || 0,
          lastPrice: ((q.bp || 0) + (q.ap || 0)) / 2,
          timestamp: q.t || new Date().toISOString()
        });
      }
    }
    
    // Get crypto quotes
    if (crypto.length > 0) {
      const cryptoSymbols = crypto.map(s => encodeURIComponent(s)).join(',');
      const data = await this.request<any>(
        `/v1beta3/crypto/us/latest/quotes?symbols=${cryptoSymbols}`,
        'GET',
        undefined,
        true
      );
      
      for (const [symbol, quote] of Object.entries(data.quotes || {})) {
        const q = quote as any;
        quotes.set(symbol, {
          symbol,
          bidPrice: q.bp || 0,
          bidSize: q.bs || 0,
          askPrice: q.ap || 0,
          askSize: q.as || 0,
          lastPrice: ((q.bp || 0) + (q.ap || 0)) / 2,
          timestamp: q.t || new Date().toISOString()
        });
      }
    }
    
    return quotes;
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Positions
  // ─────────────────────────────────────────────────────────────────────────
  
  async getPositions(): Promise<Position[]> {
    const data = await this.request<any[]>('/v2/positions');
    
    return data.map(p => ({
      symbol: p.symbol,
      qty: parseFloat(p.qty),
      side: p.side,
      marketValue: parseFloat(p.market_value),
      costBasis: parseFloat(p.cost_basis),
      unrealizedPL: parseFloat(p.unrealized_pl),
      unrealizedPLPercent: parseFloat(p.unrealized_plpc) * 100,
      currentPrice: parseFloat(p.current_price),
      avgEntryPrice: parseFloat(p.avg_entry_price)
    }));
  }
  
  async getPosition(symbol: string): Promise<Position | null> {
    try {
      const data = await this.request<any>(`/v2/positions/${symbol}`);
      
      return {
        symbol: data.symbol,
        qty: parseFloat(data.qty),
        side: data.side,
        marketValue: parseFloat(data.market_value),
        costBasis: parseFloat(data.cost_basis),
        unrealizedPL: parseFloat(data.unrealized_pl),
        unrealizedPLPercent: parseFloat(data.unrealized_plpc) * 100,
        currentPrice: parseFloat(data.current_price),
        avgEntryPrice: parseFloat(data.avg_entry_price)
      };
    } catch {
      return null;
    }
  }
  
  async closePosition(symbol: string): Promise<Order> {
    const data = await this.request<any>(`/v2/positions/${symbol}`, 'DELETE');
    return this.mapOrder(data);
  }
  
  async closeAllPositions(): Promise<void> {
    await this.request('/v2/positions', 'DELETE');
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Orders
  // ─────────────────────────────────────────────────────────────────────────
  
  async getOrders(status: 'open' | 'closed' | 'all' = 'open'): Promise<Order[]> {
    const data = await this.request<any[]>(`/v2/orders?status=${status}`);
    return data.map(o => this.mapOrder(o));
  }
  
  async submitOrder(
    symbol: string,
    qty: number,
    side: 'buy' | 'sell',
    type: 'market' | 'limit' = 'market',
    limitPrice?: number,
    stopPrice?: number
  ): Promise<Order> {
    const body: any = {
      symbol,
      qty: qty.toString(),
      side,
      type,
      time_in_force: 'day'
    };
    
    if (type === 'limit' && limitPrice) {
      body.limit_price = limitPrice.toString();
    }
    
    if (stopPrice) {
      body.stop_price = stopPrice.toString();
      body.type = type === 'limit' ? 'stop_limit' : 'stop';
    }
    
    const data = await this.request<any>('/v2/orders', 'POST', body);
    return this.mapOrder(data);
  }
  
  async cancelOrder(orderId: string): Promise<void> {
    await this.request(`/v2/orders/${orderId}`, 'DELETE');
  }
  
  async cancelAllOrders(): Promise<void> {
    await this.request('/v2/orders', 'DELETE');
  }
  
  private mapOrder(data: any): Order {
    return {
      id: data.id,
      symbol: data.symbol,
      side: data.side,
      type: data.type,
      qty: parseFloat(data.qty),
      filledQty: parseFloat(data.filled_qty || '0'),
      status: data.status,
      submittedAt: data.submitted_at,
      filledAt: data.filled_at,
      filledAvgPrice: data.filled_avg_price ? parseFloat(data.filled_avg_price) : undefined
    };
  }
  
  // ─────────────────────────────────────────────────────────────────────────
  // Market Status
  // ─────────────────────────────────────────────────────────────────────────
  
  async getClock(): Promise<{ isOpen: boolean; nextOpen: string; nextClose: string }> {
    const data = await this.request<any>('/v2/clock');
    
    return {
      isOpen: data.is_open,
      nextOpen: data.next_open,
      nextClose: data.next_close
    };
  }
  
  async getCalendar(start?: string, end?: string): Promise<any[]> {
    let endpoint = '/v2/calendar';
    const params: string[] = [];
    if (start) params.push(`start=${start}`);
    if (end) params.push(`end=${end}`);
    if (params.length) endpoint += '?' + params.join('&');
    
    return this.request<any[]>(endpoint);
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Demo
// ═══════════════════════════════════════════════════════════════════════════

async function demo() {
  console.log('\n');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('  ✧  A L P A C A   A P I   C L I E N T  ✧');
  console.log('  ═══════════════════════════════════════════════════════════');
  console.log('');
  
  const client = new AlpacaClient();
  
  // Check authentication
  console.log(`  🔐 Checking credentials (${IS_PAPER ? 'PAPER' : 'LIVE'})...`);
  
  if (!API_KEY || !SECRET_KEY) {
    console.log('  ❌ Missing credentials!');
    console.log('');
    console.log('  📋 Setup Instructions:');
    console.log('');
    console.log('  1. Create account at https://alpaca.markets');
    console.log('  2. Go to API Keys in dashboard');
    console.log('  3. Generate new API key');
    console.log('  4. Set environment variables:');
    console.log('');
    console.log('     export ALPACA_API_KEY="your_api_key"');
    console.log('     export ALPACA_SECRET="your_secret_key"');
    console.log('     export ALPACA_PAPER="true"');
    console.log('');
    console.log('  5. Run: npm run alpaca');
    console.log('');
    return;
  }
  
  const authenticated = await client.isAuthenticated();
  if (!authenticated) {
    console.log('  ❌ Authentication failed. Check your API keys.');
    return;
  }
  console.log('  ✅ Authenticated!');
  console.log('');
  
  // Get account info
  console.log('  📊 Account Info:');
  const account = await client.getAccount();
  console.log(`     Status: ${account.status}`);
  console.log(`     Cash: $${account.cash.toFixed(2)}`);
  console.log(`     Portfolio: $${account.portfolioValue.toFixed(2)}`);
  console.log(`     Buying Power: $${account.buyingPower.toFixed(2)}`);
  console.log('');
  
  // Market status
  console.log('  🕐 Market Status:');
  const clock = await client.getClock();
  console.log(`     Market: ${clock.isOpen ? '🟢 OPEN' : '🔴 CLOSED'}`);
  console.log(`     Next Open: ${new Date(clock.nextOpen).toLocaleString()}`);
  console.log(`     Next Close: ${new Date(clock.nextClose).toLocaleString()}`);
  console.log('');
  
  // Show available symbols
  console.log('  🌍 Available Symbols:');
  const symbols = client.getPopularSymbols();
  console.log(`     Stocks: ${symbols.stocks.slice(0, 10).join(', ')}...`);
  console.log(`     Crypto: ${symbols.crypto.slice(0, 5).join(', ')}...`);
  console.log('');
  
  // Get a sample quote
  console.log('  💹 Sample Quotes:');
  try {
    const appleQuote = await client.getQuote('AAPL');
    console.log(`     AAPL: Bid $${appleQuote.bidPrice.toFixed(2)} | Ask $${appleQuote.askPrice.toFixed(2)}`);
  } catch (e) {
    console.log('     (Market data requires subscription for some endpoints)');
  }
  console.log('');
  
  // Get positions
  console.log('  📈 Open Positions:');
  const positions = await client.getPositions();
  if (positions.length === 0) {
    console.log('     No open positions');
  } else {
    positions.slice(0, 5).forEach(p => {
      const emoji = p.unrealizedPL >= 0 ? '🟢' : '🔴';
      console.log(`     ${emoji} ${p.symbol}: ${p.qty} shares @ $${p.avgEntryPrice.toFixed(2)} | P&L: $${p.unrealizedPL.toFixed(2)}`);
    });
  }
  console.log('');
  
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('  🎵 "Dance through stocks and crypto, commission-free!" 🎵');
  console.log('  ─────────────────────────────────────────────────────────');
  console.log('');
}

// Run demo if executed directly
if (process.argv[1]?.includes('alpacaApi')) {
  demo().catch(console.error);
}

export default AlpacaClient;
