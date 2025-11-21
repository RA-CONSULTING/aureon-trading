import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { PieChart, Wallet, RefreshCw, AlertCircle } from "lucide-react";
import Navbar from "@/components/Navbar";
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';
import { QuickTrade } from '@/components/QuickTrade';

interface Balance {
  asset: string;
  free: number;
  locked: number;
  total: number;
  usdtValue: number;
  price: number;
}

interface PortfolioData {
  balances: Balance[];
  totalUSDT: number;
  totalBTC: number;
  accountType: string;
  canTrade: boolean;
  canWithdraw: boolean;
  canDeposit: boolean;
  fetchedAt: string;
}

const Portfolio = () => {
  const [portfolio, setPortfolio] = useState<PortfolioData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const fetchPortfolio = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const { data, error: functionError } = await supabase.functions.invoke('fetch-binance-portfolio', {
        body: {},
      });

      if (functionError) throw functionError;
      if (data.error) throw new Error(data.error);

      setPortfolio(data);
      toast({
        title: "Portfolio Updated",
        description: `Fetched ${data.balances.length} assets from Binance`,
        duration: 3000,
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to fetch portfolio';
      setError(errorMessage);
      toast({
        title: "Error Loading Portfolio",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatAmount = (amount: number) => {
    const decimals = amount < 1 ? 6 : amount < 10 ? 4 : 2;
    return amount.toFixed(decimals);
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8 flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-2">Live Binance Portfolio</h1>
            <p className="text-muted-foreground">Real-time wallet balances and asset status</p>
          </div>
          <Button onClick={fetchPortfolio} disabled={isLoading} className="gap-2">
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
            {isLoading ? 'Refreshing...' : 'Refresh'}
          </Button>
        </div>

        {error && !portfolio && (
          <Card className="bg-destructive/10 border-destructive/20 mb-8">
            <CardContent className="p-6">
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <h4 className="font-semibold mb-1">Error Loading Portfolio</h4>
                  <p className="text-sm text-muted-foreground">{error}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {isLoading && !portfolio && (
          <div className="text-center py-12">
            <RefreshCw className="h-16 w-16 mx-auto mb-4 text-primary animate-spin" />
            <p className="text-muted-foreground">Loading your Binance portfolio...</p>
          </div>
        )}

        {portfolio && (
          <>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
              <div className="lg:col-span-2 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <Card className="bg-card shadow-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Value</CardTitle>
                      <Wallet className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{formatCurrency(portfolio.totalUSDT)}</div>
                      <p className="text-xs text-muted-foreground mt-1">≈ {portfolio.totalBTC.toFixed(4)} BTC</p>
                    </CardContent>
                  </Card>

                  <Card className="bg-card shadow-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Total Assets</CardTitle>
                      <PieChart className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-3xl font-bold">{portfolio.balances.length}</div>
                      <p className="text-xs text-muted-foreground mt-1">Non-zero balances</p>
                    </CardContent>
                  </Card>

                  <Card className="bg-card shadow-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Account Type</CardTitle>
                      <Wallet className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-2xl font-bold capitalize">{portfolio.accountType}</div>
                      <Badge variant={portfolio.canTrade ? "default" : "secondary"} className="text-xs mt-2">
                        {portfolio.canTrade ? '✓ Trading' : '✗ Trading'}
                      </Badge>
                    </CardContent>
                  </Card>

                  <Card className="bg-card shadow-card">
                    <CardHeader className="flex flex-row items-center justify-between pb-2">
                      <CardTitle className="text-sm font-medium text-muted-foreground">Last Updated</CardTitle>
                      <RefreshCw className="h-4 w-4 text-primary" />
                    </CardHeader>
                    <CardContent>
                      <div className="text-sm font-mono">{new Date(portfolio.fetchedAt).toLocaleTimeString()}</div>
                      <p className="text-xs text-muted-foreground mt-1">{new Date(portfolio.fetchedAt).toLocaleDateString()}</p>
                    </CardContent>
                  </Card>
                </div>
              </div>

              <QuickTrade 
                balances={portfolio.balances} 
                canTrade={portfolio.canTrade}
              />
            </div>

            <Card className="bg-card shadow-card mb-8">
              <CardHeader>
                <CardTitle>Holdings</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {portfolio.balances.map((balance, index) => {
                    const allocation = (balance.usdtValue / portfolio.totalUSDT) * 100;
                    return (
                      <div key={balance.asset} className="flex items-center justify-between p-4 rounded-lg bg-muted/20 hover:bg-muted/40 transition-colors border border-border/50">
                        <div className="flex items-center gap-4 flex-1">
                          <Badge variant={index === 0 ? "default" : "secondary"}>{index + 1}</Badge>
                          <div>
                            <p className="font-bold text-lg">{balance.asset}</p>
                            <p className="text-sm text-muted-foreground font-mono">{formatAmount(balance.total)} {balance.asset}</p>
                            {balance.locked > 0 && <p className="text-xs text-yellow-500 mt-1">Locked: {balance.locked.toFixed(6)}</p>}
                          </div>
                        </div>
                        <div className="flex items-center gap-8">
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">Allocation</p>
                            <p className="font-bold">{allocation.toFixed(1)}%</p>
                          </div>
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">Price</p>
                            <p className="font-bold font-mono">{balance.price > 0 ? formatCurrency(balance.price) : 'N/A'}</p>
                          </div>
                          <div className="text-right min-w-[120px]">
                            <p className="text-sm text-muted-foreground">Value</p>
                            <p className="font-bold text-lg">{formatCurrency(balance.usdtValue)}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                  {portfolio.balances.length === 0 && (
                    <div className="text-center py-12 text-muted-foreground">
                      <Wallet className="h-16 w-16 mx-auto mb-4 opacity-50" />
                      <p>No assets found</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            <Card className="bg-card shadow-card">
              <CardHeader>
                <CardTitle className="text-sm font-semibold">Account Permissions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-3 gap-4">
                  <div className={`p-3 rounded-lg border ${portfolio.canTrade ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <p className="text-sm font-semibold mb-1">Trading</p>
                    <Badge variant={portfolio.canTrade ? "default" : "secondary"}>{portfolio.canTrade ? '✓ Enabled' : '✗ Disabled'}</Badge>
                  </div>
                  <div className={`p-3 rounded-lg border ${portfolio.canDeposit ? 'bg-green-500/10 border-green-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
                    <p className="text-sm font-semibold mb-1">Deposits</p>
                    <Badge variant={portfolio.canDeposit ? "default" : "secondary"}>{portfolio.canDeposit ? '✓ Enabled' : '✗ Disabled'}</Badge>
                  </div>
                  <div className={`p-3 rounded-lg border ${portfolio.canWithdraw ? 'bg-yellow-500/10 border-yellow-500/20' : 'bg-green-500/10 border-green-500/20'}`}>
                    <p className="text-sm font-semibold mb-1">Withdrawals</p>
                    <Badge variant={portfolio.canWithdraw ? "destructive" : "default"}>{portfolio.canWithdraw ? '⚠ Enabled' : '✓ Disabled'}</Badge>
                  </div>
                </div>
                <p className="text-xs text-muted-foreground mt-3">For security, withdrawals should remain disabled</p>
              </CardContent>
            </Card>
          </>
        )}
      </main>
    </div>
  );
};

export default Portfolio;
