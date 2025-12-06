import Navbar from "@/components/Navbar";
import QuantumDashboard from "@/components/QuantumDashboard";
import { Live6DWaveformVisualizer } from "@/components/Live6DWaveformVisualizer";
import QuantumFieldVisualizer from "@/components/QuantumFieldVisualizer";
import { HarmonicWaveform6DStatus } from "@/components/warroom/HarmonicWaveform6DStatus";
import { ProbabilityMatrixDisplay } from "@/components/warroom/ProbabilityMatrixDisplay";
import { ProbabilityReconstructionPanel } from "@/components/ProbabilityReconstructionPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ecosystemConnector } from "@/core/ecosystemConnector";
import { useEffect, useState } from "react";

const Quantum = () => {
  const [waveform6D, setWaveform6D] = useState(ecosystemConnector.getWaveform6D());
  const [probabilityFusion, setProbabilityFusion] = useState(ecosystemConnector.getProbabilityFusion());

  useEffect(() => {
    const unsubscribe = ecosystemConnector.subscribe((state) => {
      setWaveform6D(state.waveform6D);
      setProbabilityFusion(state.probabilityFusion);
    });
    return unsubscribe;
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🔮</span>
            <h1 className="text-3xl font-bold text-foreground">Quantum Field State</h1>
          </div>
          
          {/* Live 6D Visualization */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Live 6D Harmonic Waveform</CardTitle>
            </CardHeader>
            <CardContent>
              <Live6DWaveformVisualizer />
            </CardContent>
          </Card>
          
          {/* 6D Status + Probability Matrix */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <HarmonicWaveform6DStatus waveform={waveform6D} />
            <ProbabilityMatrixDisplay fusion={probabilityFusion} />
          </div>
          
          {/* Probability Reconstruction */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Probability Reconstruction</CardTitle>
            </CardHeader>
            <CardContent>
              <ProbabilityReconstructionPanel />
            </CardContent>
          </Card>
          
          {/* Master Equation + Field Visualizer */}
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
                <CardTitle className="text-lg">Quantum Field Visualization</CardTitle>
              </CardHeader>
              <CardContent>
                <QuantumFieldVisualizer />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Quantum;
