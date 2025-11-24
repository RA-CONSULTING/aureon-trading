import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useEffect, useState, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface StrikeEvent {
  id: string;
  timestamp: string;
  type: 'execution' | 'lhe' | 'position_close';
  message: string;
  severity: 'info' | 'success' | 'critical';
}

export function LiveStrikeStream() {
  const [events, setEvents] = useState<StrikeEvent[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Subscribe to real-time trading executions
    const channel = supabase
      .channel('strike-stream')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trading_executions',
        },
        (payload: any) => {
          const exec = payload.new;
          const severity: 'info' | 'success' | 'critical' = exec.status === 'executed' ? 'success' : 'info';
          setEvents(prev => [
            {
              id: exec.id,
              timestamp: exec.executed_at || exec.created_at,
              type: 'execution' as const,
              message: `${exec.side} ${exec.symbol} @ $${exec.executed_price?.toFixed(2) || 'MARKET'}`,
              severity,
            },
            ...prev,
          ].slice(0, 50));
        }
      )
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload: any) => {
          const event = payload.new;
          if (event.is_lhe) {
            setEvents(prev => [
              {
                id: event.id,
                timestamp: event.timestamp,
                type: 'lhe' as const,
                message: `🔥 LHE DETECTED - Γ=${(event.coherence * 100).toFixed(1)}% L=${event.lighthouse_signal.toFixed(2)}`,
                severity: 'critical' as const,
              },
              ...prev,
            ].slice(0, 50));
          }
        }
      )
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
            const pnl = parseFloat(String(position.realized_pnl));
            const severity: 'info' | 'success' | 'critical' = pnl > 0 ? 'success' : 'info';
            setEvents(prev => [
              {
                id: position.id,
                timestamp: position.closed_at,
                type: 'position_close' as const,
                message: `Position closed: ${position.symbol} P&L $${pnl.toFixed(2)}`,
                severity,
              },
              ...prev,
            ].slice(0, 50));
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  // Auto-scroll to top on new events
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [events]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'bg-destructive text-destructive-foreground';
      case 'success': return 'bg-green-500/20 text-green-500 border-green-500/50';
      default: return 'bg-primary/20 text-primary border-primary/50';
    }
  };

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>⚡ Live Strike Stream</span>
          <Badge variant="outline">{events.length} events</Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-80" ref={scrollRef}>
          <div className="space-y-2">
            {events.length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-8">
                Waiting for strikes...
              </p>
            ) : (
              events.map((event) => (
                <div
                  key={event.id}
                  className={`p-3 rounded-lg border ${getSeverityColor(event.severity)}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium flex-1">{event.message}</p>
                    <p className="text-xs opacity-70 whitespace-nowrap">
                      {new Date(event.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
