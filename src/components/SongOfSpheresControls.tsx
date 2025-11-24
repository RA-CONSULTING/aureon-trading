import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

interface PlanetaryModulator {
  name: string;
  weight: number;
  frequency_hz: number;
  phase_offset: number;
  enabled: boolean;
}

interface SongOfSpheresControlsProps {
  onModulatorChange?: (modulators: PlanetaryModulator[]) => void;
  onSynodicsChange?: (synodics: Record<string, boolean>) => void;
}

export default function SongOfSpheresControls({ 
  onModulatorChange, 
  onSynodicsChange 
}: SongOfSpheresControlsProps) {
  const [modulators, setModulators] = useState<PlanetaryModulator[]>([
    { name: 'Mercury', weight: 0.15, frequency_hz: 0.000131, phase_offset: 0, enabled: true },
    { name: 'Venus', weight: 0.25, frequency_hz: 0.0000514, phase_offset: 120, enabled: true },
    { name: 'Earth', weight: 1.0, frequency_hz: 0.0000317, phase_offset: 0, enabled: true },
    { name: 'Mars', weight: 0.35, frequency_hz: 0.0000168, phase_offset: 240, enabled: true },
    { name: 'Jupiter', weight: 0.8, frequency_hz: 0.00000267, phase_offset: 90, enabled: true },
    { name: 'Saturn', weight: 0.6, frequency_hz: 0.00000107, phase_offset: 180, enabled: true }
  ]);

  const [synodics, setSynodics] = useState({
    jupiter_saturn: true,
    earth_venus: true
  });

  const [masterMix, setMasterMix] = useState(0.5);

  const updateModulator = (index: number, field: keyof PlanetaryModulator, value: any) => {
    const updated = [...modulators];
    updated[index] = { ...updated[index], [field]: value };
    setModulators(updated);
    onModulatorChange?.(updated);
  };

  const updateSynodic = (key: string, enabled: boolean) => {
    const updated = { ...synodics, [key]: enabled };
    setSynodics(updated);
    onSynodicsChange?.(updated);
  };

  const resetToDefaults = () => {
    setModulators([
      { name: 'Mercury', weight: 0.15, frequency_hz: 0.000131, phase_offset: 0, enabled: true },
      { name: 'Venus', weight: 0.25, frequency_hz: 0.0000514, phase_offset: 120, enabled: true },
      { name: 'Earth', weight: 1.0, frequency_hz: 0.0000317, phase_offset: 0, enabled: true },
      { name: 'Mars', weight: 0.35, frequency_hz: 0.0000168, phase_offset: 240, enabled: true },
      { name: 'Jupiter', weight: 0.8, frequency_hz: 0.00000267, phase_offset: 90, enabled: true },
      { name: 'Saturn', weight: 0.6, frequency_hz: 0.00000107, phase_offset: 180, enabled: true }
    ]);
    setMasterMix(0.5);
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Song of the Spheres</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Musica Universalis
            </Badge>
            <Button variant="ghost" size="sm" onClick={resetToDefaults}>
              Reset
            </Button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Master Mix Control */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="text-sm font-medium">Master Spheres Mix</label>
            <span className="text-xs text-muted-foreground">
              {(masterMix * 100).toFixed(0)}%
            </span>
          </div>
          <Slider
            value={[masterMix]}
            onValueChange={([value]) => setMasterMix(value)}
            min={0}
            max={1}
            step={0.01}
            className="w-full"
          />
        </div>

        {/* Planetary Modulators */}
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-muted-foreground">Planetary Modulators</h3>
          {modulators.map((modulator, index) => (
            <div key={modulator.name} className="space-y-2 p-3 rounded-lg border">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Switch
                    checked={modulator.enabled}
                    onCheckedChange={(enabled) => updateModulator(index, 'enabled', enabled)}
                  />
                  <span className="text-sm font-medium">{modulator.name}</span>
                  <Badge variant="secondary" className="text-xs">
                    {(modulator.frequency_hz * 1000000).toFixed(2)}µHz
                  </Badge>
                </div>
                <span className="text-xs text-muted-foreground">
                  Weight: {modulator.weight.toFixed(2)}
                </span>
              </div>
              
              {modulator.enabled && (
                <div className="space-y-2 ml-6">
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Weight</label>
                    <Slider
                      value={[modulator.weight]}
                      onValueChange={([value]) => updateModulator(index, 'weight', value)}
                      min={0}
                      max={1.5}
                      step={0.05}
                      className="w-full"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs text-muted-foreground">Phase Offset (°)</label>
                    <Slider
                      value={[modulator.phase_offset]}
                      onValueChange={([value]) => updateModulator(index, 'phase_offset', value)}
                      min={0}
                      max={360}
                      step={15}
                      className="w-full"
                    />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Synodic Beats */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-muted-foreground">Synodic Beats</h3>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 rounded border">
              <div className="flex items-center gap-2">
                <Switch
                  checked={synodics.jupiter_saturn}
                  onCheckedChange={(enabled) => updateSynodic('jupiter_saturn', enabled)}
                />
                <span className="text-sm">Jupiter-Saturn</span>
                <Badge variant="outline" className="text-xs">19.86y</Badge>
              </div>
            </div>
            <div className="flex items-center justify-between p-2 rounded border">
              <div className="flex items-center gap-2">
                <Switch
                  checked={synodics.earth_venus}
                  onCheckedChange={(enabled) => updateSynodic('earth_venus', enabled)}
                />
                <span className="text-sm">Earth-Venus</span>
                <Badge variant="outline" className="text-xs">1.6y</Badge>
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}