import { useState, useEffect } from "react";
import { supabase } from "@/lib/supabase";
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { AuthForm } from "@/components/AuthForm";
import { SettingsDrawer } from "@/components/SettingsDrawer";
import { LivePriceTicker } from "@/components/LivePriceTicker";
import { MarketMetricsPanel } from "@/components/MarketMetricsPanel";
import { PortfolioSummaryPanel } from "@/components/PortfolioSummaryPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";
import { RefreshCw, Brain, TrendingUp, TrendingDown, Sparkles } from "lucide-react";
import { format } from "date-fns";
import type { User } from "@supabase/supabase-js";

const queryClient = new QueryClient();

interface Trade {
  id: string;
  transaction_id: string;
  exchange: string;
  symbol: string;
  side: string;
  price: number;
  quantity: number;
  quote_qty: number;
  fee: number;
  fee_asset: string;
  timestamp: string;
}

function TradeFeed() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [commentary, setCommentary] = useState<string>("");
  const [syncLoading, setSyncLoading] = useState(false);
  const [commentaryLoading, setCommentaryLoading] = useState(false);
  const [symbolInput, setSymbolInput] = useState<string>(() => {
    try {
      return localStorage.getItem('aureon_sync_symbols') ?? 'BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT';
    } catch {
      return 'BTCUSDT,ETHUSDT,SOLUSDT,XRPUSDT,BNBUSDT';
    }
  });
  const { toast } = useToast();

  useEffect(() => {
    try {
      localStorage.setItem('aureon_sync_symbols', symbolInput);
    } catch {
      // ignore
    }
  }, [symbolInput]);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      setUser(session?.user ?? null);
      setLoading(false);
    });

    return () => subscription.unsubscribe();
  }, []);

  // Subscribe to realtime trade updates
  useEffect(() => {
    if (!user) return;

    const channel = supabase
      .channel("trade-records")
      .on("postgres_changes", {
        event: "INSERT",
        schema: "public",
        table: "trade_records",
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
  }, [user, toast]);

  // Load existing trades
  useEffect(() => {
    if (user) loadTrades();
  }, [user]);

  const loadTrades = async () => {
    const { data, error } = await supabase
      .from("trade_records")
      .select("*")
      .order("timestamp", { ascending: false })
      .limit(100);

    if (!error && data) {
      setTrades(data);
    }
  };

  const fetchNewTrades = async () => {
    setSyncLoading(true);
    try {
      const symbols = symbolInput
        .split(/[,\s]+/)
        .map(s => s.trim().toUpperCase())
        .filter(Boolean);

      const { data, error } = await supabase.functions.invoke("fetch-trades", {
        body: { symbols, limit: 200 },
      });

      if (error) throw error;

      toast({
        title: "Trades Synced",
        description: `Found ${data.count} trades (${symbols.slice(0, 6).join(', ')}${symbols.length > 6 ? ', …' : ''})`,
      });

      await loadTrades();
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to fetch trades",
        variant: "destructive",
      });
    } finally {
      setSyncLoading(false);
    }
  };

  const getAICommentary = async () => {
    if (trades.length === 0) {
      toast({
        title: "No Trades",
        description: "Sync some trades first",
        variant: "destructive",
      });
      return;
    }

    setCommentaryLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke("ai-commentary", {
        body: { trades: trades.slice(0, 20) },
      });

      if (error) throw error;

      setCommentary(data.commentary);
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to get AI commentary",
        variant: "destructive",
      });
    } finally {
      setCommentaryLoading(false);
    }
  };

  const handleLogout = () => {
    setUser(null);
    setTrades([]);
    setCommentary("");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="h-10 w-10 rounded-full border-2 border-primary border-t-transparent animate-spin" />
          <p className="text-sm text-muted-foreground">Loading…</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center p-4">
        <AuthForm onSuccess={() => {}} />
      </div>
    );
  }

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
            <h1 className="text-xl font-bold text-foreground">AUREON Trade Feed</h1>
          </div>
          <div className="flex items-center gap-2">
            <div className="hidden md:block">
              <Input
                value={symbolInput}
                onChange={(e) => setSymbolInput(e.target.value)}
                placeholder="Symbols (e.g. BTCUSDT, ETHUSDT)"
                className="w-72"
              />
            </div>
            <Button onClick={fetchNewTrades} disabled={syncLoading} size="sm">
              <RefreshCw className={`w-4 h-4 mr-2 ${syncLoading ? "animate-spin" : ""}`} />
              Sync
            </Button>
            <Button onClick={getAICommentary} disabled={commentaryLoading} variant="secondary" size="sm">
              <Brain className={`w-4 h-4 mr-2 ${commentaryLoading ? "animate-pulse" : ""}`} />
              Brain
            </Button>
            <SettingsDrawer onLogout={handleLogout} />
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

          {/* Portfolio */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <PortfolioSummaryPanel />

            {/* AI Commentary */}
            {commentary ? (
              <Card className="border-primary/50 bg-primary/5 md:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-primary" />
                    AI Commentary
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-foreground leading-relaxed">{commentary}</p>
                </CardContent>
              </Card>
            ) : (
              <Card className="md:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Brain className="w-5 h-5 text-primary" />
                    AI Brain
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    Click "Brain" to generate commentary on your most recent trades.
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Trade List */}
          <Card>
            <CardHeader>
              <CardTitle>Live Trade Feed</CardTitle>
            </CardHeader>
            <CardContent>
              {trades.length === 0 ? (
                <p className="text-muted-foreground text-center py-8">
                  No trades yet. Click "Sync" to fetch from Binance.
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
