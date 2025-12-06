import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useExchangeDataVerification } from '@/hooks/useExchangeDataVerification';
import { useDataStreamMonitor } from '@/hooks/useDataStreamMonitor';
import { useBackendHealth } from '@/hooks/useBackendHealth';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw, 
  Wifi, 
  WifiOff,
  Server,
  Key,
  Activity
} from 'lucide-react';

interface SystemCheck {
  name: string;
  status: 'ok' | 'warning' | 'error' | 'offline';
  message: string;
  isRealData: boolean;
  actionNeeded?: string;
}

export function SystemHealthPanel() {
  const { verification, isLiveData, isDemoMode, liveExchangeCount, verify, getExchangeStatus } = useExchangeDataVerification();
  const { overallHealth, healthyEndpoints, unhealthyEndpoints } = useDataStreamMonitor();
  const { healthReport, refresh: refreshHealth } = useBackendHealth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await Promise.all([verify(), refreshHealth()]);
    setTimeout(() => setIsRefreshing(false), 1000);
  };

  // Helper to check exchange status
  const getExchangeCheck = (exchangeName: string, displayName: string, isRequired: boolean = false): SystemCheck => {
    const exchange = getExchangeStatus(exchangeName);
    const isConnected = exchange?.status === 'LIVE';
    
    return {
      name: `${displayName} Connection`,
      status: isConnected ? 'ok' : 'offline',
      message: isConnected 
        ? 'Connected with live data' 
        : isRequired ? 'Not connected - add API keys' : 'Not configured',
      isRealData: isConnected,
      actionNeeded: !isConnected 
        ? `Add ${displayName} API credentials ${isRequired ? '' : '(optional)'}` 
        : undefined
    };
  };

  // Build system checks
  const systemChecks: SystemCheck[] = [
    // Exchange Connections
    getExchangeCheck('binance', 'Binance', true),
    getExchangeCheck('kraken', 'Kraken', false),
    getExchangeCheck('alpaca', 'Alpaca', false),
    getExchangeCheck('capital', 'Capital.com', false),
    // Backend Health
    {
      name: 'Backend Services',
      status: healthReport?.overall_status === 'healthy' ? 'ok' : healthReport?.overall_status === 'degraded' ? 'warning' : 'error',
      message: healthReport?.overall_status === 'healthy' 
        ? 'All backend services operational' 
        : `${healthReport?.errors?.length || 0} issues detected`,
      isRealData: true,
      actionNeeded: healthReport?.overall_status !== 'healthy' 
        ? healthReport?.errors?.[0] 
        : undefined
    },
    // Data Streams
    {
      name: 'Data Streams',
      status: overallHealth === 'healthy' ? 'ok' : overallHealth === 'degraded' ? 'warning' : 'error',
      message: `${healthyEndpoints.length} healthy, ${unhealthyEndpoints.length} unhealthy`,
      isRealData: !isDemoMode,
      actionNeeded: unhealthyEndpoints.length > 0 
        ? `Fix: ${unhealthyEndpoints.join(', ')}` 
        : undefined
    },
    // Overall Data Mode
    {
      name: 'Trading Data',
      status: isLiveData ? 'ok' : isDemoMode ? 'offline' : 'warning',
      message: isLiveData 
        ? `Live data from ${liveExchangeCount} exchange(s)` 
        : 'SIMULATED - No live exchange data',
      isRealData: isLiveData,
      actionNeeded: !isLiveData 
        ? 'Connect at least one exchange for live trading' 
        : undefined
    }
  ];

  const workingCount = systemChecks.filter(c => c.status === 'ok').length;
  const needsFixCount = systemChecks.filter(c => c.status === 'error' || c.status === 'offline').length;
  const warningCount = systemChecks.filter(c => c.status === 'warning').length;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'ok': return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning': return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error': return <XCircle className="h-5 w-5 text-destructive" />;
      case 'offline': return <WifiOff className="h-5 w-5 text-muted-foreground" />;
      default: return <Activity className="h-5 w-5 text-muted-foreground" />;
    }
  };

  const getDataBadge = (isReal: boolean) => {
    if (isReal) {
      return <Badge className="bg-green-500/20 text-green-500 border-green-500/30">🟢 LIVE</Badge>;
    }
    return <Badge variant="secondary" className="bg-muted text-muted-foreground">🔴 OFFLINE</Badge>;
  };

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Server className="h-5 w-5" />
            System Health & Data Status
          </CardTitle>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
        
        {/* Summary badges */}
        <div className="flex gap-2 mt-2 flex-wrap">
          <Badge className="bg-green-500/20 text-green-500">
            ✅ {workingCount} Working
          </Badge>
          {warningCount > 0 && (
            <Badge className="bg-yellow-500/20 text-yellow-500">
              ⚠️ {warningCount} Warnings
            </Badge>
          )}
          {needsFixCount > 0 && (
            <Badge className="bg-destructive/20 text-destructive">
              ❌ {needsFixCount} Need Fix
            </Badge>
          )}
          <Badge variant={isLiveData ? "default" : "secondary"} className={isLiveData ? "bg-green-500" : ""}>
            {isLiveData ? '🟢 LIVE DATA' : '🔴 SIMULATED'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        {systemChecks.map((check, index) => (
          <div 
            key={index}
            className={`p-3 rounded-lg border ${
              check.status === 'ok' ? 'border-green-500/30 bg-green-500/5' :
              check.status === 'warning' ? 'border-yellow-500/30 bg-yellow-500/5' :
              check.status === 'offline' ? 'border-muted bg-muted/20' :
              'border-destructive/30 bg-destructive/5'
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {getStatusIcon(check.status)}
                <div>
                  <div className="font-medium flex items-center gap-2">
                    {check.name}
                    {getDataBadge(check.isRealData)}
                  </div>
                  <p className="text-sm text-muted-foreground">{check.message}</p>
                </div>
              </div>
            </div>
            
            {check.actionNeeded && (
              <div className="mt-2 p-2 rounded bg-background/50 border border-dashed">
                <p className="text-sm flex items-center gap-2">
                  <Key className="h-4 w-4 text-primary" />
                  <span className="text-primary font-medium">Action needed:</span>
                  {check.actionNeeded}
                </p>
              </div>
            )}
          </div>
        ))}

        {/* Overall status message */}
        <div className={`p-4 rounded-lg text-center ${
          isLiveData ? 'bg-green-500/10 border border-green-500/30' : 'bg-destructive/10 border border-destructive/30'
        }`}>
          {isLiveData ? (
            <div className="flex items-center justify-center gap-2 text-green-500">
              <Wifi className="h-5 w-5" />
              <span className="font-bold">LIVE TRADING READY</span>
              <span className="text-sm">- Real data from {liveExchangeCount} exchange(s)</span>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-2 text-destructive">
              <div className="flex items-center gap-2">
                <WifiOff className="h-5 w-5" />
                <span className="font-bold">OFFLINE - SIMULATED MODE</span>
              </div>
              <p className="text-sm text-muted-foreground">
                Connect at least one exchange to enable live trading
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
