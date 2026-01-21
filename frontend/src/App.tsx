import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { LivePriceTicker } from "@/components/LivePriceTicker";
import { MarketMetricsPanel } from "@/components/MarketMetricsPanel";
import { PortfolioSummaryPanel } from "@/components/PortfolioSummaryPanel";
import { ActiveTradePositions } from "@/components/ActiveTradePositions";
import { LivePnLTable } from "@/components/LivePnLTable";
import { LiveTerminalStats } from "@/components/LiveTerminalStats";
import { BrainStatePanel } from "@/components/BrainStatePanel";
import { HiveStatePanel } from "@/components/HiveStatePanel";
import { HiveStatePanel } from "@/components/HiveStatePanel";
import { useTerminalSync } from "@/hooks/useTerminalSync";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useToast } from "@/hooks/use-toast";
import { TrendingUp, TrendingDown, Sparkles } from "lucide-react";
import { format } from "date-fns";

const queryClient = new QueryClient();

// Public live feed user ID - data pushed from Python terminal
const LIVE_FEED_USER_ID = "69e5567f-7ad1-42af-860f-3709ef1f5935";

interface Trade {
  id: string;
  transaction_id: string;
  exchange: string;
  symbol: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  quote_qty: number;
  fee: number;
  fee_asset: string;
  timestamp: string;
}

function TradeFeed() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const { toast } = useToast();
  
  // Always sync terminal data (public feed)
  useTerminalSync(true, 10000);

  // Subscribe to realtime trade updates for the live feed user
  useEffect(() => {
    const channel = supabase
      .channel("trade-records")
      .on("postgres_changes", {
        event: "INSERT",
        schema: "public",
        table: "trade_records",
        filter: `user_id=eq.${LIVE_FEED_USER_ID}`,
      }, (payload) => {
        setTrades(prev => [payload.new as Trade, ...prev]);
        toast({
          title: "New Trade",
          description: `${(payload.new as Trade).side} ${(payload.new as Trade).symbol}`,
        });
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [toast]);

  // Load existing trades on mount
  useEffect(() => {
    loadTrades();
  }, []);

  const loadTrades = async () => {
    const { data, error } = await supabase
      .from("trade_records")
      .select("*")
      .eq("user_id", LIVE_FEED_USER_ID)
      .order("timestamp", { ascending: false })
      .limit(100);

    if (!error && data) {
      setTrades(data.map(t => ({ ...t, side: t.side as "BUY" | "SELL" })));
    }
  };

  const totalBuys = trades.filter(t => t.side === "BUY").length;
  const totalSells = trades.filter(t => t.side === "SELL").length;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-primary-foreground" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">AUREON Live Feed</h1>
              <p className="text-xs text-muted-foreground">Public Trading Dashboard</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="px-3 py-1 rounded-full bg-green-500/20 text-green-500 text-xs font-medium flex items-center gap-1">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              LIVE
            </div>
            <SettingsDrawer />
          </div>
        </div>
      </header>

      {/* Live Price Ticker Bar */}
      <LivePriceTicker />

      <main className="p-6">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Top Row: Stats + Market Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{trades.length}</div>
                <p className="text-muted-foreground text-sm">Total Trades</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-green-500" />
                <div>
                  <div className="text-2xl font-bold text-green-500">{totalBuys}</div>
                  <p className="text-muted-foreground text-sm">Buys</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6 flex items-center gap-2">
                <TrendingDown className="w-5 h-5 text-red-500" />
                <div>
                  <div className="text-2xl font-bold text-red-500">{totalSells}</div>
                  <p className="text-muted-foreground text-sm">Sells</p>
                </div>
              </CardContent>
            </Card>
            <MarketMetricsPanel />
          </div>

          {/* Portfolio Summary */}
          <PortfolioSummaryPanel />

          {/* Cognitive State: Brain + Hive */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <BrainStatePanel />
            <HiveStatePanel />
          </div>

          {/* Terminal Stats Mirror - Live system metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            <LiveTerminalStats />

            {/* Hive State Panel (Queen's mood, coherence, veto log) */}
            <HiveStatePanel />

            {/* Active Positions (real Binance/Kraken spot balances) */}
            <ActiveTradePositions />
          </div>

          {/* Live P&L Tracker - shows open positions with live profit/loss */}
          <LivePnLTable />

          {/* Trade List */}
          <Card>
            <CardHeader>
              <CardTitle>Live Trade Feed</CardTitle>
            </CardHeader>
            <CardContent>
              {trades.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  Waiting for trades from the Python terminal...
                </p>
              ) : (
                <div className="space-y-2 max-h-[500px] overflow-y-auto">
                  {trades.map((trade) => (
                    <div
                      key={trade.id}
                      className="flex items-center justify-between p-3 rounded-lg bg-muted/50 hover:bg-muted transition-colors"
                    >
                      <div className="flex items-center gap-4">
                        <span
                          className={`px-2 py-1 rounded text-xs font-bold ${
                            trade.side === "BUY"
                              ? "bg-green-500/20 text-green-500"
                              : "bg-red-500/20 text-red-500"
                          }`}
                        >
                          {trade.side}
                        </span>
                        <div>
                          <div className="font-medium">{trade.symbol}</div>
                          <div className="text-xs text-muted-foreground">
                            ID: {trade.transaction_id}
                          </div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono">
                          {trade.quantity} @ ${Number(trade.price).toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {format(new Date(trade.timestamp), "MMM d, HH:mm:ss")}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}

const App = () => {
  return (
    <ThemeProvider defaultTheme="dark">
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <Toaster />
          <Sonner />
          <TradeFeed />
        </TooltipProvider>
      </QueryClientProvider>
    </ThemeProvider>
  );
};

export default App;
