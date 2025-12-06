import Navbar from "@/components/Navbar";
import QuantumDashboard from "@/components/QuantumDashboard";
import { Live6DWaveformVisualizer } from "@/components/Live6DWaveformVisualizer";
import QuantumFieldVisualizer from "@/components/QuantumFieldVisualizer";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Quantum = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🔮</span>
            <h1 className="text-3xl font-bold text-foreground">Quantum Field State</h1>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Master Equation Λ(t)</CardTitle>
              </CardHeader>
              <CardContent>
                <QuantumDashboard />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">6D Harmonic Waveform</CardTitle>
              </CardHeader>
              <CardContent>
                <Live6DWaveformVisualizer />
              </CardContent>
            </Card>
          </div>
          
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Quantum Field Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              <QuantumFieldVisualizer />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Quantum;
