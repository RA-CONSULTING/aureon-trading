import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface FieldState {
  coherence: number;
  lambdaValue: number;
  lighthouseSignal: number;
  isLHE: boolean;
  prismLevel: number | null;
  timestamp: string;
}

export interface GlyphResonance {
  frequency: number;
  resonanceStrength: number;
  isActive: boolean;
  matchReason: string;
}

export function useFieldGlyphResonance() {
  const [fieldState, setFieldState] = useState<FieldState | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const calculateGlyphResonance = (frequency: number, state: FieldState): GlyphResonance => {
    let resonanceStrength = 0;
    let matchReasons: string[] = [];
    
    // Coherence-based resonance (higher coherence = stronger resonance)
    const coherenceResonance = state.coherence * 0.4;
    resonanceStrength += coherenceResonance;
    
    // Lighthouse signal resonance
    if (state.lighthouseSignal > 0.8) {
      resonanceStrength += 0.3;
      matchReasons.push('Strong Lighthouse Signal');
    }
    
    // LHE event boost
    if (state.isLHE) {
      resonanceStrength += 0.2;
      matchReasons.push('Lighthouse Event Active');
    }
    
    // Prism level matching (higher prism = higher frequency preference)
    if (state.prismLevel !== null) {
      const prismBonus = (state.prismLevel / 5) * 0.2;
      resonanceStrength += prismBonus;
      if (state.prismLevel >= 4) {
        matchReasons.push(`Prism Level ${state.prismLevel}`);
      }
    }
    
    // Frequency-specific resonance
    // 528 Hz (love frequency) gets boost when coherence is high
    if (frequency === 528 && state.coherence > 0.945) {
      resonanceStrength += 0.3;
      matchReasons.push('Love Frequency Resonance');
    }
    
    // 963 Hz (crown/unity) resonates with high lambda values
    if (frequency === 963 && state.lambdaValue > 0.9) {
      resonanceStrength += 0.25;
      matchReasons.push('Unity Field Alignment');
    }
    
    // 396 Hz (release) resonates when system is in transition
    if (frequency === 396 && state.coherence < 0.8) {
      resonanceStrength += 0.2;
      matchReasons.push('Transition Phase');
    }
    
    // Lower frequencies resonate more during lower coherence
    if (frequency < 500 && state.coherence < 0.85) {
      resonanceStrength += 0.15;
    }
    
    // Higher frequencies resonate during high coherence
    if (frequency > 700 && state.coherence > 0.9) {
      resonanceStrength += 0.15;
    }
    
    // Lambda alignment bonus
    const lambdaBonus = state.lambdaValue * 0.2;
    resonanceStrength += lambdaBonus;
    
    // Cap at 1.0
    resonanceStrength = Math.min(resonanceStrength, 1.0);
    
    return {
      frequency,
      resonanceStrength,
      isActive: resonanceStrength > 0.6,
      matchReason: matchReasons.length > 0 ? matchReasons.join(', ') : 'Baseline Resonance',
    };
  };

  const fetchFieldState = async () => {
    try {
      // Get latest lighthouse event
      const { data: lighthouseData, error: lighthouseError } = await supabase
        .from('lighthouse_events')
        .select('*')
        .order('timestamp', { ascending: false })
        .limit(1)
        .single();

      if (lighthouseError && lighthouseError.code !== 'PGRST116') {
        throw lighthouseError;
      }

      if (lighthouseData) {
        setFieldState({
          coherence: lighthouseData.coherence,
          lambdaValue: lighthouseData.lambda_value,
          lighthouseSignal: lighthouseData.lighthouse_signal,
          isLHE: lighthouseData.is_lhe,
          prismLevel: lighthouseData.prism_level,
          timestamp: lighthouseData.timestamp,
        });
      } else {
        // Fallback: get coherence history
        const { data: coherenceData, error: coherenceError } = await supabase
          .from('coherence_history')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(1)
          .single();

        if (coherenceError && coherenceError.code !== 'PGRST116') {
          throw coherenceError;
        }

        if (coherenceData) {
          setFieldState({
            coherence: coherenceData.coherence,
            lambdaValue: coherenceData.lambda_value,
            lighthouseSignal: 0,
            isLHE: false,
            prismLevel: null,
            timestamp: coherenceData.timestamp,
          });
        }
      }

      setError(null);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch field state';
      setError(errorMessage);
      console.error('Field state fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFieldState();

    // Set up real-time subscription for lighthouse events
    const channel = supabase
      .channel('field-glyph-resonance')
      .on(
        'postgres_changes',
        {
          event: 'INSERT',
          schema: 'public',
          table: 'lighthouse_events',
        },
        (payload) => {
          const newEvent = payload.new as any;
          setFieldState({
            coherence: newEvent.coherence,
            lambdaValue: newEvent.lambda_value,
            lighthouseSignal: newEvent.lighthouse_signal,
            isLHE: newEvent.is_lhe,
            prismLevel: newEvent.prism_level,
            timestamp: newEvent.timestamp,
          });
        }
      )
      .subscribe();

    // Refresh every 30 seconds as backup
    const interval = setInterval(fetchFieldState, 30000);

    return () => {
      supabase.removeChannel(channel);
      clearInterval(interval);
    };
  }, []);

  return {
    fieldState,
    isLoading,
    error,
    calculateGlyphResonance,
  };
}
