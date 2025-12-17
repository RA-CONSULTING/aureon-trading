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

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span>Real Spot Positions</span>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{positions.length} assets</Badge>
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
        ) : positions.length === 0 ? (
          <div className="text-sm text-muted-foreground text-center py-4">
            No spot positions found. Make sure you have Binance credentials configured.
          </div>
        ) : (
          <>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {positions.map((p) => (
                  <div
                    key={p.asset}
                    className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/30 p-3"
                  >
                    <div>
                      <span className="font-semibold">{p.asset}</span>
                      <div className="mt-1 text-xs text-muted-foreground">
                        Free: {p.free.toFixed(6)} · Locked: {p.locked.toFixed(6)}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="font-mono text-sm">
                        {p.total.toFixed(6)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        ≈ ${p.usdValue.toFixed(2)}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </ScrollArea>

            <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-3 text-sm">
              <span className="text-muted-foreground">Total Portfolio Value</span>
              <span className="font-mono font-semibold">${totalUsd.toFixed(2)}</span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
