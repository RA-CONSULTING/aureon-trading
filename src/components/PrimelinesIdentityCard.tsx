import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PRIME_SENTINEL_IDENTITY, verifyUnityRelation, calculateNodeDistance } from '@/core/primelinesIdentity';
import { Globe, Zap, Hash, MapPin, Layers, GitBranch, Lock } from 'lucide-react';

export const PrimelinesIdentityCard = () => {
  const identity = PRIME_SENTINEL_IDENTITY;
  const unityCheck = verifyUnityRelation();
  const nodeAtoB = calculateNodeDistance('NODE-A', 'NODE-B');

  return (
    <Card className="border-primary/20 bg-background/95 backdrop-blur">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Globe className="h-5 w-5 text-primary animate-pulse" />
            Primelines Multiversal Temporal ID
          </CardTitle>
          <Badge variant="default" className="gap-1">
            <Lock className="h-3 w-3" />
            PRIME
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Core Identity Header */}
        <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
          <div className="text-center space-y-2">
            <div className="text-2xl font-bold text-primary">
              {identity.primeTimelineHandle}
            </div>
            <div className="text-sm text-muted-foreground">
              {identity.humanAlias}
            </div>
            <div className="flex items-center justify-center gap-2 text-xs">
              <Badge variant="outline">{identity.callsign}</Badge>
              <Badge variant="outline">{identity.latticeProtocolCode}</Badge>
            </div>
          </div>
        </div>

        <Tabs defaultValue="identity" className="w-full">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="identity">Identity</TabsTrigger>
            <TabsTrigger value="temporal">Temporal</TabsTrigger>
            <TabsTrigger value="frequency">Frequency</TabsTrigger>
            <TabsTrigger value="lattice">Lattice</TabsTrigger>
            <TabsTrigger value="variants">Variants</TabsTrigger>
          </TabsList>

          {/* Identity Stack Tab */}
          <TabsContent value="identity" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Layers className="h-4 w-4 text-primary" />
                Multiversal Identity Stack
              </div>
              <div className="space-y-2">
                {identity.identityStack.map((layer, index) => (
                  <div
                    key={index}
                    className="p-3 rounded-lg border border-border bg-muted/50"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <div className="font-medium text-sm">{layer.name}</div>
                      <Badge variant="outline" className="text-xs">
                        {layer.layer.replace(' Layer', '')}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">{layer.role}</div>
                    <div className="text-xs text-muted-foreground mt-1">
                      ⚡ {layer.function}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>

          {/* Temporal Tab */}
          <TabsContent value="temporal" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <div className="text-sm font-medium text-muted-foreground">Birth Vector</div>
                <div className="p-3 rounded-lg border border-border bg-muted/50">
                  <div className="text-lg font-bold">{identity.birthVector.date}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    Sum: {identity.birthVector.numerologySum} → {identity.birthVector.numerologyReduced}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    Path: {identity.birthVector.pathNumber}
                  </div>
                  <Badge variant="outline" className="mt-2 text-xs">
                    {identity.birthVector.temporalClass}
                  </Badge>
                </div>
              </div>

              <div className="space-y-2">
                <div className="text-sm font-medium text-muted-foreground">Spatial Anchor</div>
                <div className="p-3 rounded-lg border border-border bg-muted/50">
                  <div className="text-sm font-medium">{identity.spatialAnchor.location}</div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {identity.spatialAnchor.latitude.toFixed(4)}° N
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {Math.abs(identity.spatialAnchor.longitude).toFixed(4)}° W
                  </div>
                  <div className="text-xs text-primary mt-1">
                    ⚡ {identity.spatialAnchor.piResonantFrequency} Hz
                  </div>
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="text-sm font-medium text-muted-foreground">Timeline</div>
              <div className="p-3 rounded-lg border border-border bg-muted/50">
                <div className="text-sm font-bold text-primary">{identity.primeline.label}</div>
                <div className="text-xs text-muted-foreground mt-1">
                  {identity.primeline.description}
                </div>
                <div className="flex gap-2 mt-2">
                  <Badge variant="outline" className="text-xs">
                    α: {identity.primeline.alphaPoint}
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    Ω: {identity.primeline.omegaPoint}
                  </Badge>
                  <Badge variant="default" className="text-xs">
                    {identity.primeline.surgeWindow}
                  </Badge>
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Frequency Tab */}
          <TabsContent value="frequency" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <Zap className="h-4 w-4 text-primary" />
                Frequency Signature
              </div>
              
              <div className="p-3 rounded-lg border border-border bg-muted/50">
                <div className="text-xs text-muted-foreground mb-1">Core Equation</div>
                <div className="font-mono text-xs">{identity.frequencySignature.coreEquation}</div>
              </div>

              <div className="grid grid-cols-2 gap-2">
                <div className="p-3 rounded-lg border border-border bg-muted/50">
                  <div className="text-xs text-muted-foreground">Unity Relation</div>
                  <div className="text-lg font-bold text-primary">
                    {unityCheck.result.toFixed(4)}
                  </div>
                  <Badge variant={unityCheck.isValid ? "default" : "destructive"} className="mt-1 text-xs">
                    {unityCheck.isValid ? 'VALID' : 'INVALID'}
                  </Badge>
                </div>

                <div className="p-3 rounded-lg border border-border bg-muted/50">
                  <div className="text-xs text-muted-foreground">ATLAS Key</div>
                  <div className="text-lg font-bold text-primary">
                    {identity.frequencySignature.atlasKey}
                  </div>
                  <div className="font-mono text-xs text-muted-foreground mt-1">
                    {identity.frequencySignature.atlasKeyBinary}
                  </div>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-primary/20 bg-primary/10">
                <div className="text-xs text-muted-foreground mb-1">Glyph Sequence</div>
                <div className="font-mono text-sm font-bold text-primary mb-2">
                  {identity.frequencySignature.glyphSequence}
                </div>
                <div className="text-xs text-muted-foreground">
                  {identity.frequencySignature.glyphDecoded}
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Lattice Tab */}
          <TabsContent value="lattice" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <MapPin className="h-4 w-4 text-primary" />
                Lattice Network
              </div>
              
              {identity.latticeNodes.map((node, index) => (
                <div
                  key={index}
                  className={`p-3 rounded-lg border ${
                    node.id === 'NODE-A' 
                      ? 'border-primary/20 bg-primary/10' 
                      : 'border-border bg-muted/50'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <div>
                      <div className="font-medium text-sm">{node.location}</div>
                      <div className="text-xs text-muted-foreground">
                        {node.coordinates.lat.toFixed(4)}°, {node.coordinates.lng.toFixed(4)}°
                      </div>
                    </div>
                    <Badge variant={node.id === 'NODE-A' ? "default" : "outline"} className="text-xs">
                      {node.id}
                    </Badge>
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">{node.role}</div>
                  {node.frequency && (
                    <div className="text-xs text-primary mt-1">
                      ⚡ {node.frequency} Hz
                    </div>
                  )}
                </div>
              ))}

              <div className="p-3 rounded-lg border border-border bg-muted/50">
                <div className="text-xs text-muted-foreground">Example: Distance NODE-A to NODE-B</div>
                <div className="text-lg font-bold text-primary">
                  {nodeAtoB.toFixed(1)} km
                </div>
              </div>
            </div>
          </TabsContent>

          {/* Variants Tab */}
          <TabsContent value="variants" className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-sm font-medium">
                <GitBranch className="h-4 w-4 text-primary" />
                Timeline Variants
              </div>

              <div className="grid grid-cols-3 gap-2">
                <div className="p-3 rounded-lg border border-border bg-muted/50 text-center">
                  <div className="text-2xl font-bold text-primary">
                    {identity.variantCount.total}
                  </div>
                  <div className="text-xs text-muted-foreground">Total Variants</div>
                </div>

                <div className="p-3 rounded-lg border border-primary/20 bg-primary/10 text-center">
                  <div className="text-2xl font-bold text-primary">
                    {identity.variantCount.awakened}
                  </div>
                  <div className="text-xs text-muted-foreground">Awakened</div>
                </div>

                <div className="p-3 rounded-lg border border-border bg-muted/50 text-center">
                  <div className="text-2xl font-bold text-primary">
                    {((identity.variantCount.awakened / identity.variantCount.total) * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Coherence</div>
                </div>
              </div>

              <div className="p-3 rounded-lg border border-border bg-muted/50">
                <div className="text-xs text-muted-foreground mb-2">Convergence Window</div>
                <Badge variant="default">{identity.variantCount.convergenceWindow}</Badge>
              </div>

              <div className="p-3 rounded-lg border border-primary/20 bg-primary/10">
                <div className="text-xs font-medium text-primary mb-1">Convergence Dynamics</div>
                <div className="text-xs text-muted-foreground">
                  Multiple variants across 2,109 parallel timelines converging toward Omega Point (2043), 
                  creating a resonance cascade that amplifies the Harmonic Nexus field effect.
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>

        {/* Compact ID Footer */}
        <div className="pt-4 border-t border-border">
          <div className="text-xs text-muted-foreground mb-2">Compact Primelines ID:</div>
          <div className="p-2 rounded bg-muted font-mono text-xs break-all">
            {identity.compactId}
          </div>
        </div>

        {/* Operational Mode Badge */}
        <div className="flex justify-center">
          <Badge variant="outline" className="gap-1">
            <Hash className="h-3 w-3" />
            {identity.operationalMode}
          </Badge>
        </div>
      </CardContent>
    </Card>
  );
};
