import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Info } from "lucide-react";

interface AurisNodeData {
  name: string;
  response: number;
  sensitivity: string;
  formula: string;
  color: string;
}

interface AurisNodesVisualizationProps {
  nodeResponses: Record<string, number>;
  dominantNode: string;
}

export function AurisNodesVisualization({ nodeResponses, dominantNode }: AurisNodesVisualizationProps) {
  const nodes: AurisNodeData[] = [
    {
      name: "Tiger",
      response: nodeResponses.Tiger || 0,
      sensitivity: "Volatility × spread amplification",
      formula: "f₁ = σ·Δ·tanh(μ)",
      color: "hsl(var(--chart-1))"
    },
    {
      name: "Falcon",
      response: nodeResponses.Falcon || 0,
      sensitivity: "Momentum × volume correlation",
      formula: "f₂ = μ·log(1+V)",
      color: "hsl(var(--chart-2))"
    },
    {
      name: "Hummingbird",
      response: nodeResponses.Hummingbird || 0,
      sensitivity: "Inverse volatility (stability)",
      formula: "f₃ = α/(σ+ε)",
      color: "hsl(var(--chart-3))"
    },
    {
      name: "Dolphin",
      response: nodeResponses.Dolphin || 0,
      sensitivity: "Sinusoidal momentum oscillation",
      formula: "f₄ = sin(ωμ)·Γ",
      color: "hsl(var(--chart-4))"
    },
    {
      name: "Deer",
      response: nodeResponses.Deer || 0,
      sensitivity: "Multi-factor linear combination",
      formula: "f₅ = β₁P + β₂V + β₃σ",
      color: "hsl(var(--chart-5))"
    },
    {
      name: "Owl",
      response: nodeResponses.Owl || 0,
      sensitivity: "Cosine momentum with memory",
      formula: "f₆ = cos(ωμ)·E(t-1)",
      color: "hsl(var(--chart-1))"
    },
    {
      name: "Panda",
      response: nodeResponses.Panda || 0,
      sensitivity: "High volume, low volatility",
      formula: "f₇ = V·(1-σ²)",
      color: "hsl(var(--chart-2))"
    },
    {
      name: "CargoShip",
      response: nodeResponses.CargoShip || 0,
      sensitivity: "Superlinear volume response",
      formula: "f₈ = V^1.5",
      color: "hsl(var(--chart-3))"
    },
    {
      name: "Clownfish",
      response: nodeResponses.Clownfish || 0,
      sensitivity: "Micro-price changes damped",
      formula: "f₉ = |ΔP|·e^(-σ)",
      color: "hsl(var(--chart-4))"
    }
  ];

  const maxResponse = Math.max(...nodes.map(n => Math.abs(n.response)), 0.01);

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-xl font-bold">9 Auris Nodes Substrate</CardTitle>
            <CardDescription>Multi-dimensional market perception functions</CardDescription>
          </div>
          <Badge variant="outline" className="text-primary">
            Dominant: {dominantNode}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {nodes.map((node) => {
            const normalizedValue = Math.abs(node.response) / maxResponse * 100;
            const isNegative = node.response < 0;
            const isDominant = node.name === dominantNode;

            return (
              <div
                key={node.name}
                className={`p-4 rounded-lg border transition-all ${
                  isDominant 
                    ? 'border-primary bg-primary/5 shadow-sm' 
                    : 'border-border/30 bg-background/30'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-foreground">{node.name}</span>
                    {isDominant && (
                      <Badge variant="default" className="text-xs">Dominant</Badge>
                    )}
                    <TooltipProvider>
                      <Tooltip>
                        <TooltipTrigger>
                          <Info className="h-4 w-4 text-muted-foreground" />
                        </TooltipTrigger>
                        <TooltipContent className="max-w-xs">
                          <p className="font-mono text-xs mb-1">{node.formula}</p>
                          <p className="text-xs text-muted-foreground">{node.sensitivity}</p>
                        </TooltipContent>
                      </Tooltip>
                    </TooltipProvider>
                  </div>
                  <span className={`text-sm font-mono ${isNegative ? 'text-destructive' : 'text-primary'}`}>
                    {isNegative ? '' : '+'}{node.response.toFixed(4)}
                  </span>
                </div>
                <div className="space-y-1">
                  <Progress 
                    value={normalizedValue} 
                    className="h-2"
                    style={{ 
                      '--progress-background': node.color 
                    } as React.CSSProperties}
                  />
                  <p className="text-xs text-muted-foreground">{node.sensitivity}</p>
                </div>
              </div>
            );
          })}
        </div>
        
        <div className="mt-6 p-4 bg-muted/30 rounded-lg border border-border/30">
          <p className="text-xs text-muted-foreground">
            <strong>Substrate Field:</strong> S(t) = Σ wᵢ·fᵢ(M(t)) where M(t) = [P, V, σ, μ, Δ]
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
