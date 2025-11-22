import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ReferenceLine, ResponsiveContainer } from 'recharts';
import { Activity, TrendingUp, Waves, Zap, Target } from 'lucide-react';
import type { LighthouseState } from '@/core/lighthouseConsensus';
import { useState, useEffect } from 'react';

interface LighthouseMetricsPanelProps {
  lighthouse: LighthouseState | null;
}

interface HistoricalPoint {
  timestamp: number;
  L: number;
  threshold: number;
  isLHE: boolean;
}

export const LighthouseMetricsPanel = ({ lighthouse }: LighthouseMetricsPanelProps) => {
  const [history, setHistory] = useState<HistoricalPoint[]>([]);

  useEffect(() => {
    if (!lighthouse) return;

    const newPoint: HistoricalPoint = {
      timestamp: Date.now(),
      L: lighthouse.L,
      threshold: lighthouse.threshold,
      isLHE: lighthouse.isLHE,
    };

    setHistory((prev) => {
      const updated = [...prev, newPoint];
      // Keep last 50 points
      if (updated.length > 50) {
        updated.shift();
      }
      return updated;
    });
  }, [lighthouse]);

  if (!lighthouse) {
    return (
      <Card className="p-6">
        <div className="text-center text-muted-foreground">
          <Activity className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p>Start AUREON to see Lighthouse metrics</p>
        </div>
      </Card>
    );
  }

  const metrics = [
    {
      name: 'Clin',
      label: 'Linear Coherence',
      value: lighthouse.metrics.Clin,
      icon: Waves,
      description: 'MACD-based trend strength',
      color: 'hsl(var(--chart-1))',
    },
    {
      name: 'Cnonlin',
      label: 'Nonlinear Coherence',
      value: lighthouse.metrics.Cnonlin,
      icon: TrendingUp,
      description: 'Volatility-adjusted stability',
      color: 'hsl(var(--chart-2))',
    },
    {
      name: 'Geff',
      label: 'Effective Gravity (BRAKE)',
      value: lighthouse.metrics.Geff,
      icon: Zap,
      description: 'Fibonacci curvature signal',
      color: 'hsl(var(--chart-4))',
    },
    {
      name: '|Q|',
      label: 'Anomaly Pointer (FLAME)',
      value: lighthouse.metrics.Q,
      icon: Target,
      description: 'Sudden change detector',
      color: 'hsl(var(--chart-5))',
    },
  ];

  // Format chart data
  const chartData = history.map((point, idx) => ({
    time: idx,
    L: point.L,
    threshold: point.threshold,
    isLHE: point.isLHE,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="p-6 bg-gradient-to-br from-primary/5 to-background border-2 border-primary/20">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xl font-bold">Lighthouse Consensus Metrics</h3>
            <p className="text-sm text-muted-foreground mt-1">
              Four metrics (Clin, Cnonlin, Geff, |Q|) combine via weighted geometric mean → L(t)
            </p>
          </div>
          {lighthouse.isLHE && (
            <Badge variant="default" className="bg-primary text-primary-foreground animate-pulse">
              🎯 LHE DETECTED
            </Badge>
          )}
        </div>

        {/* Geometric Mean Formula */}
        <div className="p-4 rounded-lg bg-muted/50 border border-border">
          <div className="text-center font-mono text-sm space-y-2">
            <div className="font-semibold text-foreground">L(t) = (Clin^1.0 × Cnonlin^1.2 × Geff^1.2 × |Q|^0.8)^(1/4.2)</div>
            <div className="text-muted-foreground text-xs">
              Weighted Geometric Mean | Ablation Study: Cnonlin & Geff strongest, |Q| suppressor
            </div>
          </div>
        </div>
      </Card>

      {/* Individual Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const percentage = Math.min(Math.max(metric.value * 100, 0), 100);
          
          return (
            <Card key={metric.name} className="p-4 hover:border-primary/50 transition-colors">
              <div className="flex items-start justify-between mb-3">
                <div className="p-2 rounded-lg" style={{ backgroundColor: `${metric.color}20` }}>
                  <Icon className="h-4 w-4" style={{ color: metric.color }} />
                </div>
                <span className="text-sm font-mono font-bold" style={{ color: metric.color }}>
                  {metric.value.toFixed(3)}
                </span>
              </div>
              
              <div className="space-y-2">
                <div>
                  <div className="text-sm font-semibold">{metric.name}</div>
                  <div className="text-xs text-muted-foreground">{metric.label}</div>
                </div>
                
                <Progress 
                  value={percentage} 
                  className="h-2"
                  style={{
                    '--progress-background': metric.color,
                  } as React.CSSProperties}
                />
                
                <div className="text-xs text-muted-foreground">
                  {metric.description}
                </div>
              </div>
            </Card>
          );
        })}
      </div>

      {/* L(t) Time Series Chart */}
      <Card className="p-6">
        <div className="mb-4">
          <h4 className="text-lg font-semibold mb-1">Lighthouse Signal L(t) Over Time</h4>
          <p className="text-sm text-muted-foreground">
            LHE triggered when L(t) &gt; μ + 2σ (threshold line)
          </p>
        </div>

        <div className="space-y-4">
          {/* Current Status */}
          <div className="grid grid-cols-3 gap-4">
            <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
              <div className="text-xs text-muted-foreground mb-1">Current L(t)</div>
              <div className="text-2xl font-bold text-primary">{lighthouse.L.toFixed(4)}</div>
            </div>
            
            <div className="p-3 rounded-lg bg-muted/50 border border-border">
              <div className="text-xs text-muted-foreground mb-1">Threshold (μ+2σ)</div>
              <div className="text-2xl font-bold">{lighthouse.threshold.toFixed(4)}</div>
            </div>
            
            <div className="p-3 rounded-lg bg-muted/50 border border-border">
              <div className="text-xs text-muted-foreground mb-1">Confidence</div>
              <div className="text-2xl font-bold">{(lighthouse.confidence * 100).toFixed(1)}%</div>
            </div>
          </div>

          {/* Chart */}
          {chartData.length > 0 && (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis 
                  dataKey="time" 
                  stroke="hsl(var(--muted-foreground))"
                  tick={{ fill: 'hsl(var(--muted-foreground))' }}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  tick={{ fill: 'hsl(var(--muted-foreground))' }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'hsl(var(--background))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                  formatter={(value: number) => value.toFixed(4)}
                />
                <Legend />
                
                <ReferenceLine 
                  y={0} 
                  stroke="hsl(var(--muted-foreground))" 
                  strokeDasharray="3 3" 
                />
                
                <Line
                  type="monotone"
                  dataKey="threshold"
                  stroke="hsl(var(--destructive))"
                  strokeWidth={2}
                  strokeDasharray="5 5"
                  dot={false}
                  name="Threshold (μ+2σ)"
                />
                
                <Line
                  type="monotone"
                  dataKey="L"
                  stroke="hsl(var(--primary))"
                  strokeWidth={3}
                  dot={(props: any) => {
                    const point = chartData[props.index];
                    if (point?.isLHE) {
                      return (
                        <circle
                          cx={props.cx}
                          cy={props.cy}
                          r={6}
                          fill="hsl(var(--primary))"
                          stroke="hsl(var(--background))"
                          strokeWidth={2}
                        />
                      );
                    }
                    return null;
                  }}
                  name="L(t)"
                />
              </LineChart>
            </ResponsiveContainer>
          )}

          {chartData.length === 0 && (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              <p>Collecting data points...</p>
            </div>
          )}
        </div>
      </Card>

      {/* LHE Detection Status */}
      {lighthouse.isLHE && (
        <Card className="p-4 border-2 border-primary bg-primary/5 animate-pulse">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-primary text-primary-foreground">
              <Zap className="h-6 w-6" />
            </div>
            <div>
              <div className="font-bold text-lg">Lighthouse Event Detected!</div>
              <div className="text-sm text-muted-foreground">
                L(t) = {lighthouse.L.toFixed(4)} exceeds threshold {lighthouse.threshold.toFixed(4)} with {(lighthouse.confidence * 100).toFixed(1)}% confidence
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};

