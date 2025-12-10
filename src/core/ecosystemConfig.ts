/**
 * 🐙🌌 AUREON UNIFIED ECOSYSTEM CONFIG 🌌🐙
 * 
 * Synced from Python aureon_unified_ecosystem.py CONFIG
 * This is the single source of truth for all trading parameters
 * 
 * GOAL: 51%+ Win Rate with NET PROFIT after ALL fees
 */

export const ECOSYSTEM_CONFIG = {
  // ═══════════════════════════════════════════════════════════════
  // EXCHANGE SELECTION
  // ═══════════════════════════════════════════════════════════════
  EXCHANGE: 'binance', // Default to BINANCE
  BASE_CURRENCY: 'USD',
  
  // ═══════════════════════════════════════════════════════════════
  // PLATFORM-SPECIFIC FEES (as decimals)
  // ═══════════════════════════════════════════════════════════════
  
  // 🐙 KRAKEN
  KRAKEN_FEE_MAKER: 0.0026,     // 0.26% maker fee
  KRAKEN_FEE_TAKER: 0.0040,     // 0.40% taker fee
  KRAKEN_FEE: 0.0040,           // Legacy field (uses taker)
  KRAKEN_MIN_NOTIONAL: 5.0,
  
  // 🟡 BINANCE (UK Account - Spot only)
  BINANCE_FEE_MAKER: 0.0010,    // 0.10% maker
  BINANCE_FEE_TAKER: 0.0010,    // 0.10% taker
  BINANCE_FEE: 0.0010,
  BINANCE_MIN_NOTIONAL: 1.0,
  
  // 🦙 ALPACA (Crypto)
  ALPACA_FEE_MAKER: 0.0015,     // 0.15% maker
  ALPACA_FEE_TAKER: 0.0025,     // 0.25% taker
  ALPACA_FEE_STOCK: 0.0000,     // $0 commission for stocks
  ALPACA_FEE: 0.0025,
  ALPACA_MIN_NOTIONAL: 1.0,
  ALPACA_ANALYTICS_ONLY: true,  // Alpaca is for market data/analytics only
  
  // 💼 CAPITAL.COM (CFD/Spread Betting)
  CAPITAL_FEE_SPREAD: 0.0010,   // ~0.1% avg spread cost
  CAPITAL_FEE_OVERNIGHT: 0.0001,
  CAPITAL_FEE: 0.0010,
  CAPITAL_MIN_NOTIONAL: 10.0,
  
  // ═══════════════════════════════════════════════════════════════
  // TRADING PARAMETERS
  // ═══════════════════════════════════════════════════════════════
  SLIPPAGE_PCT: 0.0010,         // 0.10% estimated slippage per trade
  SPREAD_COST_PCT: 0.0005,      // 0.05% estimated spread cost
  TAKE_PROFIT_PCT: 1.5,         // 1.5% profit target
  STOP_LOSS_PCT: 1.5,           // 1.5% stop loss
  MAX_POSITIONS: 15,            // Maximum concurrent positions
  MIN_TRADE_USD: 5.0,           // Minimum trade notional
  PORTFOLIO_RISK_BUDGET: 1.50,  // 150% - allow positions to exceed equity
  MIN_EXPECTED_EDGE_GBP: 0.001, // Require positive edge
  DEFAULT_WIN_PROB: 0.55,       // Target win probability
  WIN_RATE_CONFIDENCE_TRADES: 25,
  
  // ═══════════════════════════════════════════════════════════════
  // TRAILING STOP CONFIGURATION
  // ═══════════════════════════════════════════════════════════════
  ENABLE_TRAILING_STOP: true,
  TRAILING_ACTIVATION_PCT: 0.8,  // Activate at 0.8% profit
  TRAILING_DISTANCE_PCT: 0.5,    // Trail 0.5% behind peak
  USE_ATR_TRAILING: true,
  ATR_TRAIL_MULTIPLIER: 1.5,
  
  // ═══════════════════════════════════════════════════════════════
  // DYNAMIC PORTFOLIO REBALANCING
  // ═══════════════════════════════════════════════════════════════
  ENABLE_REBALANCING: true,
  REBALANCE_THRESHOLD: -2.0,    // Sell if losing >2%
  MIN_HOLD_CYCLES: 10,          // Hold at least 10 cycles
  QUOTE_CURRENCIES: ['USDC', 'USDT', 'GBP', 'USD', 'EUR', 'BTC', 'ETH'],
  
  // ═══════════════════════════════════════════════════════════════
  // KELLY CRITERION & RISK MANAGEMENT
  // ═══════════════════════════════════════════════════════════════
  USE_KELLY_SIZING: true,
  KELLY_SAFETY_FACTOR: 0.5,     // Half-Kelly for safety
  BASE_POSITION_SIZE: 0.10,     // Base size when Kelly disabled
  MAX_POSITION_SIZE: 0.25,      // Hard cap per trade
  MAX_SYMBOL_EXPOSURE: 0.30,    // Max 30% in one symbol
  MAX_DRAWDOWN_PCT: 50.0,       // Circuit breaker at 50% DD
  MIN_NETWORK_COHERENCE: 0.20,  // Minimum coherence to trade
  
  // ═══════════════════════════════════════════════════════════════
  // OPPORTUNITY FILTERS
  // ═══════════════════════════════════════════════════════════════
  MIN_MOMENTUM: 0.5,            // Require positive momentum
  MAX_MOMENTUM: 50.0,           // Avoid parabolic pumps
  MIN_VOLUME: 20000,            // Minimum volume
  MIN_SCORE: 40,                // Minimum opportunity score
  
  // ═══════════════════════════════════════════════════════════════
  // COHERENCE THRESHOLDS - OPTIMAL WIN RATE MODE
  // ═══════════════════════════════════════════════════════════════
  HIGH_COHERENCE_MODE: false,
  ENTRY_COHERENCE: 0.20,        // Minimum coherence to enter
  EXIT_COHERENCE: 0.15,         // Exit when coherence drops below
  
  // ═══════════════════════════════════════════════════════════════
  // LAMBDA FIELD COMPONENTS Λ(t) = S(t) + O(t) + E(t) + H(t)
  // ═══════════════════════════════════════════════════════════════
  ENABLE_LAMBDA_FIELD: true,
  OBSERVER_WEIGHT: 0.3,         // O(t) = Λ(t-1) × 0.3 (self-reference)
  ECHO_WEIGHT: 0.2,             // E(t) = avg(Λ[t-5:t]) × 0.2 (memory)
  
  // ═══════════════════════════════════════════════════════════════
  // HNC FREQUENCY INTEGRATION
  // ═══════════════════════════════════════════════════════════════
  ENABLE_HNC_FREQUENCY: true,
  HNC_FREQUENCY_WEIGHT: 0.25,   // H(t) weight in Lambda field
  HNC_COHERENCE_THRESHOLD: 0.50,
  HNC_HARMONIC_BONUS: 1.15,     // 15% bonus for harmonic resonance
  HNC_DISTORTION_PENALTY: 0.70, // 30% penalty for 440 Hz distortion
  
  // ═══════════════════════════════════════════════════════════════
  // FREQUENCY FILTERING OPTIMIZATION
  // ═══════════════════════════════════════════════════════════════
  ENABLE_FREQUENCY_FILTERING: true,
  FREQUENCY_BOOST_300HZ: 1.50,       // 50% boost for 300-399Hz (98.8% accuracy!)
  FREQUENCY_BOOST_528HZ: 1.35,       // 35% boost for 528Hz Love Frequency
  FREQUENCY_SUPPRESS_963HZ: 0.6,     // 40% suppression for 963Hz
  FREQUENCY_SUPPRESS_600HZ: 0.75,    // 25% suppression for 600-699Hz
  FREQUENCY_NEUTRAL_BASELINE: 1.0,
  FREQUENCY_WIN_RATE_TARGET: 0.60,
  
  // 🎵 SOLFEGGIO FREQUENCY BOOSTS
  FREQUENCY_BOOST_174HZ: 1.20,       // Pain Relief, Foundation
  FREQUENCY_BOOST_285HZ: 1.25,       // Healing, Tissue Regeneration
  FREQUENCY_BOOST_396HZ: 1.40,       // Liberation from Fear/Guilt
  FREQUENCY_BOOST_417HZ: 1.30,       // Undoing Situations, Change
  FREQUENCY_BOOST_639HZ: 1.25,       // Connection, Relationships
  FREQUENCY_BOOST_741HZ: 1.15,       // Awakening Intuition
  FREQUENCY_BOOST_852HZ: 1.20,       // Returning to Spiritual Order
  
  // 🌍 EARTH & COSMIC FREQUENCIES
  FREQUENCY_BOOST_SCHUMANN: 1.45,    // 7.83Hz - Earth's heartbeat
  FREQUENCY_BOOST_432HZ: 1.30,       // Universal tuning
  FREQUENCY_BOOST_136HZ: 1.25,       // OM, Earth's year frequency
  
  // 🔴 DISTORTION FREQUENCIES (AVOID)
  FREQUENCY_SUPPRESS_440HZ: 0.70,    // Artificial concert pitch
  FREQUENCY_SUPPRESS_HIGH_CHAOS: 0.50, // 1000+Hz - Chaotic
  
  // ═══════════════════════════════════════════════════════════════
  // HNC PROBABILITY MATRIX (2-Hour Window)
  // ═══════════════════════════════════════════════════════════════
  ENABLE_PROB_MATRIX: true,
  PROB_MIN_CONFIDENCE: 0.45,
  PROB_HIGH_THRESHOLD: 0.65,
  PROB_LOW_THRESHOLD: 0.40,
  PROB_LOOKBACK_MINUTES: 60,
  PROB_FORECAST_WEIGHT: 0.4,
  
  // ═══════════════════════════════════════════════════════════════
  // IMPERIAL PREDICTABILITY ENGINE
  // ═══════════════════════════════════════════════════════════════
  ENABLE_IMPERIAL: true,
  IMPERIAL_POSITION_WEIGHT: 0.35,
  IMPERIAL_MIN_COHERENCE: 0.30,
  IMPERIAL_DISTORTION_LIMIT: 0.50,
  IMPERIAL_COSMIC_BOOST: true,
  IMPERIAL_YIELD_THRESHOLD: 1e30,
  
  // ═══════════════════════════════════════════════════════════════
  // EARTH RESONANCE ENGINE
  // ═══════════════════════════════════════════════════════════════
  ENABLE_EARTH_RESONANCE: true,
  EARTH_COHERENCE_THRESHOLD: 0.50,
  EARTH_PHASE_LOCK_THRESHOLD: 0.60,
  EARTH_PHI_AMPLIFICATION: true,
  EARTH_SENTIMENT_MAPPING: true,
  EARTH_EXIT_URGENCY: true,
  
  // ═══════════════════════════════════════════════════════════════
  // QUANTUM TELESCOPE
  // ═══════════════════════════════════════════════════════════════
  ENABLE_QUANTUM_TELESCOPE: true,
  ENABLE_HARMONIC_UNDERLAY: true,
  QUANTUM_WEIGHT: 0.15,
  HARMONIC_WEIGHT: 0.20,
  HARMONIC_GATE: 0.30,
  HARMONIC_PROB_MIN: 0.40,
  OPTIMAL_MIN_GATES: 2,
  OPTIMAL_MIN_COHERENCE: 0.35,
  OPTIMAL_TREND_CONFIRM: true,
  OPTIMAL_MULTI_TF_CHECK: true,
  
  // ═══════════════════════════════════════════════════════════════
  // COMPOUNDING (10-9-1 Model)
  // ═══════════════════════════════════════════════════════════════
  COMPOUND_PCT: 0.90,           // 90% compounds
  HARVEST_PCT: 0.10,            // 10% harvests
  
  // ═══════════════════════════════════════════════════════════════
  // AURIS NODE FREQUENCIES (Hz)
  // ═══════════════════════════════════════════════════════════════
  FREQ_TIGER: 741.0,
  FREQ_FALCON: 852.0,
  FREQ_HUMMINGBIRD: 963.0,
  FREQ_DOLPHIN: 528.0,
  FREQ_DEER: 396.0,
  FREQ_OWL: 432.0,
  FREQ_PANDA: 412.3,
  FREQ_CARGOSHIP: 174.0,
  FREQ_CLOWNFISH: 639.0,
  
  // ═══════════════════════════════════════════════════════════════
  // ELEPHANT MEMORY (Quackers)
  // ═══════════════════════════════════════════════════════════════
  LOSS_STREAK_LIMIT: 3,
  COOLDOWN_MINUTES: 13,         // Fibonacci timing
  
  // ═══════════════════════════════════════════════════════════════
  // SYSTEM FLUX PREDICTION
  // ═══════════════════════════════════════════════════════════════
  FLUX_SPAN: 30,
  FLUX_THRESHOLD: 0.60,
  
  // ═══════════════════════════════════════════════════════════════
  // GOLDEN RATIO
  // ═══════════════════════════════════════════════════════════════
  PHI: 1.618033988749895,
} as const;

