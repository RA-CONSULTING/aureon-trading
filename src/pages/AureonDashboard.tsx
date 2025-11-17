import { useState, useEffect, useRef } from 'react';
import Navbar from '@/components/Navbar';
import { AureonField } from '@/components/AureonField';
import { SignalHistory } from '@/components/SignalHistory';
import { Watchlist } from '@/components/Watchlist';
import { TradingConfig } from '@/components/TradingConfig';
import { TradingDashboard } from '@/components/TradingDashboard';
import { TradingAnalytics } from '@/components/TradingAnalytics';
import { useAutoTrading } from '@/hooks/useAutoTrading';
import { MasterEquation, type LambdaState } from '@/core/masterEquation';
import { RainbowBridge, type RainbowState } from '@/core/rainbowBridge';
import { Prism, type PrismOutput } from '@/core/prism';
import { FTCPDetector, type CurvaturePoint } from '@/core/ftcpDetector';
import { LighthouseConsensus, type LighthouseState } from '@/core/lighthouseConsensus';
import { TradingSignalGenerator, type TradingSignal } from '@/core/tradingSignals';
import { BinanceWebSocketClient, type MarketData } from '@/core/binanceWebSocket';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { supabase } from '@/integrations/supabase/client';
import { useToast } from '@/hooks/use-toast';

