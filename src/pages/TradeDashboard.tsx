import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { RefreshCw, Brain, TrendingUp, TrendingDown } from 'lucide-react';
import { format } from 'date-fns';

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

export default function TradeDashboard() {
  const [trades, setTrades] = useState<Trade[]>([]);
  const [commentary, setCommentary] = useState<string>('');
  const [loading, setLoading] = useState(false);
  const [commentaryLoading, setCommentaryLoading] = useState(false);
  const { toast } = useToast();

  // Subscribe to realtime trade updates
  useEffect(() => {
    const channel = supabase
      .channel('trade-records')
      .on('postgres_changes', {
        event: 'INSERT',
        schema: 'public',
        table: 'trade_records',
      }, (payload) => {
        setTrades(prev => [payload.new as Trade, ...prev]);
        toast({
          title: 'New Trade',
          description: `${(payload.new as Trade).side} ${(payload.new as Trade).symbol}`,
        });
      })
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [toast]);

  // Load existing trades
  useEffect(() => {
    loadTrades();
  }, []);

  const loadTrades = async () => {
    const { data, error } = await supabase
      .from('trade_records')
      .select('*')
      .order('timestamp', { ascending: false })
      .limit(100);

    if (error) {
      console.error('Error loading trades:', error);
      return;
    }

    setTrades(data || []);
  };

  const fetchNewTrades = async () => {
    setLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('fetch-trades', {
        body: { symbol: 'BTCUSDT', limit: 50 },
      });

      if (error) throw error;

      toast({
        title: 'Trades Synced',
        description: `Found ${data.count} trades from Binance`,
      });

      await loadTrades();
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to fetch trades',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const getAICommentary = async () => {
    if (trades.length === 0) {
      toast({
        title: 'No Trades',
        description: 'Sync some trades first',
        variant: 'destructive',
      });
      return;
    }

    setCommentaryLoading(true);
    try {
      const { data, error } = await supabase.functions.invoke('ai-commentary', {
        body: { trades: trades.slice(0, 20) },
      });

      if (error) throw error;

      setCommentary(data.commentary);
    } catch (error: any) {
      toast({
        title: 'Error',
        description: error.message || 'Failed to get AI commentary',
        variant: 'destructive',
      });
    } finally {
      setCommentaryLoading(false);
    }
  };

  const totalBuys = trades.filter(t => t.side === 'BUY').length;
  const totalSells = trades.filter(t => t.side === 'SELL').length;

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-3xl font-bold text-foreground">Trade Dashboard</h1>
          <div className="flex gap-3">
            <Button onClick={fetchNewTrades} disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Sync Trades
            </Button>
            <Button onClick={getAICommentary} disabled={commentaryLoading} variant="secondary">
              <Brain className={`w-4 h-4 mr-2 ${commentaryLoading ? 'animate-pulse' : ''}`} />
              Ask Brain
            </Button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4">
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
        </div>

        {/* AI Commentary */}
        {commentary && (
          <Card className="border-primary/50 bg-primary/5">
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
        )}

        {/* Trade List */}
        <Card>
          <CardHeader>
            <CardTitle>Trade History</CardTitle>
          </CardHeader>
          <CardContent>
            {trades.length === 0 ? (
              <p className="text-muted-foreground text-center py-8">
                No trades yet. Click "Sync Trades" to fetch from Binance.
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
                          trade.side === 'BUY'
                            ? 'bg-green-500/20 text-green-500'
                            : 'bg-red-500/20 text-red-500'
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
                        {format(new Date(trade.timestamp), 'MMM d, HH:mm:ss')}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
