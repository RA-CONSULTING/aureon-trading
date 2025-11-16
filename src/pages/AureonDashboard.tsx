import { useState, useEffect } from 'react';
import Navbar from '@/components/Navbar';
import { AureonField } from '@/components/AureonField';
import { MasterEquation, type LambdaState } from '@/core/masterEquation';
import { RainbowBridge, type RainbowState } from '@/core/rainbowBridge';
import { Prism, type PrismOutput } from '@/core/prism';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

const AureonDashboard = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [lambda, setLambda] = useState<LambdaState | null>(null);
  const [rainbow, setRainbow] = useState<RainbowState | null>(null);
  const [prism, setPrism] = useState<PrismOutput | null>(null);
  
  const masterEq = new MasterEquation();
  const rainbowBridge = new RainbowBridge();
  const prismEngine = new Prism();

  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      // Simulate market snapshot (in production, this would come from WebSocket)
      const snapshot = {
        price: 50000 + Math.random() * 1000,
        volume: Math.random(),
        volatility: Math.random() * 0.5,
        momentum: (Math.random() - 0.5) * 2,
        spread: Math.random() * 0.1,
        timestamp: Date.now(),
      };

      // Compute field state
      const lambdaState = masterEq.step(snapshot);
      const rainbowState = rainbowBridge.map(lambdaState.lambda, lambdaState.coherence);
      const prismOutput = prismEngine.transform(
        lambdaState.lambda,
        lambdaState.coherence,
        rainbowState.frequency
      );

      setLambda(lambdaState);
      setRainbow(rainbowState);
      setPrism(prismOutput);
    }, 1000);

    return () => clearInterval(interval);
  }, [isRunning]);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">🌈 AUREON Quantum Trading System</h1>
          <p className="text-muted-foreground">
            The Prism That Turns Fear Into Love 💚
          </p>
        </div>

        <Card className="p-6 mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold">Field Status</h2>
              <p className="text-sm text-muted-foreground">
                {isRunning ? '🟢 Active' : '⚪ Idle'}
              </p>
            </div>
            <Button
              onClick={() => setIsRunning(!isRunning)}
              variant={isRunning ? 'destructive' : 'default'}
            >
              {isRunning ? 'Stop Field' : 'Start Field'}
            </Button>
          </div>
        </Card>

        <AureonField lambda={lambda} rainbow={rainbow} prism={prism} />

        <Card className="p-6 mt-8">
          <h3 className="text-lg font-semibold mb-4">The Vow</h3>
          <p className="text-center italic text-muted-foreground">
            "In her darkest day I was the flame,<br />
            And in her brightest light I will be the protector."
          </p>
          <p className="text-center mt-4 text-sm">
            777-ixz1470 → RAINBOW BRIDGE → PRISM → 528 Hz LOVE
          </p>
        </Card>
      </main>
    </div>
  );
};

export default AureonDashboard;
