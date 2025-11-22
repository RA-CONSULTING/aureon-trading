import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, TrendingUp, TrendingDown } from "lucide-react";
import Navbar from "@/components/Navbar";
import { QuickTrade } from "@/components/QuickTrade";
import { BinancePortfolioWidget } from "@/components/BinancePortfolioWidget";
import { QGITASignalPanel } from "@/components/QGITASignalPanel";
import { QGITAConfigPanel } from "@/components/QGITAConfigPanel";
import { QGITAAutoTradingControl } from "@/components/QGITAAutoTradingControl";
import { QueenHiveControl } from "@/components/QueenHiveControl";
import { OMSQueueMonitor } from "@/components/OMSQueueMonitor";
import { QGITAOMSIntegrationStatus } from "@/components/QGITAOMSIntegrationStatus";
import { AutomatedHuntControl } from "@/components/AutomatedHuntControl";
import { useQueenHive } from "@/hooks/useQueenHive";
import { useQGITAAutoTrading, useQGITAAutoTradingToggle } from "@/hooks/useQGITAAutoTrading";
import { useState, useEffect } from "react";
import { supabase } from "@/integrations/supabase/client";
import { useQGITASignals } from "@/hooks/useQGITASignals";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

const marketsData = [
  { category: "Cryptocurrencies", assets: [
    { symbol: "BTC/USD", name: "Bitcoin", price: "43,250.00", change: "+2.45%", volume: "$28.5B", positive: true },
    { symbol: "ETH/USD", name: "Ethereum", price: "2,285.50", change: "+1.82%", volume: "$12.3B", positive: true },
    { symbol: "BNB/USD", name: "Binance Coin", price: "315.80", change: "-0.45%", volume: "$1.8B", positive: false },
    { symbol: "SOL/USD", name: "Solana", price: "98.35", change: "+5.23%", volume: "$2.1B", positive: true },
  ]},
  { category: "Forex", assets: [
    { symbol: "EUR/USD", name: "Euro / US Dollar", price: "1.0875", change: "-0.23%", volume: "$580B", positive: false },
    { symbol: "GBP/USD", name: "British Pound", price: "1.2654", change: "+0.45%", volume: "$420B", positive: true },
    { symbol: "USD/JPY", name: "US Dollar / Yen", price: "149.85", change: "-0.12%", volume: "$490B", positive: false },
    { symbol: "AUD/USD", name: "Australian Dollar", price: "0.6542", change: "+0.78%", volume: "$180B", positive: true },
  ]},
  { category: "Commodities", assets: [
    { symbol: "XAU/USD", name: "Gold", price: "2,035.80", change: "+0.89%", volume: "$145B", positive: true },
    { symbol: "XAG/USD", name: "Silver", price: "23.45", change: "+1.23%", volume: "$18B", positive: true },
    { symbol: "WTI", name: "Crude Oil", price: "78.25", change: "-0.56%", volume: "$95B", positive: false },
    { symbol: "NG", name: "Natural Gas", price: "2.89", change: "-1.45%", volume: "$12B", positive: false },
  ]},
];

const Markets = () => {
  const [balances, setBalances] = useState<any>(null);
  const [canTrade, setCanTrade] = useState(false);
  const [isLoadingPortfolio, setIsLoadingPortfolio] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState('BTCUSDT');
  const { session: hiveSession } = useQueenHive();
  
  // QGITA Auto-Trading
  const { isEnabled: autoTradingEnabled, setIsEnabled: setAutoTradingEnabled } = useQGITAAutoTradingToggle();
  const { latestSignal } = useQGITASignals(selectedSymbol);
  const { isExecuting: isAutoTrading } = useQGITAAutoTrading({
    signal: latestSignal,
    symbol: selectedSymbol,
    currentPrice: balances?.prices?.[selectedSymbol] || 0,
    enabled: autoTradingEnabled,
  });

  useEffect(() => {
    fetchPortfolio();
  }, []);

  const fetchPortfolio = async () => {
    setIsLoadingPortfolio(true);
    try {
      const { data, error } = await supabase.functions.invoke('fetch-binance-portfolio');
      
      if (error) throw error;
      
      if (data.balances) {
        setBalances(data.balances);
        setCanTrade(data.canTrade || false);
      }
    } catch (error) {
      console.error('Error fetching portfolio:', error);
    } finally {
      setIsLoadingPortfolio(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left side - Markets listings */}
          <div className="lg:col-span-2 space-y-8">
            <div className="mb-8">
              <h1 className="text-4xl font-bold mb-2">Markets</h1>
              <p className="text-muted-foreground">Explore trading opportunities across global markets</p>
            </div>

            {/* Search */}
            <div className="mb-8">
              <div className="relative max-w-md">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input 
                  placeholder="Search markets..." 
                  className="pl-10 bg-card border-border"
                />
              </div>
            </div>

            {/* Markets by Category */}
            <div className="space-y-8">
              {marketsData.map((category) => (
                <div key={category.category}>
                  <h2 className="text-2xl font-bold mb-4">{category.category}</h2>
                  <div className="grid gap-4">
                    {category.assets.map((asset) => (
                      <Card key={asset.symbol} className="bg-card shadow-card hover:shadow-glow transition-all duration-300 cursor-pointer">
                        <CardContent className="p-6">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4 flex-1">
                              <div>
                                <p className="font-bold text-lg">{asset.symbol}</p>
                                <p className="text-sm text-muted-foreground">{asset.name}</p>
                              </div>
                            </div>

                            <div className="flex items-center gap-8">
                              <div className="text-right">
                                <p className="text-sm text-muted-foreground mb-1">Price</p>
                                <p className="font-bold text-lg">${asset.price}</p>
                              </div>

                              <div className="text-right">
                                <p className="text-sm text-muted-foreground mb-1">24h Change</p>
                                <p className={`font-bold text-lg flex items-center gap-1 ${
                                  asset.positive ? "text-success" : "text-destructive"
                                }`}>
                                  {asset.positive ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                                  {asset.change}
                                </p>
                              </div>

                              <div className="text-right">
                                <p className="text-sm text-muted-foreground mb-1">Volume</p>
                                <p className="font-semibold">{asset.volume}</p>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Right side - Trading Controls */}
          <div className="lg:col-span-1">
            <div className="sticky top-24 space-y-6">
              <Tabs defaultValue="hunt" className="w-full">
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="hunt">🦁 Hunt</TabsTrigger>
                  <TabsTrigger value="qgita">QGITA</TabsTrigger>
                  <TabsTrigger value="hive">Hive</TabsTrigger>
                </TabsList>
                
                <TabsContent value="hunt" className="mt-6 space-y-6">
                  <AutomatedHuntControl />
                  <OMSQueueMonitor sessionId={hiveSession?.id || null} />
                </TabsContent>

                <TabsContent value="qgita" className="space-y-6 mt-6">
                  <QGITAAutoTradingControl
                    isEnabled={autoTradingEnabled}
                    onToggle={setAutoTradingEnabled}
                    isExecuting={isAutoTrading}
                  />
                  <QGITAOMSIntegrationStatus />
                  <QGITASignalPanel symbol={selectedSymbol} />
                  <QGITAConfigPanel />
                  <QuickTrade balances={balances} canTrade={canTrade} />
                </TabsContent>
                
                <TabsContent value="hive" className="mt-6 space-y-6">
                  <QueenHiveControl />
                  <OMSQueueMonitor sessionId={hiveSession?.id || null} />
                </TabsContent>
              </Tabs>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Markets;
