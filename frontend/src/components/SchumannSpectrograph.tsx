import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Radio, Waves, Heart, Zap } from "lucide-react";
import { useSchumannResonance } from "@/hooks/useSchumannResonance";
import { RainbowBridge, type EmotionalPhase } from "@/core/rainbowBridge";
import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from "recharts";

const rainbowBridge = new RainbowBridge();

export function SchumannSpectrograph() {
  const { schumannData, isConnected } = useSchumannResonance();
  const [emotionalMappings, setEmotionalMappings] = useState<Array<{
    harmonic: string;
    frequency: number;
    amplitude: number;
    emotionalPhase: EmotionalPhase;
    emotionalFrequency: number;
    intensity: number;
  }>>([]);

  useEffect(() => {
    if (schumannData) {
      // Map each harmonic to emotional frequency
      const mappings = schumannData.harmonics.map(harmonic => {
        const lambda = harmonic.frequency / 100; // Normalize for Rainbow Bridge
        const coherence = harmonic.amplitude;
        const rainbowState = rainbowBridge.map(lambda, coherence);
        
        return {
          harmonic: harmonic.name,
          frequency: harmonic.frequency,
          amplitude: harmonic.amplitude,
          emotionalPhase: rainbowState.phase,
          emotionalFrequency: rainbowState.frequency,
          intensity: rainbowState.intensity,
        };
      });
      
      setEmotionalMappings(mappings);
    }
  }, [schumannData]);

  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'peak': return 'hsl(var(--chart-1))';
      case 'elevated': return 'hsl(var(--chart-2))';
      case 'stable': return 'hsl(var(--chart-3))';
      case 'disturbed': return 'hsl(var(--chart-5))';
      default: return 'hsl(var(--muted))';
    }
  };

  const getEmotionalColor = (phase: EmotionalPhase) => {
    const colors: Record<EmotionalPhase, string> = {
      FEAR: 'hsl(0, 70%, 45%)',
      FORMING: 'hsl(15, 85%, 60%)',
      LOVE: 'hsl(150, 100%, 50%)',
      AWE: 'hsl(220, 80%, 60%)',
      UNITY: 'hsl(270, 65%, 65%)',
    };
    return colors[phase];
  };

  if (!isConnected || !schumannData) {
    return (
      <Card className="bg-card/50 backdrop-blur border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-muted-foreground animate-pulse" />
            Schumann Spectrograph
          </CardTitle>
          <CardDescription>Connecting to Earth's electromagnetic field...</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Prepare spectrograph data
  const spectrographData = schumannData.spectrumHistory.map((spectrum, idx) => ({
    time: idx,
    ...Object.fromEntries(
      schumannData.harmonics.map((h, i) => [h.name, spectrum[i] || 0])
    )
  }));

  // Prepare harmonic chart data
  const harmonicData = schumannData.harmonics.map(h => ({
    name: h.name,
    frequency: h.frequency,
    amplitude: h.amplitude * 100,
  }));

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50 relative overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-chart-2/5 to-chart-3/5" />
      
      <CardHeader className="relative">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Radio className="w-5 h-5 text-primary" />
              Schumann Resonance Spectrograph
            </CardTitle>
            <CardDescription>
              Live Harmonic Analysis & Emotional Frequency Mapping
            </CardDescription>
          </div>
          <div className="flex gap-2">
            <Badge 
              className="text-white"
              style={{ backgroundColor: getPhaseColor(schumannData.resonancePhase) }}
            >
              {schumannData.resonancePhase.toUpperCase()}
            </Badge>
            <Badge variant="outline" className="flex items-center gap-1">
              <Waves className="w-3 h-3" />
              {schumannData.fundamentalHz.toFixed(2)} Hz
            </Badge>
          </div>
        </div>
      </CardHeader>

      <CardContent className="relative space-y-6">
        {/* Real-time Spectrograph */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-chart-1" />
            <h3 className="text-sm font-semibold">Live Spectrograph</h3>
          </div>
          <div className="h-48 bg-background/30 rounded-lg border border-border/50 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={spectrographData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis 
                  dataKey="time" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={10}
                  hide
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={10}
                  domain={[0, 1.5]}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                {schumannData.harmonics.map((harmonic, idx) => (
                  <Area
                    key={harmonic.name}
                    type="monotone"
                    dataKey={harmonic.name}
                    stackId="1"
                    stroke={`hsl(var(--chart-${(idx % 5) + 1}))`}
                    fill={`hsl(var(--chart-${(idx % 5) + 1}))`}
                    fillOpacity={0.6}
                  />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Harmonic Spectrum */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Waves className="w-4 h-4 text-chart-2" />
            <h3 className="text-sm font-semibold">Harmonic Spectrum</h3>
          </div>
          <div className="h-40 bg-background/30 rounded-lg border border-border/50 p-2">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={harmonicData}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
                <XAxis 
                  dataKey="frequency" 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={10}
                  label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5, fontSize: 10 }}
                />
                <YAxis 
                  stroke="hsl(var(--muted-foreground))"
                  fontSize={10}
                  label={{ value: 'Amplitude %', angle: -90, position: 'insideLeft', fontSize: 10 }}
                />
                <Tooltip 
                  contentStyle={{
                    backgroundColor: 'hsl(var(--popover))',
                    border: '1px solid hsl(var(--border))',
                    borderRadius: '8px',
                  }}
                />
                <Line 
                  type="monotone" 
                  dataKey="amplitude" 
                  stroke="hsl(var(--chart-2))" 
                  strokeWidth={2}
                  dot={{ fill: 'hsl(var(--chart-2))', r: 4 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Emotional Tone Mapping */}
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <Heart className="w-4 h-4 text-chart-3" />
            <h3 className="text-sm font-semibold">Emotional Frequency Mapping</h3>
          </div>
          <div className="grid gap-2">
            {emotionalMappings.map((mapping, idx) => (
              <div 
                key={idx}
                className="p-3 bg-background/30 rounded-lg border border-border/50 hover:bg-background/50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div 
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: getEmotionalColor(mapping.emotionalPhase) }}
                    />
                    <span className="text-sm font-medium">{mapping.harmonic}</span>
                    <Badge variant="outline" className="text-xs">
                      {mapping.frequency.toFixed(1)} Hz
                    </Badge>
                  </div>
                  <Badge 
                    className="text-xs"
                    style={{ 
                      backgroundColor: getEmotionalColor(mapping.emotionalPhase),
                      color: 'white'
                    }}
                  >
                    {mapping.emotionalPhase}
                  </Badge>
                </div>
                <div className="flex items-center gap-4 text-xs text-muted-foreground">
                  <span>Emotional: {mapping.emotionalFrequency} Hz</span>
                  <span>Intensity: {(mapping.intensity * 100).toFixed(0)}%</span>
                  <span>Amplitude: {(mapping.amplitude * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Emotional Phase Legend */}
        <div className="p-3 bg-background/20 rounded-lg border border-border/30">
          <div className="text-xs font-semibold mb-2 text-muted-foreground">Emotional Phases</div>
          <div className="grid grid-cols-5 gap-2">
            {(['FEAR', 'FORMING', 'LOVE', 'AWE', 'UNITY'] as EmotionalPhase[]).map(phase => (
              <div key={phase} className="flex items-center gap-1">
                <div 
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: getEmotionalColor(phase) }}
                />
                <span className="text-xs">{phase}</span>
              </div>
            ))}
          </div>
          <div className="text-xs text-muted-foreground mt-2">
            110 Hz (Fear) → 528 Hz (Love) → 963 Hz (Unity)
          </div>
        </div>

        {/* Real-time Insights */}
        {schumannData.resonancePhase === 'peak' && (
          <div className="p-3 bg-primary/10 border border-primary/30 rounded-lg">
            <div className="flex items-center gap-2 text-sm text-primary">
              <Zap className="w-4 h-4" />
              <span className="font-semibold">Peak Resonance Active</span>
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              Earth's field is in high coherence. Enhanced unity frequencies detected.
            </p>
          </div>
        )}

        <div className="text-xs text-muted-foreground text-center pt-2 border-t border-border/30">
          Last Update: {schumannData.timestamp.toLocaleTimeString()} • 
          Coherence Boost: +{(schumannData.coherenceBoost * 100).toFixed(1)}%
        </div>
      </CardContent>
    </Card>
  );
}
