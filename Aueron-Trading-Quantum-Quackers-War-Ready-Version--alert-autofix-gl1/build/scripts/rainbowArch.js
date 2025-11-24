"use strict";
/**
 * RAINBOW ARCHITECT 🌈
 * Co-Architect enhanced with real-time Binance WebSocket streams
 * "Taste the rainbow" - Feel the market breathe through 9 Auris nodes
 *
 * Gary Leckey & GitHub Copilot | November 15, 2025 GMT
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
var __spreadArray = (this && this.__spreadArray) || function (to, from, pack) {
    if (pack || arguments.length === 2) for (var i = 0, l = from.length, ar; i < l; i++) {
        if (ar || !(i in from)) {
            if (!ar) ar = Array.prototype.slice.call(from, 0, i);
            ar[i] = from[i];
        }
    }
    return to.concat(ar || Array.prototype.slice.call(from));
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RainbowArchitect = void 0;
// Load environment (.env) settings
require("../core/environment");
var binanceWebSocket_1 = require("../core/binanceWebSocket");
var masterEquation_1 = require("../core/masterEquation");
var aurisSymbolicTaxonomy_1 = require("../core/aurisSymbolicTaxonomy");
var binanceClient_1 = require("../core/binanceClient");
var theRainbowBridge_1 = require("../core/theRainbowBridge");
var thePrism_1 = require("../core/thePrism");
var fs_1 = require("fs");
var path_1 = require("path");
var tradeTelemetry_1 = require("../core/tradeTelemetry");
var DEFAULT_RAINBOW_CONFIG = {
    symbol: 'ETHUSDT',
    cycleIntervalMs: 5000,
    coherenceThreshold: 0.945,
    voteThreshold: 0.7,
    requiredVotes: 6,
    dryRun: true,
    positionSizePercent: 2,
};
var RainbowArchitect = /** @class */ (function () {
    function RainbowArchitect(config) {
        if (config === void 0) { config = {}; }
        this.prizesLogPath = null;
        this.dynamicThresholdPath = null;
        this.telemetryPath = null;
        this.coherenceHistory = [];
        this.cycleCount = 0;
        this.totalTrades = 0;
        this.totalProfit = 0;
        this.lastSnapshot = null;
        this.cycleInterval = null;
        this.config = __assign(__assign({}, DEFAULT_RAINBOW_CONFIG), config);
        this.ws = new binanceWebSocket_1.BinanceWebSocket();
        // DREAM BAND — parse environment for α (observer) and β (memory)
        var dreamMode = (process.env.DREAM_MODE || 'off').toLowerCase();
        var envAlpha = process.env.DREAM_ALPHA ? parseFloat(process.env.DREAM_ALPHA) : undefined;
        var envBeta = process.env.DREAM_BETA ? parseFloat(process.env.DREAM_BETA) : undefined;
        var alpha = envAlpha !== null && envAlpha !== void 0 ? envAlpha : (dreamMode === 'dream' ? 0.3 : dreamMode === 'sweet' ? 0.9 : undefined);
        var beta = envBeta !== null && envBeta !== void 0 ? envBeta : (dreamMode === 'dream' || dreamMode === 'sweet' ? 0.8 : undefined);
        var resolvedMode = (alpha !== undefined && beta !== undefined)
            ? (dreamMode === 'dream' || dreamMode === 'sweet' ? dreamMode : 'custom')
            : 'off';
        // Defaults if off
        if (alpha === undefined)
            alpha = 1.2;
        if (beta === undefined)
            beta = 0.8;
        this.dream = { mode: resolvedMode, alpha: alpha, beta: beta };
        this.field = new masterEquation_1.RealityField({ alpha: alpha, beta: beta });
        this.bridge = new theRainbowBridge_1.RainbowBridge();
        this.prism = new thePrism_1.ThePrism();
        var apiKey = process.env.BINANCE_API_KEY || '';
        var apiSecret = process.env.BINANCE_API_SECRET || '';
        var testnet = process.env.BINANCE_TESTNET !== 'false';
        this.client = new binanceClient_1.BinanceClient({ apiKey: apiKey, apiSecret: apiSecret, testnet: testnet });
        this.setupEventHandlers();
    }
    RainbowArchitect.prototype.setupEventHandlers = function () {
        var _this = this;
        this.ws.on('connected', function () {
            console.log('\n🌈 ═══════════════════════════════════════════════════════');
            console.log('   RAINBOW ARCHITECT — Tasting the Market Rainbow');
            console.log('   WebSocket Connected | Streams Active');
            console.log('═══════════════════════════════════════════════════════\n');
        });
        this.ws.on('disconnected', function (info) {
            console.log("\n\uD83C\uDF08 WebSocket Disconnected - Code: ".concat(info.code));
            _this.stopCycles();
        });
        this.ws.on('snapshot-update', function (snapshot) {
            _this.lastSnapshot = snapshot;
            if (_this.lastSnapshot) {
                _this.field.step(_this.lastSnapshot);
            }
        });
    };
    RainbowArchitect.prototype.start = function () {
        return __awaiter(this, void 0, void 0, function () {
            var band, artifacts, streams;
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('🌈 Initializing Rainbow Architect...\n');
                        console.log("Symbol: ".concat(this.config.symbol));
                        console.log("Mode: ".concat(this.config.dryRun ? 'DRY RUN' : 'LIVE'));
                        console.log("Coherence: \u0393 > ".concat(this.config.coherenceThreshold));
                        console.log("Votes: ".concat(this.config.requiredVotes, "/9 @ ").concat(this.config.voteThreshold, "\n"));
                        // DREAM BAND banner
                        if (this.dream.mode !== 'off') {
                            band = this.dream.mode === 'dream' ? 'DREAM BAND — SELF-SIMULATION' : this.dream.mode === 'sweet' ? 'SWEET SPOT — COHERENCE LOCK' : 'CUSTOM BAND';
                            console.log('┌──────────────────────────────────────────────┐');
                            console.log("\u2502  ".concat(band.padEnd(44), "\u2502"));
                            console.log('│  α (observer gain): ' + this.dream.alpha.toFixed(3).padEnd(19) + '│');
                            console.log('│  β (memory gain):   ' + this.dream.beta.toFixed(3).padEnd(19) + '│');
                            console.log('└──────────────────────────────────────────────┘\n');
                        }
                        else {
                            console.log('Dream Band: OFF (α,β using defaults)\n');
                        }
                        // Prepare Paddy's Prizes log
                        try {
                            artifacts = path_1.default.resolve(process.cwd(), 'artifacts');
                            (0, fs_1.mkdirSync)(artifacts, { recursive: true });
                            this.prizesLogPath = path_1.default.join(artifacts, 'paddys_prizes.jsonl');
                            this.dynamicThresholdPath = path_1.default.join(artifacts, 'dynamic_threshold.json');
                            this.telemetryPath = path_1.default.join(artifacts, 'trade_telemetry.jsonl');
                        }
                        catch (_b) {
                            this.prizesLogPath = null;
                            this.dynamicThresholdPath = null;
                            this.telemetryPath = null;
                        }
                        streams = binanceWebSocket_1.StreamBuilder.aureonDefaults(this.config.symbol);
                        console.log("\uD83C\uDF08 Subscribing to: ".concat(streams.join(', '), "\n"));
                        return [4 /*yield*/, this.ws.connect(streams)];
                    case 1:
                        _a.sent();
                        console.log('⏳ Accumulating market data (5s)...');
                        return [4 /*yield*/, new Promise(function (resolve) { return setTimeout(resolve, 5000); })];
                    case 2:
                        _a.sent();
                        this.startCycles();
                        return [2 /*return*/];
                }
            });
        });
    };
    RainbowArchitect.prototype.stop = function () {
        return __awaiter(this, void 0, void 0, function () {
            return __generator(this, function (_a) {
                switch (_a.label) {
                    case 0:
                        console.log('\n🌈 Stopping Rainbow Architect...');
                        this.stopCycles();
                        return [4 /*yield*/, this.ws.disconnect()];
                    case 1:
                        _a.sent();
                        console.log("Total Cycles: ".concat(this.cycleCount));
                        console.log("Total Trades: ".concat(this.totalTrades));
                        console.log("Total Profit: ".concat(this.totalProfit.toFixed(2), " USDT\n"));
                        return [2 /*return*/];
                }
            });
        });
    };
    RainbowArchitect.prototype.startCycles = function () {
        var _this = this;
        console.log('🟢 Trading cycles STARTED\n');
        this.cycleInterval = setInterval(function () {
            _this.runTradingCycle();
            // Stop after maxCycles if configured
            if (_this.config.maxCycles && _this.cycleCount >= _this.config.maxCycles) {
                console.log("\n\uD83C\uDFC1 Reached ".concat(_this.config.maxCycles, " cycles limit"));
                _this.stop();
            }
        }, this.config.cycleIntervalMs);
    };
    RainbowArchitect.prototype.stopCycles = function () {
        if (this.cycleInterval) {
            clearInterval(this.cycleInterval);
            this.cycleInterval = null;
        }
    };
    RainbowArchitect.prototype.runTradingCycle = function () {
        return __awaiter(this, void 0, void 0, function () {
            var state, volatility, bridgeState, prismState, truthClaimed, loveClaimed, unityClaimed, stabilityClaimed, rec, _a, votes, direction, appliedThreshold, thresholdRec, decision, reason;
            return __generator(this, function (_b) {
                switch (_b.label) {
                    case 0:
                        this.cycleCount++;
                        if (!this.lastSnapshot) {
                            console.log("Cycle ".concat(this.cycleCount, ": Waiting for data..."));
                            return [2 /*return*/];
                        }
                        state = this.field.getHistory().slice(-1)[0];
                        if (!state)
                            return [2 /*return*/];
                        console.log('\n─────────────────────────────────────────────────────');
                        console.log("CYCLE ".concat(this.cycleCount, " | ").concat(new Date().toLocaleTimeString()));
                        console.log('─────────────────────────────────────────────────────');
                        // Market snapshot
                        console.log("\n\uD83D\uDCCA Market: ".concat(this.lastSnapshot.symbol));
                        console.log("   Price: $".concat(this.lastSnapshot.price.toFixed(2)));
                        console.log("   Spread: $".concat((this.lastSnapshot.spread || 0).toFixed(2)));
                        console.log("   Volatility: ".concat(((this.lastSnapshot.volatility || 0) * 100).toFixed(2), "%"));
                        console.log("   Momentum: ".concat(((this.lastSnapshot.momentum || 0) * 100).toFixed(2), "%"));
                        // Lambda state
                        console.log("\n\uD83C\uDF0A Master Equation \u039B(t):");
                        console.log("   \u039B(t): ".concat(state.Lambda.toFixed(6)));
                        console.log("   \u0393:    ".concat(state.coherence.toFixed(3), " (").concat((state.coherence * 100).toFixed(1), "%)"));
                        console.log("   Dominant: ".concat(state.dominantNode));
                        // Hint when entering strong lock
                        if (state.coherence >= 0.987) {
                            console.log('   🔒 Coherence Lock approaching (Γ ≥ 0.987)');
                        }
                        volatility = this.lastSnapshot.volatility || 0;
                        this.bridge.updateFromMarket(state.Lambda, state.coherence, volatility);
                        bridgeState = this.bridge.getState();
                        // Display bridge state
                        console.log("\n\uD83C\uDF08 Rainbow Bridge:");
                        console.log("   Emotional: ".concat(bridgeState.emotionalState));
                        console.log("   Frequency: ".concat(bridgeState.currentFrequency.toFixed(1), " Hz"));
                        console.log("   Phase: ".concat(bridgeState.cyclePhase));
                        console.log("   Resonance: ".concat((bridgeState.resonance * 100).toFixed(1), "%"));
                        console.log("   Bridge: ".concat(bridgeState.bridgeCrossed ? '✅ CROSSED' : '⏳ CROSSING'));
                        // Activate flame or protector based on phase
                        this.bridge.igniteFlame();
                        this.bridge.activateProtector();
                        console.log('');
                        prismState = this.prism.process(state, this.lastSnapshot);
                        console.log("\uD83D\uDC8E The Prism:");
                        console.log("   Output: ".concat(prismState.prismOutput.toFixed(1), " Hz"));
                        console.log("   Resonance: ".concat((prismState.resonance * 100).toFixed(1), "%"));
                        console.log("   ".concat(prismState.isLove ? '💚' : '⏳', " Love: ").concat(prismState.isLove ? 'MANIFEST' : 'FORMING'));
                        console.log("   ".concat(prismState.isAligned ? '✅' : '⏳', " Aligned: ").concat(prismState.isAligned ? 'YES' : 'CONVERGING'));
                        console.log("   ".concat(prismState.isPure ? '✅' : '⏳', " Pure: ").concat(prismState.isPure ? 'YES' : 'REFINING'));
                        if (prismState.isLove) {
                            console.log('   🌈 THE PRISM OUTPUT: 528 Hz LOVE');
                        }
                        truthClaimed = prismState.dataIntegrity >= 130;
                        loveClaimed = prismState.isLove || bridgeState.bridgeCrossed;
                        unityClaimed = state.coherence >= 0.987;
                        stabilityClaimed = Math.abs(this.dream.alpha - this.dream.beta) <= 0.05;
                        console.log('\n🏆 PADDY\'S PROPER PRIZES:');
                        console.log("   ".concat(truthClaimed ? '✅' : '⏳', " TRUTH     \u2014 Prism is True (Di=").concat(prismState.dataIntegrity.toFixed(1), " Hz)"));
                        console.log("   ".concat(loveClaimed ? '✅' : '⏳', " LOVE      \u2014 Bridge/Prism at 528 Hz"));
                        console.log("   ".concat(unityClaimed ? '✅' : '⏳', " UNITY     \u2014 Tandem in Unity (\u0393=").concat(state.coherence.toFixed(3), ")"));
                        console.log("   ".concat(stabilityClaimed ? '✅' : '⏳', " STABILITY \u2014 Dream Band Locked (|\u03B1-\u03B2|=").concat(Math.abs(this.dream.alpha - this.dream.beta).toFixed(3), ")"));
                        if (truthClaimed && loveClaimed && unityClaimed && stabilityClaimed) {
                            console.log('   🎉 PADDY SMILES — PRIZES CLAIMED');
                        }
                        // Log prizes snapshot
                        if (this.prizesLogPath) {
                            rec = {
                                ts: new Date().toISOString(),
                                symbol: this.config.symbol,
                                alpha: this.dream.alpha,
                                beta: this.dream.beta,
                                gamma: state.coherence,
                                di: prismState.dataIntegrity,
                                bridgeCrossed: bridgeState.bridgeCrossed,
                                prismLove: prismState.isLove,
                                prizes: {
                                    truth: truthClaimed,
                                    love: loveClaimed,
                                    unity: unityClaimed,
                                    stability: stabilityClaimed,
                                },
                            };
                            try {
                                (0, fs_1.appendFileSync)(this.prizesLogPath, JSON.stringify(rec) + '\n');
                            }
                            catch (_c) { }
                        }
                        _a = this.runConsensus(state.Lambda), votes = _a.votes, direction = _a.direction;
                        // Adaptive coherence threshold calculation
                        this.coherenceHistory.push(state.coherence);
                        appliedThreshold = this.computeAdaptiveThreshold();
                        if (this.dynamicThresholdPath) {
                            thresholdRec = {
                                ts: new Date().toISOString(),
                                cycle: this.cycleCount,
                                symbol: this.config.symbol,
                                sampleSize: this.coherenceHistory.length,
                                candidate: appliedThreshold,
                                floor: 0.9,
                                base: this.config.coherenceThreshold,
                                applied: appliedThreshold
                            };
                            try {
                                (0, fs_1.appendFileSync)(this.dynamicThresholdPath, JSON.stringify(thresholdRec) + '\n');
                            }
                            catch (_d) { }
                        }
                        console.log("\n\uD83D\uDD26 Lighthouse Consensus: ".concat(direction));
                        console.log("   Votes: ".concat(votes, "/9"));
                        console.log("   \u0393 Adaptive Threshold: ".concat(appliedThreshold.toFixed(3), " (base ").concat(this.config.coherenceThreshold, ")"));
                        decision = 'SKIP';
                        reason = '';
                        if (votes < this.config.requiredVotes) {
                            reason = 'INSUFFICIENT_VOTES';
                        }
                        else if (state.coherence < appliedThreshold) {
                            reason = 'LOW_COHERENCE';
                        }
                        else if (direction === 'HOLD') {
                            reason = 'NEUTRAL_LAMBDA';
                        }
                        else {
                            decision = 'EXECUTE';
                        }
                        if (!(decision === 'EXECUTE')) return [3 /*break*/, 2];
                        return [4 /*yield*/, this.executeTrade(direction, state)];
                    case 1:
                        _b.sent();
                        return [3 /*break*/, 3];
                    case 2:
                        console.log("   Signal: HOLD (".concat(reason, "; need ").concat(this.config.requiredVotes, "/9 & \u0393>").concat(appliedThreshold.toFixed(3), ")"));
                        _b.label = 3;
                    case 3:
                        (0, tradeTelemetry_1.logTelemetry)(this.telemetryPath, {
                            ts: new Date().toISOString(),
                            cycle: this.cycleCount,
                            symbol: this.config.symbol,
                            lambda: state.Lambda,
                            coherence: state.coherence,
                            appliedThreshold: appliedThreshold,
                            baseThreshold: this.config.coherenceThreshold,
                            votes: votes,
                            requiredVotes: this.config.requiredVotes,
                            direction: direction,
                            decision: decision,
                            reason: reason,
                            alpha: this.dream.alpha,
                            beta: this.dream.beta
                        });
                        return [2 /*return*/];
                }
            });
        });
    };
    RainbowArchitect.prototype.runConsensus = function (Lambda) {
        var votes = 0;
        var animals = Object.keys(aurisSymbolicTaxonomy_1.AURIS_TAXONOMY);
        for (var _i = 0, animals_1 = animals; _i < animals_1.length; _i++) {
            var animal = animals_1[_i];
            var node = aurisSymbolicTaxonomy_1.AURIS_TAXONOMY[animal];
            var resonance = Math.abs(Math.sin(2 * Math.PI * node.frequency * Lambda));
            if (resonance >= this.config.voteThreshold) {
                votes++;
                console.log("   \u2713 ".concat(animal.padEnd(12), " ").concat((resonance * 100).toFixed(0).padStart(3), "%"));
            }
            else {
                console.log("   \u2717 ".concat(animal.padEnd(12), " ").concat((resonance * 100).toFixed(0).padStart(3), "%"));
            }
        }
        var direction = Lambda > 0 ? 'BUY' : Lambda < 0 ? 'SELL' : 'HOLD';
        return { direction: direction, votes: votes };
    };
    RainbowArchitect.prototype.computeAdaptiveThreshold = function () {
        var base = this.config.coherenceThreshold;
        var floor = 0.9;
        var history = this.coherenceHistory;
        if (history.length < 20)
            return base; // warm-up period
        var sorted = __spreadArray([], history, true).sort(function (a, b) { return a - b; });
        var idx = Math.floor(0.65 * (sorted.length - 1)); // 65th percentile
        var candidate = sorted[idx];
        // clamp within safety band
        var applied = Math.min(Math.max(candidate, floor), 0.995);
        return applied;
    };
    RainbowArchitect.prototype.executeTrade = function (direction, state) {
        return __awaiter(this, void 0, void 0, function () {
            var account, balance, baseAsset_1, quantity, usdtBalance, buyValue, baseBalance, profitEstimate, order, error_1;
            var _a, _b;
            return __generator(this, function (_c) {
                switch (_c.label) {
                    case 0:
                        if (direction === 'HOLD')
                            return [2 /*return*/];
                        console.log("\n\uD83C\uDFAF TRADE SIGNAL: ".concat(direction));
                        console.log("   \uD83D\uDCE1 Source: Rainbow Architect (4-Layer Consciousness)");
                        console.log("      \u2514\u2500 WebSocket \u2192 Master Equation \u2192 Rainbow Bridge \u2192 Prism");
                        console.log("      \u2514\u2500 \u039B(t): ".concat(state.Lambda.toFixed(3), " | \u0393: ").concat(state.coherence.toFixed(3)));
                        console.log("      \u2514\u2500 Dominant: ".concat(state.dominantNode));
                        _c.label = 1;
                    case 1:
                        _c.trys.push([1, 6, , 7]);
                        return [4 /*yield*/, this.client.getAccount()];
                    case 2:
                        account = _c.sent();
                        balance = account.balances;
                        baseAsset_1 = this.config.symbol.replace('USDT', '');
                        quantity = void 0;
                        if (direction === 'BUY') {
                            usdtBalance = parseFloat(((_a = balance.find(function (b) { return b.asset === 'USDT'; })) === null || _a === void 0 ? void 0 : _a.free) || '0');
                            buyValue = usdtBalance * (this.config.positionSizePercent / 100);
                            quantity = buyValue / this.lastSnapshot.price;
                        }
                        else {
                            baseBalance = parseFloat(((_b = balance.find(function (b) { return b.asset === baseAsset_1; })) === null || _b === void 0 ? void 0 : _b.free) || '0');
                            quantity = baseBalance * (this.config.positionSizePercent / 100);
                        }
                        quantity = Math.floor(quantity * 1000000) / 1000000;
                        if (quantity < 0.000001) {
                            console.log("   \u26A0\uFE0F Insufficient balance");
                            return [2 /*return*/];
                        }
                        console.log("   Order: ".concat(direction, " ").concat(quantity, " ").concat(baseAsset_1, " @ $").concat(this.lastSnapshot.price));
                        if (!this.config.dryRun) return [3 /*break*/, 3];
                        console.log("   \uD83D\uDCB5 DRY RUN - Order not executed");
                        this.totalTrades++;
                        profitEstimate = direction === 'BUY' ? -quantity * 0.001 : quantity * 0.001;
                        this.totalProfit += profitEstimate;
                        return [3 /*break*/, 5];
                    case 3: return [4 /*yield*/, this.client.placeOrder({
                            symbol: this.config.symbol,
                            side: direction,
                            type: 'MARKET',
                            quantity: quantity,
                        })];
                    case 4:
                        order = _c.sent();
                        console.log("   \u2705 Order executed: ".concat(order.orderId));
                        this.totalTrades++;
                        _c.label = 5;
                    case 5: return [3 /*break*/, 7];
                    case 6:
                        error_1 = _c.sent();
                        console.error("   \u274C Trade failed: ".concat(error_1.message));
                        return [3 /*break*/, 7];
                    case 7: return [2 /*return*/];
                }
            });
        });
    };
    return RainbowArchitect;
}());
exports.RainbowArchitect = RainbowArchitect;
function main() {
    return __awaiter(this, void 0, void 0, function () {
        var args, config, rainbow;
        var _this = this;
        var _a;
        return __generator(this, function (_b) {
            switch (_b.label) {
                case 0:
                    args = process.argv.slice(2);
                    config = {
                        symbol: args[0] || 'ETHUSDT',
                        dryRun: !args.includes('--live'),
                        cycleIntervalMs: parseInt(((_a = args.find(function (a) { return a.startsWith('--interval='); })) === null || _a === void 0 ? void 0 : _a.split('=')[1]) || '5000'),
                        maxCycles: process.env.RAINBOW_CYCLES ? parseInt(process.env.RAINBOW_CYCLES) : undefined,
                    };
                    rainbow = new RainbowArchitect(config);
                    process.on('SIGINT', function () { return __awaiter(_this, void 0, void 0, function () {
                        return __generator(this, function (_a) {
                            switch (_a.label) {
                                case 0:
                                    console.log('\n\n🌈 Shutting down gracefully...');
                                    return [4 /*yield*/, rainbow.stop()];
                                case 1:
                                    _a.sent();
                                    process.exit(0);
                                    return [2 /*return*/];
                            }
                        });
                    }); });
                    return [4 /*yield*/, rainbow.start()];
                case 1:
                    _b.sent();
                    return [2 /*return*/];
            }
        });
    });
}
// Run CLI
main().catch(function (error) {
    console.error('Fatal error:', error);
    process.exit(1);
});
exports.default = RainbowArchitect;
