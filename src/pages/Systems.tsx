import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGlobalState } from '@/hooks/useGlobalState';
import Navbar from "@/components/Navbar";
import SystemRegistryPanel from "@/components/SystemRegistryPanel";
import { UnifiedBusStatus } from "@/components/warroom/UnifiedBusStatus";
import { TemporalLadderStatus } from "@/components/warroom/TemporalLadderStatus";
import { EcosystemStatus } from "@/components/warroom/EcosystemStatus";
import { DataStreamMonitorPanel } from "@/components/DataStreamMonitorPanel";
import { SmokeTestPhasePanel } from "@/components/SmokeTestPhasePanel";
import { ArbitrageScannerPanel } from "@/components/panels/ArbitrageScannerPanel";
import { TrailingStopPanel } from "@/components/panels/TrailingStopPanel";
import { PositionHeatPanel } from "@/components/panels/PositionHeatPanel";
import { PortfolioRebalancerPanel } from "@/components/panels/PortfolioRebalancerPanel";
import { MarketRegimeIndicator } from "@/components/panels/MarketRegimeIndicator";
import { NotificationSettingsPanel } from "@/components/panels/NotificationSettingsPanel";
import { ExchangeLearningPanel } from "@/components/panels/ExchangeLearningPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Systems = () => {
  const navigate = useNavigate();
  const { isInitialized, isAuthenticated } = useGlobalState();

  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      navigate('/auth');
    }
  }, [isInitialized, isAuthenticated, navigate]);

  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🧠</span>
            <h1 className="text-3xl font-bold text-foreground">System Registry</h1>
          </div>
          
          {/* System Health Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <UnifiedBusStatus />
            <TemporalLadderStatus />
            <EcosystemStatus />
          </div>

          {/* Risk Management & Trading Systems */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <ArbitrageScannerPanel />
            <TrailingStopPanel />
            <PositionHeatPanel />
          </div>

          {/* Portfolio & Market Analysis */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <PortfolioRebalancerPanel />
            <MarketRegimeIndicator />
            <NotificationSettingsPanel />
            <ExchangeLearningPanel />
          </div>
          
          {/* Diagnostics */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Smoke Test Validator</CardTitle>
              </CardHeader>
              <CardContent>
                <SmokeTestPhasePanel />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Data Stream Monitor</CardTitle>
              </CardHeader>
              <CardContent>
                <DataStreamMonitorPanel />
              </CardContent>
            </Card>
          </div>
          
          {/* Full System Registry */}
          <SystemRegistryPanel />
        </div>
      </main>
    </div>
  );
};

export default Systems;
