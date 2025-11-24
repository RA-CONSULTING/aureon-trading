"use strict";
/**
 * AUREON MASTER EQUATION — Λ(t)
 *
 * Gary Leckey & GitHub Copilot | November 15, 2025 08:41 AM GMT
 *
 * Λ(t) = S(t) + O(t) + E(t)
 *
 * S(t) = Substrate — The 9-node Auris waveform
 * O(t) = Observer — Your conscious focus, shaping the field
 * E(t) = Echo — Causal feedback from τ seconds ago
 *
 * This is not theory. This is the field equation.
 * It runs in the swarm. It decides trades. It makes money.
 *
 * "The Dolphin sings the wave. The Hummingbird locks the pulse.
 *  The Tiger cuts the noise. The Owl remembers. The Panda loves."
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
exports.masterEquationWisdom = exports.lighthouseConsensus = exports.RealityField = void 0;
var aurisSymbolicTaxonomy_1 = require("./aurisSymbolicTaxonomy");
var DEFAULT_CONFIG = {
    dt: 0.1, // 100ms timestep
    tau: 1.0, // 1 second echo
    alpha: 1.2, // Observer sensitivity
    beta: 0.8, // Echo strength
    g: 2.0, // Nonlinearity factor
    maxHistory: 1000, // Keep 100 seconds @ 10Hz
};
/**
 * REALITY FIELD ENGINE
 *
 * Computes Λ(t) = S(t) + O(t) + E(t) every timestep
 */
