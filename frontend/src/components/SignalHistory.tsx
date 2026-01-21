import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';

type HistoricalSignal = {
  id: string;
  timestamp: string;
  signal_type: string;
  strength: number;
  reason: string;
  coherence: number;
  lighthouse_value: number;
};

export const SignalHistory = () => {
  const [signals, setSignals] = useState<HistoricalSignal[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchRecentSignals();

    // Subscribe to realtime updates
    const channel = supabase
      .channel('trading_signals_changes')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'trading_signals',
        },
        (payload) => {
          const newSignal = payload.new as HistoricalSignal;
          setSignals((prev) => [newSignal, ...prev].slice(0, 20));
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const fetchRecentSignals = async () => {
    try {
      const { data, error } = await supabase
        .from('trading_signals')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(20);

      if (error) throw error;
      setSignals(data || []);
    } catch (error) {
      console.error('Error fetching signals:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <p className="text-muted-foreground">Loading signal history...</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Recent Trading Signals</h3>
      <div className="space-y-3 max-h-96 overflow-y-auto">
        {signals.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No signals recorded yet. Start the field to begin tracking.
          </p>
        ) : (
          signals.map((signal) => (
            <div
              key={signal.id}
              className="border border-border rounded-lg p-3 hover:bg-muted/50 transition-colors"
            >
              <div className="flex items-center justify-between mb-2">
                <Badge
                  style={{
                    backgroundColor:
                      signal.signal_type === 'LONG'
                        ? '#00FF88'
                        : signal.signal_type === 'SHORT'
                        ? '#FF6B35'
                        : '#888',
                  }}
                >
                  {signal.signal_type}
                </Badge>
                <span className="text-xs text-muted-foreground">
                  {new Date(signal.timestamp).toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm mb-2">{signal.reason}</p>
              <div className="flex gap-4 text-xs text-muted-foreground">
                <span>Strength: {(signal.strength * 100).toFixed(0)}%</span>
                <span>Γ: {signal.coherence.toFixed(3)}</span>
                <span>L(t): {signal.lighthouse_value.toFixed(2)}</span>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
};
