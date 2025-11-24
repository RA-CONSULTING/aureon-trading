import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface Props {
  coherence: number;
  lighthouse: number;
}

const AURIS_NODES = [
  { name: 'Tiger', emoji: '🐯' },
  { name: 'Falcon', emoji: '🦅' },
  { name: 'Hummingbird', emoji: '🐦' },
  { name: 'Dolphin', emoji: '🐬' },
  { name: 'Deer', emoji: '🦌' },
  { name: 'Owl', emoji: '🦉' },
  { name: 'Panda', emoji: '🐼' },
  { name: 'CargoShip', emoji: '🚢' },
  { name: 'Clownfish', emoji: '🐠' },
];

export function AurisNodesOrbit({ coherence, lighthouse }: Props) {
  // Node is active if coherence > 0.7
  const activeThreshold = 0.7;
  const activeNodes = AURIS_NODES.map((node, i) => {
    const nodeCoherence = coherence + (Math.sin(i) * 0.2);
    return {
      ...node,
      isActive: nodeCoherence > activeThreshold,
      power: nodeCoherence,
    };
  });

  const activeCount = activeNodes.filter(n => n.isActive).length;
  const dominantNode = activeNodes.reduce((max, node) =>
    node.power > max.power ? node : max
  );
  const hasConsensus = activeCount >= 6;

  return (
    <Card className="bg-gradient-to-br from-purple-900/30 via-black to-cyan-900/30 border-purple-500/30 p-6">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-purple-300">9 Auris Nodes</h3>
          <Badge variant={hasConsensus ? 'default' : 'secondary'}>
            Votes: {activeCount}/9 {hasConsensus ? '✅' : '⏳'}
          </Badge>
        </div>

        {/* Orbital Display */}
        <div className="relative w-full aspect-square max-w-md mx-auto">
          <div className="absolute inset-0 rounded-full border-2 border-dashed border-purple-500/30 animate-spin-slow" />
          
          {activeNodes.map((node, i) => {
            const angle = (i / activeNodes.length) * 2 * Math.PI - Math.PI / 2;
            const radius = 40; // percentage
            const x = 50 + radius * Math.cos(angle);
            const y = 50 + radius * Math.sin(angle);

            return (
              <div
                key={node.name}
                className="absolute transform -translate-x-1/2 -translate-y-1/2 transition-all duration-500"
                style={{
                  left: `${x}%`,
                  top: `${y}%`,
                  animation: node.isActive ? 'pulse 2s infinite' : 'none',
                }}
              >
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-2xl transition-all ${
                    node.isActive
                      ? 'bg-gradient-to-br from-purple-500 to-cyan-500 shadow-lg shadow-purple-500/50 scale-110'
                      : 'bg-gray-700/50 scale-90 opacity-50'
                  } ${node === dominantNode ? 'ring-4 ring-yellow-400 scale-125' : ''}`}
                  title={`${node.name} - ${(node.power * 100).toFixed(1)}%`}
                >
                  {node.emoji}
                </div>
              </div>
            );
          })}

          {/* Center - Master Equation */}
          <div className="absolute inset-0 flex items-center justify-center">
            <div className="text-center">
              <div className="text-xs text-muted-foreground mb-1">Λ(t)</div>
              <div className="text-2xl font-bold text-purple-300">
                {(coherence + lighthouse).toFixed(3)}
              </div>
            </div>
          </div>
        </div>

        {/* Dominant Node */}
        <div className="bg-gradient-to-r from-purple-500/20 to-cyan-500/20 p-3 rounded-lg border border-purple-500/30 text-center">
          <div className="text-xs text-muted-foreground mb-1">Dominant Node</div>
          <div className="text-lg font-bold text-cyan-300">
            {dominantNode.emoji} {dominantNode.name}
          </div>
        </div>

        {/* Master Equation Formula */}
        <div className="text-center text-xs text-muted-foreground font-mono">
          Λ(t) = S(t) + O(t) + E(t)
        </div>
      </div>
    </Card>
  );
}
