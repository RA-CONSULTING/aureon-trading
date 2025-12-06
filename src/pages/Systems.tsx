import Navbar from "@/components/Navbar";
import SystemRegistryPanel from "@/components/SystemRegistryPanel";
import { UnifiedBusStatus } from "@/components/warroom/UnifiedBusStatus";
import { TemporalLadderStatus } from "@/components/warroom/TemporalLadderStatus";
import { EcosystemStatus } from "@/components/warroom/EcosystemStatus";
import { DataStreamMonitorPanel } from "@/components/DataStreamMonitorPanel";
import { SmokeTestPhasePanel } from "@/components/SmokeTestPhasePanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Systems = () => {
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
