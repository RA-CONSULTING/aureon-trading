import React, { useEffect, useState, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { hocusPatternPipeline, PipelineState, ModeState } from '@/core/hocusPatternPipeline';

const HocusPatternPipelineVisualizer: React.FC = () => {
  const [state, setState] = useState<PipelineState | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();
  
  useEffect(() => {
    const runPipeline = () => {
      const newState = hocusPatternPipeline.step();
      setState(newState);
      drawFieldVisualization();
      animationRef.current = requestAnimationFrame(runPipeline);
    };
    
    // Run at ~30fps
    const intervalId = setInterval(() => {
      const newState = hocusPatternPipeline.step();
      setState(newState);
      drawFieldVisualization();
    }, 33);
    
    return () => {
      clearInterval(intervalId);
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, []);
  
  const drawFieldVisualization = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    const history = hocusPatternPipeline.getFieldHistory();
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear with dark background
    ctx.fillStyle = 'hsl(222, 47%, 8%)';
    ctx.fillRect(0, 0, width, height);
    
    if (history.length < 2) return;
    
    // Draw field waveform
    ctx.beginPath();
    ctx.strokeStyle = 'hsl(142, 76%, 50%)';
    ctx.lineWidth = 2;
    
    const scale = height / 4;
    const step = width / Math.min(history.length, 200);
    
    for (let i = 0; i < history.length; i++) {
      const x = i * step;
      const y = height / 2 - history[i] * scale;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    
    // Draw mode contributions as colored overlays
    const state = hocusPatternPipeline.getState();
    if (state) {
      const colors = [
        'hsla(0, 76%, 50%, 0.3)',   // Mode 0 - red
        'hsla(45, 76%, 50%, 0.3)',  // Mode 1 - orange
        'hsla(142, 76%, 50%, 0.3)', // Mode 2 - green
        'hsla(200, 76%, 50%, 0.3)', // Mode 3 - blue
        'hsla(280, 76%, 50%, 0.3)'  // Mode 4 - purple
      ];
      
      state.modes.forEach((mode, idx) => {
        if (mode.isTemplate) {
          const modeHistory = hocusPatternPipeline.getModeHistory(idx);
          if (modeHistory.length < 2) return;
          
          ctx.beginPath();
          ctx.strokeStyle = colors[idx % colors.length];
          ctx.lineWidth = 1.5;
          
          for (let i = 0; i < modeHistory.length; i++) {
            const x = i * step;
            const y = height / 2 - modeHistory[i] * scale * 0.5;
            if (i === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
          }
          ctx.stroke();
        }
      });
    }
  };
  
  const getStageColor = (stage: string) => {
    switch (stage) {
      case 'HOCUS': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'PATTERN': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'TEMPLATE': return 'bg-green-500/20 text-green-400 border-green-500/50';
      default: return 'bg-muted text-muted-foreground';
    }
  };
  
  const getModeColor = (mode: ModeState) => {
    if (mode.isTemplate) return 'bg-green-500/20 text-green-400';
    if (mode.coherence > 0.5) return 'bg-yellow-500/20 text-yellow-400';
    return 'bg-red-500/20 text-red-400';
  };
  
  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-mono">
            Hocus → Pattern → Template Pipeline
          </CardTitle>
          {state && (
            <Badge className={getStageColor(state.pipelineStage)}>
              {state.pipelineStage}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Field Visualization */}
        <div className="rounded-lg overflow-hidden border border-border">
          <canvas 
            ref={canvasRef} 
            width={400} 
            height={120}
            className="w-full"
          />
        </div>
        
        {/* Pipeline Equations */}
        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="bg-muted/30 rounded p-2">
            <div className="text-muted-foreground mb-1">Stage 1: Pre-form</div>
            <div className="text-foreground">x(t+Δt) = x(t) + F(x)Δt + η(t)</div>
            {state && (
              <div className="text-primary mt-1">
                η = {state.noise.toFixed(4)}
              </div>
            )}
          </div>
          
          <div className="bg-muted/30 rounded p-2">
            <div className="text-muted-foreground mb-1">Stage 2: Feedback</div>
            <div className="text-foreground">x = (1-α)x + αx(t-τ)</div>
            {state && (
              <div className="text-primary mt-1">
                echo = {state.echoContribution.toFixed(4)}
              </div>
            )}
          </div>
          
          <div className="bg-muted/30 rounded p-2">
            <div className="text-muted-foreground mb-1">Stage 3: Modes</div>
            <div className="text-foreground">x(t) = Σₖ aₖ(t)φₖ</div>
            {state && (
              <div className="text-primary mt-1">
                modes = {state.modes.length}
              </div>
            )}
          </div>
          
          <div className="bg-muted/30 rounded p-2">
            <div className="text-muted-foreground mb-1">Stage 4: Coherence</div>
            <div className="text-foreground">Cₖ = |⟨aₖaₖ*⟩|/⟨|aₖ|²⟩</div>
            {state && (
              <div className="text-primary mt-1">
                Γ = {(state.totalCoherence * 100).toFixed(1)}%
              </div>
            )}
          </div>
        </div>
        
        {/* Mode States */}
        <div className="space-y-1">
          <div className="text-xs text-muted-foreground font-mono mb-2">
            Stage 5: Template Activation (θ = 0.7)
          </div>
          <div className="grid grid-cols-5 gap-1">
            {state?.modes.map((mode) => (
              <div 
                key={mode.k}
                className={`rounded p-2 text-center text-xs ${getModeColor(mode)}`}
              >
                <div className="font-mono font-bold">
                  φ{mode.k}
                </div>
                <div className="text-[10px] opacity-70">
                  {mode.frequency} Hz
                </div>
                <div className="font-mono mt-1">
                  C = {(mode.coherence * 100).toFixed(0)}%
                </div>
                <div className="text-[10px] mt-1">
                  T = {mode.isTemplate ? '1' : '0'}
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* Dominant Template */}
        {state && (
          <div className="bg-primary/10 rounded-lg p-3 border border-primary/30">
            <div className="text-xs text-muted-foreground font-mono mb-1">
              Stage 6: Dominant Template (k* = argmax Cₖ)
            </div>
            <div className="flex items-center justify-between">
              <div className="font-mono text-primary">
                k* = {state.dominantMode} ({state.modes[state.dominantMode]?.frequency} Hz)
              </div>
              <Badge variant="outline" className="font-mono">
                C = {(state.dominantCoherence * 100).toFixed(1)}%
              </Badge>
            </div>
            <div className="text-xs text-muted-foreground mt-2">
              Active Templates: {state.activeTemplates} / {state.modes.length}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default HocusPatternPipelineVisualizer;
