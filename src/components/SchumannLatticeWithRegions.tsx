import React from 'react';
import { SchumannLattice } from './SchumannLattice';
import { RegionOverlay, RegionData } from './RegionOverlay';
import { TensorDatum, IntentCompiler } from './SchumannLatticePatch';

interface SchumannLatticeWithRegionsProps {
  regions: RegionData[];
  schumannHz?: number[];
  tensorField?: TensorDatum[];
  compiler?: IntentCompiler;
  intentText?: string;
  width?: number;
  height?: number;
}

export const SchumannLatticeWithRegions: React.FC<SchumannLatticeWithRegionsProps> = ({
  regions,
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

  return (
    <div className="relative">
      <SchumannLattice
        schumannHz={schumannHz}
        tensorField={tensorField}
        compiler={compiler}
        intentText={intentText}
        width={width}
        height={height}
      />
      <svg
        width={width}
        height={height}
        className="absolute top-0 left-0 pointer-events-none"
        style={{ zIndex: 10 }}
      >
        <RegionOverlay
          regions={regions}
          width={width}
          height={height}
          scale={scale}
          centerX={centerX}
          centerY={centerY}
        />
      </svg>
    </div>
  );
};