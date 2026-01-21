// Schumann Lattice SVG Renderer
import React from 'react';
import { Blob, idFromNoteIndex } from './SchumannLatticePatch';

interface Props {
  blobs: Blob[];
  cellSize?: number;
  radius?: number;
  width?: number;
  height?: number;
  showGrid?: boolean;
  showLabels?: boolean;
}

export default function SchumannLatticeRenderer({ 
  blobs, 
  cellSize = 60, 
  radius = 12, 
  width = 800, 
  height = 600,
  showGrid = true,
  showLabels = true 
}: Props) {
  const xs = blobs.map(b => b.x);
  const ys = blobs.map(b => b.y);
  const pad = 3;
  const xmin = Math.min(-pad, ...xs) - pad;
  const xmax = Math.max(pad, ...xs) + pad;
  const ymin = Math.min(-pad, ...ys) - pad;
  const ymax = Math.max(pad, ...ys) + pad;

  const svgWidth = Math.max(width, (xmax - xmin + 1) * cellSize);
  const svgHeight = Math.max(height, (ymax - ymin + 1) * cellSize);

  function toXY(x: number, y: number) {
    const px = (x - xmin) * cellSize + (y - ymin) * cellSize * 0.5;
    const py = (y - ymin) * cellSize * 0.866;
    return { px, py };
  }

  const grid: JSX.Element[] = [];
  if (showGrid) {
    for (let x = xmin; x <= xmax; x++) {
      for (let y = ymin; y <= ymax; y++) {
        const { px, py } = toXY(x, y);
        grid.push(
          <circle key={`g-${x}-${y}`} cx={px} cy={py} r={2} fill="rgba(255,255,255,0.08)" />
        );
      }
    }
  }

  const activeBlobs = blobs.map((blob, i) => {
    const { px, py } = toXY(blob.x, blob.y);
    const note = idFromNoteIndex(blob.noteIndex);
    const hue = (blob.noteIndex * 30) % 360;
    const color = `hsl(${hue}, 70%, 60%)`;
    const r = radius * (0.5 + 0.5 * blob.weight);
    const alpha = 0.25 + 0.65 * blob.weight;

    return (
      <g key={`blob-${i}`}>
        <circle cx={px} cy={py} r={r * 1.8} fill={color} opacity={0.15} />
        <circle cx={px} cy={py} r={r} fill={color} opacity={alpha} />
        {showLabels && (
          <text x={px + 8} y={py - 8} fontSize="12" fill="rgba(255,255,255,0.8)">
            {note}
          </text>
        )}
      </g>
    );
  });

  return (
    <svg 
      width="100%" 
      height={svgHeight} 
      viewBox={`0 0 ${svgWidth} ${svgHeight}`} 
      className="rounded-2xl bg-zinc-900/40"
    >
      {grid}
      {activeBlobs}
      <text x={12} y={20} fontSize="14" fill="rgba(255,255,255,0.6)">
        Tonnetz: x=5ths, y=Maj3rds
      </text>
    </svg>
  );
}