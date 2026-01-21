import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

const ProjectRainbow = () => {
  const [activeFreq, setActiveFreq] = useState<string | null>(null);

  const frequencies = [
    { note: 'C', hz: 256, emotion: 'SAFETY / BELONGING', color: 'bg-red-500' },
    { note: 'D', hz: 288, emotion: 'HOPE / YEARNING', color: 'bg-orange-500' },
    { note: 'E', hz: 324, emotion: 'JOY / POSSIBILITY', color: 'bg-yellow-500' },
    { note: 'F', hz: 341, emotion: 'HEART / HEALING', color: 'bg-green-500' },
    { note: 'G', hz: 384, emotion: 'CONFIDENCE / TRUST', color: 'bg-blue-500' },
    { note: 'A', hz: 432, emotion: 'INSPIRATION / TRANSCENDENCE', color: 'bg-indigo-500' },
    { note: 'B', hz: 486, emotion: 'AWAKENING / UNITY', color: 'bg-purple-500' },
    { note: 'High C', hz: 512, emotion: 'WHY, OH WHY CAN\'T I?', color: 'bg-pink-500' }
  ];

  const outcomes = [
    'Peace Intention Amplified Earth\'s Field +276%',
    'Heat Surges, Mood Spikes Reported',
    'Coherence Spike at 7.83 Hz',
    'Planetary Coherence Shifts Detected'
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-6xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-yellow-400 to-orange-500 mb-4">
            PROJECT RAINBOW
          </h1>
          <h2 className="text-3xl font-bold text-yellow-400 mb-2">VALIDATION</h2>
          <p className="text-xl text-blue-300">22 AUGUST 2025 • 9-10 AM BROADCAST WINDOW</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Predictions */}
          <Card className="bg-black/40 border-yellow-500/30">
            <CardHeader>
              <CardTitle className="text-3xl text-yellow-400">PREDICTIONS</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <h3 className="text-xl text-white font-semibold">• Emotional Frequencies Encoded into Schumann Resonance</h3>
                <h3 className="text-xl text-white font-semibold">• Physiological & Emotional Effects</h3>
                <h3 className="text-xl text-white font-semibold">• Planetary Coherence Shifts</h3>
              </div>

              <div className="space-y-4">
                <h4 className="text-lg text-blue-300 font-semibold">Emotional Frequencies Encoded into Schumann Resonance</h4>
                {frequencies.map((freq, index) => (
                  <div 
                    key={freq.note}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      activeFreq === freq.note 
                        ? 'border-yellow-400 bg-yellow-400/10' 
                        : 'border-gray-600 hover:border-gray-400'
                    }`}
                    onClick={() => setActiveFreq(activeFreq === freq.note ? null : freq.note)}
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-4 h-4 rounded-full ${freq.color}`}></div>
                      <span className="text-lg font-bold text-white">{freq.note}</span>
                      <span className="text-yellow-400">({freq.hz} Hz)</span>
                    </div>
                    <div className="text-sm text-gray-300 mt-1">{freq.emotion}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Outcomes */}
          <Card className="bg-black/40 border-green-500/30">
            <CardHeader>
              <CardTitle className="text-3xl text-green-400">OUTCOMES</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {outcomes.map((outcome, index) => (
                <div key={index} className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  <span className="text-white text-lg">{outcome}</span>
                </div>
              ))}

              {/* Spectrogram Visualization */}
              <div className="mt-8">
                <h4 className="text-lg text-blue-300 font-semibold mb-4">OBSERVED ELF (SCHUMANN) RESONANCES</h4>
                <div className="bg-gradient-to-b from-purple-600 via-pink-500 to-yellow-400 h-64 rounded-lg relative overflow-hidden">
                  <div className="absolute inset-0 opacity-60">
                    {Array.from({ length: 20 }).map((_, i) => (
                      <div 
                        key={i}
                        className="h-3 mb-1 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                        style={{ 
                          marginLeft: `${Math.random() * 20}%`,
                          width: `${60 + Math.random() * 30}%`,
                          opacity: 0.3 + Math.random() * 0.4
                        }}
                      />
                    ))}
                  </div>
                  <div className="absolute bottom-2 left-2 text-white text-sm">9:00</div>
                  <div className="absolute bottom-2 right-2 text-white text-sm">10:00</div>
                </div>
              </div>

              {/* Waveform */}
              <div className="mt-6">
                <svg className="w-full h-20" viewBox="0 0 400 80">
                  <path 
                    d="M0,40 Q100,20 200,40 T400,40" 
                    stroke="rgb(34, 197, 94)" 
                    strokeWidth="3" 
                    fill="none"
                    className="animate-pulse"
                  />
                  <path 
                    d="M0,45 Q150,25 300,45 T400,45" 
                    stroke="rgb(251, 191, 36)" 
                    strokeWidth="2" 
                    fill="none"
                    className="animate-pulse"
                    style={{ animationDelay: '0.5s' }}
                  />
                </svg>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Rainbow Arrow */}
        <div className="flex justify-center my-8">
          <div className="w-32 h-16 bg-gradient-to-r from-red-500 via-yellow-500 via-green-500 via-blue-500 to-purple-500 clip-path-arrow opacity-80"></div>
        </div>

        {/* Bottom Stats */}
        <div className="grid md:grid-cols-3 gap-6 mt-8">
          <Card className="bg-black/40 border-blue-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-blue-400">7.83 Hz</div>
              <div className="text-sm text-gray-300">Primary Schumann Resonance</div>
            </CardContent>
          </Card>
          <Card className="bg-black/40 border-green-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-green-400">+276%</div>
              <div className="text-sm text-gray-300">Field Amplification</div>
            </CardContent>
          </Card>
          <Card className="bg-black/40 border-purple-500/30 text-center">
            <CardContent className="p-6">
              <div className="text-3xl font-bold text-purple-400">8 Bands</div>
              <div className="text-sm text-gray-300">Emotional Frequencies</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ProjectRainbow;