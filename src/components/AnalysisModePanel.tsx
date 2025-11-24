import React, { useState, useEffect } from 'react';
// import { motion } from 'framer-motion';
import { Card } from './ui/card';
import { Button } from './ui/button';

interface PhaseData {
  guardianPhase: number;
  anchorPhase: number;
  phaseDiff: number;
  coherence: number;
  synchrony: number;
}

export const AnalysisModePanel: React.FC<{ tool: string }> = ({ tool }) => {
  const [phaseData, setPhaseData] = useState<PhaseData[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [memoryTrace, setMemoryTrace] = useState<number[]>([]);

  const generatePhaseData = (): PhaseData[] => {
    return Array.from({ length: 50 }, (_, i) => {
      const t = i / 50;
      const guardianPhase = Math.sin(t * 4 * Math.PI) * 180;
      const anchorPhase = Math.cos(t * 3 * Math.PI) * 180;
      const phaseDiff = Math.abs(guardianPhase - anchorPhase);
      const coherence = Math.exp(-phaseDiff / 180) * 0.8 + Math.random() * 0.2;
      const synchrony = coherence > 0.6 ? 1 : 0;
      
      return { guardianPhase, anchorPhase, phaseDiff, coherence, synchrony };
    });
  };

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    await new Promise(resolve => setTimeout(resolve, 1200));
    
    const data = generatePhaseData();
    setPhaseData(data);
    
    // Generate memory trace
    const trace = Array.from({ length: 20 }, () => Math.random());
    setMemoryTrace(trace);
    
    setIsAnalyzing(false);
  };

  const renderPhaseDynamics = () => (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h4 className="font-semibold text-slate-700">Phase Dynamics Interpreter</h4>
        <Button onClick={runAnalysis} disabled={isAnalyzing} size="sm">
          {isAnalyzing ? 'Analyzing...' : 'Run Analysis'}
        </Button>
      </div>
      
      {phaseData.length > 0 && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {phaseData[phaseData.length - 1]?.guardianPhase.toFixed(1)}°
              </div>
              <div className="text-xs text-slate-500">Guardian Phase</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {phaseData[phaseData.length - 1]?.anchorPhase.toFixed(1)}°
              </div>
              <div className="text-xs text-slate-500">Anchor Phase</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {phaseData[phaseData.length - 1]?.coherence.toFixed(3)}
              </div>
              <div className="text-xs text-slate-500">Coherence</div>
            </div>
          </div>
          
          <div className="relative h-32 bg-slate-900 rounded-lg overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-24 h-24 border-2 border-blue-400 rounded-full relative">
                <div className="absolute top-0 left-1/2 w-0.5 h-12 bg-blue-400 -translate-x-0.5" />
                <div className="absolute -top-1 left-1/2 w-2 h-2 bg-blue-400 rounded-full -translate-x-1" />
              </div>
              
              <div className="w-16 h-16 border-2 border-green-400 rounded-full relative ml-4">
                <div className="absolute top-0 left-1/2 w-0.5 h-8 bg-green-400 -translate-x-0.5" />
                <div className="absolute -top-1 left-1/2 w-2 h-2 bg-green-400 rounded-full -translate-x-1" />
              </div>
            </div>
            
            <div className="absolute bottom-2 left-2 text-xs text-white">
              Guardian (Blue) • Anchor (Green)
            </div>
          </div>
          
          <div className="text-xs text-slate-500">
            Synchrony Events: {phaseData.filter(d => d.synchrony === 1).length}/50 • 
            Avg Coherence: {(phaseData.reduce((sum, d) => sum + d.coherence, 0) / phaseData.length).toFixed(3)}
          </div>
        </div>
      )}
    </div>
  );

  const renderMemoryTracer = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">Symbolic Memory Tracer</h4>
      
      {memoryTrace.length > 0 && (
        <div className="space-y-3">
          <div className="h-20 bg-slate-100 rounded-lg p-3">
            <div className="text-xs text-slate-500 mb-2">Pattern Correlation Over Time</div>
            <div className="flex items-end gap-1 h-12">
              {memoryTrace.map((value, idx) => (
                <div
                  key={idx}
                  className="bg-purple-500 rounded-sm flex-1 transition-all duration-300"
                  style={{ height: `${value * 100}%` }}
                />
              ))}
            </div>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="p-3 bg-slate-50 rounded">
              <div className="font-medium text-slate-700">Peak Correlation</div>
              <div className="text-lg font-mono text-purple-600">
                {Math.max(...memoryTrace).toFixed(3)}
              </div>
            </div>
            <div className="p-3 bg-slate-50 rounded">
              <div className="font-medium text-slate-700">Memory Persistence</div>
              <div className="text-lg font-mono text-purple-600">
                {(memoryTrace.filter(v => v > 0.5).length / memoryTrace.length * 100).toFixed(0)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderStabilityAnalyst = () => (
    <div className="space-y-4">
      <h4 className="font-semibold text-slate-700">Stability Analyst</h4>
      
      <div className="grid grid-cols-2 gap-4">
        <div className="p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-green-500 rounded-full" />
            <span className="font-medium text-green-700">Bounded Regime</span>
          </div>
          <div className="text-sm text-green-600">
            System exhibits stable oscillations within expected parameters
          </div>
        </div>
        
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
          <div className="flex items-center gap-2 mb-2">
            <div className="w-3 h-3 bg-orange-500 rounded-full animate-pulse" />
            <span className="font-medium text-orange-700">Edge Dynamics</span>
          </div>
          <div className="text-sm text-orange-600">
            Approaching phase transition threshold
          </div>
        </div>
      </div>
    </div>
  );

  switch (tool) {
    case 'phase':
      return <Card>{renderPhaseDynamics()}</Card>;
    case 'memory':
      return <Card>{renderMemoryTracer()}</Card>;
    case 'stability':
      return <Card>{renderStabilityAnalyst()}</Card>;
    case 'temporal':
      return <Card><div className="p-8 text-center text-slate-500">Temporal Synthesizer Interface</div></Card>;
    default:
      return <Card><div className="p-8 text-center text-slate-500">Select an analysis tool</div></Card>;
  }
};