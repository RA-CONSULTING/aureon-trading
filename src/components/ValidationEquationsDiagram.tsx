import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

export default function ValidationEquationsDiagram() {
  return (
    <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/50 to-purple-50/30">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-indigo-800 flex items-center gap-2">
          <span className="text-2xl">🔬</span>
          Nexus Source Law 10-9-1 — Validation Equations
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Flow Diagram */}
        <div className="bg-white/70 rounded-xl p-4 border border-indigo-100">
          <div className="font-mono text-sm text-indigo-700 leading-relaxed whitespace-pre">
{`┌───────────────────────────┐
│ Outcomes (10)             │
│ Angel × Tarot × Aura × Nx │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Harmonic Filter (9 axes)  │
│   Fᵢ = Σ wⱼ · xᵢⱼ         │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ ZPE Collapse (Observer)   │
│   Zᵢ = Fᵢ · (1+λ·χᵢ)       │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Normalize Probabilities   │
│   pᵢ = Zᵢ / Σ Zⱼ           │
└─────────────┬─────────────┘
              │
              ▼
┌───────────────────────────┐
│ Prime Timeline (1)        │
│   C* = argmax pᵢ           │
└───────────────────────────┘`}
          </div>
        </div>

        {/* Mathematical Formulas */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white/70 rounded-lg p-3 border border-indigo-100">
            <h4 className="font-semibold text-indigo-800 mb-2">Harmonic Filter (9 Axes)</h4>
            <div className="font-mono text-xs text-indigo-700 space-y-1">
              <div>Fᵢ = αAᵢ + βTᵢ + γHᵢ + δRᵢ + ϵEᵢ + ζSᵢ + ηPᵢ + θJᵢ + κQᵢ</div>
              <div className="text-[10px] text-indigo-600 mt-2">
                A: alignment, T: timing, H: coherence<br/>
                R: risk, E: effort, S: support<br/>
                P: peace, J: joy, Q: clarity
              </div>
            </div>
          </div>
          
          <div className="bg-white/70 rounded-lg p-3 border border-indigo-100">
            <h4 className="font-semibold text-indigo-800 mb-2">Observer Intent Boost</h4>
            <div className="font-mono text-xs text-indigo-700 space-y-1">
              <div>Zᵢ = Fᵢ · (1 + λ · χᵢ)</div>
              <div className="text-[10px] text-indigo-600 mt-2">
                λ: boost factor (≈0.1)<br/>
                χᵢ: intent resonance (0 or 1)<br/>
                Zero-Point Energy collapse
              </div>
            </div>
          </div>
        </div>

        {/* Constraint & Summary */}
        <div className="bg-gradient-to-r from-emerald-50 to-blue-50 rounded-lg p-3 border border-emerald-200">
          <h4 className="font-semibold text-emerald-800 mb-2">Peace & Joy Constraint</h4>
          <div className="font-mono text-xs text-emerald-700 mb-2">
              ∀i : pᵢ &gt; 0 ⇒ Cᵢ affirms Peace ∨ Joy
          </div>
          <div className="text-xs text-emerald-600">
            All surviving candidates must affirm Peace or Joy. If none survive, fallback: "Restore Harmony & Invite Joy"
          </div>
        </div>

        {/* Summary */}
        <div className="bg-white/70 rounded-lg p-3 border border-indigo-100">
          <div className="font-mono text-sm text-indigo-800 text-center">
            <strong>10</strong> enumeration → <strong>9</strong> harmonic axes → <strong>1</strong> Prime Directive
          </div>
        </div>
      </CardContent>
    </Card>
  );
}