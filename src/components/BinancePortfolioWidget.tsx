import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Wallet, RefreshCw, AlertCircle, TrendingUp, CheckCircle, XCircle } from "lucide-react";
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

interface Balance {
  asset: string;
  total: number;
  usdtValue: number;
}

interface PortfolioData {
  balances: Balance[];
  totalUSDT: number;
  totalBTC: number;
  canTrade: boolean;
  fetchedAt: string;
}

export const BinancePortfolioWidget = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchPortfolio = async () => {
    setIsLoading(true);
    setError(null);

    try {
      // Get the current session to pass auth token
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!session) {
        throw new Error('Please sign in to view your portfolio');
      }

      const { data, error: functionError } = await supabase.functions.invoke('fetch-binance-portfolio', {
        headers: {
          Authorization: `Bearer ${session.access_token}`
        }
      });

      if (functionError) throw functionError;
      if (data.error) throw new Error(data.error);

      setPortfolio(data);
      toast({
        title: "Portfolio Synced",
        description: `Live data from your Binance account`,
        duration: 2000,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch portfolio';
      setError(errorMessage);
      
      // Show helpful error messages
      let errorDescription = errorMessage;
      if (errorMessage.includes('credentials not configured') || errorMessage.includes('add your API credentials')) {
        errorDescription = 'Please add your Binance API credentials in account settings to view your portfolio.';
      }
      
      toast({
        title: "Portfolio Sync Failed",
        description: errorDescription,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
    const interval = setInterval(fetchPortfolio, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const topHoldings = portfolio?.balances
    .filter(b => b.usdtValue > 1)
    .sort((a, b) => b.usdtValue - a.usdtValue)
    .slice(0, 5) || [];

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wallet className="h-5 w-5 text-primary" />
            <CardTitle className="text-lg">Binance Portfolio</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={fetchPortfolio}
            disabled={isLoading}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && !portfolio && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-destructive/10 border border-destructive/20">
            <AlertCircle className="h-4 w-4 text-destructive mt-0.5 flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-destructive">Portfolio Unavailable</p>
              <p className="text-xs text-muted-foreground">{error}</p>
              {error.includes('credentials') && (
                <Button 
                  variant="link" 
                  size="sm" 
                  className="h-auto p-0 mt-1 text-xs"
                  onClick={() => window.location.href = '/settings'}
                >
                  Add Binance API Credentials →
                </Button>
              )}
            </div>
          </div>
        )}

        {isLoading && !portfolio && (
          <div className="text-center py-8">
            <RefreshCw className="h-8 w-8 mx-auto mb-2 text-primary animate-spin" />
            <p className="text-sm text-muted-foreground">Connecting to your Binance account...</p>
          </div>
        )}

        {portfolio && (
          <>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">Total Value</p>
                <p className="text-2xl font-bold text-foreground">
                  {formatCurrency(portfolio.totalUSDT)}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground">BTC Value</p>
                <p className="text-lg font-semibold text-foreground">
                  {portfolio.totalBTC.toFixed(6)} BTC
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
              {portfolio.canTrade ? (
                <>
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium">API Connected & Trading Enabled</span>
                </>
              ) : (
                <>
                  <XCircle className="h-4 w-4 text-destructive" />
                  <span className="text-sm font-medium">Trading Disabled</span>
                </>
              )}
            </div>

            {topHoldings.length > 0 && (
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Top Holdings</p>
                <div className="space-y-2">
                  {topHoldings.map((balance) => (
                    <div key={balance.asset} className="flex items-center justify-between p-2 rounded bg-muted/30">
                      <div className="flex items-center gap-2">
                        <Badge variant="outline" className="font-mono text-xs">
                          {balance.asset}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {balance.total < 1 ? balance.total.toFixed(6) : balance.total.toFixed(4)}
                        </span>
                      </div>
                      <span className="text-sm font-semibold">
                        {formatCurrency(balance.usdtValue)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="pt-2 border-t border-border/50">
              <div className="flex items-center justify-between text-xs text-muted-foreground">
                <span>Assets: {portfolio.balances.length}</span>
                <span>Updated: {new Date(portfolio.fetchedAt).toLocaleTimeString()}</span>
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
};
