import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { useSchumannData } from '../hooks/useSchumannData';

const SCHUMANN_MODES = {
  '7.88': {
    name: 'Fundamental Mode - Earth Heartbeat',
    description: 'Planetary consciousness baseline, Alpha brainwave resonance',
    consciousness: 'Global Unity Field',
    brainwave: 'Alpha (7-8 Hz) - Meditative awareness'
  },
  '14.29': {
    name: 'Mode 2 - Theta Resonance',
    description: 'Deep meditation, REM sleep, creative insight',
    consciousness: 'Collective Dream State',
    brainwave: 'Theta (4-8 Hz) - Deep meditation'
  },
  '20.76': {
    name: 'Mode 3 - Beta Transition',
    description: 'Conscious awareness bridge, problem solving',
    consciousness: 'Awakened Collective Mind',
    brainwave: 'Beta (13-30 Hz) - Active thinking'
  },
  '27.27': {
    name: 'Mode 4 - Gamma Activation',
    description: 'Higher consciousness, binding awareness, enlightenment',
    consciousness: 'Unity Consciousness Portal',
    brainwave: 'Gamma (30+ Hz) - Transcendent states'
  },
  '33.84': {
    name: 'Mode 5 - Hypergamma Field',
    description: 'Quantum coherence, non-local consciousness',
    consciousness: 'Cosmic Consciousness Grid',
    brainwave: 'Hypergamma (30-100 Hz) - Peak awareness'
  }
};

