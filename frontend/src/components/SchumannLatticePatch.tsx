// Schumann Lattice Integration Patch (React + TypeScript)
// ------------------------------------------------------
// Drop this file into your codebase (e.g., src/modules/SchumannLatticePatch.tsx)
// and import <SchumannLattice /> where you want the lattice to render.
//
// What this provides:
// 1) Robust pitch mapping for arbitrary Hz (C=256Hz reference by default)
// 2) Tonnetz lattice placement (x = 5ths, y = Maj3rds) with soft Gaussian blobs
// 3) TSV fusion: modulates lattice intensity by Tensor Scalar Value (coherence)
// 4) Optional intent integration hook (SymbolicCompiler-like interface)
// 5) A self-contained React component that draws the lattice as SVG
//
// ------------------------------------------------------

import React, { useEffect, useMemo, useState } from "react";

// -----------------------------
// Types
// -----------------------------
export type NoteID =
  | "C" | "Cs" | "D" | "Ds" | "E" | "F"
  | "Fs" | "G" | "Gs" | "A" | "As" | "B";

export interface LatticePoint {
  noteIndex: number; // 0..11 (C..B)
  x: number;         // steps of perfect fifth (+7)
  y: number;         // steps of major third (+4)
}

export interface Blob extends LatticePoint {
  weight: number;    // 0..1
}

// Optional run‑time data from your Nexus Unity Tensor Field
export interface TensorDatum {
  phi: number;     // phase
  kappa: number;   // curvature/anchor
  psi: number;     // local weight
  TSV: number;     // coherence value (can be negative or positive)
}

// Minimal interface for your SymbolicCompiler (see symbolic_compiler_layer.json)
export interface IntentCompiler {
  process_intent: (text: string) =>
    | { frequencies: number[]; decay?: number }
    | Promise<{ frequencies: number[]; decay?: number }>;
}

// -----------------------------
// Constants & Utilities
// -----------------------------
const NOTE_IDS: NoteID[] = [
  "C","Cs","D","Ds","E","F","Fs","G","Gs","A","As","B"
];
export const idFromNoteIndex = (i: number): NoteID => NOTE_IDS[(i % 12 + 12) % 12];

export const clamp = (x: number, lo = 0, hi = 1) => Math.min(hi, Math.max(lo, x));
export const sigmoid = (x: number) => 1 / (1 + Math.exp(-x));

// Reference pitch: C = 256Hz (keeps Earth fundamental near B region when transposed)
const C_REF = 256; // Hz

// -----------------------------
// Pitch <-> Lattice (Tonnetz) mapping
// -----------------------------
export function pitchClassToLattice(n: number): LatticePoint {
  // Find small integers (a,b) such that (7a + 4b) ≡ n (mod 12)
  let best = { a: 0, b: 0, cost: 1e9 };
  const n12 = ((n % 12) + 12) % 12;
  for (let a = -6; a <= 6; a++) {
    for (let b = -6; b <= 6; b++) {
      if ((((7 * a + 4 * b) % 12) + 12) % 12 === n12) {
        const cost = Math.abs(a) + Math.abs(b) + 0.001 * Math.abs(a * b);
        if (cost < best.cost) best = { a, b, cost } as any;
      }
    }
  }
  return { noteIndex: n12, x: best.a, y: best.b };
}