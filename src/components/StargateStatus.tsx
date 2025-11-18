import { useEffect, useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MapPin, Waves, Zap } from 'lucide-react';
import { stargateLayer } from '@/core/stargateLattice';
import type { StargateInfluence } from '@/core/stargateLattice';
import { useSentinelConfig } from '@/hooks/useSentinelConfig';

type StargateStatusProps = {
  onLocationUpdate?: (location: { lat: number; lng: number } | null) => void;
  celestialBoost?: number;
};

export const StargateStatus = ({ onLocationUpdate, celestialBoost = 0 }: StargateStatusProps) => {
  const { config } = useSentinelConfig();
  const [influence, setInfluence] = useState<StargateInfluence | null>(null);
  const [gridEnergy, setGridEnergy] = useState(0);
  const [isLocating, setIsLocating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoInitialized, setAutoInitialized] = useState(false);

  const requestLocation = () => {
    setIsLocating(true);
    setError(null);

    if (!navigator.geolocation) {
      setError('Geolocation not supported');
      setIsLocating(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        const inf = stargateLayer.getInfluence(latitude, longitude, celestialBoost);
        setInfluence(inf);
        setIsLocating(false);
        
        // Notify parent component
        if (onLocationUpdate) {
          onLocationUpdate({ lat: latitude, lng: longitude });
        }
      },
      (err) => {
        setError('Location access denied');
        setIsLocating(false);
        console.error('Geolocation error:', err);
      }
    );
  };

  // Auto-initialize with sentinel location
  useEffect(() => {
    if (config && config.auto_initialize && !autoInitialized) {
      const inf = stargateLayer.getInfluence(
        config.stargate_latitude,
        config.stargate_longitude,
        celestialBoost
      );
      setInfluence(inf);
      setAutoInitialized(true);
      
      if (onLocationUpdate) {
        onLocationUpdate({
          lat: config.stargate_latitude,
          lng: config.stargate_longitude
        });
      }
    }
  }, [config, celestialBoost, autoInitialized, onLocationUpdate]);

  useEffect(() => {
    setGridEnergy(stargateLayer.calculateGridEnergy());
    
    const interval = setInterval(() => {
      setGridEnergy(stargateLayer.calculateGridEnergy());
    }, 60000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="bg-card shadow-card">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span className="text-xl">🌍</span>
          Stargate Field Status
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {config && (
          <div className="mb-4 p-3 rounded-lg border border-primary/20 bg-primary/5">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-xl">⚡</span>
              <span className="font-bold text-sm">Prime Sentinel Active</span>
            </div>
            <p className="text-xs text-muted-foreground mb-1">{config.sentinel_name}</p>
            <p className="text-xs text-muted-foreground">{config.stargate_location}</p>
          </div>
        )}
        
        {!influence ? (
          <div className="text-center py-8">
            <MapPin className="h-12 w-12 mx-auto mb-4 text-muted-foreground opacity-50 animate-pulse" />
            <p className="text-sm text-muted-foreground mb-4">
              {config ? 'Auto-initializing Stargate at Belfast...' : 'Enable geolocation to activate Stargate Lattice influence'}
            </p>
            <Button
              onClick={requestLocation}
              disabled={isLocating}
              className="gap-2"
            >
              <MapPin className={`h-4 w-4 ${isLocating ? 'animate-pulse' : ''}`} />
              {isLocating ? 'Locating...' : 'Use Current Location'}
            </Button>
            {error && (
              <p className="text-xs text-destructive mt-2">{error}</p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 rounded-lg border border-border bg-muted/20">
                <div className="flex items-center gap-2 mb-2">
                  <MapPin className="h-4 w-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Nearest Node</span>
                </div>
                <p className="font-bold text-sm">{influence.nearestNode}</p>
                <p className="text-xs text-muted-foreground mt-1">
                  {influence.distance.toLocaleString()}km away
                </p>
              </div>

              <div className="p-4 rounded-lg border border-border bg-muted/20">
                <div className="flex items-center gap-2 mb-2">
                  <Waves className="h-4 w-4 text-primary" />
                  <span className="text-xs text-muted-foreground">Proximity</span>
                </div>
                <p className="font-bold text-sm">
                  {(influence.proximityFactor * 100).toFixed(1)}%
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  Field Strength
                </p>
              </div>
            </div>

            <div className="p-4 rounded-lg border border-primary/20 bg-primary/5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-primary" />
                  <span className="text-sm font-semibold">Coherence Boost</span>
                </div>
                <Badge variant={influence.coherenceModifier > 0.1 ? 'default' : 'secondary'}>
                  +{(influence.coherenceModifier * 100).toFixed(1)}%
                </Badge>
              </div>
              
              {influence.celestialBoost !== undefined && influence.celestialBoost > 0 && (
                <div className="mb-3 p-2 rounded bg-purple-500/10 border border-purple-500/20">
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-purple-400">✨ Celestial Amplification</span>
                    <span className="font-mono font-bold text-purple-400">
                      +{(influence.celestialBoost * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              )}
              
              {influence.frequencyBoost.length > 0 && (
                <div>
                  <p className="text-xs text-muted-foreground mb-2">
                    Active Frequencies:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {influence.frequencyBoost.map((freq, i) => (
                      <Badge key={i} variant="outline" className="text-xs">
                        {freq}Hz
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 rounded-lg border border-border bg-muted/20">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs text-muted-foreground">Planetary Grid Energy</span>
                <span className="text-sm font-mono font-bold">
                  {(gridEnergy * 100).toFixed(1)}%
                </span>
              </div>
              <div className="w-full h-2 bg-background rounded-full overflow-hidden">
                <div
                  className="h-full bg-gradient-to-r from-primary/50 to-primary transition-all duration-1000"
                  style={{ width: `${gridEnergy * 100}%` }}
                />
              </div>
            </div>

            <Button
              onClick={requestLocation}
              variant="outline"
              size="sm"
              className="w-full gap-2"
            >
              <MapPin className="h-4 w-4" />
              Update Location
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
