/**
 * Market Data Validation Layer
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Validates all incoming market data packets for:
 * - Timestamp freshness (< 10 seconds old)
 * - Price sanity (non-zero, within 50% of previous)
 * - Volume validity (positive number)
 * - Source identification
 */

export interface MarketPacket {
  symbol: string;
  exchange: string;
  price: number;
  volume?: number;
  volatility?: number;
  momentum?: number;
  timestamp: number;
  bidPrice?: number;
  askPrice?: number;
  high24h?: number;
  low24h?: number;
  priceChange24h?: number;
  spread?: number;
}

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
  freshness: 'live' | 'stale' | 'expired';
  freshnessMs: number;
  confidence: number;
}

export interface ExchangeValidationStatus {
  exchange: string;
  lastValidTimestamp: number;
  lastPrice: number;
  isStale: boolean;
  errorCount: number;
  consecutiveErrors: number;
  lastError?: string;
}

// Price history cache for sanity checks
const priceHistory: Map<string, { price: number; timestamp: number }[]> = new Map();

// Exchange status tracking
const exchangeStatus: Map<string, ExchangeValidationStatus> = new Map();

// Validation thresholds
const FRESHNESS_THRESHOLD_MS = 10000; // 10 seconds
const STALE_THRESHOLD_MS = 30000; // 30 seconds
const EXPIRED_THRESHOLD_MS = 60000; // 60 seconds
const MAX_PRICE_DEVIATION = 0.5; // 50% max deviation from previous
const MAX_HISTORY_SIZE = 100;

/**
 * Validate a market data packet
 */
export function validateMarketPacket(packet: MarketPacket): ValidationResult {
  const errors: string[] = [];
  const warnings: string[] = [];
  const now = Date.now();
  
  // 1. Timestamp freshness
  const freshnessMs = now - packet.timestamp;
  let freshness: 'live' | 'stale' | 'expired' = 'live';
  
  if (freshnessMs > EXPIRED_THRESHOLD_MS) {
    freshness = 'expired';
    errors.push(`Data expired: ${(freshnessMs / 1000).toFixed(1)}s old`);
  } else if (freshnessMs > STALE_THRESHOLD_MS) {
    freshness = 'stale';
    warnings.push(`Data stale: ${(freshnessMs / 1000).toFixed(1)}s old`);
  } else if (freshnessMs > FRESHNESS_THRESHOLD_MS) {
    warnings.push(`Data slightly delayed: ${(freshnessMs / 1000).toFixed(1)}s old`);
  }
  
  // 2. Price sanity
  if (!packet.price || packet.price <= 0) {
    errors.push('Invalid price: must be positive');
  } else if (!isFinite(packet.price)) {
    errors.push('Invalid price: not a finite number');
  } else {
    // Check against price history
    const historyKey = `${packet.exchange}:${packet.symbol}`;
    const history = priceHistory.get(historyKey) || [];
    
    if (history.length > 0) {
      const lastPrice = history[history.length - 1].price;
      const deviation = Math.abs(packet.price - lastPrice) / lastPrice;
      
      if (deviation > MAX_PRICE_DEVIATION) {
        warnings.push(`Price deviation ${(deviation * 100).toFixed(1)}% from last: ${lastPrice} → ${packet.price}`);
      }
    }
    
    // Update history
    history.push({ price: packet.price, timestamp: packet.timestamp });
    if (history.length > MAX_HISTORY_SIZE) {
      history.shift();
    }
    priceHistory.set(historyKey, history);
  }
  
  // 3. Volume validity
  if (packet.volume !== undefined) {
    if (packet.volume < 0) {
      errors.push('Invalid volume: must be non-negative');
    } else if (packet.volume === 0) {
      warnings.push('Zero volume detected');
    }
  }
  
  // 4. Spread validation
  if (packet.bidPrice && packet.askPrice) {
    if (packet.bidPrice > packet.askPrice) {
      errors.push('Invalid spread: bid > ask');
    }
    const spreadPct = (packet.askPrice - packet.bidPrice) / packet.price;
    if (spreadPct > 0.1) {
      warnings.push(`Wide spread: ${(spreadPct * 100).toFixed(2)}%`);
    }
  }
  
  // 5. Volatility sanity
  if (packet.volatility !== undefined) {
    if (packet.volatility < 0) {
      errors.push('Invalid volatility: must be non-negative');
    } else if (packet.volatility > 1) {
      warnings.push(`Extreme volatility: ${(packet.volatility * 100).toFixed(1)}%`);
    }
  }
  
  // 6. Exchange source validation
  if (!packet.exchange) {
    warnings.push('Missing exchange identifier');
  }
  
  // Update exchange status
  updateExchangeStatus(packet, errors.length === 0, errors[0]);
  
  // Calculate confidence
  const confidence = calculateConfidence(errors.length, warnings.length, freshness);
  
  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    freshness,
    freshnessMs,
    confidence,
  };
}