const AureonDashboard = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [autoTradingEnabled, setAutoTradingEnabled] = useState(false);
  const [lambda, setLambda] = useState<LambdaState | null>(null);
  const [rainbow, setRainbow] = useState<RainbowState | null>(null);
  const [prism, setPrism] = useState<PrismOutput | null>(null);
  const [ftcpPoint, setFtcpPoint] = useState<CurvaturePoint | null>(null);
  const [lighthouse, setLighthouse] = useState<LighthouseState | null>(null);
  const [signal, setSignal] = useState<TradingSignal | null>(null);
  const [savedEventsCount, setSavedEventsCount] = useState(0);
  const [savedSignalsCount, setSavedSignalsCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [currentSymbol, setCurrentSymbol] = useState('BTCUSDT');
  const [selectedSymbol, setSelectedSymbol] = useState('btcusdt');
  const [currentPrice, setCurrentPrice] = useState(0);
  
  const { toast } = useToast();
  const masterEqRef = useRef(new MasterEquation());
  const rainbowBridgeRef = useRef(new RainbowBridge());
  const prismEngineRef = useRef(new Prism());
  const ftcpDetectorRef = useRef(new FTCPDetector());
  const lighthouseRef = useRef(new LighthouseConsensus());
  const signalGenRef = useRef(new TradingSignalGenerator());
  const binanceClientRef = useRef<BinanceWebSocketClient | null>(null);
  
  // Auto-trading hook
  useAutoTrading({
    isEnabled: autoTradingEnabled && isRunning,
    signal,
    lighthouse,
    prism,
    currentPrice,
    currentSymbol,
  });
  
  // Function to save Lighthouse Event to database
  const saveLighthouseEvent = async (
    lambdaState: LambdaState,
    lighthouseState: LighthouseState,
    prismOutput: PrismOutput
  ) => {
    try {
      const { data, error } = await supabase
        .from('lighthouse_events')
        .insert({
          timestamp: new Date().toISOString(),
          lambda_value: lambdaState.lambda,
          coherence: lambdaState.coherence,
          lighthouse_signal: lighthouseState.L,
          threshold: lighthouseState.threshold,
          confidence: lighthouseState.confidence,
          is_lhe: lighthouseState.isLHE,
          metric_clin: lighthouseState.metrics.Clin,
          metric_cnonlin: lighthouseState.metrics.Cnonlin,
          metric_cphi: lighthouseState.metrics.Cphi,
          metric_geff: lighthouseState.metrics.Geff,
          metric_q: lighthouseState.metrics.Q,
          dominant_node: lambdaState.dominantNode,
          prism_level: prismOutput.level,
          prism_state: prismOutput.state,
        })
        .select()
        .single();

      if (error) throw error;
      
      if (lighthouseState.isLHE) {
        setSavedEventsCount(prev => prev + 1);
      }
      
      return data?.id;
    } catch (error) {
      console.error('Error saving lighthouse event:', error);
      return null;
    }
  };

  // Function to save Trading Signal to database
  const saveTradingSignal = async (
    tradingSignal: TradingSignal,
    lighthouseEventId: string | null
  ) => {
    try {
      const { error } = await supabase
        .from('trading_signals')
        .insert({
          timestamp: new Date(tradingSignal.timestamp).toISOString(),
          signal_type: tradingSignal.type,
          strength: tradingSignal.strength,
          lighthouse_value: tradingSignal.lighthouse,
          coherence: tradingSignal.coherence,
          prism_level: tradingSignal.prismLevel,
          reason: tradingSignal.reason,
          lighthouse_event_id: lighthouseEventId,
        });

      if (error) throw error;
      
      setSavedSignalsCount(prev => prev + 1);
      
      // Show toast for optimal signals
      if (tradingSignal.type !== 'HOLD' && tradingSignal.strength > 0.7) {
        toast({
          title: `${tradingSignal.type} Signal Saved`,
          description: tradingSignal.reason,
          duration: 3000,
        });
      }
    } catch (error) {
      console.error('Error saving trading signal:', error);
    }
  };

  // Initialize Binance WebSocket when symbol changes
  useEffect(() => {
    // Disconnect existing client if any
    if (binanceClientRef.current) {
      binanceClientRef.current.disconnect();
    }

    const client = new BinanceWebSocketClient(selectedSymbol);
    binanceClientRef.current = client;

    client.onConnect(() => {
      setIsConnected(true);
      setCurrentSymbol(client.getSymbol());
      toast({
        title: '🌐 Connected to Binance',
        description: `Live ${client.getSymbol()} market data streaming`,
        duration: 3000,
      });
    });

    client.onError((error) => {
      console.error('Binance WebSocket error:', error);
      setIsConnected(false);
      toast({
        title: '⚠️ Connection Error',
        description: 'Lost connection to Binance. Retrying...',
        variant: 'destructive',
        duration: 3000,
      });
    });

    return () => {
      if (binanceClientRef.current) {
        binanceClientRef.current.disconnect();
      }
    };
  }, [selectedSymbol, toast]);

  // Process real-time market data
  const processMarketData = async (marketData: MarketData) => {
    // Update current price
    setCurrentPrice(marketData.price);

    // Compute field state
    const lambdaState = masterEqRef.current.step(marketData);
    const rainbowState = rainbowBridgeRef.current.map(lambdaState.lambda, lambdaState.coherence);
    const prismOutput = prismEngineRef.current.transform(
      lambdaState.lambda,
      lambdaState.coherence,
      rainbowState.frequency
    );

    // FTCP Detection
    const ftcpResult = ftcpDetectorRef.current.addPoint(marketData.timestamp, lambdaState.lambda);
    const Geff = ftcpDetectorRef.current.computeGeff();
    
    // Lighthouse Consensus
    const lighthouseState = lighthouseRef.current.validate(
      lambdaState.lambda,
      lambdaState.coherence,
      lambdaState.substrate,
      lambdaState.observer,
      lambdaState.echo,
      Geff,
      ftcpResult?.isFTCP || false
    );
    
    // Trading Signal Generation
    const tradingSignal = signalGenRef.current.generateSignal(
      lambdaState,
      lighthouseState,
      prismOutput
    );

    // Save to database
    let lighthouseEventId: string | null = null;
    
    if (lighthouseState.isLHE || marketData.timestamp % 10000 < 1000) {
      lighthouseEventId = await saveLighthouseEvent(lambdaState, lighthouseState, prismOutput);
    }
    
    await saveTradingSignal(tradingSignal, lighthouseEventId);

    // Update UI state
    setLambda(lambdaState);
    setRainbow(rainbowState);
    setPrism(prismOutput);
    setFtcpPoint(ftcpResult);
    setLighthouse(lighthouseState);
    setSignal(tradingSignal);
  };

  useEffect(() => {
    if (!isRunning || !binanceClientRef.current) return;

    // Start WebSocket connection
    if (!binanceClientRef.current.isConnected()) {
      binanceClientRef.current.connect();
    }

    // Set up data handler
    binanceClientRef.current.onData(processMarketData);

    return () => {
      // Keep connection alive but stop processing
      if (binanceClientRef.current) {
        binanceClientRef.current.onData(() => {});
      }
    };
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
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <h2 className="text-xl font-semibold">Field Status</h2>
                <Select 
                  value={selectedSymbol} 
                  onValueChange={setSelectedSymbol}
                  disabled={isRunning}
                >
                  <SelectTrigger className="w-[180px]">
                    <SelectValue placeholder="Select pair" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="btcusdt">BTC/USDT</SelectItem>
                    <SelectItem value="ethusdt">ETH/USDT</SelectItem>
                    <SelectItem value="bnbusdt">BNB/USDT</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex items-center gap-4 mt-1">
                <p className="text-sm text-muted-foreground">
                  {isRunning ? '🟢 Active - Live Market Data' : '⚪ Idle'}
                </p>
                {isConnected && (
                  <Badge style={{ backgroundColor: '#00FF88' }}>
                    Connected: {currentSymbol}
                  </Badge>
                )}
                {!isConnected && isRunning && (
                  <Badge variant="destructive">Connecting...</Badge>
                )}
              </div>
              {isRunning && (
                <div className="mt-2 flex gap-4 text-xs">
                  <span className="text-muted-foreground">
                    💰 Price: <strong>${currentPrice.toFixed(2)}</strong>
                  </span>
                  <span className="text-muted-foreground">
                    📊 LHEs: <strong>{savedEventsCount}</strong>
                  </span>
                  <span className="text-muted-foreground">
                    📈 Signals: <strong>{savedSignalsCount}</strong>
                  </span>
                </div>
              )}
            </div>
            <Button
              onClick={() => setIsRunning(!isRunning)}
              variant={isRunning ? 'destructive' : 'default'}
            >
              {isRunning ? 'Stop Field' : 'Start Field'}
            </Button>
          </div>
        </Card>

        {/* Trading Signal Card */}
        {signal && (
          <Card className="p-6 mb-8 border-2" style={{
            borderColor: signal.type === 'LONG' ? '#00FF88' : signal.type === 'SHORT' ? '#FF6B35' : '#888'
          }}>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold">
                  {signal.type === 'LONG' && '📈 LONG SIGNAL'}
                  {signal.type === 'SHORT' && '📉 SHORT SIGNAL'}
                  {signal.type === 'HOLD' && '⏸️ HOLD'}
                </h2>
                <p className="text-sm text-muted-foreground mt-1">{signal.reason}</p>
              </div>
              <div className="text-right">
                <p className="text-sm text-muted-foreground">Signal Strength</p>
                <p className="text-3xl font-bold">{(signal.strength * 100).toFixed(0)}%</p>
              </div>
            </div>
            <Progress value={signal.strength * 100} className="h-3" />
          </Card>
        )}

        {/* Lighthouse Consensus Card */}
        {lighthouse && (
          <Card className="p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">🔦 Lighthouse Consensus</h3>
                <p className="text-sm text-muted-foreground">
                  Multi-Metric Validation (QGITA Framework)
                </p>
              </div>
              {lighthouse.isLHE && (
                <Badge className="text-lg px-4 py-2" style={{ backgroundColor: '#00FF88' }}>
                  🎯 LHE DETECTED
                </Badge>
              )}
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p className="text-sm text-muted-foreground">L(t) Signal</p>
                <p className="text-2xl font-bold">{lighthouse.L.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Threshold (μ + 2σ)</p>
                <p className="text-xl font-mono">{lighthouse.threshold.toFixed(3)}</p>
              </div>
            </div>

            <div className="grid grid-cols-5 gap-3">
              <div className="text-center">
                <p className="text-xs font-medium">Cₗᵢₙ</p>
                <p className="text-sm font-mono">{lighthouse.metrics.Clin.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs font-medium">Cₙₒₙₗᵢₙ</p>
                <p className="text-sm font-mono">{lighthouse.metrics.Cnonlin.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs font-medium">Cφ</p>
                <p className="text-sm font-mono">{lighthouse.metrics.Cphi.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs font-medium">Gₑff</p>
                <p className="text-sm font-mono">{lighthouse.metrics.Geff.toFixed(2)}</p>
              </div>
              <div className="text-center">
                <p className="text-xs font-medium">|Q|</p>
                <p className="text-sm font-mono">{Math.abs(lighthouse.metrics.Q).toFixed(2)}</p>
              </div>
            </div>
          </Card>
        )}

        {/* FTCP Detection Card */}
        {ftcpPoint && (
          <Card className="p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold">📐 FTCP Detection</h3>
                <p className="text-sm text-muted-foreground">
                  Fibonacci-Tightened Curvature Points
                </p>
              </div>
              {ftcpPoint.isFTCP && (
                <Badge className="text-lg px-4 py-2" style={{ backgroundColor: '#FFD700' }}>
                  ✨ FTCP FOUND
                </Badge>
              )}
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <p className="text-sm text-muted-foreground">Curvature</p>
                <p className="text-xl font-mono">{ftcpPoint.curvature.toFixed(3)}</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Golden Ratio Score</p>
                <p className="text-xl font-mono">{(ftcpPoint.goldenRatioScore * 100).toFixed(0)}%</p>
              </div>
              <div>
                <p className="text-sm text-muted-foreground">φ (1.618...)</p>
                <p className="text-xl font-mono">1.618</p>
              </div>
            </div>
          </Card>
        )}

        <div className="mb-8">
          <TradingConfig />
        </div>

        <div className="mb-8">
          <TradingDashboard />
        </div>

        <div className="mb-8">
          <TradingAnalytics />
        </div>

        <div className="mb-8">
          <Watchlist />
        </div>

        <AureonField lambda={lambda} rainbow={rainbow} prism={prism} />

        <div className="mt-8">
          <SignalHistory />
        </div>

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
