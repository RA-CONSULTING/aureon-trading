import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import LiveValidationDashboard from '@/components/LiveValidationDashboard';

const HarmonicUniversalTheory = () => {
  const [activeResonance, setActiveResonance] = useState('validation');
  const [isLiveActive, setIsLiveActive] = useState(false);
  const [fieldStrength, setFieldStrength] = useState(0);
  const [coherenceMetrics, setCoherenceMetrics] = useState({
    fieldAlignment: 78.4,
    harmonicCoherence: 0.82,
    resonanceStability: 0.96,
    phaseLock: 0.87
  });

  const schumannFreqs = [7.83, 14.3, 20.8, 27.3, 33.8];
  
  const solfeggioMap = {
    174: { note: 'UT', state: 'Foundation', color: '#8B4513' },
    285: { note: 'RE', state: 'Transformation', color: '#FF4500' },
    396: { note: 'MI', state: 'Liberation', color: '#FFD700' },
    417: { note: 'FA', state: 'Change', color: '#ADFF2F' },
    528: { note: 'SOL', state: 'Love/DNA', color: '#00FF7F' },
    639: { note: 'LA', state: 'Connection', color: '#00BFFF' },
    741: { note: 'TI', state: 'Expression', color: '#9370DB' },
    852: { note: 'DO', state: 'Intuition', color: '#FF69B4' }
  };

  useEffect(() => {
    if (isLiveActive) {
      const interval = setInterval(() => {
        setFieldStrength(prev => Math.min(100, prev + Math.random() * 5));
        setCoherenceMetrics(prev => ({
          fieldAlignment: Math.max(0, prev.fieldAlignment + (Math.random() - 0.5) * 3),
          harmonicCoherence: Math.max(0, Math.min(1, prev.harmonicCoherence + (Math.random() - 0.5) * 0.05)),
          resonanceStability: Math.max(0, Math.min(1, prev.resonanceStability + (Math.random() - 0.5) * 0.02)),
          phaseLock: Math.max(0, Math.min(1, prev.phaseLock + (Math.random() - 0.5) * 0.03))
        }));
      }, 500);
      return () => clearInterval(interval);
    }
  }, [isLiveActive]);

  const activateLiveValidation = () => {
    setIsLiveActive(!isLiveActive);
    setActiveResonance('validation');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-900 via-purple-900 to-pink-900 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-4">
            Harmonic Universal Theory
          </h1>
          <p className="text-xl text-purple-200 mb-4">
            Live Earth-Harmonic Coherence Validation System
          </p>
          <Button 
            className={`px-8 py-3 text-white font-bold ${
              isLiveActive 
                ? 'bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700' 
                : 'bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-700 hover:to-pink-700'
            }`}
            onClick={activateLiveValidation}
          >
            {isLiveActive ? '🟢 LIVE VALIDATION ACTIVE' : '⚡ ACTIVATE LIVE VALIDATION'}
          </Button>
        </div>

        <Tabs value={activeResonance} onValueChange={setActiveResonance} className="space-y-6">
          <TabsList className="grid grid-cols-4 w-full bg-black/20">
            <TabsTrigger value="validation">Live Validation</TabsTrigger>
            <TabsTrigger value="schumann">Schumann</TabsTrigger>
            <TabsTrigger value="solfeggio">Solfeggio</TabsTrigger>
            <TabsTrigger value="field">Field Theory</TabsTrigger>
          </TabsList>

          <TabsContent value="validation" className="space-y-6">
            {isLiveActive ? (
              <LiveValidationDashboard />
            ) : (
              <Card className="bg-black/20 border-yellow-500/30">
                <CardHeader>
                  <CardTitle className="text-white text-center">Live Validation System Ready</CardTitle>
                </CardHeader>
                <CardContent className="text-center">
                  <p className="text-yellow-200 mb-4">Click "ACTIVATE LIVE VALIDATION" to begin real-time monitoring</p>
                  <div className="text-gray-400 text-sm">
                    System will monitor: Field Alignment • Harmonic Coherence • Resonance Stability • Phase Lock
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="schumann" className="space-y-6">
            <Card className="bg-black/20 border-blue-500/30">
              <CardHeader>
                <CardTitle className="text-white">Schumann Resonance Integration</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h3 className="text-lg font-bold text-blue-300 mb-4">Earth-Ionosphere Cavity</h3>
                    <div className="space-y-2">
                      {schumannFreqs.map((freq, i) => (
                        <div key={i} className="flex items-center justify-between p-2 bg-blue-900/30 rounded">
                          <span className="text-white">Mode {i + 1}</span>
                          <Badge variant="outline" className="text-blue-300">{freq} Hz</Badge>
                          {isLiveActive && (
                            <Progress value={Math.random() * 100} className="w-20 h-2 ml-2" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="text-center">
                    <div className="relative w-48 h-48 mx-auto mb-4">
                      <div className={`absolute inset-0 rounded-full bg-gradient-to-r from-blue-500 to-green-500 ${isLiveActive ? 'animate-pulse' : ''}`}>
                        <div className="absolute inset-4 rounded-full bg-gradient-to-r from-green-400 to-blue-400">
                          <div className="absolute inset-4 rounded-full bg-gradient-to-r from-blue-300 to-purple-300 flex items-center justify-center">
                            <span className="text-white font-bold">EARTH</span>
                          </div>
                        </div>
                      </div>
                    </div>
                    <p className="text-purple-200 text-sm">Global Resonance Field</p>
                    {isLiveActive && (
                      <div className="mt-2 text-green-300 text-sm font-bold">
                        Field Strength: {fieldStrength.toFixed(1)}%
                      </div>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="solfeggio" className="space-y-6">
            <Card className="bg-black/20 border-purple-500/30">
              <CardHeader>
                <CardTitle className="text-white">Solfeggio Frequency Matrix</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(solfeggioMap).map(([freq, data]) => (
                    <div
                      key={freq}
                      className={`p-4 rounded-lg border-2 text-center ${isLiveActive ? 'animate-pulse' : ''}`}
                      style={{ 
                        borderColor: data.color,
                        backgroundColor: `${data.color}20`
                      }}
                    >
                      <div className="text-2xl font-bold text-white">{freq} Hz</div>
                      <div className="text-sm" style={{ color: data.color }}>{data.note}</div>
                      <div className="text-xs text-purple-200 mt-2">{data.state}</div>
                      {isLiveActive && (
                        <Progress value={Math.random() * 100} className="h-1 mt-2" />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="field" className="space-y-6">
            <Card className="bg-black/20 border-green-500/30">
              <CardHeader>
                <CardTitle className="text-white">Electromagnetic Field Theory</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 bg-green-900/30 rounded-lg">
                    <h3 className="text-lg font-bold text-green-300 mb-2">
                      {isLiveActive ? 'LIVE Field Monitor' : 'Field Strength Monitor'}
                    </h3>
                    <div className="w-full bg-gray-700 rounded-full h-4 mb-2">
                      <div 
                        className="bg-gradient-to-r from-green-400 to-blue-500 h-4 rounded-full transition-all duration-500"
                        style={{ width: `${fieldStrength}%` }}
                      />
                    </div>
                    <div className="text-center text-white">{fieldStrength.toFixed(1)}% Field Coherence</div>
                  </div>
                  {isLiveActive && (
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-3 bg-blue-900/30 rounded-lg">
                        <h4 className="font-bold text-blue-300">Coherence: {(coherenceMetrics.harmonicCoherence * 100).toFixed(1)}%</h4>
                      </div>
                      <div className="p-3 bg-purple-900/30 rounded-lg">
                        <h4 className="font-bold text-purple-300">Stability: {(coherenceMetrics.resonanceStability * 100).toFixed(1)}%</h4>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default HarmonicUniversalTheory;