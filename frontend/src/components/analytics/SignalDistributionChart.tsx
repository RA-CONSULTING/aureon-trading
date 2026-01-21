import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { supabase } from '@/integrations/supabase/client';

type SignalCount = {
  name: string;
  value: number;
  color: string;
};

const COLORS = {
  LONG: '#00FF88',
  SHORT: '#FF6B35',
  HOLD: '#888888',
};

export const SignalDistributionChart = () => {
  const [data, setData] = useState<SignalCount[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalSignals, setTotalSignals] = useState(0);

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const { data: signals, error } = await supabase
        .from('trading_signals')
        .select('signal_type')
        .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString());

      if (error) throw error;

      const counts: Record<string, number> = {
        LONG: 0,
        SHORT: 0,
        HOLD: 0,
      };

      (signals || []).forEach((signal) => {
        counts[signal.signal_type]++;
      });

      const total = Object.values(counts).reduce((sum, val) => sum + val, 0);
      setTotalSignals(total);

      const chartData = Object.entries(counts)
        .filter(([_, value]) => value > 0)
        .map(([name, value]) => ({
          name,
          value,
          color: COLORS[name as keyof typeof COLORS],
        }));

      setData(chartData);
    } catch (error) {
      console.error('Error fetching signal distribution:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">Signal Distribution</h3>
        <p className="text-muted-foreground">Loading data...</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">📊 Signal Distribution (24h)</h3>
      <p className="text-sm text-muted-foreground mb-4">
        Breakdown of LONG, SHORT, and HOLD signals
      </p>
      {data.length > 0 ? (
        <>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--background))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '8px',
                }}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
          <div className="text-center mt-4">
            <p className="text-sm text-muted-foreground">
              Total Signals: <strong>{totalSignals}</strong>
            </p>
          </div>
        </>
      ) : (
        <p className="text-center text-sm text-muted-foreground mt-4">
          No signals yet. Start the field on /aureon to begin tracking.
        </p>
      )}
    </Card>
  );
};
