import React, { useState, useCallback, useEffect } from 'react';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';

interface GainHarmonicsControlsProps {
  onControlChange: (control: { gain?: number; targets_hz?: number[] }) => void;
  currentGain: number;
  currentFundamental: number;
}

const CANONICAL_SCHUMANN = [7.83, 14.3, 20.8, 27.3, 33.8];
const SNAP_THRESHOLD = 0.05;

export function GainHarmonicsControls({ 
  onControlChange, 
  currentGain, 
  currentFundamental 
}: GainHarmonicsControlsProps) {
  const [gain, setGain] = useState(currentGain);
  const [fundamental, setFundamental] = useState(currentFundamental);
  const [autoGain, setAutoGain] = useState(false);
  const [lastCoherence, setLastCoherence] = useState<number | null>(null);
  const [lastLock, setLastLock] = useState<number | null>(null);

  // Debounced control updates
  const [debounceTimeout, setDebounceTimeout] = useState<NodeJS.Timeout | null>(null);

  const debouncedUpdate = useCallback((newGain: number, newFund: number) => {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    
    const timeout = setTimeout(() => {
      const harmonics = [
        newFund,
        newFund * 1.82, // ~14.3 Hz
        newFund * 2.66, // ~20.8 Hz  
        newFund * 3.49, // ~27.3 Hz
        newFund * 4.32  // ~33.8 Hz
      ];
      
      onControlChange({ 
        gain: newGain,
        targets_hz: harmonics 
      });
    }, 150);
    
    setDebounceTimeout(timeout);
  }, [debounceTimeout, onControlChange]);

  const handleGainChange = useCallback((value: number[]) => {
    const newGain = value[0];
    setGain(newGain);
    debouncedUpdate(newGain, fundamental);
  }, [fundamental, debouncedUpdate]);

  const handleFundamentalChange = useCallback((value: number[]) => {
    let newFund = value[0];
    
    // Snap to canonical frequencies
    const closest = CANONICAL_SCHUMANN.find(freq => 
      Math.abs(newFund - freq) < SNAP_THRESHOLD
    );
    if (closest) newFund = closest;
    
    setFundamental(newFund);
    debouncedUpdate(gain, newFund);
  }, [gain, debouncedUpdate]);

  const resetToCanonical = useCallback(() => {
    setFundamental(7.83);
    setGain(1.0);
    debouncedUpdate(1.0, 7.83);
  }, [debouncedUpdate]);

  return (
    <Card className="bg-zinc-900/50 border-zinc-700">
      <CardHeader className="pb-3">
        <CardTitle className="text-sm text-zinc-200 flex items-center justify-between">
          Field Tuning Controls
          <Badge variant="outline" className="text-xs">
            Live
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Amplitude Gain */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-zinc-300">Amplitude Gain</Label>
            <span className="text-xs text-zinc-400 font-mono">
              {gain.toFixed(2)}x
            </span>
          </div>
          <Slider
            value={[gain]}
            onValueChange={handleGainChange}
            min={0.1}
            max={3.0}
            step={0.05}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-zinc-500">
            <span>0.1x</span>
            <span>3.0x</span>
          </div>
        </div>

        {/* Fundamental Frequency */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label className="text-xs text-zinc-300">Fundamental (Hz)</Label>
            <span className="text-xs text-zinc-400 font-mono">
              {fundamental.toFixed(2)} Hz
            </span>
          </div>
          <Slider
            value={[fundamental]}
            onValueChange={handleFundamentalChange}
            min={7.0}
            max={8.5}
            step={0.01}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-zinc-500">
            <span>7.0</span>
            <span>8.5</span>
          </div>
        </div>

        {/* Auto Gain Toggle */}
        <div className="flex items-center justify-between pt-2 border-t border-zinc-700">
          <Label className="text-xs text-zinc-300">Auto Gain</Label>
          <Switch
            checked={autoGain}
            onCheckedChange={setAutoGain}
            size="sm"
          />
        </div>

        {/* Reset Button */}
        <Button
          onClick={resetToCanonical}
          variant="outline"
          size="sm"
          className="w-full text-xs"
        >
          Reset to Canonical (7.83 Hz)
        </Button>

        {/* Harmonics Preview */}
        <div className="pt-2 border-t border-zinc-700">
          <Label className="text-xs text-zinc-400 mb-2 block">Harmonics</Label>
          <div className="grid grid-cols-5 gap-1 text-xs font-mono">
            {[1, 1.82, 2.66, 3.49, 4.32].map((mult, i) => (
              <div key={i} className="text-center text-zinc-500">
                {(fundamental * mult).toFixed(1)}
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}