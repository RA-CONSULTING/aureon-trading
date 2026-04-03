/**
 * CinematicHUD - HTML overlay combining all HUD panels
 * Glassmorphic sci-fi cockpit interface
 */

import { HUDTopBar } from './HUDTopBar';
import { HUDQueenVoice } from './HUDQueenVoice';
import { HUDTradeStream } from './HUDTradeStream';
import { HUDMetricsPanel } from './HUDMetricsPanel';
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

  return (
    <div className="absolute inset-0 z-10 pointer-events-none overflow-hidden">
      {/* Top bar */}
      <HUDTopBar
        totalEquity={state.totalEquity}
        totalPnl={state.totalPnl}
        cyclePnlPercent={state.cyclePnlPercent}
        winRate={winRate}
        coherence={state.coherence}
        totalTrades={state.totalTrades}
        isActive={state.isActive}
        krakenConnected={state.ecosystemHealth === 'connected'}
        capitalConnected={state.ecosystemHealth === 'connected'}
        binanceConnected={false}
      />

      {/* Queen consciousness stream */}
      <HUDQueenVoice
        queenVoice={state.queenVoice}
        mood={hiveMood}
        queenState={state.queenState}
        activeScanner={activeScanner}
      />

      {/* Trade stream */}
      <HUDTradeStream recentTrades={state.recentTrades} />

      {/* Metrics panel */}
      <HUDMetricsPanel
        coherence={state.coherence}
        lambda={state.lambda}
        lighthouseSignal={state.lighthouseSignal}
        prismState={state.prismState}
        hncFrequency={state.hncFrequency}
        hncMarketState={state.hncMarketState}
        gaiaLatticeState={state.gaiaLatticeState}
        gaiaFrequency={state.gaiaFrequency}
        dominantNode={state.dominantNode}
      />

      {/* Bottom center - title card */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2">
        <div className="text-center">
          <div className="text-[10px] text-white/15 uppercase tracking-[0.3em] font-light">
            A Song of Space and Time
          </div>
        </div>
      </div>
    </div>
  );
}
