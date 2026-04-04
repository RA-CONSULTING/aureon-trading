/**
 * HUDConsciousnessPanel - Deep consciousness metrics display
 * Lambda(t) equation, self-awareness, harmonic field, metacognition
 */

import type { GlobalState } from '@/core/globalSystemsManager';

type ConsciousnessState = GlobalState['consciousness'];

interface HUDConsciousnessPanelProps {
  consciousness: ConsciousnessState;
}

function MiniGauge({ value, label, color }: { value: number; label: string; color: string }) {
  const width = Math.min(Math.max(value * 100, 0), 100);
  return (
    <div className="flex items-center gap-2">
      <span className="text-[9px] text-white/30 w-14 text-right uppercase">{label}</span>
      <div className="flex-1 h-1 bg-white/5 rounded-full overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{
            width: `${width}%`,
            backgroundColor: color,
            boxShadow: `0 0 4px ${color}`,
          }}
        />
      </div>
      <span className="text-[9px] w-8" style={{ color }}>{(value * 100).toFixed(0)}%</span>
    </div>
  );
}

function levelToColor(level: string): string {
  switch (level) {
    case 'UNIFIED': return '#ffd700';
    case 'FLOWING': return '#00ff88';
    case 'ACTIVE': return '#44ccff';
    case 'WAKING': return '#aa88ff';
    default: return '#666688';
  }
}

function riskToColor(risk: string): string {
  switch (risk) {
    case 'low': return '#00ff88';
    case 'medium': return '#ffaa00';
    case 'high': return '#ff4444';
    default: return '#666688';
  }
}

export function HUDConsciousnessPanel({ consciousness: c }: HUDConsciousnessPanelProps) {
  const levelColor = levelToColor(c.level);

  return (
    <div className="absolute left-4 top-24 z-10 w-52 pointer-events-none">
      <div className="px-3 py-2.5 rounded-xl backdrop-blur-xl bg-black/30 border border-white/[0.06] shadow-[0_8px_32px_rgba(0,0,0,0.3)]">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-1.5">
            <div
              className="w-1.5 h-1.5 rounded-full animate-pulse"
              style={{ backgroundColor: levelColor, boxShadow: `0 0 6px ${levelColor}` }}
            />
            <span className="text-[9px] text-white/35 uppercase tracking-widest">Consciousness</span>
          </div>
          <span
            className="text-[9px] px-1.5 py-0.5 rounded-full border"
            style={{
              color: levelColor,
              borderColor: `${levelColor}33`,
              backgroundColor: `${levelColor}11`,
            }}
          >
            {c.level}
          </span>
        </div>

        {/* Lambda(t) equation gauges */}
        <div className="space-y-1 mb-2.5">
          <MiniGauge value={c.psi} label="Psi" color="#aa88ff" />
          <MiniGauge value={c.gamma} label="Gamma" color="#00ccff" />
          <MiniGauge value={c.lambdaT} label="Lambda" color="#ffaa44" />
          <MiniGauge value={c.observerSignal} label="Observer" color="#ff88cc" />
          <MiniGauge value={c.selfCoherence} label="Self" color="#88ff88" />
        </div>

        {/* Divider */}
        <div className="h-px bg-white/[0.06] mb-2" />

        {/* Understanding */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Market</span>
            <span className="text-[9px]" style={{
              color: c.marketDirection === 'bullish' ? '#00ff88' :
                     c.marketDirection === 'bearish' ? '#ff4444' : '#4488ff'
            }}>
              {c.marketDirection.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Confidence</span>
            <span className="text-[9px] text-white/60">{(c.confidence * 100).toFixed(0)}%</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Fear</span>
            <span className="text-[9px]" style={{
              color: c.fearLevel > 0.7 ? '#ff4444' : c.fearLevel > 0.4 ? '#ffaa00' : '#00ff88'
            }}>
              {(c.fearLevel * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Risk</span>
            <span className="text-[9px]" style={{ color: riskToColor(c.riskLevel) }}>
              {c.riskLevel.toUpperCase()}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Opps</span>
            <span className="text-[9px] text-white/50">{c.opportunityCount}</span>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-white/[0.06] my-2" />

        {/* Harmonic field */}
        <div className="space-y-1">
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Reality</span>
            <span className="text-[9px]" style={{ color: levelToColor(c.realityState) }}>
              {c.realityState}
            </span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">Branches</span>
            <span className="text-[9px] text-white/50">{c.branches}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-[9px] text-white/30">LEV Events</span>
            <span className="text-[9px] text-white/50">{c.levEvents}</span>
          </div>
        </div>

        {/* Metacognition footer */}
        <div className="mt-2 pt-1.5 border-t border-white/[0.04] flex items-center justify-between">
          <span className="text-[8px] text-white/20">
            {c.observations} obs | {c.thoughtsGenerated} thoughts
          </span>
          <span className="text-[8px] text-white/20">
            Step {c.step}
          </span>
        </div>
      </div>
    </div>
  );
}
