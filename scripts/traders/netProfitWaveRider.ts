/**
 * 🌊 NET PROFIT WAVE RIDER - LIVE MARKETS 🌊
 * 
 * A→Z  ↔  Z→A  "They Can't Stop Them All!"
 * 
 *   ╔═══════════════════════════════════════════════════════════════════════════╗
 *   ║   NET PROFIT MODE - ALL FEES INCLUDED                                    ║
 *   ║                                                                           ║
 *   ║   • Trading fees (maker/taker)                                           ║
 *   ║   • Spread costs                                                          ║
 *   ║   • Overnight financing (for CFDs)                                        ║
 *   ║   • Withdrawal fees                                                       ║
 *   ║   • Only show TRUE net profit after ALL costs                            ║
 *   ║                                                                           ║
 *   ╚═══════════════════════════════════════════════════════════════════════════╝
 * 
 * Author: Gary Leckey - R&A Consulting
 */

import * as dotenv from 'dotenv';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

dotenv.config({ path: path.join(__dirname, '..', '.env') });

// ═══════════════════════════════════════════════════════════════════════════
// REALISTIC FEE STRUCTURES BY BROKER
// ═══════════════════════════════════════════════════════════════════════════

interface BrokerFees {
  name: string;
  makerFee: number;      // % per trade (maker)
  takerFee: number;      // % per trade (taker)
  spreadMarkup: number;  // Additional spread % on top of raw
  overnightRate: number; // Daily financing rate for CFDs (% per day)
  minFee: number;        // Minimum fee in £
  withdrawFee: number;   // Flat withdrawal fee £
  taxFree: boolean;      // UK spread betting = tax free
  disabled?: boolean;    // Skip broker for small accounts
}

