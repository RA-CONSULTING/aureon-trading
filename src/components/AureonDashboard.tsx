import { useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
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
import { ExchangeStatusSummary } from '@/components/ExchangeStatusSummary';
// Import hooks for global state - NO MORE LOCAL INITIALIZATION
import { 
  useGlobalState, 
  useGlobalTradingControls,
} from '@/hooks/useGlobalState';
import { globalSystemsManager } from '@/core/globalSystemsManager';

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
  
  // Get ALL state from global manager - no local state management
  const state = useGlobalState();
  const { startTrading, stopTrading } = useGlobalTradingControls();
  
  // Extract what we need from global state
  const {
    userId,
    userEmail,
    isAuthenticated,
    coherence,
    lambda,
    lighthouseSignal,
    dominantNode,
    prismLevel,
    prismState,
    isActive,
    totalEquity,
    totalTrades,
    winningTrades,
    totalPnl,
    gasTankBalance,
    recentTrades,
    lastSignal,
    lastDecision,
    nextCheckIn,
    systemStatus,
    ecosystemHealth,
    isInitialized,
  } = state;
  
  // Redirect to auth if not authenticated
  useEffect(() => {
    if (isInitialized && !isAuthenticated) {
      navigate('/auth');
    }
  }, [isInitialized, isAuthenticated, navigate]);

  const handleSignOut = async () => {
    stopTrading();
    await supabase.auth.signOut();
    navigate('/auth');
  };

  const winRate = totalTrades > 0 
    ? ((winningTrades / totalTrades) * 100).toFixed(0)
    : '0';

  const getPrismColor = () => {
    switch (prismState) {
      case 'MANIFEST': return 'text-green-400';
      case 'CONVERGING': return 'text-yellow-400';
      default: return 'text-muted-foreground';
    }
  };

  // Count active systems
  const activeSystemCount = Object.values(systemStatus).filter(Boolean).length;
  const totalSystemCount = Object.keys(systemStatus).length;

  // Show loading if not initialized
  if (!isInitialized) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="h-8 w-8 rounded-full border-2 border-primary border-t-transparent animate-spin" />
      </div>
    );
  }

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
              
              <Badge variant={isActive ? "default" : "secondary"} className="gap-1">
                <div className={cn("h-1.5 w-1.5 rounded-full", isActive ? "bg-green-400 animate-pulse" : "bg-muted-foreground")} />
                {isActive ? 'ACTIVE' : 'IDLE'}
              </Badge>
              
              <Button variant="ghost" size="sm" onClick={handleSignOut}>
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6 space-y-6">
        {/* Exchange Connection Status */}
        <ExchangeStatusSummary />
        
        {/* Systems run as background automation - no UI visualizers on home */}
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
                <span className="text-sm font-mono font-bold">{coherence.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Λ (Lambda)</span>
                <span className="text-sm font-mono">{lambda.toFixed(3)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Prism</span>
                <span className={cn("text-sm font-medium", getPrismColor())}>{prismState}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Node</span>
                <span className="text-sm">{dominantNode}</span>
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
                <span className="text-sm font-mono font-bold">${totalEquity.toFixed(2)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">P/L</span>
                <span className={cn("text-sm font-mono", totalPnl >= 0 ? "text-green-400" : "text-red-400")}>
                  {totalPnl >= 0 ? '+' : ''}${totalPnl.toFixed(2)}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Trades</span>
                <span className="text-sm font-mono">{totalTrades} ({winRate}% win)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-xs text-muted-foreground">Gas Tank</span>
                <span className="text-sm font-mono">£{gasTankBalance.toFixed(2)}</span>
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
                <Badge variant={isActive ? "default" : "outline"} className="text-[10px]">
                  {isActive ? '● ACTIVE' : '○ STOPPED'}
                </Badge>
              </CardTitle>
              
              <div className="flex gap-2">
                {!isActive ? (
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
              {isActive 
                ? 'All quantum systems are running via GlobalSystemsManager. Trades execute automatically when Γ > 0.70 and bus consensus confirms.'
                : 'Click Start to begin autonomous quantum trading. Systems run in background and persist across page navigation.'
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
            {recentTrades.length === 0 ? (
              <p className="text-xs text-muted-foreground text-center py-4">
                No trades yet. Start trading to see activity here.
              </p>
            ) : (
              <div className="space-y-2">
                {recentTrades.slice(0, 5).map((trade, i) => (
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
