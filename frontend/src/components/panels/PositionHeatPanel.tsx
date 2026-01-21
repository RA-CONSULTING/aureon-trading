import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { positionHeatTracker, HeatState } from '@/core/positionHeatTracker';
import { Flame, ThermometerSun } from 'lucide-react';
import { cn } from '@/lib/utils';

export const PositionHeatPanel = () => {
  const [heatState, setHeatState] = useState<HeatState>({
    totalHeat: 0,
    btcHeat: 0,
    ethHeat: 0,
    altHeat: 0,
    stableHeat: 0,
    canAddPosition: true,
    maxHeatReached: false
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setHeatState(positionHeatTracker.getHeatState());
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  const heatPercent = (heatState.totalHeat / 0.9) * 100;
  
  const getHeatColor = (percent: number) => {
    if (percent < 50) return 'text-green-500';
    if (percent < 75) return 'text-yellow-500';
    return 'text-red-500';
  };

  const heatGroups = [
    { name: 'BTC', heat: heatState.btcHeat },
    { name: 'ETH', heat: heatState.ethHeat },
    { name: 'ALTS', heat: heatState.altHeat },
    { name: 'STABLES', heat: heatState.stableHeat },
  ].filter(g => g.heat > 0);

  return (
    <Card className="border-border/50 bg-card/50 backdrop-blur">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Flame className="h-4 w-4 text-primary" />
          Position Heat Tracker
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Total Heat</span>
            <span className={cn("font-mono font-bold", getHeatColor(heatPercent))}>
              {(heatState.totalHeat * 100).toFixed(1)}% / 90%
            </span>
          </div>
          <Progress value={Math.min(heatPercent, 100)} className="h-2" />
        </div>

        <div className="grid grid-cols-2 gap-2">
          <div className={cn(
            "flex items-center justify-center gap-2 p-2 rounded text-xs",
            heatState.canAddPosition ? "bg-green-500/10 text-green-500" : "bg-red-500/10 text-red-500"
          )}>
            <ThermometerSun className="h-3 w-3" />
            {heatState.canAddPosition ? 'Can Add' : 'Heat Limit'}
          </div>
          <div className={cn(
            "flex items-center justify-center gap-2 p-2 rounded text-xs",
            heatState.maxHeatReached ? "bg-red-500/10 text-red-500" : "bg-muted/30 text-muted-foreground"
          )}>
            {heatState.maxHeatReached ? '⚠️ Max Heat' : '✓ OK'}
          </div>
        </div>

        <div className="space-y-1">
          <div className="text-xs text-muted-foreground mb-2">Heat by Group</div>
          {heatGroups.length === 0 ? (
            <div className="text-xs text-muted-foreground text-center py-2">No positions</div>
          ) : (
            heatGroups.map(({ name, heat }) => (
              <div key={name} className="flex items-center justify-between text-xs p-1.5 rounded bg-muted/20">
                <span className="font-medium">{name}</span>
                <span className={cn("font-mono", getHeatColor((heat / 0.5) * 100))}>
                  {(heat * 100).toFixed(1)}%
                </span>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
