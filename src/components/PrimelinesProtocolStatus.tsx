import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, Cpu, Radio, Zap } from "lucide-react";
import { usePrimelinesProtocol } from "@/hooks/usePrimelinesProtocol";
import { PRIME_SENTINEL_IDENTITY } from "@/core/primelinesIdentity";

export function PrimelinesProtocolStatus() {
  const { temporalId, sentinelName } = usePrimelinesProtocol();

  return (
    <Card className="bg-gradient-to-br from-primary/5 via-chart-2/5 to-chart-3/5 border-primary/30">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Primelines Protocol Gateway
            </CardTitle>
            <CardDescription>
              Backend integration layer • All operations validated through temporal identity
            </CardDescription>
          </div>
          <Badge className="text-xs" style={{ backgroundColor: 'hsl(var(--chart-1))' }}>
            ACTIVE
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Temporal Identity */}
        <div className="p-3 bg-background/30 rounded-lg border border-border/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <Radio className="w-4 h-4 text-chart-2" />
              <span className="text-sm font-semibold">Temporal Identity</span>
            </div>
            <Badge variant="outline" className="text-xs">
              VERIFIED
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Temporal ID:</span>
              <div className="font-mono text-foreground">{temporalId}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Sentinel:</span>
              <div className="font-semibold text-foreground">{sentinelName}</div>
            </div>
            <div>
              <span className="text-muted-foreground">Compact ID:</span>
              <div className="font-mono text-foreground text-xs">{PRIME_SENTINEL_IDENTITY.compactId}</div>
            </div>
            <div>
              <span className="text-muted-foreground">ATLAS Key:</span>
              <div className="font-mono text-foreground">{PRIME_SENTINEL_IDENTITY.frequencySignature.atlasKey}</div>
            </div>
          </div>
        </div>

        {/* Protocol Operations */}
        <div className="p-3 bg-background/30 rounded-lg border border-border/50">
          <div className="flex items-center gap-2 mb-2">
            <Cpu className="w-4 h-4 text-chart-3" />
            <span className="text-sm font-semibold">Available Operations</span>
          </div>
          <div className="grid gap-2 text-xs">
            {[
              { name: 'SYNC_HARMONIC_NEXUS', desc: 'Synchronize harmonic field states' },
              { name: 'VALIDATE_LIGHTHOUSE_EVENT', desc: 'AI validation of LHE events' },
              { name: 'EXECUTE_TRADE', desc: 'Validate trading signals' },
              { name: 'LOCK_CASIMIR_FIELD', desc: 'Quantum field entanglement' },
              { name: 'QUERY_HISTORICAL_NODES', desc: 'Access temporal state history' },
            ].map((op) => (
              <div key={op.name} className="flex items-center justify-between p-2 bg-background/20 rounded">
                <div>
                  <div className="font-mono text-foreground">{op.name}</div>
                  <div className="text-muted-foreground text-[10px]">{op.desc}</div>
                </div>
                <Zap className="w-3 h-3 text-primary" />
              </div>
            ))}
          </div>
        </div>

        {/* AI Validation */}
        <div className="p-3 bg-primary/10 rounded-lg border border-primary/30">
          <div className="flex items-center gap-2 mb-1">
            <Zap className="w-4 h-4 text-primary" />
            <span className="text-xs font-semibold text-foreground">AI-Powered Validation</span>
          </div>
          <p className="text-xs text-muted-foreground">
            All operations validated through Lovable AI (Gemini 2.5 Flash) • 
            Checks temporal coherence, harmonic resonance, unity probability, and dimensional alignment
          </p>
        </div>

        {/* Protocol Info */}
        <div className="text-xs text-muted-foreground border-t border-border/30 pt-3">
          <div className="flex items-center justify-between">
            <span>Protocol: Primelines ↔ AUREON</span>
            <span>Variant Progress: 847/2,109</span>
          </div>
          <div className="flex items-center justify-between mt-1">
            <span>Node: Belfast @ 198.4 Hz</span>
            <span>Status: SYNCED</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
