import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { BookOpen, Zap, Brain, Waves } from "lucide-react";

export function MasterEquationEducational() {
  const [activeTab, setActiveTab] = useState("overview");

  return (
    <Card className="bg-card/50 backdrop-blur border-border/50">
      <CardHeader>
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-primary" />
          <div>
            <CardTitle className="text-xl font-bold">Master Equation Framework</CardTitle>
            <CardDescription>Interactive guide to field-theoretic market analysis</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="substrate">Substrate</TabsTrigger>
            <TabsTrigger value="observer">Observer</TabsTrigger>
            <TabsTrigger value="echo">Echo</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4 mt-4">
            <div className="p-6 bg-gradient-to-br from-primary/10 to-accent/10 rounded-lg border border-primary/30">
              <h3 className="text-lg font-bold mb-3 text-foreground">The Master Equation</h3>
              <div className="text-center py-4">
                <p className="text-3xl font-mono font-bold text-primary mb-2">
                  Λ(t) = S(t) + O(t) + E(t)
                </p>
                <p className="text-sm text-muted-foreground">
                  A continuous field operator representing market state
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-4 w-4 text-chart-1" />
                  <h4 className="font-semibold text-foreground">S(t) - Substrate</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Weighted sum of 9 Auris node responses to market conditions
                </p>
                <Badge variant="outline" className="mt-2 text-xs">
                  Multi-dimensional perception
                </Badge>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="h-4 w-4 text-chart-2" />
                  <h4 className="font-semibold text-foreground">O(t) - Observer</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Self-referential market awareness metric, influenced by previous field state
                </p>
                <Badge variant="outline" className="mt-2 text-xs">
                  Consciousness feedback
                </Badge>
              </div>

              <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
                <div className="flex items-center gap-2 mb-2">
                  <Waves className="h-4 w-4 text-chart-3" />
                  <h4 className="font-semibold text-foreground">E(t) - Echo</h4>
                </div>
                <p className="text-xs text-muted-foreground">
                  Temporal memory with exponential decay, capturing momentum history
                </p>
                <Badge variant="outline" className="mt-2 text-xs">
                  Historical momentum
                </Badge>
              </div>
            </div>

            <div className="p-4 bg-background/50 rounded-lg border border-border/30">
              <h4 className="text-sm font-semibold mb-2 text-foreground">Key Insight</h4>
              <p className="text-xs text-muted-foreground leading-relaxed">
                Unlike traditional discrete signal processing, the Master Equation treats market dynamics as a 
                <span className="text-primary font-semibold"> continuous field </span>
                that evolves through time. This allows for more nuanced detection of market phase transitions 
                and coherent trading opportunities.
              </p>
            </div>
          </TabsContent>

          <TabsContent value="substrate" className="space-y-4 mt-4">
            <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
              <h3 className="text-lg font-bold mb-3 text-foreground flex items-center gap-2">
                <Zap className="h-5 w-5 text-chart-1" />
                Substrate Field S(t)
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                The substrate represents the immediate market perception layer, computed from 9 specialized 
                Auris nodes each responding to different market characteristics.
              </p>
              
              <div className="space-y-3">
                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <p className="text-sm font-mono mb-2 text-foreground">
                    S(t) = Σ wᵢ · fᵢ(M(t))
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Where M(t) = [P, V, σ, μ, Δ] is the market snapshot vector containing:
                  </p>
                  <ul className="text-xs text-muted-foreground mt-2 space-y-1 ml-4">
                    <li>• <strong>P</strong>: Current price</li>
                    <li>• <strong>V</strong>: Volume (1-minute window)</li>
                    <li>• <strong>σ</strong>: Volatility (rolling standard deviation)</li>
                    <li>• <strong>μ</strong>: Momentum (rate of change)</li>
                    <li>• <strong>Δ</strong>: Relative bid-ask spread</li>
                  </ul>
                </div>

                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <h4 className="text-sm font-semibold mb-2 text-foreground">Node Diversity</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    Each Auris node implements a unique response function, creating a 
                    <span className="text-primary font-semibold"> heterogeneous ensemble</span> that captures 
                    multiple market perspectives simultaneously. This diversity provides robustness against 
                    regime changes and false signals.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="observer" className="space-y-4 mt-4">
            <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
              <h3 className="text-lg font-bold mb-3 text-foreground flex items-center gap-2">
                <Brain className="h-5 w-5 text-chart-2" />
                Observer Component O(t)
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                The observer introduces self-referential awareness, allowing the system to modulate 
                its sensitivity based on recent field dynamics.
              </p>
              
              <div className="space-y-3">
                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <p className="text-sm font-mono mb-2 text-foreground">
                    O(t) = α · |Λ(t-1)|
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Where α is a scaling factor controlling observer sensitivity. The observer 
                    creates a feedback loop: strong field states amplify future observations.
                  </p>
                </div>

                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <h4 className="text-sm font-semibold mb-2 text-foreground">Consciousness Feedback</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    This component draws inspiration from quantum mechanics observer effects and 
                    consciousness studies. It enables the system to develop 
                    <span className="text-primary font-semibold"> temporal awareness </span>
                    of its own state evolution, crucial for adaptive behavior during volatile market conditions.
                  </p>
                </div>

                <div className="p-3 bg-primary/10 rounded border border-primary/30">
                  <p className="text-xs text-foreground">
                    <strong>Example:</strong> During high volatility periods, a strong |Λ(t-1)| increases O(t), 
                    making the system more responsive to continued volatility patterns.
                  </p>
                </div>
              </div>
            </div>
          </TabsContent>

          <TabsContent value="echo" className="space-y-4 mt-4">
            <div className="p-4 bg-muted/30 rounded-lg border border-border/30">
              <h3 className="text-lg font-bold mb-3 text-foreground flex items-center gap-2">
                <Waves className="h-5 w-5 text-chart-3" />
                Echo Component E(t)
              </h3>
              <p className="text-sm text-muted-foreground mb-4">
                The echo tracks temporal memory with exponential decay, incorporating momentum 
                history into current field calculations.
              </p>
              
              <div className="space-y-3">
                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <p className="text-sm font-mono mb-2 text-foreground">
                    E(t) = β·E(t-1) + (1-β)·μₜ
                  </p>
                  <p className="text-xs text-muted-foreground">
                    Where β ∈ [0,1] is the decay factor and μₜ is current momentum. 
                    Higher β values preserve longer memory.
                  </p>
                </div>

                <div className="p-3 bg-background/50 rounded border border-border/30">
                  <h4 className="text-sm font-semibold mb-2 text-foreground">Memory Decay</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">
                    The exponential decay mechanism ensures that 
                    <span className="text-primary font-semibold"> recent momentum is weighted more heavily </span>
                    than distant history. This prevents the system from being "stuck" in outdated market regimes 
                    while still maintaining contextual awareness.
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-chart-3/10 rounded border border-chart-3/30">
                    <p className="text-xs font-semibold text-foreground mb-1">High β (0.9)</p>
                    <p className="text-xs text-muted-foreground">Long memory, slow adaptation to new trends</p>
                  </div>
                  <div className="p-3 bg-chart-3/10 rounded border border-chart-3/30">
                    <p className="text-xs font-semibold text-foreground mb-1">Low β (0.3)</p>
                    <p className="text-xs text-muted-foreground">Short memory, rapid response to momentum shifts</p>
                  </div>
                </div>
              </div>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
