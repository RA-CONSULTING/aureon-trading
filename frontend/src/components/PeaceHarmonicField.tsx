import React, { useEffect, useRef } from 'react';

interface PeaceHarmonicFieldProps {
  intensity?: number;
  frequency?: number;
}

export const PeaceHarmonicField: React.FC<PeaceHarmonicFieldProps> = ({
  intensity = 0.5,
  frequency = 1.0
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const animate = () => {
      ctx.clearRect(0, 0, 400, 300);
      
      const time = Date.now() * 0.001 * frequency;
      
      // Draw peace harmonic frequency field
      for (let x = 0; x < 400; x += 2) {
        for (let y = 0; y < 300; y += 2) {
          const centerX = 200;
          const centerY = 150;
          const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
          
          // Peace frequency calculation
          const harmonic1 = Math.sin(distance * 0.05 + time);
          const harmonic2 = Math.cos(distance * 0.03 + time * 1.5);
          const peace = (harmonic1 + harmonic2) * intensity;
          
          // Map to green-yellow spectrum
          const alpha = Math.abs(peace) * 0.8;
          const hue = 60 + peace * 60; // Green to yellow
          
          ctx.fillStyle = `hsla(${hue}, 80%, 60%, ${alpha})`;
          ctx.fillRect(x, y, 2, 2);
        }
      }
      
      // Draw central peace symbol
      ctx.strokeStyle = '#fff';
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(200, 150, 30, 0, Math.PI * 2);
      ctx.moveTo(200, 120);
      ctx.lineTo(200, 180);
      ctx.moveTo(185, 135);
      ctx.lineTo(215, 165);
      ctx.moveTo(215, 135);
      ctx.lineTo(185, 165);
      ctx.stroke();
      
      requestAnimationFrame(animate);
    };
    
    animate();
  }, [intensity, frequency]);

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-700">
      <h3 className="text-sm font-medium text-zinc-300 mb-3">Peace Harmonic Frequency Field</h3>
      <canvas 
        ref={canvasRef}
        width={400}
        height={300}
        className="rounded-lg border border-zinc-600"
      />
      <div className="mt-2 text-xs text-zinc-400">
        Intensity: {(intensity * 100).toFixed(0)}% • Frequency: {frequency.toFixed(1)}Hz
      </div>
    </div>
  );
};