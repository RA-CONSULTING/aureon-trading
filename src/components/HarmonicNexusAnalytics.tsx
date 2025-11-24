import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

export const HarmonicNexusAnalytics = () => {
  const [resonanceData, setResonanceData] = useState({
    frequency: 7.83,
    amplitude: 0.75,
    coherence: 0.89,
    fieldStrength: 0.92
  });

  const [harmonics, setHarmonics] = useState([
    { freq: 7.83, amplitude: 0.92, phase: 0 },
    { freq: 14.3, amplitude: 0.67, phase: 45 },
    { freq: 20.8, amplitude: 0.43, phase: 90 },
    { freq: 27.3, amplitude: 0.28, phase: 135 }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setResonanceData(prev => ({
        frequency: 7.83 + (Math.random() - 0.5) * 0.1,
        amplitude: Math.max(0.1, prev.amplitude + (Math.random() - 0.5) * 0.05),
        coherence: Math.max(0.1, prev.coherence + (Math.random() - 0.5) * 0.03),
        fieldStrength: Math.max(0.1, prev.fieldStrength + (Math.random() - 0.5) * 0.02)
      }));

      setHarmonics(prev => prev.map(h => ({
        ...h,
        amplitude: Math.max(0.1, h.amplitude + (Math.random() - 0.5) * 0.05),
        phase: (h.phase + Math.random() * 5) % 360
      })));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Base Frequency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {resonanceData.frequency.toFixed(2)} Hz
            </div>
            <Progress value={resonanceData.frequency * 10} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Field Amplitude</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">
              {(resonanceData.amplitude * 100).toFixed(1)}%
            </div>
            <Progress value={resonanceData.amplitude * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Coherence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {(resonanceData.coherence * 100).toFixed(1)}%
            </div>
            <Progress value={resonanceData.coherence * 100} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Field Strength</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(resonanceData.fieldStrength * 100).toFixed(1)}%
            </div>
            <Progress value={resonanceData.fieldStrength * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Harmonic Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {harmonics.map((harmonic, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <Badge variant="outline">{harmonic.freq.toFixed(1)} Hz</Badge>
                  <div className="text-sm text-gray-600">
                    Phase: {harmonic.phase.toFixed(0)}°
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sm w-12">{(harmonic.amplitude * 100).toFixed(0)}%</span>
                  <Progress value={harmonic.amplitude * 100} className="w-24" />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default HarmonicNexusAnalytics;