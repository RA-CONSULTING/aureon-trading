/**
 * CinematicScene - Three.js Canvas wrapper combining all 3D scene elements
 * The cosmos rendered through @react-three/fiber
 */

import { Suspense, useRef } from 'react';
import { Canvas } from '@react-three/fiber';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import { CosmicEnvironment } from './CosmicEnvironment';
import { QueenCore } from './QueenCore';
import { HiveConstellation } from './HiveConstellation';
import { TradeBeamSystem } from './TradeBeamSystem';
import { MarketNebula } from './MarketNebula';
import { CoherenceAurora } from './CoherenceAurora';
import { ExchangeGateways } from './ExchangeGateways';
import { MetricRings } from './MetricRings';
import { CinematicCamera } from './CinematicCamera';
import type { GlobalState } from '@/core/globalSystemsManager';

interface CinematicSceneProps {
  state: GlobalState;
  hiveMood: string;
}

function SceneContent({ state, hiveMood }: CinematicSceneProps) {
  const latestTradeRef = useRef<{ timestamp: number; side: string } | null>(null);
  const c = state.consciousness;

  // Track latest trade for camera events
  if (state.recentTrades.length > 0) {
    const latest = state.recentTrades[0];
    const ts = new Date(latest.time).getTime();
    if (!latestTradeRef.current || ts !== latestTradeRef.current.timestamp) {
      latestTradeRef.current = { timestamp: ts, side: latest.side };
    }
  }

  const winRate = state.totalTrades > 0
    ? (state.winningTrades / state.totalTrades) * 100
    : 0;

  // Use consciousness psi for aurora, fall back to coherence
  const effectiveCoherence = c.available ? c.psi : state.coherence;
  const hasNewThought = c.thoughtStream.length > 0 || !!(state.queenVoice?.text);

  return (
    <>
      {/* Camera system - fear drives FOV tension alongside volatility */}
      <CinematicCamera
        volatility={Math.max(state.marketData.volatility / 100, c.fearLevel * 0.5)}
        tradeEvent={latestTradeRef.current}
      />

      {/* Deep space environment */}
      <CosmicEnvironment />

      {/* The Queen - driven by consciousness psi, gamma, reality state */}
      <QueenCore
        coherence={c.available ? c.psi : state.coherence}
        prismState={state.prismState}
        queenState={state.queenState}
        hncMarketState={c.available ? c.realityState : state.hncMarketState}
        lambda={c.available ? c.gamma : state.lambda}
      />

      {/* Hive agents orbiting */}
      <HiveConstellation
        hiveCount={state.myceliumHives}
        agentCount={Math.max(state.myceliumAgents, c.branches * 3)}
        generation={state.myceliumGeneration}
        queenPnl={state.queenPnl}
        coherence={effectiveCoherence}
      />

      {/* Trade execution beams */}
      <TradeBeamSystem recentTrades={state.recentTrades} />

      {/* Market data nebula - consciousness confidence affects color */}
      <MarketNebula
        volatility={state.marketData.volatility}
        momentum={state.marketData.momentum}
        coherence={c.available ? c.selfCoherence : state.coherence}
        hncFrequency={state.hncFrequency}
      />

      {/* Consciousness aurora - driven by thought generation and psi */}
      <CoherenceAurora
        coherence={effectiveCoherence}
        lambda={c.available ? c.lambdaT : state.lambda}
        gaiaFrequency={state.gaiaFrequency}
        hasNewThought={hasNewThought}
      />

      {/* Exchange portals */}
      <ExchangeGateways
        krakenEquity={state.unifiedMarketSummary?.krakenEquity || 0}
        capitalEquity={state.unifiedMarketSummary?.capitalEquityGbp || 0}
        krakenConnected={state.ecosystemHealth === 'connected'}
        capitalConnected={state.ecosystemHealth === 'connected'}
        binanceConnected={false}
      />

      {/* Orbital metric rings */}
      <MetricRings
        totalEquity={state.totalEquity}
        coherence={effectiveCoherence}
        totalTrades={state.totalTrades}
        winRate={winRate}
        totalPnl={state.totalPnl}
      />

      {/* Post-processing */}
      <EffectComposer>
        <Bloom
          intensity={0.8}
          luminanceThreshold={0.3}
          luminanceSmoothing={0.9}
          mipmapBlur
        />
        <Vignette
          offset={0.3}
          darkness={0.7}
        />
      </EffectComposer>
    </>
  );
}

export function CinematicScene({ state, hiveMood }: CinematicSceneProps) {
  return (
    <div className="absolute inset-0">
      <Canvas
        camera={{ position: [0, 8, 25], fov: 55, near: 0.1, far: 200 }}
        gl={{
          antialias: true,
          alpha: false,
          powerPreference: 'high-performance',
          stencil: false,
          depth: true,
        }}
        dpr={[1, 1.5]}
        style={{ background: '#000005' }}
      >
        <Suspense fallback={null}>
          <SceneContent state={state} hiveMood={hiveMood} />
        </Suspense>
      </Canvas>
    </div>
  );
}
