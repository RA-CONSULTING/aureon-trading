/**
 * 🌊 IMMEDIATE WAVE RIDER - LIVE MARKETS 🌊
 * 
 * A→Z  ↔  Z→A  "They Can't Stop Them All!"
 * 
 *   ╔═══════════════════════════════════════════════════════════════════════════╗
 *   ║   IMMEDIATE ENTRY MODE                                                    ║
 *   ║                                                                           ║
 *   ║   • Enter 1 position per broker IMMEDIATELY on first scan                ║
 *   ║   • Scout positions ride the wave from the start                         ║
 *   ║   • A→Z on odd cycles, Z→A on even cycles for new entries               ║
 *   ║   • "They can't stop them all!"                                          ║
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
// Configuration
// ═══════════════════════════════════════════════════════════════════════════

const CONFIG = {
  BALANCE_PER_BROKER: 20,
  POSITION_SIZE_PCT: 0.10, // 10% per trade = £2 per position
  STOP_LOSS_PCT: 0.02,     // 2% stop loss
  TAKE_PROFIT_PCT: 0.04,   // 4% take profit
  MAX_POSITIONS_PER_BROKER: 5,
  SCAN_INTERVAL_MS: 5000,  // 5 seconds
  SCOUT_ON_FIRST_SCAN: true, // Deploy scouts immediately
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
  pnl: number;
  pnlPercent: number;
  taxFree: boolean;
  isScout: boolean;
}

interface BrokerState {
  name: string;
  emoji: string;
  balance: number;
  positions: number;
  wins: number;
  losses: number;
  pnl: number;
  taxFree: boolean;
  hasScout: boolean;
  scoutDeployed: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// Real Price Feeds
// ═══════════════════════════════════════════════════════════════════════════

// BINANCE - 20 top pairs
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

// KRAKEN
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

// OKX
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

// COINBASE
async function fetchCoinbasePrices(): Promise<LivePrice[]> {
  const symbols = ['BTC-GBP', 'ETH-GBP', 'SOL-GBP', 'BTC-USD', 'ETH-USD', 'SOL-USD', 'DOGE-USD', 'ADA-USD'];
  const prices: LivePrice[] = [];
  
  // Fetch in parallel
  const fetches = symbols.map(async sym => {
    try {
      const response = await fetch(`https://api.exchange.coinbase.com/products/${sym}/ticker`);
      if (response.ok) {
        const data = await response.json();
        const bid = parseFloat(data.bid);
        const ask = parseFloat(data.ask);
        return {
          symbol: sym,
          bid,
          ask,
          mid: (bid + ask) / 2,
          spread: ask - bid
        };
      }
    } catch {}
    return null;
  });
  
  const results = await Promise.all(fetches);
  return results.filter(p => p !== null) as LivePrice[];
}

// BITSTAMP
async function fetchBitstampPrices(): Promise<LivePrice[]> {
  const symbols = ['btcgbp', 'ethgbp', 'btcusd', 'ethusd', 'xrpusd', 'ltcusd', 'solusd'];
  const prices: LivePrice[] = [];
  
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

// FOREX
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
      { base: 'NZD', symbol: 'NZD/USD' },
      { base: 'SGD', symbol: 'USD/SGD' },
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
// Immediate Wave Rider
// ═══════════════════════════════════════════════════════════════════════════

class ImmediateWaveRider {
  private positions: Map<string, Position> = new Map();
  private brokers: Map<string, BrokerState> = new Map();
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private scans = 0;
  private startTime = new Date();
  private totalPnL = 0;
  private wins = 0;
  private losses = 0;
  private priceHistory: Map<string, number[]> = new Map();

  constructor() {
    this.initBrokers();
  }

  private initBrokers() {
    const brokerList = [
      { name: 'Binance', emoji: '🪙', taxFree: false },
      { name: 'Kraken', emoji: '🦑', taxFree: false },
      { name: 'Coinbase', emoji: '🟠', taxFree: false },
      { name: 'Bitstamp', emoji: '💎', taxFree: false },
      { name: 'OKX', emoji: '⭕', taxFree: false },
      { name: 'OANDA', emoji: '💱', taxFree: false },
      { name: 'FXCM', emoji: '💹', taxFree: false },
      { name: 'IG', emoji: '📈', taxFree: true },
      { name: 'CMC', emoji: '📉', taxFree: true },
      { name: 'Capital', emoji: '📊', taxFree: false },
      { name: 'Saxo', emoji: '🏦', taxFree: false },
      { name: 'IB', emoji: '🏛️', taxFree: false },
      { name: 'Alpaca', emoji: '🦙', taxFree: false },
      { name: 'Gemini', emoji: '💠', taxFree: false },
    ];

    for (const b of brokerList) {
      this.brokers.set(b.name, {
        name: b.name,
        emoji: b.emoji,
        balance: CONFIG.BALANCE_PER_BROKER,
        positions: 0,
        wins: 0,
        losses: 0,
        pnl: 0,
        taxFree: b.taxFree,
        hasScout: false,
        scoutDeployed: false
      });
    }
  }

  async start(): Promise<void> {
    this.printHeader();
    
    console.log('\n  📡 Connecting to live markets and deploying scouts...\n');
    
    while (true) {
      this.scans++;
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      await this.executeScan();
      this.displayStatus();
      
      await new Promise(r => setTimeout(r, CONFIG.SCAN_INTERVAL_MS));
    }
  }

  private async executeScan(): Promise<void> {
    // Fetch all prices in parallel
    const [binance, kraken, okx, coinbase, bitstamp, forex] = await Promise.all([
      fetchBinancePrices(),
      fetchKrakenPrices(),
      fetchOKXPrices(),
      fetchCoinbasePrices(),
      fetchBitstampPrices(),
      fetchForexPrices()
    ]);

    // Sort by direction
    const sortFn = (a: LivePrice, b: LivePrice) => {
      const cmp = a.symbol.localeCompare(b.symbol);
      return this.scanDirection === 'A→Z' ? cmp : -cmp;
    };

    // Process each exchange - sorted by A→Z or Z→A
    this.processPrices('Binance', binance.sort(sortFn));
    this.processPrices('Kraken', kraken.sort(sortFn));
    this.processPrices('OKX', okx.sort(sortFn));
    this.processPrices('Coinbase', coinbase.sort(sortFn));
    this.processPrices('Bitstamp', bitstamp.sort(sortFn));
    
    // Forex goes to multiple brokers
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

    for (const price of prices) {
      const key = `${broker}:${price.symbol}`;
      
      // Track price history
      if (!this.priceHistory.has(key)) {
        this.priceHistory.set(key, []);
      }
      const history = this.priceHistory.get(key)!;
      history.push(price.mid);
      if (history.length > 50) history.shift();
      
      // Check existing position
      const existingPos = this.positions.get(key);
      if (existingPos) {
        this.updatePosition(key, price.mid);
        continue;
      }
    }
    
    // SCOUT DEPLOYMENT: Deploy 1 scout per broker immediately if none exists
    if (!brokerState.scoutDeployed && prices.length > 0) {
      // Pick the first asset in sorted order (A→Z or Z→A direction)
      const scoutPrice = prices[0];
      this.deployScout(broker, scoutPrice);
    }
    
    // Additional entries based on 24h momentum
    for (const price of prices) {
      const key = `${broker}:${price.symbol}`;
      if (this.positions.has(key)) continue;
      if (brokerState.positions >= CONFIG.MAX_POSITIONS_PER_BROKER) break;
      
      // Enter on strong 24h momentum
      if (price.change24h !== undefined) {
        if (price.change24h > 3) {
          // Strong bullish - LONG
          this.openPosition(broker, price, 'LONG', `📈+${price.change24h.toFixed(1)}%`, false);
        } else if (price.change24h < -3) {
          // Strong bearish - SHORT
          this.openPosition(broker, price, 'SHORT', `📉${price.change24h.toFixed(1)}%`, false);
        }
      }
    }
  }

  private deployScout(broker: string, price: LivePrice): void {
    const brokerState = this.brokers.get(broker);
    if (!brokerState) return;
    
    // Use 24h change to pick direction, or random if not available
    let direction: 'LONG' | 'SHORT';
    if (price.change24h !== undefined) {
      direction = price.change24h >= 0 ? 'LONG' : 'SHORT';
    } else {
      direction = Math.random() > 0.5 ? 'LONG' : 'SHORT';
    }
    
    const key = `${broker}:${price.symbol}`;
    const entryPrice = direction === 'LONG' ? price.ask : price.bid;
    const size = (brokerState.balance * CONFIG.POSITION_SIZE_PCT) / entryPrice;
    
    this.positions.set(key, {
      broker,
      symbol: price.symbol,
      direction,
      size,
      entryPrice,
      currentPrice: price.mid,
      pnl: 0,
      pnlPercent: 0,
      taxFree: brokerState.taxFree,
      isScout: true
    });
    
    brokerState.positions++;
    brokerState.scoutDeployed = true;
    brokerState.hasScout = true;
    
    const dir = this.scanDirection;
    const dirEmoji = direction === 'LONG' ? '⬆️' : '⬇️';
    const taxLabel = brokerState.taxFree ? ' 🎁TAX FREE' : '';
    const priceStr = price.mid < 10 ? price.mid.toFixed(5) : price.mid.toFixed(2);
    console.log(`  ${brokerState.emoji} [${dir}] 🔭 SCOUT ${dirEmoji}: ${price.symbol} @ ${priceStr}${taxLabel}`);
  }

  private openPosition(broker: string, price: LivePrice, direction: 'LONG' | 'SHORT', reason: string, isScout: boolean): void {
    const brokerState = this.brokers.get(broker);
    if (!brokerState) return;
    
    const key = `${broker}:${price.symbol}`;
    const entryPrice = direction === 'LONG' ? price.ask : price.bid;
    const size = (brokerState.balance * CONFIG.POSITION_SIZE_PCT) / entryPrice;
    
    this.positions.set(key, {
      broker,
      symbol: price.symbol,
      direction,
      size,
      entryPrice,
      currentPrice: price.mid,
      pnl: 0,
      pnlPercent: 0,
      taxFree: brokerState.taxFree,
      isScout
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
    pos.pnl = priceDiff * pos.size * multiplier;
    pos.pnlPercent = (priceDiff / pos.entryPrice) * 100 * multiplier;
    
    // Check stop loss
    if (pos.pnlPercent <= -CONFIG.STOP_LOSS_PCT * 100) {
      this.closePosition(key, 'STOP');
    }
    // Check take profit
    else if (pos.pnlPercent >= CONFIG.TAKE_PROFIT_PCT * 100) {
      this.closePosition(key, 'PROFIT');
    }
  }

  private closePosition(key: string, reason: 'STOP' | 'PROFIT'): void {
    const pos = this.positions.get(key);
    if (!pos) return;
    
    const brokerState = this.brokers.get(pos.broker);
    if (!brokerState) return;
    
    brokerState.balance += pos.pnl;
    brokerState.pnl += pos.pnl;
    this.totalPnL += pos.pnl;
    
    if (pos.pnl >= 0) {
      brokerState.wins++;
      this.wins++;
    } else {
      brokerState.losses++;
      this.losses++;
    }
    
    brokerState.positions--;
    if (pos.isScout) brokerState.hasScout = false;
    
    const emoji = pos.pnl >= 0 ? '✅' : '❌';
    const scoutLabel = pos.isScout ? ' 🔭' : '';
    const taxLabel = pos.taxFree ? ' 🎁TAX FREE!' : '';
    const pnlStr = pos.pnl >= 0 ? `+£${pos.pnl.toFixed(4)}` : `-£${Math.abs(pos.pnl).toFixed(4)}`;
    console.log(`  ${brokerState.emoji} ${emoji} ${reason}${scoutLabel}: ${pos.symbol} | P&L: ${pnlStr}${taxLabel}`);
    
    this.positions.delete(key);
  }

  private printHeader(): void {
    console.log('\n');
    console.log('  ╔═══════════════════════════════════════════════════════════════════════════════╗');
    console.log('  ║                                                                               ║');
    console.log('  ║   🌊 IMMEDIATE WAVE RIDER - LIVE MARKETS 🌊                                   ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   A→Z  ↔  Z→A  "They Can\'t Stop Them All!"                                   ║');
    console.log('  ║                                                                               ║');
    console.log('  ╠═══════════════════════════════════════════════════════════════════════════════╣');
    console.log('  ║                                                                               ║');
    console.log('  ║   CRYPTO:  🪙 Binance  🦑 Kraken  🟠 Coinbase  💎 Bitstamp  💠 Gemini  ⭕ OKX  ║');
    console.log('  ║   FOREX:   💱 OANDA  💹 FXCM  🏦 Saxo  🏛️ IB                                   ║');
    console.log('  ║   CFD:     📊 Capital  📈 IG  📉 CMC  🦙 Alpaca                               ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   🎁 TAX FREE (Spread Betting): 📈 IG  📉 CMC                                 ║');
    console.log('  ║                                                                               ║');
    console.log('  ╠═══════════════════════════════════════════════════════════════════════════════╣');
    console.log(`  ║   Capital: £${CONFIG.BALANCE_PER_BROKER} × 14 = £${CONFIG.BALANCE_PER_BROKER * 14} | Size: ${CONFIG.POSITION_SIZE_PCT*100}% | SL: ${CONFIG.STOP_LOSS_PCT*100}% | TP: ${CONFIG.TAKE_PROFIT_PCT*100}%       ║`);
    console.log('  ╚═══════════════════════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log('  🔭 Deploying SCOUTS immediately - 1 per broker in A→Z / Z→A order...');
    console.log('  ────────────────────────────────────────────────────────────────────────────────');
  }

  private displayStatus(): void {
    const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    let totalBalance = 0;
    let totalPositions = 0;
    let scoutsActive = 0;
    let taxFreePnL = 0;
    
    const lines: string[] = [];
    
    for (const [name, state] of this.brokers) {
      totalBalance += state.balance;
      totalPositions += state.positions;
      if (state.hasScout) scoutsActive++;
      if (state.taxFree) taxFreePnL += state.pnl;
      
      const hitRate = state.wins + state.losses > 0
        ? ((state.wins / (state.wins + state.losses)) * 100).toFixed(0)
        : '-';
      
      const pnlStr = state.pnl >= 0 ? `+£${state.pnl.toFixed(2)}` : `-£${Math.abs(state.pnl).toFixed(2)}`;
      const pnlEmoji = state.pnl >= 0 ? '🟢' : '🔴';
      const taxLabel = state.taxFree ? '🎁' : '  ';
      const scoutLabel = state.hasScout ? '🔭' : '  ';
      
      lines.push(
        `  │ ${state.emoji} ${state.name.padEnd(8)} │ £${state.balance.toFixed(2).padStart(6)} │ ${state.positions}/${CONFIG.MAX_POSITIONS_PER_BROKER} │ ${hitRate.padStart(3)}% │ ${pnlEmoji} ${pnlStr.padStart(8)} │ ${taxLabel} │ ${scoutLabel} │`
      );
    }
    
    const totalHitRate = this.wins + this.losses > 0
      ? ((this.wins / (this.wins + this.losses)) * 100).toFixed(1)
      : '0.0';
    
    const totalPnLStr = this.totalPnL >= 0 ? `+£${this.totalPnL.toFixed(2)}` : `-£${Math.abs(this.totalPnL).toFixed(2)}`;
    const totalEmoji = this.totalPnL >= 0 ? '🟢' : '🔴';
    
    console.log('');
    console.log('  ┌─────────────────────────────────────────────────────────────────────────────────┐');
    console.log(`  │  SCAN #${this.scans.toString().padStart(5)} [${this.scanDirection}]  │  Time: ${minutes}m ${seconds}s  │  Positions: ${totalPositions}/${14 * CONFIG.MAX_POSITIONS_PER_BROKER}  │  🔭 Scouts: ${scoutsActive}  │`);
    console.log('  ├─────────────────────────────────────────────────────────────────────────────────┤');
    console.log('  │  Broker    │ Balance  │ Pos │  HR  │     P&L    │ 🎁 │ 🔭 │');
    console.log('  ├────────────┼──────────┼─────┼──────┼────────────┼────┼────┤');
    
    for (const line of lines) {
      console.log(line);
    }
    
    console.log('  ├────────────┼──────────┼─────┼──────┼────────────┼────┼────┤');
    console.log(`  │ 🌊 TOTAL   │ £${totalBalance.toFixed(2).padStart(6)} │ ${totalPositions.toString().padStart(2)}  │${totalHitRate.padStart(5)}% │ ${totalEmoji} ${totalPnLStr.padStart(8)} │    │    │`);
    console.log('  └─────────────────────────────────────────────────────────────────────────────────┘');
    
    if (taxFreePnL !== 0) {
      const taxFreeStr = taxFreePnL >= 0 ? `+£${taxFreePnL.toFixed(4)}` : `-£${Math.abs(taxFreePnL).toFixed(4)}`;
      console.log(`  🎁 Tax-Free P&L (IG + CMC): ${taxFreeStr}`);
    }
    
    this.displayPositions();
  }

  private displayPositions(): void {
    const allPositions = Array.from(this.positions.values());
    
    if (allPositions.length === 0) {
      console.log('');
      console.log(`  🌊 [${this.scanDirection}] All scouts closed - looking for re-entry opportunities...`);
      console.log('');
      return;
    }
    
    allPositions.sort((a, b) => b.pnl - a.pnl);
    
    console.log('');
    console.log(`  🌊 Active Positions [${this.scanDirection}]:`);
    console.log('');
    
    for (const pos of allPositions.slice(0, 16)) {
      const emoji = pos.pnl >= 0 ? '🟢' : '🔴';
      const dir = pos.direction === 'LONG' ? '⬆' : '⬇';
      const brokerState = this.brokers.get(pos.broker);
      const brokerEmoji = brokerState?.emoji || '📈';
      const taxLabel = pos.taxFree ? ' 🎁' : '';
      const scoutLabel = pos.isScout ? ' 🔭' : '';
      
      const pnlStr = pos.pnl >= 0 ? `+£${pos.pnl.toFixed(4)}` : `-£${Math.abs(pos.pnl).toFixed(4)}`;
      
      console.log(`     ${brokerEmoji} ${emoji} ${pos.symbol.padEnd(12)} ${dir} → ${pnlStr} (${pos.pnlPercent.toFixed(2)}%)${taxLabel}${scoutLabel}`);
    }
    
    if (allPositions.length > 16) {
      console.log(`     ... and ${allPositions.length - 16} more positions`);
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
  ║   🌊 IMMEDIATE WAVE RIDER 🌊                                                  ║
  ║                                                                               ║
  ║   Strategy:                                                                   ║
  ║   • Deploy SCOUTS immediately - 1 per broker                                  ║
  ║   • A→Z on odd scans, Z→A on even scans                                      ║
  ║   • Enter additional positions on strong 24h momentum (>±3%)                 ║
  ║   • Ride the wave with 2% SL / 4% TP                                         ║
  ║   • "They can't stop them all!"                                              ║
  ║                                                                               ║
  ║   Live Data Sources:                                                          ║
  ║   • Binance API (20 pairs)                                                    ║
  ║   • Kraken API (10 pairs)                                                     ║
  ║   • OKX API (15 pairs)                                                        ║
  ║   • Coinbase API (8 pairs)                                                    ║
  ║   • Bitstamp API (7 pairs)                                                    ║
  ║   • Forex API (8 major pairs)                                                 ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);

  const rider = new ImmediateWaveRider();
  
  process.on('SIGINT', () => {
    console.log('\n');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('  🌊 Wave Rider concludes...');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('');
    console.log('  "A→Z ↔ Z→A - The wave rides eternal"');
    console.log('');
    process.exit(0);
  });

  await rider.start();
}

main().catch(console.error);
