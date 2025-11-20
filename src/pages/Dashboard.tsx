import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DollarSign, Activity } from "lucide-react";
import Navbar from "@/components/Navbar";
import { LiveTradingSignals } from "@/components/LiveTradingSignals";
import { LiveCoherenceTracker } from "@/components/LiveCoherenceTracker";
import { useLiveTradingSignals } from "@/hooks/useLiveTradingSignals";

const Dashboard = () => {
  const { lastMarketData } = useLiveTradingSignals('btcusdt');

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Trading Dashboard</h1>
          <p className="text-muted-foreground">Monitor live market data and trading signals</p>
        </div>

        {/* Live Market Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-card shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">BTC Price</CardTitle>
              <DollarSign className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                ${lastMarketData ? lastMarketData.price.toFixed(2) : '---'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Live from Binance WebSocket
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Volume</CardTitle>
              <Activity className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {lastMarketData ? (lastMarketData.volume * 100).toFixed(1) + '%' : '---'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Normalized 24h volume
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Volatility</CardTitle>
              <Activity className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {lastMarketData ? (lastMarketData.volatility * 100).toFixed(1) + '%' : '---'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Real-time volatility
              </p>
            </CardContent>
          </Card>

          <Card className="bg-card shadow-card">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">Momentum</CardTitle>
              <Activity className="h-4 w-4 text-primary" />
            </CardHeader>
            <CardContent>
              <div className={`text-2xl font-bold ${lastMarketData && lastMarketData.momentum > 0 ? 'text-success' : 'text-destructive'}`}>
                {lastMarketData ? (lastMarketData.momentum * 100).toFixed(1) + '%' : '---'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Price momentum
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Grid - Live Components */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live Coherence Tracker */}
          <LiveCoherenceTracker symbol="btcusdt" />

          {/* Live Trading Signals */}
          <LiveTradingSignals symbol="btcusdt" />
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
