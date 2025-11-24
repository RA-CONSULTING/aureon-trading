import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Badge } from '@/components/ui/badge';

interface FieldPoint {
  x: number;
  y: number;
  intensity: number;
  phase: number;
}

export function QuantumFieldMatrix() {
  const [fieldStrength, setFieldStrength] = useState([75]);
  const [phaseShift, setPhaseShift] = useState([0]);
  const [fieldPoints, setFieldPoints] = useState<FieldPoint[]>([]);
  const [isResonating, setIsResonating] = useState(false);

  useEffect(() => {
    const generateField = () => {
      const points: FieldPoint[] = [];
      const gridSize = 20;
      
      for (let x = 0; x < gridSize; x++) {
        for (let y = 0; y < gridSize; y++) {
          const normalizedX = (x / gridSize) * 2 - 1;
          const normalizedY = (y / gridSize) * 2 - 1;
          
          const distance = Math.sqrt(normalizedX * normalizedX + normalizedY * normalizedY);
          const phase = Math.atan2(normalizedY, normalizedX) + (phaseShift[0] / 100) * Math.PI;
          const intensity = (fieldStrength[0] / 100) * Math.exp(-distance * 2) * 
                           (1 + 0.5 * Math.sin(phase * 3));
          
          points.push({
            x: normalizedX,
            y: normalizedY,
            intensity: Math.max(0, Math.min(1, intensity)),
            phase
          });
        }
      }
      
      setFieldPoints(points);
    };

    generateField();
  }, [fieldStrength, phaseShift]);

  useEffect(() => {
    if (fieldStrength[0] > 80) {
      setIsResonating(true);
      const timer = setTimeout(() => setIsResonating(false), 2000);
      return () => clearTimeout(timer);
    }
  }, [fieldStrength]);

  const getFieldColor = (intensity: number, phase: number) => {
    const hue = (phase * 180 / Math.PI + 180) % 360;
    const saturation = 70 + intensity * 30;
    const lightness = 30 + intensity * 50;
    return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl">⚛️ Quantum Field Matrix</CardTitle>
          {isResonating && (
            <Badge variant="default" className="animate-pulse bg-yellow-500">
              RESONANCE DETECTED
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">Field Strength: {fieldStrength[0]}%</label>
            <Slider
              value={fieldStrength}
              onValueChange={setFieldStrength}
              max={100}
              step={1}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Phase Shift: {phaseShift[0]}°</label>
            <Slider
              value={phaseShift}
              onValueChange={setPhaseShift}
              min={-180}
              max={180}
              step={5}
              className="w-full"
            />
          </div>
        </div>
        
        <div className="flex justify-center">
          <div 
            className="grid grid-cols-20 gap-0 border rounded-lg p-2 bg-black"
            style={{ gridTemplateColumns: 'repeat(20, 8px)' }}
          >
            {fieldPoints.map((point, index) => (
              <div
                key={index}
                className="w-2 h-2 transition-colors duration-100"
                style={{
                  backgroundColor: getFieldColor(point.intensity, point.phase),
                  opacity: point.intensity
                }}
              />
            ))}
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-2 text-xs">
          <div className="text-center">
            <div className="font-semibold">Coherence</div>
            <div className="text-green-500">
              {(fieldPoints.reduce((sum, p) => sum + p.intensity, 0) / fieldPoints.length * 100).toFixed(1)}%
            </div>
          </div>
          <div className="text-center">
            <div className="font-semibold">Entropy</div>
            <div className="text-blue-500">
              {(Math.random() * 0.3 + 0.2).toFixed(3)}
            </div>
          </div>
          <div className="text-center">
            <div className="font-semibold">Stability</div>
            <div className="text-purple-500">
              {isResonating ? "UNSTABLE" : "STABLE"}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}