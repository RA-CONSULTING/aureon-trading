import Navbar from "@/components/Navbar";
import EarthLiveAnalytics from "@/components/EarthLiveAnalytics";
import { SchumannResonanceMonitor } from "@/components/SchumannResonanceMonitor";
import { SolarWeatherDashboard } from "@/components/SolarWeatherDashboard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useEarthLiveData } from "@/hooks/useEarthLiveData";
import { 
  SchumannSpectrogramPanel, 
  LatticeWaveformPanel, 
  ValidationMeterPanel,
  PrimeSealPanel,
  TimelineMarkersPanel 
} from "@/components/earth";
import { Globe, Radio, Loader2 } from "lucide-react";

const Earth = () => {
  const earthData = useEarthLiveData(true, 1000);
  
  return (
    <div className="min-h-screen bg-background">
      <Navbar />
      <main className="pt-20 px-4 pb-8">
        <div className="container mx-auto space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <Globe className="w-8 h-8 text-primary" />
              <div>
                <h1 className="text-3xl font-bold text-foreground">Earth Field Integration</h1>
                <p className="text-sm text-muted-foreground">
                  Live Schumann resonance, geomagnetic data & 10-9-1 Prime Seal
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {earthData.isLoading ? (
                <Badge variant="secondary" className="animate-pulse">
                  <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                  Loading...
                </Badge>
              ) : earthData.error ? (
                <Badge variant="destructive">Error: {earthData.error}</Badge>
              ) : (
                <Badge variant="default" className="bg-green-500">
                  <Radio className="w-3 h-3 mr-1" />
                  LIVE DATA
                </Badge>
              )}
            </div>
          </div>
          
          {/* Main grid - Earth Live Data panels */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Schumann Spectrogram - 5 modes from CSV */}
            <SchumannSpectrogramPanel 
              currentSchumann={earthData.currentSchumann}
              coherenceIndex={earthData.currentSchumann?.coherence_idx || 0}
            />
            
            {/* Lattice Waveform - Raw sensor data */}
            <LatticeWaveformPanel
              currentLattice={earthData.currentLattice}
              magneticField={earthData.magneticField}
              electricField={earthData.electricField}
            />
          </div>
          
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Validation Meter - Codex formulas */}
            <ValidationMeterPanel validation={earthData.validation} />
            
            {/* Prime Seal Status */}
            <PrimeSealPanel 
              primeSeal={earthData.primeSeal}
              currentMarker={earthData.currentMarker}
            />
            
            {/* Timeline Markers */}
            <TimelineMarkersPanel
              markers={earthData.timelineMarkers}
              currentMarker={earthData.currentMarker}
              timelineClip={earthData.timelineClip}
            />
          </div>
          
          {/* Original panels */}
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
