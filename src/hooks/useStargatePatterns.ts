import { useState, useEffect } from 'react';
import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

export interface StargatePattern {
  type: 'daily_peak' | 'hourly_cycle' | 'energy_surge' | 'coherence_wave';
  description: string;
  confidence: number;
  strength: number;
}

export interface TradingWindowPrediction {
  startTime: string;
  endTime: string;
  expectedNetworkStrength: number;
  expectedCoherence: number;
  confidence: number;
  tradingOpportunity: 'excellent' | 'good' | 'moderate' | 'poor';
  reasoning: string;
}

export interface PatternAnalysis {
  patterns: StargatePattern[];
  predictions: TradingWindowPrediction[];
  recommendation: string;
  riskFactors: string[];
}

export interface PatternAnalysisResult {
  success: boolean;
  dataPoints: number;
  timeRange: string;
  currentMetrics: {
    avgNetworkStrength: number;
    maxNetworkStrength: number;
    avgCoherence: number;
    avgGridEnergy: number;
    highCoherencePeriods: number;
  };
  analysis: PatternAnalysis;
  timestamp: string;
}

export function useStargatePatterns() {
  const [analysis, setAnalysis] = useState<PatternAnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyzePatterns = async (hoursBack = 24, predictionHours = 6) => {
    setIsAnalyzing(true);
    setError(null);

    try {
      const { data, error: functionError } = await supabase.functions.invoke(
        'analyze-stargate-patterns',
        {
          body: {
            temporalId: '02111991',
            hoursBack,
            predictionHours,
          },
        }
      );

      if (functionError) throw functionError;

      if (!data.success) {
        throw new Error(data.error || 'Analysis failed');
      }

      setAnalysis(data);
      
      const bestPrediction = data.analysis.predictions?.[0];
      if (bestPrediction) {
        toast.success('🔮 Pattern Analysis Complete', {
          description: `Next optimal window: ${bestPrediction.tradingOpportunity} opportunity`,
        });
      }

      return data;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Analysis failed';
      setError(errorMessage);
      toast.error('Pattern Analysis Failed', {
        description: errorMessage,
      });
      throw err;
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Auto-analyze on mount and every hour
  useEffect(() => {
    analyzePatterns();

    const interval = setInterval(() => {
      analyzePatterns();
    }, 60 * 60 * 1000); // Every hour

    return () => clearInterval(interval);
  }, []);

  return {
    analysis,
    isAnalyzing,
    error,
    analyzePatterns,
    nextOptimalWindow: analysis?.analysis.predictions?.[0],
    patterns: analysis?.analysis.patterns || [],
    recommendation: analysis?.analysis.recommendation,
  };
}
