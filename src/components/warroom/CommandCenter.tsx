import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Play, Pause, Square, AlertTriangle } from 'lucide-react';
import type { WarState, WarConfig } from '@/hooks/useWarRoom';

interface CommandCenterProps {
  warState: WarState;
  onLaunch: () => void;
  onPause: () => void;
  onResume: () => void;
  onStop: () => void;
  onEmergencyHalt: () => void;
  onConfigUpdate: (config: Partial<WarConfig>) => void;
}

export function CommandCenter({
  warState,
  onLaunch,
  onPause,
  onResume,
  onStop,
  onEmergencyHalt,
  onConfigUpdate,
}: CommandCenterProps) {
  const { status, config } = warState;

  const getStatusBadge = () => {
    switch (status) {
      case 'active':
        return <Badge className="bg-destructive text-destructive-foreground text-lg px-4 py-2 animate-pulse">🔥 TOTAL WAR ACTIVE</Badge>;
      case 'paused':
        return <Badge variant="secondary" className="text-lg px-4 py-2">⏸️ PAUSED</Badge>;
      case 'emergency_stopped':
        return <Badge variant="destructive" className="text-lg px-4 py-2">🚨 EMERGENCY STOPPED</Badge>;
      default:
        return <Badge variant="outline" className="text-lg px-4 py-2">💤 IDLE</Badge>;
    }
  };

  return (
    <Card className="p-6 bg-card/50 backdrop-blur border-primary/20">
      <div className="flex flex-col lg:flex-row gap-6">
        {/* Status & Controls */}
        <div className="flex-1 space-y-4">
          <div className="flex items-center justify-between">
            {getStatusBadge()}
            
            <div className="flex gap-2">
              {status === 'idle' && (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button size="lg" className="bg-destructive hover:bg-destructive/90">
                      <Play className="h-5 w-5 mr-2" />
                      LAUNCH ASSAULT
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>🔥 Launch Total War?</AlertDialogTitle>
                      <AlertDialogDescription>
                        Mode: <strong>{config.mode.toUpperCase()}</strong><br />
                        Lighthouse Threshold: <strong>Γ ≥ {config.lighthouseThreshold}</strong><br />
                        Position Cap: <strong>${config.positionCapUSD}</strong><br />
                        Max Symbols: <strong>{config.maxSymbols}</strong>
                        {config.mode === 'live' && (
                          <div className="mt-4 p-4 bg-destructive/10 border border-destructive rounded">
                            ⚠️ <strong>WARNING:</strong> This will execute REAL trades with REAL money!
                          </div>
                        )}
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={onLaunch} className="bg-destructive">
                        ENGAGE
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              )}

              {status === 'active' && (
                <>
                  <Button size="lg" variant="secondary" onClick={onPause}>
                    <Pause className="h-5 w-5 mr-2" />
                    Pause
                  </Button>
                  <Button size="lg" variant="outline" onClick={onStop}>
                    <Square className="h-5 w-5 mr-2" />
                    Stop
                  </Button>
                </>
              )}

              {status === 'paused' && (
                <>
                  <Button size="lg" className="bg-destructive" onClick={onResume}>
                    <Play className="h-5 w-5 mr-2" />
                    Resume
                  </Button>
                  <Button size="lg" variant="outline" onClick={onStop}>
                    <Square className="h-5 w-5 mr-2" />
                    Stop
                  </Button>
                </>
              )}

              {(status === 'active' || status === 'paused') && (
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button size="lg" variant="destructive">
                      <AlertTriangle className="h-5 w-5 mr-2" />
                      EMERGENCY
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>🚨 Emergency Stop?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will immediately:
                        <ul className="list-disc list-inside mt-2 space-y-1">
                          <li>Cancel ALL open orders</li>
                          <li>Close ALL open positions</li>
                          <li>Disable trading system</li>
                        </ul>
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction onClick={onEmergencyHalt} className="bg-destructive">
                        EXECUTE EMERGENCY STOP
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              )}
            </div>
          </div>
        </div>

        {/* Configuration */}
        <div className="flex-1 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label>Lighthouse Threshold (Γ)</Label>
              <Input
                type="number"
                min="0.01"
                max="0.99"
                step="0.01"
                value={config.lighthouseThreshold}
                onChange={(e) => onConfigUpdate({ lighthouseThreshold: parseFloat(e.target.value) })}
                disabled={status === 'active'}
              />
            </div>

            <div className="space-y-2">
              <Label>Position Cap ($)</Label>
              <Input
                type="number"
                min="10"
                max="1000"
                step="10"
                value={config.positionCapUSD}
                onChange={(e) => onConfigUpdate({ positionCapUSD: parseInt(e.target.value) })}
                disabled={status === 'active'}
              />
            </div>

            <div className="space-y-2">
              <Label>Max Symbols</Label>
              <Input
                type="number"
                min="5"
                max="100"
                step="5"
                value={config.maxSymbols}
                onChange={(e) => onConfigUpdate({ maxSymbols: parseInt(e.target.value) })}
                disabled={status === 'active'}
              />
            </div>

            <div className="space-y-2">
              <Label>Trading Mode</Label>
              <div className="flex items-center gap-2 h-10">
                <span className="text-sm">🧪 Paper</span>
                <Switch
                  checked={config.mode === 'live'}
                  onCheckedChange={(checked) => onConfigUpdate({ mode: checked ? 'live' : 'paper' })}
                  disabled={status === 'active'}
                />
                <span className="text-sm">🔥 Live</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
