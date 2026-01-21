import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2, RefreshCw, Database } from "lucide-react";
import { supabase } from "@/integrations/supabase/client";
import { useToast } from "@/hooks/use-toast";

type SpotPosition = {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usdValue: number;
  exchange: string;
};

export function ActiveTradePositions() {
  const { toast } = useToast();
  const [positions, setPositions] = useState<SpotPosition[]>([]);
  const [loading, setLoading] = useState(false);
  const [backfilling, setBackfilling] = useState(false);
  const [totalUsd, setTotalUsd] = useState(0);

  const fetchPositions = async () => {
    setLoading(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast({ title: "Not authenticated", variant: "destructive" });
        return;
      }

      const { data, error } = await supabase.functions.invoke("fetch-open-positions", {
        headers: { Authorization: `Bearer ${session.access_token}` },
      });

      if (error) throw error;

      if (data?.success) {
        setPositions(data.positions || []);
        setTotalUsd(data.totalUsdValue || 0);
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
  };

  const handleBackfill = async () => {
    setBackfilling(true);
    try {
      const { data: { session } } = await supabase.auth.getSession();
      if (!session) {
        toast({ title: "Not authenticated", variant: "destructive" });
        return;
      }

      const { data, error } = await supabase.functions.invoke("backfill-trades", {
        headers: { Authorization: `Bearer ${session.access_token}` },
        body: {},
      });

      if (error) throw error;

      if (data?.success) {
        toast({
          title: "Backfill Complete",
          description: `${data.executionsBackfilled} executions, ${data.positionsCreated} positions synced`,
        });
        // Refresh positions after backfill
        await fetchPositions();
      } else {
        throw new Error(data?.error || "Backfill failed");
      }
    } catch (err: any) {
      console.error("Backfill error:", err);
      toast({
        title: "Backfill Failed",
        description: err?.message || String(err),
        variant: "destructive",
      });
    } finally {
      setBackfilling(false);
    }
  };

  useEffect(() => {
    fetchPositions();
  }, []);

  const binancePositions = positions.filter(p => p.exchange === "binance");
  const krakenPositions = positions.filter(p => p.exchange === "kraken");
  const binanceTotal = binancePositions.reduce((sum, p) => sum + p.usdValue, 0);
  const krakenTotal = krakenPositions.reduce((sum, p) => sum + p.usdValue, 0);

  const renderPositionList = (items: SpotPosition[], exchange: string, emoji: string, total: number) => (
    <div className="flex-1 min-w-0">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-lg">{emoji}</span>
          <span className="font-semibold capitalize">{exchange}</span>
          <Badge variant="outline" className="text-xs">{items.length}</Badge>
        </div>
        <span className="text-sm font-mono text-muted-foreground">${total.toFixed(2)}</span>
      </div>
      <ScrollArea className="h-64 rounded-lg border border-border/50 bg-muted/20 p-2">
        {items.length === 0 ? (
          <div className="text-xs text-muted-foreground text-center py-8">
            No {exchange} positions
          </div>
        ) : (
          <div className="space-y-2">
            {items.map((p, i) => (
              <div
                key={`${p.asset}-${i}`}
                className="flex items-center justify-between rounded-md border border-border/30 bg-background/50 p-2"
              >
                <div>
                  <span className="font-semibold text-sm">{p.asset}</span>
                  <div className="text-xs text-muted-foreground">
                    {p.total.toFixed(6)}
                  </div>
                </div>
                <div className="text-right">
                  <div className="font-mono text-sm">${p.usdValue.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </ScrollArea>
    </div>
  );

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span>Real Spot Positions</span>
          <div className="flex items-center gap-2">
            <Badge variant="outline">${totalUsd.toFixed(2)} total</Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={fetchPositions}
              disabled={loading}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleBackfill}
              disabled={backfilling}
            >
              {backfilling ? (
                <Loader2 className="h-4 w-4 animate-spin mr-1" />
              ) : (
                <Database className="h-4 w-4 mr-1" />
              )}
              Backfill DB
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading && positions.length === 0 ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="flex gap-4">
            {renderPositionList(binancePositions, "binance", "🟡", binanceTotal)}
            {renderPositionList(krakenPositions, "kraken", "🐙", krakenTotal)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