/**
 * Update exchange status tracking
 */
function updateExchangeStatus(packet: MarketPacket, isValid: boolean, error?: string): void {
  const existing = exchangeStatus.get(packet.exchange);
  
  if (existing) {
    if (isValid) {
      existing.lastValidTimestamp = packet.timestamp;
      existing.lastPrice = packet.price;
      existing.isStale = false;
      existing.consecutiveErrors = 0;
    } else {
      existing.errorCount++;
      existing.consecutiveErrors++;
      existing.lastError = error;
      if (Date.now() - existing.lastValidTimestamp > STALE_THRESHOLD_MS) {
        existing.isStale = true;
      }
    }
  } else {
    exchangeStatus.set(packet.exchange, {
      exchange: packet.exchange,
      lastValidTimestamp: isValid ? packet.timestamp : 0,
      lastPrice: packet.price,
      isStale: !isValid,
      errorCount: isValid ? 0 : 1,
      consecutiveErrors: isValid ? 0 : 1,
      lastError: error,
    });
  }
}

/**
 * Calculate confidence score
 */
function calculateConfidence(errorCount: number, warningCount: number, freshness: string): number {
  let confidence = 1.0;
  
  // Deduct for errors (major)
  confidence -= errorCount * 0.3;
  
  // Deduct for warnings (minor)
  confidence -= warningCount * 0.05;
  
  // Deduct for staleness
  if (freshness === 'stale') confidence -= 0.2;
  if (freshness === 'expired') confidence -= 0.5;
  
  return Math.max(0, Math.min(1, confidence));
}

/**
 * Get all exchange statuses
 */
export function getExchangeStatuses(): ExchangeValidationStatus[] {
  return Array.from(exchangeStatus.values());
}

/**
 * Get status for specific exchange
 */
export function getExchangeStatus(exchange: string): ExchangeValidationStatus | undefined {
  return exchangeStatus.get(exchange);
}

/**
 * Check if any exchange has stale data
 */
export function hasStaleData(): boolean {
  return Array.from(exchangeStatus.values()).some(s => s.isStale);
}

/**
 * Get overall data health score
 */
export function getDataHealthScore(): { score: number; status: 'healthy' | 'degraded' | 'critical' } {
  const statuses = Array.from(exchangeStatus.values());
  
  if (statuses.length === 0) {
    return { score: 0, status: 'critical' };
  }
  
  const healthyCount = statuses.filter(s => !s.isStale && s.consecutiveErrors === 0).length;
  const score = healthyCount / statuses.length;
  
  let status: 'healthy' | 'degraded' | 'critical' = 'healthy';
  if (score < 0.5) status = 'critical';
  else if (score < 0.8) status = 'degraded';
  
  return { score, status };
}

/**
 * Clear validation history (for testing)
 */
export function clearValidationHistory(): void {
  priceHistory.clear();
  exchangeStatus.clear();
}
