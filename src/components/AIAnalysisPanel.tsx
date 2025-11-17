import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { supabase } from '@/integrations/supabase/client';
import { Sparkles, Loader2, AlertCircle } from 'lucide-react';
import type { LambdaState } from '@/core/masterEquation';
import type { LighthouseState } from '@/core/lighthouseConsensus';
import type { PrismOutput } from '@/core/prism';
import type { TradingSignal } from '@/core/tradingSignals';

interface AIAnalysisPanelProps {
  lambda: LambdaState | null;
  lighthouse: LighthouseState | null;
  prism: PrismOutput | null;
  signal: TradingSignal | null;
  currentPrice: number;
  currentSymbol: string;
}

export const AIAnalysisPanel = ({
  lambda,
  lighthouse,
  prism,
  signal,
  currentPrice,
  currentSymbol,
}: AIAnalysisPanelProps) => {
  const [analysis, setAnalysis] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastAnalyzedTimestamp, setLastAnalyzedTimestamp] = useState<number>(0);

  useEffect(() => {
    // Only generate analysis when we have a significant Lighthouse Event
    if (!lighthouse?.isLHE || !signal || !lambda || !prism) {
      return;
    }

    // Avoid re-analyzing the same event too quickly (5 second cooldown)
    const now = Date.now();
    if (now - lastAnalyzedTimestamp < 5000) {
      return;
    }

    generateAnalysis();
  }, [lighthouse?.isLHE, signal?.timestamp]);

  const generateAnalysis = async () => {
    if (!lambda || !lighthouse || !prism || !signal) return;

    setIsLoading(true);
    setError(null);

    try {
      const { data, error: invokeError } = await supabase.functions.invoke('analyze-lighthouse-event', {
        body: {
          lighthouseEvent: {
            lambda: lambda.lambda,
            coherence: lambda.coherence,
            lighthouseSignal: lighthouse.L,
            confidence: lighthouse.confidence,
            isLHE: lighthouse.isLHE,
            dominantNode: lambda.dominantNode,
            prismLevel: prism.level,
            prismState: prism.state,
          },
          tradingSignal: {
            type: signal.type,
            strength: signal.strength,
            reason: signal.reason,
          },
          marketData: {
            symbol: currentSymbol,
            price: currentPrice,
            volume: 0, // Will be populated from market data
            volatility: 0,
          },
        },
      });

      if (invokeError) {
        throw invokeError;
      }

      if (data?.analysis) {
        setAnalysis(data.analysis);
        setLastAnalyzedTimestamp(Date.now());
      } else if (data?.error) {
        setError(data.error);
      }
    } catch (err) {
      console.error('AI Analysis error:', err);
      setError(err instanceof Error ? err.message : 'Failed to generate analysis');
    } finally {
      setIsLoading(false);
    }
  };

  if (!lighthouse?.isLHE && !analysis) {
    return null;
  }

  return (
    <Card className="p-6 border-2 border-primary/50 bg-gradient-to-br from-primary/5 to-background">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles className="h-5 w-5 text-primary" />
        <h3 className="text-lg font-semibold">🤖 AI Analysis</h3>
        <Badge variant="outline" className="ml-auto">
          Powered by Gemini
        </Badge>
      </div>

      {isLoading && (
        <div className="flex items-center gap-3 text-muted-foreground">
          <Loader2 className="h-4 w-4 animate-spin" />
          <p className="text-sm">Analyzing Lighthouse Event...</p>
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 p-4 rounded-lg bg-destructive/10 border border-destructive/20">
          <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium text-destructive">Analysis Error</p>
            <p className="text-sm text-destructive/80 mt-1">{error}</p>
          </div>
        </div>
      )}

      {analysis && !isLoading && (
        <div className="prose prose-sm max-w-none dark:prose-invert">
          <div className="text-sm leading-relaxed whitespace-pre-line">
            {analysis}
          </div>
        </div>
      )}

      {lighthouse?.isLHE && !analysis && !isLoading && !error && (
        <p className="text-sm text-muted-foreground italic">
          Lighthouse Event detected. AI analysis will appear shortly...
        </p>
      )}
    </Card>
  );
};
