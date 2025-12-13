/**
 * Anomaly Alerts Panel - Displays market manipulation alerts from CoinAPI Anomaly Detector
 */

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AlertTriangle, ShieldCheck, ShieldAlert, Eye } from 'lucide-react';
import { coinAPIAnomalyDetector, AnomalyAlert } from '@/core/detection/coinAPIAnomalyDetector';
import { format } from 'date-fns';

export default function AnomalyAlertsPanel() {
  const [alerts, setAlerts] = useState<AnomalyAlert[]>([]);
  const [state, setState] = useState(coinAPIAnomalyDetector.getState());

  useEffect(() => {
    // Initial load
    setAlerts(coinAPIAnomalyDetector.getActiveAlerts());
    setState(coinAPIAnomalyDetector.getState());

    // Poll for updates every 5 seconds
    const interval = setInterval(() => {
      setAlerts(coinAPIAnomalyDetector.getActiveAlerts());
      setState(coinAPIAnomalyDetector.getState());
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  const criticalCount = alerts.filter(a => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter(a => a.severity === 'HIGH').length;
  const hasDanger = criticalCount > 0 || highCount > 0;

  const severityColors: Record<string, string> = {
    CRITICAL: 'bg-red-500/20 text-red-400 border-red-500/50',
    HIGH: 'bg-orange-500/20 text-orange-400 border-orange-500/50',
    MEDIUM: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
    LOW: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
  };

  const typeIcons: Record<string, string> = {
    PRICE_MANIPULATION: '📈',
    WASH_TRADING: '🔄',
    FRONTRUNNING: '🏃',
    SPOOFING: '👻',
    LAYERING: '📚',
    PUMP_DUMP: '🎢',
    FLASH_CRASH: '⚡',
    ABNORMAL_SPREAD: '↔️',
    VOLUME_SPIKE: '📊',
    ORDER_IMBALANCE: '⚖️',
  };

  return (
    <Card className={`border-border/50 bg-card/50 backdrop-blur ${hasDanger ? 'border-red-500/30' : ''}`}>
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center justify-between">
          <div className="flex items-center gap-2">
            {hasDanger ? (
              <ShieldAlert className="w-5 h-5 text-red-500" />
            ) : (
              <ShieldCheck className="w-5 h-5 text-green-500" />
            )}
            Anomaly Detection
          </div>
          <div className="flex items-center gap-2 text-sm font-normal">
            {criticalCount > 0 && (
              <Badge variant="destructive" className="text-xs">
                {criticalCount} CRITICAL
              </Badge>
            )}
            {highCount > 0 && (
              <Badge className="bg-orange-500/20 text-orange-400 border-orange-500/50 text-xs">
                {highCount} HIGH
              </Badge>
            )}
            {!hasDanger && (
              <Badge className="bg-green-500/20 text-green-400 border-green-500/50 text-xs">
                ALL CLEAR
              </Badge>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* Stats Row */}
        <div className="grid grid-cols-3 gap-2 mb-3">
          <div className="text-center p-2 rounded bg-muted/30">
            <div className="text-xs text-muted-foreground">Safe Symbols</div>
            <div className="text-lg font-bold text-green-400">{state.safeSymbols.length}</div>
          </div>
          <div className="text-center p-2 rounded bg-muted/30">
            <div className="text-xs text-muted-foreground">Flagged</div>
            <div className="text-lg font-bold text-yellow-400">{state.flaggedSymbols.length}</div>
          </div>
          <div className="text-center p-2 rounded bg-muted/30">
            <div className="text-xs text-muted-foreground">Active Alerts</div>
            <div className="text-lg font-bold text-foreground">{alerts.length}</div>
          </div>
        </div>

        {/* Alerts List */}
        <ScrollArea className="h-[200px]">
          {alerts.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
              <ShieldCheck className="w-8 h-8 mb-2 text-green-500/50" />
              <p className="text-sm">No anomalies detected</p>
              <p className="text-xs">Markets appear normal</p>
            </div>
          ) : (
            <div className="space-y-2">
              {alerts.slice(0, 10).map((alert) => (
                <div 
                  key={alert.id}
                  className={`p-2 rounded border ${severityColors[alert.severity]}`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <span>{typeIcons[alert.type] || '⚠️'}</span>
                      <span className="font-bold text-foreground">{alert.symbol}</span>
                      <Badge variant="outline" className={severityColors[alert.severity]}>
                        {alert.severity}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {format(new Date(alert.timestamp), 'HH:mm:ss')}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground">{alert.description}</p>
                  <div className="flex items-center justify-between mt-1">
                    <span className="text-xs">Confidence: {(alert.confidence * 100).toFixed(0)}%</span>
                    <Badge variant="outline" className="text-xs">
                      {alert.recommendation}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Flagged Symbols */}
        {state.flaggedSymbols.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/30">
            <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
              <Eye className="w-3 h-3" />
              Flagged Symbols (Avoid Trading)
            </div>
            <div className="flex flex-wrap gap-1">
              {state.flaggedSymbols.map((symbol) => (
                <Badge key={symbol} variant="outline" className="text-xs bg-red-500/10 text-red-400 border-red-500/30">
                  {symbol}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
