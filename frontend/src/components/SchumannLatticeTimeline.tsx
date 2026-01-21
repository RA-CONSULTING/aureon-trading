// Timeline scrubber and playback for Schumann lattice
import React, { useState, useEffect, useCallback } from 'react';
import { Button } from './ui/button';
import { Slider } from './ui/slider';
import { Play, Pause, SkipBack, SkipForward } from 'lucide-react';
import { SchumannLattice } from './SchumannLattice';
import { TimelineFrame } from './SchumannDataLoaders';

interface SchumannLatticeTimelineProps {
  frames: TimelineFrame[];
  autoPlay?: boolean;
  fps?: number;
  width?: number;
  height?: number;
  compiler?: any;
  intentText?: string;
}

export function SchumannLatticeTimeline({
  frames,
  autoPlay = false,
  fps = 8,
  width = 600,
  height = 400,
  compiler,
  intentText
}: SchumannLatticeTimelineProps) {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [isPlaying, setIsPlaying] = useState(autoPlay);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  const frameInterval = 1000 / (fps * playbackSpeed);

  useEffect(() => {
    if (!isPlaying || frames.length === 0) return;

    const interval = setInterval(() => {
      setCurrentFrame(prev => (prev + 1) % frames.length);
    }, frameInterval);

    return () => clearInterval(interval);
  }, [isPlaying, frames.length, frameInterval]);

  const handlePlay = useCallback(() => {
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  const handleFrameChange = useCallback((value: number[]) => {
    setCurrentFrame(value[0]);
    setIsPlaying(false);
  }, []);

  const handleSpeedChange = useCallback((value: number[]) => {
    setPlaybackSpeed(value[0]);
  }, []);

  if (frames.length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No timeline data available
      </div>
    );
  }

  const currentData = frames[currentFrame];

  return (
    <div className="space-y-4">
      <SchumannLattice
        schumannHz={currentData.schumannHz}
        tensorField={currentData.tensorField}
        compiler={compiler}
        intentText={intentText}
        width={width}
        height={height}
      />
      
      <div className="bg-gray-900 p-4 rounded-lg">
        <div className="flex items-center space-x-4 mb-4">
          <Button onClick={() => setCurrentFrame(0)} variant="outline" size="sm">
            <SkipBack className="w-4 h-4" />
          </Button>
          
          <Button onClick={handlePlay} variant="outline" size="sm">
            {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
          </Button>
          
          <Button onClick={() => setCurrentFrame(frames.length - 1)} variant="outline" size="sm">
            <SkipForward className="w-4 h-4" />
          </Button>
          
          <span className="text-sm text-gray-300">
            Frame {currentFrame + 1} / {frames.length}
          </span>
        </div>
        
        <div className="space-y-3">
          <div>
            <label className="text-sm text-gray-300 mb-2 block">Timeline Position</label>
            <Slider
              value={[currentFrame]}
              onValueChange={handleFrameChange}
              max={frames.length - 1}
              step={1}
              className="w-full"
            />
          </div>
          
          <div>
            <label className="text-sm text-gray-300 mb-2 block">Speed: {playbackSpeed}x</label>
            <Slider
              value={[playbackSpeed]}
              onValueChange={handleSpeedChange}
              min={0.1}
              max={3}
              step={0.1}
              className="w-full"
            />
          </div>
        </div>
        
        <div className="mt-3 text-xs text-gray-400">
          Timestamp: {new Date(currentData.t).toLocaleString()}
        </div>
      </div>
    </div>
  );
}