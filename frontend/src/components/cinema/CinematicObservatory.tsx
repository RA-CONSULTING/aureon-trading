/**
 * CinematicObservatory - Main page wrapper
 * "A Song of Space and Time"
 *
 * Fullscreen cinematic view of the Queens trading system as a living cosmos.
 * Data-driven 3D scene with glassmorphic HUD overlay.
 */

import { useGlobalState } from '@/hooks/useGlobalState';
import { useHiveState } from '@/hooks/useHiveState';
import { CinematicScene } from './CinematicScene';
import { CinematicHUD } from './CinematicHUD';

interface CinematicObservatoryProps {
  onExit?: () => void;
}

export function CinematicObservatory({ onExit }: CinematicObservatoryProps) {
  const state = useGlobalState();
  const { hiveState } = useHiveState(true, 3000);

  return (
    <div className="fixed inset-0 bg-black overflow-hidden" style={{ fontFamily: "'Source Sans Pro', sans-serif" }}>
      {/* 3D Scene - full viewport */}
      <CinematicScene
        state={state}
        hiveMood={hiveState.mood}
      />

      {/* HUD Overlay */}
      <CinematicHUD
        state={state}
        hiveMood={hiveState.mood}
        activeScanner={hiveState.active_scanner}
      />

      {/* Exit button */}
      {onExit && (
        <button
          onClick={onExit}
          className="absolute top-4 right-4 z-20 px-3 py-1.5 rounded-lg backdrop-blur-xl bg-black/30 border border-white/[0.08] text-white/40 text-xs hover:text-white/70 hover:bg-black/50 transition-all pointer-events-auto cursor-pointer"
        >
          EXIT OBSERVATORY
        </button>
      )}

      {/* Loading state */}
      {!state.isInitialized && (
        <div className="absolute inset-0 z-30 flex items-center justify-center bg-black">
          <div className="text-center">
            <div className="w-12 h-12 rounded-full border border-white/10 border-t-cyan-400 animate-spin mx-auto mb-4" />
            <div className="text-sm text-white/30 tracking-widest uppercase">
              Initializing Observatory
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
