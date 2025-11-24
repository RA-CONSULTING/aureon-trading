import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

export const QuantumAnalytics = () => {
  const [quantumState, setQuantumState] = useState({
    entanglement: 0.92,
    coherence: 0.87,
    superposition: 0.76,
    fieldStability: 0.94
  });

  const [matrixData, setMatrixData] = useState([
    { dimension: 'X', value: 0.847, stability: 0.92 },
    { dimension: 'Y', value: 0.923, stability: 0.88 },
    { dimension: 'Z', value: 0.756, stability: 0.95 },
    { dimension: 'T', value: 0.681, stability: 0.79 }
  ]);

  const [particles, setParticles] = useState([
    { id: 'Q1', spin: 0.5, energy: 1.24, phase: 45 },
    { id: 'Q2', spin: -0.5, energy: 1.18, phase: 127 },
    { id: 'Q3', spin: 0.5, energy: 1.31, phase: 289 },
    { id: 'Q4', spin: -0.5, energy: 1.09, phase: 156 }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setQuantumState(prev => ({
        entanglement: Math.max(0.1, prev.entanglement + (Math.random() - 0.5) * 0.02),
        coherence: Math.max(0.1, prev.coherence + (Math.random() - 0.5) * 0.03),
        superposition: Math.max(0.1, prev.superposition + (Math.random() - 0.5) * 0.04),
        fieldStability: Math.max(0.1, prev.fieldStability + (Math.random() - 0.5) * 0.01)
      }));

      setMatrixData(prev => prev.map(d => ({
        ...d,
        value: Math.max(0.1, d.value + (Math.random() - 0.5) * 0.05),
        stability: Math.max(0.1, d.stability + (Math.random() - 0.5) * 0.02)
      })));

      setParticles(prev => prev.map(p => ({
        ...p,
        energy: Math.max(0.5, p.energy + (Math.random() - 0.5) * 0.1),
        phase: (p.phase + Math.random() * 10) % 360
      })));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Entanglement</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {(quantumState.entanglement * 100).toFixed(1)}%
            </div>
            <Progress value={quantumState.entanglement * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Coherence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(quantumState.coherence * 100).toFixed(1)}%
            </div>
            <Progress value={quantumState.coherence * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Superposition</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {(quantumState.superposition * 100).toFixed(1)}%
            </div>
            <Progress value={quantumState.superposition * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Field Stability</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(quantumState.fieldStability * 100).toFixed(1)}%
            </div>
            <Progress value={quantumState.fieldStability * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Matrix Dimensions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {matrixData.map((dim, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <Badge variant="outline">{dim.dimension}-Dimension</Badge>
                    <span className="text-sm font-bold">{dim.value.toFixed(3)}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-600 w-16">Stability:</span>
                    <Progress value={dim.stability * 100} className="flex-1" />
                    <span className="text-xs w-12">{(dim.stability * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quantum Particles</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {particles.map((particle, index) => (
                <div key={index} className="border rounded-lg p-3">
                  <div className="flex justify-between items-center mb-2">
                    <Badge variant={particle.spin > 0 ? "default" : "secondary"}>
                      {particle.id} (↑{particle.spin > 0 ? '+' : '-'})
                    </Badge>
                    <span className="text-sm font-bold">{particle.energy.toFixed(2)} eV</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-600 w-12">Phase:</span>
                    <Progress value={(particle.phase / 360) * 100} className="flex-1" />
                    <span className="text-xs w-12">{particle.phase.toFixed(0)}°</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default QuantumAnalytics;