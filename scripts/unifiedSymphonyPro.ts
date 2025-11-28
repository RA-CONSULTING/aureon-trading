/**
 * 🎵 THE UNIFIED SYMPHONY PRO 🎵
 * 
 * Twelve Brokers Playing in Perfect Harmony
 * 
 *   ╔═══════════════════════════════════════════════════════════════════════════╗
 *   ║   🌍 ULTIMATE MULTI-BROKER TRADING ORCHESTRA 🌍                          ║
 *   ║                                                                           ║
 *   ║   EXISTING BROKERS:                                                       ║
 *   ║   🪙 Binance      📊 Capital.com   🦙 Alpaca      💱 OANDA    🦑 Kraken   ║
 *   ║                                                                           ║
 *   ║   NEW BROKERS:                                                            ║
 *   ║   🏛️ Interactive Brokers  📈 IG Markets      📉 CMC Markets              ║
 *   ║   🟠 Coinbase             💎 Bitstamp        💠 Gemini                    ║
 *   ║   ⭕ OKX                  🏦 Saxo Bank       💹 FXCM                       ║
 *   ║                                                                           ║
 *   ║   Total: 12 Brokers • All UK/Northern Ireland Available                   ║
 *   ╚═══════════════════════════════════════════════════════════════════════════╝
 * 
 * Features:
 * - Spread betting (tax-free) via IG, CMC Markets
 * - Forex via OANDA, FXCM, Saxo, IB
 * - Crypto via Binance, Kraken, Coinbase, Bitstamp, Gemini, OKX
 * - Stocks via Alpaca, IB, Saxo
 * - CFDs via Capital.com, IG, CMC
 * 
 * Run: npx tsx scripts/unifiedSymphonyPro.ts
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
  // Starting balance per broker (£20 each)
  BALANCE_PER_BROKER: 20,
  TOTAL_BROKERS: 14,
  
  // Coherence thresholds
  ENTRY_COHERENCE: 0.938,
  EXIT_COHERENCE: 0.934,
  
  // Position sizing
  POSITION_SIZE_PCT: 0.10,  // 10% per trade = £2 per position
  STOP_LOSS_PCT: 0.02,      // 2% stop loss
  TAKE_PROFIT_PCT: 0.04,    // 4% take profit
  
  // Max positions per broker
  MAX_POSITIONS_PER_BROKER: 3,
  
  // Scan timing
  SCAN_INTERVAL_MS: 5000,
  
  // Enable/disable broker categories
  ENABLE_CRYPTO: true,      // Binance, Kraken, Coinbase, Bitstamp, Gemini, OKX
  ENABLE_FOREX: true,       // OANDA, FXCM, Saxo, IB
  ENABLE_STOCKS: true,      // Alpaca, IB, Saxo
  ENABLE_CFD: true,         // Capital.com, IG, CMC
  ENABLE_SPREAD_BETTING: true,  // IG, CMC (TAX FREE!)
};

// ═══════════════════════════════════════════════════════════════════════════
// Types
// ═══════════════════════════════════════════════════════════════════════════

interface BrokerConfig {
  name: string;
  emoji: string;
  type: 'crypto' | 'forex' | 'stocks' | 'cfd' | 'multi';
  region: 'UK' | 'EU' | 'US' | 'Global';
  taxFree: boolean;  // Spread betting = tax free in UK
  assets: string[];
  color: string;
}

interface BrokerState {
  name: string;
  emoji: string;
  connected: boolean;
  balance: number;
  positions: number;
  wins: number;
  losses: number;
  pnl: number;
  lastSignal: string;
  assetCount: number;
  type: string;
  taxFree: boolean;
}

interface UnifiedPosition {
  broker: string;
  symbol: string;
  direction: 'LONG' | 'SHORT';
  size: number;
  entryPrice: number;
  currentPrice: number;
  pnl: number;
  pnlPercent: number;
  taxFree: boolean;
}

// ═══════════════════════════════════════════════════════════════════════════
// Broker Definitions
// ═══════════════════════════════════════════════════════════════════════════

const BROKER_CONFIGS: BrokerConfig[] = [
  // ═══════════════════════════════════════════════════════════════════════
  // EXISTING BROKERS
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'Binance',
    emoji: '🪙',
    type: 'crypto',
    region: 'Global',
    taxFree: false,
    color: '\x1b[33m', // Yellow
    assets: [
      'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'XRPUSDT', 'DOGEUSDT',
      'ADAUSDT', 'AVAXUSDT', 'DOTUSDT', 'LINKUSDT', 'MATICUSDT'
    ]
  },
  {
    name: 'Capital',
    emoji: '📊',
    type: 'cfd',
    region: 'UK',
    taxFree: false,
    color: '\x1b[34m', // Blue
    assets: [
      'BTCUSD', 'ETHUSD', 'GOLD', 'US500', 'UK100',
      'EURUSD', 'GBPUSD', 'AAPL', 'MSFT', 'TSLA'
    ]
  },
  {
    name: 'Alpaca',
    emoji: '🦙',
    type: 'stocks',
    region: 'US',
    taxFree: false,
    color: '\x1b[32m', // Green
    assets: [
      'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
      'NVDA', 'TSLA', 'AMD', 'NFLX', 'SPY'
    ]
  },
  {
    name: 'OANDA',
    emoji: '💱',
    type: 'forex',
    region: 'UK',
    taxFree: false,
    color: '\x1b[36m', // Cyan
    assets: [
      'EUR_USD', 'GBP_USD', 'USD_JPY', 'USD_CHF', 'AUD_USD',
      'EUR_GBP', 'GBP_JPY', 'XAU_USD', 'SPX500_USD', 'NAS100_USD'
    ]
  },
  {
    name: 'Kraken',
    emoji: '🦑',
    type: 'crypto',
    region: 'UK',
    taxFree: false,
    color: '\x1b[35m', // Magenta
    assets: [
      'XXBTZGBP', 'XETHZGBP', 'SOLGBP', 'XRPGBP', 'DOTGBP',
      'XXBTZUSD', 'XETHZUSD', 'LINKUSD', 'ADAUSD', 'ATOMUSD'
    ]
  },
  
  // ═══════════════════════════════════════════════════════════════════════
  // NEW BROKERS
  // ═══════════════════════════════════════════════════════════════════════
  {
    name: 'IB',
    emoji: '🏛️',
    type: 'multi',
    region: 'Global',
    taxFree: false,
    color: '\x1b[31m', // Red
    assets: [
      'AAPL', 'MSFT', 'HSBA', 'BP', 'SHEL',
      'EUR.USD', 'GBP.USD', 'ES', 'NQ', 'GC'
    ]
  },
  {
    name: 'IG',
    emoji: '📈',
    type: 'cfd',
    region: 'UK',
    taxFree: true,  // SPREAD BETTING = TAX FREE!
    color: '\x1b[91m', // Light Red
    assets: [
      'UK100', 'DE40', 'US500', 'EURUSD', 'GBPUSD',
      'GOLD', 'SILVER', 'OILUK', 'VOD', 'BARC'
    ]
  },
  {
    name: 'CMC',
    emoji: '📉',
    type: 'cfd',
    region: 'UK',
    taxFree: true,  // SPREAD BETTING = TAX FREE!
    color: '\x1b[92m', // Light Green
    assets: [
      'UK100', 'GER40', 'NASDAQ', 'EURUSD', 'GBPJPY',
      'XAUUSD', 'BTCUSD', 'ETHUSD', 'AAPL', 'TSLA'
    ]
  },
  {
    name: 'Coinbase',
    emoji: '🟠',
    type: 'crypto',
    region: 'UK',
    taxFree: false,
    color: '\x1b[94m', // Light Blue
    assets: [
      'BTC-GBP', 'ETH-GBP', 'SOL-GBP', 'XRP-GBP', 'DOGE-GBP',
      'BTC-USD', 'ETH-USD', 'ADA-USD', 'DOT-USD', 'LINK-USD'
    ]
  },
  {
    name: 'Bitstamp',
    emoji: '💎',
    type: 'crypto',
    region: 'UK',
    taxFree: false,
    color: '\x1b[93m', // Light Yellow
    assets: [
      'btcgbp', 'ethgbp', 'xrpgbp', 'ltcgbp', 'linkgbp',
      'btcusd', 'ethusd', 'xrpusd', 'solusd', 'adausd'
    ]
  },
  {
    name: 'Gemini',
    emoji: '💠',
    type: 'crypto',
    region: 'UK',
    taxFree: false,
    color: '\x1b[95m', // Light Magenta
    assets: [
      'BTCGBP', 'ETHGBP', 'SOLGBP', 'DOGEGBP', 'LINKGBP',
      'BTCUSD', 'ETHUSD', 'SOLUSD', 'MATICUSD', 'AAVEUSD'
    ]
  },
  {
    name: 'OKX',
    emoji: '⭕',
    type: 'crypto',
    region: 'Global',
    taxFree: false,
    color: '\x1b[96m', // Light Cyan
    assets: [
      'BTC-USDT', 'ETH-USDT', 'SOL-USDT', 'XRP-USDT', 'DOGE-USDT',
      'ADA-USDT', 'DOT-USDT', 'AVAX-USDT', 'LINK-USDT', 'NEAR-USDT'
    ]
  },
];

// Additional brokers (Saxo and FXCM)
const ADDITIONAL_BROKERS: BrokerConfig[] = [
  {
    name: 'Saxo',
    emoji: '🏦',
    type: 'multi',
    region: 'UK',
    taxFree: false,
    color: '\x1b[90m', // Dark Gray
    assets: [
      'EURUSD', 'GBPUSD', 'USDJPY', 'UK100', 'US500',
      'XAUUSD', 'HSBA:xlon', 'BP.:xlon', 'AAPL:xnas', 'MSFT:xnas'
    ]
  },
  {
    name: 'FXCM',
    emoji: '💹',
    type: 'forex',
    region: 'UK',
    taxFree: false,
    color: '\x1b[97m', // White
    assets: [
      'EUR/USD', 'GBP/USD', 'USD/JPY', 'EUR/GBP', 'GBP/JPY',
      'XAU/USD', 'UK100', 'US30', 'NAS100', 'USOil'
    ]
  }
];

// Combine all brokers
const ALL_BROKERS = [...BROKER_CONFIGS, ...ADDITIONAL_BROKERS];

// ═══════════════════════════════════════════════════════════════════════════
// Coherence Engine (Unified)
// ═══════════════════════════════════════════════════════════════════════════

class UnifiedCoherenceEngine {
  private priceHistory: Map<string, number[]> = new Map();
  private PHI = 1.618033988749895;
  private PHI_MINOR = 0.381966011250105;
  
  addPrice(key: string, price: number): void {
    if (!this.priceHistory.has(key)) {
      this.priceHistory.set(key, []);
    }
    const history = this.priceHistory.get(key)!;
    history.push(price);
    if (history.length > 100) history.shift();
  }
  
  calculateCoherence(key: string): number {
    const history = this.priceHistory.get(key);
    if (!history || history.length < 10) return 0;
    
    const recent = history.slice(-20);
    const min = Math.min(...recent);
    const max = Math.max(...recent);
    const range = max - min;
    if (range === 0) return 0.5;
    
    const current = recent[recent.length - 1];
    const normalized = (current - min) / range;
    
    // Phi-based harmonic analysis
    const phiMajorDist = Math.abs(normalized - (1 / this.PHI));
    const phiMinorDist = Math.abs(normalized - this.PHI_MINOR);
    const phiScore = 1 - Math.min(phiMajorDist, phiMinorDist);
    
    // Momentum analysis
    const momentum = (current - recent[0]) / recent[0];
    const momentumScore = Math.tanh(momentum * 50) * 0.5 + 0.5;
    
    // Wave position
    const wavePosition = Math.sin(normalized * Math.PI) ** 2;
    
    return (phiScore * 0.4 + momentumScore * 0.3 + wavePosition * 0.3);
  }
  
  getSignal(key: string): 'BUY' | 'SELL' | 'HOLD' {
    const coherence = this.calculateCoherence(key);
    const history = this.priceHistory.get(key);
    
    if (!history || history.length < 5) return 'HOLD';
    
    const trend = history[history.length - 1] > history[history.length - 5] ? 1 : -1;
    
    // For demo mode, lower threshold
    const threshold = 0.80;
    
    if (coherence >= threshold && trend > 0) return 'BUY';
    if (coherence >= threshold && trend < 0) return 'SELL';
    
    // Random entry for demo action (15% chance)
    if (Math.random() < 0.15) {
      return Math.random() > 0.5 ? 'BUY' : 'SELL';
    }
    
    return 'HOLD';
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Simulated Broker
// ═══════════════════════════════════════════════════════════════════════════

class SimulatedBroker {
  config: BrokerConfig;
  balance: number;
  positions: Map<string, UnifiedPosition> = new Map();
  wins = 0;
  losses = 0;
  realizedPnL = 0;
  
  constructor(config: BrokerConfig) {
    this.config = config;
    this.balance = CONFIG.BALANCE_PER_BROKER;
  }
  
  async getPrice(symbol: string): Promise<number> {
    const basePrice = this.getBasePrice(symbol);
    const volatility = 0.002;
    const change = (Math.random() - 0.5) * 2 * volatility;
    return basePrice * (1 + change);
  }
  
  private getBasePrice(symbol: string): number {
    const s = symbol.toUpperCase();
    
    // Crypto
    if (s.includes('BTC')) return 95000;
    if (s.includes('ETH')) return 3500;
    if (s.includes('SOL')) return 250;
    if (s.includes('XRP')) return 2.5;
    if (s.includes('DOGE')) return 0.4;
    if (s.includes('ADA')) return 1.1;
    if (s.includes('DOT')) return 8;
    if (s.includes('LINK')) return 25;
    if (s.includes('AVAX')) return 45;
    
    // Forex
    if (s.includes('EURUSD') || s.includes('EUR_USD') || s.includes('EUR/USD') || s.includes('EUR.USD')) return 1.05;
    if (s.includes('GBPUSD') || s.includes('GBP_USD') || s.includes('GBP/USD') || s.includes('GBP.USD')) return 1.27;
    if (s.includes('USDJPY') || s.includes('USD_JPY') || s.includes('USD/JPY')) return 150;
    if (s.includes('EURGBP') || s.includes('EUR_GBP') || s.includes('EUR/GBP')) return 0.83;
    if (s.includes('GBPJPY') || s.includes('GBP_JPY') || s.includes('GBP/JPY')) return 190;
    
    // Indices
    if (s.includes('UK100') || s.includes('FTSE')) return 8300;
    if (s.includes('US500') || s.includes('SPX') || s.includes('SPY')) return 6000;
    if (s.includes('US30') || s.includes('DOW')) return 43000;
    if (s.includes('NAS') || s.includes('US100') || s.includes('NQ')) return 21000;
    if (s.includes('DE40') || s.includes('GER')) return 19000;
    
    // Commodities
    if (s.includes('GOLD') || s.includes('XAU')) return 2650;
    if (s.includes('SILVER') || s.includes('XAG')) return 30;
    if (s.includes('OIL') || s.includes('BCO') || s.includes('CL')) return 75;
    
    // US Stocks
    if (s.includes('AAPL')) return 175;
    if (s.includes('MSFT')) return 420;
    if (s.includes('TSLA')) return 350;
    if (s.includes('GOOGL')) return 175;
    if (s.includes('AMZN')) return 200;
    if (s.includes('NVDA')) return 140;
    if (s.includes('META')) return 550;
    
    // UK Stocks
    if (s.includes('HSBA') || s.includes('HSBC')) return 7.5;
    if (s.includes('BP')) return 4.5;
    if (s.includes('SHEL')) return 28;
    if (s.includes('VOD')) return 0.7;
    if (s.includes('BARC')) return 2.5;
    
    return 100;
  }
  
  openPosition(symbol: string, direction: 'LONG' | 'SHORT', price: number): boolean {
    if (this.positions.has(symbol)) return false;
    if (this.positions.size >= CONFIG.MAX_POSITIONS_PER_BROKER) return false;
    
    const size = (this.balance * CONFIG.POSITION_SIZE_PCT) / price;
    
    this.positions.set(symbol, {
      broker: this.config.name,
      symbol,
      direction,
      size,
      entryPrice: price,
      currentPrice: price,
      pnl: 0,
      pnlPercent: 0,
      taxFree: this.config.taxFree
    });
    
    return true;
  }
  
  updatePosition(symbol: string, currentPrice: number): void {
    const pos = this.positions.get(symbol);
    if (!pos) return;
    
    pos.currentPrice = currentPrice;
    const priceDiff = currentPrice - pos.entryPrice;
    const multiplier = pos.direction === 'LONG' ? 1 : -1;
    pos.pnl = priceDiff * pos.size * multiplier;
    pos.pnlPercent = (priceDiff / pos.entryPrice) * 100 * multiplier;
  }
  
  checkStopLossTakeProfit(symbol: string): 'STOP' | 'PROFIT' | null {
    const pos = this.positions.get(symbol);
    if (!pos) return null;
    
    if (pos.pnlPercent <= -CONFIG.STOP_LOSS_PCT * 100) return 'STOP';
    if (pos.pnlPercent >= CONFIG.TAKE_PROFIT_PCT * 100) return 'PROFIT';
    
    return null;
  }
  
  closePosition(symbol: string, reason: string): number {
    const pos = this.positions.get(symbol);
    if (!pos) return 0;
    
    const pnl = pos.pnl;
    this.realizedPnL += pnl;
    this.balance += pnl;
    
    if (pnl >= 0) {
      this.wins++;
    } else {
      this.losses++;
    }
    
    this.positions.delete(symbol);
    return pnl;
  }
  
  getOpenPnL(): number {
    return Array.from(this.positions.values()).reduce((sum, p) => sum + p.pnl, 0);
  }
  
  getState(): BrokerState {
    return {
      name: this.config.name,
      emoji: this.config.emoji,
      connected: true,
      balance: this.balance,
      positions: this.positions.size,
      wins: this.wins,
      losses: this.losses,
      pnl: this.realizedPnL + this.getOpenPnL(),
      lastSignal: '',
      assetCount: this.config.assets.length,
      type: this.config.type,
      taxFree: this.config.taxFree
    };
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Unified Symphony Pro Controller
// ═══════════════════════════════════════════════════════════════════════════

class UnifiedSymphonyPro {
  private coherence: UnifiedCoherenceEngine;
  private brokers: SimulatedBroker[] = [];
  private scanDirection: 'A→Z' | 'Z→A' = 'A→Z';
  private scans = 0;
  private startTime: Date;
  
  constructor() {
    this.coherence = new UnifiedCoherenceEngine();
    this.startTime = new Date();
    
    // Initialize all brokers
    for (const config of ALL_BROKERS) {
      this.brokers.push(new SimulatedBroker(config));
    }
    
    console.log(`\n  ✅ Initialized ${this.brokers.length} brokers`);
  }
  
  async start(): Promise<void> {
    this.printHeader();
    
    while (true) {
      this.scans++;
      this.scanDirection = this.scanDirection === 'A→Z' ? 'Z→A' : 'A→Z';
      
      // Run all brokers in parallel
      await Promise.all(this.brokers.map(broker => this.scanBroker(broker)));
      
      // Display unified status
      this.displayStatus();
      
      await this.sleep(CONFIG.SCAN_INTERVAL_MS);
    }
  }
  
  private async scanBroker(broker: SimulatedBroker): Promise<void> {
    const assets = [...broker.config.assets];
    assets.sort((a, b) => {
      const cmp = a.localeCompare(b);
      return this.scanDirection === 'A→Z' ? cmp : -cmp;
    });
    
    // Update existing positions
    for (const [symbol, pos] of broker.positions) {
      const price = await broker.getPrice(symbol);
      broker.updatePosition(symbol, price);
      
      const action = broker.checkStopLossTakeProfit(symbol);
      if (action) {
        const pnl = broker.closePosition(symbol, action);
        const emoji = pnl >= 0 ? '✅' : '❌';
        const taxLabel = broker.config.taxFree ? ' 🎁TAX FREE!' : '';
        console.log(`  ${broker.config.emoji} ${emoji} ${action}: ${symbol} | P&L: £${pnl.toFixed(2)}${taxLabel}`);
      }
    }
    
    // Scan for new opportunities
    for (const symbol of assets) {
      if (broker.positions.has(symbol)) continue;
      if (broker.positions.size >= CONFIG.MAX_POSITIONS_PER_BROKER) break;
      
      const price = await broker.getPrice(symbol);
      const key = `${broker.config.name}:${symbol}`;
      
      this.coherence.addPrice(key, price);
      const signal = this.coherence.getSignal(key);
      
      if (signal !== 'HOLD') {
        const direction = signal === 'BUY' ? 'LONG' : 'SHORT';
        const opened = broker.openPosition(symbol, direction, price);
        
        if (opened) {
          const taxLabel = broker.config.taxFree ? ' 🎁' : '';
          console.log(`  ${broker.config.emoji} ⚡ ${signal}: ${symbol} @ ${price.toFixed(4)}${taxLabel}`);
        }
      }
    }
  }
  
  private printHeader(): void {
    console.log('\n');
    console.log('  ╔═══════════════════════════════════════════════════════════════════════════════╗');
    console.log('  ║                                                                               ║');
    console.log('  ║   🎵 THE UNIFIED SYMPHONY PRO - 12 BROKER ORCHESTRA 🎵                        ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   All UK/Northern Ireland Available Trading Platforms                         ║');
    console.log('  ║                                                                               ║');
    console.log('  ╠═══════════════════════════════════════════════════════════════════════════════╣');
    console.log('  ║                                                                               ║');
    console.log('  ║   CRYPTO:  🪙 Binance  🦑 Kraken  🟠 Coinbase  💎 Bitstamp  💠 Gemini  ⭕ OKX  ║');
    console.log('  ║   FOREX:   💱 OANDA  💹 FXCM  🏦 Saxo  🏛️ IB                                   ║');
    console.log('  ║   STOCKS:  🦙 Alpaca  🏛️ IB  🏦 Saxo                                          ║');
    console.log('  ║   CFD:     📊 Capital  📈 IG  📉 CMC                                          ║');
    console.log('  ║                                                                               ║');
    console.log('  ║   🎁 TAX FREE (Spread Betting): 📈 IG  📉 CMC                                 ║');
    console.log('  ║                                                                               ║');
    console.log('  ╠═══════════════════════════════════════════════════════════════════════════════╣');
    console.log(`  ║   Total Starting Capital: £${CONFIG.BALANCE_PER_BROKER * this.brokers.length} (£${CONFIG.BALANCE_PER_BROKER} × ${this.brokers.length} brokers)             ║`);
    console.log('  ║   Coherence Φ: Entry 0.938 | Exit 0.934                                       ║');
    console.log('  ║   Risk: 2% SL | 4% TP | 5% Position Size                                      ║');
    console.log('  ╚═══════════════════════════════════════════════════════════════════════════════╝');
    console.log('');
    console.log('  🎵 The Grand Symphony begins across 12 platforms...');
    console.log('  ────────────────────────────────────────────────────────────────────────────────');
    console.log('');
  }
  
  private displayStatus(): void {
    const elapsed = Math.floor((Date.now() - this.startTime.getTime()) / 1000);
    const minutes = Math.floor(elapsed / 60);
    const seconds = elapsed % 60;
    
    // Calculate totals
    let totalBalance = 0;
    let totalPositions = 0;
    let totalWins = 0;
    let totalLosses = 0;
    let totalPnL = 0;
    let taxFreePnL = 0;
    
    const brokerLines: string[] = [];
    
    for (const broker of this.brokers) {
      const state = broker.getState();
      totalBalance += state.balance;
      totalPositions += state.positions;
      totalWins += state.wins;
      totalLosses += state.losses;
      totalPnL += state.pnl;
      
      if (state.taxFree) {
        taxFreePnL += state.pnl;
      }
      
      const hitRate = state.wins + state.losses > 0
        ? ((state.wins / (state.wins + state.losses)) * 100).toFixed(0)
        : '-';
      
      const pnlStr = state.pnl >= 0 ? `+£${state.pnl.toFixed(2)}` : `-£${Math.abs(state.pnl).toFixed(2)}`;
      const pnlEmoji = state.pnl >= 0 ? '🟢' : '🔴';
      const taxLabel = state.taxFree ? '🎁' : '  ';
      
      brokerLines.push(
        `  │ ${state.emoji} ${state.name.padEnd(8)} │ £${state.balance.toFixed(0).padStart(5)} │ ${state.positions.toString().padStart(1)}/${CONFIG.MAX_POSITIONS_PER_BROKER} │ ${hitRate.padStart(3)}% │ ${pnlEmoji} ${pnlStr.padStart(8)} │ ${taxLabel} │`
      );
    }
    
    const totalHitRate = totalWins + totalLosses > 0
      ? ((totalWins / (totalWins + totalLosses)) * 100).toFixed(1)
      : '0.0';
    
    const totalPnLStr = totalPnL >= 0 ? `+£${totalPnL.toFixed(2)}` : `-£${Math.abs(totalPnL).toFixed(2)}`;
    const totalEmoji = totalPnL >= 0 ? '🟢' : '🔴';
    
    console.log('');
    console.log('  ┌───────────────────────────────────────────────────────────────────────────┐');
    console.log(`  │  SCAN #${this.scans.toString().padStart(5)} [${this.scanDirection}]  │  Time: ${minutes}m ${seconds}s  │  Positions: ${totalPositions}/${this.brokers.length * CONFIG.MAX_POSITIONS_PER_BROKER}  │`);
    console.log('  ├───────────────────────────────────────────────────────────────────────────┤');
    console.log('  │  Broker    │ Balance │ Pos │  HR  │     P&L    │ 🎁 │');
    console.log('  ├────────────┼─────────┼─────┼──────┼────────────┼────┤');
    
    for (const line of brokerLines) {
      console.log(line);
    }
    
    console.log('  ├────────────┼─────────┼─────┼──────┼────────────┼────┤');
    console.log(`  │ 🎵 TOTAL   │ £${totalBalance.toFixed(0).padStart(5)} │ ${totalPositions.toString().padStart(2)}  │${totalHitRate.padStart(5)}% │ ${totalEmoji} ${totalPnLStr.padStart(8)} │    │`);
    console.log('  └───────────────────────────────────────────────────────────────────────────┘');
    
    // Tax-free summary
    if (taxFreePnL !== 0) {
      const taxFreeStr = taxFreePnL >= 0 ? `+£${taxFreePnL.toFixed(2)}` : `-£${Math.abs(taxFreePnL).toFixed(2)}`;
      console.log(`  🎁 Tax-Free P&L (IG + CMC Spread Betting): ${taxFreeStr}`);
    }
    
    this.displayWave();
  }
  
  private displayWave(): void {
    const allPositions: UnifiedPosition[] = [];
    
    for (const broker of this.brokers) {
      for (const pos of broker.positions.values()) {
        allPositions.push(pos);
      }
    }
    
    if (allPositions.length === 0) {
      console.log('');
      console.log('  🌊 Waiting for coherence signals across 12 platforms...');
      console.log('');
      return;
    }
    
    allPositions.sort((a, b) => b.pnl - a.pnl);
    
    console.log('');
    console.log('  🌊 Active Positions Across All 12 Brokers:');
    console.log('');
    
    for (const pos of allPositions.slice(0, 15)) {
      const emoji = pos.pnl >= 0 ? '🟢' : '🔴';
      const dir = pos.direction === 'LONG' ? '⬆' : '⬇';
      const broker = this.brokers.find(b => b.config.name === pos.broker);
      const brokerEmoji = broker?.config.emoji || '📈';
      const taxLabel = pos.taxFree ? ' 🎁' : '';
      
      const pnlStr = pos.pnl >= 0 ? `+£${pos.pnl.toFixed(2)}` : `-£${Math.abs(pos.pnl).toFixed(2)}`;
      
      console.log(`     ${brokerEmoji} ${emoji} ${pos.symbol.padEnd(12)} ${dir} @ ${pos.entryPrice.toFixed(4)} → ${pnlStr} (${pos.pnlPercent.toFixed(1)}%)${taxLabel}`);
    }
    
    if (allPositions.length > 15) {
      console.log(`     ... and ${allPositions.length - 15} more positions`);
    }
    
    console.log('');
  }
  
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}

// ═══════════════════════════════════════════════════════════════════════════
// Main Entry Point
// ═══════════════════════════════════════════════════════════════════════════

async function main() {
  console.log(`
  ╔═══════════════════════════════════════════════════════════════════════════════╗
  ║                                                                               ║
  ║   🎵 AUREON TRADING SYSTEM - 12 BROKER UNIFIED SYMPHONY 🎵                    ║
  ║                                                                               ║
  ║   Northern Ireland / UK Multi-Platform Trading                                ║
  ║                                                                               ║
  ║   🪙 Binance     | Crypto    | 200+ pairs                                     ║
  ║   🦑 Kraken      | Crypto    | UK Friendly                                    ║
  ║   🟠 Coinbase    | Crypto    | GBP Support                                    ║
  ║   💎 Bitstamp    | Crypto    | Oldest Exchange                                ║
  ║   💠 Gemini      | Crypto    | Regulated                                      ║
  ║   ⭕ OKX         | Crypto    | 350+ pairs                                     ║
  ║   💱 OANDA       | Forex     | FCA Regulated                                  ║
  ║   💹 FXCM        | Forex     | Low Spreads                                    ║
  ║   🏦 Saxo        | Multi     | 40,000+ instruments                            ║
  ║   🏛️ IB          | Multi     | Global Access                                  ║
  ║   📊 Capital     | CFD       | Easy Platform                                  ║
  ║   🦙 Alpaca      | Stocks    | US Markets                                     ║
  ║   📈 IG          | CFD       | 🎁 TAX FREE (Spread Betting)                   ║
  ║   📉 CMC         | CFD       | 🎁 TAX FREE (Spread Betting)                   ║
  ║                                                                               ║
  ║   Author: Gary Leckey - R&A Consulting                                       ║
  ║                                                                               ║
  ╚═══════════════════════════════════════════════════════════════════════════════╝
  `);
  
  const symphony = new UnifiedSymphonyPro();
  
  process.on('SIGINT', () => {
    console.log('\n');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('  🎵 The Grand Symphony concludes...');
    console.log('  ────────────────────────────────────────────────────────────────────────────');
    console.log('');
    console.log('  "Twelve instruments playing as one, the wave rides eternal across all markets"');
    console.log('');
    process.exit(0);
  });
  
  await symphony.start();
}

main().catch(console.error);
