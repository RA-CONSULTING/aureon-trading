import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { supabase } from '@/integrations/supabase/client';

type FrequencyData = {
  hour: string;
  lheCount: number;
  totalEvents: number;
};

export const LHEFrequencyChart = () => {
  const [data, setData] = useState<FrequencyData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const { data: events, error } = await supabase
        .from('lighthouse_events')
        .select('timestamp, is_lhe')
        .gte('timestamp', new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString())
        .order('timestamp', { ascending: true });

      if (error) throw error;

      // Group by hour
      const hourlyData: Record<string, { lhe: number; total: number }> = {};

      (events || []).forEach((event) => {
        const hour = new Date(event.timestamp).getHours();
        const hourKey = `${hour}:00`;

        if (!hourlyData[hourKey]) {
          hourlyData[hourKey] = { lhe: 0, total: 0 };
        }

        hourlyData[hourKey].total++;
        if (event.is_lhe) {
          hourlyData[hourKey].lhe++;
        }
      });

      const chartData = Object.entries(hourlyData).map(([hour, counts]) => ({
        hour,
        lheCount: counts.lhe,
        totalEvents: counts.total,
      }));

      setData(chartData);
    } catch (error) {
      console.error('Error fetching LHE frequency data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">LHE Frequency (24h)</h3>
        <p className="text-muted-foreground">Loading data...</p>
      </Card>
    );
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">🎯 Lighthouse Events Frequency</h3>
      <p className="text-sm text-muted-foreground mb-4">
        LHE detections per hour over the last 24 hours
      </p>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
          <XAxis 
            dataKey="hour" 
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
          <Bar 
            dataKey="lheCount" 
            fill="#00FF88" 
            name="LHE Count"
            radius={[4, 4, 0, 0]}
          />
          <Bar 
            dataKey="totalEvents" 
            fill="#4169E1" 
            name="Total Events"
            opacity={0.3}
            radius={[4, 4, 0, 0]}
          />
        </BarChart>
      </ResponsiveContainer>
      {data.length === 0 && (
        <p className="text-center text-sm text-muted-foreground mt-4">
          No data yet. Start the field on /aureon to begin tracking.
        </p>
      )}
    </Card>
  );
};