export type EcosystemConfigType = typeof ECOSYSTEM_CONFIG;

/**
 * Get frequency modifier for a given frequency
 */
export function getFrequencyModifier(frequency: number): number {
  const config = ECOSYSTEM_CONFIG;
  
  // Solfeggio frequencies
  if (frequency >= 170 && frequency <= 180) return config.FREQUENCY_BOOST_174HZ;
  if (frequency >= 280 && frequency <= 290) return config.FREQUENCY_BOOST_285HZ;
  if (frequency >= 300 && frequency <= 399) return config.FREQUENCY_BOOST_300HZ;
  if (frequency >= 390 && frequency <= 400) return config.FREQUENCY_BOOST_396HZ;
  if (frequency >= 413 && frequency <= 422) return config.FREQUENCY_BOOST_417HZ;
  if (frequency >= 428 && frequency <= 436) return config.FREQUENCY_BOOST_432HZ;
  if (frequency >= 437 && frequency <= 443) return config.FREQUENCY_SUPPRESS_440HZ;
  if (frequency >= 524 && frequency <= 532) return config.FREQUENCY_BOOST_528HZ;
  if (frequency >= 600 && frequency <= 699) return config.FREQUENCY_SUPPRESS_600HZ;
  if (frequency >= 635 && frequency <= 643) return config.FREQUENCY_BOOST_639HZ;
  if (frequency >= 737 && frequency <= 745) return config.FREQUENCY_BOOST_741HZ;
  if (frequency >= 848 && frequency <= 856) return config.FREQUENCY_BOOST_852HZ;
  if (frequency >= 959 && frequency <= 967) return config.FREQUENCY_SUPPRESS_963HZ;
  if (frequency >= 1000) return config.FREQUENCY_SUPPRESS_HIGH_CHAOS;
  
  // Schumann and harmonics
  if (frequency >= 7.5 && frequency <= 8.1) return config.FREQUENCY_BOOST_SCHUMANN;
  if (frequency >= 132 && frequency <= 140) return config.FREQUENCY_BOOST_136HZ;
  
  return config.FREQUENCY_NEUTRAL_BASELINE;
}

