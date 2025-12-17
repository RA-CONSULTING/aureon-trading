import { useEffect, useMemo, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Loader2 } from "lucide-react";

export type TradeRecord = {
  id: string;
  exchange: string;
  symbol: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  timestamp: string;
};

type PositionRow = {
  symbol: string;
  quantity: number;
  entryPrice: number;
  currentPrice?: number;
  pnlUsd?: number;
  pnlPct?: number;
};

const priceUrl = (symbol: string) => `https://api.binance.com/api/v3/ticker/price?symbol=${encodeURIComponent(symbol)}`;

export function ActiveTradePositions({ trades }: { trades: TradeRecord[] }) {
  const positions = useMemo<PositionRow[]>(() => {
    const bySymbol = new Map<
      string,
      { buyQty: number; buyCost: number; sellQty: number }
    >();

    for (const t of trades) {
      const symbol = String(t.symbol || "").toUpperCase();
      if (!symbol) continue;
      const price = Number(t.price || 0);
      const qty = Number(t.quantity || 0);
      if (!Number.isFinite(price) || !Number.isFinite(qty) || qty <= 0) continue;

      const rec = bySymbol.get(symbol) ?? { buyQty: 0, buyCost: 0, sellQty: 0 };
      if (t.side === "BUY") {
        rec.buyQty += qty;
        rec.buyCost += qty * price;
      } else {
        rec.sellQty += qty;
      }
      bySymbol.set(symbol, rec);
    }

    const rows: PositionRow[] = [];
    for (const [symbol, s] of bySymbol.entries()) {
      const netQty = s.buyQty - s.sellQty;
      if (netQty <= 0 || s.buyQty <= 0) continue;

      const entryPrice = s.buyCost / s.buyQty;
      rows.push({ symbol, quantity: netQty, entryPrice });
    }

    return rows
      .sort((a, b) => b.quantity * b.entryPrice - a.quantity * a.entryPrice)
      .slice(0, 50);
  }, [trades]);

  const [prices, setPrices] = useState<Record<string, number>>({});
  const [loadingPrices, setLoadingPrices] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function loadPrices() {
      if (positions.length === 0) return;
      setLoadingPrices(true);
      try {
        const results = await Promise.all(
          positions.map(async (p) => {
            try {
              const res = await fetch(priceUrl(p.symbol));
              if (!res.ok) return [p.symbol, undefined] as const;
              const json = await res.json();
              const price = Number(json?.price);
              return [p.symbol, Number.isFinite(price) ? price : undefined] as const;
            } catch {
              return [p.symbol, undefined] as const;
            }
          })
        );

        if (cancelled) return;
        const next: Record<string, number> = {};
        for (const [symbol, price] of results) {
          if (typeof price === "number") next[symbol] = price;
        }
        setPrices(next);
      } finally {
        if (!cancelled) setLoadingPrices(false);
      }
    }

    loadPrices();
    return () => {
      cancelled = true;
    };
  }, [positions]);

  const enriched = useMemo(() => {
    return positions.map((p) => {
      const current = prices[p.symbol];
      if (!current) return p;
      const pnlUsd = (current - p.entryPrice) * p.quantity;
      const pnlPct = ((current - p.entryPrice) / p.entryPrice) * 100;
      return { ...p, currentPrice: current, pnlUsd, pnlPct };
    });
  }, [positions, prices]);

  const totals = useMemo(() => {
    const totalExposure = enriched.reduce(
      (sum, p) => sum + p.quantity * (p.currentPrice ?? p.entryPrice),
      0
    );
    const totalPnl = enriched.reduce((sum, p) => sum + (p.pnlUsd ?? 0), 0);
    return { totalExposure, totalPnl };
  }, [enriched]);

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between">
          <span>Active Positions</span>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{enriched.length} open</Badge>
            {loadingPrices && (
              <span className="inline-flex items-center gap-1 text-xs text-muted-foreground">
                <Loader2 className="h-3 w-3 animate-spin" /> prices
              </span>
            )}
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {enriched.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No open positions inferred from your trade history yet.
          </div>
        ) : (
          <>
            <ScrollArea className="h-64">
              <div className="space-y-2">
                {enriched.map((p) => {
                  const pnl = p.pnlUsd;
                  const isProfit = typeof pnl === "number" ? pnl >= 0 : undefined;
                  return (
                    <div
                      key={p.symbol}
                      className="flex items-center justify-between rounded-lg border border-border/50 bg-muted/30 p-3"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-semibold">{p.symbol}</span>
                          {typeof isProfit === "boolean" && (
                            <Badge variant={isProfit ? "default" : "destructive"}>
                              {isProfit ? "PROFIT" : "LOSS"}
                            </Badge>
                          )}
                        </div>
                        <div className="mt-1 text-xs text-muted-foreground">
                          Qty: {p.quantity.toFixed(6)} · Entry: ${p.entryPrice.toFixed(4)}
                          {p.currentPrice
                            ? ` · Now: $${p.currentPrice.toFixed(4)}`
                            : ""}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-mono text-sm">
                          {typeof p.pnlUsd === "number" ? (
                            <>
                              {p.pnlUsd >= 0 ? "+" : ""}${p.pnlUsd.toFixed(2)}
                              {typeof p.pnlPct === "number" ? (
                                <span className="text-xs text-muted-foreground">
                                  {" "}({p.pnlPct >= 0 ? "+" : ""}{p.pnlPct.toFixed(2)}%)
                                </span>
                              ) : null}
                            </>
                          ) : (
                            <span className="text-xs text-muted-foreground">PnL pending price</span>
                          )}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          Exposure: ${(p.quantity * (p.currentPrice ?? p.entryPrice)).toFixed(2)}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </ScrollArea>

            <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-3 text-sm">
              <span className="text-muted-foreground">Totals</span>
              <span className="font-mono">
                Exposure ${totals.totalExposure.toFixed(2)} · PnL {totals.totalPnl >= 0 ? "+" : ""}${totals.totalPnl.toFixed(2)}
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}
