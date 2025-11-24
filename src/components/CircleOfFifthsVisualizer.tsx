import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface CircleOfFifthsVisualizerProps {
  currentKey?: string;
  harmonicWeights?: number[];
  colorPaletteShift?: number;
  primeWeighting?: { unity: number; flow: number; anchor: number };
}

export default function CircleOfFifthsVisualizer({
  currentKey = 'C',
  harmonicWeights = [1, 0.8, 0.6, 0.4],
  colorPaletteShift = 0,
  primeWeighting = { unity: 1.0, flow: 0.9, anchor: 0.1 }
}: CircleOfFifthsVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [activeKey, setActiveKey] = useState(currentKey);
  
  const keys = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F'];
  const keyToHue = [0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(centerX, centerY) - 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Draw circle of fifths
    keys.forEach((key, index) => {
      const angle = (index * 30 - 90) * (Math.PI / 180); // Start at top
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      
      // Calculate hue with palette shift
      const baseHue = keyToHue[index];
      const shiftedHue = (baseHue + colorPaletteShift) % 360;
      
      // Apply prime weighting for intensity
      const weight = harmonicWeights[index % harmonicWeights.length] || 0.5;
      const primeIntensity = key === activeKey ? primeWeighting.unity : 
                           (index % 2 === 0 ? primeWeighting.flow : primeWeighting.anchor);
      
      const saturation = Math.min(100, 60 + (weight * primeIntensity * 40));
      const lightness = key === activeKey ? 70 : 50;
      
      // Draw key circle
      ctx.beginPath();
      ctx.arc(x, y, key === activeKey ? 25 : 18, 0, 2 * Math.PI);
      ctx.fillStyle = `hsl(${shiftedHue}, ${saturation}%, ${lightness}%)`;
      ctx.fill();
      
      // Draw border
      ctx.strokeStyle = key === activeKey ? '#ffffff' : `hsl(${shiftedHue}, ${saturation}%, 30%)`;
      ctx.lineWidth = key === activeKey ? 3 : 1;
      ctx.stroke();
      
      // Draw key label
      ctx.fillStyle = lightness > 60 ? '#000000' : '#ffffff';
      ctx.font = key === activeKey ? 'bold 14px sans-serif' : '12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(key, x, y);
    });
    
    // Draw connecting lines for fifth relationships
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
    ctx.lineWidth = 1;
    keys.forEach((key, index) => {
      const nextIndex = (index + 1) % keys.length;
      const angle1 = (index * 30 - 90) * (Math.PI / 180);
      const angle2 = (nextIndex * 30 - 90) * (Math.PI / 180);
      
      const x1 = centerX + Math.cos(angle1) * radius;
      const y1 = centerY + Math.sin(angle1) * radius;
      const x2 = centerX + Math.cos(angle2) * radius;
      const y2 = centerY + Math.sin(angle2) * radius;
      
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    });
    
    // Draw center point
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
    ctx.fill();
    
  }, [activeKey, harmonicWeights, colorPaletteShift, primeWeighting]);

  const handleKeyClick = (key: string) => {
    setActiveKey(key);
  };

  return (
    <Card className="w-full">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Circle of Fifths</CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              Key: {activeKey}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              Shift: {colorPaletteShift.toFixed(1)}°
            </Badge>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={300}
            height={300}
            className="w-full max-w-sm mx-auto cursor-pointer"
            onClick={(e) => {
              const rect = e.currentTarget.getBoundingClientRect();
              const x = e.clientX - rect.left;
              const y = e.clientY - rect.top;
              
              // Simple click detection - find closest key
              const centerX = rect.width / 2;
              const centerY = rect.height / 2;
              const radius = Math.min(centerX, centerY) - 40;
              
              let closestKey = activeKey;
              let minDistance = Infinity;
              
              keys.forEach((key, index) => {
                const angle = (index * 30 - 90) * (Math.PI / 180);
                const keyX = centerX + Math.cos(angle) * radius;
                const keyY = centerY + Math.sin(angle) * radius;
                
                const distance = Math.sqrt((x - keyX) ** 2 + (y - keyY) ** 2);
                if (distance < minDistance && distance < 30) {
                  minDistance = distance;
                  closestKey = key;
                }
              });
              
              handleKeyClick(closestKey);
            }}
          />
          
          <div className="mt-4 grid grid-cols-4 gap-2 text-xs">
            <div className="text-center">
              <div className="font-medium">Unity</div>
              <div className="text-muted-foreground">{primeWeighting.unity.toFixed(1)}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Flow</div>
              <div className="text-muted-foreground">{primeWeighting.flow.toFixed(1)}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Anchor</div>
              <div className="text-muted-foreground">{primeWeighting.anchor.toFixed(1)}</div>
            </div>
            <div className="text-center">
              <div className="font-medium">Weights</div>
              <div className="text-muted-foreground">
                {harmonicWeights.map(w => w.toFixed(1)).join(',')}
              </div>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}