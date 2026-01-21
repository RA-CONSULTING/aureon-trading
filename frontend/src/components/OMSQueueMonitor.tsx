import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Button } from '@/components/ui/button';
import { useOMSQueue } from '@/hooks/useOMSQueue';
import { Activity, TrendingUp, Clock, X } from 'lucide-react';

interface OMSQueueMonitorProps {
  sessionId: string | null;
}

export function OMSQueueMonitor({ sessionId }: OMSQueueMonitorProps) {
  const { status, orders, cancelOrder, isProcessing } = useOMSQueue(sessionId);

  if (!sessionId) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary" />
            OMS Queue
          </CardTitle>
          <CardDescription>No active session</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  if (!status) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-primary animate-pulse" />
            OMS Queue
          </CardTitle>
          <CardDescription>Loading queue status...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const utilizationColor = 
    status.rateLimit.utilization > 90 ? 'text-destructive' :
    status.rateLimit.utilization > 70 ? 'text-warning' :
    'text-success';

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className={`h-5 w-5 ${isProcessing ? 'animate-pulse text-primary' : 'text-primary'}`} />
          OMS Leaky Bucket Queue
        </CardTitle>
        <CardDescription>
          Priority queue with rate limit protection (100 orders/10s)
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Rate Limit Status */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Rate Limit Utilization</span>
            <span className={`text-sm font-mono font-semibold ${utilizationColor}`}>
              {status.rateLimit.utilization.toFixed(1)}%
            </span>
          </div>
          <Progress 
            value={status.rateLimit.utilization} 
            className="h-2"
          />
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>{status.rateLimit.used}/{status.rateLimit.limit} used</span>
            <span>{status.rateLimit.available} slots available</span>
          </div>
        </div>

        {/* Queue Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              Queued
            </div>
            <div className="text-2xl font-bold text-foreground">
              {status.queueDepth}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Activity className="h-3 w-3" />
              Processing
            </div>
            <div className="text-2xl font-bold text-warning">
              {status.processing}
            </div>
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <TrendingUp className="h-3 w-3" />
              Exec/min
            </div>
            <div className="text-2xl font-bold text-success">
              {status.metrics?.orders_executed_last_minute || 0}
            </div>
          </div>
        </div>

        {/* Queue Orders */}
        {orders.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-foreground">Pending Orders</h4>
            <div className="space-y-2 max-h-[300px] overflow-y-auto">
              {orders.map((order, idx) => (
                <div 
                  key={order.id}
                  className="flex items-center justify-between p-3 rounded-lg border border-border/50 bg-background/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="text-xs text-muted-foreground font-mono">
                      #{idx + 1}
                    </div>
                    <Badge variant={order.status === 'processing' ? 'default' : 'outline'}>
                      {order.status}
                    </Badge>
                    <div className="text-sm">
                      <span className="font-semibold text-foreground">{order.symbol}</span>
                      <span className={`ml-2 ${order.side === 'BUY' ? 'text-success' : 'text-destructive'}`}>
                        {order.side}
                      </span>
                    </div>
                    <div className="text-xs text-muted-foreground font-mono">
                      {order.quantity} @ ${order.price.toFixed(2)}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant="secondary" className="font-mono">
                      P{order.priority}
                    </Badge>
                    {order.status === 'queued' && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => cancelOrder(order.id)}
                        className="h-8 w-8 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Empty State */}
        {orders.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="h-12 w-12 mx-auto mb-2 opacity-20" />
            <p className="text-sm">No orders in queue</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
