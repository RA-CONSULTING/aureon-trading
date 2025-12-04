/**
 * Kraken WebSocket Client
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Real-time price streams from Kraken exchange
 */

export interface KrakenTicker {
  symbol: string;
  price: number;
  volume24h: number;
  high24h: number;
  low24h: number;
  change24h: number;
  timestamp: number;
}

export interface KrakenOrderBook {
  symbol: string;
  bids: Array<[number, number]>; // [price, quantity]
  asks: Array<[number, number]>;
  timestamp: number;
}

type TickerCallback = (ticker: KrakenTicker) => void;
type OrderBookCallback = (orderBook: KrakenOrderBook) => void;

const KRAKEN_WS_URL = 'wss://ws.kraken.com';

// Kraken symbol mapping (Kraken uses different naming)
const SYMBOL_MAP: Record<string, string> = {
  'BTCUSDT': 'XBT/USDT',
  'ETHUSDT': 'ETH/USDT',
  'XRPUSDT': 'XRP/USDT',
  'SOLUSDT': 'SOL/USDT',
  'ADAUSDT': 'ADA/USDT',
  'DOGEUSDT': 'DOGE/USDT',
  'LINKUSDT': 'LINK/USDT',
  'AVAXUSDT': 'AVAX/USDT',
};

export class KrakenWebSocket {
  private ws: WebSocket | null = null;
  private tickerCallbacks: Map<string, TickerCallback[]> = new Map();
  private orderBookCallbacks: Map<string, OrderBookCallback[]> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private isConnected = false;
  private subscriptions: Set<string> = new Set();
  private heartbeatInterval: number | null = null;

  constructor() {
    console.log('🦑 Kraken WebSocket client initialized');
  }

  /**
   * Connect to Kraken WebSocket
   */
  public connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(KRAKEN_WS_URL);

        this.ws.onopen = () => {
          console.log('🦑 Kraken WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          
          // Resubscribe to existing subscriptions
          this.subscriptions.forEach(symbol => {
            this.subscribeToSymbol(symbol);
          });
          
          resolve();
        };

        this.ws.onmessage = (event) => {
          this.handleMessage(event.data);
        };

        this.ws.onerror = (error) => {
          console.error('🦑 Kraken WebSocket error:', error);
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('🦑 Kraken WebSocket disconnected');
          this.isConnected = false;
          this.stopHeartbeat();
          this.attemptReconnect();
        };

      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Subscribe to ticker updates
   */
  public subscribeTicker(symbol: string, callback: TickerCallback): void {
    const krakenSymbol = SYMBOL_MAP[symbol] || symbol;
    
    if (!this.tickerCallbacks.has(krakenSymbol)) {
      this.tickerCallbacks.set(krakenSymbol, []);
    }
    this.tickerCallbacks.get(krakenSymbol)!.push(callback);
    
    this.subscriptions.add(krakenSymbol);
    
    if (this.isConnected) {
      this.subscribeToSymbol(krakenSymbol);
    }
  }

  /**
   * Subscribe to order book updates
   */
  public subscribeOrderBook(symbol: string, callback: OrderBookCallback): void {
    const krakenSymbol = SYMBOL_MAP[symbol] || symbol;
    
    if (!this.orderBookCallbacks.has(krakenSymbol)) {
      this.orderBookCallbacks.set(krakenSymbol, []);
    }
    this.orderBookCallbacks.get(krakenSymbol)!.push(callback);
    
    if (this.isConnected) {
      this.subscribeToOrderBookChannel(krakenSymbol);
    }
  }

  private subscribeToSymbol(krakenSymbol: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const subscribeMsg = {
      event: 'subscribe',
      pair: [krakenSymbol],
      subscription: {
        name: 'ticker'
      }
    };

    this.ws.send(JSON.stringify(subscribeMsg));
    console.log(`🦑 Subscribed to ${krakenSymbol} ticker`);
  }

  private subscribeToOrderBookChannel(krakenSymbol: string): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;

    const subscribeMsg = {
      event: 'subscribe',
      pair: [krakenSymbol],
      subscription: {
        name: 'book',
        depth: 10
      }
    };

    this.ws.send(JSON.stringify(subscribeMsg));
    console.log(`🦑 Subscribed to ${krakenSymbol} order book`);
  }

  private handleMessage(data: string): void {
    try {
      const message = JSON.parse(data);

      // Handle heartbeat
      if (message.event === 'heartbeat') {
        return;
      }

      // Handle subscription status
      if (message.event === 'subscriptionStatus') {
        console.log('🦑 Subscription status:', message.status, message.pair);
        return;
      }

      // Handle ticker data (array format)
      if (Array.isArray(message) && message.length >= 4) {
        const [channelId, tickerData, channelName, pair] = message;
        
        if (channelName === 'ticker' && typeof tickerData === 'object') {
          const ticker = this.parseTickerData(tickerData, pair);
          this.emitTicker(pair, ticker);
        }
        
        if (channelName === 'book-10' && typeof tickerData === 'object') {
          const orderBook = this.parseOrderBookData(tickerData, pair);
          this.emitOrderBook(pair, orderBook);
        }
      }

    } catch (error) {
      console.error('🦑 Error parsing Kraken message:', error);
    }
  }

  private parseTickerData(data: any, pair: string): KrakenTicker {
    // Kraken ticker format: {a: [ask], b: [bid], c: [close], v: [volume], p: [vwap], t: [trades], l: [low], h: [high], o: [open]}
    const price = parseFloat(data.c?.[0] || '0');
    const volume = parseFloat(data.v?.[1] || '0'); // 24h volume
    const high = parseFloat(data.h?.[1] || '0'); // 24h high
    const low = parseFloat(data.l?.[1] || '0'); // 24h low
    const open = parseFloat(data.o?.[1] || '0'); // 24h open
    const change = open > 0 ? ((price - open) / open) * 100 : 0;

    return {
      symbol: pair,
      price,
      volume24h: volume,
      high24h: high,
      low24h: low,
      change24h: change,
      timestamp: Date.now()
    };
  }

  private parseOrderBookData(data: any, pair: string): KrakenOrderBook {
    const bids: Array<[number, number]> = (data.b || []).map((b: string[]) => [
      parseFloat(b[0]),
      parseFloat(b[1])
    ]);
    
    const asks: Array<[number, number]> = (data.a || []).map((a: string[]) => [
      parseFloat(a[0]),
      parseFloat(a[1])
    ]);

    return {
      symbol: pair,
      bids,
      asks,
      timestamp: Date.now()
    };
  }

  private emitTicker(pair: string, ticker: KrakenTicker): void {
    const callbacks = this.tickerCallbacks.get(pair);
    if (callbacks) {
      callbacks.forEach(cb => cb(ticker));
    }
  }

  private emitOrderBook(pair: string, orderBook: KrakenOrderBook): void {
    const callbacks = this.orderBookCallbacks.get(pair);
    if (callbacks) {
      callbacks.forEach(cb => cb(orderBook));
    }
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = window.setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ event: 'ping' }));
      }
    }, 30000);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🦑 Max reconnection attempts reached');
      return;
    }

    this.reconnectAttempts++;
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    
    console.log(`🦑 Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    
    setTimeout(() => {
      this.connect().catch(err => {
        console.error('🦑 Reconnection failed:', err);
      });
    }, delay);
  }

  /**
   * Disconnect from WebSocket
   */
  public disconnect(): void {
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * Check if connected
   */
  public getIsConnected(): boolean {
    return this.isConnected;
  }
}

// Singleton instance
export const krakenWebSocket = new KrakenWebSocket();
