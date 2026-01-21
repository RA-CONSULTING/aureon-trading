import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';

interface HistoricalDataPoint {
  timestamp: string;
  coherence: number;
  lambdaValue: number;
  lighthouseSignal: number;
  isLHE: boolean;
  prismLevel: number | null;
}

interface TradeExecution {
  timestamp: string;
  symbol: string;
  side: string;
  executedPrice: number;
  quantity: number;
  status: string;
  coherence: number;
}

interface GlyphActivationPeriod {
  frequency: number;
  glyphName: string;
  startTime: string;
  endTime: string;
  avgResonance: number;
  peakResonance: number;
  duration: number;
}

interface TradingWindow {
  startTime: string;
  endTime: string;
  profitableTradesCount: number;
  totalTradesCount: number;
  winRate: number;
  avgCoherence: number;
  dominantFrequency: number | null;
}

export interface CorrelationData {
  glyphActivations: GlyphActivationPeriod[];
  tradingWindows: TradingWindow[];
  correlationScore: number;
  insights: string[];
}

const GLYPH_FREQUENCIES = [396, 432, 528, 639, 741, 852, 963];
const GLYPH_NAMES = [
  'Release (396 Hz)',
  'Harmony (432 Hz)',
  'Love (528 Hz)',
  'Connection (639 Hz)',
  'Expression (741 Hz)',
  'Intuition (852 Hz)',
  'Unity (963 Hz)',
];