/**
 * Get exchange fee for a given exchange
 */
export function getExchangeFee(exchange: string, maker: boolean = false): number {
  const config = ECOSYSTEM_CONFIG;
  const ex = exchange.toLowerCase();
  
  switch (ex) {
    case 'binance':
      return maker ? config.BINANCE_FEE_MAKER : config.BINANCE_FEE_TAKER;
    case 'kraken':
      return maker ? config.KRAKEN_FEE_MAKER : config.KRAKEN_FEE_TAKER;
    case 'alpaca':
      return maker ? config.ALPACA_FEE_MAKER : config.ALPACA_FEE_TAKER;
    case 'capital':
      return config.CAPITAL_FEE_SPREAD;
    default:
      return 0.002; // 0.2% default
  }
}

/**
 * Get minimum notional for a given exchange
 */
export function getMinNotional(exchange: string): number {
  const config = ECOSYSTEM_CONFIG;
  const ex = exchange.toLowerCase();
  
  switch (ex) {
    case 'binance':
      return config.BINANCE_MIN_NOTIONAL;
    case 'kraken':
      return config.KRAKEN_MIN_NOTIONAL;
    case 'alpaca':
      return config.ALPACA_MIN_NOTIONAL;
    case 'capital':
      return config.CAPITAL_MIN_NOTIONAL;
    default:
      return 5.0;
  }
}
