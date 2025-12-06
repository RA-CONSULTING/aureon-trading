import { useEffect, useState } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAureonSession } from '@/hooks/useAureonSession';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Activity, Zap, Brain, Radio, Database, Router, TrendingUp, TrendingDown, LogOut, Play, Square } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { UnifiedBusStatus } from '@/components/warroom/UnifiedBusStatus';
import { TemporalLadderStatus } from '@/components/warroom/TemporalLadderStatus';
import { ExchangeBalances } from '@/components/warroom/ExchangeBalances';
import { PrismStatus } from '@/components/warroom/PrismStatus';
import { EcosystemStatus } from '@/components/warroom/EcosystemStatus';
import { HarmonicWaveform6DStatus } from '@/components/warroom/HarmonicWaveform6DStatus';
import { ProbabilityMatrixDisplay } from '@/components/warroom/ProbabilityMatrixDisplay';
import { ecosystemConnector } from '@/core/ecosystemConnector';

export default function AureonDashboard() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [waveform6D, setWaveform6D] = useState(ecosystemConnector.getWaveform6D());
  const [probabilityFusion, setProbabilityFusion] = useState(ecosystemConnector.getProbabilityFusion());
  
  const {
    quantumState,
    tradingState,
    systemStatus,
    busState,
    exchangeState,
    prismState,
    marketData,
    lastSignal,
    nextCheckIn,
    lastDecision,
    startTrading,
    stopTrading
  } = useAureonSession(userId);
  
  // Subscribe to ecosystem updates for 6D state
  useEffect(() => {
    const unsubscribe = ecosystemConnector.subscribe((state) => {
      setWaveform6D(state.waveform6D);
      setProbabilityFusion(state.probabilityFusion);
    });
    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event, session) => {
      if (session) {
        setUserId(session.user.id);
        setUserEmail(session.user.email);
      } else {
        navigate('/auth');
      }
    });

    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) {
        setUserId(session.user.id);
        setUserEmail(session.user.email);
      } else {
        navigate('/auth');
      }
    });

    return () => subscription.unsubscribe();
  }, [navigate]);

  const handleSignOut = async () => {
    stopTrading();
    await supabase.auth.signOut();
    navigate('/auth');
  };

  const winRate = tradingState.totalTrades > 0 
    ? ((tradingState.winningTrades / tradingState.totalTrades) * 100).toFixed(0)
    : '0';

  const getPrismColor = () => {
    switch (quantumState.prismState) {
      case 'MANIFEST': return 'text-green-400';
      case 'CONVERGING': return 'text-yellow-400';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/90 backdrop-blur-xl">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-3">
              <div className="h-9 w-9 rounded-lg bg-gradient-prism flex items-center justify-center love-pulse">
                <Sparkles className="h-4 w-4 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-prism">AUREON</h1>
                <p className="text-[9px] text-muted-foreground tracking-widest uppercase -mt-0.5">528 Hz</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Badge variant={tradingState.isActive ? "default" : "secondary"} className="gap-1">
                <div className={cn("h-1.5 w-1.5 rounded-full", tradingState.isActive ? "bg-green-400 animate-pulse" : "bg-muted-foreground")} />
                {tradingState.isActive ? 'LIVE' : 'IDLE'}
              </Badge>
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Top Stats Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Quantum State */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Activity className="h-3 w-3" /> QUANTUM STATE
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Γ</span>
                <span className="text-sm font-mono font-bold">{quantumState.coherence.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Λ</span>
                <span className="text-sm font-mono">{quantumState.lambda.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Prism</span>
                <span className={cn("text-sm font-medium", getPrismColor())}>{quantumState.prismState}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Node</span>
                <span className="text-sm">{quantumState.dominantNode}</span>
              </div>
            </CardContent>
          </Card>

          {/* Performance */}
          <Card className="border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Zap className="h-3 w-3" /> PERFORMANCE
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-1">
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Balance</span>
                <span className="text-sm font-mono font-bold">${tradingState.totalEquity.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">P/L</span>
                <span className={cn("text-sm font-mono", tradingState.totalPnl >= 0 ? "text-green-400" : "text-red-400")}>
                  {tradingState.totalPnl >= 0 ? '+' : ''}${tradingState.totalPnl.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Trades</span>
                <span className="text-sm font-mono">{tradingState.totalTrades} ({winRate}% win)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Gas Tank</span>
                <span className="text-sm font-mono">£{tradingState.gasTankBalance.toFixed(2)}</span>
              </div>
            </CardContent>
          </Card>

          {/* Systems Status */}
          <Card className="border-border/50 lg:col-span-2">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium text-muted-foreground flex items-center gap-1">
                <Brain className="h-3 w-3" /> SYSTEMS
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                <SystemIndicator name="Master Equation" active={systemStatus.masterEquation} icon={Activity} />
                <SystemIndicator name="Lighthouse" active={systemStatus.lighthouse} icon={Radio} />
                <SystemIndicator name="Rainbow Bridge" active={systemStatus.rainbowBridge} icon={Sparkles} />
                <SystemIndicator name="Elephant Memory" active={systemStatus.elephantMemory} icon={Database} />
                <SystemIndicator name="Order Router" active={systemStatus.orderRouter} icon={Router} />
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-muted-foreground">Next check:</span>
                  <span className="font-mono">{nextCheckIn}s</span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* The Prism + Unified Ecosystem Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <PrismStatus 
            lambda={quantumState.lambda}
            coherence={quantumState.coherence}
            substrate={quantumState.substrate}
            observer={quantumState.observer}
            echo={quantumState.echo}
            volatility={marketData.volatility}
            momentum={marketData.momentum}
            baseFrequency={396}
          />
          <UnifiedBusStatus />
          <EcosystemStatus />
          <ExchangeBalances 
            totalEquityUsd={exchangeState.totalEquityUsd}
            exchanges={exchangeState.exchanges}
          />
        </div>
        
        {/* 6D Harmonic Waveform + Probability Matrix Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <HarmonicWaveform6DStatus waveform={waveform6D} />
          <ProbabilityMatrixDisplay fusion={probabilityFusion} />
        </div>
        
        {/* Extended System Status Row */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <TemporalLadderStatus />
        </div>

        {/* Trading Control */}
        <Card className="border-border/50">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                AUTONOMOUS TRADING
                <Badge variant={tradingState.isActive ? "default" : "outline"} className="text-[10px]">
                  {tradingState.isActive ? '● ACTIVE' : '○ STOPPED'}
                </Badge>
              </CardTitle>
              
              <div className="flex gap-2">
                {!tradingState.isActive ? (
                  <Button size="sm" onClick={startTrading} className="gap-1">
                    <Play className="h-3 w-3" /> Start
                  </Button>
                ) : (
                  <Button size="sm" variant="destructive" onClick={stopTrading} className="gap-1">
                    <Square className="h-3 w-3" /> Stop
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {lastSignal && (
              <div className="bg-muted/30 rounded-md p-3 mb-4">
                <p className="text-xs text-muted-foreground">Last Signal</p>
                <p className="text-sm font-mono">{lastSignal}</p>
                {lastDecision && (
                  <p className="text-xs text-muted-foreground mt-1">
                    Reason: {lastDecision.finalDecision.reason}
                  </p>
                )}
              </div>
            )}
            
            <p className="text-xs text-muted-foreground">
              {tradingState.isActive 
                ? 'All quantum systems are running via UnifiedOrchestrator. Trades execute automatically when Γ > 0.70 and bus consensus confirms.'
                : 'Click Start to begin autonomous quantum trading. Systems will run in background with full Temporal Ladder integration.'
              }
            </p>
          </CardContent>
        </Card>

        {/* Recent Trades */}
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">RECENT TRADES</CardTitle>
          </CardHeader>
          <CardContent>
            {tradingState.recentTrades.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">No trades yet</p>
            ) : (
              <div className="space-y-2 max-h-[200px] overflow-y-auto">
                {tradingState.recentTrades.map((trade, i) => (
                  <div key={i} className="flex items-center justify-between text-xs py-1 border-b border-border/30 last:border-0">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground font-mono">{trade.time}</span>
                      <Badge variant={trade.side === 'BUY' ? 'default' : 'secondary'} className="text-[10px]">
                        {trade.side}
                      </Badge>
                      <span>{trade.symbol}</span>
                      <span className="text-muted-foreground">{trade.quantity}</span>
                    </div>
                    <div className="flex items-center gap-1">
                      {trade.success ? (
                        <TrendingUp className="h-3 w-3 text-green-400" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-400" />
                      )}
                      <span className={cn("font-mono", trade.pnl >= 0 ? "text-green-400" : "text-red-400")}>
                        {trade.pnl >= 0 ? '+' : ''}${trade.pnl.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

function SystemIndicator({ name, active, icon: Icon }: { name: string; active: boolean; icon: React.ElementType }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className={cn("h-1.5 w-1.5 rounded-full", active ? "bg-green-400" : "bg-muted-foreground")} />
      <Icon className="h-3 w-3 text-muted-foreground" />
      <span className={active ? "text-foreground" : "text-muted-foreground"}>{name}</span>
    </div>
  );
}
