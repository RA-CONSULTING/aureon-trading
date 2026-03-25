/**
 * LiveTerminalStats - Mirrors the Python terminal output exactly
 * Shows real-time system metrics in the same format as the terminal
 */

import { useGlobalState } from '@/hooks/useGlobalState';
import { useTerminalMetrics } from '@/hooks/useTerminalMetrics';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

const StatusIndicator = ({ active, label }: { active: boolean; label?: string }) => (
  <span className={cn("inline-flex items-center gap-1", active ? "text-green-500" : "text-red-500")}>
    {active ? '🟢' : '🔴'}
    {label && <span className="text-xs">{label}</span>}
  </span>
);

const MetricRow = ({
  icon,
  children,
  className,
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

const safeNumber = (value: unknown, fallback = 0): number => {
  const num = Number(value);
  return Number.isFinite(num) ? num : fallback;
};

const formatCurrency = (value: unknown, currency = '€') => {
  const num = safeNumber(value);
  const sign = num >= 0 ? '+' : '';
  return `${currency}${sign}${num.toFixed(2)}`;
};

const formatPercent = (value: unknown) => {
  const num = safeNumber(value);
  const sign = num >= 0 ? '+' : '';
  return `${sign}${num.toFixed(2)}%`;
};

export function LiveTerminalStats() {
  const state = useGlobalState();
  const metrics = useTerminalMetrics();
  const recentTerminalLines = Array.isArray(state.statusLines) ? state.statusLines.slice(-6) : [];
  const recentTrades = Array.isArray(state.recentTrades) ? state.recentTrades : [];
  const activePositions = Array.isArray(state.activePositions) ? state.activePositions : [];
  const unifiedSummary = state.unifiedMarketSummary
    ? {
        krakenEquity: safeNumber(state.unifiedMarketSummary.krakenEquity),
        capitalEquityGbp: safeNumber(state.unifiedMarketSummary.capitalEquityGbp),
        krakenSessionPnl: safeNumber(state.unifiedMarketSummary.krakenSessionPnl),
        capitalSessionPnlGbp: safeNumber(state.unifiedMarketSummary.capitalSessionPnlGbp),
        capitalOpenPositions: safeNumber(state.unifiedMarketSummary.capitalOpenPositions),
        krakenOpenPositions: safeNumber(state.unifiedMarketSummary.krakenOpenPositions),
        capitalRecentCloses: Array.isArray(state.unifiedMarketSummary.capitalRecentCloses)
          ? state.unifiedMarketSummary.capitalRecentCloses
          : [],
        capitalCandidates: Array.isArray(state.unifiedMarketSummary.capitalCandidates)
          ? state.unifiedMarketSummary.capitalCandidates
          : [],
      }
    : undefined;

  const winRate = safeNumber(state.totalTrades) > 0
    ? ((safeNumber(state.winningTrades) / safeNumber(state.totalTrades)) * 100).toFixed(1)
    : '0.0';

  const coherence = safeNumber(state.coherence);
  const hncCoherence = safeNumber(state.hncCoherencePercent);
  const currentDd = safeNumber(state.currentDrawdownPercent);
  const coherenceColor = coherence >= 0.45 ? 'text-green-500' : coherence >= 0.30 ? 'text-yellow-500' : 'text-red-500';
  const gaiaColor = state.gaiaLatticeState === 'COHERENT' ? 'text-green-500' : state.gaiaLatticeState === 'NEUTRAL' ? 'text-yellow-500' : 'text-red-500';
  const hncColor = hncCoherence >= 50 ? 'text-green-500' : hncCoherence >= 25 ? 'text-yellow-500' : 'text-red-500';
  const ddColor = currentDd > 30 ? 'text-red-500' : currentDd > 15 ? 'text-yellow-500' : 'text-green-500';

  return (
    <Card className="bg-background/95 border-border/50 p-4 font-mono text-xs space-y-1">
      <div className="text-center text-primary font-bold mb-2 border-b border-border/30 pb-2">
        📊 AUREON TERMINAL MIRROR
      </div>

      <MetricRow icon="📊">
        <span className="text-muted-foreground">Active Positions</span>{' '}
        <span className="text-foreground">({activePositions.length}/{safeNumber(state.maxPositions)})</span>
      </MetricRow>

      {activePositions.slice(0, 3).map((pos, i) => (
        <MetricRow key={i} icon="   🎯" className="pl-4">
          <span className="text-primary">{pos.symbol}</span>{' '}
          {pos.exchange && <span className="text-[10px] text-muted-foreground uppercase">[{pos.exchange}]</span>}{' '}
          <span className="text-muted-foreground">Entry: ${safeNumber(pos.entryPrice).toFixed(6)}</span>{' | '}
          <span className={safeNumber(pos.pnlPercent) >= 0 ? 'text-green-500' : 'text-red-500'}>
            Now: {formatPercent(pos.pnlPercent)}
          </span>
          {safeNumber(pos.pnlPercent) < 0 ? ' 🔴' : ' 🟢'}
        </MetricRow>
      ))}

      <div className="border-t border-border/30 my-2" />

      <MetricRow icon="💎">
        <span className="text-muted-foreground">Portfolio:</span>{' '}
        <span className="text-foreground font-bold">€{safeNumber(state.totalEquity).toFixed(2)}</span>{' '}
        <span className={safeNumber(state.totalPnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
          ({formatPercent((safeNumber(state.totalPnl) / Math.max(safeNumber(state.peakEquity), 1)) * 100)})
        </span>
        {' | Peak: '}
        <span className="text-primary">€{safeNumber(state.peakEquity).toFixed(2)}</span>
      </MetricRow>

      <MetricRow icon="📉">
        <span className="text-muted-foreground">Max DD:</span>{' '}
        <span className={ddColor}>{safeNumber(state.maxDrawdownPercent).toFixed(1)}%</span>
        {' | Current DD: '}
        <span className={ddColor}>{currentDd.toFixed(1)}%</span>
      </MetricRow>

      <MetricRow icon="📈">
        <span className="text-muted-foreground">Cycle P&L:</span>{' '}
        <span className={safeNumber(state.cyclePnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
          {formatCurrency(state.cyclePnl)} ({formatPercent(state.cyclePnlPercent)})
        </span>
      </MetricRow>

      <MetricRow icon="📈">
        <span className="text-muted-foreground">Trades:</span>{' '}
        <span className="text-foreground">{safeNumber(state.totalTrades)}</span>
        {' | Wins: '}<span className="text-green-500">{safeNumber(state.winningTrades)}</span>
        {' | WR: '}<span className={Number(winRate) >= 51 ? 'text-green-500' : 'text-yellow-500'}>{winRate}%</span>
        {' | Avg Hold: '}<span className="text-muted-foreground">{safeNumber(state.avgHoldTimeMinutes).toFixed(1)}m</span>
      </MetricRow>

      <div className="border-t border-border/30 my-2" />

      <MetricRow icon="🍄">
        <span className="text-muted-foreground">Network Γ:</span>{' '}
        <span className={coherenceColor}>{coherence.toFixed(2)}</span>
        {' | WS: '}
        <StatusIndicator active={Boolean(state.wsConnected)} />
        <span className="text-muted-foreground"> ({safeNumber(state.wsMessageCount)})</span>
      </MetricRow>

      <MetricRow icon="🌐">
        <span className="text-muted-foreground">Gaia Lattice:</span>{' '}
        <span className={gaiaColor}>{state.gaiaLatticeState}</span>
        {' ('}<span className={safeNumber(state.gaiaFrequency) === 432 ? 'text-green-500' : 'text-red-500'}>
          {safeNumber(state.gaiaFrequency).toFixed(1)}Hz
        </span>{')'}
        {' | Purity: '}<span className="text-foreground">{safeNumber(state.purityPercent)}%</span>
        {' | Carrier: '}<span className="text-primary">{safeNumber(state.carrierWavePhi).toFixed(2)}φ</span>
        {' | 432Hz: '}<span className="text-foreground">{safeNumber(state.harmonicLock432)}%</span>
      </MetricRow>

      <MetricRow icon="🌍">
        <span className="text-muted-foreground">Carrier Wave:</span>
        {' Nullify: '}<span className="text-foreground">{100 - safeNumber(state.purityPercent)}%</span>
        {' | Risk: '}<span className="text-yellow-500">{safeNumber(state.riskMultiplier).toFixed(2)}x</span>
        {' | TP: '}<span className="text-green-500">{safeNumber(state.takeProfitMultiplier).toFixed(2)}x</span>
        {' | Λ-Field'}
      </MetricRow>

      <MetricRow icon="🌍">
        <span className="text-muted-foreground">HNC:</span>{' '}
        <span className="text-primary">{safeNumber(state.hncFrequency)}Hz</span>
        {' | '}<span className={hncColor}>{state.hncMarketState}</span>
        {' | Coherence: '}<span className={hncColor}>{hncCoherence}%</span>
        {' | Mod: '}<span className="text-foreground">×{safeNumber(state.hncModifier).toFixed(2)}</span>
      </MetricRow>

      <div className="border-t border-border/30 my-2" />

      <MetricRow icon="🎮">
        <span className="text-muted-foreground">Mode:</span>{' '}
        <span className={cn("font-bold", state.tradingMode === 'AGGRESSIVE' ? 'text-red-500' : state.tradingMode === 'CONSERVATIVE' ? 'text-blue-500' : 'text-yellow-500')}>
          {state.tradingMode}
        </span>
        {' | Entry Γ: '}<span className="text-foreground">{safeNumber(state.entryCoherenceThreshold).toFixed(3)}</span>
        {' | Exit Γ: '}<span className="text-foreground">{safeNumber(state.exitCoherenceThreshold).toFixed(3)}</span>
      </MetricRow>

      <MetricRow icon="💰">
        <span className="text-muted-foreground">Compounded:</span>{' '}
        <span className="text-green-500">€{safeNumber(state.compoundedCapital).toFixed(2)}</span>
        {' | Harvested: '}
        <span className="text-primary">€{safeNumber(state.harvestedCapital).toFixed(2)}</span>
      </MetricRow>

      <MetricRow icon="🌟">
        <span className="text-muted-foreground">Pool:</span>{' '}
        <span className="text-foreground">€{safeNumber(state.poolTotal).toFixed(2)} total</span>
        {' | '}<span className="text-green-500">€{safeNumber(state.poolAvailable).toFixed(2)} available</span>
        {' | Scouts: '}<span className="text-foreground">{safeNumber(state.scoutCount)}</span>
        {' | Splits: '}<span className="text-foreground">{safeNumber(state.splitCount)}</span>
      </MetricRow>

      <MetricRow icon="🍄">
        <span className="text-muted-foreground">Mycelium:</span>{' '}
        <span className="text-foreground">{safeNumber(state.myceliumHives)} hives</span>
        {' | '}<span className="text-primary">{safeNumber(state.myceliumAgents)} agents</span>
        {' | Gen '}<span className="text-foreground">{safeNumber(state.myceliumGeneration)}</span>
        {' | Queen: '}
        <span className={safeNumber(state.queenPnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
          {safeNumber(state.queenPnl) >= 0 ? '+' : ''}{safeNumber(state.queenPnl).toFixed(2)}
        </span>
        {' -> '}<span className={cn(state.queenState === 'BUY' ? 'text-green-500' : state.queenState === 'SELL' ? 'text-red-500' : 'text-yellow-500')}>{state.queenState}</span>
      </MetricRow>

      <MetricRow icon="⏱️">
        <span className="text-muted-foreground">Runtime:</span>{' '}
        <span className="text-foreground">{safeNumber(metrics.runtimeMinutes).toFixed(1)} min</span>
        {' | Positions: '}<span className="text-foreground">{activePositions.length}/{safeNumber(state.maxPositions)}</span>
        {' | Max Gen: '}<span className="text-foreground">{safeNumber(state.maxGeneration)}</span>
      </MetricRow>

      {unifiedSummary && (
        <div className="rounded border border-border/30 bg-muted/20 p-2">
          <div className="text-[10px] text-muted-foreground mb-1">UNIFIED MARKET SUMMARY</div>
          <div className="font-mono text-[11px] break-words">
            Kraken ${unifiedSummary.krakenEquity.toFixed(2)} | Capital £{unifiedSummary.capitalEquityGbp.toFixed(2)} | Open {unifiedSummary.krakenOpenPositions}K/{unifiedSummary.capitalOpenPositions}C
          </div>
          <div className="font-mono text-[11px] break-words">
            Kraken PnL ${unifiedSummary.krakenSessionPnl.toFixed(2)} | Capital PnL £{unifiedSummary.capitalSessionPnlGbp.toFixed(2)}
          </div>
        </div>
      )}

      {(state.latestMonitorLine || recentTerminalLines.length > 0 || recentTrades.length > 0) && (
        <>
          <div className="border-t border-border/30 my-2" />

          {state.latestMonitorLine && (
            <div className="rounded border border-border/30 bg-muted/20 p-2">
              <div className="text-[10px] text-muted-foreground mb-1">LIVE MONITOR</div>
              <div className="font-mono text-[11px] break-words">{state.latestMonitorLine}</div>
            </div>
          )}

          {recentTerminalLines.length > 0 && (
            <div className="rounded border border-border/30 bg-muted/20 p-2">
              <div className="text-[10px] text-muted-foreground mb-1">STATUS BLOCK</div>
              <div className="space-y-1">
                {recentTerminalLines.map((line, idx) => (
                  <div key={`${idx}-${line}`} className="font-mono text-[11px] break-words">
                    {line}
                  </div>
                ))}
              </div>
            </div>
          )}

          {recentTrades.length > 0 && (
            <div className="rounded border border-border/30 bg-muted/20 p-2">
              <div className="text-[10px] text-muted-foreground mb-1">RECENT CLOSES</div>
              <div className="space-y-1">
                {recentTrades.slice(0, 5).map((trade, idx) => (
                  <div key={`${idx}-${trade.time}-${trade.symbol}`} className="font-mono text-[11px] flex items-center justify-between gap-2">
                    <span>{trade.symbol} {trade.side} {trade.exchange ? `[${trade.exchange}]` : ''}</span>
                    <span className={safeNumber(trade.pnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
                      {safeNumber(trade.pnl) >= 0 ? '+' : ''}{safeNumber(trade.pnl).toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {unifiedSummary && (unifiedSummary.capitalRecentCloses.length > 0 || unifiedSummary.capitalCandidates.length > 0) && (
            <div className="rounded border border-border/30 bg-muted/20 p-2">
              <div className="text-[10px] text-muted-foreground mb-1">CAPITAL MARKET FEED</div>
              {unifiedSummary.capitalRecentCloses.length > 0 && (
                <div className="space-y-1 mb-2">
                  {unifiedSummary.capitalRecentCloses.map((trade, idx) => (
                    <div key={`${idx}-${trade.symbol}-${trade.reason}`} className="font-mono text-[11px] flex items-center justify-between gap-2">
                      <span>{trade.symbol} {trade.direction} [capital]</span>
                      <span className={safeNumber(trade.net_pnl) >= 0 ? 'text-green-500' : 'text-red-500'}>
                        {safeNumber(trade.net_pnl) >= 0 ? '+' : ''}{safeNumber(trade.net_pnl).toFixed(2)} GBP
                      </span>
                    </div>
                  ))}
                </div>
              )}
              {unifiedSummary.capitalCandidates.length > 0 && (
                <div className="space-y-1">
                  {unifiedSummary.capitalCandidates.map((candidate, idx) => (
                    <div key={`${idx}-${candidate.symbol}`} className="font-mono text-[11px] flex items-center justify-between gap-2">
                      <span>{candidate.symbol} [{candidate.asset_class}]</span>
                      <span className="text-primary">
                        s={safeNumber(candidate.score).toFixed(2)} chg={safeNumber(candidate.change_pct).toFixed(2)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  );
}
