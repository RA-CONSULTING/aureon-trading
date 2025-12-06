import { useState, useEffect, useCallback, useMemo } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface TradeAuditEntry {
  id: string;
  tradeId: string;
  externalOrderId: string | null;
  clientOrderId: string | null;
  stage: string;
  exchange: string;
  symbol: string;
  side: string;
  orderType: string;
  quantity: number;
  price: number | null;
  executedQty: number | null;
  executedPrice: number | null;
  commission: number | null;
  commissionAsset: string | null;
  exchangeResponse: any;
  validationStatus: string;
  validationMessage: string | null;
  errorCode: string | null;
  errorMessage: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TradeValidationStats {
  total: number;
  confirmed: number;
  pending: number;
  failed: number;
  confirmationRate: number;
  avgConfirmationTime: number;
}

export interface UseTradeValidationResult {
  trades: TradeAuditEntry[];
  stats: TradeValidationStats;
  isLoading: boolean;
  lastPolled: Date | null;
  pollConfirmations: () => Promise<void>;
  confirmTrade: (tradeId: string, orderId: string, symbol: string, exchange: string) => Promise<void>;
  filterByStatus: (status: string) => TradeAuditEntry[];
  getPendingTrades: () => TradeAuditEntry[];
  getRecentTrades: (limit?: number) => TradeAuditEntry[];
}

export function useTradeValidation(): UseTradeValidationResult {
  const [trades, setTrades] = useState<TradeAuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [lastPolled, setLastPolled] = useState<Date | null>(null);

  // Load trades from database
  const loadTrades = useCallback(async () => {
    try {
      const { data, error } = await supabase
        .from('trade_audit_log')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(100);

      if (error) {
        console.error('[useTradeValidation] Load error:', error);
        return;
      }

      const mappedTrades: TradeAuditEntry[] = (data || []).map(row => ({
        id: row.id,
        tradeId: row.trade_id,
        externalOrderId: row.external_order_id,
        clientOrderId: row.client_order_id,
        stage: row.stage,
        exchange: row.exchange,
        symbol: row.symbol,
        side: row.side,
        orderType: row.order_type,
        quantity: row.quantity,
        price: row.price,
        executedQty: row.executed_qty,
        executedPrice: row.executed_price,
        commission: row.commission,
        commissionAsset: row.commission_asset,
        exchangeResponse: row.exchange_response,
        validationStatus: row.validation_status,
        validationMessage: row.validation_message,
        errorCode: row.error_code,
        errorMessage: row.error_message,
        createdAt: row.created_at,
        updatedAt: row.updated_at,
      }));

      setTrades(mappedTrades);
    } catch (error) {
      console.error('[useTradeValidation] Error:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Poll for trade confirmations
  const pollConfirmations = useCallback(async () => {
    setIsLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('poll-trade-confirmations', {
        body: {},
      });

      if (error) {
        console.error('[useTradeValidation] Poll error:', error);
        throw error;
      }

      console.log('[useTradeValidation] Poll result:', data);
      setLastPolled(new Date());
      
      // Reload trades after polling
      await loadTrades();
    } catch (error) {
      console.error('[useTradeValidation] Poll failed:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  }, [loadTrades]);

  // Confirm a specific trade
  const confirmTrade = useCallback(async (
    tradeId: string,
    orderId: string,
    symbol: string,
    exchange: string
  ) => {
    try {
      const { data, error } = await supabase.functions.invoke('confirm-trade', {
        body: {
          trade_id: tradeId,
          external_order_id: orderId,
          symbol,
          exchange,
        },
      });

      if (error) {
        console.error('[useTradeValidation] Confirm error:', error);
        throw error;
      }

      console.log('[useTradeValidation] Confirm result:', data);
      
      // Reload trades after confirmation
      await loadTrades();
    } catch (error) {
      console.error('[useTradeValidation] Confirm failed:', error);
      throw error;
    }
  }, [loadTrades]);

  // Initial load
  useEffect(() => {
    loadTrades();
  }, [loadTrades]);

  // Subscribe to realtime updates
  useEffect(() => {
    const channel = supabase
      .channel('trade-audit-changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'trade_audit_log',
        },
        () => {
          loadTrades();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [loadTrades]);

  // Calculate stats
  const stats: TradeValidationStats = useMemo(() => {
    const total = trades.length;
    const confirmed = trades.filter(t => t.validationStatus === 'confirmed').length;
    const pending = trades.filter(t => t.validationStatus === 'pending').length;
    const failed = trades.filter(t => t.validationStatus === 'failed').length;
    
    // Calculate average confirmation time
    const confirmedTrades = trades.filter(t => t.validationStatus === 'confirmed');
    const avgConfirmationTime = confirmedTrades.length > 0
      ? confirmedTrades.reduce((sum, t) => {
          const created = new Date(t.createdAt).getTime();
          const updated = new Date(t.updatedAt).getTime();
          return sum + (updated - created);
        }, 0) / confirmedTrades.length / 1000 // Convert to seconds
      : 0;

    return {
      total,
      confirmed,
      pending,
      failed,
      confirmationRate: total > 0 ? (confirmed / total) * 100 : 0,
      avgConfirmationTime,
    };
  }, [trades]);

  // Filter by status
  const filterByStatus = useCallback((status: string): TradeAuditEntry[] => {
    return trades.filter(t => t.validationStatus === status);
  }, [trades]);

  // Get pending trades
  const getPendingTrades = useCallback((): TradeAuditEntry[] => {
    return trades.filter(t => t.validationStatus === 'pending');
  }, [trades]);

  // Get recent trades
  const getRecentTrades = useCallback((limit: number = 10): TradeAuditEntry[] => {
    return trades.slice(0, limit);
  }, [trades]);

  return {
    trades,
    stats,
    isLoading,
    lastPolled,
    pollConfirmations,
    confirmTrade,
    filterByStatus,
    getPendingTrades,
    getRecentTrades,
  };
}
