import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAutonomousTrading } from '@/hooks/useAutonomousTrading';
import { Activity, Play, Square, TrendingUp, Zap } from 'lucide-react';

export const AutonomousTradingPanel = () => {
  const {
    isActive,
    tradesExecuted,
    totalProfit,
    topPairs,
    isScanning,
    start,
    stop,
  } = useAutonomousTrading();

  return (
    <Card className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="h-5 w-5 text-yellow-500" />
            Autonomous Trading Engine
          </h3>
          <p className="text-sm text-muted-foreground">
            AI-powered multi-pair profit maximization
          </p>
        </div>
        {isActive ? (
          <Button onClick={stop} variant="destructive" size="lg">
            <Square className="h-4 w-4 mr-2" />
            Stop Trading
          </Button>
        ) : (
          <Button onClick={start} size="lg">
            <Play className="h-4 w-4 mr-2" />
            Start Trading
          </Button>
        )}
      </div>

      {/* Status */}
      <div className="grid grid-cols-3 gap-4">
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="text-2xl font-bold">{tradesExecuted}</div>
          <div className="text-xs text-muted-foreground">Trades Executed</div>
        </div>
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="text-2xl font-bold text-green-500">
            ${totalProfit.toFixed(2)}
          </div>
          <div className="text-xs text-muted-foreground">Net Profit</div>
        </div>
        <div className="p-4 rounded-lg bg-muted/50">
          <div className="flex items-center gap-2">
            {isActive ? (
              <Badge className="bg-green-500">
                <Activity className="h-3 w-3 mr-1" />
                ACTIVE
              </Badge>
            ) : (
              <Badge variant="outline">PAUSED</Badge>
            )}
          </div>
          <div className="text-xs text-muted-foreground mt-2">Status</div>
        </div>
      </div>

      {/* Top Opportunities */}
      <div>
        <h4 className="text-sm font-medium mb-3 flex items-center gap-2">
          <TrendingUp className="h-4 w-4" />
          Top 10 Opportunities
          {isScanning && <span className="text-xs text-muted-foreground">(Scanning...)</span>}
        </h4>
        <div className="space-y-2 max-h-[300px] overflow-y-auto">
          {topPairs.map((pair) => (
            <div
              key={pair.symbol}
              className="flex items-center justify-between p-3 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <div className="flex-1">
                <div className="font-medium text-sm">{pair.symbol}</div>
                <div className="text-xs text-muted-foreground">
                  ${pair.price.toFixed(2)} • Vol: ${(pair.volume24h / 1e6).toFixed(2)}M
                </div>
              </div>
              <div className="text-right">
                <div
                  className={`text-sm font-medium ${
                    pair.priceChange24h > 0 ? 'text-green-500' : 'text-red-500'
                  }`}
                >
                  {pair.priceChange24h > 0 ? '+' : ''}
                  {pair.priceChange24h.toFixed(2)}%
                </div>
                <div className="text-xs text-muted-foreground">
                  Score: {pair.opportunityScore.toFixed(1)}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
