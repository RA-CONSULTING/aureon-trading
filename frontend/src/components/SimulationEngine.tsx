import React, { useState, useEffect } from 'react';
// import { motion } from 'framer-motion';
import { Card } from './ui/card';
import { Button } from './ui/button';

interface SimulationData {
  time: number;
  phi: number;
  kappa: number;
  psi: number;
  tsv: number;
  guardianPhase: number;
  anchorPhase: number;
}

export const SimulationEngine: React.FC<{ tool: string }> = ({ tool }) => {
  const [isRunning, setIsRunning] = useState(false);
  const [data, setData] = useState<SimulationData[]>([]);
  const [currentStep, setCurrentStep] = useState(0);

  // Generate synthetic simulation data
  const generateSimData = (): SimulationData[] => {
    const steps = 100;
    return Array.from({ length: steps }, (_, i) => {
      const t = i / steps;
      const phi = Math.sin(t * 2 * Math.PI + Math.random() * 0.5) * 0.8;
      const kappa = Math.cos(t * 3 * Math.PI) * 0.6 + Math.random() * 0.2;
      const psi = Math.sin(t * 4 * Math.PI) * Math.exp(-t * 0.5) + Math.random() * 0.1;
      const tsv = (phi * kappa + psi) / 3;
      
      return {
        time: t * 1000,
        phi,
        kappa,
        psi,
        tsv,
        guardianPhase: phi * 180,
        anchorPhase: kappa * 180,
      };
    });
  };

  const runSimulation = async () => {
    setIsRunning(true);
    const simData = generateSimData();
    setData([]);
    setCurrentStep(0);

    // Animate data loading
    for (let i = 0; i < simData.length; i += 5) {
      await new Promise(resolve => setTimeout(resolve, 50));
      setData(prev => [...prev, ...simData.slice(i, i + 5)]);
      setCurrentStep(i + 5);
    }
    setIsRunning(false);
  };

  const renderTensorEvolution = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="font-semibold text-slate-700">Tensor Evolution (φ, κ, ψ, TSV)</h4>
        <Button onClick={runSimulation} disabled={isRunning} size="sm">
          {isRunning ? 'Running...' : 'Start Evolution'}
        </Button>
      </div>
      
      {data.length > 0 && (
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <div className="text-xs text-slate-500">Φ (Phase) - Current: {data[data.length - 1]?.phi.toFixed(3)}</div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.abs(data[data.length - 1]?.phi || 0) * 100}%` }}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="text-xs text-slate-500">κ (Coherence) - Current: {data[data.length - 1]?.kappa.toFixed(3)}</div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-green-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.abs(data[data.length - 1]?.kappa || 0) * 100}%` }}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="text-xs text-slate-500">ψ (Amplitude) - Current: {data[data.length - 1]?.psi.toFixed(3)}</div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-purple-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.abs(data[data.length - 1]?.psi || 0) * 100}%` }}
              />
            </div>
          </div>
          
          <div className="space-y-2">
            <div className="text-xs text-slate-500">TSV (Tensor) - Current: {data[data.length - 1]?.tsv.toFixed(3)}</div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div 
                className="bg-orange-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.abs(data[data.length - 1]?.tsv || 0) * 100}%` }}
              />
            </div>
          </div>
        </div>
      )}
      
      <div className="text-xs text-slate-500">
        Progress: {currentStep}/100 steps • {isRunning ? 'Evolving...' : 'Ready'}
      </div>
    </div>
  );

  const renderStabilityMonitor = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">Stability Monitor</h4>
      {data.length > 0 && (
        <div className="grid grid-cols-3 gap-4">
          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">
              {Math.max(...data.map(d => Math.abs(d.psi))).toFixed(3)}
            </div>
            <div className="text-xs text-slate-500">Max ψ Amplitude</div>
          </div>
          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {(data.reduce((sum, d) => sum + Math.abs(d.tsv), 0) / data.length).toFixed(3)}
            </div>
            <div className="text-xs text-slate-500">Avg TSV</div>
          </div>
          <div className="text-center p-3 bg-slate-50 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">
              {Math.abs(data[data.length - 1]?.guardianPhase - data[data.length - 1]?.anchorPhase).toFixed(1)}°
            </div>
            <div className="text-xs text-slate-500">Phase Diff</div>
          </div>
        </div>
      )}
    </div>
  );

  switch (tool) {
    case 'tensor':
      return <Card>{renderTensorEvolution()}</Card>;
    case 'stability':
      return <Card>{renderStabilityMonitor()}</Card>;
    case 'compare':
      return <Card><div className="p-8 text-center text-slate-500">System State Comparison Tool</div></Card>;
    case 'pattern':
      return <Card><div className="p-8 text-center text-slate-500">Pattern Tracker Interface</div></Card>;
    default:
      return <Card><div className="p-8 text-center text-slate-500">Select a simulation tool</div></Card>;
  }
};