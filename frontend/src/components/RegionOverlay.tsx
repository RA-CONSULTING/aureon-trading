import React from 'react';
import { LatticePoint, pitchClassToLattice } from './SchumannLatticePatch';

export interface RegionData {
  id: string;
  name: string;
  lat: number;
  lon: number;
  dominantHz: number;
  weight: number;
}

interface RegionOverlayProps {
  regions: RegionData[];
  width: number;
  height: number;
  scale: number;
  centerX: number;
  centerY: number;
}

export const RegionOverlay: React.FC<RegionOverlayProps> = ({
  regions,
  width,
  height,
  scale,
  centerX,
  centerY
}) => {
  return (
    <g className="region-overlay">
      {regions.map((region) => {
        // Convert Hz to pitch class and lattice position
        const pitchClass = Math.round(12 * Math.log2(region.dominantHz / 256));
        const latticePoint = pitchClassToLattice(pitchClass);
        
        // Add small jitter based on lat/lon to prevent overlaps
        const jitterX = (region.lon / 180) * 0.3;
        const jitterY = (region.lat / 90) * 0.3;
        
        const x = centerX + (latticePoint.x + jitterX) * scale;
        const y = centerY - (latticePoint.y + jitterY) * scale;
        
        // Ensure point is within bounds
        if (x < 0 || x > width || y < 0 || y > height) return null;
        
        const opacity = Math.min(1, region.weight * 0.8 + 0.2);
        const radius = Math.max(2, region.weight * 8);
        
        return (
          <g key={region.id}>
            <circle
              cx={x}
              cy={y}
              r={radius}
              fill="rgba(255, 165, 0, 0.7)"
              stroke="rgba(255, 140, 0, 0.9)"
              strokeWidth="1"
              opacity={opacity}
            />
            <text
              x={x}
              y={y - radius - 4}
              fontSize="10"
              fill="rgba(255, 255, 255, 0.8)"
              textAnchor="middle"
              className="pointer-events-none"
            >
              {region.name}
            </text>
          </g>
        );
      })}
    </g>
  );
};