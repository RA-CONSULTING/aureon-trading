import React, { useRef, useEffect } from 'react';

interface Point6D {
  x: number; y: number; z: number;
  w: number; v: number; u: number;
  intensity: number;
  phase: number;
}

interface QuantumField6DVisualizerProps {
  fieldPoints: Point6D[];
  fieldStrength: number;
  phaseShift: number;
  isResonating: boolean;
}

export function QuantumField6DVisualizer({ 
  fieldPoints, 
  fieldStrength, 
  phaseShift, 
  isResonating 
}: QuantumField6DVisualizerProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.95)';
    ctx.fillRect(0, 0, width, height);

    // Project 6D to 2D using multiple projections
    fieldPoints.forEach((point, index) => {
      // Primary 3D projection (x,y,z)
      const x1 = (point.x * 0.8 + point.z * 0.3) * width * 0.4 + width * 0.25;
      const y1 = (point.y * 0.8 - point.z * 0.2) * height * 0.4 + height * 0.25;

      // Secondary 3D projection (w,v,u) 
      const x2 = (point.w * 0.8 + point.u * 0.3) * width * 0.4 + width * 0.75;
      const y2 = (point.v * 0.8 - point.u * 0.2) * height * 0.4 + height * 0.25;

      // Tertiary projection (mixed dimensions)
      const x3 = (point.x * 0.5 + point.w * 0.5) * width * 0.3 + width * 0.5;
      const y3 = (point.y * 0.5 + point.v * 0.5) * height * 0.3 + height * 0.75;

      const intensity = point.intensity;
      const hue = (point.phase * 180 / Math.PI + phaseShift + 180) % 360;
      
      // Draw primary projection
      ctx.fillStyle = `hsla(${hue}, 70%, ${30 + intensity * 50}%, ${intensity * 0.8})`;
      ctx.beginPath();
      ctx.arc(x1, y1, 2 + intensity * 3, 0, Math.PI * 2);
      ctx.fill();

      // Draw secondary projection
      ctx.fillStyle = `hsla(${(hue + 120) % 360}, 60%, ${40 + intensity * 40}%, ${intensity * 0.6})`;
      ctx.beginPath();
      ctx.arc(x2, y2, 1 + intensity * 2, 0, Math.PI * 2);
      ctx.fill();

      // Draw tertiary projection
      ctx.fillStyle = `hsla(${(hue + 240) % 360}, 50%, ${50 + intensity * 30}%, ${intensity * 0.4})`;
      ctx.beginPath();
      ctx.arc(x3, y3, 1 + intensity * 1.5, 0, Math.PI * 2);
      ctx.fill();

      // Connect projections with lines for high intensity points
      if (intensity > 0.7) {
        ctx.strokeStyle = `hsla(${hue}, 80%, 60%, ${intensity * 0.3})`;
        ctx.lineWidth = 0.5;
        ctx.beginPath();
        ctx.moveTo(x1, y1);
        ctx.lineTo(x2, y2);
        ctx.lineTo(x3, y3);
        ctx.stroke();
      }
    });

    // Add resonance effects
    if (isResonating) {
      ctx.strokeStyle = 'rgba(255, 255, 0, 0.3)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(width * 0.25, height * 0.25, 50, 0, Math.PI * 2);
      ctx.arc(width * 0.75, height * 0.25, 50, 0, Math.PI * 2);
      ctx.arc(width * 0.5, height * 0.75, 50, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Add dimension labels
    ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
    ctx.font = '10px monospace';
    ctx.fillText('XYZ', 10, height * 0.25);
    ctx.fillText('WVU', width * 0.75 - 20, height * 0.25);
    ctx.fillText('MIX', width * 0.5 - 15, height * 0.75 + 60);

  }, [fieldPoints, fieldStrength, phaseShift, isResonating]);

  return (
    <canvas
      ref={canvasRef}
      width={400}
      height={300}
      className="border rounded-lg bg-black"
      style={{ imageRendering: 'pixelated' }}
    />
  );
}