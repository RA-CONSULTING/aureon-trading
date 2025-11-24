// Main Schumann Lattice Integration Component
import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Slider } from '@/components/ui/slider';
import SchumannLatticeRenderer from './SchumannLatticeRenderer';
import { schumannToBlobs } from './SchumannLatticeCore';
import { TensorDatum, IntentCompiler } from './SchumannLatticePatch';

interface Props {
  schumannFrequencies?: number[];
  tensorData?: TensorDatum[];
  intentCompiler?: IntentCompiler;
  autoUpdate?: boolean;
  updateInterval?: number;
}

export default function SchumannLatticeIntegration({
  schumannFrequencies = [7.83, 14.3, 20.8, 27.3, 33.8],
  tensorData,
  intentCompiler,
  autoUpdate = false,
  updateInterval = 1000
}: Props) {
  const [intentText, setIntentText] = useState('');
  const [intentFreqs, setIntentFreqs] = useState<number[]>([]);
  const [isPlaying, setIsPlaying] = useState(autoUpdate);
  const [intensity, setIntensity] = useState([1]);

  const blobs = useMemo(() => {
    const baseBlobs = schumannToBlobs(schumannFrequencies, tensorData);
    const intentBlobs = schumannToBlobs(intentFreqs);
    
    return [...baseBlobs, ...intentBlobs.map(blob => ({
      ...blob,
      weight: blob.weight * intensity[0] * 0.7
    }))];
  }, [schumannFrequencies, tensorData, intentFreqs, intensity]);

  const processIntent = async () => {
    if (!intentCompiler || !intentText.trim()) return;
    
    try {
      const result = await intentCompiler.process_intent(intentText);
      setIntentFreqs(result.frequencies || []);
    } catch (error) {
      console.error('Intent processing failed:', error);
    }
  };

  useEffect(() => {
    if (!isPlaying) return;
    
    const interval = setInterval(() => {
      // Simulate live data updates
      const jitter = () => (Math.random() - 0.5) * 0.2;
      const updatedFreqs = schumannFrequencies.map(f => f * (1 + jitter()));
      // Would update parent state here in real implementation
    }, updateInterval);
    
    return () => clearInterval(interval);
  }, [isPlaying, updateInterval, schumannFrequencies]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Schumann Lattice Integration
          <Button 
            variant={isPlaying ? "secondary" : "default"}
            onClick={() => setIsPlaying(!isPlaying)}
            size="sm"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex gap-2">
          <Input
            placeholder="Enter intention (e.g., 'peace and healing')"
            value={intentText}
            onChange={(e) => setIntentText(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && processIntent()}
          />
          <Button onClick={processIntent} disabled={!intentCompiler}>
            Compile
          </Button>
        </div>
        
        <div className="space-y-2">
          <label className="text-sm font-medium">Intensity: {intensity[0].toFixed(2)}</label>
          <Slider
            value={intensity}
            onValueChange={setIntensity}
            max={2}
            min={0}
            step={0.1}
            className="w-full"
          />
        </div>

        <SchumannLatticeRenderer 
          blobs={blobs}
          cellSize={50}
          radius={10}
          height={400}
        />
        
        <div className="text-xs text-muted-foreground">
          Base frequencies: {schumannFrequencies.map(f => f.toFixed(1)).join(', ')} Hz
          {intentFreqs.length > 0 && (
            <div>Intent frequencies: {intentFreqs.map(f => f.toFixed(1)).join(', ')} Hz</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}