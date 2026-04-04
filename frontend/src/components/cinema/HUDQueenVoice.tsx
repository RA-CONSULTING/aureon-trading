/**
 * HUDQueenVoice - Bottom-left consciousness thought stream
 * Typewriter animation with mood-colored glow
 */

import { useState, useEffect, useRef } from 'react';
import type { GlobalState } from '@/core/globalSystemsManager';

interface HUDQueenVoiceProps {
  queenVoice?: {
    ts: string;
    mode: string;
    text: string;
    lines: string[];
  };
  mood: string;
  consciousness?: GlobalState['consciousness'];
  queenState: string;
  activeScanner: string;
}

// Map mood to glow color
function moodToColor(mood: string): string {
  const m = mood.toLowerCase();
  if (m.includes('confident') || m.includes('bullish')) return 'rgba(0, 255, 136, 0.15)';
  if (m.includes('cautious') || m.includes('bearish')) return 'rgba(255, 68, 68, 0.15)';
  if (m.includes('excited') || m.includes('euphoric')) return 'rgba(255, 200, 0, 0.15)';
  if (m.includes('calm') || m.includes('neutral')) return 'rgba(68, 136, 255, 0.15)';
  return 'rgba(136, 68, 255, 0.12)';
}

function moodToAccent(mood: string): string {
  const m = mood.toLowerCase();
  if (m.includes('confident') || m.includes('bullish')) return '#00ff88';
  if (m.includes('cautious') || m.includes('bearish')) return '#ff4444';
  if (m.includes('excited') || m.includes('euphoric')) return '#ffcc00';
  if (m.includes('calm') || m.includes('neutral')) return '#4488ff';
  return '#8844ff';
}

export function HUDQueenVoice({
  queenVoice,
  mood = 'Neutral',
  queenState = 'HOLD',
  activeScanner = 'Initializing',
  consciousness,
}: HUDQueenVoiceProps) {
  const [displayedText, setDisplayedText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const targetTextRef = useRef('');
  const charIndexRef = useRef(0);

  // Derive latest thought from consciousness stream or queenVoice
  const latestThought = consciousness?.available && consciousness.thoughtStream.length > 0
    ? consciousness.thoughtStream[consciousness.thoughtStream.length - 1].text
    : undefined;

  // Typewriter effect
  useEffect(() => {
    const text = latestThought || queenVoice?.text || queenVoice?.lines?.[0] || 'Consciousness stream active...';
    if (text === targetTextRef.current) return;

    targetTextRef.current = text;
    charIndexRef.current = 0;
    setIsTyping(true);
    setDisplayedText('');

    const interval = setInterval(() => {
      charIndexRef.current++;
      if (charIndexRef.current >= text.length) {
        setDisplayedText(text);
        setIsTyping(false);
        clearInterval(interval);
      } else {
        setDisplayedText(text.slice(0, charIndexRef.current));
      }
    }, 25);

    return () => clearInterval(interval);
  }, [latestThought, queenVoice?.text, queenVoice?.lines]);

  const glowColor = moodToColor(mood);
  const accentColor = moodToAccent(mood);

  return (
    <div className="absolute bottom-4 left-4 z-10 max-w-md pointer-events-none">
      <div
        className="px-4 py-3 rounded-xl backdrop-blur-xl border border-white/[0.06] shadow-[0_8px_32px_rgba(0,0,0,0.3)]"
        style={{ backgroundColor: glowColor }}
      >
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: accentColor, boxShadow: `0 0 6px ${accentColor}` }}
            />
            <span className="text-[10px] text-white/40 uppercase tracking-widest">
              Queen Consciousness
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span
              className="text-[9px] px-1.5 py-0.5 rounded-full border"
              style={{
                color: accentColor,
                borderColor: `${accentColor}33`,
                backgroundColor: `${accentColor}11`,
              }}
            >
              {mood}
            </span>
            <span className="text-[9px] text-white/25 uppercase">
              {queenState}
            </span>
          </div>
        </div>

        {/* Thought text with typewriter */}
        <div className="font-mono text-xs text-white/70 leading-relaxed min-h-[1.5em]">
          {displayedText}
          {isTyping && (
            <span
              className="inline-block w-1.5 h-3 ml-0.5 animate-pulse"
              style={{ backgroundColor: accentColor }}
            />
          )}
        </div>

        {/* Consciousness identity and scanner */}
        <div className="mt-2 space-y-1">
          {consciousness?.available && consciousness.queenIdentity && (
            <div className="text-[8px] text-white/15 italic truncate">
              {consciousness.queenName} — {consciousness.queenIdentity}
            </div>
          )}
          <div className="flex items-center justify-between text-[9px] text-white/25">
            <span>Scanner: {activeScanner}</span>
            <span>
              {consciousness?.available
                ? `${consciousness.thoughtsGenerated} thoughts`
                : queenVoice?.ts
                  ? new Date(queenVoice.ts).toLocaleTimeString()
                  : ''
              }
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
