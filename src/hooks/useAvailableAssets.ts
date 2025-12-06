import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface CryptoAsset {
  id: string;
  symbol: string;
  baseAsset: string;
  quoteAsset: string;
  exchange: string;
  minQty?: number;
  maxQty?: number;
  stepSize?: number;
  minNotional?: number;
  tickSize?: number;
  pricePrecision?: number;
  quantityPrecision?: number;
  isActive: boolean;
  isSpotTradingAllowed: boolean;
  status: string;
  lastSyncedAt: string;
}

export interface UseAvailableAssetsResult {
  assets: CryptoAsset[];
  assetsByExchange: Record<string, CryptoAsset[]>;
  isLoading: boolean;
  lastSynced: Date | null;
  totalAssets: number;
  syncAssets: (exchanges?: string[]) => Promise<void>;
  getAssetInfo: (symbol: string, exchange?: string) => CryptoAsset | undefined;
  searchAssets: (query: string) => CryptoAsset[];
  filterByExchange: (exchange: string) => CryptoAsset[];
  filterByQuoteAsset: (quoteAsset: string) => CryptoAsset[];
}

export function useAvailableAssets(): UseAvailableAssetsResult {
  const [assets, setAssets] = useState<CryptoAsset[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastSynced, setLastSynced] = useState<Date | null>(null);

  // Load assets from database
  const loadAssets = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('crypto_assets_registry')
        .select('*')
        .eq('is_active', true)
        .order('symbol', { ascending: true });

      if (error) {
        console.error('[useAvailableAssets] Load error:', error);
        return;
      }

      const mappedAssets: CryptoAsset[] = (data || []).map(row => ({
        id: row.id,
        symbol: row.symbol,
        baseAsset: row.base_asset,
        quoteAsset: row.quote_asset,
        exchange: row.exchange,
        minQty: row.min_qty,
        maxQty: row.max_qty,
        stepSize: row.step_size,
        minNotional: row.min_notional,
        tickSize: row.tick_size,
        pricePrecision: row.price_precision,
        quantityPrecision: row.quantity_precision,
        isActive: row.is_active,
        isSpotTradingAllowed: row.is_spot_trading_allowed,
        status: row.status,
        lastSyncedAt: row.last_synced_at,
      }));

      setAssets(mappedAssets);
      
      if (mappedAssets.length > 0) {
        const latestSync = mappedAssets.reduce((latest, asset) => {
          const assetDate = new Date(asset.lastSyncedAt);
          return assetDate > latest ? assetDate : latest;
        }, new Date(0));
        setLastSynced(latestSync);
      }
    } catch (error) {
      console.error('[useAvailableAssets] Error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Sync assets from exchanges
  const syncAssets = useCallback(async (exchanges: string[] = ['binance', 'kraken']) => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('sync-exchange-assets', {
        body: { exchanges },
      });

      if (error) {
        console.error('[useAvailableAssets] Sync error:', error);
        throw error;
      }

      console.log('[useAvailableAssets] Sync result:', data);
      
      // Reload assets after sync
      await loadAssets();
    } catch (error) {
      console.error('[useAvailableAssets] Sync failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [loadAssets]);

  // Initial load
  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  // Subscribe to realtime updates
  useEffect(() => {
    const channel = supabase
      .channel('crypto-assets-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'crypto_assets_registry',
        },
        () => {
          loadAssets();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [loadAssets]);

  // Group assets by exchange
  const assetsByExchange = useMemo(() => {
    return assets.reduce((acc, asset) => {
      if (!acc[asset.exchange]) {
        acc[asset.exchange] = [];
      }
      acc[asset.exchange].push(asset);
      return acc;
    }, {} as Record<string, CryptoAsset[]>);
  }, [assets]);

  // Get specific asset info
  const getAssetInfo = useCallback((symbol: string, exchange?: string): CryptoAsset | undefined => {
    if (exchange) {
      return assets.find(a => a.symbol === symbol && a.exchange === exchange);
    }
    return assets.find(a => a.symbol === symbol);
  }, [assets]);

  // Search assets by query
  const searchAssets = useCallback((query: string): CryptoAsset[] => {
    const lowerQuery = query.toLowerCase();
    return assets.filter(a => 
      a.symbol.toLowerCase().includes(lowerQuery) ||
      a.baseAsset.toLowerCase().includes(lowerQuery)
    );
  }, [assets]);

  // Filter by exchange
  const filterByExchange = useCallback((exchange: string): CryptoAsset[] => {
    return assets.filter(a => a.exchange === exchange);
  }, [assets]);

  // Filter by quote asset
  const filterByQuoteAsset = useCallback((quoteAsset: string): CryptoAsset[] => {
    return assets.filter(a => a.quoteAsset === quoteAsset);
  }, [assets]);

  return {
    assets,
    assetsByExchange,
    isLoading,
    lastSynced,
    totalAssets: assets.length,
    syncAssets,
    getAssetInfo,
    searchAssets,
    filterByExchange,
    filterByQuoteAsset,
  };
}
