/**
 * Startup Harvester
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * On system startup, scans existing exchange holdings
 * and sells any that are in profit to harvest gains
 * Like Python aureon_unified_ecosystem.py harvest_existing_assets()
 */

import { supabase } from '@/integrations/supabase/client';
import { unifiedBus } from './unifiedBus';
import { temporalLadder, SYSTEMS } from './temporalLadder';
import { elephantMemory } from './elephantMemory';
import { capitalPool } from './capitalPool';

export interface HarvestCandidate {
  symbol: string;
  asset: string;
  exchange: string;
  quantity: number;
  currentPrice: number;
  valueUsd: number;
  avgCost: number | null;
  unrealizedPnL: number;
  unrealizedPnLPct: number;
  shouldHarvest: boolean;
  reason: string;
}

export interface HarvestResult {
  scanned: number;
  harvested: number;
  totalValue: number;
  totalProfit: number;
  candidates: HarvestCandidate[];
  executed: HarvestCandidate[];
  errors: string[];
}

const HARVEST_CONFIG = {
  minProfitPct: 0.5, // Min 0.5% profit to harvest
  minValueUsd: 10, // Min $10 value to consider
  excludeAssets: ['USDT', 'USDC', 'BUSD', 'USD', 'EUR', 'GBP'], // Don't sell stablecoins
  maxHarvestPct: 0.50, // Max 50% of any asset to harvest
};

class StartupHarvester {
  private hasRun: boolean = false;
  private lastResult: HarvestResult | null = null;

  constructor() {
    console.log('🌾 Startup Harvester initialized');
  }

