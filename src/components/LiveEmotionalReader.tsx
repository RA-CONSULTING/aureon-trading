import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { toFixedSafe } from '@/utils/number';

interface EmotionalReading {
  timestamp: Date;
  frequency: number;
  valence: number;
  arousal: number;
  intensity: number;
  dominantEmotion: string;
  emotionalTags: string[];
  color: string;
  confidence: number;
}

const LiveEmotionalReader: React.FC = () => {
  const [isLive, setIsLive] = useState(false);
  const [currentReading, setCurrentReading] = useState<EmotionalReading>({
    timestamp: new Date(),
    frequency: 7.83,
    valence: 0.5,
    arousal: 0.5,
    intensity: 0.3,
    dominantEmotion: 'Neutral',
    emotionalTags: ['Balanced'],
    color: '#6366f1',
    confidence: 0.7
  });
  const [readingHistory, setReadingHistory] = useState<EmotionalReading[]>([]);

  // Emotional states mapping
  const emotionalStates = [
    { emotion: 'Joy', tags: ['Happy', 'Energetic', 'Positive'], color: '#22c55e', valence: 0.8, arousal: 0.7 },
    { emotion: 'Calm', tags: ['Peaceful', 'Relaxed', 'Centered'], color: '#3b82f6', valence: 0.7, arousal: 0.2 },
    { emotion: 'Excitement', tags: ['Thrilled', 'Animated', 'Eager'], color: '#f59e0b', valence: 0.9, arousal: 0.9 },
    { emotion: 'Anxiety', tags: ['Worried', 'Tense', 'Restless'], color: '#ef4444', valence: 0.2, arousal: 0.8 },
    { emotion: 'Sadness', tags: ['Melancholy', 'Down', 'Withdrawn'], color: '#6366f1', valence: 0.2, arousal: 0.3 },
    { emotion: 'Anger', tags: ['Frustrated', 'Irritated', 'Intense'], color: '#dc2626', valence: 0.1, arousal: 0.9 },
    { emotion: 'Love', tags: ['Compassionate', 'Connected', 'Warm'], color: '#ec4899', valence: 0.9, arousal: 0.5 },
    { emotion: 'Focus', tags: ['Concentrated', 'Alert', 'Clear'], color: '#8b5cf6', valence: 0.6, arousal: 0.6 }
  ];

  const generateLiveReading = (): EmotionalReading => {
    const baseFreq = 7.83 + (Math.random() - 0.5) * 2;
    const state = emotionalStates[Math.floor(Math.random() * emotionalStates.length)];
    
    const valenceNoise = (Math.random() - 0.5) * 0.3;
    const arousalNoise = (Math.random() - 0.5) * 0.3;
    
    return {
      timestamp: new Date(),
      frequency: baseFreq,
      valence: Math.max(0, Math.min(1, state.valence + valenceNoise)),
      arousal: Math.max(0, Math.min(1, state.arousal + arousalNoise)),
      intensity: 0.3 + Math.random() * 0.7,
      dominantEmotion: state.emotion,
      emotionalTags: state.tags,
      color: state.color,
      confidence: 0.6 + Math.random() * 0.4
    };
  };

  useEffect(() => {
    if (!isLive) return;

    const interval = setInterval(() => {
      const newReading = generateLiveReading();
      setCurrentReading(newReading);
      setReadingHistory(prev => [newReading, ...prev.slice(0, 19)]); // Keep last 20 readings
    }, 1500); // Update every 1.5 seconds

    return () => clearInterval(interval);
  }, [isLive]);

  const toggleLive = () => {
    setIsLive(!isLive);
  };

  const resetReadings = () => {
    setIsLive(false);
    setReadingHistory([]);
    setCurrentReading({
      timestamp: new Date(),
      frequency: 7.83,
      valence: 0.5,
      arousal: 0.5,
      intensity: 0.3,
      dominantEmotion: 'Neutral',
      emotionalTags: ['Balanced'],
      color: '#6366f1',
      confidence: 0.7
    });
  };

  return (
    <div className="space-y-6">
      {/* Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button onClick={toggleLive} className="flex items-center gap-2">
            {isLive ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            {isLive ? 'Pause Reading' : 'Start Live Reading'}
          </Button>
          <Button onClick={resetReadings} variant="outline" className="flex items-center gap-2">
            <RotateCcw className="w-4 h-4" />
            Reset
          </Button>
        </div>
        <Badge variant={isLive ? "default" : "secondary"} className="text-sm px-3 py-1">
          {isLive ? "🔴 LIVE" : "⏸️ PAUSED"}
        </Badge>
      </div>

      {/* Current Reading */}
      <Card className="bg-gradient-to-br from-white/10 to-white/5 backdrop-blur-md border-white/20 text-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div 
              className="w-6 h-6 rounded-full animate-pulse" 
              style={{ backgroundColor: currentReading.color }}
            />
            Live Emotional Reading
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="text-center">
            <div className="text-4xl font-bold mb-2 text-white drop-shadow-lg">
              {currentReading.dominantEmotion}
            </div>
            <div className="text-lg text-white/80 mb-4">
              {toFixedSafe(currentReading.frequency, 2)} Hz • {currentReading.timestamp.toLocaleTimeString()}
            </div>
            <div className="flex flex-wrap justify-center gap-2">
              {currentReading.emotionalTags.map((tag, index) => (
                <Badge 
                  key={index} 
                  variant="outline" 
                  className="text-white border-white/30"
                  style={{ 
                    backgroundColor: currentReading.color + '20',
                    borderColor: currentReading.color
                  }}
                >
                  {tag}
                </Badge>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">
                  <span>Valence (Positivity)</span>
                  <span>{toFixedSafe(currentReading.valence * 100, 0)}%</span>
                </div>
                <Progress 
                  value={currentReading.valence * 100} 
                  className="h-3"
                />
              </div>
              
              <div>
                <div className="flex justify-between text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">
                  <span>Arousal (Energy)</span>
                  <span>{toFixedSafe(currentReading.arousal * 100, 0)}%</span>
                </div>
                <Progress 
                  value={currentReading.arousal * 100} 
                  className="h-3"
                />
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">
                  <span>Intensity</span>
                  <span>{toFixedSafe(currentReading.intensity * 100, 0)}%</span>
                </div>
                <Progress 
                  value={currentReading.intensity * 100} 
                  className="h-3"
                />
              </div>
              
              <div>
                <div className="flex justify-between text-sm font-semibold text-gray-800 dark:text-gray-200 mb-2">
                  <span>Confidence</span>
                  <span>{toFixedSafe(currentReading.confidence * 100, 0)}%</span>
                </div>
                <Progress 
                  value={currentReading.confidence * 100} 
                  className="h-3"
                />
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Reading History */}
      {readingHistory.length > 0 && (
        <Card className="bg-white/10 backdrop-blur-md border-white/20 text-white">
          <CardHeader>
            <CardTitle>Recent Readings ({readingHistory.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {readingHistory.map((reading, index) => (
                <div 
                  key={index} 
                  className="flex items-center justify-between p-3 bg-white/5 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-3 h-3 rounded-full" 
                      style={{ backgroundColor: reading.color }}
                    />
                    <span className="font-medium">{reading.dominantEmotion}</span>
                    <span className="text-sm text-white/60">
                      {reading.timestamp.toLocaleTimeString()}
                    </span>
                  </div>
                  <div className="text-sm text-white/80">
                    V:{toFixedSafe(reading.valence, 1)} A:{toFixedSafe(reading.arousal, 1)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default LiveEmotionalReader;