/**
 * User Balances Hook
 * Prime Sentinel: GARY LECKEY 02111991
 * 
 * Fetches real user balances from all connected exchanges
 */

import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/lib/supabase';

export interface AssetBalance {
  asset: string;
  free: number;
  locked: number;
  usdValue: number;
}

export interface ExchangeBalance {
  exchange: string;
  connected: boolean;
  assets: AssetBalance[];
  totalUsd: number;
  error?: string;
}

export interface UserBalancesState {
  balances: ExchangeBalance[];
  totalEquityUsd: number;
  connectedExchanges: string[];
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
}

export function useUserBalances(autoRefresh: boolean = true, refreshInterval: number = 30000) {
  const [state, setState] = useState<UserBalancesState>({
    balances: [],
    totalEquityUsd: 0,
    connectedExchanges: [],
    isLoading: true,
    error: null,
    lastUpdated: null
  });
  const [fetchCount, setFetchCount] = useState(0);

  const fetchBalances = useCallback(async () => {
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        // Not authenticated - silently skip without error
        setState(prev => ({ ...prev, isLoading: false }));
        return;
      }
      
      setState(prev => ({ ...prev, isLoading: true, error: null }));

      const { data, error } = await supabase.functions.invoke('get-user-balances', {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (error) {
        throw new Error(error.message || 'Failed to fetch balances');
      }

      if (data?.success) {
        setFetchCount(c => c + 1);
        console.log(`[useUserBalances] Fetch #${fetchCount + 1}: $${data.totalEquityUsd?.toFixed(2)} from ${data.connectedExchanges?.length || 0} exchanges`);
        
        setState({
          balances: data.balances || [],
          totalEquityUsd: data.totalEquityUsd || 0,
          connectedExchanges: data.connectedExchanges || [],
          isLoading: false,
          error: null,
          lastUpdated: new Date()
        });
      } else {
        throw new Error(data?.error || 'Failed to fetch balances');
      }
    } catch (err) {
      console.error('[useUserBalances] Error:', err);
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: err instanceof Error ? err.message : 'Unknown error'
      }));
    }
  }, [fetchCount]);

  // Initial fetch and auto-refresh
  useEffect(() => {
    fetchBalances();

    if (autoRefresh && refreshInterval > 0) {
      const interval = setInterval(fetchBalances, refreshInterval);
      return () => clearInterval(interval);
    }
  }, [fetchBalances, autoRefresh, refreshInterval]);

  // Get consolidated assets across all exchanges
  const getConsolidatedAssets = useCallback(() => {
    const assetMap = new Map<string, { free: number; locked: number; usdValue: number; exchanges: string[] }>();

    for (const exchange of state.balances) {
      if (!exchange.connected) continue;
      
      for (const asset of exchange.assets) {
        const existing = assetMap.get(asset.asset);
        if (existing) {
          existing.free += asset.free;
          existing.locked += asset.locked;
          existing.usdValue += asset.usdValue;
          existing.exchanges.push(exchange.exchange);
        } else {
          assetMap.set(asset.asset, {
            free: asset.free,
            locked: asset.locked,
            usdValue: asset.usdValue,
            exchanges: [exchange.exchange]
          });
        }
      }
    }

    return Array.from(assetMap.entries())
      .map(([asset, data]) => ({ asset, ...data }))
      .sort((a, b) => b.usdValue - a.usdValue);
  }, [state.balances]);

  return {
    ...state,
    refresh: fetchBalances,
    getConsolidatedAssets
  };
}
