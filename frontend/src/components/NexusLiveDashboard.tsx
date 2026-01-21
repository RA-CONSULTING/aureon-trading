import React, { useEffect, useMemo, useRef, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

// ---------- helpers ----------
function fmt(x: unknown, d = 2, empty = "—") {
  const n = typeof x === "string" ? Number(x) : (x as number);
  return Number.isFinite(n) ? n.toFixed(d) : empty;
}
function clamp01(x: number) { return Math.max(0, Math.min(1, x)); }
function hsl(h:number, s:number, l:number){ return `hsl(${h} ${s}% ${l}%)`; }

// ---------- types ----------
export type AurisMetrics = {
  ts?: string;
  coherence_score?: number;
  schumann_lock?: number;
  tsv_gain?: number;
  prime_alignment?: number;
  ten_nine_one_concordance?: number;
};

export type AuraMetrics = {
  ts?: string;
  alpha_theta_ratio?: number;
  alpha_theta_norm?: number;
  hrv_norm?: number;
  gsr_norm?: number;
  prime_concordance_10_9_1?: number;
  calm_index?: number;
  aura_hue_deg?: number;
}

// ---------- AuraRing ----------
function AuraRing({m}:{m: AuraMetrics}){
  const hue = Number.isFinite(m?.aura_hue_deg as number) ? (m.aura_hue_deg as number) : 160;
  const glow = 10 + 50*clamp01(m?.calm_index ?? 0);
  const sat  = 40 + 40*clamp01(m?.prime_concordance_10_9_1 ?? 0);
  const light= 45 + 10*clamp01(m?.hrv_norm ?? 0);
  const ring = useMemo(()=>({
    stroke: hsl(hue, sat, light),
    fill:   hsl(hue, Math.min(90, sat+10), Math.min(80, light+10))
  }), [hue, sat, light]);
  
  return (
    <div className="relative grid place-items-center">
      <svg width="240" height="240" viewBox="0 0 240 240">
        <defs>
          <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation={glow}/>
          </filter>
        </defs>
        <circle cx="120" cy="120" r="86" stroke={ring.stroke} strokeWidth="12" fill="none" filter="url(#glow)"/>
        <circle cx="120" cy="120" r="78" fill={ring.fill} opacity="0.25"/>
      </svg>
      <div className="absolute bottom-3 text-xs text-zinc-200 bg-zinc-900/70 px-2 py-1 rounded-xl">
        calm {fmt(m?.calm_index,2)} · 10:9:1 {fmt(m?.prime_concordance_10_9_1,2)}
      </div>
    </div>
  );
}

// ---------- Lattice Metrics ----------
function LatticeMetrics({m}:{m: AurisMetrics}){
  const metrics = [
    { label: "Coherence", value: m?.coherence_score, color: "emerald", unit: "" },
    { label: "Schumann Lock", value: m?.schumann_lock, color: "blue", unit: "%" },
    { label: "TSV Gain", value: m?.tsv_gain, color: "purple", unit: "dB" },
    { label: "Prime Alignment", value: m?.prime_alignment, color: "orange", unit: "" },
  ];
  
  return (
    <div className="grid grid-cols-2 gap-4">
      {metrics.map(({label, value, color, unit}) => (
        <Card key={label} className={`bg-gradient-to-br from-${color}-900 to-${color}-800 text-white`}>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">{fmt(value)}{unit}</div>
            <div className="text-sm text-${color}-200">{label}</div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// Main component combining aura and lattice displays
export function NexusLiveDashboard({ aurisMetrics, auraMetrics }: { 
  aurisMetrics: AurisMetrics; 
  auraMetrics: AuraMetrics; 
}) {
  return (
    <div className="flex flex-col items-center space-y-6">
      <AuraRing m={auraMetrics} />
      <div className="w-full max-w-md">
        <LatticeMetrics m={aurisMetrics} />
      </div>
    </div>
  );
}

// Export individual components
export { AuraRing, LatticeMetrics };