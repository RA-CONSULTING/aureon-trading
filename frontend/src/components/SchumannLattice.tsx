import React from 'react';
import { TensorDatum, IntentCompiler, pitchClassToLattice, clamp } from './SchumannLatticePatch';

interface SchumannLatticeProps {
  schumannHz?: number[];
  tensorField?: TensorDatum[];
  compiler?: IntentCompiler;
  intentText?: string;
  width?: number;
  height?: number;
}

export const SchumannLattice: React.FC<SchumannLatticeProps> = ({
  schumannHz = [7.83, 14.3, 20.8, 27.3, 33.8],
  tensorField = [],
  compiler,
  intentText = "",
  width = 600,
  height = 400
}) => {
  const scale = 40;
  const centerX = width / 2;
  const centerY = height / 2;

  // Convert Hz to pitch classes and lattice points
  const latticePoints = schumannHz.map(hz => {
    const pitchClass = Math.round(12 * Math.log2(hz / 256));
    return pitchClassToLattice(pitchClass);
  });

  // Calculate TSV modulation
  const avgTSV = tensorField.length > 0 
    ? tensorField.reduce((sum, t) => sum + t.TSV, 0) / tensorField.length 
    : 0;
  const tsvGain = clamp(0.7 + avgTSV * 0.12, 0.3, 1.4);

  return (
    <div className="relative bg-slate-900 rounded-lg overflow-hidden">
      <svg width={width} height={height} className="border border-slate-700">
        <defs>
          <radialGradient id="nodeGradient" cx="0.5" cy="0.5" r="0.5">
            <stop offset="0%" stopColor="rgba(34, 197, 94, 0.8)" />
            <stop offset="100%" stopColor="rgba(34, 197, 94, 0.2)" />
          </radialGradient>
        </defs>
        
        {/* Grid lines */}
        <g stroke="rgba(148, 163, 184, 0.1)" strokeWidth="1">
          {Array.from({ length: 21 }, (_, i) => i - 10).map(i => (
            <g key={i}>
              <line
                x1={centerX + i * scale}
                y1={0}
                x2={centerX + i * scale}
                y2={height}
              />
              <line
                x1={0}
                y1={centerY + i * scale}
                x2={width}
                y2={centerY + i * scale}
              />
            </g>
          ))}
        </g>

        {/* Schumann resonance nodes */}
        {latticePoints.map((point, i) => {
          const x = centerX + point.x * scale;
          const y = centerY - point.y * scale;
          const radius = (8 + i * 2) * tsvGain;
          const opacity = clamp(0.4 + tsvGain * 0.3, 0.2, 1);

          return (
            <g key={i}>
              <circle
                cx={x}
                cy={y}
                r={radius}
                fill="url(#nodeGradient)"
                opacity={opacity}
              />
              <text
                x={x}
                y={y + 4}
                fontSize="10"
                fill="white"
                textAnchor="middle"
                className="pointer-events-none"
              >
                {schumannHz[i].toFixed(1)}
              </text>
            </g>
          );
        })}
        
        {/* Intent visualization */}
        {intentText && (
          <text
            x={width - 10}
            y={20}
            fontSize="12"
            fill="rgba(147, 51, 234, 0.8)"
            textAnchor="end"
            className="pointer-events-none"
          >
            Intent: {intentText}
          </text>
        )}
      </svg>
    </div>
  );
};

export default SchumannLattice;