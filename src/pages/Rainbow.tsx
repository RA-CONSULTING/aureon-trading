import Navbar from "@/components/Navbar";
import HarmonicNexusAnalytics from "@/components/HarmonicNexusAnalytics";
import { HarmonicFieldVisualizer } from "@/components/HarmonicFieldVisualizer";
import ProjectRainbow from "@/components/ProjectRainbow";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Rainbow = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🌈</span>
            <h1 className="text-3xl font-bold text-foreground">Rainbow Bridge & Harmonic Nexus</h1>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Harmonic Nexus Analytics</CardTitle>
              </CardHeader>
              <CardContent>
                <HarmonicNexusAnalytics />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Harmonic Field State</CardTitle>
              </CardHeader>
              <CardContent>
                <HarmonicFieldVisualizer />
              </CardContent>
            </Card>
          </div>
          
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Project Rainbow</CardTitle>
            </CardHeader>
            <CardContent>
              <ProjectRainbow />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Rainbow;
