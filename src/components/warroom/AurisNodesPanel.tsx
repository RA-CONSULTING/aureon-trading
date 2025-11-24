import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface AurisNodesPanelProps {
  coherence: number;
  lighthouse: number;
}

const AURIS_NODES = [
  { name: 'Tiger', emoji: '🐯', threshold: 0.7 },
  { name: 'Falcon', emoji: '🦅', threshold: 0.7 },
  { name: 'Hummingbird', emoji: '🐦', threshold: 0.7 },
  { name: 'Dolphin', emoji: '🐬', threshold: 0.7 },
  { name: 'Deer', emoji: '🦌', threshold: 0.7 },
  { name: 'Owl', emoji: '🦉', threshold: 0.7 },
  { name: 'Panda', emoji: '🐼', threshold: 0.7 },
  { name: 'CargoShip', emoji: '🚢', threshold: 0.7 },
  { name: 'Clownfish', emoji: '🐠', threshold: 0.7 },
];

export function AurisNodesPanel({ coherence, lighthouse }: AurisNodesPanelProps) {
  // Simulate node activation based on coherence (in real system, would come from Master Equation)
  const getNodeActive = (index: number) => {
    // Simple simulation: nodes activate based on coherence level
    const threshold = 0.6 + (index * 0.04);
    return coherence >= threshold;
  };

  const activeCount = AURIS_NODES.filter((_, i) => getNodeActive(i)).length;
  const hasConsensus = activeCount >= 6; // 6/9 consensus required
  const dominantNode = AURIS_NODES[Math.floor(Math.random() * activeCount)] || AURIS_NODES[0];

  return (
    <Card className="p-6 bg-card/50 backdrop-blur border-primary/20">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            🦁 9 AURIS NODES
          </h3>
          <div className="flex items-center gap-3">
            <Badge variant={hasConsensus ? "default" : "secondary"}>
              Votes: {activeCount}/9
            </Badge>
            <Badge variant="outline">
              Dominant: {dominantNode.emoji} {dominantNode.name}
            </Badge>
            <Badge variant={hasConsensus ? "default" : "destructive"}>
              {hasConsensus ? '✅ Consensus' : '⏳ No Consensus'}
            </Badge>
          </div>
        </div>

        {/* Nodes Grid */}
        <div className="grid grid-cols-3 md:grid-cols-9 gap-4">
          {AURIS_NODES.map((node, index) => {
            const isActive = getNodeActive(index);
            const isDominant = node.name === dominantNode.name && isActive;

            return (
              <div
                key={node.name}
                className={cn(
                  "flex flex-col items-center justify-center p-4 rounded-lg border-2 transition-all",
                  isActive 
                    ? "bg-primary/10 border-primary shadow-lg shadow-primary/20" 
                    : "bg-muted/20 border-muted opacity-40",
                  isDominant && "ring-4 ring-primary/50 scale-110"
                )}
              >
                <div className="text-4xl mb-2">
                  {isActive ? node.emoji : '⚪'}
                </div>
                <p className="text-xs font-medium text-center">
                  {node.name}
                </p>
              </div>
            );
          })}
        </div>

        {/* Field Metrics */}
        <div className="flex items-center justify-between pt-4 border-t border-border/50">
          <div className="flex items-center gap-6">
            <div>
              <p className="text-xs text-muted-foreground">Coherence (Γ)</p>
              <p className={cn(
                "text-2xl font-bold font-mono",
                coherence >= 0.945 ? "text-green-500" : "text-yellow-500"
              )}>
                {coherence.toFixed(3)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Lighthouse (L)</p>
              <p className={cn(
                "text-2xl font-bold font-mono",
                lighthouse >= 0.7 ? "text-green-500" : "text-yellow-500"
              )}>
                {lighthouse.toFixed(3)}
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Active Nodes</p>
              <p className="text-2xl font-bold font-mono text-primary">
                {activeCount}/9
              </p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground">Status</p>
              <p className={cn(
                "text-lg font-bold",
                hasConsensus ? "text-green-500" : "text-yellow-500"
              )}>
                {hasConsensus ? '🟢 READY' : '🟡 WAIT'}
              </p>
            </div>
          </div>

          <div className="text-right">
            <p className="text-xs text-muted-foreground mb-1">Master Equation</p>
            <p className="text-sm font-mono text-primary">
              Λ(t) = S(t) + O(t) + E(t)
            </p>
          </div>
        </div>
      </div>
    </Card>
  );
}