const BROKER_FEES: Record<string, BrokerFees> = {
  // CRYPTO EXCHANGES
  'Binance': {
    name: 'Binance',
    makerFee: 0.10,      // 0.10%
    takerFee: 0.10,      // 0.10%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 0,       // Varies by crypto
    taxFree: false
  },
  'Kraken': {
    name: 'Kraken',
    makerFee: 0.16,      // 0.16%
    takerFee: 0.26,      // 0.26%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 1.50,
    taxFree: false
  },
  'Coinbase': {
    name: 'Coinbase',
    makerFee: 0.40,      // 0.40% (Advanced Trade)
    takerFee: 0.60,      // 0.60%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  'Bitstamp': {
    name: 'Bitstamp',
    makerFee: 0.30,      // 0.30%
    takerFee: 0.40,      // 0.40%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  'OKX': {
    name: 'OKX',
    makerFee: 0.08,      // 0.08%
    takerFee: 0.10,      // 0.10%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  'Gemini': {
    name: 'Gemini',
    makerFee: 0.20,      // 0.20%
    takerFee: 0.40,      // 0.40%
    spreadMarkup: 0,
    overnightRate: 0,
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  
  // FOREX BROKERS
  'OANDA': {
    name: 'OANDA',
    makerFee: 0,
    takerFee: 0,
    spreadMarkup: 0.0001, // ~1 pip markup
    overnightRate: 0.008, // ~3% annual / 365
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  'FXCM': {
    name: 'FXCM',
    makerFee: 0,
    takerFee: 0,
    spreadMarkup: 0.00015,
    overnightRate: 0.008,
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  
  // UK SPREAD BETTING (TAX FREE!)
  'IG': {
    name: 'IG',
    makerFee: 0,
    takerFee: 0,
    spreadMarkup: 0.0003, // Spread betting has wider spreads
    overnightRate: 0.0082, // ~3% annual
    minFee: 0,
    withdrawFee: 0,
    taxFree: true         // 🎁 NO TAX ON PROFITS!
  },
  'CMC': {
    name: 'CMC',
    makerFee: 0,
    takerFee: 0,
    spreadMarkup: 0.0003,
    overnightRate: 0.0082,
    minFee: 0,
    withdrawFee: 0,
    taxFree: true         // 🎁 NO TAX ON PROFITS!
  },
  
  // CFD BROKERS
  'Capital': {
    name: 'Capital',
    makerFee: 0,
    takerFee: 0,
    spreadMarkup: 0.0002,
    overnightRate: 0.0055, // ~2% annual
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  },
  'Saxo': {
    name: 'Saxo',
    makerFee: 0.05,       // Commission on stocks
    takerFee: 0.05,
    spreadMarkup: 0.0001,
    overnightRate: 0.0082,
    minFee: 0,            // DISABLED - min fee too high for £20 account
    withdrawFee: 0,
    taxFree: false,
    disabled: true        // Skip this broker for small accounts
  },
  'IB': {
    name: 'IB',
    makerFee: 0.05,       // Very low commissions
    takerFee: 0.05,
    spreadMarkup: 0,
    overnightRate: 0.005,
    minFee: 0,            // DISABLED - min fee too high for £20 account  
    withdrawFee: 0,
    taxFree: false,
    disabled: true        // Skip this broker for small accounts
  },
  'Alpaca': {
    name: 'Alpaca',
    makerFee: 0,          // Commission-free stocks
    takerFee: 0,
    spreadMarkup: 0,
    overnightRate: 0,     // No overnight for stocks
    minFee: 0,
    withdrawFee: 0,
    taxFree: false
  }
};

// ═══════════════════════════════════════════════════════════════════════════
// Configuration - ADJUSTED FOR NET PROFIT
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  BALANCE_PER_BROKER: 20,
  POSITION_SIZE_PCT: 0.15,  // 15% per trade = £3 per position
  
  // ADJUSTED TARGETS TO COVER FEES
  // Most brokers charge 0.1-0.6% per trade (round trip = 0.2-1.2%)
  // We need TP > fees to be net positive
  STOP_LOSS_PCT: 0.025,     // 2.5% stop loss
  TAKE_PROFIT_PCT: 0.05,    // 5% take profit (covers fees + profit)
  
  MAX_POSITIONS_PER_BROKER: 4,
  SCAN_INTERVAL_MS: 5000,
  
  // Only enter on strong momentum to ensure higher win rate
  MIN_MOMENTUM_PCT: 2.5,    // Only enter if 24h change > 2.5%
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface LivePrice {
  symbol: string;
  bid: number;
  ask: number;
  mid: number;
  spread: number;
  change24h?: number;
}

interface Position {
  broker: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  grossPnl: number;      // Before fees
  fees: number;          // Total fees
  netPnl: number;        // After fees
  pnlPercent: number;
  taxFree: boolean;
  isScout: boolean;
  entryTime: Date;
}

interface BrokerState {
  name: string;
  emoji: string;
  balance: number;
  positions: number;
  wins: number;
  losses: number;
  grossPnl: number;
  totalFees: number;
  netPnl: number;
  taxFree: boolean;
  hasScout: boolean;
  scoutDeployed: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// Real Price Feeds
// ═══════════════════════════════════════════════════════════════════════════

async function fetchBinancePrices(): Promise<LivePrice[]> {
  const symbols = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'DOGEUSDT', 'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT',
    'MATICUSDT', 'LTCUSDT', 'NEARUSDT', 'UNIUSDT', 'AAVEUSDT',
    'APTUSDT', 'ARBUSDT', 'OPUSDT', 'ATOMUSDT', 'SHIBUSDT'
  ];
  
  try {
    const response = await fetch('https://api.binance.com/api/v3/ticker/24hr');
    if (!response.ok) return [];
    
    const data = await response.json();
    const prices: LivePrice[] = [];
    
    for (const sym of symbols) {
      const ticker = data.find((t: any) => t.symbol === sym);
      if (ticker) {
        const bid = parseFloat(ticker.bidPrice);
        const ask = parseFloat(ticker.askPrice);
        prices.push({
          symbol: sym,
          bid,
          ask,
          mid: (bid + ask) / 2,
          spread: ask - bid,
          change24h: parseFloat(ticker.priceChangePercent)
        });
      }
    }
    return prices;
  } catch { return []; }
}

async function fetchKrakenPrices(): Promise<LivePrice[]> {
  const pairs = 'XXBTZGBP,XETHZGBP,XXBTZUSD,XETHZUSD,SOLUSD,XRPUSD,ADAUSD,DOTUSD,LINKUSD,ATOMUSD';
  
  try {
    const response = await fetch(`https://api.kraken.com/0/public/Ticker?pair=${pairs}`);
    if (!response.ok) return [];
    
    const data = await response.json();
    if (data.error?.length > 0) return [];
    
    const prices: LivePrice[] = [];
    for (const [key, ticker] of Object.entries(data.result) as any) {
      const bid = parseFloat(ticker.b[0]);
      const ask = parseFloat(ticker.a[0]);
      const open = parseFloat(ticker.o);
      const last = parseFloat(ticker.c[0]);
      prices.push({
        symbol: key,
        bid,
        ask,
        mid: (bid + ask) / 2,
        spread: ask - bid,
        change24h: ((last - open) / open) * 100
      });
    }
    return prices;
  } catch { return []; }
}

async function fetchOKXPrices(): Promise<LivePrice[]> {
  const symbols = [
    'BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'XRP-USDT', 'DOGE-USDT',
    'ADA-USDT', 'DOT-USDT', 'AVAX-USDT', 'LINK-USDT', 'NEAR-USDT',
    'ATOM-USDT', 'UNI-USDT', 'AAVE-USDT', 'LTC-USDT', 'ARB-USDT'
  ];
  
  try {
    const response = await fetch('https://www.okx.com/api/v5/market/tickers?instType=SPOT');
    if (!response.ok) return [];
    
    const data = await response.json();
    if (!data.data) return [];
    
    const prices: LivePrice[] = [];
    for (const sym of symbols) {
      const ticker = data.data.find((t: any) => t.instId === sym);
      if (ticker) {
        const bid = parseFloat(ticker.bidPx);
        const ask = parseFloat(ticker.askPx);
        const open = parseFloat(ticker.open24h);
        const last = parseFloat(ticker.last);
        prices.push({
          symbol: sym,
          bid,
          ask,
          mid: (bid + ask) / 2,
          spread: ask - bid,
          change24h: ((last - open) / open) * 100
        });
      }
    }
    return prices;
  } catch { return []; }
}

async function fetchCoinbasePrices(): Promise<LivePrice[]> {
  const symbols = ['BTC-GBP', 'ETH-GBP', 'SOL-GBP', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'ADA-USD'];
  const prices: LivePrice[] = [];
  
  const fetches = symbols.map(async sym => {
    try {
      const response = await fetch(`https://api.exchange.coinbase.com/products/${sym}/ticker`);
      if (response.ok) {
        const data = await response.json();
        const bid = parseFloat(data.bid);
        const ask = parseFloat(data.ask);
        return { symbol: sym, bid, ask, mid: (bid + ask) / 2, spread: ask - bid };
      }
    } catch {}
    return null;
  });
  
  const results = await Promise.all(fetches);
  return results.filter(p => p !== null) as LivePrice[];
}

async function fetchBitstampPrices(): Promise<LivePrice[]> {
  const symbols = ['btcgbp', 'ethgbp', 'btcusd', 'ethusd', 'xrpusd', 'ltcusd', 'solusd'];
  
  const fetches = symbols.map(async sym => {
    try {
      const response = await fetch(`https://www.bitstamp.net/api/v2/ticker/${sym}/`);
      if (response.ok) {
        const data = await response.json();
        const bid = parseFloat(data.bid);
        const ask = parseFloat(data.ask);
        const open = parseFloat(data.open);
        const last = parseFloat(data.last);
        return {
          symbol: sym.toUpperCase(),
          bid,
          ask,
          mid: (bid + ask) / 2,
          spread: ask - bid,
          change24h: ((last - open) / open) * 100
        };
      }
    } catch {}
    return null;
  });
  
  const results = await Promise.all(fetches);
  return results.filter(p => p !== null) as LivePrice[];
}

async function fetchForexPrices(): Promise<LivePrice[]> {
  try {
    const response = await fetch('https://api.exchangerate-api.com/v4/latest/USD');
    if (!response.ok) return [];
    
    const data = await response.json();
    const prices: LivePrice[] = [];
    
    const pairs = [
      { base: 'EUR', symbol: 'EUR/USD' },
      { base: 'GBP', symbol: 'GBP/USD' },
      { base: 'JPY', symbol: 'USD/JPY' },
      { base: 'CHF', symbol: 'USD/CHF' },
      { base: 'AUD', symbol: 'AUD/USD' },
      { base: 'CAD', symbol: 'USD/CAD' },
    ];
    
    for (const pair of pairs) {
      const rate = data.rates[pair.base];
      if (rate) {
        let mid: number;
        if (pair.symbol.startsWith('USD/')) {
          mid = rate;
        } else {
          mid = 1 / rate;
        }
        const spread = mid * 0.0002;
        prices.push({
          symbol: pair.symbol,
          bid: mid - spread / 2,
          ask: mid + spread / 2,
          mid,
          spread
        });
      }
    }
    return prices;
  } catch { return []; }
}

// ═══════════════════════════════════════════════════════════════════════════
// Fee Calculator
// ═══════════════════════════════════════════════════════════════════════════

function calculateFees(broker: string, tradeValue: number, holdingDays: number = 0): number {
  const fees = BROKER_FEES[broker];
  if (!fees) return 0;
  
  // Entry + Exit fees (round trip)
  const entryFee = Math.max(tradeValue * (fees.takerFee / 100), fees.minFee);
  const exitFee = Math.max(tradeValue * (fees.takerFee / 100), fees.minFee);
  
  // Spread cost (built into entry)
  const spreadCost = tradeValue * fees.spreadMarkup;
  
  // Overnight financing (CFDs/Forex)
  const overnightCost = tradeValue * fees.overnightRate * holdingDays;
  
  return entryFee + exitFee + spreadCost + overnightCost;
}

function getBreakevenPercent(broker: string): number {
  const fees = BROKER_FEES[broker];
  if (!fees) return 0.5; // Default 0.5%
  
  // Round trip = 2x taker fee + spread
  return (fees.takerFee * 2) + (fees.spreadMarkup * 100);
}

// ═══════════════════════════════════════════════════════════════════════════
// Net Profit Wave Rider
// ═══════════════════════════════════════════════════════════════════════════

class NetProfitWaveRider {
  private positions: Map<string, Position> = new Map();
  private brokers: Map<string, BrokerState> = new Map();
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private scans = 0;
  private startTime = new Date();
  private totalGrossPnL = 0;
  private totalFees = 0;
  private totalNetPnL = 0;
  private wins = 0;
  private losses = 0;

  constructor() {
    this.initBrokers();
  }

  private initBrokers() {
    const brokerList = [
      { name: 'Binance', emoji: '🪙' },
      { name: 'Kraken', emoji: '🦑' },
      { name: 'Coinbase', emoji: '🟠' },
      { name: 'Bitstamp', emoji: '💎' },
      { name: 'OKX', emoji: '⭕' },
      { name: 'OANDA', emoji: '💱' },
      { name: 'FXCM', emoji: '💹' },
      { name: 'IG', emoji: '📈' },
      { name: 'CMC', emoji: '📉' },
      { name: 'Capital', emoji: '📊' },
      { name: 'Saxo', emoji: '🏦' },
      { name: 'IB', emoji: '🏛️' },
      { name: 'Alpaca', emoji: '🦙' },
      { name: 'Gemini', emoji: '💠' },
    ];

    for (const b of brokerList) {
      const fees = BROKER_FEES[b.name];
      this.brokers.set(b.name, {
        name: b.name,
        emoji: b.emoji,
        balance: CONFIG.BALANCE_PER_BROKER,
        positions: 0,
        wins: 0,
        losses: 0,
        grossPnl: 0,
        totalFees: 0,
        netPnl: 0,
        taxFree: fees?.taxFree || false,
        hasScout: false,
        scoutDeployed: false
      });
    }
  }

  async start(): Promise<void> {
    this.printHeader();
    
    console.log('\n  📡 Connecting to live markets...\n');
    console.log('  💰 FEE STRUCTURE LOADED:');
    console.log('  ────────────────────────────────────────────────────────────────────────────────');
    
    for (const [name, fees] of Object.entries(BROKER_FEES)) {
      const breakeven = getBreakevenPercent(name);
      const taxLabel = fees.taxFree ? ' 🎁TAX FREE' : '';
      console.log(`     ${name.padEnd(10)} │ Fee: ${(fees.takerFee * 2).toFixed(2)}% round-trip │ Breakeven: ${breakeven.toFixed(2)}%${taxLabel}`);
    }
    
    console.log('  ────────────────────────────────────────────────────────────────────────────────');
    console.log(`  📊 Target TP: ${CONFIG.TAKE_PROFIT_PCT * 100}% │ SL: ${CONFIG.STOP_LOSS_PCT * 100}% │ Min Momentum: ${CONFIG.MIN_MOMENTUM_PCT}%`);
    console.log('  ────────────────────────────────────────────────────────────────────────────────\n');
    
    while (true) {
      this.scans++;
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      await this.executeScan();
      this.displayStatus();
      
      await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL_MS));
    }
  }

  private async executeScan(): Promise<void> {
    const [binance, kraken, okx, coinbase, bitstamp, forex] = await Promise.all([
      fetchBinancePrices(),
      fetchKrakenPrices(),
      fetchOKXPrices(),
      fetchCoinbasePrices(),
      fetchBitstampPrices(),
      fetchForexPrices()
    ]);

    const sortFn = (a: LivePrice, b: LivePrice) => {
      const cmp = a.symbol.localeCompare(b.symbol);
      return this.scanDirection === 'A→Z' ? cmp : -cmp;
    };

    this.processPrices('Binance', binance.sort(sortFn));
    this.processPrices('Kraken', kraken.sort(sortFn));
    this.processPrices('OKX', okx.sort(sortFn));
    this.processPrices('Coinbase', coinbase.sort(sortFn));
    this.processPrices('Bitstamp', bitstamp.sort(sortFn));
    
    const sortedForex = forex.sort(sortFn);
    this.processPrices('OANDA', sortedForex);
    this.processPrices('FXCM', sortedForex);
    this.processPrices('IG', sortedForex);
    this.processPrices('CMC', sortedForex);
    this.processPrices('Saxo', sortedForex);
    this.processPrices('Capital', sortedForex);
    this.processPrices('IB', sortedForex);
  }

  private processPrices(broker: string, prices: LivePrice[]): void {
    const brokerState = this.brokers.get(broker);
    if (!brokerState || prices.length === 0) return;
    
    // Skip disabled brokers (high min fees for small accounts)
    const fees = BROKER_FEES[broker];
    if (fees?.disabled) return;

    // Update existing positions
    for (const price of prices) {
      const key = `${broker}:${price.symbol}`;
      if (this.positions.has(key)) {
        this.updatePosition(key, price.mid);
      }
    }
    
    // Deploy scout if none exists
    if (!brokerState.scoutDeployed && prices.length > 0) {
      // Find best momentum opportunity
      const bestMomentum = prices
        .filter(p => p.change24h !== undefined && Math.abs(p.change24h) >= CONFIG.MIN_MOMENTUM_PCT)
        .sort((a, b) => Math.abs(b.change24h!) - Math.abs(a.change24h!))[0];
      
      if (bestMomentum) {
        this.deployScout(broker, bestMomentum);
      } else if (prices[0]) {
        // Fall back to first in A→Z/Z→A order
        this.deployScout(broker, prices[0]);
      }
    }
    
    // Additional momentum entries
    for (const price of prices) {
      const key = `${broker}:${price.symbol}`;
      if (this.positions.has(key)) continue;
      if (brokerState.positions >= CONFIG.MAX_POSITIONS_PER_BROKER) break;
      
      if (price.change24h !== undefined && Math.abs(price.change24h) >= CONFIG.MIN_MOMENTUM_PCT) {
        if (price.change24h > CONFIG.MIN_MOMENTUM_PCT) {
          this.openPosition(broker, price, 'LONG', `📈+${price.change24h.toFixed(1)}%`, false);
        } else if (price.change24h < -CONFIG.MIN_MOMENTUM_PCT) {
          this.openPosition(broker, price, 'SHORT', `📉${price.change24h.toFixed(1)}%`, false);
        }
      }
    }
  }

  private deployScout(broker: string, price: LivePrice): void {
    const brokerState = this.brokers.get(broker);
    if (!brokerState) return;
    
    let direction: 'LONG' | 'SHORT';
    if (price.change24h !== undefined) {
      direction = price.change24h >= 0 ? 'LONG' : 'SHORT';
    } else {
      direction = Math.random() > 0.5 ? 'LONG' : 'SHORT';
    }
    
    const key = `${broker}:${price.symbol}`;
    const entryPrice = direction === 'LONG' ? price.ask : price.bid;
    const tradeValue = brokerState.balance * CONFIG.POSITION_SIZE_PCT;
    const size = tradeValue / entryPrice;
    
    // Calculate entry fees immediately
    const fees = BROKER_FEES[broker];
    const entryFee = fees ? Math.max(tradeValue * (fees.takerFee / 100), fees.minFee) : 0;
    const spreadCost = fees ? tradeValue * fees.spreadMarkup : 0;
    
    this.positions.set(key, {
      broker,
      symbol: price.symbol,
      direction,
      size,
      entryPrice,
      currentPrice: price.mid,
      grossPnl: 0,
      fees: entryFee + spreadCost,
      netPnl: -(entryFee + spreadCost), // Start negative due to entry costs
      pnlPercent: 0,
      taxFree: brokerState.taxFree,
      isScout: true,
      entryTime: new Date()
    });
    
    brokerState.positions++;
    brokerState.scoutDeployed = true;
    brokerState.hasScout = true;
    
    const dir = this.scanDirection;
    const dirEmoji = direction === 'LONG' ? '⬆️' : '⬇️';
    const taxLabel = brokerState.taxFree ? ' 🎁TAX FREE' : '';
    const priceStr = price.mid < 10 ? price.mid.toFixed(5) : price.mid.toFixed(2);
    const feeStr = (entryFee + spreadCost).toFixed(4);
    console.log(`  ${brokerState.emoji} [${dir}] 🔭 SCOUT ${dirEmoji}: ${price.symbol} @ ${priceStr} (fee: £${feeStr})${taxLabel}`);
  }

  private openPosition(broker: string, price: LivePrice, direction: 'LONG' | 'SHORT', reason: string, isScout: boolean): void {
    const brokerState = this.brokers.get(broker);
    if (!brokerState) return;
    
    const key = `${broker}:${price.symbol}`;
    const entryPrice = direction === 'LONG' ? price.ask : price.bid;
    const tradeValue = brokerState.balance * CONFIG.POSITION_SIZE_PCT;
    const size = tradeValue / entryPrice;
    
    const fees = BROKER_FEES[broker];
    const entryFee = fees ? Math.max(tradeValue * (fees.takerFee / 100), fees.minFee) : 0;
    const spreadCost = fees ? tradeValue * fees.spreadMarkup : 0;
    
    this.positions.set(key, {
      broker,
      symbol: price.symbol,
      direction,
      size,
      entryPrice,
      currentPrice: price.mid,
      grossPnl: 0,
      fees: entryFee + spreadCost,
      netPnl: -(entryFee + spreadCost),
      pnlPercent: 0,
      taxFree: brokerState.taxFree,
      isScout,
      entryTime: new Date()
    });
    
    brokerState.positions++;
    
    const dir = this.scanDirection;
    const dirEmoji = direction === 'LONG' ? '⬆️' : '⬇️';
    const taxLabel = brokerState.taxFree ? ' 🎁' : '';
    const priceStr = price.mid < 10 ? price.mid.toFixed(5) : price.mid.toFixed(2);
    console.log(`  ${brokerState.emoji} [${dir}] ⚡ ${dirEmoji} ${price.symbol} @ ${priceStr} (${reason})${taxLabel}`);
  }

  private updatePosition(key: string, currentPrice: number): void {
    const pos = this.positions.get(key);
    if (!pos) return;
    
    const brokerState = this.brokers.get(pos.broker);
    if (!brokerState) return;
    
    pos.currentPrice = currentPrice;
    const priceDiff = currentPrice - pos.entryPrice;
    const multiplier = pos.direction === 'LONG' ? 1 : -1;
    pos.grossPnl = priceDiff * pos.size * multiplier;
    pos.pnlPercent = (priceDiff / pos.entryPrice) * 100 * multiplier;
    
    // Calculate current fees (including potential exit fee)
    const tradeValue = pos.size * pos.entryPrice;
    const fees = BROKER_FEES[pos.broker];
    const holdingDays = (Date.now() - pos.entryTime.getTime()) / (1000 * 60 * 60 * 24);
    pos.fees = calculateFees(pos.broker, tradeValue, holdingDays);
    pos.netPnl = pos.grossPnl - pos.fees;
    
    // Check stop loss (on NET basis)
    const netPnlPercent = (pos.netPnl / tradeValue) * 100;
    if (netPnlPercent <= -CONFIG.STOP_LOSS_PCT * 100) {
      this.closePosition(key, 'STOP');
    }
    // Check take profit (on NET basis)
    else if (netPnlPercent >= CONFIG.TAKE_PROFIT_PCT * 100) {
      this.closePosition(key, 'PROFIT');
    }
  }

  private closePosition(key: string, reason: 'STOP' | 'PROFIT'): void {
    const pos = this.positions.get(key);
    if (!pos) return;
    
    const brokerState = this.brokers.get(pos.broker);
    if (!brokerState) return;
    
    // Final fee calculation
    const tradeValue = pos.size * pos.entryPrice;
    const holdingDays = (Date.now() - pos.entryTime.getTime()) / (1000 * 60 * 60 * 24);
    const totalFees = calculateFees(pos.broker, tradeValue, holdingDays);
    const netPnl = pos.grossPnl - totalFees;
    
    brokerState.balance += netPnl;
    brokerState.grossPnl += pos.grossPnl;
    brokerState.totalFees += totalFees;
    brokerState.netPnl += netPnl;
    
    this.totalGrossPnL += pos.grossPnl;
    this.totalFees += totalFees;
    this.totalNetPnL += netPnl;
    
    if (netPnl >= 0) {
      brokerState.wins++;
      this.wins++;
    } else {
      brokerState.losses++;
      this.losses++;
    }
    
    brokerState.positions--;
    if (pos.isScout) brokerState.hasScout = false;
    
    const emoji = netPnl >= 0 ? '✅' : '❌';
    const scoutLabel = pos.isScout ? ' 🔭' : '';
    const taxLabel = pos.taxFree ? ' 🎁TAX FREE!' : '';
    const grossStr = pos.grossPnl >= 0 ? `+£${pos.grossPnl.toFixed(4)}` : `-£${Math.abs(pos.grossPnl).toFixed(4)}`;
    const netStr = netPnl >= 0 ? `+£${netPnl.toFixed(4)}` : `-£${Math.abs(netPnl).toFixed(4)}`;
    console.log(`  ${brokerState.emoji} ${emoji} ${reason}${scoutLabel}: ${pos.symbol} | Gross: ${grossStr} | Fees: £${totalFees.toFixed(4)} | NET: ${netStr}${taxLabel}`);
    
    this.positions.delete(key);
  }

  private printHeader(): void {
    console.log('\n');
    console.log('  ╔═══════════════════════════════════════════════════════════════════════════════╗');
    console.log('  ║                                                                               ║');
    console.log('  ║   💰 NET PROFIT WAVE RIDER - LIVE MARKETS 💰                                  ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   A→Z  ↔  Z→A  "Profit AFTER All Fees!"                                      ║');
    console.log('  ║                                                                               ║');
    console.log('  ╠═══════════════════════════════════════════════════════════════════════════════╣');
    console.log('  ║                                                                               ║');
    console.log('  ║   FEES INCLUDED:                                                              ║');
    console.log('  ║   • Trading fees (maker/taker)                                               ║');
    console.log('  ║   • Spread costs                                                              ║');
    console.log('  ║   • Overnight financing                                                       ║');
    console.log('  ║   • Minimum fees                                                              ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   🎁 TAX FREE (Spread Betting): 📈 IG  📉 CMC                                 ║');
    console.log('  ║                                                                               ║');
    console.log('  ╚═══════════════════════════════════════════════════════════════════════════════╝');
  }

  private displayStatus(): void {
    const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    let totalBalance = 0;
    let totalPositions = 0;
    let scoutsActive = 0;
    let taxFreeNetPnL = 0;
    
    const lines: string[] = [];
    
    for (const [name, state] of this.brokers) {
      totalBalance += state.balance;
      totalPositions += state.positions;
      if (state.hasScout) scoutsActive++;
      if (state.taxFree) taxFreeNetPnL += state.netPnl;
      
      const hitRate = state.wins + state.losses > 0
        ? ((state.wins / (state.wins + state.losses)) * 100).toFixed(0)
        : '-';
      
      const netStr = state.netPnl >= 0 ? `+£${state.netPnl.toFixed(2)}` : `-£${Math.abs(state.netPnl).toFixed(2)}`;
      const netEmoji = state.netPnl >= 0 ? '🟢' : '🔴';
      const taxLabel = state.taxFree ? '🎁' : '  ';
      const scoutLabel = state.hasScout ? '🔭' : '  ';
      const feesStr = state.totalFees > 0 ? `£${state.totalFees.toFixed(2)}` : '£0.00';
      
      lines.push(
        `  │ ${state.emoji} ${state.name.padEnd(8)} │ £${state.balance.toFixed(2).padStart(6)} │ ${state.positions}/${CONFIG.MAX_POSITIONS_PER_BROKER} │ ${feesStr.padStart(6)} │ ${netEmoji} ${netStr.padStart(8)} │ ${taxLabel} │`
      );
    }
    
    const totalHitRate = this.wins + this.losses > 0
      ? ((this.wins / (this.wins + this.losses)) * 100).toFixed(1)
      : '0.0';
    
    const totalNetStr = this.totalNetPnL >= 0 ? `+£${this.totalNetPnL.toFixed(2)}` : `-£${Math.abs(this.totalNetPnL).toFixed(2)}`;
    const totalEmoji = this.totalNetPnL >= 0 ? '🟢' : '🔴';
    
    console.log('');
    console.log('  ┌──────────────────────────────────────────────────────────────────────────────────┐');
    console.log(`  │  SCAN #${this.scans.toString().padStart(5)} [${this.scanDirection}]  │  Time: ${minutes}m ${seconds}s  │  Positions: ${totalPositions}/${14 * CONFIG.MAX_POSITIONS_PER_BROKER}  │  🔭 Scouts: ${scoutsActive}  │`);
    console.log('  ├──────────────────────────────────────────────────────────────────────────────────┤');
    console.log('  │  Broker    │ Balance  │ Pos │  Fees  │  NET P&L   │ 🎁 │');
    console.log('  ├────────────┼──────────┼─────┼────────┼────────────┼────┤');
    
    for (const line of lines) {
      console.log(line);
    }
    
    console.log('  ├────────────┼──────────┼─────┼────────┼────────────┼────┤');
    console.log(`  │ 💰 TOTAL   │ £${totalBalance.toFixed(2).padStart(6)} │ ${totalPositions.toString().padStart(2)}  │ £${this.totalFees.toFixed(2).padStart(5)} │ ${totalEmoji} ${totalNetStr.padStart(8)} │    │`);
    console.log('  └──────────────────────────────────────────────────────────────────────────────────┘');
    
    // Summary
    console.log('');
    console.log(`  📊 PROFIT BREAKDOWN:`);
    const grossStr = this.totalGrossPnL >= 0 ? `+£${this.totalGrossPnL.toFixed(4)}` : `-£${Math.abs(this.totalGrossPnL).toFixed(4)}`;
    console.log(`     Gross P&L:  ${grossStr}`);
    console.log(`     Total Fees: -£${this.totalFees.toFixed(4)}`);
    console.log(`     ──────────────────────`);
    console.log(`     NET P&L:    ${totalNetStr} ${this.totalNetPnL >= 0 ? '✅ PROFITABLE' : '⚠️  IN DRAWDOWN'}`);
    
    if (taxFreeNetPnL !== 0) {
      const taxFreeStr = taxFreeNetPnL >= 0 ? `+£${taxFreeNetPnL.toFixed(4)}` : `-£${Math.abs(taxFreeNetPnL).toFixed(4)}`;
      console.log(`     🎁 Tax-Free (IG+CMC): ${taxFreeStr}`);
    }
    
    console.log(`     Win Rate: ${totalHitRate}% (${this.wins}W / ${this.losses}L)`);
    
    this.displayPositions();
  }

  private displayPositions(): void {
    const allPositions = Array.from(this.positions.values());
    
    if (allPositions.length === 0) {
      console.log('');
      console.log(`  🌊 [${this.scanDirection}] Looking for high-momentum opportunities (>${CONFIG.MIN_MOMENTUM_PCT}% 24h change)...`);
      console.log('');
      return;
    }
    
    allPositions.sort((a, b) => b.netPnl - a.netPnl);
    
    console.log('');
    console.log(`  🌊 Active Positions [${this.scanDirection}] (showing NET P&L after fees):`);
    console.log('');
    
    for (const pos of allPositions.slice(0, 14)) {
      const emoji = pos.netPnl >= 0 ? '🟢' : '🔴';
      const dir = pos.direction === 'LONG' ? '⬆' : '⬇';
      const brokerState = this.brokers.get(pos.broker);
      const brokerEmoji = brokerState?.emoji || '📈';
      const taxLabel = pos.taxFree ? ' 🎁' : '';
      const scoutLabel = pos.isScout ? ' 🔭' : '';
      
      const netStr = pos.netPnl >= 0 ? `+£${pos.netPnl.toFixed(4)}` : `-£${Math.abs(pos.netPnl).toFixed(4)}`;
      const feeStr = `fee:£${pos.fees.toFixed(3)}`;
      
      console.log(`     ${brokerEmoji} ${emoji} ${pos.symbol.padEnd(12)} ${dir} → NET: ${netStr} (${feeStr})${taxLabel}${scoutLabel}`);
    }
    
    if (allPositions.length > 14) {
      console.log(`     ... and ${allPositions.length - 14} more positions`);
    }
    
    console.log('');
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   💰 NET PROFIT WAVE RIDER 💰                                                 ║
  ║                                                                               ║
  ║   All fees and costs accounted for:                                          ║
  ║   • Maker/Taker fees (0.08% - 0.60%)                                         ║
  ║   • Spread costs                                                              ║
  ║   • Overnight financing (CFDs/Forex)                                          ║
  ║   • Minimum fees                                                              ║
  ║                                                                               ║
  ║   Strategy:                                                                   ║
  ║   • Only enter on strong momentum (>${CONFIG.MIN_MOMENTUM_PCT}% 24h change)                         ║
  ║   • TP: ${CONFIG.TAKE_PROFIT_PCT * 100}% (covers fees + profit)                                            ║
  ║   • SL: ${CONFIG.STOP_LOSS_PCT * 100}% (tight risk control)                                            ║
  ║   • A→Z ↔ Z→A wave direction                                                 ║
  ║                                                                               ║
  ║   🎁 TAX FREE profits on IG & CMC (UK Spread Betting)                        ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  const rider = new NetProfitWaveRider();
  
  process.on('SIGINT', () => {
    console.log('\n');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('  💰 Net Profit Wave Rider concludes...');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('');
    process.exit(0);
  });

  await rider.start();
}

main().catch(console.error);
