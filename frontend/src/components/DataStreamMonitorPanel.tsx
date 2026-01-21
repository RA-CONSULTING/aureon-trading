import { useState } from 'react';
import { useDataStreamMonitor } from '@/hooks/useDataStreamMonitor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  ArrowUpCircle, 
  ArrowDownCircle, 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  Trash2,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';

export function DataStreamMonitorPanel() {
  const {
    streams,
    stats,
    totalRequests,
    totalErrors,
    overallHealth,
    lastUpdate,
    healthyEndpoints,
    unhealthyEndpoints,
    clearHistory,
  } = useDataStreamMonitor();
  
  const [selectedEndpoint, setSelectedEndpoint] = useState<string | null>(null);

  const getHealthIcon = () => {
    switch (overallHealth) {
      case 'healthy': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'degraded': return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'down': return <XCircle className="h-4 w-4 text-red-500" />;
    }
  };

  const getHealthBadge = () => {
    switch (overallHealth) {
      case 'healthy': return <Badge variant="default" className="bg-green-600">HEALTHY</Badge>;
      case 'degraded': return <Badge variant="secondary" className="bg-yellow-600">DEGRADED</Badge>;
      case 'down': return <Badge variant="destructive">DOWN</Badge>;
    }
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  const statArray = Array.from(stats.values()).sort((a, b) => {
    // Sort by: unhealthy first, then by total requests desc
    if (a.isHealthy !== b.isHealthy) return a.isHealthy ? 1 : -1;
    return (b.successCount + b.errorCount) - (a.successCount + a.errorCount);
  });

  return (
    <Card className="border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Activity className="h-4 w-4" />
            DATA STREAM MONITOR
            {getHealthIcon()}
            {getHealthBadge()}
          </CardTitle>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span>{totalRequests} requests</span>
            <span className="text-red-400">{totalErrors} errors</span>
            <Button variant="ghost" size="sm" onClick={clearHistory}>
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </div>
        <div className="flex items-center gap-2 text-[10px] text-muted-foreground mt-1">
          <RefreshCw className="h-3 w-3" />
          Last update: {formatTime(lastUpdate)}
          <span className="ml-2">
            {healthyEndpoints.length} healthy / {unhealthyEndpoints.length} unhealthy
          </span>
        </div>
      </CardHeader>
      
      <CardContent>
        <Tabs defaultValue="endpoints" className="w-full">
          <TabsList className="grid w-full grid-cols-2 mb-3">
            <TabsTrigger value="endpoints" className="text-xs">Endpoints</TabsTrigger>
            <TabsTrigger value="live" className="text-xs">Live Stream</TabsTrigger>
          </TabsList>
          
          <TabsContent value="endpoints">
            <ScrollArea className="h-[300px]">
              <div className="space-y-1">
                {statArray.map((stat) => (
                  <div 
                    key={stat.endpoint}
                    className={cn(
                      "flex items-center justify-between p-2 rounded-md text-xs cursor-pointer hover:bg-muted/50 transition-colors",
                      selectedEndpoint === stat.endpoint && "bg-muted",
                      !stat.isHealthy && (stat.successCount > 0 || stat.errorCount > 0) && "border-l-2 border-yellow-500"
                    )}
                    onClick={() => setSelectedEndpoint(stat.endpoint === selectedEndpoint ? null : stat.endpoint)}
                  >
                    <div className="flex items-center gap-2">
                      {stat.isHealthy ? (
                        <CheckCircle className="h-3 w-3 text-green-500" />
                      ) : stat.successCount > 0 || stat.errorCount > 0 ? (
                        <AlertTriangle className="h-3 w-3 text-yellow-500" />
                      ) : (
                        <XCircle className="h-3 w-3 text-muted-foreground" />
                      )}
                      <span className="font-mono truncate max-w-[180px]" title={stat.endpoint}>
                        {stat.endpoint}
                      </span>
                    </div>
                    
                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1">
                        <ArrowUpCircle className="h-3 w-3 text-green-500" />
                        <span className="text-green-400">{stat.successCount}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <ArrowDownCircle className="h-3 w-3 text-red-500" />
                        <span className="text-red-400">{stat.errorCount}</span>
                      </div>
                      <span className="text-muted-foreground w-14 text-right">
                        {stat.avgLatencyMs.toFixed(0)}ms
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </TabsContent>
          
          <TabsContent value="live">
            <ScrollArea className="h-[300px]">
              <div className="space-y-1 font-mono text-[10px]">
                {streams.slice(0, 50).map((stream) => (
                  <div 
                    key={stream.id}
                    className={cn(
                      "flex items-center gap-2 p-1.5 rounded",
                      stream.status === 'success' && "bg-green-500/10",
                      stream.status === 'error' && "bg-red-500/10",
                      stream.status === 'pending' && "bg-yellow-500/10"
                    )}
                  >
                    <span className="text-muted-foreground w-16">
                      {formatTime(stream.timestamp)}
                    </span>
                    
                    {stream.direction === 'OUT' ? (
                      <ArrowUpCircle className="h-3 w-3 text-blue-400" />
                    ) : (
                      <ArrowDownCircle className={cn(
                        "h-3 w-3",
                        stream.status === 'success' ? "text-green-400" : "text-red-400"
                      )} />
                    )}
                    
                    <span className="truncate flex-1" title={stream.endpoint}>
                      {stream.endpoint}
                    </span>
                    
                    <span className={cn(
                      "w-10 text-right",
                      stream.latencyMs < 100 ? "text-green-400" :
                      stream.latencyMs < 500 ? "text-yellow-400" : "text-red-400"
                    )}>
                      {stream.latencyMs}ms
                    </span>
                    
                    {stream.status === 'success' && (
                      <CheckCircle className="h-3 w-3 text-green-500" />
                    )}
                    {stream.status === 'error' && (
                      <XCircle className="h-3 w-3 text-red-500" />
                    )}
                    {stream.status === 'pending' && (
                      <RefreshCw className="h-3 w-3 text-yellow-500 animate-spin" />
                    )}
                  </div>
                ))}
                
                {streams.length === 0 && (
                  <div className="text-center text-muted-foreground py-8">
                    No streams recorded yet. Data will appear as API calls are made.
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
        
        {/* Selected Endpoint Details */}
        {selectedEndpoint && (
          <div className="mt-3 p-3 bg-muted/30 rounded-md">
            <div className="text-xs font-medium mb-2">{selectedEndpoint}</div>
            {(() => {
              const stat = stats.get(selectedEndpoint);
              if (!stat) return null;
              return (
                <div className="grid grid-cols-2 gap-2 text-[10px]">
                  <div>
                    <span className="text-muted-foreground">Success Rate:</span>
                    <span className="ml-1 font-mono">
                      {stat.successCount + stat.errorCount > 0 
                        ? ((stat.successCount / (stat.successCount + stat.errorCount)) * 100).toFixed(1)
                        : 0}%
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Avg Latency:</span>
                    <span className="ml-1 font-mono">{stat.avgLatencyMs.toFixed(0)}ms</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Success:</span>
                    <span className="ml-1 font-mono">
                      {stat.lastSuccess ? formatTime(stat.lastSuccess) : 'Never'}
                    </span>
                  </div>
                  <div>
                    <span className="text-muted-foreground">Last Error:</span>
                    <span className="ml-1 font-mono">
                      {stat.lastError ? formatTime(stat.lastError) : 'Never'}
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
