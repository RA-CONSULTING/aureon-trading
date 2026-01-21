import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

export interface OMSStatus {
  queueDepth: number;
  processing: number;
  rateLimit: {
    limit: number;
    used: number;
    available: number;
    utilization: number;
    windowDurationMs: number;
  };
  metrics: {
    queue_depth: number;
    current_window_orders: number;
    rate_limit_utilization: number;
    orders_executed_last_minute: number;
    orders_failed_last_minute: number;
  } | null;
}

export interface QueuedOrder {
  id: string;
  symbol: string;
  side: 'BUY' | 'SELL';
  quantity: number;
  price: number;
  priority: number;
  status: string;
  queued_at: string;
}

export function useOMSQueue(sessionId: string | null) {
  const [status, setStatus] = useState<OMSStatus | null>(null);
  const [orders, setOrders] = useState<QueuedOrder[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const { toast } = useToast();

  const fetchStatus = useCallback(async () => {
    if (!sessionId) return;

    try {
      const { data, error } = await supabase.functions.invoke('oms-leaky-bucket', {
        body: { action: 'status', sessionId },
      });

      if (error) throw error;
      if (data.success) {
        setStatus(data);
      }
    } catch (error) {
      console.error('Failed to fetch OMS status:', error);
    }
  }, [sessionId]);

  const fetchOrders = useCallback(async () => {
    if (!sessionId) return;

    try {
      const { data, error } = await supabase
        .from('oms_order_queue')
        .select('*')
        .eq('session_id', sessionId)
        .in('status', ['queued', 'processing'])
        .order('priority', { ascending: false })
        .order('queued_at', { ascending: true });

      if (error) throw error;
      setOrders((data || []).map(order => ({
        ...order,
        side: order.side as 'BUY' | 'SELL',
      })));
    } catch (error) {
      console.error('Failed to fetch orders:', error);
    }
  }, [sessionId]);

  const enqueueOrder = useCallback(async (orderParams: {
    hiveId: string;
    agentId: string;
    symbol: string;
    side: 'BUY' | 'SELL';
    quantity: number;
    price: number;
    priority?: number;
    metadata?: {
      signalStrength?: number;
      coherence?: number;
      lighthouseValue?: number;
    };
  }) => {
    if (!sessionId) return null;

    try {
      const { data, error } = await supabase.functions.invoke('oms-leaky-bucket', {
        body: {
          action: 'enqueue',
          sessionId,
          ...orderParams,
        },
      });

      if (error) throw error;

      if (data.success) {
        toast({
          title: 'Order Queued',
          description: `Position ${data.position} in queue`,
        });
        await fetchOrders();
        return data.orderId;
      }
    } catch (error) {
      console.error('Failed to enqueue order:', error);
      toast({
        title: 'Failed to Queue Order',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }

    return null;
  }, [sessionId, toast, fetchOrders]);

  const processQueue = useCallback(async () => {
    if (!sessionId || isProcessing) return;

    setIsProcessing(true);

    try {
      const { data, error } = await supabase.functions.invoke('oms-leaky-bucket', {
        body: { action: 'process' },
      });

      if (error) throw error;

      if (data.success && data.processed > 0) {
        console.log(`✅ Processed ${data.processed} orders`);
        await Promise.all([fetchStatus(), fetchOrders()]);
      }
    } catch (error) {
      console.error('Failed to process queue:', error);
    } finally {
      setIsProcessing(false);
    }
  }, [sessionId, isProcessing, fetchStatus, fetchOrders]);

  const cancelOrder = useCallback(async (orderId: string) => {
    try {
      const { data, error } = await supabase.functions.invoke('oms-leaky-bucket', {
        body: { action: 'cancel', orderId },
      });

      if (error) throw error;

      if (data.success) {
        toast({
          title: 'Order Cancelled',
          description: 'Order removed from queue',
        });
        await fetchOrders();
      }
    } catch (error) {
      console.error('Failed to cancel order:', error);
      toast({
        title: 'Failed to Cancel',
        description: error instanceof Error ? error.message : 'Unknown error',
        variant: 'destructive',
      });
    }
  }, [toast, fetchOrders]);

  // Auto-refresh status every 2 seconds
  useEffect(() => {
    if (!sessionId) return;

    fetchStatus();
    fetchOrders();

    const interval = setInterval(() => {
      fetchStatus();
      fetchOrders();
    }, 2000);

    return () => clearInterval(interval);
  }, [sessionId, fetchStatus, fetchOrders]);

  // Auto-process queue every 100ms
  useEffect(() => {
    if (!sessionId) return;

    const interval = setInterval(() => {
      processQueue();
    }, 100);

    return () => clearInterval(interval);
  }, [sessionId, processQueue]);

  return {
    status,
    orders,
    enqueueOrder,
    processQueue,
    cancelOrder,
    isProcessing,
  };
}
