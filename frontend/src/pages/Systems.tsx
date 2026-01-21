import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useGlobalState } from '@/hooks/useGlobalState';
import Navbar from "@/components/Navbar";
import FullPortfolioDisplay from "@/components/FullPortfolioDisplay";
import SystemRegistryPanel from "@/components/SystemRegistryPanel";
import { UnifiedBusStatus } from "@/components/warroom/UnifiedBusStatus";
import { TemporalLadderStatus } from "@/components/warroom/TemporalLadderStatus";
import { EcosystemStatus } from "@/components/warroom/EcosystemStatus";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

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
            <span className="text-3xl">📊</span>
            <h1 className="text-3xl font-bold text-foreground">Portfolio & Systems</h1>
          </div>
          
          <Tabs defaultValue="portfolio" className="w-full">
            <TabsList className="grid w-full grid-cols-2 mb-6">
              <TabsTrigger value="portfolio">💰 Portfolio & Trades</TabsTrigger>
              <TabsTrigger value="systems">🧠 System Registry</TabsTrigger>
            </TabsList>

            {/* Portfolio Tab - Full balances, trades, positions */}
            <TabsContent value="portfolio">
              <FullPortfolioDisplay />
            </TabsContent>

            {/* Systems Tab - System health and registry */}
            <TabsContent value="systems" className="space-y-6">
              {/* System Health Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <UnifiedBusStatus />
                <TemporalLadderStatus />
                <EcosystemStatus />
              </div>
              
              {/* Full System Registry */}
              <SystemRegistryPanel />
            </TabsContent>
          </Tabs>
        </div>
      </main>
    </div>
  );
};

export default Systems;
