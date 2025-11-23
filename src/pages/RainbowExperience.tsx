import { useState, useEffect, useRef } from 'react';
import Navbar from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Slider } from '@/components/ui/slider';
import { Play, Pause, Volume2, VolumeX, Sparkles } from 'lucide-react';
import { RainbowBridge } from '@/core/rainbowBridge';
import { Prism } from '@/core/prism';

const RainbowExperience = () => {
  const [lambda, setLambda] = useState(0.5);
  const [coherence, setCoherence] = useState(0.75);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.3);
  
  const rainbowRef = useRef(new RainbowBridge());
  const prismRef = useRef(new Prism());
  const audioContextRef = useRef<AudioContext | null>(null);
  const oscillatorRef = useRef<OscillatorNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);

  const rainbowState = rainbowRef.current.map(lambda, coherence);
  const prismOutput = prismRef.current.transform(lambda, coherence, rainbowState.frequency);

  // Frequency spectrum visualization
  const frequencySpectrum = [
    { freq: 110, label: 'Fear', color: 'from-red-500 to-red-600', emotion: 'FEAR' },
    { freq: 174, label: 'Releasing', color: 'from-orange-500 to-orange-600', emotion: 'RELEASING' },
    { freq: 285, label: 'Healing', color: 'from-yellow-500 to-yellow-600', emotion: 'HEALING' },
    { freq: 396, label: 'Liberation', color: 'from-green-500 to-green-600', emotion: 'LIBERATION' },
    { freq: 417, label: 'Change', color: 'from-cyan-500 to-cyan-600', emotion: 'CHANGE' },
    { freq: 528, label: 'LOVE', color: 'from-emerald-500 to-emerald-600', emotion: 'LOVE' },
    { freq: 639, label: 'Connection', color: 'from-blue-500 to-blue-600', emotion: 'CONNECTION' },
    { freq: 741, label: 'Expression', color: 'from-indigo-500 to-indigo-600', emotion: 'EXPRESSION' },
    { freq: 852, label: 'Intuition', color: 'from-violet-500 to-violet-600', emotion: 'INTUITION' },
    { freq: 963, label: 'Unity', color: 'from-purple-500 to-purple-600', emotion: 'UNITY' },
  ];

  const getClosestFrequency = (freq: number) => {
    return frequencySpectrum.reduce((prev, curr) => 
      Math.abs(curr.freq - freq) < Math.abs(prev.freq - freq) ? curr : prev
    );
  };

  const currentFreq = getClosestFrequency(rainbowState.frequency);

  // Audio synthesis
  useEffect(() => {
    if (typeof window !== 'undefined') {
      audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
      gainNodeRef.current = audioContextRef.current.createGain();
      gainNodeRef.current.connect(audioContextRef.current.destination);
      gainNodeRef.current.gain.value = isMuted ? 0 : volume;
    }

    return () => {
      if (oscillatorRef.current) {
        oscillatorRef.current.stop();
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = isMuted ? 0 : volume;
    }
  }, [volume, isMuted]);

  const playFrequency = () => {
    if (!audioContextRef.current || !gainNodeRef.current) return;

    if (oscillatorRef.current) {
      oscillatorRef.current.stop();
    }

    oscillatorRef.current = audioContextRef.current.createOscillator();
    oscillatorRef.current.type = 'sine';
    oscillatorRef.current.frequency.value = rainbowState.frequency;
    oscillatorRef.current.connect(gainNodeRef.current);
    oscillatorRef.current.start();
    setIsPlaying(true);
  };

  const stopFrequency = () => {
    if (oscillatorRef.current) {
      oscillatorRef.current.stop();
      oscillatorRef.current = null;
    }
    setIsPlaying(false);
  };

  const togglePlay = () => {
    if (isPlaying) {
      stopFrequency();
    } else {
      playFrequency();
    }
  };

  useEffect(() => {
    if (isPlaying && oscillatorRef.current) {
      oscillatorRef.current.frequency.value = rainbowState.frequency;
    }
  }, [rainbowState.frequency, isPlaying]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      
      <main className="container mx-auto px-4 pt-24 pb-12">
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Header */}
          <div className="text-center space-y-4">
            <div className="flex items-center justify-center gap-3">
              <Sparkles className="h-12 w-12 text-primary animate-pulse" />
              <h1 className="text-5xl font-bold bg-gradient-primary bg-clip-text text-transparent">
                Rainbow Bridge Experience
              </h1>
              <Sparkles className="h-12 w-12 text-primary animate-pulse" />
            </div>
            <p className="text-xl text-muted-foreground">
              Taste the quantum frequencies from FEAR to UNITY
            </p>
            <Badge variant="outline" className="text-lg px-4 py-2">
              528 Hz = LOVE 💚
            </Badge>
          </div>

          {/* Current State Display */}
          <Card className="bg-gradient-to-br from-primary/5 to-accent/5 border-2 border-primary/20">
            <CardHeader>
              <CardTitle className="text-center text-2xl">Current Frequency State</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="text-center space-y-2">
                <div className={`inline-block px-8 py-4 rounded-lg bg-gradient-to-r ${currentFreq.color} text-white font-bold text-4xl shadow-glow`}>
                  {rainbowState.frequency.toFixed(2)} Hz
                </div>
                <div className="text-2xl font-semibold">{currentFreq.emotion}</div>
                <Badge variant="secondary" className="text-lg">
                  Phase: {rainbowState.phase}
                </Badge>
              </div>

              {/* Audio Controls */}
              <div className="flex items-center justify-center gap-4">
                <Button
                  size="lg"
                  onClick={togglePlay}
                  className="gap-2"
                >
                  {isPlaying ? <Pause className="h-5 w-5" /> : <Play className="h-5 w-5" />}
                  {isPlaying ? 'Stop Frequency' : 'Play Frequency'}
                </Button>
                
                <Button
                  size="lg"
                  variant="outline"
                  onClick={() => setIsMuted(!isMuted)}
                >
                  {isMuted ? <VolumeX className="h-5 w-5" /> : <Volume2 className="h-5 w-5" />}
                </Button>

                <div className="w-32">
                  <Slider
                    value={[volume * 100]}
                    onValueChange={(v) => setVolume(v[0] / 100)}
                    max={100}
                    step={1}
                    disabled={isMuted}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Controls */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Lambda (Λ) - Field Strength</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-3xl font-bold text-center text-primary">
                  {lambda.toFixed(3)}
                </div>
                <Slider
                  value={[lambda * 100]}
                  onValueChange={(v) => setLambda(v[0] / 100)}
                  max={100}
                  step={1}
                  className="w-full"
                />
                <p className="text-sm text-muted-foreground text-center">
                  Controls the base frequency mapping
                </p>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Coherence (Γ) - Alignment</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-3xl font-bold text-center text-primary">
                  {coherence.toFixed(3)}
                </div>
                <Slider
                  value={[coherence * 100]}
                  onValueChange={(v) => setCoherence(v[0] / 100)}
                  max={100}
                  step={1}
                  className="w-full"
                />
                <p className="text-sm text-muted-foreground text-center">
                  Higher coherence → closer to 528 Hz LOVE
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Frequency Spectrum */}
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Frequency Spectrum: 110 - 963+ Hz</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {frequencySpectrum.map((item) => {
                  const isActive = Math.abs(rainbowState.frequency - item.freq) < 50;
                  return (
                    <div
                      key={item.freq}
                      className={`relative p-4 rounded-lg border-2 transition-all duration-300 ${
                        isActive 
                          ? 'border-primary shadow-glow scale-105' 
                          : 'border-border/50 opacity-60'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className={`w-12 h-12 rounded-full bg-gradient-to-r ${item.color} flex items-center justify-center text-white font-bold shadow-lg`}>
                            {item.freq}
                          </div>
                          <div>
                            <div className="font-bold text-lg">{item.emotion}</div>
                            <div className="text-sm text-muted-foreground">{item.freq} Hz</div>
                          </div>
                        </div>
                        {isActive && (
                          <Badge className="animate-pulse">Active</Badge>
                        )}
                      </div>
                      {isActive && (
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary to-accent rounded-t-lg"></div>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>

          {/* Prism Transformation */}
          <Card className="bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-2 border-purple-500/20">
            <CardHeader>
              <CardTitle className="text-center text-2xl">
                💎 Prism Transformation
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="text-center space-y-2">
                <div className="text-3xl font-bold text-primary">
                  Level {prismOutput.level} / 5
                </div>
                <Badge variant="outline" className="text-lg">
                  {prismOutput.state}
                </Badge>
              </div>
              
              <div className="space-y-2">
                <div className="flex justify-between text-sm mb-1">
                  <span>Transformation Progress</span>
                  <span>{((prismOutput.level / 5) * 100).toFixed(0)}%</span>
                </div>
                <div className="w-full h-4 bg-secondary rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-500 to-pink-500 transition-all duration-500"
                    style={{ width: `${(prismOutput.level / 5) * 100}%` }}
                  />
                </div>
              </div>

              <div className="text-center text-sm text-muted-foreground">
                {coherence >= 0.9 ? (
                  <div className="text-green-500 font-semibold text-lg">
                    🎯 Prism locked to 528 Hz LOVE frequency!
                  </div>
                ) : (
                  <div>
                    Increase coherence to 0.9+ to lock to 528 Hz
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Quick Presets */}
          <Card>
            <CardHeader>
              <CardTitle className="text-center">Quick Frequency Presets</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {frequencySpectrum.slice(0, 5).map((item) => (
                  <Button
                    key={item.freq}
                    variant="outline"
                    className="h-auto py-4 flex-col gap-2"
                    onClick={() => {
                      // Calculate approximate lambda/coherence for this frequency
                      const targetLambda = (item.freq - 110) / (963 - 110);
                      const targetCoherence = item.freq === 528 ? 0.95 : 0.7;
                      setLambda(targetLambda);
                      setCoherence(targetCoherence);
                    }}
                  >
                    <div className={`w-8 h-8 rounded-full bg-gradient-to-r ${item.color}`}></div>
                    <div className="font-semibold">{item.emotion}</div>
                    <div className="text-xs text-muted-foreground">{item.freq} Hz</div>
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default RainbowExperience;
