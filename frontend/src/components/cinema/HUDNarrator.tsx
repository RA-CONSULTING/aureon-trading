/**
 * HUDNarrator - Documentary narration overlay
 * Fades in, holds, fades out. One caption at a time.
 * Positioned bottom-center above the title card.
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { NarratorEngine, type NarratorEvent, type NarratorEventType } from './NarratorEngine';
import type { GlobalState } from '@/core/globalSystemsManager';

interface HUDNarratorProps {
  state: GlobalState;
  onEvent?: (event: NarratorEventType) => void;
}

type Phase = 'idle' | 'fade-in' | 'hold' | 'fade-out';

export function HUDNarrator({ state, onEvent }: HUDNarratorProps) {
  const engineRef = useRef<NarratorEngine | null>(null);
  const [text, setText] = useState('');
  const [phase, setPhase] = useState<Phase>('idle');
  const phaseTimerRef = useRef<ReturnType<typeof setTimeout>>();
  const queueRef = useRef<NarratorEvent | null>(null);

  // Initialize engine once
  if (!engineRef.current) {
    engineRef.current = new NarratorEngine();
  }

  const showNarration = useCallback((event: NarratorEvent) => {
    setText(event.text);
    setPhase('fade-in');
    onEvent?.(event.type);

    // Phase timeline: fade-in 1s → hold 7s → fade-out 2s
    clearTimeout(phaseTimerRef.current);
    phaseTimerRef.current = setTimeout(() => {
      setPhase('hold');
      phaseTimerRef.current = setTimeout(() => {
        setPhase('fade-out');
        phaseTimerRef.current = setTimeout(() => {
          setPhase('idle');
          setText('');
          // Check if there's a queued narration
          if (queueRef.current) {
            const next = queueRef.current;
            queueRef.current = null;
            setTimeout(() => showNarration(next), 500);
          }
        }, 2000);
      }, 7000);
    }, 1000);
  }, [onEvent]);

  // Tick the narrator engine every 3 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (!engineRef.current) return;
      const event = engineRef.current.tick(state);
      if (!event) return;

      if (phase === 'idle') {
        showNarration(event);
      } else {
        // Queue it - only keep latest
        queueRef.current = event;
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [state, phase, showNarration]);

  // Cleanup
  useEffect(() => {
    return () => clearTimeout(phaseTimerRef.current);
  }, []);

  if (!text) return null;

  const opacity = phase === 'fade-in' ? 1 : phase === 'hold' ? 1 : phase === 'fade-out' ? 0 : 0;
  const translateY = phase === 'fade-in' ? 0 : phase === 'idle' ? 8 : 0;

  return (
    <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-10 pointer-events-none max-w-2xl w-full px-8">
      <div
        className="text-center px-6 py-3 rounded-xl backdrop-blur-md bg-black/20 border border-white/[0.04]"
        style={{
          opacity,
          transform: `translateY(${translateY}px)`,
          transition: phase === 'fade-in'
            ? 'opacity 1s ease-out, transform 1s ease-out'
            : phase === 'fade-out'
            ? 'opacity 2s ease-in'
            : 'none',
        }}
      >
        <p className="text-sm italic text-white/55 tracking-wide leading-relaxed font-light">
          {text}
        </p>
      </div>
    </div>
  );
}
