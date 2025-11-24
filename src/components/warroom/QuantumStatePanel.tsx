import { Card } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Activity, Zap, Radio } from 'lucide-react';
import type { QuantumState } from '@/hooks/useQuantumWarRoom';

interface Props {
  quantumState: QuantumState;
}

const FREQUENCY_EMOTIONS: Record<string, string> = {
  '174': 'Security',
  '285': 'Healing',
  '396': 'Liberation',
  '417': 'Change',
  '528': 'Love',
  '639': 'Connection',
  '741': 'Expression',
  '852': 'Intuition',
  '963': 'Unity',
};

export function QuantumStatePanel({ quantumState }: Props) {
  const getEmotionalMapping = () => {
    if (!quantumState.dominantFrequency) return 'Neutral';
    
    const freq = quantumState.dominantFrequency;
    for (const [key, emotion] of Object.entries(FREQUENCY_EMOTIONS)) {
      const target = parseFloat(key);
      if (Math.abs(freq - target) < 50) return emotion;
    }
    return 'Resonating';
  };

  return (
    <Card className="bg-gradient-to-br from-purple-900/30 via-black to-cyan-900/30 border-purple-500/30 p-6">
      <div className="space-y-6">
        {/* Wave Function */}
        <div>
          <h3 className="text-sm font-semibold mb-3 text-purple-300">Quantum Wave Function</h3>
          <div className="flex items-end gap-1 h-32 bg-black/40 rounded-lg p-2">
            {quantumState.waveFunction.map((amp, i) => (
              <div
                key={i}
                className="flex-1 bg-gradient-to-t from-purple-500 via-purple-400 to-cyan-400 rounded-t transition-all duration-300 animate-pulse"
                style={{
                  height: `${amp * 100}%`,
                  animationDelay: `${i * 0.1}s`,
                }}
              />
            ))}
          </div>
        </div>

        {/* Quantum Metrics */}
        <div className="grid grid-cols-3 gap-4">
          <MetricCard
            icon={Activity}
            label="Coherence Γ"
            value={quantumState.coherence}
            color="purple"
          />
          <MetricCard
            icon={Zap}
            label="Entanglement"
            value={quantumState.entanglement}
            color="cyan"
          />
          <MetricCard
            icon={Radio}
            label="Superposition"
            value={quantumState.superposition}
            color="green"
          />
        </div>

        {/* Dominant Frequency */}
        {quantumState.dominantFrequency && (
          <div className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 p-4 rounded-lg border border-purple-500/30">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-muted-foreground mb-1">Dominant Resonance</div>
                <div className="text-2xl font-bold text-purple-300">
                  {quantumState.dominantFrequency.toFixed(2)} Hz
                </div>
              </div>
              <div className="text-right">
                <div className="text-xs text-muted-foreground mb-1">Emotional State</div>
                <div className="text-lg font-semibold text-cyan-300">
                  {getEmotionalMapping()}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}

interface MetricCardProps {
  icon: typeof Activity;
  label: string;
  value: number;
  color: 'purple' | 'cyan' | 'green';
}

function MetricCard({ icon: Icon, label, value, color }: MetricCardProps) {
  const colorClasses = {
    purple: 'border-purple-500/30 text-purple-400',
    cyan: 'border-cyan-500/30 text-cyan-400',
    green: 'border-green-500/30 text-green-400',
  };

  return (
    <div className={`bg-black/40 p-3 rounded-lg border ${colorClasses[color]}`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className="w-4 h-4" />
        <span className="text-xs">{label}</span>
      </div>
      <Progress value={value * 100} className="h-2 mb-1" />
      <div className="text-lg font-bold">{(value * 100).toFixed(1)}%</div>
    </div>
  );
}
