// Complete Schumann Lattice Integration with all features
import React, { useCallback } from 'react';
import { SchumannLattice } from './SchumannLattice';
import { SchumannLatticeTimeline } from './SchumannLatticeTimeline';
import { SchumannLatticeWithRegions } from './SchumannLatticeWithRegions';
import { loadZipFrames, csvToFrames, TimelineFrame } from './SchumannDataLoaders';
import { TensorDatum } from './SchumannLatticePatch';

interface Region {
  id: string;
  name: string;
  lat: number;
  lon: number;
  dominantHz: number;
  weight: number;
}

interface SchumannLatticeCompleteProps {
  mode: 'static' | 'timeline' | 'regions';
  schumannHz?: number[];
  tensorField?: TensorDatum[];
  frames?: TimelineFrame[];
  regions?: Region[];
  compiler?: any;
  intentText?: string;
  width?: number;
  height?: number;
  autoPlay?: boolean;
  fps?: number;
}

export function SchumannLatticeComplete({
  mode = 'static',
  schumannHz = [7.83, 14.3, 20.8, 27.3, 33.8],
  tensorField = [],
  frames = [],
  regions = [],
  compiler,
  intentText,
  width = 600,
  height = 400,
  autoPlay = false,
  fps = 8
}: SchumannLatticeCompleteProps) {

  const handleFileUpload = useCallback(async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      let loadedFrames: TimelineFrame[] = [];
      
      if (file.name.endsWith('.zip')) {
        loadedFrames = await loadZipFrames(file);
      } else if (file.name.endsWith('.csv')) {
        loadedFrames = await csvToFrames(file);
      }
      
      console.log(`Loaded ${loadedFrames.length} frames from ${file.name}`);
      // In a real app, you'd update state here
    } catch (error) {
      console.error('Error loading file:', error);
    }
  }, []);

  const renderLattice = () => {
    switch (mode) {
      case 'timeline':
        return (
          <SchumannLatticeTimeline
            frames={frames}
            autoPlay={autoPlay}
            fps={fps}
            width={width}
            height={height}
            compiler={compiler}
            intentText={intentText}
          />
        );
      
      case 'regions':
        return (
          <SchumannLatticeWithRegions
            regions={regions}
            schumannHz={schumannHz}
            tensorField={tensorField}
            compiler={compiler}
            intentText={intentText}
            width={width}
            height={height}
          />
        );
      
      default:
        return (
          <SchumannLattice
            schumannHz={schumannHz}
            tensorField={tensorField}
            compiler={compiler}
            intentText={intentText}
            width={width}
            height={height}
          />
        );
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center space-x-4 mb-4">
        <label className="text-sm font-medium">
          Upload Data:
          <input
            type="file"
            accept=".zip,.csv"
            onChange={handleFileUpload}
            className="ml-2 text-xs"
          />
        </label>
      </div>
      
      {renderLattice()}
      
      <div className="text-xs text-gray-500 mt-4">
        Mode: {mode} | Intent: {intentText || 'none'} | 
        Frequencies: {schumannHz.map(f => f.toFixed(1)).join(', ')} Hz
      </div>
    </div>
  );
}

export default SchumannLatticeComplete;