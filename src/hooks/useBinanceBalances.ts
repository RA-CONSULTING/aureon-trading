import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

export type AccountBalance = {
  name: string;
  balances: Record<string, { free: number; locked: number; total: number; usdValue?: number }>;
  canTrade?: boolean;
  error?: string;
};

export type BalanceTotals = {
  USDT: number;
  BTC: number;
  ETH: number;
  totalUSDValue?: number;
};

export function useBinanceBalances() {
  const [accounts, setAccounts] = useState<AccountBalance[]>([]);
  const [totals, setTotals] = useState<BalanceTotals>({ USDT: 0, BTC: 0, ETH: 0 });
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { toast } = useToast();

  const fetchBalances = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('get-binance-balances');

      if (error) throw error;

      if (data.success) {
        setAccounts(data.accounts);
        setTotals(data.totals);
        setLastUpdated(new Date(data.timestamp));
      } else {
        throw new Error(data.error || 'Failed to fetch balances');
      }
    } catch (error: any) {
      console.error('Failed to fetch Binance balances:', error);
      toast({
        title: '❌ Balance Fetch Failed',
        description: error?.message || 'Unknown error',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBalances();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(fetchBalances, 30000);
    return () => clearInterval(interval);
  }, []);

  return {
    accounts,
    totals,
    loading,
    lastUpdated,
    refresh: fetchBalances,
  };
}
