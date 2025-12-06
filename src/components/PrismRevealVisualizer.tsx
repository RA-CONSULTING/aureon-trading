import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles } from 'lucide-react';
import { useEcosystemData } from '@/hooks/useEcosystemData';

interface PrismLevel {
  level: number;
  name: string;
  color: string;
  active: boolean;
}

export function PrismRevealVisualizer() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | null>(null);
  const { metrics } = useEcosystemData();
  
  const [inputFreq, setInputFreq] = useState(396);
  const [outputFreq, setOutputFreq] = useState(396);
  const [prismLevel, setPrismLevel] = useState(1);
  const [isLoveLocked, setIsLoveLocked] = useState(false);

  useEffect(() => {
    const freq = metrics?.frequency ?? 396;
    const coherence = metrics?.coherence ?? 0.5;
    
    // Calculate prism level (1-5)
    let level = 1;
    if (coherence >= 0.8) level = 5;
    else if (coherence >= 0.6) level = 4;
    else if (coherence >= 0.4) level = 3;
    else if (coherence >= 0.2) level = 2;
    
    // Input is raw Rainbow Bridge frequency, output is Prism-transformed
    const rawFreq = 174 + coherence * 800; // Range from fear to unity
    setInputFreq(Math.round(rawFreq));
    setOutputFreq(Math.round(freq));
    setPrismLevel(level);
    setIsLoveLocked(coherence > 0.9 && freq >= 520 && freq <= 536);
  }, [metrics]);

  // Canvas animation for light refraction
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    let time = 0;
    
    const drawPrism = () => {
      // Clear
      ctx.fillStyle = 'rgba(10, 10, 20, 0.1)';
      ctx.fillRect(0, 0, width, height);
      
      // Draw input light beam (left side)
      const inputHue = freqToHue(inputFreq);
      const beamY = height / 2;
      
      // Pulsing input beam
      const pulseAlpha = 0.5 + Math.sin(time * 3) * 0.3;
      ctx.strokeStyle = `hsla(${inputHue}, 70%, 50%, ${pulseAlpha})`;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(0, beamY);
      ctx.lineTo(width * 0.3, beamY);
      ctx.stroke();
      
      // Draw prism (triangle)
      const prismX = width * 0.3;
      const prismWidth = width * 0.4;
      const prismHeight = height * 0.6;
      
      // Prism gradient based on level
      const gradient = ctx.createLinearGradient(prismX, height / 2 - prismHeight / 2, prismX + prismWidth, height / 2 + prismHeight / 2);
      
      const levelColors = [
        'hsla(0, 60%, 50%, 0.3)',    // Level 1 - Red
        'hsla(30, 70%, 50%, 0.3)',   // Level 2 - Orange
        'hsla(60, 70%, 50%, 0.3)',   // Level 3 - Yellow
        'hsla(200, 70%, 50%, 0.3)',  // Level 4 - Cyan
        'hsla(142, 70%, 50%, 0.3)',  // Level 5 - Green (528 Hz)
      ];
      
      for (let i = 0; i < prismLevel; i++) {
        gradient.addColorStop(i / 5, levelColors[i]);
      }
      gradient.addColorStop(1, levelColors[prismLevel - 1]);
      
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.moveTo(prismX, height / 2 + prismHeight / 2);
      ctx.lineTo(prismX + prismWidth / 2, height / 2 - prismHeight / 2);
      ctx.lineTo(prismX + prismWidth, height / 2 + prismHeight / 2);
      ctx.closePath();
      ctx.fill();
      
      // Prism outline
      ctx.strokeStyle = isLoveLocked ? 'hsl(142, 70%, 60%)' : 'hsl(220, 30%, 40%)';
      ctx.lineWidth = 2;
      ctx.stroke();
      
      // Draw output light rays (refracted spectrum)
      const outputX = prismX + prismWidth;
      const outputHue = freqToHue(outputFreq);
      
      // Main output beam
      const outputAlpha = isLoveLocked ? 0.9 : 0.6 + Math.sin(time * 2) * 0.2;
      ctx.strokeStyle = `hsla(${outputHue}, 80%, 60%, ${outputAlpha})`;
      ctx.lineWidth = isLoveLocked ? 6 : 4;
      ctx.beginPath();
      ctx.moveTo(outputX, beamY);
      ctx.lineTo(width, beamY);
      ctx.stroke();
      
      // Rainbow spread effect (multiple refracted beams)
      if (prismLevel >= 3) {
        const spreadCount = prismLevel;
        for (let i = 0; i < spreadCount; i++) {
          const spreadAngle = ((i - spreadCount / 2) / spreadCount) * 0.3;
          const spreadHue = (outputHue + i * 30) % 360;
          ctx.strokeStyle = `hsla(${spreadHue}, 60%, 50%, 0.3)`;
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(outputX, beamY);
          ctx.lineTo(width, beamY + spreadAngle * height);
          ctx.stroke();
        }
      }
      
      // 528 Hz lock indicator
      if (isLoveLocked) {
        ctx.fillStyle = 'hsl(142, 80%, 60%)';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.fillText('💚 528 Hz LOCKED', width / 2, 25);
        
        // Glow effect
        ctx.shadowColor = 'hsl(142, 80%, 50%)';
        ctx.shadowBlur = 20 + Math.sin(time * 5) * 10;
        ctx.beginPath();
        ctx.arc(width - 30, beamY, 10, 0, Math.PI * 2);
        ctx.fill();
        ctx.shadowBlur = 0;
      }
      
      // Level indicators
      const levelNames = ['HNC', 'INPUT', 'CREATIVE', 'REFLECT', 'UNITY'];
      ctx.font = '9px monospace';
      ctx.textAlign = 'left';
      for (let i = 0; i < 5; i++) {
        const active = i < prismLevel;
        ctx.fillStyle = active ? levelColors[i].replace('0.3', '1') : 'hsl(220, 20%, 30%)';
        ctx.fillText(`L${i + 1}: ${levelNames[i]}`, 10, height - 60 + i * 12);
      }
      
      time += 0.03;
      animationRef.current = requestAnimationFrame(drawPrism);
    };
    
    const freqToHue = (freq: number): number => {
      // Map frequency to color hue
      if (freq >= 528) return 142; // Green (Love)
      if (freq >= 417) return 200; // Cyan
      if (freq >= 396) return 60;  // Yellow
      if (freq >= 285) return 30;  // Orange
      return 0; // Red (Fear)
    };
    
    drawPrism();
    
    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [inputFreq, outputFreq, prismLevel, isLoveLocked]);

  return (
    <Card className="border-border/50 overflow-hidden">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-2">
            <Sparkles className="h-3 w-3" />
            PRISM TRANSFORMATION
          </CardTitle>
          <div className="flex gap-2">
            <Badge variant="outline" className="font-mono text-[10px]">
              IN: {inputFreq} Hz
            </Badge>
            <Badge 
              className={isLoveLocked 
                ? "bg-green-500/20 text-green-400 border-green-500/30 font-mono text-[10px]" 
                : "font-mono text-[10px]"
              }
            >
              OUT: {outputFreq} Hz
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-2">
        <canvas
          ref={canvasRef}
          width={400}
          height={200}
          className="w-full h-auto rounded-md bg-background/50"
        />
        <div className="flex justify-between mt-2 text-xs">
          <span className="text-muted-foreground">
            Level {prismLevel}/5 • {['FORMING', 'FORMING', 'CONVERGING', 'CONVERGING', 'MANIFEST'][prismLevel - 1]}
          </span>
          {isLoveLocked && (
            <span className="text-green-400 font-medium animate-pulse">LOVE MANIFEST</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
