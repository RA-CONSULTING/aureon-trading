import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Zap, AlertTriangle } from 'lucide-react';
import { useQGITAConfig } from '@/hooks/useQGITAConfig';

interface QGITAAutoTradingControlProps {
  isEnabled: boolean;
  onToggle: (enabled: boolean) => void;
  isExecuting: boolean;
}

export function QGITAAutoTradingControl({
  isEnabled,
  onToggle,
  isExecuting,
}: QGITAAutoTradingControlProps) {
  const { config } = useQGITAConfig();

  return (
    <Card className="border-primary/20">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" />
            <CardTitle>QGITA Auto-Trading</CardTitle>
          </div>
          {isExecuting && (
            <Badge variant="outline" className="animate-pulse">
              Executing...
            </Badge>
          )}
        </div>
        <CardDescription>
          Automatically execute trades on Tier 1 & 2 signals
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <Label htmlFor="qgita-auto-trading" className="text-base">
            Enable Auto-Trading
          </Label>
          <Switch
            id="qgita-auto-trading"
            checked={isEnabled}
            onCheckedChange={onToggle}
          />
        </div>

        {isEnabled && (
          <Alert variant="default" className="bg-primary/5 border-primary/20">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Auto-trading is <strong>ACTIVE</strong>. Trades will execute automatically when Tier 1 or Tier 2 QGITA signals are detected.
            </AlertDescription>
          </Alert>
        )}

        <div className="space-y-2 pt-2 border-t">
          <div className="text-sm font-medium">Position Size Multipliers</div>
          <div className="space-y-1 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tier 1 (80-100%):</span>
              <span className="font-medium">{(config.tier1PositionMultiplier * 100).toFixed(0)}% position</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tier 2 (60-79%):</span>
              <span className="font-medium">{(config.tier2PositionMultiplier * 100).toFixed(0)}% position</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Tier 3 (&lt;60%):</span>
              <span className="font-medium text-muted-foreground">No trade</span>
            </div>
          </div>
        </div>

        <div className="text-xs text-muted-foreground pt-2 border-t">
          Risk management rules from trading config will apply: stop loss, take profit, daily limits, and position size constraints.
        </div>
      </CardContent>
    </Card>
  );
}
