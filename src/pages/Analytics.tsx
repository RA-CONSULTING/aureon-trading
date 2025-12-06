import Navbar from "@/components/Navbar";
import { TradingAnalytics } from "@/components/TradingAnalytics";
import { PerformanceMetricsDashboard } from "@/components/PerformanceMetricsDashboard";
import DecisionVerificationPanel from "@/components/DecisionVerificationPanel";
import { LiveTradingStatusPanel } from "@/components/LiveTradingStatusPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Analytics = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">📊</span>
            <h1 className="text-3xl font-bold text-foreground">Trading Analytics</h1>
          </div>
          
          {/* Live Status + Decision Verification */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Live Trading Status</CardTitle>
              </CardHeader>
              <CardContent>
                <LiveTradingStatusPanel />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Decision Verification</CardTitle>
              </CardHeader>
              <CardContent>
                <DecisionVerificationPanel />
              </CardContent>
            </Card>
          </div>
          
          {/* Performance Metrics */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Performance Metrics</CardTitle>
            </CardHeader>
            <CardContent>
              <PerformanceMetricsDashboard />
            </CardContent>
          </Card>
          
          {/* Trading Analytics */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Trading Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <TradingAnalytics />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Analytics;