  /**
   * Scan exchange balances for harvest candidates
   */
  async scanForHarvest(): Promise<HarvestCandidate[]> {
    const candidates: HarvestCandidate[] = [];

    try {
      // Get current session
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        console.warn('[Harvester] No auth session');
        return [];
      }

      // Fetch balances from edge function
      const { data, error } = await supabase.functions.invoke('get-user-balances', {
        body: { userId: session.user.id }
      });

      if (error || !data?.success) {
        console.error('[Harvester] Failed to fetch balances:', error?.message || data?.error);
        return [];
      }

      const balances = data.balances || [];
      
      for (const balance of balances) {
        const { asset, free, exchange, usdValue } = balance;
        
        // Skip stablecoins and low values
        if (HARVEST_CONFIG.excludeAssets.includes(asset)) continue;
        if (usdValue < HARVEST_CONFIG.minValueUsd) continue;
        if (free <= 0) continue;

        // Get memory for this symbol
        const symbol = `${asset}USDT`;
        const memory = elephantMemory.getSymbolMemory(symbol);
        
        // Estimate profit (use elephant memory if available)
        let avgCost: number | null = null;
        let unrealizedPnL = 0;
        let unrealizedPnLPct = 0;

        if (memory && memory.trades > 0) {
          // Rough estimate based on elephant memory
          avgCost = memory.profit / memory.trades;
          unrealizedPnL = memory.profit;
          unrealizedPnLPct = memory.profit / Math.max(usdValue - memory.profit, 1) * 100;
        }

        // Should harvest if in sufficient profit
        const shouldHarvest = unrealizedPnLPct >= HARVEST_CONFIG.minProfitPct;
        
        candidates.push({
          symbol,
          asset,
          exchange,
          quantity: free,
          currentPrice: usdValue / free,
          valueUsd: usdValue,
          avgCost,
          unrealizedPnL,
          unrealizedPnLPct,
          shouldHarvest,
          reason: shouldHarvest 
            ? `Profit ${unrealizedPnLPct.toFixed(2)}% >= ${HARVEST_CONFIG.minProfitPct}%` 
            : unrealizedPnLPct < HARVEST_CONFIG.minProfitPct 
              ? `Profit ${unrealizedPnLPct.toFixed(2)}% < ${HARVEST_CONFIG.minProfitPct}%`
              : 'Unknown cost basis',
        });
      }

      console.log(`[Harvester] Found ${candidates.length} candidates, ${candidates.filter(c => c.shouldHarvest).length} eligible for harvest`);
      return candidates;

    } catch (error) {
      console.error('[Harvester] Scan error:', error);
      return [];
    }
  }

  /**
   * Execute harvest on profitable positions
   */
  async harvest(dryRun: boolean = true): Promise<HarvestResult> {
    const result: HarvestResult = {
      scanned: 0,
      harvested: 0,
      totalValue: 0,
      totalProfit: 0,
      candidates: [],
      executed: [],
      errors: [],
    };

    try {
      // Scan for candidates
      const candidates = await this.scanForHarvest();
      result.candidates = candidates;
      result.scanned = candidates.length;
      result.totalValue = candidates.reduce((sum, c) => sum + c.valueUsd, 0);

      // Filter to harvestable
      const toHarvest = candidates.filter(c => c.shouldHarvest);
      
      if (toHarvest.length === 0) {
        console.log('[Harvester] No positions eligible for harvest');
        this.publishState(result);
        return result;
      }

      console.log(`[Harvester] ${toHarvest.length} positions eligible for harvest`);

      if (dryRun) {
        console.log('[Harvester] DRY RUN - No trades executed');
        result.executed = toHarvest;
        result.harvested = toHarvest.length;
        result.totalProfit = toHarvest.reduce((sum, c) => sum + c.unrealizedPnL, 0);
      } else {
        // Execute sells
        for (const candidate of toHarvest) {
          try {
            const sellQty = candidate.quantity * HARVEST_CONFIG.maxHarvestPct;
            
            const { data, error } = await supabase.functions.invoke('execute-trade', {
              body: {
                symbol: candidate.symbol,
                signalType: 'SHORT', // SELL
                quantity: sellQty,
                price: candidate.currentPrice,
                recommendedExchange: candidate.exchange,
              }
            });

            if (error || !data?.success) {
              result.errors.push(`${candidate.symbol}: ${error?.message || data?.error}`);
              continue;
            }

            result.executed.push(candidate);
            result.harvested++;
            result.totalProfit += candidate.unrealizedPnL * HARVEST_CONFIG.maxHarvestPct;

            // Update elephant memory
            elephantMemory.recordTrade(
              candidate.symbol, 
              candidate.unrealizedPnL * HARVEST_CONFIG.maxHarvestPct,
              'SELL'
            );

            // Release from capital pool
            capitalPool.release(candidate.symbol, candidate.unrealizedPnL * HARVEST_CONFIG.maxHarvestPct);

            console.log(`[Harvester] Harvested ${candidate.symbol} | Qty: ${sellQty.toFixed(6)} | Profit: $${(candidate.unrealizedPnL * HARVEST_CONFIG.maxHarvestPct).toFixed(2)}`);

          } catch (error: any) {
            result.errors.push(`${candidate.symbol}: ${error.message}`);
          }
        }
      }

      this.lastResult = result;
      this.hasRun = true;
      this.publishState(result);

      console.log(`[Harvester] Complete | Scanned: ${result.scanned} | Harvested: ${result.harvested} | Profit: $${result.totalProfit.toFixed(2)}`);

    } catch (error: any) {
      console.error('[Harvester] Harvest error:', error);
      result.errors.push(error.message);
    }

    return result;
  }

  /**
   * Run harvest on startup (once only)
   */
  async runOnStartup(dryRun: boolean = true): Promise<HarvestResult | null> {
    if (this.hasRun) {
      console.log('[Harvester] Already ran on startup, skipping');
      return this.lastResult;
    }

    console.log('[Harvester] Running startup harvest...');
    return this.harvest(dryRun);
  }

  /**
   * Get last harvest result
   */
  getLastResult(): HarvestResult | null {
    return this.lastResult;
  }

  private publishState(result: HarvestResult): void {
    unifiedBus.publish({
      systemName: 'StartupHarvester',
      timestamp: Date.now(),
      ready: true,
      coherence: result.harvested > 0 ? 0.95 : 0.7,
      confidence: result.errors.length === 0 ? 0.9 : 0.5,
      signal: 'NEUTRAL',
      data: {
        scanned: result.scanned,
        harvested: result.harvested,
        totalProfit: result.totalProfit,
        errors: result.errors.length,
      },
    });

    temporalLadder.heartbeat(SYSTEMS.STARTUP_HARVESTER, result.errors.length === 0 ? 0.9 : 0.5);
  }
}

export const startupHarvester = new StartupHarvester();
