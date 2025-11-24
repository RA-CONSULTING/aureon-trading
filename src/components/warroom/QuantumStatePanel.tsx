import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import type { QuantumState } from '@/hooks/useQuantumWarRoom';

interface Props {
  quantumState: QuantumState;
  hiveMindCoherence: number;
}

export function QuantumStatePanel({ quantumState, hiveMindCoherence }: Props) {
  const getCoherenceColor = (coherence: number) => {
    if (coherence >= 0.945) return 'text-green-500';
    if (coherence >= 0.85) return 'text-yellow-500';
    return 'text-red-500';
  };

  const getPrismColor = (level: number) => {
    if (level >= 4) return 'text-purple-500';
    if (level >= 3) return 'text-blue-500';
    if (level >= 2) return 'text-yellow-500';
    return 'text-gray-500';
  };

  return (
    <Card className="bg-card/50 backdrop-blur border-primary/20">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>🌊 Quantum Field State</span>
          {quantumState.isLHE && (
            <Badge variant="destructive" className="animate-pulse">
              🔥 LHE ACTIVE
            </Badge>
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {/* Coherence Γ */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Coherence (Γ)</p>
            <p className={`text-2xl font-bold ${getCoherenceColor(quantumState.coherence)}`}>
              {(quantumState.coherence * 100).toFixed(1)}%
            </p>
          </div>

          {/* Lambda Λ(t) */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Lambda Λ(t)</p>
            <p className="text-2xl font-bold text-primary">
              {quantumState.lambda.toFixed(3)}
            </p>
          </div>

          {/* Lighthouse Signal */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Lighthouse (L)</p>
            <p className="text-2xl font-bold text-blue-500">
              {quantumState.lighthouseSignal.toFixed(2)}
            </p>
          </div>

          {/* Prism Level */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Prism Level</p>
            <p className={`text-2xl font-bold ${getPrismColor(quantumState.prismLevel)}`}>
              {quantumState.prismLevel}/5
            </p>
          </div>

          {/* Dominant Node */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Dominant Node</p>
            <p className="text-lg font-bold text-yellow-500">
              {quantumState.dominantNode || 'None'}
            </p>
          </div>

          {/* Prism State */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Prism State</p>
            <Badge variant="outline" className="text-xs">
              {quantumState.prismState}
            </Badge>
          </div>

          {/* Hive Mind Coherence */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Hive Mind</p>
            <p className="text-lg font-bold text-purple-500">
              {(hiveMindCoherence * 100).toFixed(0)}%
            </p>
          </div>

          {/* Frequency */}
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground">Frequency</p>
            <p className="text-lg font-bold text-green-500">
              {quantumState.dominantFrequency ? `${quantumState.dominantFrequency}Hz` : '--'}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
