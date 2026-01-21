import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

export interface PredictedWindow {
  startTime: Date;
  endTime: Date;
  confidence: number;
  expectedCoherence: number;
  expectedLHECount: number;
  reasoning: string;
  dayOfWeek: string;
  hourRange: string;
}

export interface HistoricalPattern {
  dayOfWeek: number;
  hour: number;
  activationRate: number;
  avgCoherence: number;
  avgLHECount: number;
  sampleSize: number;
}

export function usePredictiveWindows(daysAhead = 7) {
  const [predictions, setPredictions] = useState<PredictedWindow[]>([]);
  const [patterns, setPatterns] = useState<HistoricalPattern[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const analyzePredictiveWindows = async () => {
      setIsAnalyzing(true);
      setError(null);

      try {
        // Fetch last 30 days of scheduler history
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

        const { data: history, error: historyError } = await supabase
          .from('scheduler_history')
          .select('*')
          .gte('timestamp', thirtyDaysAgo.toISOString())
          .order('timestamp', { ascending: true });

        if (historyError) throw historyError;

        if (!history || history.length === 0) {
          setPredictions([]);
          setPatterns([]);
          setIsAnalyzing(false);
          return;
        }

        // Analyze patterns by day of week and hour
        const patternMap = new Map<string, {
          activations: number;
          totalSamples: number;
          coherenceSum: number;
          lheSum: number;
        }>();

        history.forEach(record => {
          const date = new Date(record.timestamp);
          const dayOfWeek = date.getDay();
          const hour = date.getHours();
          const key = `${dayOfWeek}-${hour}`;

          const existing = patternMap.get(key) || {
            activations: 0,
            totalSamples: 0,
            coherenceSum: 0,
            lheSum: 0,
          };

          existing.totalSamples++;
          existing.coherenceSum += record.coherence_at_action;
          existing.lheSum += record.lighthouse_events_count;

          if (record.action === 'enable') {
            existing.activations++;
          }

          patternMap.set(key, existing);
        });

        // Convert to patterns array
        const analyzedPatterns: HistoricalPattern[] = [];
        patternMap.forEach((value, key) => {
          const [dayOfWeek, hour] = key.split('-').map(Number);
          analyzedPatterns.push({
            dayOfWeek,
            hour,
            activationRate: value.activations / value.totalSamples,
            avgCoherence: value.coherenceSum / value.totalSamples,
            avgLHECount: value.lheSum / value.totalSamples,
            sampleSize: value.totalSamples,
          });
        });

        setPatterns(analyzedPatterns);

        // Generate predictions for next N days
        const now = new Date();
        const predictedWindows: PredictedWindow[] = [];

        for (let dayOffset = 0; dayOffset < daysAhead; dayOffset++) {
          const targetDate = new Date(now);
          targetDate.setDate(targetDate.getDate() + dayOffset);
          const dayOfWeek = targetDate.getDay();

          // Find patterns for this day of week
          const dayPatterns = analyzedPatterns.filter(p => p.dayOfWeek === dayOfWeek);

          if (dayPatterns.length === 0) continue;

          // Find high-probability windows (activation rate > 0.5 and sufficient samples)
          const strongPatterns = dayPatterns
            .filter(p => p.activationRate > 0.5 && p.sampleSize >= 3)
            .sort((a, b) => b.activationRate - a.activationRate);

          strongPatterns.forEach(pattern => {
            const windowStart = new Date(targetDate);
            windowStart.setHours(pattern.hour, 0, 0, 0);

            const windowEnd = new Date(windowStart);
            windowEnd.setHours(windowStart.getHours() + 1);

            // Skip past windows
            if (windowEnd < now) return;

            const confidence = Math.min(
              pattern.activationRate * (Math.min(pattern.sampleSize, 10) / 10),
              1
            );

            const dayNames = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
            
            predictedWindows.push({
              startTime: windowStart,
              endTime: windowEnd,
              confidence,
              expectedCoherence: pattern.avgCoherence,
              expectedLHECount: pattern.avgLHECount,
              reasoning: `Historical data shows ${(pattern.activationRate * 100).toFixed(0)}% activation rate during this window (${pattern.sampleSize} samples)`,
              dayOfWeek: dayNames[pattern.dayOfWeek],
              hourRange: `${String(pattern.hour).padStart(2, '0')}:00-${String(pattern.hour + 1).padStart(2, '0')}:00`,
            });
          });
        }

        // Sort by start time
        predictedWindows.sort((a, b) => a.startTime.getTime() - b.startTime.getTime());

        setPredictions(predictedWindows);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
        setError(errorMessage);
        console.error('Predictive windows analysis error:', err);
      } finally {
        setIsAnalyzing(false);
      }
    };

    analyzePredictiveWindows();

    // Refresh every hour
    const interval = setInterval(analyzePredictiveWindows, 60 * 60 * 1000);

    return () => clearInterval(interval);
  }, [daysAhead]);

  return {
    predictions,
    patterns,
    isAnalyzing,
    error,
    nextOptimalWindow: predictions[0],
  };
}
