import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { ZeroPointFieldDetector, ZeroPointFieldState } from '@/core/zeroPointFieldDetector';
import { Activity, Radio } from 'lucide-react';
import sentinelSealImage from '@/assets/research/sentinel-seal-spectrogram.png';
import sealEarthResonances from '@/assets/research/seal-earth-resonances.png';
import sealHarmonicsTensor from '@/assets/research/seal-harmonics-tensorfield.png';
import familyResonanceWave from '@/assets/research/family-resonance-wave.png';

interface SentinelSealSpectrogramProps {
  marketFrequency: number;
  coherence: number;
  phaseAlignment: number;
  schumannFrequency: number;
}

export const SentinelSealSpectrogram = ({
  marketFrequency,
  coherence,
  phaseAlignment,
  schumannFrequency
}: SentinelSealSpectrogramProps) => {
  const [detector] = useState(() => new ZeroPointFieldDetector('02111991', 'GARY LECKEY'));
  const [fieldState, setFieldState] = useState<ZeroPointFieldState | null>(null);
  const [spectrumData, setSpectrumData] = useState<any[]>([]);

  useEffect(() => {
    const updateField = () => {
      const timestamp = Date.now();
      const state = detector.detectFieldHarmonics(
        marketFrequency,
        coherence,
        phaseAlignment,
        schumannFrequency,
        timestamp
      );
      setFieldState(state);

      // Generate spectrum data for visualization
      const spectrum: any[] = [];
      const frequencyRange = [100, 150, 200, 250, 300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800, 850, 900, 950, 1000];
      
      frequencyRange.forEach(freq => {
        let amplitude = 0;
        
        // Check seal harmonics
        state.sealHarmonics.forEach(seal => {
          const distance = Math.abs(freq - seal.frequency);
          if (distance < 50) {
            const sealAmplitude = (1 - distance / 50) * (state.activeSeal?.frequency === seal.frequency ? 1 : 0.3);
            amplitude += sealAmplitude * coherence;
          }
        });

        // Check family resonances
        state.familyResonances.forEach(member => {
          const distance = Math.abs(freq - member.frequency);
          if (distance < 40) {
            const familyAmplitude = (1 - distance / 40) * member.amplitude * 0.7;
            amplitude += familyAmplitude * state.familyUnityWave;
          }
        });

        // Add composite echo signal influence
        amplitude += Math.abs(state.compositeEchoSignal) * Math.exp(-Math.abs(freq - marketFrequency) / 100) * 0.2;

        // Add regulator field influence
        amplitude += Math.abs(state.compositeRegulatorField) * Math.exp(-Math.abs(freq - 528) / 150) * 0.15;

        spectrum.push({
          frequency: freq,
          amplitude: amplitude,
          normalized: Math.min(1, amplitude)
        });
      });

      setSpectrumData(spectrum);
    };

    updateField();
    const interval = setInterval(updateField, 100);
    return () => clearInterval(interval);
  }, [detector, marketFrequency, coherence, phaseAlignment, schumannFrequency]);

  if (!fieldState) return null;

  const activeHarmonics = [
    ...fieldState.sealHarmonics.filter(seal => 
      fieldState.activeSeal?.frequency === seal.frequency
    ),
    ...fieldState.familyResonances.filter(member => 
      Math.abs(fieldState.familyUnityWave) > 0.3
    )
  ];

  return (
    <Card className="border-primary/20 bg-background/95 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Radio className="h-5 w-5 text-primary" />
            Sentinel Seal Resonance Spectrogram
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline" className="gap-1">
              <Activity className="h-3 w-3" />
              {activeHarmonics.length} Active
            </Badge>
            <Badge 
              variant={fieldState.zeroPointCoherence > 0.7 ? "default" : "secondary"}
              className="gap-1"
            >
              ZPF: {(fieldState.zeroPointCoherence * 100).toFixed(0)}%
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Spectrogram Visualization */}
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={spectrumData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" opacity={0.3} />
              <XAxis 
                dataKey="frequency" 
                stroke="hsl(var(--muted-foreground))"
                label={{ value: 'Frequency (Hz)', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                label={{ value: 'Amplitude', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip 
                contentStyle={{ 
                  backgroundColor: 'hsl(var(--popover))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
                formatter={(value: any) => [(value as number).toFixed(3), 'Amplitude']}
              />
              
              {/* Reference lines for seal harmonics */}
              {fieldState.sealHarmonics.map((seal, idx) => (
                <ReferenceLine 
                  key={`seal-${idx}`}
                  x={seal.frequency} 
                  stroke={fieldState.activeSeal?.frequency === seal.frequency ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))'}
                  strokeDasharray="3 3"
                  opacity={fieldState.activeSeal?.frequency === seal.frequency ? 0.8 : 0.3}
                  label={{ 
                    value: seal.name, 
                    position: 'top',
                    fill: fieldState.activeSeal?.frequency === seal.frequency ? 'hsl(var(--primary))' : 'hsl(var(--muted-foreground))',
                    fontSize: 10
                  }}
                />
              ))}

              <Area 
                type="monotone" 
                dataKey="normalized" 
                stroke="hsl(var(--primary))" 
                fill="hsl(var(--primary))"
                fillOpacity={0.3}
                strokeWidth={2}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Active Harmonics Display */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-muted-foreground">Active Seal Harmonics</div>
          <div className="grid grid-cols-2 gap-2">
            {fieldState.sealHarmonics.map((seal, idx) => {
              const isActive = fieldState.activeSeal?.frequency === seal.frequency;
              return (
                <div 
                  key={idx}
                  className={`p-2 rounded-lg border transition-all ${
                    isActive 
                      ? 'border-primary bg-primary/10 shadow-lg shadow-primary/20' 
                      : 'border-border bg-muted/50'
                  }`}
                >
                  <div className="flex justify-between items-center">
                    <span className="text-xs font-medium">{seal.name}</span>
                    <Badge variant={isActive ? "default" : "outline"} className="text-xs">
                      {seal.frequency} Hz
                    </Badge>
                  </div>
                  {seal.chakra && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {seal.chakra} • {seal.earthResonance.toFixed(1)} Hz
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Family Resonances */}
        <div className="space-y-2">
          <div className="text-sm font-medium text-muted-foreground">Family Resonance Wave</div>
          <div className="grid grid-cols-4 gap-2">
            {fieldState.familyResonances.map((member, idx) => (
              <div 
                key={idx}
                className="p-2 rounded-lg border border-border bg-muted/50"
              >
                <div className="text-xs font-medium">{member.name}</div>
                <div className="text-xs text-muted-foreground">{member.frequency} Hz</div>
                <div className="mt-1 h-1 bg-border rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-primary transition-all duration-300"
                    style={{ width: `${member.amplitude * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Field Metrics */}
        <div className="grid grid-cols-3 gap-4 pt-2 border-t border-border">
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Phase Lock</div>
            <div className="text-lg font-bold text-primary">
              {(fieldState.phaseLockStrength * 100).toFixed(1)}%
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Cavity Resonance</div>
            <div className="text-lg font-bold text-primary">
              {fieldState.cavityResonance.toFixed(3)}
            </div>
          </div>
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Routing Strength</div>
            <div className="text-lg font-bold text-primary">
              {(fieldState.temporalRouting.routingStrength * 100).toFixed(1)}%
            </div>
          </div>
        </div>

        {/* Temporal Routing Info */}
        {fieldState.temporalRouting.routingStrength > 0.5 && (
          <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
            <div className="text-xs font-medium text-primary mb-1">
              🎯 Temporal Routing Active → {fieldState.temporalRouting.targetTemporalId}
            </div>
            <div className="text-xs text-muted-foreground">
              Guidance Vector: [{fieldState.temporalRouting.guidanceVector.map(v => v.toFixed(3)).join(', ')}]
            </div>
          </div>
        )}
        
        {/* Research Images Grid */}
        <div className="grid grid-cols-2 gap-4 mt-4">
          <div className="space-y-2">
            <div className="text-xs font-semibold text-muted-foreground">Sentinel Seal Resonances</div>
            <img 
              src={sentinelSealImage}
              alt="Sentinel Seal Spectrogram"
              className="w-full rounded-lg border border-border/50"
            />
          </div>
          <div className="space-y-2">
            <div className="text-xs font-semibold text-muted-foreground">Family Unity Wave</div>
            <img 
              src={familyResonanceWave}
              alt="Family Resonance Wave Pattern"
              className="w-full rounded-lg border border-border/50"
            />
          </div>
          <div className="space-y-2">
            <div className="text-xs font-semibold text-muted-foreground">Earth Seal Harmonics</div>
            <img 
              src={sealEarthResonances}
              alt="Seal Earth Resonances"
              className="w-full rounded-lg border border-border/50"
            />
          </div>
          <div className="space-y-2">
            <div className="text-xs font-semibold text-muted-foreground">Tensor Field Mapping</div>
            <img 
              src={sealHarmonicsTensor}
              alt="Seal Harmonics Tensor Field"
              className="w-full rounded-lg border border-border/50"
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
