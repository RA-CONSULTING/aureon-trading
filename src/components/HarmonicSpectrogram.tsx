import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

interface HarmonicData {
  harmonic: number;
  frequency: number;
  amplitude: number;
  phase: number;
  color: string;
}

export const HarmonicSpectrogram = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [harmonics, setHarmonics] = useState<HarmonicData[]>([
    { harmonic: 1, frequency: 7.83, amplitude: 1.0, phase: 0, color: '#8B5CF6' },
    { harmonic: 2, frequency: 14.3, amplitude: 0.6, phase: 0, color: '#3B82F6' },
    { harmonic: 3, frequency: 20.8, amplitude: 0.4, phase: 0, color: '#10B981' },
    { harmonic: 4, frequency: 27.3, amplitude: 0.3, phase: 0, color: '#F59E0B' },
    { harmonic: 5, frequency: 33.8, amplitude: 0.2, phase: 0, color: '#EF4444' }
  ]);
  
  const [timeOffset, setTimeOffset] = useState(0);
  const [compositeWave, setCompositeWave] = useState<number[]>([]);

  useEffect(() => {
    const interval = setInterval(() => {
      setTimeOffset(prev => prev + 0.1);
      
      // Update harmonic data with slight variations
      setHarmonics(prev => prev.map(h => ({
        ...h,
        amplitude: Math.max(0.1, h.amplitude + (Math.random() - 0.5) * 0.02),
        phase: h.phase + (Math.random() - 0.5) * 0.1
      })));
    }, 50);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const timeRange = 10;
    const maxAmplitude = 17.5;

    // Clear canvas with dark background
    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, width, height);

    // Calculate composite waveform
    const points = 1000;
    const composite: number[] = [];
    
    for (let i = 0; i < points; i++) {
      const t = (i / points) * timeRange;
      let sum = 0;
      
      harmonics.forEach(harmonic => {
        const freq = harmonic.frequency / 10; // Scale for visualization
        const wave = harmonic.amplitude * Math.sin(2 * Math.PI * freq * (t + timeOffset) + harmonic.phase);
        sum += wave;
      });
      
      composite.push(sum);
    }

    setCompositeWave(composite);

    // Draw individual harmonics
    harmonics.forEach((harmonic, index) => {
      ctx.strokeStyle = harmonic.color;
      ctx.lineWidth = 2;
      ctx.globalAlpha = 0.8;
      ctx.beginPath();

      const baseY = height - (index + 1) * (height / 7);
      const freq = harmonic.frequency / 10;

      for (let x = 0; x < width; x++) {
        const t = (x / width) * timeRange;
        const wave = harmonic.amplitude * Math.sin(2 * Math.PI * freq * (t + timeOffset) + harmonic.phase);
        const y = baseY - (wave * 20);

        if (x === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      
      ctx.stroke();
    });

    // Draw composite waveform
    ctx.strokeStyle = '#FFFFFF';
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.9;
    ctx.beginPath();

    const compositeBaseY = height - 50;
    
    for (let x = 0; x < width; x++) {
      const index = Math.floor((x / width) * composite.length);
      const wave = composite[index] || 0;
      const y = compositeBaseY - (wave * 8);

      if (x === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    }
    
    ctx.stroke();

    // Draw labels
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '12px Arial';
    ctx.globalAlpha = 0.7;
    
    harmonics.forEach((harmonic, index) => {
      const y = height - (index + 1) * (height / 7) + 5;
      ctx.fillText(`Harmonic ${harmonic.harmonic}`, 10, y);
    });
    
    ctx.fillText('Composite Waveform', 10, compositeBaseY + 15);

  }, [harmonics, timeOffset]);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="text-lg font-semibold">
          Visual Harmonic Score - Song of Time and Space
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="relative">
          <canvas
            ref={canvasRef}
            width={800}
            height={400}
            className="w-full h-auto border border-gray-300 rounded"
          />
          
          {/* Legend */}
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            {harmonics.map((harmonic, index) => (
              <div key={index} className="flex items-center gap-2">
                <div 
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: harmonic.color }}
                />
                <span>
                  Harmonic {harmonic.harmonic} ({harmonic.frequency.toFixed(1)} Hz)
                </span>
              </div>
            ))}
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-white rounded" />
              <span>Composite Waveform</span>
            </div>
          </div>

          {/* Real-time stats */}
          <div className="mt-4 grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
            {harmonics.map((harmonic, index) => (
              <div key={index} className="text-center">
                <div className="font-semibold" style={{ color: harmonic.color }}>
                  H{harmonic.harmonic}
                </div>
                <div className="text-gray-600">
                  {(harmonic.amplitude * 100).toFixed(0)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default HarmonicSpectrogram;