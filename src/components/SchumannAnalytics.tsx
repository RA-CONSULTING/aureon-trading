import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { HarmonicSpectrogram } from './HarmonicSpectrogram';
export const SchumannAnalytics = () => {
  const [resonanceData, setResonanceData] = useState({
    primaryFreq: 7.83,
    amplitude: 0.82,
    qFactor: 4.2,
    globalCoherence: 0.76
  });

  const [regionData, setRegionData] = useState([
    { region: 'North America', strength: 0.89, phase: 12 },
    { region: 'Europe', strength: 0.76, phase: 45 },
    { region: 'Asia', strength: 0.92, phase: 78 },
    { region: 'Africa', strength: 0.68, phase: 156 },
    { region: 'South America', strength: 0.74, phase: 234 },
    { region: 'Oceania', strength: 0.81, phase: 289 }
  ]);

  const [modeData, setModeData] = useState([
    { mode: 1, freq: 7.83, power: 0.92, active: true },
    { mode: 2, freq: 14.3, power: 0.67, active: true },
    { mode: 3, freq: 20.8, power: 0.43, active: false },
    { mode: 4, freq: 27.3, power: 0.28, active: true },
    { mode: 5, freq: 33.8, power: 0.15, active: false }
  ]);

  useEffect(() => {
    const interval = setInterval(() => {
      setResonanceData(prev => ({
        primaryFreq: 7.83 + (Math.random() - 0.5) * 0.05,
        amplitude: Math.max(0.1, prev.amplitude + (Math.random() - 0.5) * 0.03),
        qFactor: Math.max(1, prev.qFactor + (Math.random() - 0.5) * 0.2),
        globalCoherence: Math.max(0.1, prev.globalCoherence + (Math.random() - 0.5) * 0.02)
      }));

      setRegionData(prev => prev.map(r => ({
        ...r,
        strength: Math.max(0.1, r.strength + (Math.random() - 0.5) * 0.05),
        phase: (r.phase + Math.random() * 5) % 360
      })));

      setModeData(prev => prev.map(m => ({
        ...m,
        power: Math.max(0.05, m.power + (Math.random() - 0.5) * 0.03),
        active: Math.random() > 0.3
      })));
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Primary Frequency</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {resonanceData.primaryFreq.toFixed(2)} Hz
            </div>
            <Progress value={resonanceData.primaryFreq * 10} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Amplitude</CardTitle>
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
            <CardTitle className="text-sm">Q-Factor</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-purple-600">
              {resonanceData.qFactor.toFixed(1)}
            </div>
            <Progress value={resonanceData.qFactor * 20} className="mt-2" />
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Global Coherence</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600">
              {(resonanceData.globalCoherence * 100).toFixed(1)}%
            </div>
            <Progress value={resonanceData.globalCoherence * 100} className="mt-2" />
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Regional Resonance</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {regionData.map((region, index) => (
                <div key={index} className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <Badge variant="outline">{region.region}</Badge>
                    <div className="text-sm text-gray-600">
                      {region.phase.toFixed(0)}° phase
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm w-12">{(region.strength * 100).toFixed(0)}%</span>
                    <Progress value={region.strength * 100} className="w-20" />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>🌍 Schumann Resonance Modes</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {modeData.map((mode, index) => {
                const modeInfo = [
                  { 
                    title: "Mode 1 → Fundamental", 
                    physics: "The 'base note' of Earth's resonance", 
                    symbolic: "Grounding, stability, and the 'heartbeat of Gaia'",
                    freq: "~7.83 Hz"
                  },
                  { 
                    title: "Mode 2 → First Harmonic", 
                    physics: "First harmonic above the base. Shows global thunderstorm intensity", 
                    symbolic: "Creativity, decision-making, dynamic balance",
                    freq: "~14.3 Hz"
                  },
                  { 
                    title: "Mode 3 → Second Harmonic", 
                    physics: "Reflects complex Earth–ionosphere interactions", 
                    symbolic: "Transition states, problem-solving, clarity vs. confusion",
                    freq: "~20.8 Hz"
                  },
                  { 
                    title: "Mode 4 → Higher Harmonic", 
                    physics: "Sensitive to solar activity; fluctuates with geomagnetic conditions", 
                    symbolic: "Integration, subtle intuition, weaving higher patterns",
                    freq: "~27.3 Hz"
                  },
                  { 
                    title: "Mode 5 → Highest Harmonic", 
                    physics: "Fine-scale oscillations, weakest under normal conditions", 
                    symbolic: "Spiritual attunement, unity consciousness, the 'higher voice' of Gaia",
                    freq: "~33.8 Hz"
                  }
                ][index];

                return (
                  <div key={index} className="border rounded-lg p-3 bg-gray-50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <Badge variant={mode.active ? "default" : "secondary"}>
                          {modeInfo.title}
                        </Badge>
                        <div className="text-sm font-medium text-blue-600">
                          {modeInfo.freq}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="text-sm w-12">{(mode.power * 100).toFixed(0)}%</span>
                        <Progress value={mode.power * 100} className="w-20" />
                      </div>
                    </div>
                    <div className="text-xs text-gray-600 mb-1">
                      <strong>Physics:</strong> {modeInfo.physics}
                    </div>
                    <div className="text-xs text-purple-600">
                      <strong>Symbolic:</strong> {modeInfo.symbolic}
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Live Harmonic Spectrogram */}
      <HarmonicSpectrogram />
    </div>
  );
};

export default SchumannAnalytics;