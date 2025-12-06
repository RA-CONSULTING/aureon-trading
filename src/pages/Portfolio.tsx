import Navbar from "@/components/Navbar";
import { AssetInventoryPanel } from "@/components/AssetInventoryPanel";
import { RealBinanceBalances } from "@/components/RealBinanceBalances";
import { KrakenStatusPanel } from "@/components/KrakenStatusPanel";
import { AssetPriceListPanel } from "@/components/AssetPriceListPanel";
import { UserDataVerificationPanel } from "@/components/UserDataVerificationPanel";
import { ExchangeDataVerificationPanel } from "@/components/ExchangeDataVerificationPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Portfolio = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">💼</span>
            <h1 className="text-3xl font-bold text-foreground">Portfolio & Exchanges</h1>
          </div>
          
          {/* Data Verification */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UserDataVerificationPanel />
            <ExchangeDataVerificationPanel />
          </div>
          
          {/* Exchange Balances */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Binance Balances</CardTitle>
              </CardHeader>
              <CardContent>
                <RealBinanceBalances />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Kraken Status</CardTitle>
              </CardHeader>
              <CardContent>
                <KrakenStatusPanel />
              </CardContent>
            </Card>
          </div>
          
          {/* Full Asset Price List */}
          <AssetPriceListPanel />
          
          {/* Asset Inventory */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Asset Inventory</CardTitle>
            </CardHeader>
            <CardContent>
              <AssetInventoryPanel />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Portfolio;
