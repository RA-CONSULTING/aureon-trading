import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface TemporalPattern {
  day: number;
  month: number;
  year: number;
  dayOfYear: number;
  lunarCycle: number;
  solarCycle: number;
  harmonicPhase: number;
}

interface AlignmentWindow {
  timestamp: Date;
  alignmentScore: number;
  coherence: number;
  pattern: string;
  nextPeak: Date;
  cyclePhase: 'ascending' | 'peak' | 'descending' | 'trough';
}

interface TemporalAlignment {
  currentAlignment: number;
  birthPattern: TemporalPattern;
  currentPattern: TemporalPattern;
  optimalWindows: AlignmentWindow[];
  nextOptimal: Date;
  cycleResonance: number;
}

export function useTemporalAlignment(birthdate: string = '1991-11-02') {
  const [alignment, setAlignment] = useState<TemporalAlignment | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const calculateTemporalPatterns = (date: Date): TemporalPattern => {
      const day = date.getDate();
      const month = date.getMonth() + 1;
      const year = date.getFullYear();
      
      // Day of year (1-365/366)
      const startOfYear = new Date(year, 0, 1);
      const dayOfYear = Math.floor((date.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24)) + 1;
      
      // Lunar cycle approximation (29.53 days)
      const lunarPhase = (dayOfYear % 29.53) / 29.53;
      
      // Solar cycle within year (0-1)
      const solarCycle = dayOfYear / 365.25;
      
      // Harmonic phase based on birthdate numbers
      // 02/11/1991 → 2 + 11 + 1991 = 2004 → 2+0+0+4 = 6
      const harmonicBase = day + month + year;
      const harmonicReduced = harmonicBase.toString().split('').reduce((sum, digit) => sum + parseInt(digit), 0);
      const harmonicPhase = (harmonicReduced % 9) / 9; // Reduce to 0-1 scale
      
      return {
        day,
        month,
        year,
        dayOfYear,
        lunarCycle: lunarPhase,
        solarCycle,
        harmonicPhase
      };
    };

    const calculateAlignment = (birth: TemporalPattern, current: TemporalPattern): number => {
      // Calculate temporal resonance between birth and current patterns
      
      // Day/Month alignment (0-1)
      const dayAlignment = 1 - Math.abs(birth.day - current.day) / 31;
      const monthAlignment = 1 - Math.abs(birth.month - current.month) / 12;
      
      // Lunar cycle alignment
      const lunarAlignment = 1 - Math.abs(birth.lunarCycle - current.lunarCycle);
      
      // Solar cycle alignment (seasonal)
      const solarAlignment = 1 - Math.abs(birth.solarCycle - current.solarCycle);
      
      // Harmonic resonance
      const harmonicAlignment = 1 - Math.abs(birth.harmonicPhase - current.harmonicPhase);
      
      // Weighted average with emphasis on harmonic and lunar cycles
      const alignment = (
        dayAlignment * 0.15 +
        monthAlignment * 0.15 +
        lunarAlignment * 0.25 +
        solarAlignment * 0.2 +
        harmonicAlignment * 0.25
      );
      
      return alignment;
    };

    const findOptimalWindows = async (birthPattern: TemporalPattern): Promise<AlignmentWindow[]> => {
      try {
        // Fetch recent coherence history
        const { data: coherenceData } = await supabase
          .from('coherence_history')
          .select('*')
          .order('timestamp', { ascending: false })
          .limit(100);

        if (!coherenceData) return [];

        // Calculate alignment scores for historical data
        const windows: AlignmentWindow[] = coherenceData
          .map(record => {
            const timestamp = new Date(record.timestamp);
            const pattern = calculateTemporalPatterns(timestamp);
            const alignmentScore = calculateAlignment(birthPattern, pattern);
            
            // Determine cycle phase based on alignment trend
            const getCyclePhase = (score: number): AlignmentWindow['cyclePhase'] => {
              if (score >= 0.8) return 'peak';
              if (score >= 0.6) return 'ascending';
              if (score >= 0.4) return 'descending';
              return 'trough';
            };

            return {
              timestamp,
              alignmentScore,
              coherence: record.coherence,
              pattern: `D:${pattern.day} M:${pattern.month} H:${pattern.harmonicPhase.toFixed(2)}`,
              nextPeak: new Date(timestamp.getTime() + 29.53 * 24 * 60 * 60 * 1000), // Next lunar cycle
              cyclePhase: getCyclePhase(alignmentScore)
            };
          })
          .filter(w => w.alignmentScore > 0.6) // Only show strong alignments
          .sort((a, b) => b.alignmentScore - a.alignmentScore)
          .slice(0, 10);

        return windows;
      } catch (error) {
        console.error('Error fetching optimal windows:', error);
        return [];
      }
    };

    const calculateNextOptimal = (birthPattern: TemporalPattern): Date => {
      const now = new Date();
      const currentPattern = calculateTemporalPatterns(now);
      
      // Calculate days until next strong alignment
      // This occurs when lunar cycle aligns with birth lunar cycle
      const lunarDiff = birthPattern.lunarCycle - currentPattern.lunarCycle;
      const daysToNextLunar = lunarDiff > 0 ? lunarDiff * 29.53 : (1 + lunarDiff) * 29.53;
      
      // Also consider seasonal alignment (birth month)
      const monthDiff = birthPattern.month - (now.getMonth() + 1);
      const daysToNextSeasonal = monthDiff > 0 ? monthDiff * 30 : (12 + monthDiff) * 30;
      
      // Choose the nearer alignment
      const daysToNext = Math.min(daysToNextLunar, daysToNextSeasonal);
      
      return new Date(now.getTime() + daysToNext * 24 * 60 * 60 * 1000);
    };

    const updateAlignment = async () => {
      try {
        const birth = new Date(birthdate);
        const now = new Date();
        
        const birthPattern = calculateTemporalPatterns(birth);
        const currentPattern = calculateTemporalPatterns(now);
        
        const currentAlignment = calculateAlignment(birthPattern, currentPattern);
        const optimalWindows = await findOptimalWindows(birthPattern);
        const nextOptimal = calculateNextOptimal(birthPattern);
        
        // Calculate cycle resonance (0-1) based on multiple factors
        const cycleResonance = (
          currentAlignment * 0.4 +
          (optimalWindows.length > 0 ? optimalWindows[0].alignmentScore : 0) * 0.3 +
          (currentPattern.lunarCycle > 0.9 || currentPattern.lunarCycle < 0.1 ? 0.3 : 0) // New moon / full moon bonus
        );
        
        setAlignment({
          currentAlignment,
          birthPattern,
          currentPattern,
          optimalWindows,
          nextOptimal,
          cycleResonance
        });
      } catch (error) {
        console.error('Error calculating temporal alignment:', error);
      } finally {
        setLoading(false);
      }
    };

    updateAlignment();

    // Update every minute
    const interval = setInterval(updateAlignment, 60000);

    return () => clearInterval(interval);
  }, [birthdate]);

  return { alignment, loading };
}
