"use strict";
/**
 * AUREON QUANTUM TRADING SYSTEM (AQTS)
 * Binance WebSocket Market Data Streams
 *
 * "Taste the Rainbow" - Real-time sensory perception of market dynamics
 *
 * Streams:
 * - Trade streams (@trade) - Raw trade information, real-time
 * - Aggregate trades (@aggTrade) - Aggregated taker orders
 * - Depth streams (@depth) - Order book updates (100ms)
 * - Best bid/ask (@bookTicker) - Top of book in real-time
 * - Mini ticker (@miniTicker) - 24hr rolling window stats
 * - Kline streams (@kline_1m) - Candlestick updates
 *
 * Architecture:
 * - Single WebSocket connection with combined streams
 * - Auto-reconnect with exponential backoff
 * - Heartbeat ping/pong (20s intervals)
 * - Stream subscription management
 * - Rate limit: 5 messages/second, max 1024 streams
 */
var __extends = (this && this.__extends) || (function () {
    var extendStatics = function (d, b) {
        extendStatics = Object.setPrototypeOf ||
            ({ __proto__: [] } instanceof Array && function (d, b) { d.__proto__ = b; }) ||
            function (d, b) { for (var p in b) if (Object.prototype.hasOwnProperty.call(b, p)) d[p] = b[p]; };
        return extendStatics(d, b);
    };
    return function (d, b) {
        if (typeof b !== "function" && b !== null)
            throw new TypeError("Class extends value " + String(b) + " is not a constructor or null");
        extendStatics(d, b);
        function __() { this.constructor = d; }
        d.prototype = b === null ? Object.create(b) : (__.prototype = b.prototype, new __());
    };
})();
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
var __generator = (this && this.__generator) || function (thisArg, body) {
    var _ = { label: 0, sent: function() { if (t[0] & 1) throw t[1]; return t[1]; }, trys: [], ops: [] }, f, y, t, g = Object.create((typeof Iterator === "function" ? Iterator : Object).prototype);
    return g.next = verb(0), g["throw"] = verb(1), g["return"] = verb(2), typeof Symbol === "function" && (g[Symbol.iterator] = function() { return this; }), g;
    function verb(n) { return function (v) { return step([n, v]); }; }
    function step(op) {
        if (f) throw new TypeError("Generator is already executing.");
        while (g && (g = 0, op[0] && (_ = 0)), _) try {
            if (f = 1, y && (t = op[0] & 2 ? y["return"] : op[0] ? y["throw"] || ((t = y["return"]) && t.call(y), 0) : y.next) && !(t = t.call(y, op[1])).done) return t;
            if (y = 0, t) op = [op[0] & 2, t.value];
            switch (op[0]) {
                case 0: case 1: t = op; break;
                case 4: _.label++; return { value: op[1], done: false };
                case 5: _.label++; y = op[1]; op = [0]; continue;
                case 7: op = _.ops.pop(); _.trys.pop(); continue;
                default:
                    if (!(t = _.trys, t = t.length > 0 && t[t.length - 1]) && (op[0] === 6 || op[0] === 2)) { _ = 0; continue; }
                    if (op[0] === 3 && (!t || (op[1] > t[0] && op[1] < t[3]))) { _.label = op[1]; break; }
                    if (op[0] === 6 && _.label < t[1]) { _.label = t[1]; t = op; break; }
                    if (t && _.label < t[2]) { _.label = t[2]; _.ops.push(op); break; }
                    if (t[2]) _.ops.pop();
                    _.trys.pop(); continue;
            }
            op = body.call(thisArg, _);
        } catch (e) { op = [6, e]; y = 0; } finally { f = t = 0; }
        if (op[0] & 5) throw op[1]; return { value: op[0] ? op[1] : void 0, done: true };
    }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.StreamBuilder = exports.BinanceWebSocket = void 0;
var ws_1 = require("ws");
var events_1 = require("events");
// ============================================================================
// BINANCE WEBSOCKET CLIENT
// ============================================================================
var BinanceWebSocket = /** @class */ (function (_super) {
    __extends(BinanceWebSocket, _super);
    function BinanceWebSocket() {
        var _this = _super.call(this) || this;
        _this.ws = null;
        _this.baseUrl = 'wss://stream.binance.com:9443';
        _this.streams = new Set();
        _this.subscriptionId = 0;
        _this.reconnectAttempts = 0;
        _this.maxReconnectAttempts = 10;
        _this.reconnectDelay = 1000; // Start at 1 second
        _this.pingInterval = null;
        _this.isConnecting = false;
        _this.isClosing = false;
        // Market data aggregation
        _this.marketSnapshots = new Map();
        _this.tradeBuffer = new Map();
        _this.lastUpdateTime = new Map();
        return _this;
    }
    // ==========================================================================
    // CONNECTION MANAGEMENT
    // ==========================================================================
    BinanceWebSocket.prototype.connect = function () {
        return __awaiter(this, arguments, void 0, function (streams) {
            var url;
            var _this = this;
            if (streams === void 0) { streams = []; }
            return __generator(this, function (_a) {
                if (this.ws && this.ws.readyState === ws_1.default.OPEN) {
                    console.log('🌈 WebSocket already connected');
                    return [2 /*return*/];
                }
                if (this.isConnecting) {
                    console.log('🌈 Connection already in progress...');
                    return [2 /*return*/];
                }
                this.isConnecting = true;
                this.isClosing = false;
                try {
                    url = streams.length > 0
                        ? "".concat(this.baseUrl, "/stream?streams=").concat(streams.join('/'))
                        : "".concat(this.baseUrl, "/ws");
                    console.log("\uD83C\uDF08 Connecting to Binance WebSocket...");
                    console.log("   URL: ".concat(url));
                    this.ws = new ws_1.default(url);
                    // Setup event handlers
                    this.ws.on('open', function () { return _this.onOpen(streams); });
                    this.ws.on('message', function (data) { return _this.onMessage(data); });
                    this.ws.on('error', function (error) { return _this.onError(error); });
                    this.ws.on('close', function (code, reason) { return _this.onClose(code, reason); });
                    this.ws.on('ping', function (data) { return _this.onPing(data); });
                    this.ws.on('pong', function (data) { return _this.onPong(data); });
                }
                catch (error) {
                    this.isConnecting = false;
                    console.error('🌈 Connection failed:', error);
                    throw error;
                }
                return [2 /*return*/];
            });
        });
    };
    BinanceWebSocket.prototype.onOpen = function (initialStreams) {
        var _this = this;
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.reconnectDelay = 1000;
        console.log('🌈 WebSocket CONNECTED - Tasting the rainbow...');
        // Store initial streams
        initialStreams.forEach(function (s) { return _this.streams.add(s); });
        // Start heartbeat (ping every 20s as per Binance spec)
        this.startHeartbeat();
        this.emit('connected');
    };
    BinanceWebSocket.prototype.onMessage = function (data) {
        try {
            var message = JSON.parse(data.toString());
            // Handle subscription responses
            if (message.result !== undefined && message.id !== undefined) {
                this.handleSubscriptionResponse(message);
                return;
            }
            // Handle combined stream format
            if (message.stream && message.data) {
                this.processMarketEvent(message.stream, message.data);
                return;
            }
            // Handle single stream format
            if (message.e) {
                this.processMarketEvent('single', message);
                return;
            }
        }
        catch (error) {
            console.error('🌈 Message parse error:', error);
        }
    };
    BinanceWebSocket.prototype.onError = function (error) {
        console.error('🌈 WebSocket error:', error.message);
        this.emit('error', error);
    };
    BinanceWebSocket.prototype.onClose = function (code, reason) {
        console.log("\uD83C\uDF08 WebSocket CLOSED - Code: ".concat(code, ", Reason: ").concat(reason.toString() || 'Unknown'));
        this.stopHeartbeat();
        this.ws = null;
        if (!this.isClosing && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.scheduleReconnect();
        }
        this.emit('disconnected', { code: code, reason: reason.toString() });
    };
    BinanceWebSocket.prototype.onPing = function (data) {
        // Server sent ping - respond with pong
        if (this.ws && this.ws.readyState === ws_1.default.OPEN) {
            this.ws.pong(data);
        }
    };
    BinanceWebSocket.prototype.onPong = function (data) {
        // Server responded to our ping
        // console.log('🌈 Pong received');
    };
    // ==========================================================================
    // HEARTBEAT & RECONNECTION
    // ==========================================================================
    BinanceWebSocket.prototype.startHeartbeat = function () {
        var _this = this;
        this.stopHeartbeat();
        // Send ping every 20 seconds (Binance spec)
        this.pingInterval = setInterval(function () {
            if (_this.ws && _this.ws.readyState === ws_1.default.OPEN) {
                _this.ws.ping();
            }
        }, 20000);
    };
    BinanceWebSocket.prototype.stopHeartbeat = function () {
        if (this.pingInterval) {
            clearInterval(this.pingInterval);
            this.pingInterval = null;
        }
    };
    BinanceWebSocket.prototype.scheduleReconnect = function () {
        var _this = this;
        this.reconnectAttempts++;
        var delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1), 60000);
        console.log("\uD83C\uDF08 Reconnecting in ".concat(delay, "ms (attempt ").concat(this.reconnectAttempts, "/").concat(this.maxReconnectAttempts, ")..."));
        setTimeout(function () {
            var streamArray = Array.from(_this.streams);
            _this.connect(streamArray);
        }, delay);
    };
    // ==========================================================================
    // STREAM SUBSCRIPTION MANAGEMENT
    // ==========================================================================
    BinanceWebSocket.prototype.subscribe = function (streamNames) {
        var _this = this;
        if (!this.ws || this.ws.readyState !== ws_1.default.OPEN) {
            console.warn('🌈 Cannot subscribe - WebSocket not connected');
            return;
        }
        var subscription = {
            method: 'SUBSCRIBE',
            params: streamNames,
            id: ++this.subscriptionId
        };
        this.ws.send(JSON.stringify(subscription));
        streamNames.forEach(function (s) { return _this.streams.add(s); });
        console.log("\uD83C\uDF08 Subscribed to: ".concat(streamNames.join(', ')));
    };
    BinanceWebSocket.prototype.unsubscribe = function (streamNames) {
        var _this = this;
        if (!this.ws || this.ws.readyState !== ws_1.default.OPEN) {
            console.warn('🌈 Cannot unsubscribe - WebSocket not connected');
            return;
        }
        var subscription = {
            method: 'UNSUBSCRIBE',
            params: streamNames,
            id: ++this.subscriptionId
        };
        this.ws.send(JSON.stringify(subscription));
        streamNames.forEach(function (s) { return _this.streams.delete(s); });
        console.log("\uD83C\uDF08 Unsubscribed from: ".concat(streamNames.join(', ')));
    };
    BinanceWebSocket.prototype.listSubscriptions = function () {
        if (!this.ws || this.ws.readyState !== ws_1.default.OPEN) {
            console.warn('🌈 Cannot list subscriptions - WebSocket not connected');
            return;
        }
        var request = {
            method: 'LIST_SUBSCRIPTIONS',
            id: ++this.subscriptionId
        };
        this.ws.send(JSON.stringify(request));
    };
    BinanceWebSocket.prototype.handleSubscriptionResponse = function (response) {
        if (response.result === null) {
            // Success
            this.emit('subscription-response', { id: response.id, success: true });
        }
        else if (response.result && Array.isArray(response.result)) {
            // List of subscriptions
            console.log("\uD83C\uDF08 Active subscriptions: ".concat(response.result.join(', ')));
            this.emit('subscriptions-list', response.result);
        }
        else if (response.error) {
            // Error
            console.error("\uD83C\uDF08 Subscription error (ID ".concat(response.id, "):"), response.error);
            this.emit('subscription-error', response.error);
        }
    };
    // ==========================================================================
    // MARKET DATA PROCESSING
    // ==========================================================================
    BinanceWebSocket.prototype.processMarketEvent = function (stream, data) {
        var eventType = data.e;
        var symbol = data.s;
        // Update last update time
        this.lastUpdateTime.set(symbol, Date.now());
        // Emit specific event types
        switch (eventType) {
            case 'trade':
                this.processTrade(data);
                this.emit('trade', data);
                break;
            case 'aggTrade':
                this.processAggTrade(data);
                this.emit('aggTrade', data);
                break;
            case 'depthUpdate':
                this.processDepthUpdate(data);
                this.emit('depth', data);
                break;
            case '24hrMiniTicker':
                this.processMiniTicker(data);
                this.emit('miniTicker', data);
                break;
            case 'kline':
                this.processKline(data);
                this.emit('kline', data);
                break;
            default:
                // Book ticker has no 'e' field
                if (data.u && data.b && data.a) {
                    this.processBookTicker(data);
                    this.emit('bookTicker', data);
                }
        }
        // Emit generic market event
        this.emit('market-event', { stream: stream, data: data });
    };
    BinanceWebSocket.prototype.processTrade = function (trade) {
        var symbol = trade.s, price = trade.p, qty = trade.q, time = trade.T;
        // Buffer trades for momentum calculation
        if (!this.tradeBuffer.has(symbol)) {
            this.tradeBuffer.set(symbol, []);
        }
        var buffer = this.tradeBuffer.get(symbol);
        buffer.push(trade);
        // Keep only last 100 trades
        if (buffer.length > 100) {
            buffer.shift();
        }
        // Update market snapshot
        this.updateSnapshot(symbol, {
            price: parseFloat(price),
            volume: parseFloat(qty),
            timestamp: time
        });
    };
    BinanceWebSocket.prototype.processAggTrade = function (aggTrade) {
        var symbol = aggTrade.s, price = aggTrade.p, qty = aggTrade.q, time = aggTrade.T;
        this.updateSnapshot(symbol, {
            price: parseFloat(price),
            volume: parseFloat(qty),
            timestamp: time
        });
    };
    BinanceWebSocket.prototype.processDepthUpdate = function (depth) {
        var symbol = depth.s, bids = depth.b, asks = depth.a;
        if (bids.length > 0 && asks.length > 0) {
            var bestBid = parseFloat(bids[0][0]);
            var bestAsk = parseFloat(asks[0][0]);
            var spread = bestAsk - bestBid;
            this.updateSnapshot(symbol, {
                bidPrice: bestBid,
                askPrice: bestAsk,
                spread: spread
            });
        }
    };
    BinanceWebSocket.prototype.processBookTicker = function (ticker) {
        var symbol = ticker.s, bidPrice = ticker.b, askPrice = ticker.a;
        var bid = parseFloat(bidPrice);
        var ask = parseFloat(askPrice);
        var spread = ask - bid;
        this.updateSnapshot(symbol, {
            bidPrice: bid,
            askPrice: ask,
            spread: spread
        });
    };
    BinanceWebSocket.prototype.processMiniTicker = function (ticker) {
        var symbol = ticker.s, close = ticker.c, volume = ticker.v, eventTime = ticker.E;
        this.updateSnapshot(symbol, {
            price: parseFloat(close),
            volume: parseFloat(volume),
            timestamp: eventTime
        });
    };
    BinanceWebSocket.prototype.processKline = function (kline) {
        var symbol = kline.s, k = kline.k;
        if (k.x) { // Only process closed klines
            var close_1 = k.c, volume = k.v, trades = k.n;
            this.updateSnapshot(symbol, {
                price: parseFloat(close_1),
                volume: parseFloat(volume),
                trades: trades
            });
        }
    };
    BinanceWebSocket.prototype.updateSnapshot = function (symbol, update) {
        var snapshot = this.marketSnapshots.get(symbol);
        if (!snapshot) {
            snapshot = {
                symbol: symbol,
                timestamp: Date.now(),
                price: 0,
                volume: 0,
                trades: 0
            };
            this.marketSnapshots.set(symbol, snapshot);
        }
        // Merge update
        Object.assign(snapshot, update);
        snapshot.timestamp = Date.now();
        // Calculate volatility and momentum if we have trade history
        var tradeBuffer = this.tradeBuffer.get(symbol);
        if (tradeBuffer && tradeBuffer.length >= 10) {
            var prices = tradeBuffer.map(function (t) { return parseFloat(t.p); });
            var recent = prices.slice(-10);
            var avgPrice_1 = recent.reduce(function (a, b) { return a + b; }, 0) / recent.length;
            var variance = recent.reduce(function (sum, p) { return sum + Math.pow(p - avgPrice_1, 2); }, 0) / recent.length;
            snapshot.volatility = Math.sqrt(variance) / avgPrice_1; // Coefficient of variation
            var oldPrice = recent[0];
            var newPrice = recent[recent.length - 1];
            snapshot.momentum = (newPrice - oldPrice) / oldPrice;
        }
        this.emit('snapshot-update', snapshot);
    };
    // ==========================================================================
    // PUBLIC API
    // ==========================================================================
    BinanceWebSocket.prototype.getSnapshot = function (symbol) {
        return this.marketSnapshots.get(symbol);
    };
    BinanceWebSocket.prototype.getAllSnapshots = function () {
        return Array.from(this.marketSnapshots.values());
    };
    BinanceWebSocket.prototype.isConnected = function () {
        return this.ws !== null && this.ws.readyState === ws_1.default.OPEN;
    };
    BinanceWebSocket.prototype.getActiveStreams = function () {
        return Array.from(this.streams);
    };
    BinanceWebSocket.prototype.disconnect = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                this.isClosing = true;
                this.stopHeartbeat();
                if (this.ws) {
                    this.ws.close(1000, 'Client disconnect');
                    this.ws = null;
                }
                console.log('🌈 WebSocket disconnected');
                return [2 /*return*/];
            });
        });
    };
    return BinanceWebSocket;
}(events_1.EventEmitter));
exports.BinanceWebSocket = BinanceWebSocket;
// ============================================================================
// STREAM NAME BUILDERS
// ============================================================================
var StreamBuilder = /** @class */ (function () {
    function StreamBuilder() {
    }
    /**
     * Trade stream - Raw trade information
     * Update: Real-time
     */
    StreamBuilder.trade = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@trade");
    };
    /**
     * Aggregate trade stream - Aggregated for single taker order
     * Update: Real-time
     */
    StreamBuilder.aggTrade = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@aggTrade");
    };
    /**
     * Diff depth stream - Order book updates
     * Update: 1000ms or 100ms
     */
    StreamBuilder.depth = function (symbol, speed) {
        if (speed === void 0) { speed = '100ms'; }
        return speed === '100ms'
            ? "".concat(symbol.toLowerCase(), "@depth@100ms")
            : "".concat(symbol.toLowerCase(), "@depth");
    };
    /**
     * Partial book depth - Top N levels
     * Update: 1000ms or 100ms
     */
    StreamBuilder.partialDepth = function (symbol, levels, speed) {
        if (speed === void 0) { speed = '100ms'; }
        return speed === '100ms'
            ? "".concat(symbol.toLowerCase(), "@depth").concat(levels, "@100ms")
            : "".concat(symbol.toLowerCase(), "@depth").concat(levels);
    };
    /**
     * Book ticker - Best bid/ask
     * Update: Real-time
     */
    StreamBuilder.bookTicker = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@bookTicker");
    };
    /**
     * Mini ticker - 24hr rolling window
     * Update: 1000ms
     */
    StreamBuilder.miniTicker = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@miniTicker");
    };
    /**
     * All market mini tickers
     * Update: 1000ms
     */
    StreamBuilder.allMiniTickers = function () {
        return '!miniTicker@arr';
    };
    /**
     * Kline/Candlestick stream
     * Update: 1000ms for 1s, 2000ms for others
     */
    StreamBuilder.kline = function (symbol, interval) {
        return "".concat(symbol.toLowerCase(), "@kline_").concat(interval);
    };
    /**
     * Average price stream
     * Update: 1000ms
     */
    StreamBuilder.avgPrice = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@avgPrice");
    };
    /**
     * Full ticker - 24hr statistics
     * Update: 1000ms
     */
    StreamBuilder.ticker = function (symbol) {
        return "".concat(symbol.toLowerCase(), "@ticker");
    };
    /**
     * All market tickers
     * Update: 1000ms
     */
    StreamBuilder.allTickers = function () {
        return '!ticker@arr';
    };
    /**
     * Rolling window ticker
     * Update: 1000ms
     */
    StreamBuilder.rollingTicker = function (symbol, windowSize) {
        return "".concat(symbol.toLowerCase(), "@ticker_").concat(windowSize);
    };
    /**
     * Build AUREON default streams - optimized for Master Equation
     */
    StreamBuilder.aureonDefaults = function (symbol) {
        return [
            StreamBuilder.aggTrade(symbol), // Price + momentum
            StreamBuilder.depth(symbol, '100ms'), // Order book dynamics
            StreamBuilder.miniTicker(symbol), // 24hr stats
            StreamBuilder.kline(symbol, '1m') // Candlestick pattern
        ];
    };
    return StreamBuilder;
}());
exports.StreamBuilder = StreamBuilder;
