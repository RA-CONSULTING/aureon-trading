import { Card } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useHistoricalData } from '@/hooks/useHistoricalData';
import { Loader2 } from 'lucide-react';

export function HistoricalTimeline() {
  const { coherence, tradeVolume, cumulativePnL, isLoading } = useHistoricalData();

  if (isLoading) {
    return (
      <Card className="bg-black/40 border-border/30 p-6 flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-400" />
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <ChartCard
        title="Coherence Γ (24h)"
        data={coherence}
        dataKey="value"
        color="#a855f7"
      />
      <ChartCard
        title="Trade Volume (24h)"
        data={tradeVolume}
        dataKey="value"
        color="#06b6d4"
      />
      <ChartCard
        title="Cumulative P&L (24h)"
        data={cumulativePnL}
        dataKey="value"
        color="#22c55e"
      />
    </div>
  );
}

interface ChartCardProps {
  title: string;
  data: any[];
  dataKey: string;
  color: string;
}

function ChartCard({ title, data, dataKey, color }: ChartCardProps) {
  return (
    <Card className="bg-black/40 border-border/30 p-4">
      <h3 className="text-sm font-semibold mb-3 text-muted-foreground">{title}</h3>
      <ResponsiveContainer width="100%" height={150}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id={`gradient-${color}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={color} stopOpacity={0.8} />
              <stop offset="95%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="timestamp" hide />
          <YAxis hide />
          <Tooltip
            contentStyle={{
              backgroundColor: 'rgba(0,0,0,0.8)',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: '8px',
            }}
          />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke={color}
            fill={`url(#gradient-${color})`}
            strokeWidth={2}
          />
        </AreaChart>
      </ResponsiveContainer>
    </Card>
  );
}
