/**
 * Lot Size Validator
 * Validates trade quantity against exchange-specific min/max/step rules
 * 
 * Gap Closure: Matches Python aureon_unified_ecosystem.py lot size validation
 */

import { supabase } from '@/integrations/supabase/client';

export interface LotSizeRules {
  symbol: string;
  exchange: string;
  minQty: number;
  maxQty: number;
  stepSize: number;
  minNotional: number;
  tickSize: number;
  pricePrecision: number;
  quantityPrecision: number;
}

export interface LotValidationResult {
  valid: boolean;
  adjustedQuantity: number;
  adjustedPrice: number;
  error?: string;
  reason?: string;
}

// Default lot size rules per exchange (fallback if not in database)
const DEFAULT_RULES: Record<string, Partial<LotSizeRules>> = {
  binance: {
    minQty: 0.00001,
    maxQty: 10000,
    stepSize: 0.00001,
    minNotional: 10, // $10 minimum order value
    tickSize: 0.01,
  },
  kraken: {
    minQty: 0.0001,
    maxQty: 5000,
    stepSize: 0.0001,
    minNotional: 10,
    tickSize: 0.01,
  },
  alpaca: {
    minQty: 0.001,
    maxQty: 100000,
    stepSize: 0.001,
    minNotional: 1, // $1 for fractional shares
    tickSize: 0.01,
  },
  capital: {
    minQty: 0.01,
    maxQty: 10000,
    stepSize: 0.01,
    minNotional: 10,
    tickSize: 0.0001,
  },
};

class LotSizeValidator {
  private rulesCache: Map<string, LotSizeRules> = new Map();
  private lastCacheRefresh: number = 0;
  private cacheRefreshInterval: number = 60000; // 1 minute

  /**
   * Get lot size rules for a symbol from database or defaults
   */
  async getRules(symbol: string, exchange: string = 'binance'): Promise<LotSizeRules> {
    const cacheKey = `${exchange}:${symbol}`;
    
    // Check cache first
    if (this.rulesCache.has(cacheKey) && Date.now() - this.lastCacheRefresh < this.cacheRefreshInterval) {
      return this.rulesCache.get(cacheKey)!;
    }
    
    try {
      // Try to fetch from database (crypto_assets_registry)
      const { data, error } = await supabase
        .from('crypto_assets_registry')
        .select('*')
        .eq('symbol', symbol)
        .eq('exchange', exchange)
        .maybeSingle();
      
      if (data && !error) {
        const rules: LotSizeRules = {
          symbol,
          exchange,
          minQty: data.min_qty || DEFAULT_RULES[exchange]?.minQty || 0.00001,
          maxQty: data.max_qty || DEFAULT_RULES[exchange]?.maxQty || 10000,
          stepSize: data.step_size || DEFAULT_RULES[exchange]?.stepSize || 0.00001,
          minNotional: data.min_notional || DEFAULT_RULES[exchange]?.minNotional || 10,
          tickSize: data.tick_size || DEFAULT_RULES[exchange]?.tickSize || 0.01,
          pricePrecision: data.price_precision || 8,
          quantityPrecision: data.quantity_precision || 8,
        };
        
        this.rulesCache.set(cacheKey, rules);
        this.lastCacheRefresh = Date.now();
        return rules;
      }
    } catch (err) {
      console.warn('[LotSizeValidator] Database fetch failed, using defaults:', err);
    }
    
    // Use default rules
    const defaults = DEFAULT_RULES[exchange] || DEFAULT_RULES.binance;
    return {
      symbol,
      exchange,
      minQty: defaults.minQty || 0.00001,
      maxQty: defaults.maxQty || 10000,
      stepSize: defaults.stepSize || 0.00001,
      minNotional: defaults.minNotional || 10,
      tickSize: defaults.tickSize || 0.01,
      pricePrecision: 8,
      quantityPrecision: 8,
    };
  }

  /**
   * Round quantity to step size (like Python's normalize_quantity)
   */
  roundToStepSize(quantity: number, stepSize: number): number {
    if (stepSize <= 0) return quantity;
    return Math.floor(quantity / stepSize) * stepSize;
  }

  /**
   * Round price to tick size
   */
  roundToTickSize(price: number, tickSize: number): number {
    if (tickSize <= 0) return price;
    return Math.round(price / tickSize) * tickSize;
  }

  /**
   * Validate and adjust order quantity
   */
  async validate(
    symbol: string,
    quantity: number,
    price: number,
    exchange: string = 'binance'
  ): Promise<LotValidationResult> {
    const rules = await this.getRules(symbol, exchange);
    
    // Round to step size
    let adjustedQuantity = this.roundToStepSize(quantity, rules.stepSize);
    
    // Round price to tick size
    const adjustedPrice = this.roundToTickSize(price, rules.tickSize);
    
    // Check minimum quantity
    if (adjustedQuantity < rules.minQty) {
      return {
        valid: false,
        adjustedQuantity: 0,
        adjustedPrice,
        error: `Quantity ${adjustedQuantity} below minimum ${rules.minQty}`,
        reason: 'BELOW_MIN_QTY',
      };
    }
    
    // Check maximum quantity
    if (adjustedQuantity > rules.maxQty) {
      adjustedQuantity = rules.maxQty;
      console.log(`[LotSizeValidator] Quantity capped to max: ${rules.maxQty}`);
    }
    
    // Check minimum notional (order value)
    const notionalValue = adjustedQuantity * adjustedPrice;
    if (notionalValue < rules.minNotional) {
      // Try to adjust quantity to meet minimum notional
      const requiredQty = this.roundToStepSize(rules.minNotional / adjustedPrice, rules.stepSize);
      
      if (requiredQty > rules.maxQty) {
        return {
          valid: false,
          adjustedQuantity: 0,
          adjustedPrice,
          error: `Order value $${notionalValue.toFixed(2)} below minimum $${rules.minNotional}`,
          reason: 'BELOW_MIN_NOTIONAL',
        };
      }
      
      adjustedQuantity = requiredQty;
      console.log(`[LotSizeValidator] Quantity adjusted to meet min notional: ${adjustedQuantity}`);
    }
    
    // Final validation
    const finalNotional = adjustedQuantity * adjustedPrice;
    if (finalNotional < rules.minNotional) {
      return {
        valid: false,
        adjustedQuantity: 0,
        adjustedPrice,
        error: `Cannot meet minimum notional of $${rules.minNotional}`,
        reason: 'CANNOT_MEET_NOTIONAL',
      };
    }
    
    console.log(`[LotSizeValidator] ✅ ${symbol}@${exchange} | Qty: ${quantity.toFixed(8)} → ${adjustedQuantity.toFixed(8)} | Notional: $${finalNotional.toFixed(2)}`);
    
    return {
      valid: true,
      adjustedQuantity,
      adjustedPrice,
    };
  }

  /**
   * Format quantity with correct precision
   */
  formatQuantity(quantity: number, precision: number = 8): string {
    return quantity.toFixed(precision).replace(/\.?0+$/, '');
  }

  /**
   * Clear cache (e.g., after symbol info refresh)
   */
  clearCache(): void {
    this.rulesCache.clear();
    this.lastCacheRefresh = 0;
  }
}

export const lotSizeValidator = new LotSizeValidator();
