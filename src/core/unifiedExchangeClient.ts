/**
 * Unified Exchange Client Interface
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Single interface for all exchange interactions
 */

export type ExchangeType = 'binance' | 'kraken' | 'alpaca' | 'capital';

export interface ExchangeBalance {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usdValue?: number;
}

export interface ExchangeTicker {
  symbol: string;
  price: number;
  bidPrice: number;
  askPrice: number;
  volume24h: number;
  change24h: number;
  timestamp: number;
}

export interface ExchangeOrderResult {
  orderId: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  type: 'MARKET' | 'LIMIT';
  quantity: number;
  price: number;
  status: 'NEW' | 'FILLED' | 'PARTIALLY_FILLED' | 'CANCELED' | 'REJECTED';
  executedQty: number;
  executedPrice: number;
  commission: number;
  commissionAsset: string;
  timestamp: number;
}

export interface ExchangeFees {
  maker: number;
  taker: number;
}

// Exchange fee rates
export const EXCHANGE_FEES: Record<ExchangeType, ExchangeFees> = {
  binance: { maker: 0.0010, taker: 0.0010 }, // 0.10%
  kraken: { maker: 0.0016, taker: 0.0026 }, // 0.16% / 0.26%
  alpaca: { maker: 0.0000, taker: 0.0000 }, // Commission-free
  capital: { maker: 0.0020, taker: 0.0020 }, // 0.20% spread
};

export interface UnifiedExchangeClientConfig {
  exchange: ExchangeType;
  apiKey?: string;
  apiSecret?: string;
  testnet?: boolean;
}

/**
 * Unified Exchange Client
 * Provides a consistent interface for all supported exchanges
 */
export class UnifiedExchangeClient {
  private exchange: ExchangeType;
  private apiKey: string;
  private apiSecret: string;
  private testnet: boolean;
  private lastBalances: ExchangeBalance[] = [];
  private lastUpdate: number = 0;

  constructor(config: UnifiedExchangeClientConfig) {
    this.exchange = config.exchange;
    this.apiKey = config.apiKey || '';
    this.apiSecret = config.apiSecret || '';
    this.testnet = config.testnet || false;
    
    console.log(`📊 Unified Exchange Client initialized for ${this.exchange}`);
  }

  /**
   * Get exchange type
   */
  public getExchange(): ExchangeType {
    return this.exchange;
  }

  /**
   * Get fee rates for this exchange
   */
  public getFees(): ExchangeFees {
    return EXCHANGE_FEES[this.exchange];
  }

  /**
   * Fetch account balances
   */
  public async getBalances(): Promise<ExchangeBalance[]> {
    try {
      switch (this.exchange) {
        case 'binance':
          return await this.fetchBinanceBalances();
        case 'kraken':
          return await this.fetchKrakenBalances();
        case 'alpaca':
          return await this.fetchAlpacaBalances();
        case 'capital':
          return await this.fetchCapitalBalances();
        default:
          throw new Error(`Unsupported exchange: ${this.exchange}`);
      }
    } catch (error) {
      console.error(`${this.exchange} balance fetch error:`, error);
      return this.lastBalances;
    }
  }

  /**
   * Fetch ticker data
   */
  public async getTicker(symbol: string): Promise<ExchangeTicker | null> {
    try {
      switch (this.exchange) {
        case 'binance':
          return await this.fetchBinanceTicker(symbol);
        case 'kraken':
          return await this.fetchKrakenTicker(symbol);
        default:
          return null;
      }
    } catch (error) {
      console.error(`${this.exchange} ticker fetch error:`, error);
      return null;
    }
  }

  /**
   * Get all 24h tickers
   */
  public async get24hTickers(): Promise<ExchangeTicker[]> {
    try {
      switch (this.exchange) {
        case 'binance':
          return await this.fetchBinance24hTickers();
        case 'kraken':
          return await this.fetchKraken24hTickers();
        default:
          return [];
      }
    } catch (error) {
      console.error(`${this.exchange} 24h tickers error:`, error);
      return [];
    }
  }

  /**
   * Convert amount from one asset to another
   */
  public async convertToQuote(
    fromAsset: string,
    toAsset: string,
    amount: number
  ): Promise<number> {
    const symbol = `${fromAsset}${toAsset}`;
    const ticker = await this.getTicker(symbol);
    
    if (ticker) {
      return amount * ticker.price;
    }
    
    // Try reverse pair
    const reverseSymbol = `${toAsset}${fromAsset}`;
    const reverseTicker = await this.getTicker(reverseSymbol);
    
    if (reverseTicker && reverseTicker.price > 0) {
      return amount / reverseTicker.price;
    }
    
    return 0;
  }

  // Exchange-specific implementations
  private async fetchBinanceBalances(): Promise<ExchangeBalance[]> {
    // Use the authenticated get-user-balances endpoint
    const { supabase } = await import('@/integrations/supabase/client');
    const { data: { session } } = await supabase.auth.getSession();
    
    if (!session) {
      console.warn('No session for fetchBinanceBalances');
      return [];
    }
    
    const { data, error } = await supabase.functions.invoke('get-user-balances', {
      headers: { Authorization: `Bearer ${session.access_token}` }
    });
    
    if (error) throw new Error('Failed to fetch Binance balances');
    
    const binanceExchange = data?.balances?.find((b: any) => b.exchange === 'binance');
    if (binanceExchange?.assets) {
      this.lastBalances = binanceExchange.assets.map((b: any) => ({
        asset: b.asset,
        free: b.free,
        locked: b.locked,
        total: b.free + b.locked,
        usdValue: b.usdValue
      }));
      this.lastUpdate = Date.now();
    }
    
    return this.lastBalances;
  }

