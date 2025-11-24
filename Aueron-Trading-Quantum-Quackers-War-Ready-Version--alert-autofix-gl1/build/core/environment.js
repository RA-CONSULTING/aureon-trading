"use strict";
/**
 * Environment configuration for AUREON trading system
 * Supports both development and production modes with proper isolation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.envConfig = void 0;
exports.log = log;
var dotenv_1 = require("dotenv");
// Load .env file if it exists
dotenv_1.default.config();
function getEnvironmentConfig() {
    var mode = (process.env.NODE_ENV || 'development');
    var binanceApiKey = process.env.BINANCE_API_KEY || null;
    var binanceApiSecret = process.env.BINANCE_API_SECRET || null;
    var binanceTestnet = process.env.BINANCE_TESTNET !== 'false'; // default to testnet for safety
    var loggingLevel = (process.env.LOG_LEVEL || 'info');
    var verboseLogging = process.env.VERBOSE_LOGGING === 'true';
    var paperMode = process.env.PAPER_MODE !== 'false'; // default to paper mode
    var maxOrderSize = Number(process.env.MAX_ORDER_SIZE || 10000);
    var maxDailyTrades = Number(process.env.MAX_DAILY_TRADES || 1000);
    var riskLimitPercent = Number(process.env.RISK_LIMIT_PERCENT || 2);
    return {
        mode: mode,
        binance: {
            apiKey: binanceApiKey,
            apiSecret: binanceApiSecret,
            testnet: binanceTestnet,
        },
        logging: {
            level: loggingLevel,
            verbose: verboseLogging,
        },
        trading: {
            paperMode: paperMode,
            maxOrderSize: maxOrderSize,
            maxDailyTrades: maxDailyTrades,
            riskLimitPercent: riskLimitPercent,
        },
    };
}
exports.envConfig = getEnvironmentConfig();
// Logging utility
function log(level, message, data) {
    var levelPriority = { debug: 0, info: 1, warn: 2, error: 3 };
    if (levelPriority[level] >= levelPriority[exports.envConfig.logging.level]) {
        var timestamp = new Date().toISOString();
        var prefix = "[".concat(timestamp, "] [").concat(level.toUpperCase(), "]");
        console.log(prefix, message, data ? JSON.stringify(data, null, 2) : '');
    }
}