export function useGlyphTradingCorrelation(daysBack = 7) {
  const [correlation, setCorrelation] = useState<CorrelationData | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const calculateGlyphResonance = (frequency: number, coherence: number, lambda: number, lighthouse: number, isLHE: boolean): number => {
    let resonance = coherence * 0.4 + lambda * 0.2;
    
    if (lighthouse > 0.8) resonance += 0.3;
    if (isLHE) resonance += 0.2;
    
    if (frequency === 528 && coherence > 0.945) resonance += 0.3;
    if (frequency === 963 && lambda > 0.9) resonance += 0.25;
    if (frequency < 500 && coherence < 0.85) resonance += 0.15;
    if (frequency > 700 && coherence > 0.9) resonance += 0.15;
    
    return Math.min(resonance, 1.0);
  };

  const analyzeCorrelation = async () => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const startDate = new Date();
      startDate.setDate(startDate.getDate() - daysBack);

      // Fetch lighthouse events for field state
      const { data: lighthouseData, error: lighthouseError } = await supabase
        .from('lighthouse_events')
        .select('*')
        .gte('timestamp', startDate.toISOString())
        .order('timestamp', { ascending: true });

      if (lighthouseError) throw lighthouseError;

      // Fetch trading executions
      const { data: tradesData, error: tradesError } = await supabase
        .from('trading_executions')
        .select('*')
        .gte('created_at', startDate.toISOString())
        .order('created_at', { ascending: true });

      if (tradesError) throw tradesError;

      if (!lighthouseData || lighthouseData.length === 0) {
        setCorrelation({
          glyphActivations: [],
          tradingWindows: [],
          correlationScore: 0,
          insights: ['Insufficient historical data for correlation analysis'],
        });
        setIsAnalyzing(false);
        return;
      }

      // Convert lighthouse data to historical points
      const historicalPoints: HistoricalDataPoint[] = lighthouseData.map(event => ({
        timestamp: event.timestamp,
        coherence: event.coherence,
        lambdaValue: event.lambda_value,
        lighthouseSignal: event.lighthouse_signal,
        isLHE: event.is_lhe,
        prismLevel: event.prism_level,
      }));

      // Analyze glyph activations (periods when resonance > 0.6)
      const glyphActivations: GlyphActivationPeriod[] = [];
      
      GLYPH_FREQUENCIES.forEach((frequency, freqIdx) => {
        let currentActivation: GlyphActivationPeriod | null = null;
        let resonanceSum = 0;
        let resonanceCount = 0;
        let peakResonance = 0;

        historicalPoints.forEach((point, idx) => {
          const resonance = calculateGlyphResonance(
            frequency,
            point.coherence,
            point.lambdaValue,
            point.lighthouseSignal,
            point.isLHE
          );

          if (resonance > 0.6) {
            if (!currentActivation) {
              currentActivation = {
                frequency,
                glyphName: GLYPH_NAMES[freqIdx],
                startTime: point.timestamp,
                endTime: point.timestamp,
                avgResonance: 0,
                peakResonance: resonance,
                duration: 0,
              };
            } else {
              currentActivation.endTime = point.timestamp;
            }
            
            resonanceSum += resonance;
            resonanceCount++;
            peakResonance = Math.max(peakResonance, resonance);
          } else {
            if (currentActivation) {
              currentActivation.avgResonance = resonanceSum / resonanceCount;
              currentActivation.peakResonance = peakResonance;
              currentActivation.duration = 
                (new Date(currentActivation.endTime).getTime() - 
                 new Date(currentActivation.startTime).getTime()) / (1000 * 60); // minutes
              
              glyphActivations.push(currentActivation);
              currentActivation = null;
              resonanceSum = 0;
              resonanceCount = 0;
              peakResonance = 0;
            }
          }
        });

        // Close any open activation
        if (currentActivation) {
          currentActivation.avgResonance = resonanceSum / resonanceCount;
          currentActivation.peakResonance = peakResonance;
          currentActivation.duration = 
            (new Date(currentActivation.endTime).getTime() - 
             new Date(currentActivation.startTime).getTime()) / (1000 * 60);
          glyphActivations.push(currentActivation);
        }
      });

      // Analyze trading windows (hourly buckets)
      const tradingWindows: TradingWindow[] = [];
      const windowSize = 60 * 60 * 1000; // 1 hour in milliseconds

      if (tradesData && tradesData.length > 0) {
        const firstTrade = new Date(tradesData[0].created_at).getTime();
        const lastTrade = new Date(tradesData[tradesData.length - 1].created_at).getTime();
        
        for (let windowStart = firstTrade; windowStart <= lastTrade; windowStart += windowSize) {
          const windowEnd = windowStart + windowSize;
          
          const windowTrades = tradesData.filter(trade => {
            const tradeTime = new Date(trade.created_at).getTime();
            return tradeTime >= windowStart && tradeTime < windowEnd;
          });

          if (windowTrades.length === 0) continue;

          const profitableTrades = windowTrades.filter(t => t.status === 'executed').length;
          const winRate = windowTrades.length > 0 ? profitableTrades / windowTrades.length : 0;
          const avgCoherence = windowTrades.reduce((sum, t) => sum + t.coherence, 0) / windowTrades.length;

          // Find dominant frequency during this window
          const windowLighthouse = lighthouseData.filter(event => {
            const eventTime = new Date(event.timestamp).getTime();
            return eventTime >= windowStart && eventTime < windowEnd;
          });

          let dominantFrequency: number | null = null;
          if (windowLighthouse.length > 0) {
            const frequencyResonances = GLYPH_FREQUENCIES.map(freq => {
              const avgResonance = windowLighthouse.reduce((sum, event) => 
                sum + calculateGlyphResonance(
                  freq,
                  event.coherence,
                  event.lambda_value,
                  event.lighthouse_signal,
                  event.is_lhe
                ), 0
              ) / windowLighthouse.length;
              return { frequency: freq, resonance: avgResonance };
            });
            
            const strongest = frequencyResonances.reduce((max, curr) => 
              curr.resonance > max.resonance ? curr : max
            );
            dominantFrequency = strongest.frequency;
          }

          tradingWindows.push({
            startTime: new Date(windowStart).toISOString(),
            endTime: new Date(windowEnd).toISOString(),
            profitableTradesCount: profitableTrades,
            totalTradesCount: windowTrades.length,
            winRate,
            avgCoherence,
            dominantFrequency,
          });
        }
      }

      // Calculate correlation score
      let correlationScore = 0;
      const insights: string[] = [];

      if (tradingWindows.length > 0 && glyphActivations.length > 0) {
        // Check how many profitable windows had strong glyph activations
        const profitableWindows = tradingWindows.filter(w => w.winRate > 0.6);
        let overlaps = 0;

        profitableWindows.forEach(window => {
          const windowStart = new Date(window.startTime).getTime();
          const windowEnd = new Date(window.endTime).getTime();

          const hasActivation = glyphActivations.some(activation => {
            const activationStart = new Date(activation.startTime).getTime();
            const activationEnd = new Date(activation.endTime).getTime();
            return (activationStart <= windowEnd && activationEnd >= windowStart);
          });

          if (hasActivation) overlaps++;
        });

        correlationScore = profitableWindows.length > 0 
          ? overlaps / profitableWindows.length 
          : 0;

        // Generate insights
        if (correlationScore > 0.7) {
          insights.push(`Strong correlation (${(correlationScore * 100).toFixed(0)}%) between glyph activations and profitable trading`);
        } else if (correlationScore > 0.4) {
          insights.push(`Moderate correlation (${(correlationScore * 100).toFixed(0)}%) detected between field resonance and trade success`);
        } else {
          insights.push(`Weak correlation (${(correlationScore * 100).toFixed(0)}%) - glyph patterns may not strongly predict trading outcomes`);
        }

        // Find most profitable frequency
        const frequencyProfitability = GLYPH_FREQUENCIES.map(freq => {
          const relevantWindows = tradingWindows.filter(w => w.dominantFrequency === freq);
          const avgWinRate = relevantWindows.length > 0
            ? relevantWindows.reduce((sum, w) => sum + w.winRate, 0) / relevantWindows.length
            : 0;
          return { frequency: freq, winRate: avgWinRate, count: relevantWindows.length };
        }).filter(f => f.count > 0);

        if (frequencyProfitability.length > 0) {
          const best = frequencyProfitability.reduce((max, curr) => 
            curr.winRate > max.winRate ? curr : max
          );
          const freqName = GLYPH_NAMES[GLYPH_FREQUENCIES.indexOf(best.frequency)];
          insights.push(`${freqName} shows highest win rate: ${(best.winRate * 100).toFixed(0)}% across ${best.count} windows`);
        }

        // High coherence insight
        const highCoherenceWindows = tradingWindows.filter(w => w.avgCoherence > 0.9);
        if (highCoherenceWindows.length > 0) {
          const avgWinRate = highCoherenceWindows.reduce((sum, w) => sum + w.winRate, 0) / highCoherenceWindows.length;
          insights.push(`High coherence (>0.9) periods show ${(avgWinRate * 100).toFixed(0)}% win rate`);
        }
      }

      setCorrelation({
        glyphActivations,
        tradingWindows,
        correlationScore,
        insights,
      });

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMessage);
      console.error('Glyph correlation analysis error:', err);
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    analyzeCorrelation();

    // Refresh every 5 minutes
    const interval = setInterval(analyzeCorrelation, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [daysBack]);

  return {
    correlation,
    isAnalyzing,
    error,
    refresh: analyzeCorrelation,
  };
}
