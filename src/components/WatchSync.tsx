import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Heart, Activity, Zap, Watch } from 'lucide-react';
import { mapFrequencyToEmotion, EmotionState } from '@/lib/aureon';
import { toFixedSafe } from '@/utils/number';

interface BiometricData {
  heartRate: number;
  hrv: number;
  stressLevel: number;
  steps: number;
  timestamp: Date;
  resonanceCorrelation?: {
    frequency: number;
    note: string;
    emotions: string[];
    color: string;
    coherence: number;
  };
}

const WatchSync: React.FC = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [biometricData, setBiometricData] = useState<BiometricData | null>(null);
  const [syncHistory, setSyncHistory] = useState<BiometricData[]>([]);

  // Simulate Pixel watch data with Aureon correlation
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      // Simulate biometric data
      const heartRate = 60 + Math.random() * 40;
      const hrv = 20 + Math.random() * 60;
      const stressLevel = Math.random() * 100;
      const steps = Math.floor(Math.random() * 1000) + 5000;

      // Correlate HRV to frequency (simplified mapping)
      const correlatedFreq = 7.83 + (hrv - 50) * 0.05;
      const emotionState = mapFrequencyToEmotion(correlatedFreq * 32);
      const coherence = Math.max(0, Math.min(100, 100 - Math.abs(hrv - 50)));

      const newData: BiometricData = {
        heartRate,
        hrv,
        stressLevel,
        steps,
        timestamp: new Date(),
        resonanceCorrelation: {
          frequency: correlatedFreq,
          note: emotionState.note,
          emotions: emotionState.emotion,
          color: emotionState.color,
          coherence
        }
      };

      setBiometricData(newData);
      setSyncHistory(prev => [newData, ...prev.slice(0, 19)]);
    }, 3000);

    return () => clearInterval(interval);
  }, [isConnected]);

  const connectWatch = () => {
    setIsConnected(true);
    // Simulate initial connection data
    setBiometricData({
      heartRate: 72,
      hrv: 45,
      stressLevel: 35,
      steps: 6543,
      timestamp: new Date(),
      resonanceCorrelation: {
        frequency: 7.83,
        note: 'C',
        emotions: ['Safety', 'Grounding', 'Belonging'],
        color: '#FF0000',
        coherence: 78
      }
    });
  };

  const getStressColor = (level: number) => {
    if (level < 30) return 'bg-green-500';
    if (level < 60) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getCoherenceColor = (coherence: number) => {
    if (coherence > 70) return 'text-green-400';
    if (coherence > 40) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Watch className="w-5 h-5" />
            Pixel Watch Integration
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-gray-500'}`} />
              <span>{isConnected ? 'Connected' : 'Disconnected'}</span>
            </div>
            {!isConnected && (
              <Button onClick={connectWatch} variant="outline">
                Connect Watch
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Live Biometric Data */}
      {isConnected && biometricData && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Current Readings */}
          <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
            <CardHeader>
              <CardTitle>Live Biometrics</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Heart className="w-4 h-4 text-red-400" />
                  <span>Heart Rate</span>
                </div>
                <span className="text-lg font-semibold">{Math.round(biometricData.heartRate)} BPM</span>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-4 h-4 text-blue-400" />
                  <span>HRV</span>
                </div>
                <span className="text-lg font-semibold">{Math.round(biometricData.hrv)} ms</span>
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-400" />
                    <span>Stress Level</span>
                  </div>
                  <span className="text-lg font-semibold">{Math.round(biometricData.stressLevel)}%</span>
                </div>
                <Progress value={biometricData.stressLevel} className="h-2" />
              </div>

              <div className="flex items-center justify-between">
                <span>Steps Today</span>
                <span className="text-lg font-semibold">{biometricData.steps.toLocaleString()}</span>
              </div>
            </CardContent>
          </Card>

          {/* Resonance Correlation */}
          <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
            <CardHeader>
              <CardTitle>Aureon Correlation</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {biometricData.resonanceCorrelation && (
                <>
                  <div className="text-center p-4 rounded-lg" 
                    style={{ backgroundColor: biometricData.resonanceCorrelation.color + '20' }}>
                    <div className="text-2xl font-bold" 
                      style={{ color: biometricData.resonanceCorrelation.color }}>
                      {biometricData.resonanceCorrelation.note}
                    </div>
                    <div className="text-sm text-purple-200">
                      {toFixedSafe(biometricData?.resonanceCorrelation?.frequency, 2)} Hz
                    </div>
                  </div>

                  <div>
                    <div className="text-sm text-purple-200 mb-2">Emotional State</div>
                    <div className="flex flex-wrap gap-2">
                      {biometricData.resonanceCorrelation.emotions.map((emotion, idx) => (
                        <Badge key={idx} variant="outline" className="text-white border-white/30">
                          {emotion}
                        </Badge>
                      ))}
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span>Coherence</span>
                      <span className={`text-lg font-semibold ${getCoherenceColor(biometricData.resonanceCorrelation.coherence)}`}>
                        {Math.round(biometricData.resonanceCorrelation.coherence)}%
                      </span>
                    </div>
                    <Progress value={biometricData.resonanceCorrelation.coherence} className="h-2" />
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sync History */}
      {syncHistory.length > 0 && (
        <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
          <CardHeader>
            <CardTitle>Recent Sync History</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {syncHistory.slice(0, 10).map((entry, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-white/5 rounded-lg">
                  <div className="flex items-center gap-4">
                    <div className="text-sm text-purple-200">
                      {entry.timestamp.toLocaleTimeString()}
                    </div>
                    <div className="flex items-center gap-2">
                      <Heart className="w-3 h-3 text-red-400" />
                      <span className="text-sm">{Math.round(entry.heartRate)}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <Activity className="w-3 h-3 text-blue-400" />
                      <span className="text-sm">{Math.round(entry.hrv)}</span>
                    </div>
                  </div>
                  {entry.resonanceCorrelation && (
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: entry.resonanceCorrelation.color }}
                      />
                      <span className="text-sm">{entry.resonanceCorrelation.note}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default WatchSync;