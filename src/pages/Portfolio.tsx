import Navbar from "@/components/Navbar";
import { AssetInventoryPanel } from "@/components/AssetInventoryPanel";
import { RealBinanceBalances } from "@/components/RealBinanceBalances";
import { KrakenStatusPanel } from "@/components/KrakenStatusPanel";
import { AlpacaStatusPanel } from "@/components/AlpacaStatusPanel";
import { CapitalStatusPanel } from "@/components/CapitalStatusPanel";
import { AssetPriceListPanel } from "@/components/AssetPriceListPanel";
import { UserDataVerificationPanel } from "@/components/UserDataVerificationPanel";
import { ExchangeDataVerificationPanel } from "@/components/ExchangeDataVerificationPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useNavigate } from "react-router-dom";
import { Settings } from "lucide-react";

const Portfolio = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-3xl">💼</span>
              <h1 className="text-3xl font-bold text-foreground">Portfolio & Exchanges</h1>
            </div>
            <Button variant="outline" onClick={() => navigate('/settings')}>
              <Settings className="h-4 w-4 mr-2" />
              Configure API Keys
            </Button>
          </div>
          
          {/* Data Verification */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <UserDataVerificationPanel />
            <ExchangeDataVerificationPanel />
          </div>
          
          {/* All 4 Exchange Balances */}
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span>🟡</span> Binance
                </CardTitle>
              </CardHeader>
              <CardContent>
                <RealBinanceBalances />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span>🦑</span> Kraken
                </CardTitle>
              </CardHeader>
              <CardContent>
                <KrakenStatusPanel />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span>🦙</span> Alpaca
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AlpacaStatusPanel />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-lg flex items-center gap-2">
                  <span>💼</span> Capital.com
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CapitalStatusPanel />
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
