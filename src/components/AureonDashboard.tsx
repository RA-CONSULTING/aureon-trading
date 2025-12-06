import { useEffect, useState, useRef } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { useAureonSession } from '@/hooks/useAureonSession';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, Activity, Zap, Brain, Radio, Database, Router, LogOut, Play, Square, Wifi, WifiOff } from 'lucide-react';
import { DataSourceIndicator, DemoModeWarningBanner } from '@/components/DataSourceIndicator';
import { useNavigate } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { UserAssetsPanel } from '@/components/warroom/UserAssetsPanel';
import { SmartAlertBanner } from '@/components/SmartAlertBanner';
import { FloatingAIButton } from '@/components/FloatingAIButton';
import { ecosystemConnector } from '@/core/ecosystemConnector';
import { backgroundServices } from '@/core/backgroundServices';
import { toast } from 'sonner';

// Simple system indicator component
function SystemIndicator({ name, active, icon: Icon }: { name: string; active: boolean; icon: React.ElementType }) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className={cn("h-2 w-2 rounded-full", active ? "bg-green-400" : "bg-muted-foreground")} />
      <Icon className="h-3 w-3 text-muted-foreground" />
      <span className={cn(active ? "text-foreground" : "text-muted-foreground")}>{name}</span>
    </div>
  );
}

export default function AureonDashboard() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  
  // Ecosystem health check state
  const [lastDataReceived, setLastDataReceived] = useState<Date | null>(null);
  const [ecosystemHealth, setEcosystemHealth] = useState<'connected' | 'stale' | 'disconnected'>('disconnected');
  const healthCheckRef = useRef<NodeJS.Timeout | null>(null);
  
  const {
    quantumState,
    tradingState,
    systemStatus,
    marketData,
    lastSignal,
    lastDecision,
    nextCheckIn,
    startTrading,
    stopTrading
  } = useAureonSession(userId);
  
  // Start background services on mount
  useEffect(() => {
    backgroundServices.start();
    return () => backgroundServices.stop();
  }, []);
  
  // Subscribe to ecosystem updates for health monitoring
  useEffect(() => {
    const unsubscribe = ecosystemConnector.subscribe(() => {
      setLastDataReceived(new Date());
      setEcosystemHealth('connected');
    });
    
    // Health check: mark as stale if no data for 10s, disconnected if 30s
    healthCheckRef.current = setInterval(() => {
      if (lastDataReceived) {
        const timeSince = Date.now() - lastDataReceived.getTime();
        if (timeSince > 30000) {
          setEcosystemHealth('disconnected');
        } else if (timeSince > 10000) {
          setEcosystemHealth('stale');
        } else {
          setEcosystemHealth('connected');
        }
      }
    }, 2000);
    
    return () => {
      unsubscribe();
      if (healthCheckRef.current) clearInterval(healthCheckRef.current);
    };
  }, [lastDataReceived]);

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
    backgroundServices.stop();
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

  // Count active systems
  const activeSystemCount = Object.values(systemStatus).filter(Boolean).length;
  const totalSystemCount = Object.keys(systemStatus).length;

  return (
    <div className="min-h-screen bg-background">
      {/* Demo Mode Warning Banner */}
      <DemoModeWarningBanner />
      
      {/* Smart Alert Banner - only shows when there are issues */}
      <SmartAlertBanner />
      
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
              <DataSourceIndicator compact />
              
              {/* Ecosystem Health */}
              <Badge 
                variant={ecosystemHealth === 'connected' ? 'default' : ecosystemHealth === 'stale' ? 'secondary' : 'destructive'} 
                className="gap-1"
              >
                {ecosystemHealth === 'connected' ? <Wifi className="h-3 w-3" /> : <WifiOff className="h-3 w-3" />}
                {ecosystemHealth === 'connected' ? 'OK' : ecosystemHealth === 'stale' ? 'STALE' : 'DOWN'}
              </Badge>
              
              {/* Systems Summary */}
              <Badge variant={activeSystemCount === totalSystemCount ? "default" : "secondary"} className="gap-1">
                <Brain className="h-3 w-3" />
                {activeSystemCount}/{totalSystemCount}
              </Badge>
              
              <Badge variant={tradingState.isActive ? "default" : "secondary"} className="gap-1">
                <div className={cn("h-1.5 w-1.5 rounded-full", tradingState.isActive ? "bg-green-400 animate-pulse" : "bg-muted-foreground")} />
                {tradingState.isActive ? 'ACTIVE' : 'IDLE'}
              </Badge>
              
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Top Stats Row - Essential Cards Only */}
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
                <span className="text-xs text-muted-foreground">Γ (Coherence)</span>
                <span className="text-sm font-mono font-bold">{quantumState.coherence.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Λ (Lambda)</span>
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

          {/* Systems Status - Compact */}
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
        
        {/* User Assets Panel - Multi-Exchange Holdings */}
        <UserAssetsPanel />

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

        {/* Recent Trades - Compact */}
        <Card className="border-border/50">
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium text-muted-foreground">RECENT TRADES</CardTitle>
          </CardHeader>
          <CardContent>
            {tradingState.recentTrades.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                No trades yet. Start trading to see activity here.
              </p>
            ) : (
              <div className="space-y-2">
                {tradingState.recentTrades.slice(0, 5).map((trade, i) => (
                  <div key={i} className="flex items-center justify-between text-xs border-b border-border/30 pb-2 last:border-0">
                    <div className="flex items-center gap-2">
                      <Badge variant={trade.side === 'BUY' ? 'default' : 'secondary'} className="text-[9px]">
                        {trade.side}
                      </Badge>
                      <span className="font-mono">{trade.symbol}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-muted-foreground">{trade.quantity}</span>
                      <span className={cn("font-mono", trade.pnl >= 0 ? "text-green-400" : "text-red-400")}>
                        {trade.pnl >= 0 ? '+' : ''}{trade.pnl.toFixed(2)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </main>
      
      {/* Floating AI Button */}
      <FloatingAIButton />
    </div>
  );
}
