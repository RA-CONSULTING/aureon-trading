import React, { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { earthStreamsMonitor, type SimpleEarthStreams } from '@/lib/earth-streams';
import { earthAureonBridge, type EarthFieldInfluence } from '@/core/earthAureonBridge';
import { SCHUMANN_FREQUENCIES } from '@/lib/schumann-emotional-mapping';

export const EarthFieldMonitor: React.FC = () => {
  const [earthStreams, setEarthStreams] = useState<SimpleEarthStreams | null>(null);
  const [influence, setInfluence] = useState<EarthFieldInfluence | null>(null);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // Initialize earth streams monitor
    if (!earthStreamsMonitor.isMonitoringActive()) {
      earthStreamsMonitor.initialize();
    }

    const interval = setInterval(async () => {
      const streams = earthStreamsMonitor.getEarthStreamMetrics();
      if (streams) {
        const simpleStreams: SimpleEarthStreams = {
          solarWindVelocity: streams.solarWind.velocity,
          geomagneticKp: streams.geomagnetic.kpIndex,
          ionosphericDensity: streams.atmospheric.ionosphericDensity / 1e10,
          fieldCoupling: streams.fieldCoupling
        };
        
        setEarthStreams(simpleStreams);
        
        // Get influence
        const earthInfluence = await earthAureonBridge.getEarthInfluence(simpleStreams);
        setInfluence(earthInfluence);
        setIsActive(true);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  if (!earthStreams || !influence) {
    return (
      <Card className="p-4 bg-gradient-to-br from-blue-950/30 to-purple-950/30 border-blue-500/30">
        <div className="text-blue-300 animate-pulse">
          🌍 Initializing Earth Field Monitor...
        </div>
      </Card>
    );
  }

  const getKpColor = (kp: number) => {
    if (kp < 3) return 'text-green-400';
    if (kp < 5) return 'text-yellow-400';
    return 'text-red-400';
  };

  const getCoherenceColor = (coherence: number) => {
    if (coherence > 0.7) return 'text-emerald-400';
    if (coherence > 0.4) return 'text-blue-400';
    return 'text-orange-400';
  };

  const getBoostColor = (boost: number) => {
    if (boost > 0.1) return 'text-green-400';
    if (boost > 0) return 'text-blue-400';
    if (boost > -0.05) return 'text-yellow-400';
    return 'text-red-400';
  };

  return (
    <Card className="p-4 bg-gradient-to-br from-blue-950/30 to-purple-950/30 border-blue-500/30 space-y-3">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-lg font-bold text-blue-300 flex items-center gap-2">
          🌍 Earth Field Monitor
          {isActive && (
            <span className="inline-block w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          )}
        </h3>
        <div className="text-xs text-blue-400">
          {influence.dominantFrequency.toFixed(2)} Hz
        </div>
      </div>

      {/* Schumann Resonance */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-sm text-blue-200">Schumann Coherence</span>
          <span className={`text-sm font-mono ${getCoherenceColor(influence.schumannCoherence)}`}>
            {(influence.schumannCoherence * 100).toFixed(1)}%
          </span>
        </div>
        <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
            style={{ width: `${influence.schumannCoherence * 100}%` }}
          />
        </div>
      </div>

      {/* Solar Wind */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-sm text-blue-200">Solar Wind</span>
          <span className="text-sm font-mono text-cyan-400">
            {earthStreams.solarWindVelocity.toFixed(0)} km/s
          </span>
        </div>
        <div className="flex gap-1">
          {influence.solarWindModifier > 0 ? (
            <span className="text-xs text-green-400">↑ Amplifying</span>
          ) : influence.solarWindModifier < -0.05 ? (
            <span className="text-xs text-red-400">↓ Disrupting</span>
          ) : (
            <span className="text-xs text-blue-400">→ Neutral</span>
          )}
        </div>
      </div>

      {/* Geomagnetic Field */}
      <div className="space-y-1">
        <div className="flex justify-between items-center">
          <span className="text-sm text-blue-200">Geomagnetic Kp</span>
          <span className={`text-sm font-mono ${getKpColor(earthStreams.geomagneticKp)}`}>
            {earthStreams.geomagneticKp.toFixed(1)}
          </span>
        </div>
        <div className="text-xs text-slate-400">
          {earthStreams.geomagneticKp < 3 ? 'Quiet' : earthStreams.geomagneticKp < 5 ? 'Unsettled' : 'Storm'}
        </div>
      </div>

      {/* Emotional Resonance */}
      {influence.emotionalState && (
        <div className="space-y-1 pt-2 border-t border-blue-500/20">
          <div className="flex justify-between items-center">
            <span className="text-sm text-blue-200">Emotional Field</span>
            <span className="text-sm font-mono text-purple-400">
              {(influence.emotionalResonance * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex flex-wrap gap-1">
            {influence.emotionalState.emotionalTags.slice(0, 3).map((tag, i) => (
              <span
                key={i}
                className="text-xs px-2 py-0.5 rounded-full bg-purple-500/20 text-purple-300"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Combined Boost */}
      <div className="pt-2 border-t border-blue-500/20">
        <div className="flex justify-between items-center">
          <span className="text-sm font-semibold text-blue-200">Trading Signal Boost</span>
          <span className={`text-lg font-bold ${getBoostColor(influence.combinedBoost)}`}>
            {influence.combinedBoost > 0 ? '+' : ''}
            {(influence.combinedBoost * 100).toFixed(1)}%
          </span>
        </div>
        <div className="mt-1 text-xs text-slate-400">
          {influence.combinedBoost > 0.1
            ? '🟢 Strong positive field alignment'
            : influence.combinedBoost > 0
            ? '🔵 Moderate field support'
            : influence.combinedBoost > -0.05
            ? '🟡 Neutral conditions'
            : '🔴 Field disruption active'}
        </div>
      </div>

      {/* Frequency Reference */}
      <div className="pt-2 border-t border-blue-500/20 text-xs text-slate-400 space-y-1">
        <div className="font-semibold text-blue-300">Schumann Harmonics:</div>
        <div className="grid grid-cols-2 gap-1">
          <div>7.83 Hz • Fundamental</div>
          <div>14.3 Hz • 2nd</div>
          <div>20.8 Hz • 3rd</div>
          <div>27.3 Hz • 4th</div>
        </div>
      </div>
    </Card>
  );
};
