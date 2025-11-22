import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAutomatedHunt } from '@/hooks/useAutomatedHunt';
import { useState } from 'react';
import { Target, PlayCircle, StopCircle, RefreshCw, TrendingUp, Activity } from 'lucide-react';

export function AutomatedHuntControl() {
  const { huntSession, recentTargets, isScanning, startHunt, stopHunt, triggerScan } = useAutomatedHunt();
  
  const [config, setConfig] = useState({
    minVolatility: 2.0,
    minVolume: 100000,
    maxTargets: 5,
    scanInterval: 300,
  });

  const handleStart = async () => {
    await startHunt(config);
  };

  const isActive = huntSession?.status === 'active';

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Target className={`h-5 w-5 ${isActive ? 'text-success animate-pulse' : 'text-muted-foreground'}`} />
          🦁 Automated Hunt Loop
        </CardTitle>
        <CardDescription>
          Pride Scanner + QGITA + OMS — Continuous opportunity detection
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Hunt Status */}
        {huntSession && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Status</span>
              <Badge variant={isActive ? 'default' : 'secondary'}>
                {isActive ? '🟢 Hunting' : '⏸️ Stopped'}
              </Badge>
            </div>
            
            {/* Statistics Grid */}
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 rounded-lg border border-border/50 bg-background/50">
                <div className="text-xs text-muted-foreground mb-1">Scans</div>
                <div className="text-xl font-bold text-foreground">{huntSession.total_scans}</div>
              </div>
              <div className="p-3 rounded-lg border border-border/50 bg-background/50">
                <div className="text-xs text-muted-foreground mb-1">Targets</div>
                <div className="text-xl font-bold text-foreground">{huntSession.total_targets_found}</div>
              </div>
              <div className="p-3 rounded-lg border border-border/50 bg-background/50">
                <div className="text-xs text-muted-foreground mb-1">Signals</div>
                <div className="text-xl font-bold text-success">{huntSession.total_signals_generated}</div>
              </div>
              <div className="p-3 rounded-lg border border-border/50 bg-background/50">
                <div className="text-xs text-muted-foreground mb-1">Queued</div>
                <div className="text-xl font-bold text-primary">{huntSession.total_orders_queued}</div>
              </div>
            </div>

            {/* Last Scan Time */}
            {huntSession.last_scan_at && (
              <div className="text-xs text-muted-foreground">
                Last scan: {new Date(huntSession.last_scan_at).toLocaleTimeString()}
              </div>
            )}
          </div>
        )}

        {/* Configuration (only show when not active) */}
        {!isActive && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label className="text-xs">Min Volatility %</Label>
                <Input
                  type="number"
                  value={config.minVolatility}
                  onChange={(e) => setConfig({ ...config, minVolatility: parseFloat(e.target.value) })}
                  step={0.5}
                  min={0}
                  className="h-8"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Min Volume ($)</Label>
                <Input
                  type="number"
                  value={config.minVolume}
                  onChange={(e) => setConfig({ ...config, minVolume: parseFloat(e.target.value) })}
                  step={10000}
                  min={0}
                  className="h-8"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Max Targets</Label>
                <Input
                  type="number"
                  value={config.maxTargets}
                  onChange={(e) => setConfig({ ...config, maxTargets: parseInt(e.target.value) })}
                  min={1}
                  max={20}
                  className="h-8"
                />
              </div>
              <div className="space-y-2">
                <Label className="text-xs">Scan Interval (s)</Label>
                <Input
                  type="number"
                  value={config.scanInterval}
                  onChange={(e) => setConfig({ ...config, scanInterval: parseInt(e.target.value) })}
                  step={60}
                  min={60}
                  className="h-8"
                />
              </div>
            </div>
          </div>
        )}

        {/* Recent Targets */}
        {recentTargets.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Recent Targets
            </h4>
            <div className="space-y-2 max-h-[200px] overflow-y-auto">
              {recentTargets.slice(0, 5).map((target) => (
                <div 
                  key={target.id}
                  className="flex items-center justify-between p-2 rounded border border-border/50 bg-background/30"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-semibold text-foreground">{target.symbol}</span>
                    {target.order_queued && (
                      <Badge variant="default" className="text-xs">Queued</Badge>
                    )}
                    {target.signal_tier && (
                      <Badge variant="outline" className="text-xs">T{target.signal_tier}</Badge>
                    )}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Score: {target.opportunity_score.toFixed(0)} | {target.volatility_24h.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Controls */}
        <div className="flex gap-2">
          {isActive ? (
            <>
              <Button
                onClick={() => triggerScan()}
                disabled={isScanning}
                variant="outline"
                className="flex-1"
              >
                {isScanning ? (
                  <>
                    <Activity className="mr-2 h-4 w-4 animate-spin" />
                    Scanning...
                  </>
                ) : (
                  <>
                    <RefreshCw className="mr-2 h-4 w-4" />
                    Scan Now
                  </>
                )}
              </Button>
              <Button
                onClick={stopHunt}
                variant="destructive"
                className="flex-1"
              >
                <StopCircle className="mr-2 h-4 w-4" />
                Stop Hunt
              </Button>
            </>
          ) : (
            <Button
              onClick={handleStart}
              className="w-full"
            >
              <PlayCircle className="mr-2 h-4 w-4" />
              Start Hunt
            </Button>
          )}
        </div>

        {/* Info Box */}
        <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
          <p className="text-xs text-foreground">
            🦁 <strong>Hunt Loop:</strong> Scans all USDT pairs, calculates opportunity scores 
            (volatility × volume), generates QGITA signals for top targets, and queues orders via OMS.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
