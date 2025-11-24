import React, { useEffect, useRef } from 'react';

interface QuantumFieldVisualizerProps {
  fieldData?: number[];
  width?: number;
  height?: number;
  title?: string;
}

export const QuantumFieldVisualizer: React.FC<QuantumFieldVisualizerProps> = ({
  fieldData = [],
  width = 400,
  height = 300,
  title = "Quantum Field Projection"
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Create quantum field visualization
    const imageData = ctx.createImageData(width, height);
    const data = imageData.data;

    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const index = (y * width + x) * 4;
        
        // Generate quantum field pattern
        const centerX = width / 2;
        const centerY = height / 2;
        const distance = Math.sqrt((x - centerX) ** 2 + (y - centerY) ** 2);
        const angle = Math.atan2(y - centerY, x - centerX);
        
        // Quantum interference pattern
        const wave1 = Math.sin(distance * 0.1 + Date.now() * 0.001);
        const wave2 = Math.cos(angle * 8 + Date.now() * 0.002);
        const interference = wave1 * wave2;
        
        // Map to color spectrum (purple to yellow)
        const intensity = (interference + 1) / 2;
        data[index] = Math.floor(255 * (1 - intensity)); // R
        data[index + 1] = Math.floor(128 * intensity); // G
        data[index + 2] = Math.floor(255 * intensity); // B
        data[index + 3] = 255; // A
      }
    }

    ctx.putImageData(imageData, 0, 0);

    // Add fracture curve overlay
    ctx.strokeStyle = '#000';
    ctx.lineWidth = 2;
    ctx.beginPath();
    for (let i = 0; i < width; i++) {
      const t = i / width;
      const y = height/2 + 50 * Math.sin(t * Math.PI * 4) * Math.exp(-t * 2);
      if (i === 0) ctx.moveTo(i, y);
      else ctx.lineTo(i, y);
    }
    ctx.stroke();
  }, [width, height, fieldData]);

  return (
    <div className="bg-zinc-900 rounded-xl p-4 border border-zinc-700">
      <h3 className="text-sm font-medium text-zinc-300 mb-3">{title}</h3>
      <canvas 
        ref={canvasRef}
        width={width}
        height={height}
        className="rounded-lg border border-zinc-600"
      />
    </div>
  );
};

export default QuantumFieldVisualizer;