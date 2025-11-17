// Binance WebSocket Market Data Integration
// Real-time streams: @aggTrade, @depth, @miniTicker, @kline

export type BinanceAggTrade = {
  e: string;      // Event type
  E: number;      // Event time
  s: string;      // Symbol
  p: string;      // Price
  q: string;      // Quantity
  T: number;      // Trade time
};

export type BinanceMiniTicker = {
  e: string;      // Event type
  E: number;      // Event time
  s: string;      // Symbol
  c: string;      // Close price
  o: string;      // Open price
  h: string;      // High price
  l: string;      // Low price
  v: string;      // Total traded base asset volume
  q: string;      // Total traded quote asset volume
};

export type BinanceDepth = {
  e: string;      // Event type
  E: number;      // Event time
  s: string;      // Symbol
  b: string[][];  // Bids [price, quantity]
  a: string[][];  // Asks [price, quantity]
};

export type MarketData = {
  price: number;
  volume: number;
  volatility: number;
  momentum: number;
  spread: number;
  timestamp: number;
};

export class BinanceWebSocketClient {
  private ws: WebSocket | null = null;
  private symbol: string;
  private streams: string[];
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private reconnectDelay = 1000;
  private isConnecting = false;
  
  private priceHistory: number[] = [];
  private volumeHistory: number[] = [];
  private maxHistory = 100;
  
  private lastPrice = 0;
  private currentVolume = 0;
  private bidPrice = 0;
  private askPrice = 0;
  
  private onDataCallback: ((data: MarketData) => void) | null = null;
  private onErrorCallback: ((error: Error) => void) | null = null;
  private onConnectCallback: (() => void) | null = null;

  constructor(symbol: string = 'btcusdt') {
    this.symbol = symbol.toLowerCase();
    this.streams = [
      `${this.symbol}@aggTrade`,
      `${this.symbol}@depth@100ms`,
      `${this.symbol}@miniTicker`,
    ];
  }

  connect() {
    if (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN)) {
      console.log('WebSocket already connected or connecting');
      return;
    }

    this.isConnecting = true;
    const streamNames = this.streams.join('/');
    const wsUrl = `wss://stream.binance.com:9443/stream?streams=${streamNames}`;

    console.log('Connecting to Binance WebSocket:', wsUrl);

    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ Binance WebSocket connected');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        if (this.onConnectCallback) {
          this.onConnectCallback();
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.isConnecting = false;
        if (this.onErrorCallback) {
          this.onErrorCallback(new Error('WebSocket connection error'));
        }
      };

      this.ws.onclose = () => {
        console.log('WebSocket disconnected');
        this.isConnecting = false;
        this.ws = null;
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('Error creating WebSocket:', error);
      this.isConnecting = false;
      if (this.onErrorCallback) {
        this.onErrorCallback(error as Error);
      }
    }
  }

  private handleMessage(message: any) {
    if (!message.data) return;

    const data = message.data;
    const eventType = data.e;

    switch (eventType) {
      case 'aggTrade':
        this.handleAggTrade(data as BinanceAggTrade);
        break;
      case '24hrMiniTicker':
        this.handleMiniTicker(data as BinanceMiniTicker);
        break;
      case 'depthUpdate':
        this.handleDepth(data as BinanceDepth);
        break;
    }

    // Emit market snapshot after processing any update
    this.emitMarketData();
  }

  private handleAggTrade(trade: BinanceAggTrade) {
    this.lastPrice = parseFloat(trade.p);
    this.currentVolume = parseFloat(trade.q);
    
    this.priceHistory.push(this.lastPrice);
    if (this.priceHistory.length > this.maxHistory) {
      this.priceHistory.shift();
    }
  }

  private handleMiniTicker(ticker: BinanceMiniTicker) {
    const volume = parseFloat(ticker.v);
    this.volumeHistory.push(volume);
    
    if (this.volumeHistory.length > this.maxHistory) {
      this.volumeHistory.shift();
    }
  }

  private handleDepth(depth: BinanceDepth) {
    if (depth.b && depth.b.length > 0) {
      this.bidPrice = parseFloat(depth.b[0][0]);
    }
    if (depth.a && depth.a.length > 0) {
      this.askPrice = parseFloat(depth.a[0][0]);
    }
  }

  private emitMarketData() {
    if (!this.onDataCallback) return;

    const marketData: MarketData = {
      price: this.lastPrice,
      volume: this.computeNormalizedVolume(),
      volatility: this.computeVolatility(),
      momentum: this.computeMomentum(),
      spread: this.computeSpread(),
      timestamp: Date.now(),
    };

    this.onDataCallback(marketData);
  }

  private computeVolatility(): number {
    if (this.priceHistory.length < 10) return 0;

    const recent = this.priceHistory.slice(-20);
    const mean = recent.reduce((sum, p) => sum + p, 0) / recent.length;
    const variance = recent.reduce((sum, p) => sum + Math.pow(p - mean, 2), 0) / recent.length;
    const stddev = Math.sqrt(variance);

    // Normalize to 0-1 range (assuming typical stddev is 0-500 for BTC)
    return Math.min(stddev / 500, 1);
  }

  private computeMomentum(): number {
    if (this.priceHistory.length < 10) return 0;

    const recent = this.priceHistory.slice(-10);
    const older = this.priceHistory.slice(-20, -10);
    
    if (older.length === 0) return 0;

    const recentAvg = recent.reduce((sum, p) => sum + p, 0) / recent.length;
    const olderAvg = older.reduce((sum, p) => sum + p, 0) / older.length;

    // Normalized momentum: -1 to 1
    const momentum = (recentAvg - olderAvg) / olderAvg;
    return Math.max(-1, Math.min(1, momentum * 100)); // Scale by 100
  }

  private computeNormalizedVolume(): number {
    if (this.volumeHistory.length === 0) return 0;

    const maxVolume = Math.max(...this.volumeHistory);
    const currentVol = this.volumeHistory[this.volumeHistory.length - 1] || 0;

    return maxVolume > 0 ? currentVol / maxVolume : 0;
  }

  private computeSpread(): number {
    if (this.bidPrice === 0 || this.askPrice === 0) return 0;

    const spread = this.askPrice - this.bidPrice;
    const midPrice = (this.askPrice + this.bidPrice) / 2;

    // Normalize spread as percentage
    return midPrice > 0 ? spread / midPrice : 0;
  }

  private attemptReconnect() {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      if (this.onErrorCallback) {
        this.onErrorCallback(new Error('Max reconnection attempts reached'));
      }
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    
    console.log(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

    setTimeout(() => {
      this.connect();
    }, delay);
  }

  onData(callback: (data: MarketData) => void) {
    this.onDataCallback = callback;
  }

  onError(callback: (error: Error) => void) {
    this.onErrorCallback = callback;
  }

  onConnect(callback: () => void) {
    this.onConnectCallback = callback;
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN;
  }

  getSymbol(): string {
    return this.symbol.toUpperCase();
  }
}
