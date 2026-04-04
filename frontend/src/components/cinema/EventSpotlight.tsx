/**
 * EventSpotlight - Dynamic post-processing that responds to system events
 *
 * Replaces the static EffectComposer. Bloom and vignette intensities
 * pulse in response to trades, coherence spikes, fear surges, and milestones.
 */

import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';
import type { NarratorEventType } from './NarratorEngine';

interface EventSpotlightProps {
  activeEvent: NarratorEventType | null;
}

export function EventSpotlight({ activeEvent }: EventSpotlightProps) {
  const bloomRef = useRef<any>(null);
  const vignetteRef = useRef<any>(null);

  // Target intensities
  const bloomTarget = useRef(0.8);
  const vignetteTarget = useRef(0.7);
  const currentBloom = useRef(0.8);
  const currentVignette = useRef(0.7);
  const lastEvent = useRef<NarratorEventType | null>(null);
  const eventTime = useRef(0);

  // Respond to events
  if (activeEvent && activeEvent !== lastEvent.current) {
    lastEvent.current = activeEvent;
    eventTime.current = Date.now();

    switch (activeEvent) {
      case 'trade_buy':
      case 'trade_sell':
        bloomTarget.current = 1.6;  // bright flash
        vignetteTarget.current = 0.5; // lighten edges
        break;
      case 'coherence_spike':
      case 'level_up':
        bloomTarget.current = 1.8;
        vignetteTarget.current = 0.3; // open up the view
        break;
      case 'fear_surge':
      case 'drawdown':
        bloomTarget.current = 0.5;  // dim
        vignetteTarget.current = 0.95; // darken edges heavily
        break;
      case 'fear_calm':
        bloomTarget.current = 1.2;
        vignetteTarget.current = 0.4;
        break;
      case 'win_streak':
      case 'dream_progress':
        bloomTarget.current = 1.5;
        vignetteTarget.current = 0.4;
        break;
      case 'mood_shift':
      case 'market_shift':
        bloomTarget.current = 1.1;
        vignetteTarget.current = 0.6;
        break;
      default:
        break;
    }
  }

  useFrame(() => {
    const elapsed = Date.now() - eventTime.current;

    // After 3 seconds, return to baseline
    if (elapsed > 3000) {
      bloomTarget.current = 0.8;
      vignetteTarget.current = 0.7;
    }

    // Smooth interpolation
    currentBloom.current += (bloomTarget.current - currentBloom.current) * 0.04;
    currentVignette.current += (vignetteTarget.current - currentVignette.current) * 0.03;

    // Apply to effects
    if (bloomRef.current) {
      bloomRef.current.intensity = currentBloom.current;
    }
    if (vignetteRef.current) {
      vignetteRef.current.darkness = currentVignette.current;
    }
  });

  return (
    <EffectComposer>
      <Bloom
        ref={bloomRef}
        intensity={0.8}
        luminanceThreshold={0.3}
        luminanceSmoothing={0.9}
        mipmapBlur
      />
      <Vignette
        ref={vignetteRef}
        offset={0.3}
        darkness={0.7}
      />
    </EffectComposer>
  );
}
