import { TradingModeToggle } from './TradingModeToggle';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGlobalState } from '@/hooks/useGlobalState';
import { Zap, Activity, Clock } from 'lucide-react';

interface TradeControlsHeaderProps {
  onLaunchAssault: () => void;
  onEmergencyStop: () => void;
  status: 'idle' | 'active' | 'emergency_stopped';
  tradesExecuted: number;
  netPnL: number;
  currentBalance: number;
}

export function TradeControlsHeader({
  onLaunchAssault,
  onEmergencyStop,
  status,
  tradesExecuted,
  netPnL,
  currentBalance,
}: TradeControlsHeaderProps) {
  const globalState = useGlobalState();

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardContent className="p-4">
        <div className="flex flex-wrap items-center justify-between gap-4">
          {/* Left: Trading Mode + Status */}
          <div className="flex items-center gap-4">
            <TradingModeToggle userId={globalState.userId} />
            
            <div className="flex items-center gap-2">
              <Badge 
                variant={status === 'active' ? 'default' : status === 'emergency_stopped' ? 'destructive' : 'secondary'}
                className={status === 'active' ? 'bg-green-500 animate-pulse' : ''}
              >
                {status === 'idle' && '⏸️ IDLE'}
                {status === 'active' && '🔥 ACTIVE'}
                {status === 'emergency_stopped' && '🚨 STOPPED'}
              </Badge>
              
              {globalState.isRunning && (
                <Badge variant="outline" className="flex items-center gap-1">
                  <Activity className="h-3 w-3" />
                  Systems Online
                </Badge>
              )}
            </div>
          </div>

          {/* Center: Stats */}
          <div className="flex items-center gap-6">
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Balance</p>
              <p className="text-lg font-bold text-green-500">${currentBalance.toFixed(2)}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Trades</p>
              <p className="text-lg font-bold text-primary">{tradesExecuted}</p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground">Net P&L</p>
              <p className={`text-lg font-bold ${netPnL >= 0 ? 'text-green-500' : 'text-destructive'}`}>
                {netPnL >= 0 ? '+' : ''}${netPnL.toFixed(2)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-xs text-muted-foreground flex items-center gap-1">
                <Clock className="h-3 w-3" /> Next Cycle
              </p>
              <p className="text-lg font-bold">{globalState.nextCheckIn}s</p>
            </div>
          </div>

          {/* Right: Action Buttons */}
          <div className="flex items-center gap-2">
            {status === 'idle' && (
              <Button
                size="lg"
                onClick={onLaunchAssault}
                className="bg-gradient-to-r from-green-500 to-primary hover:from-green-600 hover:to-primary/90 text-white font-bold"
              >
                <Zap className="h-4 w-4 mr-2" />
                LAUNCH ASSAULT
              </Button>
            )}
            {status === 'active' && (
              <Button
                size="lg"
                variant="destructive"
                onClick={onEmergencyStop}
                className="font-bold animate-pulse"
              >
                🚨 EMERGENCY STOP
              </Button>
            )}
            {status === 'emergency_stopped' && (
              <Button
                size="lg"
                onClick={onLaunchAssault}
                className="bg-gradient-to-r from-amber-500 to-orange-500 hover:from-amber-600 hover:to-orange-600 text-white font-bold"
              >
                🔄 RESUME TRADING
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
