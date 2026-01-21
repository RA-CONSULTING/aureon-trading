import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Play, Pause, Square, BarChart3, Activity } from 'lucide-react';

export function SimulationDashboard() {
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleStart = () => {
    setIsRunning(true);
    // Simulate progress
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);
          return 0;
        }
        return prev + 2;
      });
    }, 100);
  };

  const handleStop = () => {
    setIsRunning(false);
    setProgress(0);
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Tensor Evolution Control
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4 mb-4">
            <Button onClick={handleStart} disabled={isRunning} size="sm">
              <Play className="w-4 h-4 mr-1" />
              Start
            </Button>
            <Button onClick={() => setIsRunning(!isRunning)} variant="outline" size="sm">
              {isRunning ? <Pause className="w-4 h-4 mr-1" /> : <Play className="w-4 h-4 mr-1" />}
              {isRunning ? 'Pause' : 'Resume'}
            </Button>
            <Button onClick={handleStop} variant="destructive" size="sm">
              <Square className="w-4 h-4 mr-1" />
              Stop
            </Button>
            <Badge variant={isRunning ? 'default' : 'secondary'}>
              {isRunning ? 'Running' : 'Idle'}
            </Badge>
          </div>
          {isRunning && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-muted-foreground">
                Processing φ, κ, ψ, TSV evolution... {progress}%
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">System States</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button variant="outline" size="sm" className="w-full justify-start">
                Early vs Mid Overlay
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                Mid vs Late Overlay
              </Button>
              <Button variant="outline" size="sm" className="w-full justify-start">
                Full Timeline View
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              Stability Monitor
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span>MaxPsiAmplitude</span>
                <Badge variant="outline">Stable</Badge>
              </div>
              <Progress value={75} className="w-full" />
              <Button variant="outline" size="sm" className="w-full">
                View Chaos Analysis
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}