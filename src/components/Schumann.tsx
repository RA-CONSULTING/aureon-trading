import { useState, useEffect } from 'react';
import { toFixedSafe } from '@/utils/number';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { mapFrequencyToEmotion, analyze, EmotionState, ResonanceReport, EarthPacket, HumanPacket } from '@/lib/aureon';
import { EmotionSmoother } from '@/lib/aureon-smoothing';
import { NOTES } from '@/lib/aureon-data';
import ResonanceSpiral from './ResonanceSpiral';

export default function Schumann() {
  const [emotionState, setEmotionState] = useState<EmotionState>({
    fIn: 256,
    fNorm: 256,
    primary: 'C',
    weights: [],
    valence: 0.6,
    arousal: 0.25,
    color: '#FF0000',
    confidence: 0.7,
    tags: ['Safety', 'Belonging']
  });
  
  const [resonanceReport, setResonanceReport] = useState<ResonanceReport>({
    state: emotionState,
    gri: 50,
    alignment: 0.5,
    contributors: {
      freqAlign: 0.5,
      hrv: 0.6,
      alpha: 0.4,
      balance: 0.7,
      kp: 0.8,
      lightning: 0.9
    }
  });
  
  const [schumannBands, setSchumannBands] = useState([7.83, 14.3, 20.8, 27.3, 33.8]);
  const [isLive, setIsLive] = useState(true);

  // Simulate data generation
  const generateSimulatedData = () => {
    const earth: EarthPacket = {
      schumann: [
        7.83 + (Math.random() - 0.5) * 0.5,
        14.3 + (Math.random() - 0.5) * 1.0,
        20.8 + (Math.random() - 0.5) * 1.5,
        27.3 + (Math.random() - 0.5) * 2.0,
        33.8 + (Math.random() - 0.5) * 2.5
      ],
      kp: Math.floor(Math.random() * 9),
      lightningDensity: Math.random() * 100
    };

    const human: HumanPacket = {
      mainFreq: 0.08 + Math.random() * 0.04, // 0.08-0.12 Hz breathing
      rmssd: 20 + Math.random() * 80,
      hf: Math.random(),
      lf: Math.random(),
      alpha: Math.random()
    };

    const baseFreq = 8 + Math.random() * 32; // 8-40 Hz range
    return { earth, human, baseFreq };
  };

  useEffect(() => {
    if (!isLive) return;
    
    const interval = setInterval(() => {
      const { earth, human, baseFreq } = generateSimulatedData();
      
      // Analyze using new Aureon v1.0 system
      const report = analyze(baseFreq * 8, earth, human); // Scale to 256-512 range
      setEmotionState(report.state);
      setResonanceReport(report);
      
      // Update Schumann bands
      setSchumannBands(earth.schumann);
    }, 2000);

    return () => clearInterval(interval);
  }, [isLive]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-white mb-2">
            Aureon io • Total Resonance
          </h1>
          <p className="text-xl text-blue-200 mb-4">
            "All that is, all that was, all that shall be — unity in tandem"
          </p>
          <Badge 
            variant={isLive ? "default" : "secondary"}
            className="text-sm px-4 py-1"
          >
            {isLive ? "🔴 LIVE" : "⏸️ PAUSED"}
          </Badge>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          {/* Resonance Spiral */}
          <Card className="bg-black/20 backdrop-blur-sm border-white/20">
            <CardHeader>
              <CardTitle className="text-white text-center">Resonance Spiral</CardTitle>
            </CardHeader>
            <CardContent className="flex justify-center">
              <ResonanceSpiral 
                emotionState={emotionState}
                gri={resonanceReport.gri}
              />
            </CardContent>
          </Card>

          {/* Current State */}
          <Card className="bg-black/20 backdrop-blur-sm border-white/20">
            <CardHeader>
              <CardTitle className="text-white">Current Resonance State</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div 
                className="p-6 rounded-lg border-2 transition-all duration-500"
                style={{ 
                  backgroundColor: `${emotionState.color}20`,
                  borderColor: emotionState.color 
                }}
              >
                <h3 className="text-2xl font-bold text-white mb-2">
                  {emotionState.tags.join(' • ')}
                </h3>
                <p className="text-white/80 mb-4">
                  Note: {emotionState.primary} • {toFixedSafe(emotionState.fNorm, 1)} Hz
                </p>
                
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between text-sm text-white/70 mb-1">
                      <span>Valence (Positivity)</span>
                      <span>{toFixedSafe(emotionState.valence * 100, 0)}%</span>
                    </div>
                    <Progress value={emotionState.valence * 100} className="h-2" />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm text-white/70 mb-1">
                      <span>Arousal (Energy)</span>
                      <span>{toFixedSafe(emotionState.arousal * 100, 0)}%</span>
                    </div>
                    <Progress value={emotionState.arousal * 100} className="h-2" />
                  </div>
                  
                  <div>
                    <div className="flex justify-between text-sm text-white/70 mb-1">
                      <span>Confidence</span>
                      <span>{toFixedSafe(emotionState.confidence * 100, 0)}%</span>
                    </div>
                    <Progress value={emotionState.confidence * 100} className="h-2" />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="text-center p-4 bg-white/10 rounded-lg">
                  <div className="text-2xl font-bold text-white">
                    {Math.round(resonanceReport.gri)}
                  </div>
                  <div className="text-sm text-white/70">Global Resonance Index</div>
                </div>
                
                <div className="text-center p-4 bg-white/10 rounded-lg">
                  <div className="text-2xl font-bold text-white">
                    {toFixedSafe(resonanceReport.alignment * 100, 0)}%
                  </div>
                  <div className="text-sm text-white/70">Earth Alignment</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Schumann Resonance Bands */}
        <Card className="bg-black/20 backdrop-blur-sm border-white/20">
          <CardHeader>
            <CardTitle className="text-white">Schumann Resonance Bands</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
              {schumannBands.map((freq, index) => (
                <div key={index} className="text-center p-4 bg-white/10 rounded-lg">
                  <div className="text-xl font-bold text-white">
                    {toFixedSafe(freq, 2)}
                  </div>
                  <div className="text-sm text-white/70">
                    Band {index + 1} (Hz)
                  </div>
                  <div className="mt-2">
                    <Progress 
                      value={(freq / 40) * 100} 
                      className="h-2"
                    />
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}