import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { MonteCarloResults } from '@/core/monteCarloEngine';
import { TrendingUp, Target, Shield, Activity, AlertCircle } from 'lucide-react';
import { BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';

interface MonteCarloResultsProps {
  results: MonteCarloResults | null;
}

export const MonteCarloResultsDisplay = ({ results }: MonteCarloResultsProps) => {
  if (!results) {
    return (
      <Card className="p-8 text-center">
        <Activity className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Simulation Results</h3>
        <p className="text-muted-foreground">
          Configure and run a Monte Carlo simulation above
        </p>
      </Card>
    );
  }

  const { aggregateMetrics, distribution, robustnessScore, successRate, simulations } = results;

  // Prepare histogram data for return distribution
  const returnBins = 20;
  const returnHistogram = createHistogram(distribution.totalReturns, returnBins);

  // Prepare scatter plot data
  const scatterData = simulations.map(s => ({
    winRate: s.results.metrics.winRate,
    totalReturn: s.results.metrics.totalReturnPercent,
    maxDrawdown: s.results.metrics.maxDrawdownPercent,
  }));

  function createHistogram(data: number[], bins: number) {
    const min = Math.min(...data);
    const max = Math.max(...data);
    const binSize = (max - min) / bins;
    
    const histogram = new Array(bins).fill(0).map((_, i) => ({
      range: `${(min + i * binSize).toFixed(1)}`,
      count: 0,
    }));

    data.forEach(value => {
      const binIndex = Math.min(Math.floor((value - min) / binSize), bins - 1);
      histogram[binIndex].count++;
    });

    return histogram;
  }

  const getRobustnessColor = (score: number) => {
    if (score >= 80) return 'text-green-500';
    if (score >= 60) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getRobustnessLabel = (score: number) => {
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="space-y-6">
      {/* Key Metrics with Confidence Intervals */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Robustness Score</p>
            <Shield className={`h-6 w-6 ${getRobustnessColor(robustnessScore)}`} />
          </div>
          <p className={`text-3xl font-bold ${getRobustnessColor(robustnessScore)}`}>
            {robustnessScore.toFixed(0)}/100
          </p>
          <p className="text-xs text-muted-foreground mt-1">{getRobustnessLabel(robustnessScore)}</p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Success Rate</p>
            <Target className="h-6 w-6 text-primary" />
          </div>
          <p className="text-3xl font-bold">{successRate.toFixed(1)}%</p>
          <p className="text-xs text-muted-foreground mt-1">
            {Math.round((successRate / 100) * simulations.length)}/{simulations.length} profitable
          </p>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-muted-foreground">Simulations</p>
            <Activity className="h-6 w-6 text-blue-500" />
          </div>
          <p className="text-3xl font-bold">{simulations.length}</p>
          <p className="text-xs text-muted-foreground mt-1">Randomized scenarios</p>
        </Card>
      </div>

      {/* Confidence Intervals */}
      <Card className="p-6">
        <h3 className="text-lg font-semibold mb-4">📊 Performance Confidence Intervals (95%)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Total Return</span>
                <span className="text-sm text-muted-foreground">
                  Mean: {aggregateMetrics.totalReturn.mean.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-red-500">{aggregateMetrics.totalReturn.ci95Lower.toFixed(2)}%</span>
                <div className="flex-1 h-2 bg-muted rounded-full relative overflow-hidden">
                  <div
                    className="absolute h-full bg-green-500 opacity-30"
                    style={{
                      left: `${((aggregateMetrics.totalReturn.ci95Lower - aggregateMetrics.totalReturn.min) / (aggregateMetrics.totalReturn.max - aggregateMetrics.totalReturn.min)) * 100}%`,
                      right: `${100 - ((aggregateMetrics.totalReturn.ci95Upper - aggregateMetrics.totalReturn.min) / (aggregateMetrics.totalReturn.max - aggregateMetrics.totalReturn.min)) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-green-500">{aggregateMetrics.totalReturn.ci95Upper.toFixed(2)}%</span>
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                σ = {aggregateMetrics.totalReturn.std.toFixed(2)}%
              </p>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Win Rate</span>
                <span className="text-sm text-muted-foreground">
                  Mean: {aggregateMetrics.winRate.mean.toFixed(1)}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs">{aggregateMetrics.winRate.ci95Lower.toFixed(1)}%</span>
                <div className="flex-1 h-2 bg-muted rounded-full relative overflow-hidden">
                  <div
                    className="absolute h-full bg-primary opacity-30"
                    style={{
                      left: `${((aggregateMetrics.winRate.ci95Lower - aggregateMetrics.winRate.min) / (aggregateMetrics.winRate.max - aggregateMetrics.winRate.min)) * 100}%`,
                      right: `${100 - ((aggregateMetrics.winRate.ci95Upper - aggregateMetrics.winRate.min) / (aggregateMetrics.winRate.max - aggregateMetrics.winRate.min)) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs">{aggregateMetrics.winRate.ci95Upper.toFixed(1)}%</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Profit Factor</span>
                <span className="text-sm text-muted-foreground">
                  Mean: {aggregateMetrics.profitFactor.mean.toFixed(2)}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs">{aggregateMetrics.profitFactor.ci95Lower.toFixed(2)}</span>
                <div className="flex-1 h-2 bg-muted rounded-full relative overflow-hidden">
                  <div
                    className="absolute h-full bg-yellow-500 opacity-30"
                    style={{
                      left: `${((aggregateMetrics.profitFactor.ci95Lower - aggregateMetrics.profitFactor.min) / (aggregateMetrics.profitFactor.max - aggregateMetrics.profitFactor.min)) * 100}%`,
                      right: `${100 - ((aggregateMetrics.profitFactor.ci95Upper - aggregateMetrics.profitFactor.min) / (aggregateMetrics.profitFactor.max - aggregateMetrics.profitFactor.min)) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs">{aggregateMetrics.profitFactor.ci95Upper.toFixed(2)}</span>
              </div>
            </div>

            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">Max Drawdown</span>
                <span className="text-sm text-muted-foreground">
                  Mean: {aggregateMetrics.maxDrawdown.mean.toFixed(2)}%
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs">{aggregateMetrics.maxDrawdown.ci95Lower.toFixed(2)}%</span>
                <div className="flex-1 h-2 bg-muted rounded-full relative overflow-hidden">
                  <div
                    className="absolute h-full bg-red-500 opacity-30"
                    style={{
                      left: `${((aggregateMetrics.maxDrawdown.ci95Lower - aggregateMetrics.maxDrawdown.min) / (aggregateMetrics.maxDrawdown.max - aggregateMetrics.maxDrawdown.min)) * 100}%`,
                      right: `${100 - ((aggregateMetrics.maxDrawdown.ci95Upper - aggregateMetrics.maxDrawdown.min) / (aggregateMetrics.maxDrawdown.max - aggregateMetrics.maxDrawdown.min)) * 100}%`,
                    }}
                  />
                </div>
                <span className="text-xs">{aggregateMetrics.maxDrawdown.ci95Upper.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Charts */}
      <Tabs defaultValue="distribution" className="w-full">
        <TabsList>
          <TabsTrigger value="distribution">Return Distribution</TabsTrigger>
          <TabsTrigger value="scatter">Risk/Return</TabsTrigger>
          <TabsTrigger value="summary">Summary Stats</TabsTrigger>
        </TabsList>

        <TabsContent value="distribution">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Return Distribution Histogram</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={returnHistogram}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="range" stroke="hsl(var(--muted-foreground))" label={{ value: 'Return (%)', position: 'insideBottom', offset: -5 }} />
                <YAxis stroke="hsl(var(--muted-foreground))" label={{ value: 'Frequency', angle: -90, position: 'insideLeft' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Bar dataKey="count" fill="hsl(var(--primary))" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="scatter">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Risk vs Return (All Simulations)</h3>
            <ResponsiveContainer width="100%" height={400}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis
                  type="number"
                  dataKey="maxDrawdown"
                  name="Max Drawdown"
                  stroke="hsl(var(--muted-foreground))"
                  label={{ value: 'Max Drawdown (%)', position: 'insideBottom', offset: -5 }}
                />
                <YAxis
                  type="number"
                  dataKey="totalReturn"
                  name="Total Return"
                  stroke="hsl(var(--muted-foreground))"
                  label={{ value: 'Total Return (%)', angle: -90, position: 'insideLeft' }}
                />
                <Tooltip
                  cursor={{ strokeDasharray: '3 3' }}
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Scatter name="Simulations" data={scatterData} fill="hsl(var(--primary))" fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="summary">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Statistical Summary</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              {[
                { label: 'Best Return', value: `${aggregateMetrics.totalReturn.max.toFixed(2)}%`, color: 'text-green-500' },
                { label: 'Worst Return', value: `${aggregateMetrics.totalReturn.min.toFixed(2)}%`, color: 'text-red-500' },
                { label: 'Median Return', value: `${aggregateMetrics.totalReturn.median.toFixed(2)}%` },
                { label: 'Best Win Rate', value: `${aggregateMetrics.winRate.max.toFixed(1)}%`, color: 'text-green-500' },
                { label: 'Worst Win Rate', value: `${aggregateMetrics.winRate.min.toFixed(1)}%`, color: 'text-red-500' },
                { label: 'Median Sharpe', value: aggregateMetrics.sharpeRatio.median.toFixed(2) },
              ].map((stat, i) => (
                <div key={i} className="p-4 border rounded-lg">
                  <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
                  <p className={`text-xl font-bold ${stat.color || ''}`}>{stat.value}</p>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};
