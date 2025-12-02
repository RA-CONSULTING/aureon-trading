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
      bgGlow: 'hover:shadow-glow-love',
    },
    {
      icon: TrendingUp,
      label: 'Net P&L Today',
      value: `${metrics.netPnLToday >= 0 ? '+' : ''}$${metrics.netPnLToday.toFixed(2)}`,
      subValue: `ROI: ${metrics.roiPercent.toFixed(2)}%`,
      color: metrics.netPnLToday >= 0 ? 'text-success' : 'text-destructive',
      bgGlow: metrics.netPnLToday >= 0 ? 'hover:shadow-glow-love' : '',
    },
    {
      icon: Zap,
      label: 'Trades Today',
      value: `${metrics.tradesToday}`,
      subValue: `Queue: ${metrics.queueDepth}`,
      color: 'text-love',
      bgGlow: 'hover:shadow-glow-prism',
    },
    {
      icon: Target,
      label: 'Win Rate',
      value: `${metrics.winRate.toFixed(1)}%`,
      subValue: `Avg: $${metrics.avgPositionSize.toFixed(2)}`,
      color: 'text-accent',
      bgGlow: 'hover:shadow-glow-prism',
    },
    {
      icon: Activity,
      label: 'Coherence',
      value: `Γ ${metrics.currentCoherence.toFixed(3)}`,
      subValue: `L ${metrics.currentLighthouse.toFixed(3)}`,
      color: metrics.currentCoherence >= 0.945 ? 'text-primary' : 'text-love',
      bgGlow: metrics.currentCoherence >= 0.945 ? 'hover:shadow-glow-love' : '',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
      {kpiCards.map((kpi, index) => {
        const Icon = kpi.icon;
        return (
          <Card 
            key={index} 
            className={`p-4 bg-card/60 backdrop-blur border-border/40 transition-all duration-300 card-hover-glow ${kpi.bgGlow}`}
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex items-start justify-between">
              <div className="space-y-1 flex-1 min-w-0">
                <p className="text-xs text-muted-foreground truncate">{kpi.label}</p>
                <p className={`text-xl font-bold ${kpi.color} truncate`}>
                  {kpi.value}
                </p>
                <p className="text-[10px] text-muted-foreground truncate">
                  {kpi.subValue}
                </p>
              </div>
              <Icon className={`h-6 w-6 ${kpi.color} opacity-40 flex-shrink-0`} />
            </div>
            {isScanning && (
              <div className="mt-2 h-0.5 bg-muted rounded-full overflow-hidden">
                <div className="h-full bg-primary shimmer" style={{ width: '100%' }} />
              </div>
            )}
          </Card>
        );
      })}
    </div>
  );
}