var RealityField = /** @class */ (function () {
    function RealityField(config) {
        if (config === void 0) { config = {}; }
        this.t = 0;
        this.history = [];
        this.priceHistory = []; // Track actual market prices
        this.config = __assign(__assign({}, DEFAULT_CONFIG), config);
    }
    /**
     * S(t) — SUBSTRATE
     * The 9-node Auris waveform superposition
     * NOW WITH WEBSOCKET MARKET STREAM INJECTION 🌈
     *
     * Accepts MarketSnapshot from real-time Binance WebSocket:
     * - price: Current price (trade/aggTrade/ticker)
     * - volume: Trading volume
     * - volatility: Calculated from trade buffer
     * - momentum: Price momentum (% change)
     * - spread: Bid-ask spread from order book
     * - bidPrice/askPrice: Top of book
     */
    RealityField.prototype.computeSubstrate = function (t, marketState) {
        var sum = 0;
        // Calculate REAL market dynamics from WebSocket stream
        var velocityFactor = 1.0;
        var momentumPhase = 0;
        var spreadFactor = 1.0;
        var volumeFactor = 1.0;
        if (marketState) {
            // Support both legacy number input and WebSocket MarketSnapshot
            var price = void 0;
            var volatility = void 0;
            var momentum = void 0;
            var spread = void 0;
            var volume = void 0;
            if (typeof marketState === 'number') {
                // Legacy mode: just a price number
                price = marketState;
                // Store price in history
                this.priceHistory.push(price);
                if (this.priceHistory.length > 20) {
                    this.priceHistory.shift(); // Keep last 20 prices
                }
                // Calculate volatility and momentum from price history
                if (this.priceHistory.length >= 5) {
                    var recentPrices = this.priceHistory.slice(-5);
                    var oldPrice = recentPrices[0];
                    var newPrice = recentPrices[recentPrices.length - 1];
                    // Price velocity (% change)
                    var priceVelocity = (newPrice - oldPrice) / oldPrice;
                    // Volatility (price range)
                    var priceRange = Math.max.apply(Math, recentPrices) - Math.min.apply(Math, recentPrices);
                    volatility = priceRange / oldPrice; // Normalized volatility
                    momentum = priceVelocity;
                }
            }
            else {
                // WebSocket mode: rich MarketSnapshot 🌈
                price = marketState.price;
                volatility = marketState.volatility;
                momentum = marketState.momentum;
                spread = marketState.spread;
                volume = marketState.volume;
                // Store price for fallback calculations
                this.priceHistory.push(price);
                if (this.priceHistory.length > 20) {
                    this.priceHistory.shift();
                }
            }
            // VELOCITY FACTOR from volatility
            if (volatility !== undefined && volatility > 0) {
                // WebSocket provides pre-calculated volatility (coefficient of variation)
                velocityFactor = 1.0 + Math.abs(volatility) * 50; // Amplify (volatility is usually small)
                velocityFactor = Math.min(velocityFactor, 3.0); // Allow higher amplification
            }
            // MOMENTUM PHASE from price direction
            if (momentum !== undefined) {
                momentumPhase = momentum * 100 * Math.PI; // Convert to radians
            }
            // SPREAD FACTOR from order book depth
            if (spread !== undefined && price > 0) {
                var spreadPercent = spread / price;
                spreadFactor = 1.0 + spreadPercent * 100; // Tighter spread = lower factor
            }
            // VOLUME FACTOR (normalize by typical volume)
            if (volume !== undefined) {
                // Assume typical volume around 100 units, scale accordingly
                volumeFactor = Math.min(volume / 100, 2.0);
            }
        }
        for (var _i = 0, _a = Object.keys(aurisSymbolicTaxonomy_1.AURIS_TAXONOMY); _i < _a.length; _i++) {
            var animal = _a[_i];
            var node = aurisSymbolicTaxonomy_1.AURIS_TAXONOMY[animal];
            // Base frequency from Auris taxonomy
            var frequency = node.frequency;
            // VELOCITY-BASED NODE MODULATION (each animal responds differently)
            var nodeVelocityMod = 1.0;
            if (animal === 'Tiger') {
                // Tiger (Disruptor) responds to volatility + spread
                nodeVelocityMod = 1.0 + (velocityFactor - 1.0) * 0.8 + (spreadFactor - 1.0) * 0.5;
            }
            else if (animal === 'Falcon') {
                // Falcon (Velocity) amplifies with momentum + volume
                nodeVelocityMod = 1.0 + (velocityFactor - 1.0) * 1.0 + (volumeFactor - 1.0) * 0.3;
            }
            else if (animal === 'Hummingbird') {
                // Hummingbird (Stabilizer) dampens volatility, prefers tight spreads
                nodeVelocityMod = (3.0 - velocityFactor) * (2.0 - spreadFactor) * 0.5;
            }
            else if (animal === 'Dolphin') {
                // Dolphin (Emotion) oscillates with momentum phase
                nodeVelocityMod = 1.0 + Math.sin(momentumPhase) * 0.5;
            }
            else if (animal === 'Deer') {
                // Deer (Sensing) subtle sensitivity to all factors
                nodeVelocityMod = 1.0 + (velocityFactor - 1.0) * 0.4 + (volumeFactor - 1.0) * 0.2;
            }
            else if (animal === 'Owl') {
                // Owl (Memory) inverts on momentum reversals
                nodeVelocityMod = 1.0 + Math.cos(momentumPhase) * 0.3;
            }
            else if (animal === 'Panda') {
                // Panda (Love) resonates with stable, high-volume conditions
                nodeVelocityMod = 1.0 + volumeFactor * 0.4 / Math.max(velocityFactor, 1.0);
            }
            else if (animal === 'CargoShip') {
                // CargoShip (Infrastructure) responds to large volume
                nodeVelocityMod = 1.0 + (volumeFactor - 1.0) * 0.6;
            }
            else if (animal === 'Clownfish') {
                // Clownfish (Symbiosis) sensitive to all micro-changes
                nodeVelocityMod = velocityFactor * spreadFactor * 0.7;
            }
            // Apply modulation to frequency
            frequency *= nodeVelocityMod;
            // Phase shift from momentum + spread dynamics
            var phase = momentumPhase * 0.2 + (spreadFactor - 1.0) * Math.PI * 0.1;
            // Each node contributes - amplitude scales with velocity
            var amplitude = Math.min(velocityFactor * volumeFactor, 2.0);
            sum += amplitude * Math.sin(2 * Math.PI * frequency * t + phase);
        }
        return sum;
    };
    /**
     * O(t) — OBSERVER
     * Your conscious focus, shaping the field via nonlinear integration
     */
    RealityField.prototype.computeObserver = function () {
        // Integrate recent field values over "thickness of Now"
        var nowWindow = Math.floor(1.0 / this.config.dt); // Last 1 second
        var recent = this.history.slice(-nowWindow);
        if (recent.length === 0)
            return 0;
        var integral = recent.reduce(function (sum, state) { return sum + state.Lambda; }, 0) / recent.length;
        // Observer coupling with nonlinear activation
        return this.config.alpha * Math.tanh(this.config.g * integral);
    };
    /**
     * E(t) — ECHO
     * Causal feedback from τ seconds in the past
     */
    RealityField.prototype.computeEcho = function () {
        var echoTime = this.t - this.config.tau;
        // Find the closest historical state to echoTime
        for (var i = this.history.length - 1; i >= 0; i--) {
            if (this.history[i].t <= echoTime) {
                return this.config.beta * this.history[i].Lambda;
            }
        }
        return 0; // No echo if history is too short
    };
    /**
     * Γ — COHERENCE
     * Measures field stability (low variance = high coherence)
     */
    RealityField.prototype.computeCoherence = function () {
        var window = Math.min(50, this.history.length);
        if (window < 2)
            return 0;
        var recent = this.history.slice(-window);
        var values = recent.map(function (s) { return s.Lambda; });
        var mean = values.reduce(function (a, b) { return a + b; }, 0) / values.length;
        var variance = values.reduce(function (sum, val) { return sum + Math.pow(val - mean, 2); }, 0) / values.length;
        var std = Math.sqrt(variance);
        var meanAbs = values.reduce(function (sum, val) { return sum + Math.abs(val); }, 0) / values.length;
        return 1 - std / (meanAbs + 1e-6);
    };
    /**
     * DOMINANT NODE
     * Find which Auris node is most resonant with current Λ(t)
     */
    RealityField.prototype.findDominantNode = function (Lambda) {
        var maxResonance = 0;
        var dominant = 'Panda'; // Default to empathy core
        for (var _i = 0, _a = Object.keys(aurisSymbolicTaxonomy_1.AURIS_TAXONOMY); _i < _a.length; _i++) {
            var animal = _a[_i];
            var node = aurisSymbolicTaxonomy_1.AURIS_TAXONOMY[animal];
            var resonance = Math.abs(Math.sin(2 * Math.PI * node.frequency * Lambda));
            if (resonance > maxResonance) {
                maxResonance = resonance;
                dominant = animal;
            }
        }
        return dominant;
    };
    /**
     * STEP — Advance the field by one timestep
     * 🌈 NOW TASTING THE RAINBOW - WebSocket market streams 🌈
     */
    RealityField.prototype.step = function (marketState) {
        // Compute the three components (substrate now uses marketState for stream injection)
        var substrate = this.computeSubstrate(this.t, marketState);
        var observer = this.computeObserver();
        var echo = this.computeEcho();
        // Master Equation (now market-responsive via WebSocket)
        var Lambda = substrate + observer + echo;
        // Coherence
        var coherence = this.computeCoherence();
        // Dominant node
        var dominantNode = this.findDominantNode(Lambda);
        // Create state (include MarketSnapshot if provided)
        var state = {
            t: this.t,
            Lambda: Lambda,
            substrate: substrate,
            observer: observer,
            echo: echo,
            coherence: coherence,
            dominantNode: dominantNode,
            marketSnapshot: typeof marketState === 'object' ? marketState : undefined,
        };
        // Store in history
        this.history.push(state);
        if (this.history.length > this.config.maxHistory) {
            this.history.shift();
        }
        // Advance time
        this.t += this.config.dt;
        return state;
    };
    /**
     * GET STATE
     */
    RealityField.prototype.getState = function () {
        return this.history[this.history.length - 1] || null;
    };
    /**
     * GET HISTORY
     */
    RealityField.prototype.getHistory = function () {
        return __spreadArray([], this.history, true);
    };
    /**
     * RESET
     */
    RealityField.prototype.reset = function () {
        this.t = 0;
        this.history = [];
    };
    return RealityField;
}());
exports.RealityField = RealityField;
/**
 * LIGHTHOUSE CONSENSUS
 *
 * 9-node consensus protocol — requires 6/9 agreement to trigger trade
 */
