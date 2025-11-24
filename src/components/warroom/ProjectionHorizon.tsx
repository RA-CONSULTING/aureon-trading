import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { useProjections } from '@/hooks/useProjections';
import { TrendingUp } from 'lucide-react';

interface Props {
  currentBalance: number;
  winRate: number;
  avgTradeSize: number;
  tradesPerDay: number;
}

export function ProjectionHorizon({ currentBalance, winRate, avgTradeSize, tradesPerDay }: Props) {
  const projection = useProjections(currentBalance, winRate, avgTradeSize, tradesPerDay);

  const chartData = projection.timestamps.map((timestamp, i) => ({
    timestamp,
    projected: projection.projectedBalance[i],
    min: projection.confidenceBand.min[i],
    max: projection.confidenceBand.max[i],
  }));

  const nextMilestone = projection.milestones.find(m => m.amount > currentBalance);

  return (
    <Card className="bg-gradient-to-br from-green-900/30 via-black to-cyan-900/30 border-green-500/30 p-6">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-green-300 flex items-center gap-2">
            <TrendingUp className="w-5 h-5" />
            Future Projection
          </h3>
          {nextMilestone?.eta && (
            <Badge variant="outline" className="border-green-500/50 text-green-300">
              Next: {nextMilestone.label} in {nextMilestone.eta}
            </Badge>
          )}
        </div>

        {/* Chart */}
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={chartData}>
            <defs>
              <linearGradient id="projectedGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
              </linearGradient>
            </defs>
            <XAxis dataKey="timestamp" hide />
            <YAxis hide />
            <Tooltip
              contentStyle={{
                backgroundColor: 'rgba(0,0,0,0.8)',
                border: '1px solid rgba(34,197,94,0.3)',
                borderRadius: '8px',
              }}
              formatter={(value: number) => `$${value.toFixed(2)}`}
            />
            
            {/* Current position */}
            <ReferenceLine
              x={chartData[0]?.timestamp}
              stroke="#22c55e"
              strokeDasharray="3 3"
              label="Now"
            />

            {/* Confidence band */}
            <Line
              type="monotone"
              dataKey="max"
              stroke="#22c55e"
              strokeWidth={1}
              strokeOpacity={0.3}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="min"
              stroke="#22c55e"
              strokeWidth={1}
              strokeOpacity={0.3}
              dot={false}
            />

            {/* Main projection */}
            <Line
              type="monotone"
              dataKey="projected"
              stroke="#22c55e"
              strokeWidth={3}
              dot={false}
              fill="url(#projectedGradient)"
            />
          </LineChart>
        </ResponsiveContainer>

        {/* Milestones */}
        <div className="grid grid-cols-5 gap-2">
          {projection.milestones.map((milestone) => (
            <div
              key={milestone.amount}
              className={`text-center p-2 rounded border ${
                currentBalance >= milestone.amount
                  ? 'bg-green-500/20 border-green-500/50'
                  : 'bg-black/30 border-border/20'
              }`}
            >
              <div className="text-xs font-bold">{milestone.label}</div>
              {milestone.eta && (
                <div className="text-xs text-muted-foreground">{milestone.eta}</div>
              )}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