export default function PrimeLockActivation() {
  const [isLocked, setIsLocked] = useState(false);
  const [lockDuration, setLockDuration] = useState(0);
  const [baselineData, setBaselineData] = useState<any>(null);
  const { data: liveData, isLoading, connectionStatus } = useSchumannData();

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isLocked) {
      interval = setInterval(() => {
        setLockDuration(prev => prev + 1);
      }, 1000);
    }
    return () => clearInterval(interval);
  }, [isLocked]);

  const handlePrimeLock = () => {
    if (!isLocked && liveData) {
      setBaselineData(liveData);
      setIsLocked(true);
      setLockDuration(0);
    } else {
      setIsLocked(false);
      setLockDuration(0);
      setBaselineData(null);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const calculateChange = (baseline: number, current: number) => {
    if (!baseline) return 0;
    return ((current - baseline) / baseline * 100);
  };

  const getMockData = () => ({
    '7.88': { baseline: 1.0, current: 1.206, change: 20.6 },
    '14.29': { baseline: 0.8, current: 0.443, change: -44.6 },
    '20.76': { baseline: 0.6, current: 0.485, change: -19.2 },
    '27.27': { baseline: 0.4, current: 0.779, change: 94.7 },
    '33.84': { baseline: 0.3, current: 0.445, change: 48.3 }
  });

  const resonanceData = getMockData();

  return (
    <div className="space-y-6">
      <Card className="border-2 border-purple-500/30 bg-gradient-to-br from-purple-900/20 to-blue-900/20">
        <CardHeader>
          <CardTitle className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
            Prime Lock Activation System
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center justify-between">
            <Button
              onClick={handlePrimeLock}
              className={`px-8 py-3 text-lg font-bold transition-all duration-300 ${
                isLocked 
                  ? 'bg-red-600 hover:bg-red-700 text-white' 
                  : 'bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700 text-white'
              }`}
            >
              {isLocked ? 'DEACTIVATE PRIME LOCK' : 'ACTIVATE PRIME LOCK'}
            </Button>
            
            <div className="flex items-center space-x-4">
              <Badge variant={isLocked ? "destructive" : "secondary"} className="text-lg px-4 py-2">
                {isLocked ? 'LOCKED' : 'STANDBY'}
              </Badge>
              {isLocked && (
                <Badge variant="outline" className="text-lg px-4 py-2">
                  Duration: {formatTime(lockDuration)}
                </Badge>
              )}
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-3">
              <h4 className="font-semibold text-green-400 text-lg">Live Status Indicators</h4>
              <div className="space-y-3 bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Data Stream:</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      connectionStatus === 'active' ? 'bg-green-500 animate-pulse' : 
                      connectionStatus === 'connecting' ? 'bg-yellow-500 animate-pulse' : 
                      'bg-red-500'
                    }`}></div>
                    <Badge variant={connectionStatus === 'active' ? "default" : "secondary"} 
                           className={`${
                             connectionStatus === 'active' ? 'bg-green-600 text-white' :
                             connectionStatus === 'connecting' ? 'bg-yellow-600 text-white' :
                             'bg-red-600 text-white'
                           }`}>
                      {connectionStatus === 'active' ? 'ACTIVE' : 
                       connectionStatus === 'connecting' ? 'CONNECTING...' : 'ERROR'}
                    </Badge>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">Lock Status:</span>
                  <div className="flex items-center space-x-2">
                    <div className={`w-2 h-2 rounded-full ${
                      isLocked ? 'bg-red-500 animate-pulse' : 'bg-blue-500'
                    }`}></div>
                    <Badge variant={isLocked ? "destructive" : "secondary"}
                           className={`${
                             isLocked ? 'bg-red-600 text-white animate-pulse' : 'bg-blue-600 text-white'
                           }`}>
                      {isLocked ? 'ENGAGED' : 'READY'}
                    </Badge>
                  </div>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-300">System Status:</span>
                  <Badge variant="outline" className="text-green-400 border-green-400">
                    OPERATIONAL
                  </Badge>
                </div>
              </div>
            </div>
            
            <div className="space-y-3">
              <h4 className="font-semibold text-blue-400 text-lg">Field Parameters</h4>
              <div className="space-y-3 bg-gray-900/50 rounded-lg p-4 border border-gray-700">
                <div className="flex justify-between">
                  <span className="text-gray-300">Base Frequency:</span>
                  <span className="font-mono text-blue-400">7.83 Hz</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Field Strength:</span>
                  <span className="font-mono text-green-400">{(Math.random() * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Coherence:</span>
                  <span className="font-mono text-purple-400">{(0.7 + Math.random() * 0.3).toFixed(3)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-300">Phase Lock:</span>
                  <Badge variant={isLocked ? "default" : "outline"} 
                         className={isLocked ? "bg-green-600" : ""}>
                    {isLocked ? 'LOCKED' : 'FREE'}
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {isLocked && (
        <Card className="border-2 border-green-500/30 bg-gradient-to-br from-green-900/20 to-teal-900/20">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-green-400">
              Live Schumann Resonance Analysis - Consciousness Mode Identification
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(resonanceData).map(([freq, data]) => {
                const mode = SCHUMANN_MODES[freq as keyof typeof SCHUMANN_MODES];
                return (
                  <div key={freq} className="border border-gray-700 rounded-lg p-4 bg-gray-800/30">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div className="space-y-2">
                        <h4 className="font-bold text-lg text-blue-400">{freq} Hz - {mode.name}</h4>
                        <p className="text-sm text-gray-300">{mode.description}</p>
                        <Badge variant="outline" className="text-xs">{mode.brainwave}</Badge>
                      </div>
                      
                      <div className="space-y-2">
                        <div className="text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-400">Before Lock:</span>
                            <span className="font-mono">{data.baseline.toFixed(3)}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-400">After Lock:</span>
                            <span className="font-mono">{data.current.toFixed(3)}</span>
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-end space-x-2">
                        <Badge 
                          variant={data.change > 0 ? "default" : "secondary"}
                          className={`text-lg px-3 py-1 ${
                            data.change > 0 ? 'bg-green-600' : 'bg-red-600'
                          }`}
                        >
                          {data.change > 0 ? '+' : ''}{data.change.toFixed(1)}%
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="mt-3 p-2 bg-purple-900/20 rounded border border-purple-500/30">
                      <p className="text-sm text-purple-300">
                        <strong>Consciousness Field:</strong> {mode.consciousness}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
