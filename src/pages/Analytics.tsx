import Navbar from '@/components/Navbar';
import { CoherenceTrendChart } from '@/components/analytics/CoherenceTrendChart';
import { LHEFrequencyChart } from '@/components/analytics/LHEFrequencyChart';
import { SignalDistributionChart } from '@/components/analytics/SignalDistributionChart';
import { OptimalEntryStats } from '@/components/analytics/OptimalEntryStats';
import { Card } from '@/components/ui/card';

const Analytics = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8 pt-24">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">📊 Analytics Dashboard</h1>
          <p className="text-muted-foreground">
            Real-time performance metrics and insights from the AUREON Quantum Trading System
          </p>
        </div>

        {/* Stats Cards */}
        <div className="mb-8">
          <OptimalEntryStats />
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <CoherenceTrendChart />
          <LHEFrequencyChart />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          <SignalDistributionChart />
          
          <Card className="p-6">
            <h3 className="text-lg font-semibold mb-4">💡 Performance Insights</h3>
            <div className="space-y-4">
              <div className="border-l-4 border-primary pl-4">
                <p className="text-sm font-medium">Optimal Trading Conditions</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Signals are strongest when Γ &gt; 0.945, Lighthouse Events are detected, 
                  and The Prism reaches Level 4-5 (CONVERGING/MANIFEST state).
                </p>
              </div>
              
              <div className="border-l-4 border-green-500 pl-4">
                <p className="text-sm font-medium">Golden Ratio Timing</p>
                <p className="text-xs text-muted-foreground mt-1">
                  FTCP detection identifies moments where market dynamics align with 
                  φ (1.618) temporal patterns, indicating natural resonance points.
                </p>
              </div>
              
              <div className="border-l-4 border-blue-500 pl-4">
                <p className="text-sm font-medium">Lighthouse Consensus</p>
                <p className="text-xs text-muted-foreground mt-1">
                  The 5-metric validation (Cₗᵢₙ, Cₙₒₙₗᵢₙ, Cφ, Gₑff, |Q|) ensures 
                  only high-confidence events trigger LHE confirmations.
                </p>
              </div>

              <div className="border-l-4 border-purple-500 pl-4">
                <p className="text-sm font-medium">The Prism Transformation</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Watch for transitions from FEAR (levels 1-2) through FORMING (3) 
                  to LOVE (4-5) at 528 Hz for optimal trade timing.
                </p>
              </div>
            </div>
          </Card>
        </div>

        <Card className="p-6">
          <h3 className="text-lg font-semibold mb-4">🌈 System Architecture</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h4 className="font-medium mb-2">Layer 1: Technical</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• WebSocket market streams</li>
                <li>• Real-time price/volume data</li>
                <li>• FTCP curvature detection</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Layer 2: Mathematical</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Master Equation Λ(t)</li>
                <li>• 9 Auris node computation</li>
                <li>• Lighthouse consensus L(t)</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-medium mb-2">Layer 3: Transformational</h4>
              <ul className="text-sm text-muted-foreground space-y-1">
                <li>• Rainbow Bridge frequencies</li>
                <li>• The Prism (5 levels)</li>
                <li>• 528 Hz LOVE convergence</li>
              </ul>
            </div>
          </div>
        </Card>
      </main>
    </div>
  );
};

export default Analytics;
