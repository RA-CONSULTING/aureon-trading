import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import type { WatchlistSymbol } from './useMultiSymbolWatchlist';

export type PriceAlert = {
  id: string;
  symbol: string;
  alert_type: 'price_above' | 'price_below' | 'change_percent_above' | 'change_percent_below';
  target_value: number;
  current_value: number | null;
  is_active: boolean;
  is_triggered: boolean;
  triggered_at: string | null;
  created_at: string;
  notes: string | null;
};

export const usePriceAlerts = (symbolData: Map<string, WatchlistSymbol>) => {
  const [alerts, setAlerts] = useState<PriceAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const { toast } = useToast();

  // Load alerts from database
  const loadAlerts = async () => {
    try {
      const { data, error } = await supabase
        .from('price_alerts')
        .select('*')
        .order('created_at', { ascending: false });

      if (error) throw error;
      setAlerts((data || []) as PriceAlert[]);
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();

    // Subscribe to realtime updates
    const channel = supabase
      .channel('price_alerts_changes')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'price_alerts',
        },
        () => {
          loadAlerts();
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  // Check alerts against current market data
  useEffect(() => {
    if (alerts.length === 0 || symbolData.size === 0) return;

    alerts.forEach(async (alert) => {
      if (!alert.is_active || alert.is_triggered) return;

      const symbolInfo = symbolData.get(alert.symbol);
      if (!symbolInfo) return;

      let shouldTrigger = false;
      let message = '';

      switch (alert.alert_type) {
        case 'price_above':
          shouldTrigger = symbolInfo.price >= alert.target_value;
          message = `${alert.symbol} reached $${symbolInfo.price.toLocaleString()} (target: $${alert.target_value.toLocaleString()})`;
          break;
        case 'price_below':
          shouldTrigger = symbolInfo.price <= alert.target_value;
          message = `${alert.symbol} dropped to $${symbolInfo.price.toLocaleString()} (target: $${alert.target_value.toLocaleString()})`;
          break;
        case 'change_percent_above':
          shouldTrigger = symbolInfo.changePercent >= alert.target_value;
          message = `${alert.symbol} gained ${symbolInfo.changePercent.toFixed(2)}% (target: ${alert.target_value}%)`;
          break;
        case 'change_percent_below':
          shouldTrigger = symbolInfo.changePercent <= alert.target_value;
          message = `${alert.symbol} lost ${Math.abs(symbolInfo.changePercent).toFixed(2)}% (target: ${alert.target_value}%)`;
          break;
      }

      if (shouldTrigger) {
        // Trigger the alert
        await triggerAlert(alert.id, symbolInfo.price);
        
        toast({
          title: '🔔 Price Alert Triggered!',
          description: message,
          duration: 10000,
        });
      }
    });
  }, [symbolData, alerts, toast]);

  const triggerAlert = async (alertId: string, currentValue: number) => {
    try {
      await supabase
        .from('price_alerts')
        .update({
          is_triggered: true,
          triggered_at: new Date().toISOString(),
          current_value: currentValue,
        })
        .eq('id', alertId);
    } catch (error) {
      console.error('Error triggering alert:', error);
    }
  };

  const createAlert = async (
    symbol: string,
    alertType: PriceAlert['alert_type'],
    targetValue: number,
    notes?: string
  ) => {
    try {
      const { error } = await supabase
        .from('price_alerts')
        .insert({
          symbol,
          alert_type: alertType,
          target_value: targetValue,
          notes,
        });

      if (error) throw error;

      toast({
        title: 'Alert Created',
        description: `Price alert set for ${symbol}`,
        duration: 3000,
      });

      return true;
    } catch (error) {
      console.error('Error creating alert:', error);
      toast({
        title: 'Error',
        description: 'Failed to create alert',
        variant: 'destructive',
        duration: 3000,
      });
      return false;
    }
  };

  const deleteAlert = async (alertId: string) => {
    try {
      const { error } = await supabase
        .from('price_alerts')
        .delete()
        .eq('id', alertId);

      if (error) throw error;

      toast({
        title: 'Alert Deleted',
        description: 'Price alert removed',
        duration: 3000,
      });

      return true;
    } catch (error) {
      console.error('Error deleting alert:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete alert',
        variant: 'destructive',
        duration: 3000,
      });
      return false;
    }
  };

  const toggleAlert = async (alertId: string, isActive: boolean) => {
    try {
      const { error } = await supabase
        .from('price_alerts')
        .update({ is_active: isActive })
        .eq('id', alertId);

      if (error) throw error;
      return true;
    } catch (error) {
      console.error('Error toggling alert:', error);
      return false;
    }
  };

  return {
    alerts,
    loading,
    createAlert,
    deleteAlert,
    toggleAlert,
  };
};