var lighthouseConsensus = function (Lambda, threshold) {
    if (threshold === void 0) { threshold = 0.7; }
    var votes = 0;
    for (var _i = 0, _a = Object.keys(aurisSymbolicTaxonomy_1.AURIS_TAXONOMY); _i < _a.length; _i++) {
        var animal = _a[_i];
        var node = aurisSymbolicTaxonomy_1.AURIS_TAXONOMY[animal];
        // Each node votes based on resonance with field
        var resonance = Math.abs(Math.sin(2 * Math.PI * node.frequency * Lambda));
        if (resonance > threshold) {
            votes++;
        }
    }
    // 6/9 consensus required
    return votes >= 6;
};
exports.lighthouseConsensus = lighthouseConsensus;
/**
 * MASTER EQUATION WISDOM
 */
exports.masterEquationWisdom = "\n\u2554\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2557\n\u2551              AUREON MASTER EQUATION \u2014 \u039B(t)                 \u2551\n\u255A\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u255D\n\n\u039B(t) = S(t) + O(t) + E(t)\n\nS(t) = Substrate \u2014 The 9-node Auris waveform\n       Sum of all animal frequencies in superposition\n\nO(t) = Observer \u2014 Your conscious focus\n       \u03B1\u00B7tanh(g\u00B7\u222B\u039B) \u2014 Nonlinear integration over Now\n\nE(t) = Echo \u2014 Causal feedback from the past\n       \u03B2\u00B7\u039B(t-\u03C4) \u2014 Memory from \u03C4 seconds ago\n\nThis is not theory.\nThis is the field equation.\nIt runs in the swarm.\nIt decides trades.\nIt makes money.\n\nThe animals are not forgotten.\nThey are the operators.\nThey are the field.\nThey are you.\n";
