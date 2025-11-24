"use strict";
/**
 * Binance API Client - Production-grade live trading integration
 * - REST API for account info, order placement, execution
 * - WebSocket for real-time price feeds & order updates
 * - Secure credential management with encryption
 * - Testnet/Live mode toggle
 */
var __assign = (this && this.__assign) || function () {
    __assign = Object.assign || function(t) {
        for (var s, i = 1, n = arguments.length; i < n; i++) {
            s = arguments[i];
            for (var p in s) if (Object.prototype.hasOwnProperty.call(s, p))
                t[p] = s[p];
        }
        return t;
    };
    return __assign.apply(this, arguments);
};
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
exports.BinanceClient = void 0;
var crypto_1 = require("crypto");
var BinanceClient = /** @class */ (function () {
    function BinanceClient(config) {
        this.recvWindow = 5000;
        this.apiKey = config.apiKey;
        this.apiSecret = config.apiSecret;
        this.recvWindow = config.recvWindow || 5000;
        if (config.testnet) {
            this.baseUrl = 'https://testnet.binance.vision/api';
            this.wsBaseUrl = 'wss://stream.testnet.binance.vision:9443/ws';
        }
        else {
            this.baseUrl = 'https://api.binance.com/api';
            this.wsBaseUrl = 'wss://stream.binance.com:9443/ws';
        }
    }
    /**
     * Sign request parameters using HMAC-SHA256
     */
    BinanceClient.prototype.signParams = function (params) {
        var queryString = this.buildQueryString(params);
        var signature = crypto_1.default
            .createHmac('sha256', this.apiSecret)
            .update(queryString)
            .digest('hex');
        return "".concat(queryString, "&signature=").concat(signature);
    };
    /**
     * Build query string from params object
     */
    BinanceClient.prototype.buildQueryString = function (params) {
        return Object.entries(params)
            .filter(function (_a) {
            var v = _a[1];
            return v !== undefined && v !== null;
        })
            .map(function (_a) {
            var k = _a[0], v = _a[1];
            return "".concat(k, "=").concat(encodeURIComponent(v));
        })
            .join('&');
    };
    /**
     * Make authenticated request to Binance REST API
     */
    BinanceClient.prototype.request = function (method, endpoint, params) {
        return __awaiter(this, void 0, void 0, function () {
            var timestamp, fullParams, signedParams, url, response, errorData;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        timestamp = Date.now();
                        fullParams = __assign({ timestamp: timestamp }, params);
                        signedParams = this.signParams(fullParams);
                        url = "".concat(this.baseUrl).concat(endpoint, "?").concat(signedParams);
                        return [4 /*yield*/, fetch(url, {
                                method: method,
                                headers: {
                                    'X-MBX-APIKEY': this.apiKey,
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                },
                            })];
                    case 1:
                        response = _a.sent();
                        if (!!response.ok) return [3 /*break*/, 3];
                        return [4 /*yield*/, response.json().catch(function () { return ({}); })];
                    case 2:
                        errorData = _a.sent();
                        throw new Error("Binance API error (".concat(response.status, "): ").concat(JSON.stringify(errorData)));
                    case 3: return [2 /*return*/, response.json()];
                }
            });
        });
    };
    /**
     * Get account information (balances, trading status)
     */
    BinanceClient.prototype.getAccount = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('GET', '/v3/account')];
            });
        });
    };
    /**
     * Get current price of a symbol (public endpoint, no auth required)
     */
    BinanceClient.prototype.getPrice = function (symbol) {
        return __awaiter(this, void 0, void 0, function () {
            var url, response, data;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        url = "".concat(this.baseUrl, "/v3/ticker/price?symbol=").concat(symbol);
                        return [4 /*yield*/, fetch(url)];
                    case 1:
                        response = _a.sent();
                        if (!response.ok) {
                            throw new Error("Binance API error (".concat(response.status, "): Failed to fetch price"));
                        }
                        return [4 /*yield*/, response.json()];
                    case 2:
                        data = (_a.sent());
                        return [2 /*return*/, Number(data.price)];
                }
            });
        });
    };
    /**
     * Get 24h ticker stats (volume, price change, etc)
     */
    BinanceClient.prototype.get24hStats = function (symbol) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('GET', '/v3/ticker/24hr', { symbol: symbol })];
            });
        });
    };
    /**
     * Get exchange info (symbols, filters)
     */
    BinanceClient.prototype.getExchangeInfo = function (symbols) {
        return __awaiter(this, void 0, void 0, function () {
            var url, resp;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        url = symbols && symbols.length
                            ? "".concat(this.baseUrl, "/v3/exchangeInfo?symbols=").concat(encodeURIComponent(JSON.stringify(symbols)))
                            : "".concat(this.baseUrl, "/v3/exchangeInfo");
                        return [4 /*yield*/, fetch(url)];
                    case 1:
                        resp = _a.sent();
                        if (!resp.ok) {
                            throw new Error("Binance API error (".concat(resp.status, "): Failed to fetch exchangeInfo"));
                        }
                        return [2 /*return*/, resp.json()];
                }
            });
        });
    };
    /**
     * Get order book depth (public endpoint) for liquidity checks
     */
    BinanceClient.prototype.getOrderBook = function (symbol_1) {
        return __awaiter(this, arguments, void 0, function (symbol, limit) {
            var url, resp;
            if (limit === void 0) { limit = 10; }
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        url = "".concat(this.baseUrl, "/v3/depth?symbol=").concat(symbol, "&limit=").concat(limit);
                        return [4 /*yield*/, fetch(url)];
                    case 1:
                        resp = _a.sent();
                        if (!resp.ok) {
                            throw new Error("Binance API error (".concat(resp.status, "): Failed to fetch order book for ").concat(symbol));
                        }
                        return [2 /*return*/, resp.json()];
                }
            });
        });
    };
    /**
     * Place a market or limit order
     */
    BinanceClient.prototype.placeOrder = function (order) {
        return __awaiter(this, void 0, void 0, function () {
            var params;
            return __generator(this, function (_a) {
                params = {
                    symbol: order.symbol,
                    side: order.side,
                    type: order.type,
                };
                // Prefer quoteOrderQty for MARKET orders when provided; otherwise use quantity
                if (order.type === 'MARKET' && order.quoteOrderQty && order.quoteOrderQty > 0) {
                    params.quoteOrderQty = order.quoteOrderQty;
                }
                else if (order.quantity && order.quantity > 0) {
                    params.quantity = order.quantity;
                }
                if (order.type === 'LIMIT') {
                    if (!order.price)
                        throw new Error('Price required for LIMIT orders');
                    params.price = order.price;
                    params.timeInForce = order.timeInForce || 'GTC';
                }
                return [2 /*return*/, this.request('POST', '/v3/order', params)];
            });
        });
    };
    /**
     * Cancel an open order
     */
    BinanceClient.prototype.cancelOrder = function (symbol, orderId) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('DELETE', '/v3/order', {
                        symbol: symbol,
                        orderId: orderId,
                    })];
            });
        });
    };
    /**
     * Get order status
     */
    BinanceClient.prototype.getOrder = function (symbol, orderId) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('GET', '/v3/order', {
                        symbol: symbol,
                        orderId: orderId,
                    })];
            });
        });
    };
    /**
     * Get all open orders (or specific symbol)
     */
    BinanceClient.prototype.getOpenOrders = function (symbol) {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('GET', '/v3/openOrders', symbol ? { symbol: symbol } : {})];
            });
        });
    };
    /**
     * Get account trade list for a symbol (requires auth)
     */
    BinanceClient.prototype.getMyTrades = function (symbol_1) {
        return __awaiter(this, arguments, void 0, function (symbol, limit) {
            if (limit === void 0) { limit = 20; }
            return __generator(this, function (_a) {
                return [2 /*return*/, this.request('GET', '/v3/myTrades', { symbol: symbol, limit: limit })];
            });
        });
    };
    /**
     * Subscribe to real-time price updates via WebSocket
     * Returns a subscription handle that can be closed
     */
    BinanceClient.prototype.subscribeToPrice = function (symbol, callback) {
        var streamName = "".concat(symbol.toLowerCase(), "@trade");
        var ws = new WebSocket("".concat(this.wsBaseUrl, "/").concat(streamName));
        ws.onmessage = function (event) {
            try {
                var data = JSON.parse(event.data);
                callback({
                    symbol: data.s,
                    price: Number(data.p),
                    time: data.T,
                });
            }
            catch (err) {
                console.error('WebSocket parse error:', err);
            }
        };
        ws.onerror = function (err) {
            console.error("WebSocket error for ".concat(symbol, ":"), err);
        };
        // Return unsubscribe function
        return function () {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    };
    /**
     * Subscribe to multiple price streams with a single WebSocket connection
     */
    BinanceClient.prototype.subscribeToMultiplePrices = function (symbols, callback) {
        var streams = symbols.map(function (s) { return "".concat(s.toLowerCase(), "@trade"); });
        var streamParam = streams.join('/');
        var ws = new WebSocket("".concat(this.wsBaseUrl, "/stream?streams=").concat(streamParam));
        ws.onmessage = function (event) {
            try {
                var message = JSON.parse(event.data);
                if (message.data) {
                    var data = message.data;
                    callback({
                        symbol: data.s,
                        price: Number(data.p),
                        time: data.T,
                    });
                }
            }
            catch (err) {
                console.error('WebSocket parse error:', err);
            }
        };
        ws.onerror = function (err) {
            console.error('WebSocket error:', err);
        };
        return function () {
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    };
    /**
     * Get Binance server time (for sync validation)
     */
    BinanceClient.prototype.getServerTime = function () {
        return __awaiter(this, void 0, void 0, function () {
            var data;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0: return [4 /*yield*/, this.request('GET', '/v3/time')];
                    case 1:
                        data = _a.sent();
                        return [2 /*return*/, data.serverTime];
                }
            });
        });
    };
    return BinanceClient;
}());
exports.BinanceClient = BinanceClient;
