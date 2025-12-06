import Navbar from "@/components/Navbar";
import { BacktestingInterface } from "@/components/BacktestingInterface";
import { SimulationDashboard } from "@/components/SimulationDashboard";
import { SimulationVerificationPanel } from "@/components/SimulationVerificationPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Backtest = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🔬</span>
            <h1 className="text-3xl font-bold text-foreground">Backtesting & Simulation</h1>
          </div>
          
          {/* Simulation Verification */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Simulation Verification</CardTitle>
            </CardHeader>
            <CardContent>
              <SimulationVerificationPanel />
            </CardContent>
          </Card>
          
          {/* Backtesting Interface */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Backtesting Interface</CardTitle>
            </CardHeader>
            <CardContent>
              <BacktestingInterface />
            </CardContent>
          </Card>
          
          {/* Simulation Dashboard */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Simulation Dashboard</CardTitle>
            </CardHeader>
            <CardContent>
              <SimulationDashboard />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Backtest;
