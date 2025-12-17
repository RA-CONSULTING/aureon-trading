import { useEffect, useState, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, RefreshCw, TrendingUp, TrendingDown, Clock, DollarSign, Fuel } from "lucide-react";
import { supabase } from "@/lib/supabase";
import { useToast } from "@/hooks/use-toast";

interface PositionWithPnL {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  entryPrice: number;
  quantity: number;
  positionValueUsdt: number;
  currentPrice: number;
  unrealizedPnl: number;
  unrealizedPnlPct: number;
  openedAt: string;
  exchange: string;
  entryFee: number;
  gasCost: number;
  totalCosts: number;
  netPnl: number;
  holdingDurationMs: number;
  holdingDurationFormatted: string;
}

interface Summary {
  totalPnl: number;
  totalCosts: number;
  netPnl: number;
  positionCount: number;
}

export function LivePnLTable() {
  const { toast } = useToast();
  const [positions, setPositions] = useState<PositionWithPnL[]>([]);
  const [summary, setSummary] = useState<Summary>({ totalPnl: 0, totalCosts: 0, netPnl: 0, positionCount: 0 });
  const [loading, setLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchPositions = useCallback(async () => {
    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast({ title: "Not authenticated", variant: "destructive" });
        return;
      }

      const { data, error } = await supabase.functions.invoke("fetch-positions-pnl", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (error) throw error;

      if (data?.success) {
        setPositions(data.positions || []);
        setSummary(data.summary || { totalPnl: 0, totalCosts: 0, netPnl: 0, positionCount: 0 });
        setLastUpdated(new Date());
      } else {
        throw new Error(data?.error || "Failed to fetch positions");
      }
    } catch (err: any) {
      console.error("Fetch positions error:", err);
      toast({
        title: "Failed to fetch positions",
        description: err?.message || String(err),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    fetchPositions();
    // Auto-refresh every 10 seconds for live P&L
    const interval = setInterval(fetchPositions, 10000);
    return () => clearInterval(interval);
  }, [fetchPositions]);

  const formatCurrency = (value: number) => {
    const prefix = value >= 0 ? "+$" : "-$";
    return `${prefix}${Math.abs(value).toFixed(2)}`;
  };

  const formatPercent = (value: number) => {
    const prefix = value >= 0 ? "+" : "";
    return `${prefix}${value.toFixed(2)}%`;
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>Live P&L Tracker</span>
            <Badge variant="outline" className="text-xs">
              {positions.length} open
            </Badge>
          </div>
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            {lastUpdated && (
              <span>Updated {lastUpdated.toLocaleTimeString()}</span>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchPositions}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && positions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : positions.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-8">
            No open positions. Trades will appear here with live P&L tracking.
          </div>
        ) : (
          <>
            <ScrollArea className="h-80">
              <div className="space-y-3">
                {positions.map((pos) => (
                  <div
                    key={pos.id}
                    className="rounded-lg border border-border/50 bg-muted/30 p-4"
                  >
                    {/* Header row */}
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={pos.side === "BUY" ? "default" : "destructive"}
                          className="text-xs"
                        >
                          {pos.side === "BUY" ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                          {pos.side}
                        </Badge>
                        <span className="font-semibold">{pos.symbol}</span>
                        <Badge variant="outline" className="text-xs">
                          {pos.exchange}
                        </Badge>
                      </div>
                      <div className={`text-lg font-mono font-bold ${pos.netPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                        {formatCurrency(pos.netPnl)}
                      </div>
                    </div>

                    {/* Metrics grid */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                      <div>
                        <div className="text-muted-foreground">Entry</div>
                        <div className="font-mono">${pos.entryPrice.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Current</div>
                        <div className="font-mono">${pos.currentPrice.toFixed(4)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Quantity</div>
                        <div className="font-mono">{pos.quantity.toFixed(6)}</div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Value</div>
                        <div className="font-mono">${pos.positionValueUsdt.toFixed(2)}</div>
                      </div>
                    </div>

                    {/* P&L details */}
                    <div className="mt-3 pt-3 border-t border-border/30 grid grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                      <div>
                        <div className="text-muted-foreground flex items-center gap-1">
                          <TrendingUp className="h-3 w-3" /> Gross P&L
                        </div>
                        <div className={`font-mono ${pos.unrealizedPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                          {formatCurrency(pos.unrealizedPnl)} ({formatPercent(pos.unrealizedPnlPct)})
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground flex items-center gap-1">
                          <DollarSign className="h-3 w-3" /> Entry Fee
                        </div>
                        <div className="font-mono text-orange-400">
                          -${pos.entryFee.toFixed(4)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground flex items-center gap-1">
                          <Fuel className="h-3 w-3" /> Gas Cost
                        </div>
                        <div className="font-mono text-orange-400">
                          -${pos.gasCost.toFixed(4)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground">Total Costs</div>
                        <div className="font-mono text-orange-400">
                          -${pos.totalCosts.toFixed(4)}
                        </div>
                      </div>
                      <div>
                        <div className="text-muted-foreground flex items-center gap-1">
                          <Clock className="h-3 w-3" /> Holding
                        </div>
                        <div className="font-mono">
                          {pos.holdingDurationFormatted}
                        </div>
                      </div>
                    </div>

                    {/* Opened timestamp */}
                    <div className="mt-2 text-xs text-muted-foreground">
                      Opened: {new Date(pos.openedAt).toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            {/* Summary footer */}
            <div className="mt-4 pt-4 border-t border-border/50 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Gross P&L</div>
                <div className={`font-mono font-semibold ${summary.totalPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {formatCurrency(summary.totalPnl)}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Total Costs</div>
                <div className="font-mono font-semibold text-orange-400">
                  -${summary.totalCosts.toFixed(2)}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Net P&L</div>
                <div className={`font-mono font-semibold ${summary.netPnl >= 0 ? "text-green-500" : "text-red-500"}`}>
                  {formatCurrency(summary.netPnl)}
                </div>
              </div>
              <div>
                <div className="text-muted-foreground">Open Positions</div>
                <div className="font-mono font-semibold">
                  {summary.positionCount}
                </div>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
