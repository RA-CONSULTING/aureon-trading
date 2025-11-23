import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useQuery } from '@tanstack/react-query';
import { supabase } from '@/integrations/supabase/client';
import { TrendingUp, Clock, DollarSign, Activity } from 'lucide-react';

interface TWAPOrder {
  id: string;
  symbol: string;
  side: string;
  total_quantity: number;
  executed_quantity: number;
  executed_amount: number;
  avg_price: number;
  algo_status: string;
  duration_seconds: number;
  book_time: string;
  urgency: string;
}

export function TWAPMonitor() {
  const { data: twapOrders } = useQuery({
    queryKey: ['twap-orders'],
    queryFn: async () => {
      const { data, error } = await supabase
        .from('twap_orders')
        .select('*')
        .order('created_at', { ascending: false })
        .limit(10);

      if (error) throw error;
      return data as TWAPOrder[];
    },
    refetchInterval: 5000,
  });

  const activeTWAP = twapOrders?.filter(o => o.algo_status === 'WORKING') || [];
  const totalVolume = twapOrders?.reduce((sum, o) => sum + (o.executed_amount || 0), 0) || 0;

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          TWAP Orders Monitor
        </CardTitle>
        <CardDescription>
          Intelligent order execution via Binance Algo Trading
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Summary Stats */}
        <div className="grid grid-cols-3 gap-3">
          <div className="p-3 rounded-lg border border-border/50 bg-background/30">
            <div className="text-xs text-muted-foreground mb-1">Active TWAP</div>
            <div className="text-2xl font-bold text-primary">{activeTWAP.length}</div>
          </div>
          <div className="p-3 rounded-lg border border-border/50 bg-background/30">
            <div className="text-xs text-muted-foreground mb-1">Total Orders</div>
            <div className="text-2xl font-bold text-foreground">{twapOrders?.length || 0}</div>
          </div>
          <div className="p-3 rounded-lg border border-border/50 bg-background/30">
            <div className="text-xs text-muted-foreground mb-1">Volume</div>
            <div className="text-2xl font-bold text-success">${(totalVolume / 1000).toFixed(1)}K</div>
          </div>
        </div>

        {/* Active TWAP Orders */}
        {activeTWAP.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              Active Executions
            </h4>
            {activeTWAP.map((order) => {
              const fillPercent = (order.executed_quantity / order.total_quantity) * 100;
              const elapsedTime = Math.floor((Date.now() - new Date(order.book_time).getTime()) / 1000);
              const remainingTime = Math.max(0, order.duration_seconds - elapsedTime);
              const timeProgress = (elapsedTime / order.duration_seconds) * 100;

              return (
                <div 
                  key={order.id}
                  className="p-3 rounded-lg border border-border/50 bg-background/20 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-semibold text-foreground">{order.symbol}</span>
                      <Badge variant={order.side === 'BUY' ? 'default' : 'destructive'} className="text-xs">
                        {order.side}
                      </Badge>
                      <Badge variant="outline" className="text-xs">
                        {order.urgency}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {Math.floor(remainingTime / 60)}m {remainingTime % 60}s left
                    </div>
                  </div>

                  {/* Quantity Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Fill Progress</span>
                      <span className="text-foreground font-medium">{fillPercent.toFixed(1)}%</span>
                    </div>
                    <Progress value={fillPercent} className="h-2" />
                    <div className="flex justify-between text-xs text-muted-foreground">
                      <span>{order.executed_quantity.toFixed(4)} / {order.total_quantity.toFixed(4)}</span>
                      <span className="flex items-center gap-1">
                        <DollarSign className="h-3 w-3" />
                        Avg: ${order.avg_price?.toFixed(2) || '0.00'}
                      </span>
                    </div>
                  </div>

                  {/* Time Progress */}
                  <div className="space-y-1">
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Time Progress</span>
                      <span className="text-foreground font-medium">{timeProgress.toFixed(1)}%</span>
                    </div>
                    <Progress value={timeProgress} className="h-1" />
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Recent Completed */}
        {twapOrders && twapOrders.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-foreground">Recent Orders</h4>
            <div className="space-y-1 max-h-[200px] overflow-y-auto">
              {twapOrders.slice(0, 5).map((order) => (
                <div 
                  key={order.id}
                  className="flex items-center justify-between p-2 rounded border border-border/30 bg-background/10 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-foreground">{order.symbol}</span>
                    <Badge 
                      variant={
                        order.algo_status === 'WORKING' ? 'default' :
                        order.algo_status === 'FINISHED' ? 'secondary' :
                        'outline'
                      }
                      className="text-xs"
                    >
                      {order.algo_status}
                    </Badge>
                  </div>
                  <div className="text-muted-foreground">
                    {order.executed_quantity.toFixed(4)} @ ${order.avg_price?.toFixed(2) || '0.00'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {!twapOrders || twapOrders.length === 0 && (
          <div className="text-center py-8 text-muted-foreground text-sm">
            No TWAP orders yet. Orders above ${' '}
            <span className="text-foreground font-semibold">500</span> will use TWAP.
          </div>
        )}
      </CardContent>
    </Card>
  );
}