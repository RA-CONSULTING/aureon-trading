import Navbar from "@/components/Navbar";
import { PrismRevealVisualizer } from "@/components/PrismRevealVisualizer";
import { CymaticsFieldVisualizer } from "@/components/CymaticsFieldVisualizer";
import { PrismStatus } from "@/components/warroom/PrismStatus";
import { HarmonicDataIntegrityPanel } from "@/components/HarmonicDataIntegrityPanel";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useAureonSession } from "@/hooks/useAureonSession";
import { useEffect, useState } from "react";
import { supabase } from "@/integrations/supabase/client";

const Prism = () => {
  const [userId, setUserId] = useState<string | null>(null);
  
  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (session) setUserId(session.user.id);
    });
  }, []);

  const { quantumState, marketData } = useAureonSession(userId);

  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">💎</span>
            <h1 className="text-3xl font-bold text-foreground">The Prism - 528 Hz Transformation</h1>
          </div>
          
          {/* Prism Status Card */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <PrismStatus 
              lambda={quantumState.lambda}
              coherence={quantumState.coherence}
              substrate={quantumState.substrate}
              observer={quantumState.observer}
              echo={quantumState.echo}
              volatility={marketData.volatility}
              momentum={marketData.momentum}
              baseFrequency={396}
            />
            <HarmonicDataIntegrityPanel />
          </div>
          
          {/* 5-Level Frequency Transformation */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">5-Level Frequency Transformation</CardTitle>
            </CardHeader>
            <CardContent>
              <PrismRevealVisualizer />
            </CardContent>
          </Card>
          
          {/* Cymatics Field */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Cymatics Field Visualization</CardTitle>
            </CardHeader>
            <CardContent>
              <CymaticsFieldVisualizer />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Prism;
