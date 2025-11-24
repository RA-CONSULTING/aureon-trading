import { Card } from '@/components/ui/card';
import { DollarSign, TrendingUp, Zap, Target, Activity } from 'lucide-react';
import type { WarMetrics } from '@/hooks/useWarMetrics';
import type { BalanceTotals } from '@/hooks/useBinanceBalances';

interface MetricsHQProps {
  metrics: WarMetrics;
  totals: BalanceTotals;
  isScanning: boolean;
}

export function MetricsHQ({ metrics, totals, isScanning }: MetricsHQProps) {
  const kpiCards = [
    {
      icon: DollarSign,
      label: 'Total Balance',
      value: `$${totals.totalUSDValue.toFixed(2)}`,
      subValue: `${totals.BTC.toFixed(4)} BTC · ${totals.USDT.toFixed(2)} USDT`,
      color: 'text-primary',
    },
    {
      icon: TrendingUp,
      label: 'Net P&L Today',
      value: `${metrics.netPnLToday >= 0 ? '+' : ''}$${metrics.netPnLToday.toFixed(2)}`,
      subValue: `ROI: ${metrics.roiPercent.toFixed(2)}%`,
      color: metrics.netPnLToday >= 0 ? 'text-green-500' : 'text-red-500',
    },
    {
      icon: Zap,
      label: 'Trades Today',
      value: `${metrics.tradesToday}`,
      subValue: `Queue: ${metrics.queueDepth}`,
      color: 'text-yellow-500',
    },
    {
      icon: Target,
      label: 'Win Rate',
      value: `${metrics.winRate.toFixed(1)}%`,
      subValue: `Avg: $${metrics.avgPositionSize.toFixed(2)}`,
      color: 'text-blue-500',
    },
    {
      icon: Activity,
      label: 'Coherence',
      value: `Γ ${metrics.currentCoherence.toFixed(3)}`,
      subValue: `L ${metrics.currentLighthouse.toFixed(3)}`,
      color: metrics.currentCoherence >= 0.945 ? 'text-green-500' : 'text-yellow-500',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
      {kpiCards.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <Card key={index} className="p-4 bg-card/50 backdrop-blur border-primary/20 hover:border-primary/40 transition-all">
            <div className="flex items-start justify-between">
              <div className="space-y-1 flex-1">
                <p className="text-sm text-muted-foreground">{kpi.label}</p>
                <p className={`text-2xl font-bold ${kpi.color}`}>
                  {kpi.value}
                </p>
                <p className="text-xs text-muted-foreground">
                  {kpi.subValue}
                </p>
              </div>
              <Icon className={`h-8 w-8 ${kpi.color} opacity-50`} />
            </div>
            {isScanning && (
              <div className="mt-2 h-1 bg-primary/20 rounded-full overflow-hidden">
                <div className="h-full bg-primary animate-pulse" style={{ width: '70%' }} />
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
