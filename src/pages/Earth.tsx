import Navbar from "@/components/Navbar";
import EarthLiveAnalytics from "@/components/EarthLiveAnalytics";
import { SchumannResonanceMonitor } from "@/components/SchumannResonanceMonitor";
import { SolarWeatherDashboard } from "@/components/SolarWeatherDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Earth = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          <div className="flex items-center gap-3 mb-6">
            <span className="text-3xl">🌍</span>
            <h1 className="text-3xl font-bold text-foreground">Earth Field Integration</h1>
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Schumann Resonance (7.83 Hz)</CardTitle>
              </CardHeader>
              <CardContent>
                <SchumannResonanceMonitor />
              </CardContent>
            </Card>
            
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="text-lg">Solar Weather</CardTitle>
              </CardHeader>
              <CardContent>
                <SolarWeatherDashboard />
              </CardContent>
            </Card>
          </div>
          
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="text-lg">Earth Live Analytics</CardTitle>
            </CardHeader>
            <CardContent>
              <EarthLiveAnalytics />
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
};

export default Earth;
