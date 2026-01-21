import { useState, useEffect, useCallback } from 'react';
import { supabase } from '@/integrations/supabase/client';

export type StrikeEventType = 'execution' | 'position_update' | 'lighthouse' | 'signal' | 'order_queue';

export interface StrikeEvent {
  id: string;
  timestamp: string;
  type: StrikeEventType;
  symbol?: string;
  side?: string;
  price?: number;
  quantity?: number;
  status: 'success' | 'failed' | 'pending';
  coherence?: number;
  lighthouse?: number;
  message: string;
  pnl?: number;
}

export function useStrikeFeed(maxEvents: number = 100) {
  const [events, setEvents] = useState<StrikeEvent[]>([]);
  const [executionCount, setExecutionCount] = useState({ success: 0, failed: 0 });

  const addEvent = useCallback((event: StrikeEvent) => {
    setEvents(prev => {
      const updated = [event, ...prev].slice(0, maxEvents);
      return updated;
    });

    if (event.type === 'execution') {
      setExecutionCount(prev => ({
        success: event.status === 'success' ? prev.success + 1 : prev.success,
        failed: event.status === 'failed' ? prev.failed + 1 : prev.failed,
      }));
    }
  }, [maxEvents]);

  // Subscribe to trading executions
  useEffect(() => {
    const executionsChannel = supabase
      .channel('executions-feed')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trading_executions',
        },
        (payload: any) => {
          const execution = payload.new;
          addEvent({
            id: execution.id,
            timestamp: execution.created_at,
            type: 'execution',
            symbol: execution.symbol,
            side: execution.side,
            price: execution.executed_price || execution.price,
            quantity: execution.quantity,
            status: execution.status === 'filled' ? 'success' : execution.status === 'failed' ? 'failed' : 'pending',
            coherence: execution.coherence,
            lighthouse: execution.lighthouse_value,
            message: `${execution.side} ${execution.symbol} @ $${(execution.executed_price || execution.price)?.toFixed(4)}`,
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(executionsChannel);
    };
  }, [addEvent]);

  // Subscribe to position updates
  useEffect(() => {
    const positionsChannel = supabase
      .channel('positions-feed')
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'trading_positions',
        },
        (payload: any) => {
          const position = payload.new;
          if (position.status === 'closed' && position.realized_pnl) {
            addEvent({
              id: `pos-${position.id}`,
              timestamp: position.closed_at || new Date().toISOString(),
              type: 'position_update',
              symbol: position.symbol,
              side: position.side,
              status: position.realized_pnl > 0 ? 'success' : 'failed',
              pnl: parseFloat(position.realized_pnl),
              message: `Closed ${position.symbol}: ${position.realized_pnl > 0 ? '✅' : '❌'} $${parseFloat(position.realized_pnl).toFixed(2)}`,
            });
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(positionsChannel);
    };
  }, [addEvent]);

  // Subscribe to Lighthouse events
  useEffect(() => {
    const lighthouseChannel = supabase
      .channel('lighthouse-feed')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload: any) => {
          const lhe = payload.new;
          if (lhe.is_lhe) {
            addEvent({
              id: lhe.id,
              timestamp: lhe.timestamp,
              type: 'lighthouse',
              status: 'success',
              coherence: lhe.coherence,
              lighthouse: lhe.lighthouse_signal,
              message: `🔥 LHE Detected: Γ=${lhe.coherence.toFixed(3)} L=${lhe.lighthouse_signal.toFixed(3)} [${lhe.dominant_node || 'Unknown'}]`,
            });
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(lighthouseChannel);
    };
  }, [addEvent]);

  // Subscribe to order queue
  useEffect(() => {
    const queueChannel = supabase
      .channel('queue-feed')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'oms_order_queue',
        },
        (payload: any) => {
          const order = payload.new;
          addEvent({
            id: order.id,
            timestamp: order.queued_at,
            type: 'order_queue',
            symbol: order.symbol,
            side: order.side,
            price: order.price,
            quantity: order.quantity,
            status: 'pending',
            coherence: order.coherence,
            lighthouse: order.lighthouse_value,
            message: `⏳ Queued: ${order.side} ${order.symbol} @ $${order.price.toFixed(4)}`,
          });
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(queueChannel);
    };
  }, [addEvent]);

  const clearEvents = useCallback(() => {
    setEvents([]);
    setExecutionCount({ success: 0, failed: 0 });
  }, []);

  const filterByType = useCallback((type: StrikeEventType) => {
    return events.filter(e => e.type === type);
  }, [events]);

  return {
    events,
    executionCount,
    clearEvents,
    filterByType,
    lighthouseEvents: events.filter(e => e.type === 'lighthouse'),
    executionEvents: events.filter(e => e.type === 'execution'),
  };
}
