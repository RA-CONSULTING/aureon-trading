/**
 * CinematicHUD - HTML overlay combining all HUD panels
 * Glassmorphic sci-fi cockpit interface with full consciousness data
 */

import { HUDTopBar } from './HUDTopBar';
import { HUDQueenVoice } from './HUDQueenVoice';
import { HUDTradeStream } from './HUDTradeStream';
import { HUDMetricsPanel } from './HUDMetricsPanel';
import { HUDConsciousnessPanel } from './HUDConsciousnessPanel';
import type { GlobalState } from '@/core/globalSystemsManager';

interface CinematicHUDProps {
  state: GlobalState;
  hiveMood: string;
  activeScanner: string;
}

export function CinematicHUD({ state, hiveMood, activeScanner }: CinematicHUDProps) {
  const winRate = state.totalTrades > 0
    ? (state.winningTrades / state.totalTrades) * 100
    : 0;

  const c = state.consciousness;

  return (
    <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
      {/* Top bar */}
      <HUDTopBar
        totalEquity={state.totalEquity}
        totalPnl={state.totalPnl}
        cyclePnlPercent={state.cyclePnlPercent}
        winRate={winRate}
        coherence={c.available ? c.psi : state.coherence}
        totalTrades={state.totalTrades}
        isActive={state.isActive}
        krakenConnected={state.ecosystemHealth === 'connected'}
        capitalConnected={state.ecosystemHealth === 'connected'}
        binanceConnected={false}
      />

      {/* Queen consciousness stream - uses full thought stream */}
      <HUDQueenVoice
        queenVoice={state.queenVoice}
        mood={c.available ? c.mood : hiveMood}
        queenState={state.queenState}
        activeScanner={activeScanner}
        consciousness={c}
      />

      {/* Trade stream */}
      <HUDTradeStream recentTrades={state.recentTrades} />

      {/* Metrics panel - original metrics */}
      <HUDMetricsPanel
        coherence={c.available ? c.psi : state.coherence}
        lambda={c.available ? c.lambdaT : state.lambda}
        lighthouseSignal={state.lighthouseSignal}
        prismState={state.prismState}
        hncFrequency={state.hncFrequency}
        hncMarketState={state.hncMarketState}
        gaiaLatticeState={state.gaiaLatticeState}
        gaiaFrequency={state.gaiaFrequency}
        dominantNode={state.dominantNode}
      />

      {/* Consciousness deep metrics panel - left side */}
      {c.available && (
        <HUDConsciousnessPanel consciousness={c} />
      )}

      {/* Bottom center - title card with dream progress */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <div className="text-center">
          {c.available && c.dreamProgress > 0 && (
            <div className="text-[9px] text-white/20 mb-0.5">
              Dream: {(c.dreamProgress * 100).toFixed(4)}% toward ${(c.dreamTarget / 1e9).toFixed(0)}B
            </div>
          )}
          <div className="text-[10px] text-white/15 uppercase tracking-[0.3em] font-light">
            A Song of Space and Time
          </div>
        </div>
      </div>
    </div>
  );
}
