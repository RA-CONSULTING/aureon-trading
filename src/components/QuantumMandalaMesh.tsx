import React, { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { fmt } from '@/utils/number';

interface QuantumNode {
  x: number;
  y: number;
  phase: number;
  amplitude: number;
  frequency: number;
}

export const QuantumMandalaMesh: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isActive, setIsActive] = useState(false);
  const [meshDensity, setMeshDensity] = useState([32]);
  const [fieldIntensity, setFieldIntensity] = useState([0.75]);
  const [rotationSpeed, setRotationSpeed] = useState([1.0]);
  
  const [nodes, setNodes] = useState<QuantumNode[]>([]);
  const [fieldMetrics, setFieldMetrics] = useState({
    psiAmplitude: 0.82,
    coherenceIndex: 0.91,
    entanglementDegree: 0.76,
    mandalaSymmetry: 0.95
  });

  useEffect(() => {
    // Initialize quantum nodes in mandala pattern
    const newNodes: QuantumNode[] = [];
    const density = meshDensity[0];
    const rings = 8;
    
    for (let ring = 1; ring <= rings; ring++) {
      const nodesInRing = Math.floor(density * ring / 4);
      const radius = ring * 30;
      
      for (let i = 0; i < nodesInRing; i++) {
        const angle = (i / nodesInRing) * 2 * Math.PI;
        newNodes.push({
          x: 400 + radius * Math.cos(angle),
          y: 300 + radius * Math.sin(angle),
          phase: Math.random() * 2 * Math.PI,
          amplitude: Math.random() * 0.5 + 0.5,
          frequency: 0.5 + ring * 0.1
        });
      }
    }
    
    setNodes(newNodes);
  }, [meshDensity]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = 800;
    canvas.height = 600;

    const drawQuantumMandala = (time: number) => {
      // Clear with deep space background
      const gradient = ctx.createRadialGradient(400, 300, 0, 400, 300, 400);
      gradient.addColorStop(0, '#1a1a2e');
      gradient.addColorStop(0.5, '#16213e');
      gradient.addColorStop(1, '#0f0f23');
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const rotation = time * rotationSpeed[0] * 0.001;
      const intensity = fieldIntensity[0];

      // Draw quantum field mesh
      ctx.strokeStyle = 'rgba(138, 43, 226, 0.3)';
      ctx.lineWidth = 1;
      
      nodes.forEach((node, i) => {
        const psi = node.amplitude * Math.sin(
          node.frequency * time * 0.01 + node.phase + rotation
        );
        
        // Draw connections to nearby nodes
        nodes.forEach((otherNode, j) => {
          if (i >= j) return;
          const dx = node.x - otherNode.x;
          const dy = node.y - otherNode.y;
          const distance = Math.sqrt(dx * dx + dy * dy);
          
          if (distance < 80) {
            const alpha = Math.max(0, 1 - distance / 80) * intensity * 0.5;
            ctx.strokeStyle = `rgba(138, 43, 226, ${alpha})`;
            ctx.beginPath();
            ctx.moveTo(node.x, node.y);
            ctx.lineTo(otherNode.x, otherNode.y);
            ctx.stroke();
          }
        });

        // Draw quantum nodes
        const nodeSize = Math.abs(psi) * 8 + 2;
        const hue = (psi + 1) * 180 + 200; // Purple to cyan spectrum
        ctx.fillStyle = `hsla(${hue}, 70%, 60%, ${intensity})`;
        ctx.beginPath();
        ctx.arc(node.x, node.y, nodeSize, 0, 2 * Math.PI);
        ctx.fill();
        
        // Add quantum glow effect
        ctx.shadowColor = `hsla(${hue}, 70%, 60%, 0.8)`;
        ctx.shadowBlur = 10;
        ctx.fill();
        ctx.shadowBlur = 0;
      });

      // Draw central mandala core
      ctx.save();
      ctx.translate(400, 300);
      ctx.rotate(rotation);
      
      for (let i = 0; i < 12; i++) {
        ctx.rotate(Math.PI / 6);
        const coreIntensity = Math.sin(time * 0.003) * 0.3 + 0.7;
        ctx.strokeStyle = `rgba(255, 215, 0, ${coreIntensity * intensity})`;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(0, 0);
        ctx.lineTo(0, -60);
        ctx.stroke();
        
        // Sacred geometry patterns
        ctx.strokeStyle = `rgba(0, 255, 255, ${coreIntensity * intensity * 0.6})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(0, -40, 10, 0, 2 * Math.PI);
        ctx.stroke();
      }
      
      ctx.restore();
    };

    let animationId: number;
    const animate = (time: number) => {
      drawQuantumMandala(time);
      
      if (isActive) {
        // Update field metrics with quantum fluctuations
        setFieldMetrics(prev => ({
          psiAmplitude: Math.max(0, Math.min(1, prev.psiAmplitude + (Math.random() - 0.5) * 0.02)),
          coherenceIndex: Math.max(0, Math.min(1, prev.coherenceIndex + (Math.random() - 0.5) * 0.015)),
          entanglementDegree: Math.max(0, Math.min(1, prev.entanglementDegree + (Math.random() - 0.5) * 0.01)),
          mandalaSymmetry: Math.max(0, Math.min(1, prev.mandalaSymmetry + (Math.random() - 0.5) * 0.005))
        }));
      }
      
      animationId = requestAnimationFrame(animate);
    };

    animationId = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationId);
  }, [nodes, isActive, fieldIntensity, rotationSpeed]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card className="bg-gradient-to-r from-purple-900 via-blue-900 to-indigo-900 text-white">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center space-x-2">
              <span className="text-2xl">🕉️</span>
              <span>Quantum Mandala Mesh</span>
            </span>
            <Button
              onClick={() => setIsActive(!isActive)}
              variant={isActive ? "destructive" : "secondary"}
              size="sm"
            >
              {isActive ? "🌀 ACTIVE" : "⚡ ACTIVATE"}
            </Button>
          </CardTitle>
        </CardHeader>
      </Card>

      {/* Quantum Field Visualization */}
      <Card>
        <CardContent className="p-6">
          <canvas
            ref={canvasRef}
            className="w-full border rounded-lg"
            style={{ maxWidth: '100%', height: 'auto', backgroundColor: '#0a0a1a' }}
          />
        </CardContent>
      </Card>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Mesh Density</label>
              <Slider
                value={meshDensity}
                onValueChange={setMeshDensity}
                max={64}
                min={16}
                step={4}
              />
              <div className="text-xs text-gray-500">{meshDensity[0]} nodes/ring</div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Field Intensity</label>
              <Slider
                value={fieldIntensity}
                onValueChange={setFieldIntensity}
                max={1}
                min={0.1}
                step={0.05}
              />
              <div className="text-xs text-gray-500">{fmt(fieldIntensity[0], 2)}×</div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Rotation Speed</label>
              <Slider
                value={rotationSpeed}
                onValueChange={setRotationSpeed}
                max={3}
                min={0.1}
                step={0.1}
              />
              <div className="text-xs text-gray-500">{fmt(rotationSpeed[0], 1)}×</div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quantum Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-purple-600 to-purple-800 text-white">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{fmt(fieldMetrics.psiAmplitude, 3)}</div>
            <div className="text-sm opacity-80">Ψ Amplitude</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-blue-600 to-blue-800 text-white">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{fmt(fieldMetrics.coherenceIndex, 3)}</div>
            <div className="text-sm opacity-80">Coherence Index</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-indigo-600 to-indigo-800 text-white">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{fmt(fieldMetrics.entanglementDegree, 3)}</div>
            <div className="text-sm opacity-80">Entanglement</div>
          </CardContent>
        </Card>
        
        <Card className="bg-gradient-to-br from-cyan-600 to-cyan-800 text-white">
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{fmt(fieldMetrics.mandalaSymmetry, 3)}</div>
            <div className="text-sm opacity-80">Mandala Symmetry</div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};