/**
 * Multi-Exchange Balances Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * React hook for managing multi-exchange balances
 */

import { useState, useEffect, useCallback } from 'react';
import { multiExchangeClient, MultiExchangeState, ConsolidatedBalance, ExchangeStatus } from '../core/multiExchangeClient';
import { smartOrderRouter, RoutingDecision } from '../core/smartOrderRouter';
import { ExchangeType } from '../core/unifiedExchangeClient';

export interface UseMultiExchangeBalancesResult {
  state: MultiExchangeState | null;
  consolidatedBalances: ConsolidatedBalance[];
  exchangeStatuses: ExchangeStatus[];
  totalEquityUsd: number;
  isLoading: boolean;
  error: string | null;
  refresh: () => Promise<void>;
  getRouting: (symbol: string, side: 'BUY' | 'SELL', quantity: number) => Promise<RoutingDecision | null>;
  lastRoutingDecision: RoutingDecision | null;
  getPositionSize: (riskPercentage?: number) => { positionSizeUsd: number; availableBalance: number; riskAmount: number };
}

export function useMultiExchangeBalances(): UseMultiExchangeBalancesResult {
  const [state, setState] = useState<MultiExchangeState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastRoutingDecision, setLastRoutingDecision] = useState<RoutingDecision | null>(null);

  useEffect(() => {
    // Initialize multi-exchange client
    multiExchangeClient.initialize().catch(console.error);

    // Subscribe to state updates
    const unsubscribe = multiExchangeClient.subscribe((newState) => {
      setState(newState);
      setIsLoading(false);
      setError(null);
    });

    // Initial fetch
    setIsLoading(true);
    multiExchangeClient.fetchAllBalances()
      .then(setState)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to fetch balances');
      })
      .finally(() => setIsLoading(false));

    return () => {
      unsubscribe();
    };
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const newState = await multiExchangeClient.fetchAllBalances();
      setState(newState);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh balances');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const getRouting = useCallback(async (
    symbol: string,
    side: 'BUY' | 'SELL',
    quantity: number
  ): Promise<RoutingDecision | null> => {
    try {
      const decision = await smartOrderRouter.getBestQuote(symbol, side, quantity);
      setLastRoutingDecision(decision);
      return decision;
    } catch (err) {
      console.error('Routing error:', err);
      return null;
    }
  }, []);

  const getPositionSize = useCallback((riskPercentage: number = 0.02) => {
    return multiExchangeClient.calculatePositionSize(riskPercentage, 'USDT');
  }, []);

  return {
    state,
    consolidatedBalances: state?.consolidatedBalances || [],
    exchangeStatuses: state?.exchanges || [],
    totalEquityUsd: state?.totalEquityUsd || 0,
    isLoading,
    error,
    refresh,
    getRouting,
    lastRoutingDecision,
    getPositionSize
  };
}

/**
 * Hook for getting balance for a specific asset across exchanges
 */
export function useAssetBalance(asset: string) {
  const { consolidatedBalances } = useMultiExchangeBalances();
  
  const balance = consolidatedBalances.find(b => b.asset === asset);
  
  return {
    asset,
    totalFree: balance?.totalFree || 0,
    totalLocked: balance?.totalLocked || 0,
    grandTotal: balance?.grandTotal || 0,
    usdValue: balance?.usdValue || 0,
    byExchange: balance?.balances || {}
  };
}

/**
 * Hook for exchange status only
 */
export function useExchangeStatus(exchange: ExchangeType) {
  const { exchangeStatuses } = useMultiExchangeBalances();
  
  return exchangeStatuses.find(s => s.exchange === exchange) || {
    exchange,
    connected: false,
    lastUpdate: 0,
    balanceCount: 0,
    totalUsdValue: 0
  };
}
