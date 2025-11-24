import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface NexusState {
  phaseLock: boolean;
  harmonicField: number;
  quantumCoherence: number;
  temporalGate: boolean;
  fieldIntensity: number;
}

export function HarmonicNexusCore() {
  const [nexusState, setNexusState] = useState<NexusState>({
    phaseLock: false,
    harmonicField: 7.83,
    quantumCoherence: 0.75,
    temporalGate: false,
    fieldIntensity: 0.5
  });
  
  const [isActive, setIsActive] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (!canvasRef.current || !isActive) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let frame = 0;
    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      
      // Draw harmonic field visualization
      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;
      
      // Phase-locked harmonics
      for (let i = 0; i < 8; i++) {
        const radius = 50 + i * 20;
        const phase = (frame * 0.02) + (i * Math.PI / 4);
        const intensity = nexusState.fieldIntensity * (1 + Math.sin(phase) * 0.3);
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius, 0, 2 * Math.PI);
        ctx.strokeStyle = `hsla(${180 + i * 30}, 70%, 60%, ${intensity})`;
        ctx.lineWidth = 2;
        ctx.stroke();
      }
      
      // Quantum coherence field
      if (nexusState.phaseLock) {
        ctx.beginPath();
        ctx.arc(centerX, centerY, 30, 0, 2 * Math.PI);
        ctx.fillStyle = `hsla(60, 100%, 70%, ${nexusState.quantumCoherence})`;
        ctx.fill();
      }
      
      frame++;
      requestAnimationFrame(animate);
    };
    
    animate();
  }, [isActive, nexusState]);

  const toggleNexus = () => {
    setIsActive(!isActive);
    if (!isActive) {
      setNexusState(prev => ({
        ...prev,
        phaseLock: true,
        temporalGate: true,
        fieldIntensity: Math.random() * 0.5 + 0.5
      }));
    }
  };

  return (
    <div className="w-full space-y-6">
      <Card className="bg-gradient-to-br from-slate-900 to-purple-900 border-purple-500/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-2xl font-bold text-white">
              🌌 Harmonic Nexus Core
            </CardTitle>
            <Button 
              onClick={toggleNexus}
              variant={isActive ? "destructive" : "default"}
              className="font-semibold"
            >
              {isActive ? "Disengage Nexus" : "Activate Nexus"}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-black/30 p-3 rounded-lg">
                  <div className="text-xs text-gray-300">Phase Lock</div>
                  <Badge variant={nexusState.phaseLock ? "default" : "secondary"}>
                    {nexusState.phaseLock ? "LOCKED" : "UNLOCKED"}
                  </Badge>
                </div>
                <div className="bg-black/30 p-3 rounded-lg">
                  <div className="text-xs text-gray-300">Temporal Gate</div>
                  <Badge variant={nexusState.temporalGate ? "default" : "secondary"}>
                    {nexusState.temporalGate ? "OPEN" : "CLOSED"}
                  </Badge>
                </div>
                <div className="bg-black/30 p-3 rounded-lg">
                  <div className="text-xs text-gray-300">Harmonic Freq</div>
                  <div className="text-lg font-mono text-cyan-400">
                    {nexusState.harmonicField.toFixed(2)} Hz
                  </div>
                </div>
                <div className="bg-black/30 p-3 rounded-lg">
                  <div className="text-xs text-gray-300">Coherence</div>
                  <div className="text-lg font-mono text-green-400">
                    {(nexusState.quantumCoherence * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
            <div className="flex items-center justify-center">
              <canvas 
                ref={canvasRef}
                width={300}
                height={300}
                className={cn(
                  "border rounded-lg transition-all duration-500",
                  isActive ? "border-cyan-500 shadow-lg shadow-cyan-500/20" : "border-gray-600"
                )}
              />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}