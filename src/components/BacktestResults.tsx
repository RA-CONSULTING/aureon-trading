import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import type { BacktestResults } from '@/core/backtestEngine';
import { TrendingUp, TrendingDown, Target, DollarSign, Activity, Award, AlertCircle } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface BacktestResultsProps {
  results: BacktestResults | null;
}

export const BacktestResultsDisplay = ({ results }: BacktestResultsProps) => {
  if (!results) {
    return (
      <Card className="p-8 text-center">
        <Activity className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
        <h3 className="text-xl font-semibold mb-2">No Backtest Results</h3>
        <p className="text-muted-foreground">
          Configure and run a backtest above to see results
        </p>
      </Card>
    );
  }

  const { metrics, equityCurve, trades } = results;

  // Prepare equity curve data for chart
  const equityChartData = equityCurve.map(point => ({
    time: new Date(point.timestamp).toLocaleDateString(),
    equity: point.equity,
    drawdown: -point.drawdown,
  }));

  // Prepare trades distribution
  const tradesDistribution = trades.map((trade, index) => ({
    trade: index + 1,
    pnl: trade.pnl,
    pnlPercent: trade.pnlPercent,
  }));

  return (
    <div className="space-y-6">
      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Total Return</p>
              <p className={`text-2xl font-bold ${metrics.totalReturn >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                {metrics.totalReturn >= 0 ? '+' : ''}${metrics.totalReturn.toFixed(2)}
              </p>
              <p className="text-xs text-muted-foreground">
                {metrics.totalReturnPercent >= 0 ? '+' : ''}{metrics.totalReturnPercent.toFixed(2)}%
              </p>
            </div>
            <DollarSign className={`h-8 w-8 ${metrics.totalReturn >= 0 ? 'text-green-500' : 'text-red-500'}`} />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Win Rate</p>
              <p className="text-2xl font-bold">{metrics.winRate.toFixed(1)}%</p>
              <p className="text-xs text-muted-foreground">
                {metrics.winningTrades}W / {metrics.losingTrades}L
              </p>
            </div>
            <Target className="h-8 w-8 text-primary" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Max Drawdown</p>
              <p className="text-2xl font-bold text-red-500">
                {metrics.maxDrawdownPercent.toFixed(2)}%
              </p>
              <p className="text-xs text-muted-foreground">Peak to trough</p>
            </div>
            <TrendingDown className="h-8 w-8 text-red-500" />
          </div>
        </Card>

        <Card className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-muted-foreground">Profit Factor</p>
              <p className="text-2xl font-bold">{metrics.profitFactor.toFixed(2)}</p>
              <p className="text-xs text-muted-foreground">
                Sharpe: {metrics.sharpeRatio.toFixed(2)}
              </p>
            </div>
            <Award className="h-8 w-8 text-yellow-500" />
          </div>
        </Card>
      </div>

      {/* Additional Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="p-4">
          <p className="text-sm text-muted-foreground mb-1">Total Trades</p>
          <p className="text-xl font-bold">{metrics.totalTrades}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Win</p>
          <p className="text-xl font-bold text-green-500">+${metrics.avgWin.toFixed(2)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Loss</p>
          <p className="text-xl font-bold text-red-500">-${metrics.avgLoss.toFixed(2)}</p>
        </Card>
        <Card className="p-4">
          <p className="text-sm text-muted-foreground mb-1">Avg Duration</p>
          <p className="text-xl font-bold">{metrics.avgTradeDuration.toFixed(0)}m</p>
        </Card>
      </div>

      {/* Charts */}
      <Tabs defaultValue="equity" className="w-full">
        <TabsList>
          <TabsTrigger value="equity">Equity Curve</TabsTrigger>
          <TabsTrigger value="drawdown">Drawdown</TabsTrigger>
          <TabsTrigger value="trades">Trade Distribution</TabsTrigger>
          <TabsTrigger value="details">Trade Details</TabsTrigger>
        </TabsList>

        <TabsContent value="equity">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Equity Curve</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={equityChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="equity"
                  stroke="hsl(var(--primary))"
                  strokeWidth={2}
                  name="Portfolio Value ($)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="drawdown">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Drawdown</h3>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={equityChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="time" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="drawdown"
                  stroke="hsl(var(--destructive))"
                  strokeWidth={2}
                  name="Drawdown (%)"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="trades">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Trade P&L Distribution</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={tradesDistribution}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="trade" stroke="hsl(var(--muted-foreground))" />
                <YAxis stroke="hsl(var(--muted-foreground))" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                <Bar dataKey="pnl" name="P&L ($)">
                  {tradesDistribution.map((entry, index) => (
                    <rect key={`bar-${index}`} fill={entry.pnl >= 0 ? 'hsl(var(--chart-2))' : 'hsl(var(--destructive))'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </TabsContent>

        <TabsContent value="details">
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">Trade Details</h3>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {trades.map((trade, index) => (
                <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium">#{index + 1}</span>
                    <Badge variant={trade.side === 'LONG' ? 'default' : 'destructive'}>
                      {trade.side}
                    </Badge>
                    <span className="text-sm text-muted-foreground">
                      {new Date(trade.entryTime).toLocaleDateString()}
                    </span>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-xs text-muted-foreground">Entry → Exit</p>
                      <p className="text-sm font-mono">
                        ${trade.entryPrice.toFixed(2)} → ${trade.exitPrice.toFixed(2)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className={`text-lg font-bold ${trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                      </p>
                      <p className="text-xs text-muted-foreground">{trade.exitReason}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Best/Worst Trades */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <Award className="h-5 w-5 text-green-500" />
            <h3 className="text-lg font-semibold">Best Trade</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">P&L</span>
              <span className="text-lg font-bold text-green-500">+${metrics.largestWin.toFixed(2)}</span>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <AlertCircle className="h-5 w-5 text-red-500" />
            <h3 className="text-lg font-semibold">Worst Trade</h3>
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-muted-foreground">P&L</span>
              <span className="text-lg font-bold text-red-500">${metrics.largestLoss.toFixed(2)}</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};
