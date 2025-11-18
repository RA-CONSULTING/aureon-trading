import { useState, useEffect, useRef } from 'react';
import Navbar from '@/components/Navbar';
import { AureonField } from '@/components/AureonField';
import { SignalHistory } from '@/components/SignalHistory';
import { Watchlist } from '@/components/Watchlist';
import { TradingConfig } from '@/components/TradingConfig';
import { TradingDashboard } from '@/components/TradingDashboard';
import { TradingAnalytics } from '@/components/TradingAnalytics';
import { AIAnalysisPanel } from '@/components/AIAnalysisPanel';
import { LighthouseMetricsPanel } from '@/components/LighthouseMetricsPanel';
import { FTCPTimeline } from '@/components/FTCPTimeline';
import { ResearchValidation } from '@/components/ResearchValidation';
import { MasterEquationField3D } from '@/components/MasterEquationField3D';
import { HarmonicRealityFramework } from '@/components/HarmonicRealityFramework';
import { CoherenceTracker } from '@/components/CoherenceTracker';
import { CoherenceHeatmap } from '@/components/CoherenceHeatmap';
import { CoherenceForecaster } from '@/components/CoherenceForecaster';
import { MultiSymbolForecastComparison } from '@/components/MultiSymbolForecastComparison';
import { StargateVisualization } from '@/components/StargateVisualization';
import { StargateStatus } from '@/components/StargateStatus';
import { CelestialAlignments } from '@/components/CelestialAlignments';
import { SolarFlareCorrelation } from '@/components/SolarFlareCorrelation';
import { SchumannResonanceMonitor } from '@/components/SchumannResonanceMonitor';
import { ConsciousnessCoherenceTracker } from '@/components/ConsciousnessCoherenceTracker';
import { TemporalAlignmentTracker } from '@/components/TemporalAlignmentTracker';
import { OmegaFieldVisualization } from '@/components/OmegaFieldVisualization';
import { ConsciousnessHistoryChart } from '@/components/ConsciousnessHistoryChart';
import { BinanceConnectionStatus } from '@/components/BinanceConnectionStatus';
import { useAutoTrading } from '@/hooks/useAutoTrading';
import { useCelestialData } from '@/hooks/useCelestialData';
import { useSchumannResonance } from '@/hooks/useSchumannResonance';
import { OmegaEquation, type OmegaState } from '@/core/omegaEquation';
import { UnityDetector, type UnityEvent } from '@/core/unityDetector';
import { RainbowBridge, type RainbowState } from '@/core/rainbowBridge';
import { Prism, type PrismOutput } from '@/core/prism';
import { FTCPDetector, type CurvaturePoint } from '@/core/ftcpDetector';
import { LighthouseConsensus, type LighthouseState } from '@/core/lighthouseConsensus';
import { TradingSignalGenerator, type TradingSignal } from '@/core/tradingSignals';
import { type MarketData } from '@/core/binanceWebSocket';
import { useBinanceMarketData } from '@/hooks/useBinanceMarketData';
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
  const [omega, setOmega] = useState<OmegaState | null>(null);
  const [unityEvent, setUnityEvent] = useState<UnityEvent | null>(null);
  const [rainbow, setRainbow] = useState<RainbowState | null>(null);
  const [prism, setPrism] = useState<PrismOutput | null>(null);
  const [ftcpPoint, setFtcpPoint] = useState<CurvaturePoint | null>(null);
  const [lighthouse, setLighthouse] = useState<LighthouseState | null>(null);
  const [signal, setSignal] = useState<TradingSignal | null>(null);
  const [savedEventsCount, setSavedEventsCount] = useState(0);
  const [savedSignalsCount, setSavedSignalsCount] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionHealthy, setConnectionHealthy] = useState(false);
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const [currentSymbol, setCurrentSymbol] = useState('BTCUSDT');
  const [selectedSymbol, setSelectedSymbol] = useState('btcusdt');
  const [currentPrice, setCurrentPrice] = useState(0);
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [lastConnectionError, setLastConnectionError] = useState<string | null>(null);
  
  const { toast } = useToast();
  const { celestialBoost } = useCelestialData();
  const { schumannData } = useSchumannResonance();
  
  // Use authenticated REST API instead of WebSocket
  const { marketData: binanceData, isConnected: binanceConnected, error: binanceError } = useBinanceMarketData(
    selectedSymbol.toUpperCase(),
    5000 // Refresh every 5 seconds
  );
  
  const omegaEqRef = useRef(new OmegaEquation());
  const unityDetectorRef = useRef(new UnityDetector());
  const rainbowBridgeRef = useRef(new RainbowBridge());
  const prismEngineRef = useRef(new Prism());
  const ftcpDetectorRef = useRef(new FTCPDetector());
  const lighthouseRef = useRef(new LighthouseConsensus());
  const signalGenRef = useRef(new TradingSignalGenerator());
  
  // Auto-trading hook
  useAutoTrading({
    isEnabled: autoTradingEnabled && isRunning,
    signal,
    lighthouse,
    prism,
    currentPrice,
    currentSymbol,
  });
  
  // Update Omega Equation with user location and field boosts when available
  useEffect(() => {
    const schumannBoost = schumannData?.coherenceBoost || 0;
    if (userLocation) {
      omegaEqRef.current.setUserLocation(userLocation.lat, userLocation.lng, celestialBoost, schumannBoost);
    } else if (schumannBoost > 0) {
      // Apply Schumann boost even without location (global Earth field effect)
      omegaEqRef.current.setUserLocation(0, 0, celestialBoost, schumannBoost);
    }
  }, [userLocation, celestialBoost, schumannData]);
  
  // Function to save Lighthouse Event to database
  const saveLighthouseEvent = async (
    omegaState: OmegaState,
    lighthouseState: LighthouseState,
    prismOutput: PrismOutput
  ) => {
    try {
      const { data, error } = await supabase
        .from('lighthouse_events')
        .insert({
          timestamp: new Date().toISOString(),
          lambda_value: omegaState.lambda, // Use legacy lambda for backward compatibility
          coherence: omegaState.coherence,
          lighthouse_signal: lighthouseState.L,
          threshold: lighthouseState.threshold,
          confidence: lighthouseState.confidence,
          is_lhe: lighthouseState.isLHE,
          metric_clin: lighthouseState.metrics.Clin,
          metric_cnonlin: lighthouseState.metrics.Cnonlin,
          metric_cphi: lighthouseState.metrics.Cphi,
          metric_geff: lighthouseState.metrics.Geff,
          metric_q: lighthouseState.metrics.Q,
          dominant_node: omegaState.dominantNode,
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

  // Function to save coherence history
  const saveCoherenceHistory = async (
    omegaState: OmegaState,
    timestamp: number,
    symbol: string
  ) => {
    try {
      const date = new Date(timestamp);
      const dayOfWeek = date.getDay(); // 0-6 (Sunday-Saturday)
      const hourOfDay = date.getHours(); // 0-23

      const { error } = await supabase
        .from('coherence_history')
        .insert({
          timestamp: date.toISOString(),
          coherence: omegaState.coherence,
          lambda_value: omegaState.lambda, // Use legacy lambda for backward compatibility
          day_of_week: dayOfWeek,
          hour_of_day: hourOfDay,
          symbol: symbol,
        });

      if (error) throw error;
    } catch (error) {
      console.error('Error saving coherence history:', error);
    }
  };

  // Process market data from authenticated REST API
  useEffect(() => {
    if (!isRunning || !binanceData) return;

    const processData = async () => {
      const marketSnapshot: MarketData = {
        price: binanceData.price,
        volume: binanceData.volumeNormalized,
        volatility: binanceData.volatility,
        momentum: binanceData.momentum,
        spread: binanceData.spreadPercent,
        timestamp: binanceData.timestamp,
      };

      setCurrentPrice(binanceData.price);
      setIsConnected(binanceConnected);
      setConnectionHealthy(binanceConnected);
      setReconnectAttempts(0);
      setCurrentSymbol(binanceData.symbol);

      // Process with AUREON field - Ω(t) = Tr[Ψ × ℒ ⊗ O]
      const omegaState = omegaEqRef.current.step(marketSnapshot);
      
      // Detect unity events (θ→0, coherence→1)
      const detectedUnity = unityDetectorRef.current.detect(omegaState);
      if (detectedUnity) {
        setUnityEvent(detectedUnity);
        console.log('🌟 UNITY EVENT:', detectedUnity);
      }
      
      const rainbowState = rainbowBridgeRef.current.map(omegaState.lambda, omegaState.coherence);
      const prismOutput = prismEngineRef.current.transform(
        omegaState.lambda,
        omegaState.coherence,
        rainbowState.frequency
      );

      // FTCP Detection
      const ftcpResult = ftcpDetectorRef.current.addPoint(marketSnapshot.timestamp, omegaState.lambda);
      const Geff = ftcpDetectorRef.current.computeGeff();
      
      // Lighthouse Consensus
      const lighthouseState = lighthouseRef.current.validate(
        omegaState.lambda,
        omegaState.coherence,
        omegaState.substrate,
        omegaState.observer,
        omegaState.echo,
        Geff,
        ftcpResult?.isFTCP || false
      );
      
      // Trading Signal Generation
      const tradingSignal = signalGenRef.current.generateSignal(
        omegaState,
        lighthouseState,
        prismOutput
      );

      // Save to database
      let lighthouseEventId: string | null = null;
      
      if (lighthouseState.isLHE || marketSnapshot.timestamp % 10000 < 1000) {
        lighthouseEventId = await saveLighthouseEvent(omegaState, lighthouseState, prismOutput);
      }
      
      await saveTradingSignal(tradingSignal, lighthouseEventId);

      // Save coherence history periodically
      if (marketSnapshot.timestamp % 10000 < 1000) {
        await saveCoherenceHistory(omegaState, marketSnapshot.timestamp, binanceData.symbol);
      }

      // Update UI state
      setOmega(omegaState);
      setRainbow(rainbowState);
      setPrism(prismOutput);
      setFtcpPoint(ftcpResult);
      setLighthouse(lighthouseState);
      setSignal(tradingSignal);
    };

    processData();
  }, [binanceData, isRunning, binanceConnected]);
  // Handle connection errors
  useEffect(() => {
    if (binanceError) {
      setLastConnectionError(binanceError);
      toast({
        title: '⚠️ Connection Error',
        description: binanceError,
        variant: 'destructive',
        duration: 5000,
      });
    }
  }, [binanceError, toast]);

  // REST API polling handles data automatically via useBinanceMarketData hook
  // No manual connection management needed

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

        {/* Binance Connection Status */}
        <div className="mb-8">
          <BinanceConnectionStatus
            isConnected={isConnected}
            isHealthy={connectionHealthy}
            reconnectAttempts={reconnectAttempts}
            lastError={lastConnectionError}
            onReconnect={() => {
              // Refetch market data manually
              window.location.reload();
            }}
          />
        </div>

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

        {/* AI Analysis Panel */}
        {signal && lighthouse && omega && (
          <div className="mb-8">
            <AIAnalysisPanel
              lambda={omega}
              lighthouse={lighthouse}
              prism={prism}
              signal={signal}
              currentPrice={currentPrice}
              currentSymbol={currentSymbol}
            />
          </div>
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

        {/* Lighthouse Metrics Visualization */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            <LighthouseMetricsPanel lighthouse={lighthouse} />
          </div>
          <StargateStatus onLocationUpdate={setUserLocation} celestialBoost={celestialBoost} />
        </div>

        {/* Omega Field Visualization - Full Tensor Product */}
        {omega && (
          <div className="mb-8">
            <OmegaFieldVisualization omega={omega} unityEvent={unityEvent} />
          </div>
        )}

        {/* Consciousness Coherence Tracker */}
        {omega && (
          <div className="mb-8">
            <ConsciousnessCoherenceTracker currentCoherence={omega.coherence} />
          </div>
        )}

        {/* Consciousness Field History Chart */}
        <div className="mb-8">
          <ConsciousnessHistoryChart />
        </div>

        {/* Temporal Alignment Tracker */}
        <div className="mb-8">
          <TemporalAlignmentTracker />
        </div>

        {/* FTCP Timeline Visualization */}
        <div className="mb-8">
          <FTCPTimeline 
            ftcpPoint={ftcpPoint}
            currentPrice={currentPrice}
            currentSymbol={currentSymbol}
          />
        </div>


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
          <ResearchValidation />
        </div>

        <div className="mb-8">
          <HarmonicRealityFramework />
        </div>

        <div className="mb-8">
          <CoherenceTracker lambda={omega} isRunning={isRunning} />
        </div>

        <div className="mb-8">
          <CoherenceHeatmap symbol={currentSymbol} />
        </div>

        <div className="mb-8">
          <CoherenceForecaster />
        </div>

        <div className="mb-8">
          <MultiSymbolForecastComparison />
        </div>

        <div className="mb-8">
          <StargateVisualization />
        </div>

        <div className="mb-8">
          <CelestialAlignments />
        </div>

        <div className="mb-8">
          <SchumannResonanceMonitor />
        </div>

        <div className="mb-8">
          <SolarFlareCorrelation />
        </div>

        <div className="mb-8">
          <MasterEquationField3D lambda={omega} />
        </div>

        <div className="mb-8">
          <Watchlist />
        </div>

        <AureonField lambda={omega} rainbow={rainbow} prism={prism} />

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
