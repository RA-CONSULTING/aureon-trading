import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { supabase } from '@/integrations/supabase/client';

type DataPoint = {
  time: string;
  coherence: number;
  lighthouse: number;
};

export const CoherenceTrendChart = () => {
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();

    // Realtime subscription
    const channel = supabase
      .channel('coherence_updates')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload) => {
          const newEvent = payload.new as any;
          const newPoint: DataPoint = {
            time: new Date(newEvent.timestamp).toLocaleTimeString(),
            coherence: Number(newEvent.coherence),
            lighthouse: Number(newEvent.lighthouse_signal),
          };
          setData((prev) => [...prev.slice(-50), newPoint]);
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, []);

  const fetchData = async () => {
    try {
      const { data: events, error } = await supabase
        .from('lighthouse_events')
        .select('timestamp, coherence, lighthouse_signal')
        .order('timestamp', { ascending: false })
        .limit(50);

      if (error) throw error;

      const chartData = (events || [])
        .reverse()
        .map((event) => ({
          time: new Date(event.timestamp).toLocaleTimeString(),
          coherence: Number(event.coherence),
          lighthouse: Number(event.lighthouse_signal),
        }));

      setData(chartData);
    } catch (error) {
      console.error('Error fetching coherence data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Coherence & Lighthouse Trends</h3>
        <p className="text-muted-foreground">Loading data...</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Coherence & Lighthouse Trends</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Real-time tracking of field coherence Γ and Lighthouse signal L(t)
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            dataKey="time" 
            tick={{ fontSize: 12 }}
            stroke="hsl(var(--muted-foreground))"
          />
          <YAxis 
            tick={{ fontSize: 12 }}
            stroke="hsl(var(--muted-foreground))"
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'hsl(var(--background))',
              border: '1px solid hsl(var(--border))',
              borderRadius: '8px',
            }}
          />
          <ReferenceLine 
            y={0.945} 
            stroke="#00FF88" 
            strokeDasharray="3 3" 
            label={{ value: 'Γ = 0.945 (Optimal)', fill: '#00FF88', fontSize: 10 }}
          />
          <Line 
            type="monotone" 
            dataKey="coherence" 
            stroke="#00FF88" 
            strokeWidth={2}
            dot={false}
            name="Coherence Γ"
          />
          <Line 
            type="monotone" 
            dataKey="lighthouse" 
            stroke="#4169E1" 
            strokeWidth={2}
            dot={false}
            name="Lighthouse L(t)"
          />
        </LineChart>
      </ResponsiveContainer>
      {data.length === 0 && (
        <p className="text-center text-sm text-muted-foreground mt-4">
          No data yet. Start the field on /aureon to begin tracking.
        </p>
      )}
    </Card>
  );
};
