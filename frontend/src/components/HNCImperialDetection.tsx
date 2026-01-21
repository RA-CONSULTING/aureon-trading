import { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { HNCImperialDetector, HNC_FREQUENCIES, CRITICAL_MASS } from '@/core/hncImperialDetector';
import { temporalLadder, SYSTEMS } from '@/core/temporalLadder';
import { useBasicEcosystemMetrics, useHarmonicMetrics } from '@/hooks/useEcosystemData';
import { Radio } from 'lucide-react';

interface LogEntry {
  message: string;
  type: 'default' | 'success' | 'fail' | 'warning';
  timestamp: Date;
}

const HNCImperialDetection = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [status, setStatus] = useState<'STANDBY' | 'ACTIVE SCAN' | 'BRIDGE OPEN'>('STANDBY');
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [frequencies, setFrequencies] = useState({
    '7.83': false,
    '256': false,
    '528': false,
    '963': false,
    '440': false
  });
  const [imperialYield, setImperialYield] = useState(0);
  const [harmonicFidelity, setHarmonicFidelity] = useState(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const logContainerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();
  const spectrogramDataRef = useRef<number[][]>([]);

  // Use real ecosystem data
  const basicMetrics = useBasicEcosystemMetrics();
  const harmonicMetrics = useHarmonicMetrics();
  const coherence = basicMetrics.coherence;
  const lambda = basicMetrics.frequency / 528; // Normalize frequency as lambda proxy
  const resonance = harmonicMetrics.harmonicFidelity;
  const dimensionalCoherence = harmonicMetrics.coherence;

  const detector = new HNCImperialDetector();

  // Update imperial yield and fidelity from real ecosystem data
  useEffect(() => {
    if (status === 'BRIDGE OPEN') {
      // Use real coherence to modulate the yield display
      const realYield = CRITICAL_MASS * coherence;
      setImperialYield(realYield);
      setHarmonicFidelity(dimensionalCoherence * 100);
    }
  }, [coherence, dimensionalCoherence, status]);

  // Register with Temporal Ladder on mount
  useEffect(() => {
    temporalLadder.registerSystem(SYSTEMS.HARMONIC_NEXUS);
    console.log('🌈 HNC Imperial Detection connected to Temporal Ladder');
    
    const heartbeatInterval = setInterval(() => {
      const health = status === 'BRIDGE OPEN' ? 1.0 : status === 'ACTIVE SCAN' ? 0.8 : 0.6;
      temporalLadder.heartbeat(SYSTEMS.HARMONIC_NEXUS, health);
    }, 2000);

    return () => {
      clearInterval(heartbeatInterval);
      temporalLadder.unregisterSystem(SYSTEMS.HARMONIC_NEXUS);
    };
  }, [status]);

  // Auto-scroll logs
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Initialize canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    ctx.fillStyle = 'hsl(120 100% 5%)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
  }, []);

  const log = (message: string, type: LogEntry['type'] = 'default') => {
    setLogs(prev => [...prev, { message, type, timestamp: new Date() }]);
  };

  const wait = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

  const activateFrequency = (freq: string) => {
    setFrequencies(prev => ({ ...prev, [freq]: true }));
  };

  const nullifyFrequency = (freq: string) => {
    setFrequencies(prev => ({ ...prev, [freq]: true }));
  };

  const animateYieldCounter = async (target: number) => {
    const duration = 2000;
    const steps = 50;
    const increment = target / steps;
    
    for (let i = 0; i <= steps; i++) {
      setImperialYield(increment * i);
      await wait(duration / steps);
    }
  };

  const drawSpectrogram = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;

    // Use real coherence to influence spectrum intensity
    const baseIntensity = coherence * 100;
    const spectrumSize = 256;
    const spectrum = new Array(spectrumSize).fill(0).map(() => baseIntensity + Math.random() * 50);
    
    // Add frequency peaks based on real resonance
    if (frequencies['7.83']) spectrum[10] = 100 + resonance * 100;
    if (frequencies['528']) spectrum[128] = 120 + resonance * 80;
    if (frequencies['963']) spectrum[230] = 140 + resonance * 60;

    spectrogramDataRef.current.unshift(spectrum);
    if (spectrogramDataRef.current.length > height) {
      spectrogramDataRef.current.pop();
    }

    ctx.fillStyle = 'hsl(120 100% 5%)';
    ctx.fillRect(0, 0, width, height);

    spectrogramDataRef.current.forEach((row, y) => {
      row.forEach((value, x) => {
        const intensity = Math.min(255, value);
        let color;
        
        if (intensity > 150) {
          color = `hsl(180 100% ${intensity / 4}%)`;
        } else if (intensity > 100) {
          color = `hsl(120 100% ${intensity / 5}%)`;
        } else {
          color = `hsl(0 100% ${intensity / 6}%)`;
        }
        
        ctx.fillStyle = color;
        ctx.fillRect((x / spectrumSize) * width, y, width / spectrumSize, 1);
      });
    });

    ctx.fillStyle = 'hsl(120 100% 60%)';
    ctx.font = '10px monospace';
    ctx.fillText('963Hz UNITY', 10, 20);
    ctx.fillText('528Hz LOVE', 10, height / 2);
    ctx.fillText('7.83Hz SCHUMANN', 10, height - 10);

    if (isRunning) {
      animationRef.current = requestAnimationFrame(drawSpectrogram);
    }
  };

  const runSequence = async () => {
    setIsRunning(true);
    setStatus('ACTIVE SCAN');
    setLogs([]);
    setFrequencies({ '7.83': false, '256': false, '528': false, '963': false, '440': false });
    setImperialYield(0);
    setHarmonicFidelity(0);

    drawSpectrogram();

    log(`HNC IMPERIAL DETECTION v8.${detector.getGuardianId()}`);
    log(`GUARDIAN ID: ${detector.getGuardianId()}`);
    log(`LIVE COHERENCE: Γ = ${coherence.toFixed(3)}`);
    log("INITIATING IMPERIAL SCAN...");
    await wait(1500);

    log("LOADING VISUALS NEXUS⁵ DATASET...", "warning");
    await wait(1000);

    log("EXTRACTING FREQUENCY COMB...", "warning");
    await wait(800);

    log("DETECTED 7.83 Hz [SCHUMANN HEARTBEAT]", "success");
    activateFrequency('7.83');
    await wait(800);

    log("DETECTED 256 Hz [SCIENTIFIC ROOT]", "success");
    activateFrequency('256');
    await wait(800);

    log("DETECTED 528 Hz [DNA REPAIR / LOVE]", "success");
    activateFrequency('528');
    await wait(800);

    log("DETECTED 963 Hz [UNITY CROWN]", "success");
    activateFrequency('963');
    await wait(1000);

    log("ANALYZING 440 Hz DISTORTION GRID...");
    await wait(1000);
    log("440 Hz AMPLITUDE: < 0.01% (NULLIFIED)", "success");
    nullifyFrequency('440');
    await wait(500);

    log("PHASE SPACE RECONSTRUCTION: 6D FISH DETECTED");
    await wait(800);

    log("CALCULATING IMPERIAL YIELD...");
    await animateYieldCounter(CRITICAL_MASS * coherence);
    setHarmonicFidelity(dimensionalCoherence * 100);
    await wait(500);

    log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");
    log("IMPERIAL YIELD: CRITICAL MASS REACHED", "success");
    log("SIGNAL ZERO PROTOCOL: EXECUTED", "success");
    log("DIMENSIONAL FISSION: COMPLETE", "success");
    log("THE RAINBOW BRIDGE IS OPEN", "success");
    log("THE LIGHTHOUSE IS ON", "success");
    log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━");

    setStatus('BRIDGE OPEN');
    setIsRunning(false);
    
    temporalLadder.broadcast(SYSTEMS.HARMONIC_NEXUS, 'BRIDGE_OPENED', {
      imperialYield: CRITICAL_MASS * coherence,
      harmonicFidelity: dimensionalCoherence * 100,
      liveCoherence: coherence,
      timestamp: Date.now()
    });
  };

  const getStatusColor = () => {
    switch (status) {
      case 'STANDBY': return 'hsl(180 100% 50%)';
      case 'ACTIVE SCAN': return 'hsl(45 100% 51%)';
      case 'BRIDGE OPEN': return 'hsl(120 100% 60%)';
    }
  };

  const getLogColor = (type: LogEntry['type']) => {
    switch (type) {
      case 'success': return 'text-[hsl(180_100%_60%)]';
      case 'fail': return 'text-[hsl(0_100%_60%)]';
      case 'warning': return 'text-[hsl(45_100%_60%)]';
      default: return 'text-[hsl(120_100%_60%)]';
    }
  };

  return (
    <div className="container mx-auto p-4 max-w-7xl">
      <Card className="hnc-terminal hnc-crt relative overflow-hidden border-[hsl(120_100%_30%)]">
        <div className="hnc-scan-line" />
        
        {/* Header */}
        <div className="border-b border-[hsl(120_100%_20%)] p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Radio className="h-6 w-6 hnc-text-glow" />
              <h1 
                className="text-2xl font-bold hnc-glitch hnc-text-glow" 
                data-text="HNC IMPERIAL DETECTION"
              >
                HNC IMPERIAL DETECTION
              </h1>
            </div>
            <div className="text-right">
              <div className="text-sm opacity-70">TEMPLATE v8.02111991</div>
              <div className="text-sm">LIVE Γ: {coherence.toFixed(3)} | Λ: {lambda.toFixed(3)}</div>
              <div className="flex items-center gap-2 justify-end mt-1">
                <span className="text-sm">STATUS:</span>
                <div 
                  className="px-2 py-1 text-xs font-bold border"
                  style={{ 
                    color: getStatusColor(),
                    borderColor: getStatusColor(),
                    boxShadow: `0 0 10px ${getStatusColor()}`
                  }}
                >
                  {status}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-2 gap-4 p-4">
          {/* Left: Spectrogram */}
          <div className="space-y-4">
            <div className="border border-[hsl(120_100%_20%)] p-2">
              <div className="text-sm font-bold mb-2 hnc-text-glow">VISUALS NEXUS⁵ FEED</div>
              <canvas 
                ref={canvasRef}
                className="w-full h-64 border border-[hsl(120_100%_15%)]"
              />
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="border border-[hsl(120_100%_20%)] p-3">
                <div className="text-xs opacity-70 mb-1">IMPERIAL YIELD</div>
                <div className="text-2xl font-bold hnc-text-glow">
                  {imperialYield.toExponential(2)}
                </div>
                <div className="text-xs opacity-70">PLANCK UNITS</div>
              </div>
              <div className="border border-[hsl(120_100%_20%)] p-3">
                <div className="text-xs opacity-70 mb-1">HARMONIC</div>
                <div className="text-2xl font-bold hnc-text-glow">
                  {harmonicFidelity.toFixed(0)}%
                </div>
                <div className="text-xs opacity-70">FIDELITY</div>
              </div>
            </div>

            <Button
              onClick={runSequence}
              disabled={isRunning}
              className="w-full bg-[hsl(120_100%_20%)] hover:bg-[hsl(120_100%_25%)] border-2 border-[hsl(120_100%_40%)] text-[hsl(120_100%_60%)] font-bold py-6 hnc-text-glow"
            >
              {isRunning ? '[ SCANNING... ]' : status === 'BRIDGE OPEN' ? '[ SEQUENCE COMPLETE ]' : '[ INITIATE SEQUENCE ]'}
            </Button>
          </div>

          {/* Right: Terminal Log */}
          <div className="space-y-4">
            <div className="border border-[hsl(120_100%_20%)] p-2 h-96 overflow-hidden flex flex-col">
              <div className="text-sm font-bold mb-2 hnc-text-glow">TERMINAL OUTPUT</div>
              <div 
                ref={logContainerRef}
                className="flex-1 overflow-y-auto font-mono text-xs space-y-1"
              >
                {logs.map((entry, i) => (
                  <div key={i} className={getLogColor(entry.type)}>
                    <span className="opacity-50">&gt; </span>
                    {entry.message}
                  </div>
                ))}
              </div>
            </div>

            {/* Frequency Dashboard */}
            <div className="border border-[hsl(120_100%_20%)] p-3">
              <div className="text-sm font-bold mb-3 hnc-text-glow">FREQUENCY DETECTION</div>
              <div className="grid grid-cols-5 gap-2">
                {Object.entries(frequencies).map(([freq, active]) => (
                  <div 
                    key={freq}
                    className={`border p-2 text-center ${
                      active 
                        ? freq === '440' 
                          ? 'border-[hsl(0_100%_50%)] bg-[hsl(0_100%_10%)]' 
                          : 'border-[hsl(120_100%_50%)] bg-[hsl(120_100%_15%)]'
                        : 'border-[hsl(120_100%_20%)] opacity-40'
                    }`}
                  >
                    <div className={`text-lg font-bold ${freq === '440' && active ? 'line-through' : ''}`}>
                      {freq}
                    </div>
                    <div className="text-[8px] opacity-70">Hz</div>
                    {active && (
                      <div className={`text-[10px] mt-1 ${freq === '440' ? 'text-[hsl(0_100%_60%)]' : 'text-[hsl(120_100%_60%)]'}`}>
                        {freq === '440' ? 'NULLIFIED' : '✓ DETECTED'}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default HNCImperialDetection;