  private async fetchKrakenBalances(): Promise<ExchangeBalance[]> {
    const response = await fetch(
      `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/get-kraken-balances`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch Kraken balances');
    
    const data = await response.json();
    
    if (data.balances) {
      this.lastBalances = data.balances;
      this.lastUpdate = Date.now();
    }
    
    return this.lastBalances;
  }

  private async fetchAlpacaBalances(): Promise<ExchangeBalance[]> {
    const response = await fetch(
      `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/get-alpaca-balances`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch Alpaca balances');
    
    const data = await response.json();
    
    if (data.balances) {
      this.lastBalances = data.balances;
      this.lastUpdate = Date.now();
    }
    
    return this.lastBalances;
  }

  private async fetchCapitalBalances(): Promise<ExchangeBalance[]> {
    const response = await fetch(
      `${import.meta.env.VITE_SUPABASE_URL}/functions/v1/get-capital-balances`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      }
    );
    
    if (!response.ok) throw new Error('Failed to fetch Capital.com balances');
    
    const data = await response.json();
    
    if (data.balances) {
      this.lastBalances = data.balances;
      this.lastUpdate = Date.now();
    }
    
    return this.lastBalances;
  }

  private async fetchBinanceTicker(symbol: string): Promise<ExchangeTicker | null> {
    try {
      const response = await fetch(
        `https://api.binance.com/api/v3/ticker/24hr?symbol=${symbol}`
      );
      
      if (!response.ok) return null;
      
      const data = await response.json();
      
      return {
        symbol: data.symbol,
        price: parseFloat(data.lastPrice),
        bidPrice: parseFloat(data.bidPrice),
        askPrice: parseFloat(data.askPrice),
        volume24h: parseFloat(data.volume),
        change24h: parseFloat(data.priceChangePercent),
        timestamp: Date.now()
      };
    } catch {
      return null;
    }
  }

  private async fetchKrakenTicker(symbol: string): Promise<ExchangeTicker | null> {
    // Kraken public API
    const krakenSymbol = this.mapToKrakenSymbol(symbol);
    
    try {
      const response = await fetch(
        `https://api.kraken.com/0/public/Ticker?pair=${krakenSymbol}`
      );
      
      if (!response.ok) return null;
      
      const data = await response.json();
      const tickerData = Object.values(data.result)[0] as any;
      
      if (!tickerData) return null;
      
      return {
        symbol,
        price: parseFloat(tickerData.c[0]),
        bidPrice: parseFloat(tickerData.b[0]),
        askPrice: parseFloat(tickerData.a[0]),
        volume24h: parseFloat(tickerData.v[1]),
        change24h: 0, // Kraken doesn't provide this directly
        timestamp: Date.now()
      };
    } catch {
      return null;
    }
  }

  private async fetchBinance24hTickers(): Promise<ExchangeTicker[]> {
    try {
      const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
      if (!response.ok) return [];
      
      const data = await response.json();
      
      return data
        .filter((t: any) => t.symbol.endsWith('USDT'))
        .slice(0, 50)
        .map((t: any) => ({
          symbol: t.symbol,
          price: parseFloat(t.lastPrice),
          bidPrice: parseFloat(t.bidPrice),
          askPrice: parseFloat(t.askPrice),
          volume24h: parseFloat(t.volume),
          change24h: parseFloat(t.priceChangePercent),
          timestamp: Date.now()
        }));
    } catch {
      return [];
    }
  }

  private async fetchKraken24hTickers(): Promise<ExchangeTicker[]> {
    // Kraken public tickers endpoint
    const pairs = ['XBTUSDT', 'ETHUSDT', 'SOLUSDT', 'ADAUSDT', 'XRPUSDT'];
    
    try {
      const response = await fetch(
        `https://api.kraken.com/0/public/Ticker?pair=${pairs.join(',')}`
      );
      
      if (!response.ok) return [];
      
      const data = await response.json();
      const tickers: ExchangeTicker[] = [];
      
      for (const [pair, tickerData] of Object.entries(data.result || {})) {
        const t = tickerData as any;
        tickers.push({
          symbol: pair,
          price: parseFloat(t.c[0]),
          bidPrice: parseFloat(t.b[0]),
          askPrice: parseFloat(t.a[0]),
          volume24h: parseFloat(t.v[1]),
          change24h: 0,
          timestamp: Date.now()
        });
      }
      
      return tickers;
    } catch {
      return [];
    }
  }

  private mapToKrakenSymbol(symbol: string): string {
    const mapping: Record<string, string> = {
      'BTCUSDT': 'XBTUSDT',
      'ETHUSDT': 'ETHUSDT',
      'SOLUSDT': 'SOLUSDT',
      'XRPUSDT': 'XRPUSDT',
    };
    return mapping[symbol] || symbol;
  }

  /**
   * Check if credentials are configured
   */
  public hasCredentials(): boolean {
    return this.apiKey.length > 0 && this.apiSecret.length > 0;
  }

  /**
   * Get last update timestamp
   */
  public getLastUpdate(): number {
    return this.lastUpdate;
  }
}
