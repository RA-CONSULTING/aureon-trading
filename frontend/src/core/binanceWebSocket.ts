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
  private pingInterval: NodeJS.Timeout | null = null;
  private lastPongTime = 0;
  private connectionHealthy = false;
  private connectionStartTime = 0;
  private reconnect24hTimer: NodeJS.Timeout | null = null;
  
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
  private onDisconnectCallback: (() => void) | null = null;

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
      console.log('[Binance WS] Already connected or connecting');
      return;
    }

    this.isConnecting = true;
    this.connectionHealthy = false;
    const streamNames = this.streams.join('/');
    // Use standard port 443 instead of 9443 for better compatibility
    const wsUrl = `wss://stream.binance.com:443/stream?streams=${streamNames}`;

    console.log('[Binance WS] Attempting connection to:', wsUrl);
    console.log('[Binance WS] Attempt #', this.reconnectAttempts + 1);

    try {
      this.ws = new WebSocket(wsUrl);
      
      // Add connection timeout
      const connectionTimeout = setTimeout(() => {
        if (this.ws && this.ws.readyState !== WebSocket.OPEN) {
          console.warn('[Binance WS] Connection timeout, retrying...');
          this.ws.close();
        }
      }, 10000); // 10 second timeout

      this.ws.onopen = () => {
        clearTimeout(connectionTimeout);

        console.log('✅ [Binance WS] Connected successfully');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.connectionHealthy = true;
        this.lastPongTime = Date.now();
        this.connectionStartTime = Date.now();
        this.startHealthCheck();
        this.schedule24HourReconnect();
        
        if (this.onConnectCallback) {
          this.onConnectCallback();
        }
      };

      this.ws.onmessage = (event) => {
        try {
          this.lastPongTime = Date.now(); // Update last activity time
          this.connectionHealthy = true;
          
          // Handle binary ping frames (Binance sends these)
          if (event.data instanceof Blob) {
            console.log('[Binance WS] Received binary ping, sending pong');
            // Binary data is a ping, respond with pong
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
              this.ws.send(event.data); // Echo back as pong
            }
            return;
          }
          
          const message = JSON.parse(event.data);
          this.handleMessage(message);
        } catch (error) {
          console.error('[Binance WS] Parse error:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('❌ [Binance WS] Connection error:', {
          readyState: this.ws?.readyState,
          error: error,
          timestamp: new Date().toISOString()
        });
        this.isConnecting = false;
        this.connectionHealthy = false;
        
        if (this.onErrorCallback) {
          this.onErrorCallback(new Error(`WebSocket connection error - ReadyState: ${this.ws?.readyState}`));
        }
      };

      this.ws.onclose = (event) => {
        console.log('🔌 [Binance WS] Disconnected:', {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean,
          timestamp: new Date().toISOString()
        });
        
        this.stopHealthCheck();
        this.isConnecting = false;
        this.connectionHealthy = false;
        this.ws = null;
        
        if (this.onDisconnectCallback) {
          this.onDisconnectCallback();
        }
        
        this.attemptReconnect();
      };
    } catch (error) {
      console.error('❌ [Binance WS] Failed to create connection:', error);
      this.isConnecting = false;
      this.connectionHealthy = false;
      
      if (this.onErrorCallback) {
        this.onErrorCallback(error as Error);
      }
    }
  }

  private startHealthCheck() {
    this.stopHealthCheck();
    
    // Check connection health every 30 seconds
    this.pingInterval = setInterval(() => {
      const timeSinceLastPong = Date.now() - this.lastPongTime;
      const connectionAge = Date.now() - this.connectionStartTime;
      
      // Binance expects pong within 60 seconds of ping
      if (timeSinceLastPong > 70000) { // 70 seconds to be safe
        console.warn('⚠️ [Binance WS] No activity for 70s, reconnecting...');
        this.connectionHealthy = false;
        this.disconnect();
        this.connect();
      } else {
        console.log('✅ [Binance WS] Connection healthy', {
          lastActivity: `${Math.floor(timeSinceLastPong / 1000)}s ago`,
          connectionAge: `${Math.floor(connectionAge / 1000 / 60)}min`
        });
      }
    }, 30000);
  }

  private schedule24HourReconnect() {
    // Clear any existing timer
    if (this.reconnect24hTimer) {
      clearTimeout(this.reconnect24hTimer);
    }
    
    // Binance connections are only valid for 24 hours
    // Reconnect after 23.5 hours to be safe
    const reconnectTime = 23.5 * 60 * 60 * 1000; // 23.5 hours in ms
    
    console.log('[Binance WS] Scheduled 24-hour reconnect');
    
    this.reconnect24hTimer = setTimeout(() => {
      console.log('🔄 [Binance WS] 24-hour limit reached, reconnecting...');
      this.disconnect();
      this.connect();
    }, reconnectTime);
  }

  private stopHealthCheck() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    
    if (this.reconnect24hTimer) {
      clearTimeout(this.reconnect24hTimer);
      this.reconnect24hTimer = null;
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
      console.error('❌ [Binance WS] Max reconnection attempts reached. Please refresh the page to retry.');
      if (this.onErrorCallback) {
        this.onErrorCallback(new Error('Connection failed after multiple attempts. Please check your internet connection and refresh the page.'));
      }
      return;
    }

    this.reconnectAttempts++;
    // Cap delay at 30 seconds max
    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 30000);
    
    console.log(`🔄 [Binance WS] Reconnecting in ${delay / 1000}s (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

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

  onDisconnect(callback: () => void) {
    this.onDisconnectCallback = callback;
  }

  disconnect() {
    console.log('[Binance WS] Disconnecting...');
    this.stopHealthCheck();
    
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    
    this.connectionHealthy = false;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent reconnection
  }

  isConnected(): boolean {
    return this.ws !== null && this.ws.readyState === WebSocket.OPEN && this.connectionHealthy;
  }

  getConnectionHealth(): { connected: boolean; healthy: boolean; attempts: number } {
    return {
      connected: this.ws !== null && this.ws.readyState === WebSocket.OPEN,
      healthy: this.connectionHealthy,
      attempts: this.reconnectAttempts
    };
  }

  getSymbol(): string {
    return this.symbol.toUpperCase();
  }
}
