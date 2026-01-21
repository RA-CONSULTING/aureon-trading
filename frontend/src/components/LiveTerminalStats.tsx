/**
 * LiveTerminalStats - Mirrors the Python terminal output exactly
 * Shows real-time system metrics in the same format as the terminal
 */

import { useGlobalState } from '@/hooks/useGlobalState';
import { useTerminalMetrics } from '@/hooks/useTerminalMetrics';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const StatusIndicator = ({ active, label }: { active: boolean; label?: string }) => (
  <span className={cn(
    "inline-flex items-center gap-1",
    active ? "text-green-500" : "text-red-500"
  )}>
    {active ? '🟢' : '🔴'}
    {label && <span className="text-xs">{label}</span>}
  </span>
);

const MetricRow = ({ 
  icon, 
  children,
  className 
}: { 
  icon: string; 
  children: React.ReactNode;
  className?: string;
}) => (
  <div className={cn("font-mono text-sm flex items-start gap-2", className)}>
    <span>{icon}</span>
    <span className="flex-1">{children}</span>
  </div>
);

const formatCurrency = (value: number, currency = '€') => {
  const sign = value >= 0 ? '+' : '';
  return `${currency}${sign}${value.toFixed(2)}`;
};

const formatPercent = (value: number) => {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
};

export function LiveTerminalStats() {
  const state = useGlobalState();
  const metrics = useTerminalMetrics();
  
  const winRate = state.totalTrades > 0 
    ? ((state.winningTrades / state.totalTrades) * 100).toFixed(1)
    : '0.0';
  
  const coherenceColor = state.coherence >= 0.45 ? 'text-green-500' : 
                         state.coherence >= 0.30 ? 'text-yellow-500' : 'text-red-500';
  
  const gaiaColor = state.gaiaLatticeState === 'COHERENT' ? 'text-green-500' :
                    state.gaiaLatticeState === 'NEUTRAL' ? 'text-yellow-500' : 'text-red-500';
  
  const hncColor = state.hncCoherencePercent >= 50 ? 'text-green-500' :
                   state.hncCoherencePercent >= 25 ? 'text-yellow-500' : 'text-red-500';
  
  const ddColor = state.currentDrawdownPercent > 30 ? 'text-red-500' :
                  state.currentDrawdownPercent > 15 ? 'text-yellow-500' : 'text-green-500';

  return (
    <Card className="bg-background/95 border-border/50 p-4 font-mono text-xs space-y-1">
      {/* Header */}
      <div className="text-center text-primary font-bold mb-2 border-b border-border/30 pb-2">
        📊 AUREON TERMINAL MIRROR
      </div>
      
      {/* Active Positions */}
      <MetricRow icon="📊">
        <span className="text-muted-foreground">Active Positions</span>{' '}
        <span className="text-foreground">({state.activePositions.length}/{state.maxPositions})</span>
      </MetricRow>
      
      {state.activePositions.slice(0, 3).map((pos, i) => (
        <MetricRow key={i} icon="   🎯" className="pl-4">
          <span className="text-primary">{pos.symbol}</span>{' '}
          <span className="text-muted-foreground">Entry: ${pos.entryPrice.toFixed(6)}</span>{' | '}
          <span className={pos.pnlPercent >= 0 ? 'text-green-500' : 'text-red-500'}>
            Now: {formatPercent(pos.pnlPercent)}
          </span>
          {pos.pnlPercent < 0 ? ' 🔴' : ' 🟢'}
        </MetricRow>
      ))}
      
      <div className="border-t border-border/30 my-2" />
      
      {/* Portfolio */}
      <MetricRow icon="💎">
        <span className="text-muted-foreground">Portfolio:</span>{' '}
        <span className="text-foreground font-bold">€{state.totalEquity.toFixed(2)}</span>{' '}
        <span className={state.totalPnl >= 0 ? 'text-green-500' : 'text-red-500'}>
          ({formatPercent((state.totalPnl / Math.max(state.peakEquity, 1)) * 100)})
        </span>
        {' | Peak: '}
        <span className="text-primary">€{state.peakEquity.toFixed(2)}</span>
      </MetricRow>
      
      <MetricRow icon="📉">
        <span className="text-muted-foreground">Max DD:</span>{' '}
        <span className={ddColor}>{state.maxDrawdownPercent.toFixed(1)}%</span>
        {' | Current DD: '}
        <span className={ddColor}>{state.currentDrawdownPercent.toFixed(1)}%</span>
      </MetricRow>
      
      <MetricRow icon="📈">
        <span className="text-muted-foreground">Cycle P&L:</span>{' '}
        <span className={state.cyclePnl >= 0 ? 'text-green-500' : 'text-red-500'}>
          {formatCurrency(state.cyclePnl)} ({formatPercent(state.cyclePnlPercent)})
        </span>
      </MetricRow>
      
      <MetricRow icon="📈">
        <span className="text-muted-foreground">Trades:</span>{' '}
        <span className="text-foreground">{state.totalTrades}</span>
        {' | Wins: '}<span className="text-green-500">{state.winningTrades}</span>
        {' | WR: '}<span className={Number(winRate) >= 51 ? 'text-green-500' : 'text-yellow-500'}>{winRate}%</span>
        {' | Avg Hold: '}<span className="text-muted-foreground">{state.avgHoldTimeMinutes.toFixed(1)}m</span>
      </MetricRow>
      
      <div className="border-t border-border/30 my-2" />
      
      {/* Network & Frequency */}
      <MetricRow icon="🍄">
        <span className="text-muted-foreground">Network Γ:</span>{' '}
        <span className={coherenceColor}>{state.coherence.toFixed(2)}</span>
        {' | WS: '}
        <StatusIndicator active={state.wsConnected} />
        <span className="text-muted-foreground"> ({state.wsMessageCount})</span>
      </MetricRow>
      
      <MetricRow icon="🌐">
        <span className="text-muted-foreground">Gaia Lattice:</span>{' '}
        <span className={gaiaColor}>{state.gaiaLatticeState}</span>
        {' ('}<span className={state.gaiaFrequency === 432 ? 'text-green-500' : 'text-red-500'}>
          {state.gaiaFrequency.toFixed(1)}Hz
        </span>{')'}
        {state.gaiaLatticeState === 'DISTORTION' ? ' 🔴' : state.gaiaLatticeState === 'COHERENT' ? ' 🟢' : ' 🟡'}
        {' | Purity: '}<span className="text-foreground">{state.purityPercent}%</span>
        {' | Carrier: '}<span className="text-primary">{state.carrierWavePhi.toFixed(2)}φ</span>
        {' | 432Hz: '}<span className="text-foreground">{state.harmonicLock432}%</span>
      </MetricRow>
      
      <MetricRow icon="🌍">
        <span className="text-muted-foreground">Carrier Wave:</span>
        {' Nullify: '}<span className="text-foreground">{100 - state.purityPercent}%</span>
        {' | Risk: '}<span className="text-yellow-500">{state.riskMultiplier.toFixed(2)}x</span>
        {' | TP: '}<span className="text-green-500">{state.takeProfitMultiplier.toFixed(2)}x</span>
        {' | Λ-Field'}
      </MetricRow>
      
      <MetricRow icon="🌍">
        <span className="text-muted-foreground">HNC:</span>{' '}
        <span className="text-primary">{state.hncFrequency}Hz</span>
        {' | '}<span className={hncColor}>{state.hncMarketState}</span>
        {' | Coherence: '}<span className={hncColor}>{state.hncCoherencePercent}%</span>
        {state.hncCoherencePercent > 50 ? ' 🟢' : ' 🔴'}
        {' | Mod: '}<span className="text-foreground">×{state.hncModifier.toFixed(2)}</span>
      </MetricRow>
      
      <div className="border-t border-border/30 my-2" />
      
      {/* Trading Mode */}
      <MetricRow icon="🎮">
        <span className="text-muted-foreground">Mode:</span>{' '}
        <span className={cn(
          "font-bold",
          state.tradingMode === 'AGGRESSIVE' ? 'text-red-500' :
          state.tradingMode === 'CONSERVATIVE' ? 'text-blue-500' : 'text-yellow-500'
        )}>
          {state.tradingMode === 'AGGRESSIVE' ? '🔥' : state.tradingMode === 'CONSERVATIVE' ? '🛡️' : '⚖️'}{' '}
          {state.tradingMode}
        </span>
        {' | Entry Γ: '}<span className="text-foreground">{state.entryCoherenceThreshold.toFixed(3)}</span>
        {' | Exit Γ: '}<span className="text-foreground">{state.exitCoherenceThreshold.toFixed(3)}</span>
      </MetricRow>
      
      <MetricRow icon="💰">
        <span className="text-muted-foreground">Compounded:</span>{' '}
        <span className="text-green-500">€{state.compoundedCapital.toFixed(2)}</span>
        {' | Harvested: '}
        <span className="text-primary">€{state.harvestedCapital.toFixed(2)}</span>
      </MetricRow>
      
      <MetricRow icon="🌟">
        <span className="text-muted-foreground">Pool:</span>{' '}
        <span className="text-foreground">€{state.poolTotal.toFixed(2)} total</span>
        {' | '}<span className="text-green-500">€{state.poolAvailable.toFixed(2)} available</span>
        {' | Scouts: '}<span className="text-foreground">{state.scoutCount}</span>
        {' | Splits: '}<span className="text-foreground">{state.splitCount}</span>
      </MetricRow>
      
      <MetricRow icon="🍄">
        <span className="text-muted-foreground">Mycelium:</span>{' '}
        <span className="text-foreground">{state.myceliumHives} hives</span>
        {' | '}<span className="text-primary">{state.myceliumAgents} agents</span>
        {' | Gen '}<span className="text-foreground">{state.myceliumGeneration}</span>
        {' | 👸 Queen: '}
        <span className={state.queenPnl >= 0 ? 'text-green-500' : 'text-red-500'}>
          {state.queenPnl >= 0 ? '+' : ''}{state.queenPnl.toFixed(2)}
        </span>
        {' → '}<span className={cn(
          state.queenState === 'BUY' ? 'text-green-500' :
          state.queenState === 'SELL' ? 'text-red-500' : 'text-yellow-500'
        )}>{state.queenState}</span>
      </MetricRow>
      
      <MetricRow icon="⏱️">
        <span className="text-muted-foreground">Runtime:</span>{' '}
        <span className="text-foreground">{metrics.runtimeMinutes.toFixed(1)} min</span>
        {' | Positions: '}<span className="text-foreground">{state.activePositions.length}/{state.maxPositions}</span>
        {' | Max Gen: '}<span className="text-foreground">{state.maxGeneration}</span>
      </MetricRow>
    </Card>
  );
}
