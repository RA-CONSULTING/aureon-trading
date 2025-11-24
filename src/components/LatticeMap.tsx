import React from 'react';
import { idFromNoteIndex, LatticePoint } from '@/lib/tonnetz';

type Blob = LatticePoint & { weight: number };

interface Props {
  blobs: Blob[];              // active lattice blobs
  cellSize?: number;          // px
  radius?: number;            // dot radius
  className?: string;
}

const NOTE_COLORS: Record<string, string> = {
  'C': '#ff6b6b', 'C#': '#ff8e53', 'D': '#ff9f43', 'D#': '#feca57',
  'E': '#48dbfb', 'F': '#0abde3', 'F#': '#006ba6', 'G': '#5f27cd',
  'G#': '#a55eea', 'A': '#fd79a8', 'A#': '#fdcb6e', 'B': '#6c5ce7'
};

export default function LatticeMap({ blobs, cellSize=60, radius=12, className='' }: Props) {
  // compute extents
  const xs = blobs.map(b=>b.x), ys = blobs.map(b=>b.y);
  const pad = 3;
  const xmin = Math.min(-pad, ...xs)-pad, xmax = Math.max(pad, ...xs)+pad;
  const ymin = Math.min(-pad, ...ys)-pad, ymax = Math.max(pad, ...ys)+pad;

  const width = (xmax - xmin + 1) * cellSize;
  const height = (ymax - ymin + 1) * cellSize;

  function toXY(x:number,y:number) {
    // skew for a hex-like layout
    const px = (x - xmin) * cellSize + (y - ymin) * cellSize * 0.5;
    const py = (y - ymin) * cellSize * 0.866; // ≈ sqrt(3)/2
    return {px, py};
  }

  // background grid
  const grid: JSX.Element[] = [];
  for (let x = xmin; x <= xmax; x++) {
    for (let y = ymin; y <= ymax; y++) {
      const {px,py} = toXY(x,y);
      grid.push(
        <circle key={`g-${x}-${y}`} cx={px} cy={py} r={2} fill="rgba(255,255,255,0.08)"/>
      );
    }
  }

  // active blobs
  const active = blobs.map((b,i) => {
    const {px,py} = toXY(b.x,b.y);
    const note = idFromNoteIndex(b.noteIndex);
    const color = NOTE_COLORS[note] || "#ffffff";
    const r = radius * (0.5 + 0.5*b.weight); // weight→size
    const alpha = 0.25 + 0.65*b.weight;
    return (
      <g key={`b-${i}`}>
        <circle cx={px} cy={py} r={r*1.8} fill={color} opacity={0.15}/>
        <circle cx={px} cy={py} r={r} fill={color} opacity={alpha}/>
        <text x={px+8} y={py-8} fontSize="12" fill="rgba(255,255,255,0.8)">{note}</text>
      </g>
    );
  });

  return (
    <div className={`rounded-2xl bg-zinc-900/40 p-4 ${className}`}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        {grid}
        {active}
        <text x={12} y={20} fontSize="14" fill="rgba(255,255,255,0.6)">
          Tonnetz: x=5ths, y=Maj3rds
        </text>
      </svg>
    </div>
  );
}